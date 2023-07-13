
#Bunch of function related to mesh creation and other simple interraction

import bpy, bmesh
from mathutils import Vector


def texture_data(type="",name="",duppli_existing=False,image_data=None): 
    """create e new texture data, type in [IMAGE,CLOUDS,NOISE,WOOD]""" #used in terrain displacement 
    
    if image_data:
        type = "IMAGE"
        
    t = bpy.data.textures.get(name)
    if duppli_existing: #Dorian, first of all this is false and second of all this function is not used anywhere except for the shitty terrain module.. 
        t = t.copy()
    if t is None:
        t = bpy.data.textures.new(name=name,type=type)
        
    t.type = type 
    
    if image_data:
        t.image = image_data
     
    return t

def get_bb_points(o):
    """get the four bounding box top points""" 
    #used in 2dremesher

    points = []
    for i in [1,2,5,6]: #=top
        p = o.matrix_world @ Vector((o.bound_box[i][0],o.bound_box[i][1],o.bound_box[i][2]))
        p += Vector((0,0,p[2]*0.1))
        points.append(p)
    return points

def quad(objname,points):
    """create quad from four points""" 
    #used in 2dremesher 

    mymesh = bpy.data.meshes.new(objname)
    myobject = bpy.data.objects.new(objname, mymesh)
    bpy.context.scene.collection.objects.link(myobject)
    # Generate mesh data
    mymesh.from_pydata(points, [], [(0, 1, 3, 2)])
    # Calculate the edges
    mymesh.update(calc_edges=True)

    return myobject

def point(name,collection):
    """create single point object"""
    #used in camera culling and dynamic camera mask 

    # Create new mesh and a new object
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)

    # Make a mesh from a list of vertices/edges/faces
    me.from_pydata([(0.0, 0.0, 0.0)], [], [])

    # Display name and update the mesh
    me.update()

    collection.objects.link(ob)

    return ob

def subdivide(o,subdiv=5):
    """subdivide o""" 
    #used below and in grid-bisect

    m = o.modifiers.new(type='SUBSURF',name='sub')
    m.subdivision_type = 'SIMPLE'
    m.levels = subdiv
    override = bpy.context.copy()
    override["object"] = o
    bpy.ops.object.modifier_apply(override, modifier="sub")

    return o 

def subdivided_plane(subdiv=5,ratio=0.5): 
    """create subdivided plane, (gross bpy.ops)""" 
    #used in terrain creation 

    bpy.ops.mesh.primitive_plane_add(size=20, enter_editmode=False)
    plane = bpy.context.object
    plane.scale[0] = ratio
    subdivide(plane,subdiv=subdiv)

    return plane 

def lock_transform(o,value=True):
    """lock object transforms""" 
    #used when creating the scattering object, and in dynamic camera 
    
    for i in [0,1,2]:
        o.lock_location[i] = value
        o.lock_rotation[i] = value
        o.lock_scale[i]    = value

    return None 