# Leotio Studios Flow-Test v0.5 · 28.11.2026: S0 (Einschlagbild, Vorlauf), RING (Staubring vorher), JZ (Strahlen steiler), SZM (Groessenfaktor), DDELAY (Belag erst spaeter); Standardwerte = Runde 9 (v0.4); v0.4: Deposit-Farbe repariert, FRAMES-Liste, feiner Staub statt grosser Koerner; v0.3: Nahbereich-Maszstab (wenige grosse Koepfe, grobe Koerner aus simT_a8e, Tiefenschaerfe, Bewegungsunschaerfe, schnellerer Stoss/Absetzen); dicker/opaker (mehr Dichte, laengere Quelle), neutrales weisses Licht, symmetrische Strahlen (weniger Drift), Deposit waechst mit dem Aufprall, Domain strikt im Quadrat; v0.2: GRAIN (Korn in der Dichte), mehr Aufloesung moeglich; v0.1: Mantaflow-Rauch fuer genau einen Schlag (Schlag 1, Gelb #E3A21A, p=[-0.5,0.42] aus takt-a8.json)
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
H = float(E('DH', '0.55')); DW = float(E('DW', '1.80'))   # Domain etwas kleiner als das Quadrat (2 m), weil die Kamera von oben mit Perspektive hohe Schichten nach aussen schiebt
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H / 2)); dom = bpy.context.active_object; dom.name = 'Domain'
dom.scale = (DW, DW, H)
md = dom.modifiers.new('fluid', 'FLUID'); md.fluid_type = 'DOMAIN'; ds = md.domain_settings
ds.domain_type = 'GAS'; ds.resolution_max = int(E('RES', '96'))
ds.use_noise = int(E('NOISE', '2')) > 0
if ds.use_noise: ds.noise_scale = int(E('NOISE', '2')); ds.noise_strength = float(E('NSCALE', '2.0')) * 0.5
ds.vorticity = float(E('VORT', '0.25'))
ds.alpha = float(E('SINK', '2.5')); ds.beta = 0.0
DISS = int(E('DISS', '0'))   # v0.4: Rauch loest sich linear ueber DISS Bilder auf (0 = nie), gegen grauen Restdunst
ds.use_dissolve_smoke = DISS > 0
if DISS > 0: ds.dissolve_speed = DISS; ds.use_dissolve_smoke_log = False
ds.time_scale = float(E('TS', '1.8'))   # Nahbereich: schneller Stoss und schnelleres Absetzen   # v0.3: Rauch loest sich nicht auf, Koepfe bleiben dicht
ds.use_collision_border_bottom = True
for s in ('top', 'front', 'back', 'left', 'right'):
    try: setattr(ds, 'use_collision_border_' + s, False)
    except Exception: pass
ds.cache_directory = os.path.join(OUT, 'cache'); os.makedirs(OUT, exist_ok=True)
ds.cache_frame_start, ds.cache_frame_end = 1, FR
try: ds.cache_type = 'ALL'
except Exception: pass

# Quelle (v0.2): dichter Kern + NR Strahlen (Finger) mit ungleicher Geschwindigkeit je Richtung, harter Stoss in den ersten 2 Bildern
import random
rng = random.Random(int(E('SEED', '7')))
VEL = float(E('VEL', '16')); NR = int(E('NR', '8')); BC = int(E('BURSTC', '9')); BJ = int(E('BURSTJ', '3'))
S0 = int(E('S0', '1')); SZM = float(E('SZM', '1.0')); JZ = float(E('JZ', '-0.25')); ST = 0
def quelle(name, r, loc, vel, vnorm, dens, frames):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=16, ring_count=8); o = bpy.context.active_object; o.name = name
    mf = o.modifiers.new('fluid', 'FLUID'); mf.fluid_type = 'FLOW'; fs = mf.flow_settings
    fs.flow_type = 'SMOKE'; fs.flow_behavior = 'INFLOW'; fs.flow_source = 'MESH'
    fs.smoke_color = lin; fs.density = dens; fs.surface_distance = 1.0
    fs.use_initial_velocity = True; fs.velocity_normal = vnorm; fs.velocity_coord = vel
    if S0 > 1: fs.use_inflow = False; fs.keyframe_insert('use_inflow', frame=1)
    fs.use_inflow = True; fs.keyframe_insert('use_inflow', frame=ST if ST else S0)
    fs.use_inflow = False; fs.keyframe_insert('use_inflow', frame=(ST if ST else S0) + frames)
    o.hide_render = True
BASEV = [rng.uniform(0.55, 1.5) * (1.0 + 0.5 * (rng.random() < 0.25)) for _ in range(NR // 2)]   # einzelne Strahlen schiessen weit vor
CL = int(E('CORECL', '1'))   # v0.4: Kern als unregelmaessiger Haufen kleiner Quellen statt einer glatten Kugel
CR = float(E('CORER', '0.20')); CD = float(E('COREDENS', '4.0')); CV = VEL * float(E('COREV', '0.22'))
if CL <= 1:
    quelle('Kern', CR, (px, py, 0.14), (0, 0, -VEL * 0.15), CV, CD, BC)
else:
    for ci in range(CL):
        a_, b_, c_ = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.4, 0.4); nn = max(math.sqrt(a_ * a_ + b_ * b_), 1e-3)
        quelle('Kern%d' % ci, CR * rng.uniform(0.4, 0.7), (px + a_ / nn * CR * 0.8 * rng.random(), py + b_ / nn * CR * 0.8 * rng.random(), 0.14 + c_ * 0.05), (0, 0, -VEL * 0.15), CV * rng.uniform(0.6, 1.4), CD * rng.uniform(0.8, 1.2), BC + rng.randint(-2, 2))
for i in range(NR):
    th = 2 * math.pi * (i + rng.uniform(-0.35, 0.35)) / NR
    base = BASEV[i % (NR // 2)]   # Gegenueber-Paare teilen die Grundgeschwindigkeit: kein Drift in eine Richtung
    v = VEL * base * rng.uniform(0.88, 1.12)
    quelle('Strahl%d' % i, 0.07 * SZM, (px + math.cos(th) * 0.05, py + math.sin(th) * 0.05, 0.12), (math.cos(th) * v, math.sin(th) * v, JZ * v), 0.0, float(E('JETDENS', '3.5')), BJ)
if E('RING', '0') == '1':   # Vorbote: feiner Staubring 3 Bilder vor dem Durchbruch (ohne Zufallszahlen, Rest bleibt wie Runde 9)
    ST = max(1, S0 - 3)
    for k in range(10):
        a = 2 * math.pi * k / 10
        quelle('Ring%d' % k, 0.03, (px + math.cos(a) * 0.08, py + math.sin(a) * 0.08, 0.03), (math.cos(a) * VEL * 0.25, math.sin(a) * VEL * 0.25, VEL * 0.03), 0.0, float(E('RINGD', '0.5')), 3)
    ST = 0

# Material der Domain: Principled Volume, Dichte und Farbe aus dem Rauch
m = bpy.data.materials.new('Rauch'); m.use_nodes = True; nt = m.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new('ShaderNodeOutputMaterial'); pv = nt.nodes.new('ShaderNodeVolumePrincipled')
ad = nt.nodes.new('ShaderNodeAttribute'); ad.attribute_name = 'density'
ac = nt.nodes.new('ShaderNodeAttribute'); ac.attribute_name = 'color'
mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = float(E('DENS', '25'))
G = float(E('GRAIN', '0'))   # v0.2: Korn/raue Raender: Dichte wird mit einem feinen 3D-Noise moduliert (0 = aus)
if G > 0:
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = float(E('GSCALE', '90')); nz.inputs['Detail'].default_value = 8
    ga = nt.nodes.new('ShaderNodeMath'); ga.operation = 'MULTIPLY_ADD'; ga.use_clamp = True; ga.inputs[1].default_value = 1.6 * G; ga.inputs[2].default_value = 1.0 - 0.8 * G
    gm = nt.nodes.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], ga.inputs[0])
    nt.links.new(ad.outputs['Fac'], gm.inputs[0]); nt.links.new(ga.outputs[0], gm.inputs[1])
    G2 = float(E('G2', '0'))   # v0.4: zweiter, feinerer Rauschmassstab gegen glatte Knet-Oberflaeche
    if G2 > 0:
        nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = float(E('G2SCALE', '160')); nz2.inputs['Detail'].default_value = 6
        ga2 = nt.nodes.new('ShaderNodeMath'); ga2.operation = 'MULTIPLY_ADD'; ga2.use_clamp = True; ga2.inputs[1].default_value = 1.4 * G2; ga2.inputs[2].default_value = 1.0 - 0.7 * G2
        gm2 = nt.nodes.new('ShaderNodeMath'); gm2.operation = 'MULTIPLY'
        nt.links.new(tc.outputs['Object'], nz2.inputs['Vector']); nt.links.new(nz2.outputs['Fac'], ga2.inputs[0]); nt.links.new(gm.outputs[0], gm2.inputs[0]); nt.links.new(ga2.outputs[0], gm2.inputs[1]); nt.links.new(gm2.outputs[0], mu.inputs[0])
    else:
        nt.links.new(gm.outputs[0], mu.inputs[0])
else:
    nt.links.new(ad.outputs['Fac'], mu.inputs[0])
nt.links.new(mu.outputs[0], pv.inputs['Density'])
if E('CATTR', '0') == '1': nt.links.new(ac.outputs['Color'], pv.inputs['Color'])   # Farb-Attribut des Rauchs (wirkt dunkel/oliv), Standard: feste Pulverfarbe
else: pv.inputs['Color'].default_value = tuple(l * m for l, m in zip(lin, [float(v) for v in E('COLMUL', '1,0.85,1').split(',')])) + (1,)   # Mehrfachstreuung + blaues Umgebungslicht kippen Gelb nach Gruen: Gruen-Anteil daempfen
pv.inputs['Anisotropy'].default_value = 0.3
AC = [float(v) for v in E('ABSCOL', '0.95,0.85,0.2').split(',')]   # v0.3: Absorptionsfarbe: Blau wird geschluckt (wie echtes Gelbpigment), Rot/Gruen kaum -> Schatten neutral bis warm statt blau
try: pv.inputs['Absorption Color'].default_value = tuple(AC) + (1,)
except Exception: pass
try:
    pv.inputs['Emission Strength'].default_value = float(E('EMIT', '0.0')); pv.inputs['Emission Color'].default_value = (*lin, 1)
except Exception: pass
nt.links.new(pv.outputs['Volume'], out.inputs['Volume'])
dom.data.materials.append(m)

# Liegende Farbe (v0.2): Deposit-Textur aus der Simulation (nur bis vor Schlag 2), gleiche Abbildung wie render.py
SIM = E('SIM', '')
pap = bpy.data.materials['Papier']; pn = pap.node_tree; pb = pn.nodes['Principled BSDF']
imgD = None
if SIM:
    gg = pn.nodes.new('ShaderNodeNewGeometry'); sp = pn.nodes.new('ShaderNodeSeparateXYZ'); pn.links.new(gg.outputs['Position'], sp.inputs[0])
    def lm(inp, mul, add):
        mm = pn.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY_ADD'; mm.inputs[1].default_value = mul; mm.inputs[2].default_value = add; pn.links.new(inp, mm.inputs[0]); return mm
    ux, uy = lm(sp.outputs['X'], 0.5, 0.5), lm(sp.outputs['Y'], 0.5, 0.5)
    cb = pn.nodes.new('ShaderNodeCombineXYZ'); pn.links.new(ux.outputs[0], cb.inputs['X']); pn.links.new(uy.outputs[0], cb.inputs['Y'])
    imgD = pn.nodes.new('ShaderNodeTexImage'); imgD.extension = 'CLIP'; pn.links.new(cb.outputs[0], imgD.inputs['Vector'])
    gn_ = pn.nodes.new('ShaderNodeMix'); gn_.data_type = 'RGBA'; gn_.blend_type = 'MULTIPLY'; gn_.inputs['Factor'].default_value = 1.0
    gn_.inputs['B'].default_value = tuple(float(E('DGAIN', '1.2')) * float(v) for v in E('DCOLMUL', '1,1,1').split(',')) + (1,)
    pn.links.new(imgD.outputs['Color'], gn_.inputs['A'])   # v0.4: Link war in v0.3 im Kommentar verschwunden (Deposit grau)
    mx = pn.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.90, 0.905, 0.905, 1)
    dr = pn.nodes.new('ShaderNodeValue'); dr.outputs[0].default_value = 0.0
    da = pn.nodes.new('ShaderNodeMath'); da.operation = 'MULTIPLY'; pn.links.new(imgD.outputs['Alpha'], da.inputs[0]); pn.links.new(dr.outputs[0], da.inputs[1])
    pn.links.new(da.outputs[0], mx.inputs['Factor']); pn.links.new(gn_.outputs['Result'], mx.inputs['B']); pn.links.new(mx.outputs['Result'], pb.inputs['Base Color'])
def set_deposit(f):
    if imgD is None: return
    dr.outputs[0].default_value = max(0.0, min(1.0, (f - S0 - float(E('DDELAY', '0'))) / float(E('DRAMP', '14')))) ** 1.5   # Deposit waechst erst mit dem Aufprall (Bild 1 = Stoss)
    k = min(int(E('DEP0', '60')) + 2 * max(f - S0, 0), int(E('DEP1', '110')))   # Sim-Bild: Schlag 1 bei Sim-Bild 60, Schlag 2 ab 112
    pth = os.path.join(SIM, 'dep_%04d.png' % k)
    if os.path.exists(pth):
        if imgD.image: bpy.data.images.remove(imgD.image)
        imgD.image = bpy.data.images.load(pth); imgD.image.colorspace_settings.name = 'sRGB'

cam.data.dof.use_dof = True; cam.data.dof.focus_distance = cam.location.z; cam.data.dof.aperture_fstop = float(E('DOFN', '0.25'))   # Fokus auf Papier, Wolke nahe der Kamera unscharf
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = float(E('MBLUR', '0.5'))
wn = sc.world.node_tree.nodes['Background']; wn.inputs['Color'].default_value = (0.80, 0.80, 0.80, 1)   # v0.3: neutrale Umgebung statt blaulich -> Gelb bleibt gelb, Schatten nicht blau
for o_ in bpy.data.objects:
    if o_.type == 'LIGHT': o_.data.color = (1.0, 1.0, 1.0)
sc.cycles.volume_bounces = int(E('VB', '8')); sc.cycles.max_bounces = max(sc.cycles.max_bounces, int(E('VB', '8')))   # v0.2: Mehrfachstreuung im dichten Pulver (sonst dunkler Kern)

if E('PLATE'):   # Maske: Papier ohne Wolke und ohne Deposit, einmal gerendert
    dom.hide_render = True
    if imgD is not None: dr.outputs[0].default_value = 0.0
    sc.frame_set(1); sc.render.filepath = os.path.join(OUT, 'plate.png'); bpy.ops.render.render(write_still=True); print('PLATE_OK', flush=True); sys.exit(0)

# Grobe Koerner (v0.3): gelbe Partikel aus simT_a8e (Schlag 1), die aus der Wolke fallen
import numpy as np
PR = float(E('PR', '2.5')); PSUB = int(E('PSUB', '2'))
me_p = bpy.data.meshes.new('Koerner'); ob_p = bpy.data.objects.new('Koerner', me_p); bpy.context.collection.objects.link(ob_p)
gt = bpy.data.node_groups.new('KoernerPunkte', 'GeometryNodeTree')
gt.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry'); gt.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi_ = gt.nodes.new('NodeGroupInput'); go_ = gt.nodes.new('NodeGroupOutput'); m2 = gt.nodes.new('GeometryNodeMeshToPoints')
na_ = gt.nodes.new('GeometryNodeInputNamedAttribute'); na_.data_type = 'FLOAT'; na_.inputs['Name'].default_value = 'rad'; sm_ = gt.nodes.new('GeometryNodeSetMaterial')
gt.links.new(gi_.outputs[0], m2.inputs['Mesh']); gt.links.new(na_.outputs['Attribute'], m2.inputs['Radius']); gt.links.new(m2.outputs['Points'], sm_.inputs['Geometry']); gt.links.new(sm_.outputs['Geometry'], go_.inputs[0])
ob_p.modifiers.new('pp', 'NODES').node_group = gt
pm = bpy.data.materials.new('Koerner'); pm.use_nodes = True; pbs = pm.node_tree.nodes['Principled BSDF']
pbs.inputs['Base Color'].default_value = (*lin, 1); pbs.inputs['Roughness'].default_value = 0.9; sm_.inputs['Material'].default_value = pm
def set_particles(f):
    k = min(int(E('DEP0', '60')) + 2 * max(f - S0, 0), 202)
    pth = os.path.join(SIM, 'pts_%04d.npz' % k) if SIM else ''
    me_p.clear_geometry()
    if not pth or not os.path.exists(pth): return
    z = np.load(pth); P = z['p']; C = z['c'].astype(np.float32); R = z['r'].astype(np.float32)
    sel = (C[:, 1] > 0.5) & (C[:, 2] < 0.3) & (np.abs(P[:, 0]) < 0.97) & (np.abs(P[:, 1]) < 0.97)   # nur Gelb (Schlag 1), nur im Quadrat
    idx = np.nonzero(sel)[0][::PSUB]
    if len(idx) == 0: return
    me_p.vertices.add(len(idx)); me_p.vertices.foreach_set('co', P[idx].ravel())
    a_ = me_p.attributes.new('rad', 'FLOAT', 'POINT'); a_.data.foreach_set('value', R[idx] * PR); me_p.update()

t0 = time.time()
if MODE in ('bake', 'all'):
    bpy.context.view_layer.objects.active = dom
    bpy.ops.fluid.bake_data()
    print('BAKE_SEKUNDEN', round(time.time() - t0, 1), flush=True)
    if ds.use_noise:   # Noise-Upres (Blumenkohl-Raender) ist ein eigener Backschritt
        bpy.ops.fluid.bake_noise()
        print('NOISE_SEKUNDEN', round(time.time() - t0, 1), flush=True)
import json
def apply_look(lk):   # v0.4: Look-Varianten (Farbe, Licht, Deposit, Staub) auf demselben Bake, ohne neue Simulation
    global PR, PSUB
    g = lambda k, d: lk.get(k, E(k, d))
    cm = [float(v) for v in str(g('COLMUL', '1,0.75,1')).split(',')]; pv.inputs['Color'].default_value = tuple(l * m for l, m in zip(lin, cm)) + (1,)
    ac = [float(v) for v in str(g('ABSCOL', '0.95,0.85,0.2')).split(',')]
    try: pv.inputs['Absorption Color'].default_value = tuple(ac) + (1,)
    except Exception: pass
    try: pv.inputs['Emission Strength'].default_value = float(g('EMIT', '0.0'))
    except Exception: pass
    mu.inputs[1].default_value = float(g('DENS', '200'))
    w = float(g('WORLD', '0.8')); wn.inputs['Color'].default_value = (w, w, w, 1)
    sunc = [float(v) for v in str(g('SUNC', '1,1,1')).split(',')]
    for o_ in bpy.data.objects:
        if o_.type == 'LIGHT': o_.data.color = tuple(sunc)
    if imgD is not None: gn_.inputs['B'].default_value = tuple(float(g('DGAIN', '1.2')) * float(v) for v in str(g('DCOLMUL', '1,1,1')).split(',')) + (1,)
    PR = float(g('PR', '1.5')); PSUB = int(g('PSUB', '30'))

if MODE in ('render', 'all'):
    LOOKS = json.loads(E('LOOKS', '[{}]'))
    FL = [int(v) for v in E('FRAMES').split(',') if v.strip()] if E('FRAMES') else list(range(RA[0], RA[1] + 1))
    for vi, lk in enumerate(LOOKS):
        apply_look(lk)
        od = OUT if len(LOOKS) == 1 else os.path.join(OUT, 'v%d' % vi)
        os.makedirs(os.path.join(od, 'f'), exist_ok=True)
        for f in FL:
            t1 = time.time(); sc.frame_set(f); set_deposit(f); set_particles(f); sc.render.filepath = os.path.join(od, 'f', 'f_%04d.png' % f)
            bpy.ops.render.render(write_still=True)
            print('BILD', vi, f, round(time.time() - t1, 1), 's', flush=True)
        if E('WITHPLATE', '1') == '1':   # Maske: Papier ohne Wolke/Deposit/Koerner im gleichen Licht
            dom.hide_render = True; me_p.clear_geometry()
            if imgD is not None: dr.outputs[0].default_value = 0.0
            sc.frame_set(1); sc.render.filepath = os.path.join(od, 'plate.png'); bpy.ops.render.render(write_still=True)
            os.makedirs(os.path.join(od, 'pd'), exist_ok=True)   # Referenz fuer die Schattenmessung: Deposit ohne Wolke und ohne Koerner
            dom.hide_render = True; me_p.clear_geometry()
            for f in (12, 23):
                sc.frame_set(f); set_deposit(f); me_p.clear_geometry(); sc.render.filepath = os.path.join(od, 'pd', 'f_%04d.png' % f); bpy.ops.render.render(write_still=True)
            dom.hide_render = False
print('GESAMT_SEKUNDEN', round(time.time() - t0, 1), flush=True)
