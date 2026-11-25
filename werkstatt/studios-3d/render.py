# Leotio Studios 3D-Render v1.7 · 25.11.2026: Schaumkarte wfo_; 25.11.2026: echter Wasserkoerper (wat_/wtn_ aus sim.py), eigenes Flaechenlicht nur fuers Wasser; Szene + Puder-Teilchen (Punktwolke) + abgelegter Puder (Textur, Relief)
import bpy, sys, os, numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene
A=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
SIM=A[0]; OUTD=A[1]; frames=[int(x) for x in A[2].split(',')] if ',' in A[2] else None
if frames is None:
    a,b=A[2].split('-'); frames=list(range(int(a),int(b)+1))
STEP=int(os.environ.get('STEP','1')); frames=frames[::STEP]
RX=int(os.environ.get('RX','1920')); RY=int(os.environ.get('RY','1080')); SPP=int(os.environ.get('SPP','48'))
os.makedirs(OUTD,exist_ok=True)
GAIN=float(os.environ.get('GAIN','1.0'))
sc,cam=scene.build(float(os.environ.get('TILT','28')),(RX,RY),SPP)
if os.environ.get('CAM'):
    cx,cy,cz,lens=[float(v) for v in os.environ['CAM'].split(',')]
    cam.location=(cx,cy,cz); cam.data.lens=lens
# --- Papier-Material um Puderschicht erweitern
mat=bpy.data.materials['Papier']; nt=mat.node_tree; N=nt.nodes; Lk=nt.links
bsdf=N['Principled BSDF']
geo=N.new('ShaderNodeNewGeometry')
sep=N.new('ShaderNodeSeparateXYZ'); Lk.new(geo.outputs['Position'],sep.inputs[0])
def lin(inp,mul,add):
    m=N.new('ShaderNodeMath'); m.operation='MULTIPLY_ADD'; m.inputs[1].default_value=mul; m.inputs[2].default_value=add
    Lk.new(inp,m.inputs[0]); return m
ux=lin(sep.outputs['X'],0.5,0.5); uy=lin(sep.outputs['Y'],0.5,0.5)
comb=N.new('ShaderNodeCombineXYZ'); Lk.new(ux.outputs[0],comb.inputs['X']); Lk.new(uy.outputs[0],comb.inputs['Y'])
imgD=N.new('ShaderNodeTexImage'); imgD.extension='CLIP'; imgD.interpolation='Linear'
imgH=N.new('ShaderNodeTexImage'); imgH.extension='CLIP'
Lk.new(comb.outputs[0],imgD.inputs['Vector']); Lk.new(comb.outputs[0],imgH.inputs['Vector'])
# Korn
grain=N.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value=6000; grain.inputs['Detail'].default_value=2
paper_col=(0.90,0.905,0.905,1)
mix=N.new('ShaderNodeMix'); mix.data_type='RGBA'
mix.inputs['A'].default_value=paper_col
gain=N.new('ShaderNodeMix'); gain.data_type='RGBA'; gain.blend_type='MULTIPLY'; gain.inputs['Factor'].default_value=1.0
gain.inputs['B'].default_value=(GAIN,GAIN,GAIN,1)
Lk.new(imgD.outputs['Color'],gain.inputs['A'])
Lk.new(imgD.outputs['Alpha'],mix.inputs['Factor']); Lk.new(gain.outputs['Result'],mix.inputs['B'])
# Effekt-Karte: R = nass (Wasser in den Rillen), G = Leuchten
imgF=N.new('ShaderNodeTexImage'); imgF.extension='CLIP'; Lk.new(comb.outputs[0],imgF.inputs['Vector'])
sepF=N.new('ShaderNodeSeparateColor'); Lk.new(imgF.outputs['Color'],sepF.inputs['Color'])
wetf=N.new('ShaderNodeMath'); wetf.operation='MULTIPLY'; wetf.inputs[1].default_value=0.42; Lk.new(sepF.outputs['Red'],wetf.inputs[0])
wetmix=N.new('ShaderNodeMix'); wetmix.data_type='RGBA'; wetmix.inputs['B'].default_value=(0.42,0.55,0.66,1)
Lk.new(wetf.outputs[0],wetmix.inputs['Factor']); Lk.new(mix.outputs['Result'],wetmix.inputs['A'])
Lk.new(wetmix.outputs['Result'],bsdf.inputs['Base Color'])
emis=N.new('ShaderNodeMath'); emis.operation='MULTIPLY'; emis.inputs[1].default_value=float(os.environ.get('GLOW','3.2')); Lk.new(sepF.outputs['Green'],emis.inputs[0])
bsdf.inputs['Emission Color'].default_value=(1.0,0.80,0.48,1); Lk.new(emis.outputs[0],bsdf.inputs['Emission Strength'])
# Rauheit: Puder matt
rough=N.new('ShaderNodeMath'); rough.operation='MULTIPLY_ADD'; rough.inputs[1].default_value=0.13; rough.inputs[2].default_value=0.85
Lk.new(imgD.outputs['Alpha'],rough.inputs[0])
rwet=N.new('ShaderNodeMath'); rwet.operation='MULTIPLY_ADD'; rwet.inputs[1].default_value=-0.8; rwet.use_clamp=True
Lk.new(sepF.outputs['Red'],rwet.inputs[0]); Lk.new(rough.outputs[0],rwet.inputs[2]); Lk.new(rwet.outputs[0],bsdf.inputs['Roughness'])
# Relief der Puderschicht: Hoehenkarte + Korn
old_bump=[n for n in N if n.type=='BUMP'][0]
h_add=N.new('ShaderNodeMath'); h_add.operation='MULTIPLY_ADD'; h_add.inputs[2].default_value=0
Lk.new(grain.outputs['Fac'],h_add.inputs[0]); Lk.new(imgD.outputs['Alpha'],h_add.inputs[1])
h_sum=N.new('ShaderNodeMath'); h_sum.operation='ADD'
Lk.new(imgH.outputs['Color'],h_sum.inputs[0]); Lk.new(h_add.outputs[0],h_sum.inputs[1])
bump2=N.new('ShaderNodeBump'); bump2.inputs['Strength'].default_value=0.22; bump2.inputs['Distance'].default_value=0.004
Lk.new(h_sum.outputs[0],bump2.inputs['Height']); Lk.new(old_bump.outputs['Normal'],bump2.inputs['Normal'])
Lk.new(bump2.outputs['Normal'],bsdf.inputs['Normal'])
# --- Punktwolke fuer fliegenden Puder
me=bpy.data.meshes.new('Puder'); ob=bpy.data.objects.new('Puder',me); bpy.context.collection.objects.link(ob)
gn=bpy.data.node_groups.new('PuderPunkte','GeometryNodeTree')
gn.interface.new_socket('Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
gn.interface.new_socket('Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
gi=gn.nodes.new('NodeGroupInput'); go=gn.nodes.new('NodeGroupOutput')
m2p=gn.nodes.new('GeometryNodeMeshToPoints'); na=gn.nodes.new('GeometryNodeInputNamedAttribute'); na.data_type='FLOAT'; na.inputs['Name'].default_value='rad'
sm=gn.nodes.new('GeometryNodeSetMaterial')
gn.links.new(gi.outputs[0],m2p.inputs['Mesh']); gn.links.new(na.outputs['Attribute'],m2p.inputs['Radius'])
gn.links.new(m2p.outputs['Points'],sm.inputs['Geometry']); gn.links.new(sm.outputs['Geometry'],go.inputs[0])
mod=ob.modifiers.new('pp','NODES'); mod.node_group=gn
ob.visible_shadow=bool(os.environ.get('PSHADOW'))
pm=bpy.data.materials.new('PuderLuft'); pm.use_nodes=True
pn=pm.node_tree.nodes; pb=pn['Principled BSDF']
at=pn.new('ShaderNodeAttribute'); at.attribute_name='col'; at.attribute_type='GEOMETRY'
pm.node_tree.links.new(at.outputs['Color'],pb.inputs['Base Color'])
pb.inputs['Roughness'].default_value=0.95
pb.inputs['Alpha'].default_value=float(os.environ.get('PALPHA','0.45'))
pb.inputs['Specular IOR Level'].default_value=0.0
pb.inputs['Subsurface Weight'].default_value=0.3 if 'Subsurface Weight' in pb.inputs else 0
sm.inputs['Material'].default_value=pm
# --- Wasserkoerper: Hoehenfeld ueber dem Quadrat, liegt trocken unter dem Rillenboden
WG=512; HAVEW=any(os.path.exists(f'{SIM}/wat_{f:04d}.npy') for f in frames)
if HAVEW:
    DG=scene.D
    xs=np.linspace(-1,1,WG,dtype=np.float32); gx,gy=np.meshgrid(xs,xs[::-1])     # Zeile 0 = y +1 (wie die Karten)
    wme=bpy.data.meshes.new('Wasser'); wob=bpy.data.objects.new('Wasser',wme); bpy.context.collection.objects.link(wob)
    co=np.stack([gx,gy,np.full_like(gx,-DG-0.01)],-1).reshape(-1,3)
    ii=np.arange(WG*WG).reshape(WG,WG); q=np.stack([ii[:-1,:-1],ii[1:,:-1],ii[1:,1:],ii[:-1,1:]],-1).reshape(-1,4)
    wme.vertices.add(len(co)); wme.vertices.foreach_set('co',co.ravel())
    wme.loops.add(q.size); wme.loops.foreach_set('vertex_index',q.ravel())
    wme.polygons.add(len(q)); wme.polygons.foreach_set('loop_start',np.arange(0,q.size,4)); wme.polygons.foreach_set('loop_total',np.full(len(q),4))
    wme.update(); wme.polygons.foreach_set('use_smooth',np.ones(len(q),bool)); wob.visible_shadow=False
    wm_=bpy.data.materials.new('Wasser'); wm_.use_nodes=True; wn=wm_.node_tree.nodes; wl=wm_.node_tree.links; wb=wn['Principled BSDF']
    wg=wn.new('ShaderNodeNewGeometry'); ws=wn.new('ShaderNodeSeparateXYZ'); wl.new(wg.outputs['Position'],ws.inputs[0])
    def wlin(inp):
        m=wn.new('ShaderNodeMath'); m.operation='MULTIPLY_ADD'; m.inputs[1].default_value=0.5; m.inputs[2].default_value=0.5; wl.new(inp,m.inputs[0]); return m
    wc=wn.new('ShaderNodeCombineXYZ'); wl.new(wlin(ws.outputs['X']).outputs[0],wc.inputs['X']); wl.new(wlin(ws.outputs['Y']).outputs[0],wc.inputs['Y'])
    imgT=wn.new('ShaderNodeTexImage'); imgT.extension='EXTEND'; wl.new(wc.outputs[0],imgT.inputs['Vector'])
    tm=wn.new('ShaderNodeMix'); tm.data_type='RGBA'; tm.inputs['A'].default_value=(0.86,0.94,1.0,1)
    wgm=wn.new('ShaderNodeGamma'); wgm.inputs['Gamma'].default_value=float(os.environ.get('WSAT','1.25')); wl.new(imgT.outputs['Color'],wgm.inputs['Color'])   # kraeftigere Farbe: Pigment im Wasser
    wl.new(imgT.outputs['Alpha'],tm.inputs['Factor']); wl.new(wgm.outputs['Color'],tm.inputs['B']); wl.new(tm.outputs['Result'],wb.inputs['Base Color'])
    imgS=wn.new('ShaderNodeTexImage'); imgS.extension='EXTEND'; wl.new(wc.outputs[0],imgS.inputs['Vector'])        # Schaum: weiss, matt, undurchsichtig
    fm=wn.new('ShaderNodeMix'); fm.data_type='RGBA'; fm.inputs['B'].default_value=(1,1,1,1); wl.new(imgS.outputs['Color'],fm.inputs['Factor']); wl.new(tm.outputs['Result'],fm.inputs['A']); wl.new(fm.outputs['Result'],wb.inputs['Base Color'])
    fr_=wn.new('ShaderNodeMath'); fr_.operation='MULTIPLY_ADD'; fr_.inputs[1].default_value=0.5; fr_.inputs[2].default_value=0.03; wl.new(imgS.outputs['Color'],fr_.inputs[0]); wl.new(fr_.outputs[0],wb.inputs['Roughness'])
    tw=wn.new('ShaderNodeMath'); tw.operation='MULTIPLY_ADD'; tw.inputs[1].default_value=-float(os.environ.get('WOPAK','0.4')); tw.inputs[2].default_value=1.0
    wl.new(imgT.outputs['Alpha'],tw.inputs[0])
    tf=wn.new('ShaderNodeMath'); tf.operation='SUBTRACT'; tf.use_clamp=True; wl.new(tw.outputs[0],tf.inputs[0]); wl.new(imgS.outputs['Color'],tf.inputs[1]); wl.new(tf.outputs[0],wb.inputs['Transmission Weight'])
    wb.inputs['IOR'].default_value=1.333; wb.inputs['Roughness'].default_value=0.03
    wnz=wn.new('ShaderNodeTexNoise'); wnz.noise_dimensions='4D'; wnz.inputs['Scale'].default_value=float(os.environ.get('WRIP','38')); wnz.inputs['Detail'].default_value=2
    wbp=wn.new('ShaderNodeBump'); wbp.inputs['Strength'].default_value=float(os.environ.get('WBUMP','0.6')); wbp.inputs['Distance'].default_value=0.004
    wl.new(wnz.outputs['Fac'],wbp.inputs['Height']); wl.new(wbp.outputs['Normal'],wb.inputs['Normal'])
    for k_,v_ in (('use_raytrace_refraction',True),('use_transparency_overlap',False)):
        try: setattr(wm_,k_,v_)
        except Exception: pass
    try: sc.eevee.use_raytracing=True
    except Exception: pass
    wme.materials.append(wm_)
    # Flaechenlicht ueber der Kamera-Achse, nur fuer das Wasser: gibt den Glanz auf dem Spiegel, das Papier bleibt wie es ist
    bpy.ops.object.light_add(type='AREA',location=tuple(float(v) for v in os.environ.get('WLPOS','1.0,1.4,3.0').split(','))); WL=bpy.context.active_object; WL.data.size=float(os.environ.get('WLSIZE','0.8')); WL.data.energy=float(os.environ.get('WLIGHT','30'))
    try:
        col_=bpy.data.collections.new('NurWasser'); col_.objects.link(wob); WL.light_linking.receiver_collection=col_
    except Exception as e_: print('light linking fehlt',e_)
for f in frames:
    z=np.load(f'{SIM}/pts_{f:04d}.npz'); P=z['p']; C=z['c'].astype(np.float32); Rr=z['r'].astype(np.float32)
    me.clear_geometry()
    n=len(P)
    if n>0:
        me.vertices.add(n); me.vertices.foreach_set('co',P.ravel())
        a=me.attributes.new('rad','FLOAT','POINT'); a.data.foreach_set('value',Rr)
        c=me.attributes.new('col','FLOAT_COLOR','POINT'); c.data.foreach_set('color',np.concatenate([C,np.ones((n,1),np.float32)],1).ravel())
    me.update()
    for img,node,cs in ((f'{SIM}/dep_{f:04d}.png',imgD,'sRGB'),(f'{SIM}/hgt_{f:04d}.png',imgH,'Non-Color'),(f'{SIM}/fx_{f:04d}.png',imgF,'Non-Color')):
        if not os.path.exists(img): continue
        if node.image: bpy.data.images.remove(node.image)
        node.image=bpy.data.images.load(os.path.abspath(img)); node.image.colorspace_settings.name=cs
    if HAVEW:
        wp=f'{SIM}/wat_{f:04d}.npy'; zz=np.full(WG*WG,-DG-0.01,np.float32)
        if os.path.exists(wp):
            hh_=np.load(wp).astype(np.float32)
            zz=np.where(hh_>0.03,-DG+hh_*DG*float(os.environ.get('WFILL','0.92')),-DG-0.01).astype(np.float32).ravel()
            tp=f'{SIM}/wtn_{f:04d}.png'
            if imgT.image: bpy.data.images.remove(imgT.image)
            imgT.image=bpy.data.images.load(os.path.abspath(tp)); imgT.image.colorspace_settings.name='sRGB'; imgT.image.alpha_mode='CHANNEL_PACKED'
            if imgS.image: bpy.data.images.remove(imgS.image)
            imgS.image=bpy.data.images.load(os.path.abspath(f'{SIM}/wfo_{f:04d}.png')); imgS.image.colorspace_settings.name='Non-Color'
        co[:,2]=zz; wme.vertices.foreach_set('co',co.ravel()); wme.update()
        wnz.inputs['W'].default_value=f*0.06
    sc.render.filepath=f'{OUTD}/f_{f:04d}.png'
    bpy.ops.render.render(write_still=True)
    print('frame',f,'punkte',n,flush=True)
