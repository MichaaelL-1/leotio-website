# Leotio Studios 3D (Werkstatt) · 25.11.2026

Blender-Skripte für die Puder-Animation des Studios-Logos (K2 in 3D). Nicht Teil der Website.

- `sim.py` Puder-Simulation (numpy/scipy/pillow), schreibt `simC/`
- `scene.py` Logo-Relief, Licht, Kamera senkrecht von oben (Originalgröße)
- `render.py` Render pro Bild (Cycles oder EEVEE), Aufruf über Blender `-b --python render.py -- simC out 0-239`
- `run.sh preview|final` kompletter Lauf auf dem Mac
