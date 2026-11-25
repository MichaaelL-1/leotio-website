#!/bin/bash
# Leotio Studios 3D-Lauf v1 · 25.11.2026
# Aufruf: ./run.sh preview|final   (im Ordner ~/Developer/leotio-3d)
set -e
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
[ -d .venv ] || { python3 -m venv .venv; .venv/bin/pip install -q numpy scipy pillow; }
command -v ffmpeg >/dev/null || brew install ffmpeg
[ -f simC/dep_0239.png ] || .venv/bin/python sim.py simC
MODE=${1:-preview}
if [ "$MODE" = preview ]; then
  rm -rf prev; ENGINE=EEVEE EEVEE_SPP=16 GAIN=1.2 RX=960 RY=540 $B -b --python render.py -- simC prev 0-239 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i prev/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 out/k2-3d-vorschau.mp4
else
  rm -rf final; GPU=1 GAIN=1.2 RX=1920 RY=1080 SPP=64 $B -b --python render.py -- simC final 0-239 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i final/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 out/k2-3d.mp4
fi
ls -la out/
