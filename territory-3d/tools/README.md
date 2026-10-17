# Скрипты выгрузки (справочно)

Скрипты, которыми получены `data/*.json` и `textures/plan.jpg`. Пути к входным
файлам в них заданы относительно рабочих папок сеанса — перед запуском поправить.

| Папка | Что делает |
|---|---|
| `genplan/` | `extract.py` — векторная выгрузка PDF генплана (pdfplumber) по цветовым классам; `build_site.py` — здания, бордюры, ограждения, парковка, навесы, габионы в метрах; `signs*.py` — дорожные знаки (кластеры символов → выноски → точки установки); `add_arrows.py` — стрелки движения; `strip_signs.py` — копия PDF без слоя знаков для текстуры (правка content stream через pypdf); `rebuild.sh` — порядок запуска. |
| `abk1_dwg/` | `views.py`/`render.py` — обзор DXF (после `dwg2dxf` из LibreDWG); `plan_extract.py` — объекты архитектурного плана; `build_abk1.py` — `data/abk1.json`. |
| `abk2_pdf/` | `digitize.py` — оцифровка растрового плана V.2 (OpenCV: стены по двойным линиям, стеклянные перегородки, мебель); `build_abk2.py` — `data/abk2.json` с фасадом и фермами по «Итог1». |

Зависимости: pdfplumber, pypdf, numpy, Pillow, opencv-python-headless, ezdxf,
matplotlib, poppler-utils (`pdftoppm`), LibreDWG (`dwg2dxf`, собран из исходников 0.13.3).
