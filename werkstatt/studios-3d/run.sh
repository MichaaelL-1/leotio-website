#!/bin/bash
# Leotio Studios 3D-Lauf v4 · 25.11.2026
# Aufruf: ./run.sh preview|final   (im Ordner ~/Developer/leotio-3d)
set -e
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
[ -d .venv ] || { python3 -m venv .venv; .venv/bin/pip install -q numpy scipy pillow; }
command -v ffmpeg >/dev/null || brew install ffmpeg
[ -f simC/dep_0287.png ] || NEX=${NEX:-10} SCALE=${SCALE:-1.3} NP=${NP:-200000} FINE=0.7 CHALK=0.12 GAP=0.28 FPS=36 DUR=8 .venv/bin/python sim.py simC
MODE=${1:-preview}
if [ "$MODE" = preview ]; then
  rm -rf prev; ENGINE=EEVEE EEVEE_SPP=16 GAIN=1.2 PALPHA=0.3 RX=960 RY=540 $B -b --python render.py -- simC prev 0-287 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i prev/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 out/k2-3d-vorschau.mp4
elif [ "$MODE" = explosion ]; then
  # eine Explosion, Nahaufnahme, Zeitlupe (48 Bilder/s simuliert, mit 24 abgespielt)
  rm -rf simX ex; ONE=0.3,0.25,0.5,4 NP=500000 FPS=72 DUR=2.5 FINE=0.7 CHALK=0.12 .venv/bin/python sim.py simX
  ENGINE=EEVEE EEVEE_SPP=32 GAIN=1.2 PALPHA=0.3 RX=1920 RY=1080 CAM=0.3,0.25,2.2,50 $B -b --python render.py -- simX ex 0-179 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i ex/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 out/k2-3d-explosion.mp4
else
  rm -rf final; GPU=1 GAIN=1.2 PALPHA=0.3 RX=1920 RY=1080 SPP=64 $B -b --python render.py -- simC final 0-287 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i final/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 out/k2-3d.mp4
fi
ls -la out/
