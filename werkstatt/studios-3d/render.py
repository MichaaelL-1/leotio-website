# Leotio Studios 3D-Render v1.2 · 25.11.2026: Szene + Puder-Teilchen (Punktwolke) + abgelegter Puder (Textur, Relief)
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
Lk.new(mix.outputs['Result'],bsdf.inputs['Base Color'])
# Rauheit: Puder matt
rough=N.new('ShaderNodeMath'); rough.operation='MULTIPLY_ADD'; rough.inputs[1].default_value=0.13; rough.inputs[2].default_value=0.85
Lk.new(imgD.outputs['Alpha'],rough.inputs[0]); Lk.new(rough.outputs[0],bsdf.inputs['Roughness'])
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
ob.visible_shadow=False
pm=bpy.data.materials.new('PuderLuft'); pm.use_nodes=True
pn=pm.node_tree.nodes; pb=pn['Principled BSDF']
at=pn.new('ShaderNodeAttribute'); at.attribute_name='col'; at.attribute_type='GEOMETRY'
pm.node_tree.links.new(at.outputs['Color'],pb.inputs['Base Color'])
pb.inputs['Roughness'].default_value=0.95
pb.inputs['Alpha'].default_value=0.45
pb.inputs['Specular IOR Level'].default_value=0.0
pb.inputs['Subsurface Weight'].default_value=0.3 if 'Subsurface Weight' in pb.inputs else 0
sm.inputs['Material'].default_value=pm
for f in frames:
    z=np.load(f'{SIM}/pts_{f:04d}.npz'); P=z['p']; C=z['c'].astype(np.float32); Rr=z['r'].astype(np.float32)
    me.clear_geometry()
    n=len(P)
    if n>0:
        me.vertices.add(n); me.vertices.foreach_set('co',P.ravel())
        a=me.attributes.new('rad','FLOAT','POINT'); a.data.foreach_set('value',Rr)
        c=me.attributes.new('col','FLOAT_COLOR','POINT'); c.data.foreach_set('color',np.concatenate([C,np.ones((n,1),np.float32)],1).ravel())
    me.update()
    for img,node,cs in ((f'{SIM}/dep_{f:04d}.png',imgD,'sRGB'),(f'{SIM}/hgt_{f:04d}.png',imgH,'Non-Color')):
        if node.image: bpy.data.images.remove(node.image)
        node.image=bpy.data.images.load(os.path.abspath(img)); node.image.colorspace_settings.name=cs
    sc.render.filepath=f'{OUTD}/f_{f:04d}.png'
    bpy.ops.render.render(write_still=True)
    print('frame',f,'punkte',n,flush=True)
