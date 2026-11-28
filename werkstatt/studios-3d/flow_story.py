# Leotio Studios Flow-Story v0.4 · 28.11.2026: FADE0/FADE1 weicher Ausblendverlauf statt Mantaflow-Dissolve (verschwand bei schnellen Stoessen in 4 Bildern), Korn-Regler G1A/G1S/G2A/G2S; v0.3: DEPRAMP (Belag waechst erst mit dem Absinken, nur fuer Einzelwurf-Tests), laengeres Stehen (DISS), Licht wie Runde 9; v0.2: ERMODE=wide|tight (Quellenanordnung); ERUPT=1 Eruption aus einem Punkt (kein Strom von der Seite), Papier-Vorbote (Aufwoelbung); v0.1: alle 6 Wuerfe aus takt-a8.json als Mantaflow-Rauch (eine Domain je Wurf), Wurf von der Seite, Zeitlupe im Einschlag, gestaffelte Groessen, weiches Licht, Tiefenschaerfe. Basis: flow_test.py v0.4 (Runde 9).
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
    dram = pn.nodes.new('ShaderNodeValue'); dram.outputs[0].default_value = 1.0
    dam = pn.nodes.new('ShaderNodeMath'); dam.operation = 'MULTIPLY'; pn.links.new(imgD.outputs['Alpha'], dam.inputs[0]); pn.links.new(dram.outputs[0], dam.inputs[1])
    pn.links.new(dam.outputs[0], mx.inputs['Factor']); pn.links.new(gn_.outputs['Result'], mx.inputs['B']); pn.links.new(mx.outputs['Result'], pb.inputs['Base Color'])
ERUPT = E('ERUPT', '1') == '1'
def bump_pulse(px, py, fi, name):   # Vorbote: Papier woelbt sich unter dem Einschlagpunkt kurz auf (nur Schattierung)
    old = [l for l in pn.links if l.to_socket == pb.inputs['Normal']]
    src = old[0].from_socket if old else None
    gp = pn.nodes.new('ShaderNodeNewGeometry'); spp = pn.nodes.new('ShaderNodeSeparateXYZ'); pn.links.new(gp.outputs['Position'], spp.inputs[0])
    dx = pn.nodes.new('ShaderNodeMath'); dx.operation = 'SUBTRACT'; dx.inputs[1].default_value = px; pn.links.new(spp.outputs['X'], dx.inputs[0])
    dy = pn.nodes.new('ShaderNodeMath'); dy.operation = 'SUBTRACT'; dy.inputs[1].default_value = py; pn.links.new(spp.outputs['Y'], dy.inputs[0])
    dx2 = pn.nodes.new('ShaderNodeMath'); dx2.operation = 'MULTIPLY'; pn.links.new(dx.outputs[0], dx2.inputs[0]); pn.links.new(dx.outputs[0], dx2.inputs[1])
    dy2 = pn.nodes.new('ShaderNodeMath'); dy2.operation = 'MULTIPLY'; pn.links.new(dy.outputs[0], dy2.inputs[0]); pn.links.new(dy.outputs[0], dy2.inputs[1])
    r2 = pn.nodes.new('ShaderNodeMath'); r2.operation = 'ADD'; pn.links.new(dx2.outputs[0], r2.inputs[0]); pn.links.new(dy2.outputs[0], r2.inputs[1])
    den = pn.nodes.new('ShaderNodeMath'); den.operation = 'MULTIPLY_ADD'; den.inputs[1].default_value = float(E('DOMEK', '40')); den.inputs[2].default_value = 1.0; pn.links.new(r2.outputs[0], den.inputs[0])
    hh = pn.nodes.new('ShaderNodeMath'); hh.operation = 'DIVIDE'; hh.inputs[0].default_value = 1.0; pn.links.new(den.outputs[0], hh.inputs[1])
    amp = pn.nodes.new('ShaderNodeValue'); amp.name = name; amp.outputs[0].default_value = 0.0
    hm = pn.nodes.new('ShaderNodeMath'); hm.operation = 'MULTIPLY'; pn.links.new(hh.outputs[0], hm.inputs[0]); pn.links.new(amp.outputs[0], hm.inputs[1])
    bp = pn.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 1.0; bp.inputs['Distance'].default_value = 0.05; pn.links.new(hm.outputs[0], bp.inputs['Height'])
    if src is not None: pn.links.new(src, bp.inputs['Normal'])
    pn.links.new(bp.outputs['Normal'], pb.inputs['Normal'])
    PRE = int(E('PRE', '4'))
    for fr, v in ((1, 0.0), (max(1, fi - PRE), 0.0), (fi - 1, 1.0), (fi, 1.0), (fi + 2, 0.0)):   # waechst ueber PRE Bilder, faellt mit dem Durchbruch
        amp.outputs[0].default_value = v; amp.outputs[0].keyframe_insert('default_value', frame=fr)
DEPRAMP = E('DEPRAMP', '0') == '1'
def set_deposit(f):
    if imgD is None: return
    if DEPRAMP:   # Einzelwurf-Test: Belag erst D0 Bilder nach dem Einschlag, waechst ueber D1 Bilder (mit dem Absinken der Wolke)
        x = (f - fi_[SEL[0]] - float(E('DEPD0', '8'))) / float(E('DEPD1', '34')); dram.outputs[0].default_value = max(0.0, min(1.0, x)) ** 1.5
    pth = os.path.join(SIM, 'dep_%04d.png' % min(2 * (f - 1), 575))   # Filmbild n = f-1, Sim-Bild = 2n
    if os.path.exists(pth):
        if imgD.image: bpy.data.images.remove(imgD.image)
        imgD.image = bpy.data.images.load(pth); imgD.image.colorspace_settings.name = 'sRGB'

# --- Feinstaub: Partikel aus simT_a8e in ihrer Farbe, nur im Quadrat, stark ausgeduennt
import numpy as np
PR = float(E('PR', '1.0')); PSUB = int(E('PSUB', '40'))
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
    pth = os.path.join(SIM, 'pts_%04d.npz' % min(2 * (f - 1), 575))
    if not os.path.exists(pth): return
    z = np.load(pth); P = z['p']; C = z['c'].astype(np.float32); R = z['r'].astype(np.float32)
    sel = (np.abs(P[:, 0]) < 0.97) & (np.abs(P[:, 1]) < 0.97)
    idx = np.nonzero(sel)[0][::PSUB]
    if len(idx) == 0: return
    me_p.vertices.add(len(idx)); me_p.vertices.foreach_set('co', P[idx].ravel())
    a_ = me_p.attributes.new('rad', 'FLOAT', 'POINT'); a_.data.foreach_set('value', R[idx] * PR)
    c_ = me_p.attributes.new('col', 'FLOAT_COLOR', 'POINT'); c_.data.foreach_set('color', np.concatenate([C[idx], np.ones((len(idx), 1), np.float32)], 1).ravel()); me_p.update()

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
    cm = [float(v) for v in E('YCM', '1,0.72,0.32').split(',')] if yellow else [1, 1, 1]; mx_ = max(L)
    ac = [float(v) for v in E('YAC', '0.93,0.74,0.26').split(',')] if yellow else [1 - 0.8 * (1 - l / mx_) for l in L]   # Absorption nach Pigmentfarbe: Rest-Kanaele werden geschluckt, Schatten bleiben neutral
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
    g1, g2 = noise(float(E('G1S', '40')), float(E('G1A', '1.0'))), noise(float(E('G2S', '130')), float(E('G2A', '0.7')))
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
    F0, F1 = int(E('FADE0', '0')), int(E('FADE1', '0'))   # weicher Ausblendverlauf nach dem Einschlag (0 = erst am Fensterende)
    keys = ((1, base), (fi + F0, base), (fi + F1, 0.0)) if F1 > 0 else ((1, base), (e - 8, base), (e, 0.0))
    for fr, v in keys:
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
    if not ERUPT: st = quelle(dom, 'Strom%d' % i, 0.07, (px - dv[0] * SL, py - dv[1] * SL, 0.15), (dv[0] * VEL * 0.9, dv[1] * VEL * 0.9, -0.1 * VEL), 0.0, float(E('STREAMD', '2.0')), max(1, fi - SF), SF + 1)
    if not ERUPT:
        st.location = (px - dv[0] * SL, py - dv[1] * SL, 0.15); st.keyframe_insert('location', frame=max(1, fi - SF))
        st.location = (px, py, 0.13); st.keyframe_insert('location', frame=fi)
    else:
        bump_pulse(px, py, fi, 'dome%d' % i)
    CR = float(E('CORER', '0.28')) * sz; CD = float(E('COREDENS', '2.5')); CV = VEL * 0.22
    for ci in range(int(E('CORECL', '9'))):
        a_, b_, c_ = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.4, 0.4); nn = max(math.sqrt(a_ * a_ + b_ * b_), 1e-3)
        if ERUPT and E('ERMODE', 'wide') == 'wide':   # breite Anordnung wie Runde 9 (Haufen aus Quellen), nur mit Aufwaertsimpuls
            quelle(dom, 'Kern%d_%d' % (i, ci), CR * rng.uniform(0.4, 0.7), (px + a_ / nn * CR * 0.8 * rng.random(), py + b_ / nn * CR * 0.8 * rng.random(), 0.12 + abs(c_) * 0.05),
                   (dv[0] * VEL * 0.1, dv[1] * VEL * 0.1, VEL * float(E('UP', '0.4')) * rng.uniform(0.5, 1.1)), CV * rng.uniform(0.6, 1.4), CD * rng.uniform(0.8, 1.2), fi, 6 + rng.randint(-2, 2))
        elif ERUPT:   # Punktquelle knapp ueber der Flaeche, Geschwindigkeit nach oben (Kegel), leicht gekippt in Wurfrichtung
            quelle(dom, 'Kern%d_%d' % (i, ci), CR * rng.uniform(0.25, 0.45), (px + a_ / nn * CR * 0.25 * rng.random(), py + b_ / nn * CR * 0.25 * rng.random(), 0.05 + abs(c_) * 0.03),
                   (dv[0] * VEL * 0.12 + a_ * VEL * 0.15, dv[1] * VEL * 0.12 + b_ * VEL * 0.15, VEL * float(E('UP', '0.55')) * rng.uniform(0.7, 1.3)), CV * 0.4, CD * rng.uniform(1.2, 1.8), fi, 5 + rng.randint(-1, 2))
        else:
            quelle(dom, 'Kern%d_%d' % (i, ci), CR * rng.uniform(0.4, 0.7), (px + a_ / nn * CR * 0.8 * rng.random(), py + b_ / nn * CR * 0.8 * rng.random(), 0.14 + c_ * 0.05),
                   (dv[0] * VEL * 0.25, dv[1] * VEL * 0.25, -VEL * 0.15), CV * rng.uniform(0.6, 1.4), CD * rng.uniform(0.8, 1.2), fi, 6 + rng.randint(-2, 2))
    NR = int(E('NR', '12')); BASEV = [rng.uniform(0.55, 1.5) * (1.0 + 0.5 * (rng.random() < 0.25)) for _ in range(NR // 2)]
    for j in range(NR):
        a = 2 * math.pi * (j + rng.uniform(-0.35, 0.35)) / NR; v = VEL * BASEV[j % (NR // 2)] * rng.uniform(0.88, 1.12) * (1 + 0.55 * math.cos(a - th))   # in Wurfrichtung staerker
        quelle(dom, 'Strahl%d_%d' % (i, j), 0.06, (px + math.cos(a) * 0.04, py + math.sin(a) * 0.04, 0.06 if ERUPT else 0.12), (math.cos(a) * v, math.sin(a) * v, (float(E('JETUP', '0.5')) * v * rng.uniform(0.4, 1.2)) if ERUPT else -0.25 * v), 0.0, float(E('JETDENS', '2.2')), fi, 2)
    if ERUPT:   # Vorbote: feiner Staubring laeuft ueber die Flaeche, bevor der Durchbruch kommt
        for k in range(10):
            a = 2 * math.pi * k / 10
            quelle(dom, 'Ring%d_%d' % (i, k), 0.03, (px + math.cos(a) * 0.08, py + math.sin(a) * 0.08, 0.03), (math.cos(a) * VEL * 0.25, math.sin(a) * VEL * 0.25, VEL * 0.03), 0.0, float(E('RINGD', '0.5')), max(1, fi - 3), 3)
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
    FL = [int(v) for v in E('FRAMES').split(',') if v.strip()] if E('FRAMES') else list(range(1, TF + 1))
    os.makedirs(os.path.join(OUT, 'f'), exist_ok=True)
    for f in FL:
        t1 = time.time(); sc.frame_set(f); set_deposit(f); set_particles(f); sc.render.filepath = os.path.join(OUT, 'f', 'f_%04d.png' % f); bpy.ops.render.render(write_still=True)
        print('BILD', f, round(time.time() - t1, 1), 's', flush=True)
    if imgD is not None:   # Maske-Referenz: leeres Papier ohne Deposit
        leer = bpy.data.images.new('leer', 4, 4, alpha=True); leer.pixels = [0.0] * (4 * 4 * 4); leer.colorspace_settings.name = 'sRGB'
        if imgD.image: bpy.data.images.remove(imgD.image)
        imgD.image = leer
    for f in (1,): sc.frame_set(1); sc.render.filepath = os.path.join(OUT, 'plate.png'); bpy.ops.render.render(write_still=True)   # leeres Papier ohne Deposit fuer die Maske
    json.dump({'einschlagbilder': fi_, 'einschlag_s': [(f - 1) / 24.0 for f in fi_], 'anlauf_bilder': SF, 'fps': 24}, open(os.path.join(OUT, 'timing.json'), 'w'))
print('GESAMT_SEKUNDEN', round(time.time() - t0, 1), flush=True)
