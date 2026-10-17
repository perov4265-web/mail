set -e
cd "$(dirname "$0")"
python3 -I build_site.py /home/user/mail/territory-3d/data/site.json
python3 -I signs_build.py
python3 -I add_arrows.py
