#!/bin/sh
cd "$(dirname "$0")"
python3 make7.py && python3 gen_rich.py && python3 mkhome.py && python3 gen_home.py
python3 gen_sektor_ek.py
sed -i 's/30 hazır temadan/148 hazır temadan/g' index.html paketler-ozellikler.html 2>/dev/null
