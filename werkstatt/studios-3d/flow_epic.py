# Leotio Studios Flow-Epic v0.6 · 28.11.2026: Episch-Test: zwei Schlaege (Gelb, Blau) in EINER Mantaflow-Domain, Stern aus Fahnen (Kern + Strahlen + duenne schnelle Strahlen + lange Fahnen), Farbe je Quelle (Farbattribut), weiches Licht, Bewegungsunschaerfe, Belag waechst beim Absinken. Basis: flow_test.py v0.5 (Runde 9), flow_story.py v0.5.
# Aufruf: blender -b --python flow_epic.py -- AUSGABEORDNER
# Umgebung: TF=100 Bilder  RES=256 DW=2.4 DH=0.9  FA=4 (Einschlagbild Schlag 1)  GAP=26 (Abstand Schlag 2 in Bildern, Takt 1,08 s)  HDFRAME=40 (ein HD-Standbild)  FRAMES=Liste  SIM=<simT_a8e>
import bpy, math, os, sys, time, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene
from mathutils import Vector
import numpy as np
E = os.environ.get
OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1]); os.makedirs(OUT, exist_ok=True)
TF = int(E('TF', '100')); RX, RY = int(E('RX', '640')), int(E('RY', '360'))
sc, cam = scene.build(28.0, (RX, RY), int(E('SPP', '16')))
sc.render.fps = 24; sc.frame_start = 1; sc.frame_end = TF
SIM = E('SIM', '')
def lin3(h): return [(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)]
FA = int(E('FA', '4')); GAP = int(E('GAP', '26')); OFF = 30 - FA   # Filmbild = Bild + OFF (Schlag 1 liegt im Film bei Bild 30)
PA = float(E('PASTEL', '0.25'))
Y = lin3('E3A21A'); Bl = lin3('2F8FC4')
YEFF = [l * k for l, k in zip(Y, [float(v) for v in E('YCM', '1,0.72,0.32').split(',')])]      # Indischgelb ohne Gruen-/Ocker-Kippen
BEFF = [l * (1 - PA) + PA * 0.8 for l in Bl]                                                     # Coelinblau, pastelliger
HITS = [dict(f=FA, p=(-0.5, 0.42), col=YEFF, sz=1.0), dict(f=FA + GAP, p=(0.47, -0.36), col=BEFF, sz=float(E('SZ2', '1.0')))]

# --- Licht, Kamera
for o_ in bpy.data.objects:
    if o_.type == 'LIGHT':
        el, az = math.radians(float(E('SUNEL', '30'))), math.radians(135)
        d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        o_.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); o_.data.energy = float(E('SUNE', '4.5')); o_.data.angle = math.radians(float(E('SUNA', '10'))); o_.data.color = (1, 1, 1)
wn = sc.world.node_tree.nodes['Background']; wn.inputs['Color'].default_value = (0.95, 0.95, 0.95, 1)
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = cam.location.z; cam.data.dof.aperture_fstop = float(E('DOFN', '0.2'))
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = float(E('MBLUR', '1.2'))
sc.cycles.volume_bounces = 8; sc.cycles.max_bounces = max(sc.cycles.max_bounces, 8)

# --- Papier: Deposit aus der Simulation (nur Schlag 1 und 2), Belag waechst erst beim Absinken
pap = bpy.data.materials['Papier']; pn = pap.node_tree; pb = pn.nodes['Principled BSDF']
for n_ in pn.nodes:
    if n_.type == 'TEX_NOISE' and n_.inputs['Scale'].default_value > 500: n_.inputs['Scale'].default_value = float(E('PGRAIN', '350'))
imgD = None
if SIM:
    gg = pn.nodes.new('ShaderNodeNewGeometry'); sp = pn.nodes.new('ShaderNodeSeparateXYZ'); pn.links.new(gg.outputs['Position'], sp.inputs[0])
    def lm(inp, mul, add):
        mm = pn.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY_ADD'; mm.inputs[1].default_value = mul; mm.inputs[2].default_value = add; pn.links.new(inp, mm.inputs[0]); return mm
    ux, uy = lm(sp.outputs['X'], 0.5, 0.5), lm(sp.outputs['Y'], 0.5, 0.5)
    cb = pn.nodes.new('ShaderNodeCombineXYZ'); pn.links.new(ux.outputs[0], cb.inputs['X']); pn.links.new(uy.outputs[0], cb.inputs['Y'])
    imgD = pn.nodes.new('ShaderNodeTexImage'); imgD.extension = 'CLIP'; pn.links.new(cb.outputs[0], imgD.inputs['Vector'])
    gn_ = pn.nodes.new('ShaderNodeMix'); gn_.data_type = 'RGBA'; gn_.blend_type = 'MULTIPLY'; gn_.inputs['Factor'].default_value = 1.0
    gn_.inputs['B'].default_value = (1.2, 1.2, 1.2, 1); pn.links.new(imgD.outputs['Color'], gn_.inputs['A'])
    mx = pn.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.90, 0.905, 0.905, 1)
    dram = pn.nodes.new('ShaderNodeValue'); dram.outputs[0].default_value = 0.0
    dam = pn.nodes.new('ShaderNodeMath'); dam.operation = 'MULTIPLY'; pn.links.new(imgD.outputs['Alpha'], dam.inputs[0]); pn.links.new(dram.outputs[0], dam.inputs[1])
    pn.links.new(dam.outputs[0], mx.inputs['Factor']); pn.links.new(gn_.outputs['Result'], mx.inputs['B']); pn.links.new(mx.outputs['Result'], pb.inputs['Base Color'])
SIMCAP = 186   # Sim-Bild, ab dem Schlag 3 (Rot) liegt
def simk(f): return min(2 * (f + OFF), SIMCAP)
def set_deposit(f):
    if imgD is None: return
    x = (f - FA - float(E('DDELAY', '8'))) / float(E('DRAMP', '40')); dram.outputs[0].default_value = max(0.0, min(1.0, x)) ** 1.5
    pth = os.path.join(SIM, 'dep_%04d.png' % simk(f))
    if os.path.exists(pth):
        if imgD.image: bpy.data.images.remove(imgD.image)
        imgD.image = bpy.data.images.load(pth); imgD.image.colorspace_settings.name = 'sRGB'
# --- Feinstaub aus den Sim-Partikeln (Farben der Schlaege 1 und 2)
PR = float(E('PR', '1.0')); PSUB = int(E('PSUB', '25'))
me_p = bpy.data.meshes.new('Staub'); ob_p = bpy.data.objects.new('Staub', me_p); bpy.context.collection.objects.link(ob_p)
gt = bpy.data.node_groups.new('StaubPunkte', 'GeometryNodeTree')
gt.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry'); gt.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi_ = gt.nodes.new('NodeGroupInput'); go_ = gt.nodes.new('NodeGroupOutput'); m2 = gt.nodes.new('GeometryNodeMeshToPoints')
na_ = gt.nodes.new('GeometryNodeInputNamedAttribute'); na_.data_type = 'FLOAT'; na_.inputs['Name'].default_value = 'rad'; sm_ = gt.nodes.new('GeometryNodeSetMaterial')
gt.links.new(gi_.outputs[0], m2.inputs['Mesh']); gt.links.new(na_.outputs['Attribute'], m2.inputs['Radius']); gt.links.new(m2.outputs['Points'], sm_.inputs['Geometry']); gt.links.new(sm_.outputs['Geometry'], go_.inputs[0])
ob_p.modifiers.new('pp', 'NODES').node_group = gt
pm = bpy.data.materials.new('Staub'); pm.use_nodes = True; pbs = pm.node_tree.nodes['Principled BSDF']
at_ = pm.node_tree.nodes.new('ShaderNodeAttribute'); at_.attribute_name = 'col'; at_.attribute_type = 'GEOMETRY'
pm.node_tree.links.new(at_.outputs['Color'], pbs.inputs['Base Color']); pbs.inputs['Roughness'].default_value = 0.9; sm_.inputs['Material'].default_value = pm
def set_particles(f):
    me_p.clear_geometry()
    if not SIM or PSUB <= 0: return
    pth = os.path.join(SIM, 'pts_%04d.npz' % simk(f))
    if not os.path.exists(pth): return
    z = np.load(pth); P = z['p']; C = z['c'].astype(np.float32); R = z['r'].astype(np.float32)
    sel = (np.abs(P[:, 0]) < 0.97) & (np.abs(P[:, 1]) < 0.97)
    idx = np.nonzero(sel)[0][::PSUB]
    if len(idx) == 0: return
    me_p.vertices.add(len(idx)); me_p.vertices.foreach_set('co', P[idx].ravel())
    a_ = me_p.attributes.new('rad', 'FLOAT', 'POINT'); a_.data.foreach_set('value', R[idx] * PR)
    c_ = me_p.attributes.new('col', 'FLOAT_COLOR', 'POINT'); c_.data.foreach_set('color', np.concatenate([C[idx], np.ones((len(idx), 1), np.float32)], 1).ravel()); me_p.update()

# --- Domain (eine fuer beide Schlaege)
RES = int(E('RES', '256')); DW = float(E('DW', '2.4')); DH = float(E('DH', '0.9'))
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, DH / 2)); dom = bpy.context.active_object; dom.name = 'Domain'; dom.scale = (DW, DW, DH)
md = dom.modifiers.new('fluid', 'FLUID'); md.fluid_type = 'DOMAIN'; ds = md.domain_settings
ds.domain_type = 'GAS'; ds.resolution_max = RES; ds.use_noise = False; ds.vorticity = float(E('VORT', '0.7')); ds.alpha = float(E('SINK', '1.5')); ds.beta = 0.0
ds.time_scale = float(E('TS', '0.6'))   # Zeitlupe ueber den ganzen Lauf
ds.use_collision_border_bottom = True
for sd in ('top', 'front', 'back', 'left', 'right'):
    try: setattr(ds, 'use_collision_border_' + sd, False)
    except Exception: pass
DISS = int(E('DISS', '0')); ds.use_dissolve_smoke = DISS > 0
if DISS > 0: ds.dissolve_speed = DISS; ds.use_dissolve_smoke_log = False
ds.cache_directory = os.path.join(OUT, 'cache'); os.makedirs(ds.cache_directory, exist_ok=True)
ds.cache_frame_start, ds.cache_frame_end = 1, TF
try: ds.cache_type = 'ALL'
except Exception: pass

# --- Material: Farbe aus dem Rauch-Farbattribut, Absorption nach Pigmentfarbe, Korn
m = bpy.data.materials.new('Rauch'); m.use_nodes = True; nt = m.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new('ShaderNodeOutputMaterial'); pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Anisotropy'].default_value = 0.3
ac_ = nt.nodes.new('ShaderNodeAttribute'); ac_.attribute_name = 'color'
sepc = nt.nodes.new('ShaderNodeSeparateColor')
mxa = nt.nodes.new('ShaderNodeMath'); mxa.operation = 'MAXIMUM'
mxb = nt.nodes.new('ShaderNodeMath'); mxb.operation = 'MAXIMUM'
mxc = nt.nodes.new('ShaderNodeMath'); mxc.operation = 'MAXIMUM'; mxc.inputs[1].default_value = 0.001
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'DIVIDE'; inv.inputs[0].default_value = 1.0
nrm = nt.nodes.new('ShaderNodeVectorMath'); nrm.operation = 'SCALE'
ab1 = nt.nodes.new('ShaderNodeVectorMath'); ab1.operation = 'SCALE'; ab1.inputs['Scale'].default_value = 0.8
ab2 = nt.nodes.new('ShaderNodeVectorMath'); ab2.operation = 'ADD'; ab2.inputs[1].default_value = (0.2, 0.2, 0.2)
nt.links.new(ac_.outputs['Color'], sepc.inputs['Color'])
nt.links.new(sepc.outputs['Red'], mxa.inputs[0]); nt.links.new(sepc.outputs['Green'], mxa.inputs[1])
nt.links.new(mxa.outputs[0], mxb.inputs[0]); nt.links.new(sepc.outputs['Blue'], mxb.inputs[1])
nt.links.new(mxb.outputs[0], mxc.inputs[0]); nt.links.new(mxc.outputs[0], inv.inputs[1])
nt.links.new(ac_.outputs['Color'], nrm.inputs[0]); nt.links.new(inv.outputs[0], nrm.inputs['Scale'])
nt.links.new(nrm.outputs[0], ab1.inputs[0]); nt.links.new(ab1.outputs[0], ab2.inputs[0])
nt.links.new(ac_.outputs['Color'], pv.inputs['Color']); nt.links.new(ab2.outputs[0], pv.inputs['Absorption Color'])
ad = nt.nodes.new('ShaderNodeAttribute'); ad.attribute_name = 'density'; tc = nt.nodes.new('ShaderNodeTexCoord')
def noise(scale, amp):
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    ga = nt.nodes.new('ShaderNodeMath'); ga.operation = 'MULTIPLY_ADD'; ga.use_clamp = True; ga.inputs[1].default_value = 1.6 * amp; ga.inputs[2].default_value = 1.0 - 0.8 * amp
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], ga.inputs[0]); return ga
g1, g2 = noise(float(E('G1S', '45')), float(E('G1A', '1.2'))), noise(float(E('G2S', '150')), float(E('G2A', '0.8')))
m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; nt.links.new(ad.outputs['Fac'], m1.inputs[0]); nt.links.new(g1.outputs[0], m1.inputs[1])
m2_ = nt.nodes.new('ShaderNodeMath'); m2_.operation = 'MULTIPLY'; nt.links.new(m1.outputs[0], m2_.inputs[0]); nt.links.new(g2.outputs[0], m2_.inputs[1])
fade = nt.nodes.new('ShaderNodeValue'); BASE = float(E('DENS', '60'))
m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; nt.links.new(m2_.outputs[0], m3.inputs[0]); nt.links.new(fade.outputs[0], m3.inputs[1])
nt.links.new(m3.outputs[0], pv.inputs['Density']); nt.links.new(pv.outputs['Volume'], out.inputs['Volume'])
dom.data.materials.append(m)
F0, F1 = int(E('FADE0', str(TF - 28))), int(E('FADE1', str(TF)))   # weiches Ausblenden am Ende (nur Gesamt, kein Dissolve)
for fr, v in ((1, BASE), (F0, BASE), (F1, 0.0)):
    fade.outputs[0].default_value = v; fade.outputs[0].keyframe_insert('default_value', frame=fr)

# --- Quellen: Stern aus Kern, Strahlen, duennen schnellen Strahlen und langen Fahnen (alle mit Farbe des Schlags)
VEL = float(E('VEL', '14')); rng = random.Random(7)
def quelle(name, r, loc, vel, vnorm, dens, start, frames, col):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=12, ring_count=6); o = bpy.context.active_object; o.name = name
    mf = o.modifiers.new('fluid', 'FLUID'); mf.fluid_type = 'FLOW'; fs = mf.flow_settings
    fs.flow_type = 'SMOKE'; fs.flow_behavior = 'INFLOW'; fs.flow_source = 'MESH'; fs.smoke_color = col; fs.density = dens; fs.surface_distance = 1.0
    fs.use_initial_velocity = True; fs.velocity_normal = vnorm; fs.velocity_coord = vel
    if start > 1: fs.use_inflow = False; fs.keyframe_insert('use_inflow', frame=1)
    fs.use_inflow = True; fs.keyframe_insert('use_inflow', frame=start)
    fs.use_inflow = False; fs.keyframe_insert('use_inflow', frame=start + frames)
    o.hide_render = True
NJ, NT, NL = int(E('NR', '12')), int(E('NT', '16')), int(E('NL', '14'))
for hi, h in enumerate(HITS):
    px, py = h['p']; fi = h['f']; col = h['col']; sz = h['sz']; rng = random.Random(7 + hi)
    CR = float(E('CORER', '0.26')) * sz; CD = float(E('COREDENS', '2.2')); CV = VEL * 0.22
    for ci in range(10):
        a_, b_, c_ = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.4, 0.4); nn = max(math.sqrt(a_ * a_ + b_ * b_), 1e-3)
        quelle('K%d_%d' % (hi, ci), CR * rng.uniform(0.4, 0.7), (px + a_ / nn * CR * 0.8 * rng.random(), py + b_ / nn * CR * 0.8 * rng.random(), 0.14 + c_ * 0.05), (0, 0, -VEL * 0.15), CV * rng.uniform(0.6, 1.4), CD * rng.uniform(0.8, 1.2), fi, 6 + rng.randint(-2, 2), col)
    BV = [rng.uniform(0.55, 1.5) * (1.0 + 0.5 * (rng.random() < 0.25)) for _ in range(NJ // 2)]
    for j in range(NJ):
        a = 2 * math.pi * (j + rng.uniform(-0.35, 0.35)) / NJ; v = VEL * BV[j % (NJ // 2)] * rng.uniform(0.88, 1.12)
        quelle('S%d_%d' % (hi, j), 0.06, (px + math.cos(a) * 0.05, py + math.sin(a) * 0.05, 0.12), (math.cos(a) * v, math.sin(a) * v, -0.25 * v), 0.0, float(E('JETDENS', '2.0')), fi, 2, col)
    for j in range(NT):   # duenne, schnelle Strahlen (Fasern)
        a = 2 * math.pi * (j + rng.uniform(-0.5, 0.5)) / NT; v = VEL * rng.uniform(1.4, 2.6)
        quelle('T%d_%d' % (hi, j), 0.035, (px + math.cos(a) * 0.05, py + math.sin(a) * 0.05, 0.10), (math.cos(a) * v, math.sin(a) * v, -0.10 * v), 0.0, float(E('THIND', '1.4')), fi, 2, col)
    for j in range(NL):   # lange Fahnen bis weit ueber das Quadrat
        a = 2 * math.pi * (j + rng.uniform(-0.4, 0.4)) / NL; v = VEL * rng.uniform(2.2, 3.6)
        quelle('L%d_%d' % (hi, j), 0.035, (px + math.cos(a) * 0.06, py + math.sin(a) * 0.06, 0.10), (math.cos(a) * v, math.sin(a) * v, -0.05 * v * rng.uniform(0, 1)), 0.0, float(E('NLD', '1.2')), fi, 3, col)

t0 = time.time()
bpy.context.view_layer.objects.active = dom; dom.select_set(True)
bpy.ops.fluid.bake_data(); print('BAKE_SEKUNDEN', round(time.time() - t0, 1), flush=True)
FL = [int(v) for v in E('FRAMES').split(',') if v.strip()] if E('FRAMES') else list(range(1, TF + 1))
os.makedirs(os.path.join(OUT, 'f'), exist_ok=True)
for f in FL:
    t1 = time.time(); sc.frame_set(f); set_deposit(f); set_particles(f); sc.render.filepath = os.path.join(OUT, 'f', 'f_%04d.png' % f); bpy.ops.render.render(write_still=True)
    print('BILD', f, round(time.time() - t1, 1), 's', flush=True)
HDF = int(E('HDFRAME', '0'))
if HDF:
    t1 = time.time(); sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.cycles.samples = int(E('HDSPP', '64')); sc.frame_set(HDF); set_deposit(HDF); set_particles(HDF)
    sc.render.filepath = os.path.join(OUT, 'hd.png'); bpy.ops.render.render(write_still=True); print('HD', HDF, round(time.time() - t1, 1), 's', flush=True)
json.dump({'einschlag_bilder': [h['f'] for h in HITS], 'fps': 24, 'film_offset': OFF}, open(os.path.join(OUT, 'timing.json'), 'w'))
print('GESAMT_SEKUNDEN', round(time.time() - t0, 1), flush=True)
