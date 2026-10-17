#!/usr/bin/env python3
"""Фотореалистичные рендеры по скриншотам модели через gen-api.ru (image-to-image).

Запуск:  GEN_API_KEY=... python3 tools/genapi_render.py renders/ai/jobs.json [имена...]
jobs.json — список задач: {"name", "ref", "prompt"}; результат кладётся в renders/ai/<name>.jpg,
состояние (request_id, url, cost) дописывается в renders/ai/state.json, так что повторный
запуск доделывает только то, чего ещё нет.
"""
import json, os, sys, time, pathlib, requests

API = "https://api.gen-api.ru/api/v1"
MODEL = os.environ.get("GEN_API_MODEL", "nano-banana-2")
KEY = os.environ["GEN_API_KEY"]
H = {"Authorization": f"Bearer {KEY}", "Accept": "application/json"}
PREFIX = ("Turn this 3D model screenshot into a photorealistic render. Keep the exact camera, geometry, layout, "
          "proportions and positions of every object from the reference image. Do not add anything that is not in the "
          "reference: no extra buildings, containers, vehicles, machinery, people, text, labels, arrows or logos. "
          "Coloured zones and lines on the ground are only CAD markings: render them as plain grey asphalt or paving "
          "with thin white bay lines. ")

root = pathlib.Path(__file__).resolve().parent.parent
jobs_path = pathlib.Path(sys.argv[1]); only = set(sys.argv[2:])
out_dir = jobs_path.parent; state_path = out_dir / "state.json"
jobs = json.load(open(jobs_path, encoding="utf-8"))
state = json.load(open(state_path, encoding="utf-8")) if state_path.exists() else {}
def save(): json.dump(state, open(state_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 1. отправка
for j in jobs:
    n = j["name"]
    if only and n not in only: continue
    st = state.setdefault(n, {})
    if st.get("request_id") and st.get("status") != "error": continue
    files = {"image_urls[]": open(root / j["ref"], "rb")}
    data = {"prompt": PREFIX + j["prompt"], "aspect_ratio": j.get("aspect_ratio", "16:9"),
            "resolution": j.get("resolution", os.environ.get("GEN_API_RES", "1K")), "output_format": "jpeg", "is_sync": "false"}
    r = requests.post(f"{API}/networks/{MODEL}", headers=H, data=data, files=files, timeout=120)
    try: resp = r.json()
    except Exception: resp = {"raw": r.text[:300]}
    st.update(request_id=resp.get("request_id"), status=resp.get("status"), model=MODEL, submit=resp if not resp.get("request_id") else None)
    print("submit", n, resp.get("request_id"), resp.get("status"), "" if resp.get("request_id") else resp); save()

# 2. ожидание и скачивание
pending = [j["name"] for j in jobs if (not only or j["name"] in only) and state.get(j["name"], {}).get("request_id") and not (out_dir / f"{j['name']}.jpg").exists()]
deadline = time.time() + 900
while pending and time.time() < deadline:
    for n in list(pending):
        st = state[n]
        r = requests.get(f"{API}/request/get/{st['request_id']}", headers=H, timeout=60).json()
        st["status"] = r.get("status")
        if r.get("status") == "success":
            st.update(url=r["result"][0], cost=r.get("cost"), runtime=r.get("runtime")); save()
            try:
                img = requests.get(st["url"], timeout=120); img.raise_for_status()
                (out_dir / f"{n}.jpg").write_bytes(img.content); st["saved"] = True
                print("saved", n, len(img.content), "bytes, cost", st["cost"])
            except Exception as e:
                st["saved"] = False; print("DOWNLOAD FAILED", n, st["url"], e)
            pending.remove(n)
        elif r.get("status") == "error":
            st["error"] = r; print("ERROR", n, json.dumps(r, ensure_ascii=False)[:300]); pending.remove(n)
    save()
    if pending: time.sleep(8)
print("done; pending:", pending)
