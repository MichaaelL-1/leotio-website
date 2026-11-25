#!/bin/bash
# Leotio Studios 3D-Lauf v13 · 25.11.2026
# Aufruf: ./run.sh preview | explosion | fuenf | takt <welle|wasser|licht> | final | variante <schlag|farben|rillen>   (im Ordner ~/Developer/leotio-3d)
# Loescht nichts: alte Ordner wandern nach alt/
set -e
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
[ -d .venv ] || { python3 -m venv .venv; .venv/bin/pip install -q numpy scipy pillow; }
command -v ffmpeg >/dev/null || brew install ffmpeg
mkdir -p out alt
weg() { for d in "$@"; do case "$d" in sim*|pv*|ex*) [ -e "./$d" ] && rm -rf "./$d";; esac; done; return 0; }   # alte Zwischendaten loeschen (Michael 25.11.: immer aufraeumen)
SIMENV="NEX=10 SCALE=1.3 NP=200000 FINE=0.7 CHALK=0.12 GAP=0.28 FPS=36 DUR=8"
MODE=${1:-preview}
if [ "$MODE" = preview ]; then
  [ -f simC/dep_0287.png ] || env $SIMENV .venv/bin/python sim.py simC
  weg prev; ENGINE=EEVEE EEVEE_SPP=16 GAIN=1.2 PALPHA=0.3 RX=960 RY=540 $B -b --python render.py -- simC prev 0-287 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i prev/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 out/k2-3d-vorschau.mp4
elif [ "$MODE" = variante ]; then
  V=$2; weg simV_$V pv_$V
  env $SIMENV VAR=$V .venv/bin/python sim.py simV_$V
  ENGINE=EEVEE EEVEE_SPP=16 GAIN=1.2 PALPHA=0.3 RX=960 RY=540 $B -b --python render.py -- simV_$V pv_$V 0-287 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i pv_$V/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 out/k2-3d-$V.mp4
elif [ "$MODE" = fuenf ]; then
  weg sim5 pv5
  FUENF=1 SCALE=1.7 NP=400000 FINE=0.7 CHALK=0.12 GAP=0.9 DUST=0.12 HT=0.3 FPS=36 DUR=8 VAR=welle .venv/bin/python sim.py sim5
  ENGINE=EEVEE EEVEE_SPP=16 GAIN=1.2 PALPHA=0.3 RX=960 RY=540 $B -b --python render.py -- sim5 pv5 0-287 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i pv5/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 out/k2-3d-fuenf.mp4
elif [ "$MODE" = takt ]; then
  V=$2; weg simT_$V pvT_$V
  TAKT=takt.json NOFALL=1 VAR=$V SCALE=1.0 NP=${NP:-700000} SOFT=${SOFT:-1} MW=${MW:-0.57} FINE=0.8 CHALK=0.12 DUST=${DUST:-0} HT=0.3 FPS=36 DUR=8 NSPARK=${NSPARK:-26000} WMODE=${WMODE:-} .venv/bin/python sim.py simT_$V
  ENGINE=${ENGINE:-EEVEE} EEVEE_SPP=16 SPP=${SPP:-24} GAIN=1.2 PALPHA=0.3 RX=960 RY=540 $B -b --python render.py -- simT_$V pvT_$V ${FRAMES:-0-287} 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i pvT_$V/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 out/k2-3d-takt-$V.mp4
  weg simT_$V pvT_$V
elif [ "$MODE" = explosion ]; then
  weg simX ex; ONE=0.3,0.25,0.5,4 NP=200000 FPS=72 DUR=3.5 FINE=0.7 CHALK=0.12 DUST=0.3 HT=0.45 .venv/bin/python sim.py simX
  ENGINE=EEVEE EEVEE_SPP=32 GAIN=1.2 PALPHA=0.3 PSHADOW=1 RX=1920 RY=1080 CAM=0.3,0.25,2.8,50 $B -b --python render.py -- simX ex 0-251 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i ex/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 out/k2-3d-explosion.mp4
else
  weg final; GPU=1 GAIN=1.2 PALPHA=0.3 RX=1920 RY=1080 SPP=64 $B -b --python render.py -- simC final 0-287 2>&1 | grep '^frame' | tail -1
  ffmpeg -loglevel error -y -framerate 24 -i final/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 out/k2-3d.mp4
fi
ls -la out/
