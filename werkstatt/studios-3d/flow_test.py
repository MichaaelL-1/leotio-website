# Leotio Studios Flow-Test v0.1 · 28.11.2026: Mantaflow-Rauch fuer genau einen Schlag (Schlag 1, Gelb #E3A21A, p=[-0.5,0.42] aus takt-a8.json)
# Aufruf: blender -b --python flow_test.py -- AUSGABEORDNER [bake|render|all] [VON-BIS]
# Gleiche Szene wie scene.py (Logo, Kamera von oben, Licht), Domain nur ueber dem Quadrat. Umgebung (alle optional):
#   RES=96 Aufloesung der Rauch-Zellen (laengste Seite)   NOISE=2 Noise-Upres (0 = aus)   VORT=0.35 Vorticity   NSCALE=2.0 Noise-Groesse
#   SINK=2.0 Absinken (Buoyancy Density)   DENS=25 Dichte-Faktor des Volumens   FR=72 Bilder (24 fps)   VEL=3.0 Ausstossgeschwindigkeit
#   RX=1280 RY=720 SPP=48 (Cycles, GPU=1 fuer Metal)   POS=-0.5,0.42   COL=E3A21A   BURST=3 Ausstoss-Bilder
import bpy, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene
E = os.environ.get
arg = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(arg[0]); MODE = arg[1] if len(arg) > 1 else 'all'
FR = int(E('FR', '72'))
RA = [int(x) for x in arg[2].split('-')] if len(arg) > 2 else [1, FR]
RX, RY = int(E('RX', '1280')), int(E('RY', '720'))
sc, cam = scene.build(28.0, (RX, RY), int(E('SPP', '48')))
sc.render.fps = 24; sc.frame_start = 1; sc.frame_end = FR
px, py = [float(v) for v in E('POS', '-0.5,0.42').split(',')]
hexc = E('COL', 'E3A21A'); lin = [(int(hexc[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)]

# Domain: nur ueber dem Quadrat (Logo-Quadrat = -1..1 m), 0..0.7 m hoch
H = 0.7
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H / 2)); dom = bpy.context.active_object; dom.name = 'Domain'
dom.scale = (2.0, 2.0, H)
md = dom.modifiers.new('fluid', 'FLUID'); md.fluid_type = 'DOMAIN'; ds = md.domain_settings
ds.domain_type = 'GAS'; ds.resolution_max = int(E('RES', '96'))
ds.use_noise = int(E('NOISE', '2')) > 0
if ds.use_noise: ds.noise_scale = int(E('NOISE', '2')); ds.noise_strength = float(E('NSCALE', '2.0')) * 0.5
ds.vorticity = float(E('VORT', '0.35'))
ds.alpha = float(E('SINK', '2.0')); ds.beta = 0.0
ds.use_collision_border_bottom = True
for s in ('top', 'front', 'back', 'left', 'right'):
    try: setattr(ds, 'use_collision_border_' + s, False)
    except Exception: pass
ds.cache_directory = os.path.join(OUT, 'cache'); os.makedirs(OUT, exist_ok=True)
ds.cache_frame_start, ds.cache_frame_end = 1, FR
try: ds.cache_type = 'ALL'
except Exception: pass

# Quelle: kleine Kugel ueber dem Einschlag, kurzer Ausstoss ueber BURST Bilder, Richtung nach aussen und auf die Flaeche zu
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(px, py, 0.12)); fl = bpy.context.active_object; fl.name = 'Quelle'
mf = fl.modifiers.new('fluid', 'FLUID'); mf.fluid_type = 'FLOW'; fs = mf.flow_settings
fs.flow_type = 'SMOKE'; fs.flow_behavior = 'INFLOW'; fs.flow_source = 'MESH'
fs.smoke_color = lin; fs.density = 1.0; fs.surface_distance = 1.0
fs.use_initial_velocity = True; fs.velocity_normal = float(E('VEL', '3.0')); fs.velocity_coord = (0, 0, -float(E('VEL', '3.0')) * 0.6)
B = int(E('BURST', '3'))
fs.use_inflow = True; fs.keyframe_insert('use_inflow', frame=1)
fs.use_inflow = False; fs.keyframe_insert('use_inflow', frame=1 + B)
fl.hide_render = True

# Material der Domain: Principled Volume, Dichte und Farbe aus dem Rauch
m = bpy.data.materials.new('Rauch'); m.use_nodes = True; nt = m.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new('ShaderNodeOutputMaterial'); pv = nt.nodes.new('ShaderNodeVolumePrincipled')
ad = nt.nodes.new('ShaderNodeAttribute'); ad.attribute_name = 'density'
ac = nt.nodes.new('ShaderNodeAttribute'); ac.attribute_name = 'color'
mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = float(E('DENS', '25'))
nt.links.new(ad.outputs['Fac'], mu.inputs[0]); nt.links.new(mu.outputs[0], pv.inputs['Density'])
nt.links.new(ac.outputs['Color'], pv.inputs['Color'])
pv.inputs['Anisotropy'].default_value = 0.3
try: pv.inputs['Absorption Color'].default_value = (*lin, 1)
except Exception: pass
nt.links.new(pv.outputs['Volume'], out.inputs['Volume'])
dom.data.materials.append(m)

t0 = time.time()
if MODE in ('bake', 'all'):
    bpy.context.view_layer.objects.active = dom
    bpy.ops.fluid.bake_data()
    print('BAKE_SEKUNDEN', round(time.time() - t0, 1), flush=True)
    if ds.use_noise:   # Noise-Upres (Blumenkohl-Raender) ist ein eigener Backschritt
        bpy.ops.fluid.bake_noise()
        print('NOISE_SEKUNDEN', round(time.time() - t0, 1), flush=True)
if MODE in ('render', 'all'):
    os.makedirs(os.path.join(OUT, 'f'), exist_ok=True)
    for f in range(RA[0], RA[1] + 1):
        t1 = time.time(); sc.frame_set(f); sc.render.filepath = os.path.join(OUT, 'f', 'f_%04d.png' % f)
        bpy.ops.render.render(write_still=True)
        print('BILD', f, round(time.time() - t1, 1), 's', flush=True)
print('GESAMT_SEKUNDEN', round(time.time() - t0, 1), flush=True)
