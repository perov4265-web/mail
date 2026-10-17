#!/usr/bin/env python3
"""Собирает просмотрщик в один автономный HTML: Three.js, данные и текстура плана встроены.

  THREE_DIR=node_modules/three ESBUILD=npx\\ esbuild python3 tools/build_single.py [выход.html]
"""
import base64, json, os, pathlib, re, subprocess, sys, tempfile
root = pathlib.Path(__file__).resolve().parent.parent
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'territory-3d.html'
three = pathlib.Path(os.environ.get('THREE_DIR', root / 'node_modules' / 'three'))
esbuild = os.environ.get('ESBUILD', 'npx esbuild').split()
html = (root / 'index.html').read_text(encoding='utf-8')
m = re.search(r'<script type="module">\n(.*?)</script>', html, re.S); app = m.group(1)
with tempfile.TemporaryDirectory() as td:
    src = pathlib.Path(td) / 'app.js'
    src.write_text(app.replace("from './js/building.js'", f"from '{(root / 'js' / 'building.js').as_posix()}'"), encoding='utf-8')
    bundle = pathlib.Path(td) / 'bundle.js'
    subprocess.run([*esbuild, str(src), '--bundle', '--format=esm', '--minify', '--charset=utf8', '--log-level=warning',
                    f'--alias:three={(three / "build" / "three.module.js").as_posix()}',
                    f'--alias:three/addons={(three / "examples" / "jsm").as_posix()}', f'--outfile={bundle}'], check=True, cwd=root)
    js = bundle.read_text(encoding='utf-8')
site = json.loads((root / 'data' / 'site.json').read_text(encoding='utf-8'))
tex = root / site['meta']['texture']['file']
site['meta']['texture']['file'] = 'data:image/jpeg;base64,' + base64.b64encode(tex.read_bytes()).decode()
inline = {'data/site.json': site}
for n in ('abk1', 'abk2', 'mosque'): inline[f'data/{n}.json'] = json.loads((root / 'data' / f'{n}.json').read_text(encoding='utf-8'))
loader = ('<script>const __INLINE=' + json.dumps(inline, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') +
          ';const __fetch=window.fetch.bind(window);window.fetch=(u,...a)=>(typeof u==="string"&&u in __INLINE)?Promise.resolve(new Response(JSON.stringify(__INLINE[u]),{headers:{"content-type":"application/json"}})):__fetch(u,...a);</script>\n')
html = re.sub(r'<script type="importmap">.*?</script>\n', '', html, flags=re.S)
html = html.replace(m.group(0), loader + '<script type="module">\n' + js.replace('</script', '<\\/script') + '\n</script>')
out.write_text(html, encoding='utf-8'); print(out, out.stat().st_size, 'bytes')
