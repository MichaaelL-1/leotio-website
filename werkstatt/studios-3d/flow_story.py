# Leotio Studios Flow-Story v0.1 · 28.11.2026: alle 6 Wuerfe aus takt-a8.json als Mantaflow-Rauch (eine Domain je Wurf), Wurf von der Seite, Zeitlupe im Einschlag, gestaffelte Groessen, weiches Licht, Tiefenschaerfe. Basis: flow_test.py v0.4 (Runde 9).
# Aufruf: blender -b --python flow_story.py -- AUSGABEORDNER [bake|render|all]
# Umgebung (optional): TF=228 Bilder (24 fps)  RES=160  RX=640 RY=360 SPP=16  SIM=<simT_a8e>  HITS=0,1,2,3,4,5 (Auswahl)  FRAMES=Liste (nur diese Bilder rendern)
#   SF=4 Anlaufbilder (Strom von der Seite)  WIN=50 Fenster je Domain  SLOW=0.35 Zeitlupenfaktor  SLOWF=12 Zeitlupenbilder  DOFN=0.15  DW=3.2 DH=1.2
import bpy, math, os, sys, time, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene
from mathutils import Vector
E = os.environ.get
arg = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(arg[0]); MODE = arg[1] if len(arg) > 1 else 'all'
os.makedirs(OUT, exist_ok=True)
TF = int(E('TF', '228')); RX, RY = int(E('RX', '640')), int(E('RY', '360'))
sc, cam = scene.build(28.0, (RX, RY), int(E('SPP', '16')))
sc.render.fps = 24; sc.frame_start = 1; sc.frame_end = TF
SIM = E('SIM', '')
TAKT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), E('TAKT', 'takt-a8.json')), encoding='utf-8'))
PAL = ['E3A21A', '2F8FC4', '23379A', '7B3F98', 'CC2E2A']
def lin3(h): return [(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)]

# --- Licht und Kamera: weiches Studiolicht (hohe, grosse Sonne = kurze weiche Schatten), Tiefenschaerfe
for o_ in bpy.data.objects:
    if o_.type == 'LIGHT':
        el, az = math.radians(float(E('SUNEL', '62'))), math.radians(135)
        d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        o_.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); o_.data.energy = float(E('SUNE', '2.6')); o_.data.angle = math.radians(float(E('SUNA', '25'))); o_.data.color = (1, 1, 1)
wn = sc.world.node_tree.nodes['Background']; wn.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1)
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = cam.location.z; cam.data.dof.aperture_fstop = float(E('DOFN', '0.15'))
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.cycles.volume_bounces = 8; sc.cycles.max_bounces = max(sc.cycles.max_bounces, 8)

# --- Papier: groeberes Korn
pap = bpy.data.materials['Papier']; pn = pap.node_tree; pb = pn.nodes['Principled BSDF']
for n_ in pn.nodes:
    if n_.type == 'TEX_NOISE' and n_.inputs['Scale'].default_value > 500: n_.inputs['Scale'].default_value = float(E('PGRAIN', '350'))
    if n_.type == 'BUMP': n_.inputs['Strength'].default_value = float(E('PBUMP', '0.14'))
# --- Liegender Puder: Deposit aus der Simulation, alle Schlaege (nur im Quadrat, Rillen frei), gleiche Abbildung wie render.py
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
    pn.links.new(imgD.outputs['Alpha'], mx.inputs['Factor']); pn.links.new(gn_.outputs['Result'], mx.inputs['B']); pn.links.new(mx.outputs['Result'], pb.inputs['Base Color'])
def set_deposit(f):
    if imgD is None: return
    pth = os.path.join(SIM, 'dep_%04d.png' % min(2 * (f - 1), 575))   # Filmbild n = f-1, Sim-Bild = 2n
    if os.path.exists(pth):
        if imgD.image: bpy.data.images.remove(imgD.image)
        imgD.image = bpy.data.images.load(pth); imgD.image.colorspace_settings.name = 'sRGB'

# --- Wuerfe
RES = int(E('RES', '160')); DW = float(E('DW', '3.2')); DH = float(E('DH', '1.2')); SF = int(E('SF', '4')); WIN = int(E('WIN', '50'))
SLOW = float(E('SLOW', '0.35')); SLOWF = int(E('SLOWF', '12')); DISS = int(E('DISS', '36'))
SZ = [float(v) for v in E('SZ', '1.0,0.75,1.15,0.9,1.15,0.45').split(',')]                 # gestaffelte Groessen je Wurf
THROW = [float(v) for v in E('THROW', '-20,160,75,-110,20,250').split(',')]                # Wurfrichtung in Grad (Bewegungsrichtung), 6. aus wd
hits = TAKT['hits']; SEL = [int(v) for v in E('HITS', ','.join(str(i) for i in range(len(hits)))).split(',')]
fi_ = [int(round(h['t'] * 24)) + 1 for h in hits]   # Einschlagbild (1-basiert)
def bound(i):   # Fenster einer Domain: vom Anlauf bis kurz vor dem Anlauf des naechsten Wurfs (keine Fremd-Emission)
    s = max(1, fi_[i] - SF - 1); e = fi_[i] + WIN
    if i + 1 < len(hits): e = min(e, fi_[i + 1] - SF - 2)
    return s, min(e, TF)
doms = {}
def material(i, name):
    c = PAL[hits[i]['c']]; L = lin3(c)
    yellow = hits[i]['c'] == 0
    cm = [1, 0.65, 0.3] if yellow else [1, 1, 1]; mx_ = max(L)
    ac = [0.92, 0.7, 0.2] if yellow else [1 - 0.8 * (1 - l / mx_) for l in L]   # Absorption nach Pigmentfarbe: Rest-Kanaele werden geschluckt, Schatten bleiben neutral
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); pv = nt.nodes.new('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = tuple(l * k for l, k in zip(L, cm)) + (1,); pv.inputs['Anisotropy'].default_value = 0.3
    try: pv.inputs['Absorption Color'].default_value = tuple(ac) + (1,)
    except Exception: pass
    ad = nt.nodes.new('ShaderNodeAttribute'); ad.attribute_name = 'density'; tc = nt.nodes.new('ShaderNodeTexCoord')
    def noise(scale, amp):
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
        ga = nt.nodes.new('ShaderNodeMath'); ga.operation = 'MULTIPLY_ADD'; ga.use_clamp = True; ga.inputs[1].default_value = 1.6 * amp; ga.inputs[2].default_value = 1.0 - 0.8 * amp
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], ga.inputs[0]); return ga
    g1, g2 = noise(40, 1.0), noise(130, 0.7)
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; nt.links.new(ad.outputs['Fac'], m1.inputs[0]); nt.links.new(g1.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(g2.outputs[0], m2.inputs[1])
    fade = nt.nodes.new('ShaderNodeValue'); fade.name = 'fade'; fade.outputs[0].default_value = float(E('DENS', '100'))
    m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; nt.links.new(m2.outputs[0], m3.inputs[0]); nt.links.new(fade.outputs[0], m3.inputs[1])
    nt.links.new(m3.outputs[0], pv.inputs['Density']); nt.links.new(pv.outputs['Volume'], out.inputs['Volume'])
    return m, fade
def quelle(dom, name, r, loc, vel, vnorm, dens, start, frames, scale_key=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=16, ring_count=8); o = bpy.context.active_object; o.name = name
    mf = o.modifiers.new('fluid', 'FLUID'); mf.fluid_type = 'FLOW'; fs = mf.flow_settings
    fs.flow_type = 'SMOKE'; fs.flow_behavior = 'INFLOW'; fs.flow_source = 'MESH'; fs.smoke_color = lin3(PAL[0]); fs.density = dens; fs.surface_distance = 1.0
    fs.use_initial_velocity = True; fs.velocity_normal = vnorm; fs.velocity_coord = vel
    if start > 1: fs.use_inflow = False; fs.keyframe_insert('use_inflow', frame=1)
    fs.use_inflow = True; fs.keyframe_insert('use_inflow', frame=start)
    fs.use_inflow = False; fs.keyframe_insert('use_inflow', frame=start + frames)
    o.hide_render = True
    return o
def build_hit(i):
    h = hits[i]; px, py = h['p']; rng = random.Random(7 + i); fi = fi_[i]; s, e = bound(i)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, DH / 2)); dom = bpy.context.active_object; dom.name = 'Domain%d' % i
    dom.scale = (DW, DW, DH)
    md = dom.modifiers.new('fluid', 'FLUID'); md.fluid_type = 'DOMAIN'; ds = md.domain_settings
    ds.domain_type = 'GAS'; ds.resolution_max = RES; ds.use_noise = False; ds.vorticity = float(E('VORT', '0.9')); ds.alpha = float(E('SINK', '1.5')); ds.beta = 0.0
    ds.use_collision_border_bottom = True
    for sd in ('top', 'front', 'back', 'left', 'right'):
        try: setattr(ds, 'use_collision_border_' + sd, False)
        except Exception: pass
    ds.use_dissolve_smoke = True; ds.dissolve_speed = DISS; ds.use_dissolve_smoke_log = False
    ds.cache_directory = os.path.join(OUT, 'cache', 'h%d' % i); os.makedirs(ds.cache_directory, exist_ok=True)
    ds.cache_frame_start, ds.cache_frame_end = s, e
    try: ds.cache_type = 'ALL'
    except Exception: pass
    # Zeitlupe im Einschlag: Stoss schnell, dann SLOWF Bilder verlangsamt, danach normal
    ds.time_scale = 1.0
    if E('NOSLOW') != '1':
        for fr, v in ((s, 1.0), (fi + 2, 1.0), (fi + 3, SLOW), (fi + 3 + SLOWF, SLOW), (fi + 4 + SLOWF, 1.0)):
            ds.time_scale = v; ds.keyframe_insert('time_scale', frame=fr)
    m, fade = material(i, 'Rauch%d' % i); dom.data.materials.append(m)
    base = float(E('DENS', '100')); fade.outputs[0].default_value = base
    for fr, v in ((1, base), (e - 8, base), (e, 0.0)):   # Ausblenden am Fensterende (verhindert hartes Abschneiden)
        fade.outputs[0].default_value = v; fade.outputs[0].keyframe_insert('default_value', frame=fr)
    # Sichtbarkeit der Domain nur im Fenster
    dom.hide_render = True; dom.keyframe_insert('hide_render', frame=1)
    dom.hide_render = False; dom.keyframe_insert('hide_render', frame=s)
    dom.hide_render = True; dom.keyframe_insert('hide_render', frame=e + 1)
    # Wurfrichtung, Strom von der Seite, Einschlag
    th = math.radians(THROW[i] if i < len(THROW) else 0.0)
    if h.get('wd'): th = math.radians(h['wd'][0])
    dv = (math.cos(th), math.sin(th)); sz = SZ[i] if i < len(SZ) else 1.0
    VEL = float(E('VEL', '17')) * (0.85 + 0.15 * sz); SL = float(E('STREAML', '0.9'))
    st = quelle(dom, 'Strom%d' % i, 0.07, (px - dv[0] * SL, py - dv[1] * SL, 0.15), (dv[0] * VEL * 0.9, dv[1] * VEL * 0.9, -0.1 * VEL), 0.0, float(E('STREAMD', '2.0')), max(1, fi - SF), SF + 1)
    st.location = (px - dv[0] * SL, py - dv[1] * SL, 0.15); st.keyframe_insert('location', frame=max(1, fi - SF))
    st.location = (px, py, 0.13); st.keyframe_insert('location', frame=fi)
    CR = float(E('CORER', '0.28')) * sz; CD = float(E('COREDENS', '2.5')); CV = VEL * 0.22
    for ci in range(int(E('CORECL', '9'))):
        a_, b_, c_ = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.4, 0.4); nn = max(math.sqrt(a_ * a_ + b_ * b_), 1e-3)
        quelle(dom, 'Kern%d_%d' % (i, ci), CR * rng.uniform(0.4, 0.7), (px + a_ / nn * CR * 0.8 * rng.random(), py + b_ / nn * CR * 0.8 * rng.random(), 0.14 + c_ * 0.05),
               (dv[0] * VEL * 0.25, dv[1] * VEL * 0.25, -VEL * 0.15), CV * rng.uniform(0.6, 1.4), CD * rng.uniform(0.8, 1.2), fi, 6 + rng.randint(-2, 2))
    NR = int(E('NR', '12')); BASEV = [rng.uniform(0.55, 1.5) * (1.0 + 0.5 * (rng.random() < 0.25)) for _ in range(NR // 2)]
    for j in range(NR):
        a = 2 * math.pi * (j + rng.uniform(-0.35, 0.35)) / NR; v = VEL * BASEV[j % (NR // 2)] * rng.uniform(0.88, 1.12) * (1 + 0.55 * math.cos(a - th))   # in Wurfrichtung staerker
        quelle(dom, 'Strahl%d_%d' % (i, j), 0.07, (px + math.cos(a) * 0.05, py + math.sin(a) * 0.05, 0.12), (math.cos(a) * v, math.sin(a) * v, -0.25 * v), 0.0, float(E('JETDENS', '2.2')), fi, 2)
    doms[i] = dom
for i in SEL: build_hit(i)

# --- Auswertung: Bake je Domain, Render
t0 = time.time()
if MODE in ('bake', 'all'):
    for i in SEL:
        bpy.context.view_layer.objects.active = doms[i]
        for o_ in bpy.context.selected_objects: o_.select_set(False)
        doms[i].select_set(True)
        t1 = time.time(); bpy.ops.fluid.bake_data(); print('BAKE', i, round(time.time() - t1, 1), 's', flush=True)
if MODE in ('render', 'all'):
    FL = [int(v) for v in E('FRAMES').split(',')] if E('FRAMES') else list(range(1, TF + 1))
    os.makedirs(os.path.join(OUT, 'f'), exist_ok=True)
    for f in FL:
        t1 = time.time(); sc.frame_set(f); set_deposit(f); sc.render.filepath = os.path.join(OUT, 'f', 'f_%04d.png' % f); bpy.ops.render.render(write_still=True)
        print('BILD', f, round(time.time() - t1, 1), 's', flush=True)
    if imgD is not None:   # Maske-Referenz: leeres Papier ohne Deposit
        leer = bpy.data.images.new('leer', 4, 4, alpha=True); leer.pixels = [0.0] * (4 * 4 * 4); leer.colorspace_settings.name = 'sRGB'
        if imgD.image: bpy.data.images.remove(imgD.image)
        imgD.image = leer
    for f in (1,): sc.frame_set(1); sc.render.filepath = os.path.join(OUT, 'plate.png'); bpy.ops.render.render(write_still=True)   # leeres Papier ohne Deposit fuer die Maske
    json.dump({'einschlagbilder': fi_, 'einschlag_s': [(f - 1) / 24.0 for f in fi_], 'anlauf_bilder': SF, 'fps': 24}, open(os.path.join(OUT, 'timing.json'), 'w'))
print('GESAMT_SEKUNDEN', round(time.time() - t0, 1), flush=True)
