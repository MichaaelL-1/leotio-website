# Leotio Studios 3D-Szene v1.3 · 25.11.2026: Logo als Papier-Relief, Licht, Kamera (Blender bpy)
import bpy, math, sys, os
from mathutils import Vector
U=0.01            # 1 Logo-Einheit = 1 cm, Logo 2 m
D=0.016           # Rillentiefe (flacher, nah am Original)
w=7.881
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
def box(name,x0,y0,x1,y1,z0,z1,mat,bevel=0.0):
    # Logo-Koordinaten: x nach rechts, y nach unten -> Blender y = -y
    cx=(x0+x1)/2*U-1.0; cy=-((y0+y1)/2*U-1.0)
    bpy.ops.mesh.primitive_cube_add(size=1,location=(cx,cy,(z0+z1)/2))
    o=bpy.context.active_object; o.name=name
    o.scale=((x1-x0)*U,(y1-y0)*U,(z1-z0))
    bpy.ops.object.transform_apply(scale=True)
    if bevel>0:
        m=o.modifiers.new('bev','BEVEL'); m.width=bevel; m.segments=4; m.limit_method='ANGLE'
    o.data.materials.append(mat)
    return o
def paper_mat():
    m=bpy.data.materials.new('Papier'); m.use_nodes=True
    nt=m.node_tree; b=nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(0.90,0.905,0.905,1)
    b.inputs['Roughness'].default_value=0.85
    tex=nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=900; tex.inputs['Detail'].default_value=6
    bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=0.08; bump.inputs['Distance'].default_value=0.0006
    nt.links.new(tex.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],b.inputs['Normal'])
    return m
def poly(name,pts,z0,z1,mat,bevel=0.0):
    import bmesh
    me=bpy.data.meshes.new(name); o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o)
    bm=bmesh.new()
    vb=[bm.verts.new((x*U-1.0,-(y*U-1.0),z0)) for x,y in pts]
    vt=[bm.verts.new((x*U-1.0,-(y*U-1.0),z1)) for x,y in pts]
    n=len(pts)
    bm.faces.new(vt); bm.faces.new(list(reversed(vb)))
    for i in range(n):
        j=(i+1)%n; bm.faces.new([vb[i],vb[j],vt[j],vt[i]])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(me); bm.free()
    if bevel>0:
        m=o.modifiers.new('bev','BEVEL'); m.width=bevel; m.segments=4; m.limit_method='ANGLE'
    o.data.materials.append(mat); return o
def build(cam_tilt=28.0, res=(1920,1080), samples=64):
    clear()
    sc=bpy.context.scene
    mat=paper_mat()
    B=0.012   # Kantenrundung wie gepraegtes Papier
    # Boden der Rillen
    box('Boden',-300,-300,500,500,-D-0.02,-D,mat)
    # Papier ausserhalb des Quadrats: ein Stueck mit quadratischem Loch
    out_=box('Aussen',-300,-300,500,500,-D,0,mat)
    cut=box('Schnitt',0,0,200,200,-1,1,mat); cut.hide_render=True; cut.hide_viewport=True
    bo=out_.modifiers.new('loch','BOOLEAN'); bo.operation='DIFFERENCE'; bo.object=cut
    bv=out_.modifiers.new('bev','BEVEL'); bv.width=B; bv.segments=4; bv.limit_method='ANGLE'
    # Innen: L als ein Koerper, Quadrat-Flaeche
    poly('L',[(w,w),(54.638,w),(54.638,145.362),(200-w,145.362),(200-w,200-w),(w,200-w)],-D,0,mat,B)
    box('Quadrat',54.638+w,w,200-w,137.481,-D,0,mat,B)
    # Licht: Sonne oben links, flach genug fuer klare Rillenschatten
    bpy.ops.object.light_add(type='SUN',location=(0,0,5)); L=bpy.context.active_object
    L.data.energy=5.2; L.data.angle=math.radians(3)
    el=math.radians(24); az=math.radians(135)   # aus Nordwest
    L.rotation_euler=(0,0,0)
    d=Vector((math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)))
    L.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    L.data.color=(1.0,0.97,0.93)
    world=bpy.data.worlds.new('W'); sc.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.75,0.77,0.80,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.45
    # Kamera: leicht geneigt, Logo mittig
    # Kamera senkrecht von oben; Logo exakt so gross und mittig wie das Original (560 px bei 1920 px Breite)
    lens=50.0; width_m=2.0*1920/560; dist=width_m*lens/36.0
    bpy.ops.object.camera_add(location=(0,0,dist)); cam=bpy.context.active_object
    cam.data.lens=lens; cam.data.sensor_fit='HORIZONTAL'; cam.data.sensor_width=36; cam.rotation_euler=(0,0,0)
    cam.data.clip_end=100
    sc.camera=cam
    eng=os.environ.get('ENGINE','CYCLES')
    if eng=='EEVEE':
        sc.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
        sc.eevee.taa_render_samples=int(os.environ.get('EEVEE_SPP','32'))
        try: sc.eevee.use_shadows=True
        except Exception: pass
    sc.cycles.samples=samples
    if eng=='CYCLES':
        sc.render.engine='CYCLES'; sc.cycles.device='CPU'
        if os.environ.get('GPU'):
            p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.get_devices()
            for d in p.devices: d.use=(d.type=='METAL')
            sc.cycles.device='GPU'
    sc.cycles.use_denoising=True
    sc.render.resolution_x,sc.render.resolution_y=res; sc.render.resolution_percentage=100
    sc.view_settings.view_transform='Standard'; sc.view_settings.look='AgX - Base Contrast' if False else 'None'
    sc.render.film_transparent=False
    sc.view_settings.exposure=-0.22
    return sc,cam
if __name__=='__main__':
    out=sys.argv[-1]
    sc,cam=build(float(os.environ.get('TILT','28')),(int(os.environ.get('RX','960')),int(os.environ.get('RY','540'))),int(os.environ.get('SPP','32')))
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
