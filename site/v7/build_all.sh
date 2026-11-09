#!/bin/sh
cd "$(dirname "$0")"
python3 make7.py && python3 gen_rich.py && python3 mkhome.py && python3 gen_home.py
