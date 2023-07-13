
#General Import/Export functions that can be used a bit everywhere 

import bpy
import os

from . import coll_utils

from . extra_utils import dprint


#  dP""b8 888888  dP"Yb  88b 88  dP"Yb  8888b.  888888
# dP   `" 88__   dP   Yb 88Yb88 dP   Yb  8I  Yb 88__
# Yb  "88 88""   Yb   dP 88 Y88 Yb   dP  8I  dY 88""
#  YboodP 888888  YbodP  88  Y8  YbodP  8888Y"  888888


def import_geonodes( blend_path, geonode_names, link=False, ):
    """import geonode(s) from given blend_path"""
    return_list=[]
        
    with bpy.data.libraries.load(blend_path, link=link) as (data_from, data_to):
        #loop over every nodegroups in blend
        for g in data_from.node_groups:
            #check for name
            if g in geonode_names:
                #add to return list 
                if g not in return_list:
                    return_list.append(g)
                #check if not already imported
                if g not in bpy.data.node_groups:
                    # add to import list  
                    data_to.node_groups.append(g)

    if (len(return_list)==0):
        return [None]

    return return_list


def import_and_add_geonode( o, mod_name="", node_name="", blend_path="", copy=True, use_fake_user=True, unique_nodegroups=[], show_viewport=True,):
    """Create a geonode modifier, import node from blend path if does not exist in user file"""

    #create new modifier that will gost geonode
    m = o.modifiers.new(name=mod_name,type="NODES")
    m.show_viewport = show_viewport
        
    #get geonodegraph
    geonode = bpy.data.node_groups.get(node_name)
    
    #import geonodegraph if not already in blend?
    if (geonode is None):
        import_geonodes(blend_path,[node_name],)
        geonode = bpy.data.node_groups[node_name]
        geonode.use_fake_user = use_fake_user
        
    #is geonodegraph unique? 
    if (copy):
        geonode = geonode.copy()

    #control if some nodegroups in this geonodegraph need to be unique ?
    for nm in unique_nodegroups:

        #support 1x level nested? ex "s_distribution_manual.uuid_equivalence"
        nnm = None 
        if ("." in nm):
            nm,nnm,*_ = nm.split(".")

        n = geonode.nodes.get(nm)

        if (n is None):
            print(f"S5 failed to copy() {nm}")
            continue
            
        #support 1x level nested?
        if (nnm is not None):
            nn = n.node_tree.nodes.get(nnm)
            if (nn is None):
                print(f"S5 failed to copy() {nnm}")
                continue
            nn.node_tree = nn.node_tree.copy()
            del nnm
            continue

        n.node_tree = n.node_tree.copy()    
        continue

    #assign nodegraph to modifier
    m.node_group = geonode
    
    return m 


#  dP"Yb  88""Yb  88888 888888  dP""b8 888888 .dP"Y8
# dP   Yb 88__dP     88 88__   dP   `"   88   `Ybo."
# Yb   dP 88""Yb o.  88 88""   Yb        88   o.`Y8b
#  YbodP  88oodP "bodP' 888888  YboodP   88   8bodP'


def import_objects( blend_path="", object_names=[], link=False, link_coll="Geo-Scatter Import",):
    """import obj(s) from given blend_path"""

    #if all object names are already imported, then we simply skip this function
    if all([n in bpy.data.objects for n in object_names]):
        return object_names

    dprint(f"import_objects({os.path.basename(blend_path)})->start")

    r_list=[]

    with bpy.data.libraries.load(blend_path, link=link) as (data_from, data_to):
        #loop over every obj in blend
        for g in data_from.objects:
            #check if name in selected and not import twice
            if (g in object_names) and (g not in r_list):
                r_list.append(g)
                #import in data.objects if not already 
                if (g not in bpy.data.objects):
                    data_to.objects.append(g)

    dprint("import_objects->end")

    #Nothing found ?
    if (len(r_list)==0):
        return [None]

    #cleanse asset mark?
    for n in r_list:
        o = bpy.data.objects.get(n)
        if (o is None):
            continue
        if (o.asset_data is None):
            continue
        o.asset_clear()
        continue

    #store import in collection?
    if (link_coll not in (None,""),):
        #create Geo-Scatter collections if not already
        coll_utils.create_scatter5_collections()
        #get collection, create if not found
        import_coll = coll_utils.create_new_collection(link_coll, parent_name="Geo-Scatter")
        #always move imported in collection
        for n in r_list:
            if (n not in import_coll.objects):
                import_coll.objects.link(bpy.data.objects[n])

    return r_list


def export_objects( blend_path, objects_list, ):
    """export obj in a new .blend"""

    data_blocks = set(objects_list)
    bpy.data.libraries.write(blend_path, data_blocks, )

    return None


#    db    .dP"Y8 .dP"Y8 888888 888888     88""Yb 88""Yb  dP"Yb  Yb        dP .dP"Y8 888888 88""Yb
#   dPYb   `Ybo." `Ybo." 88__     88       88__dP 88__dP dP   Yb  Yb  db  dP  `Ybo." 88__   88__dP
#  dP__Yb  o.`Y8b o.`Y8b 88""     88       88""Yb 88"Yb  Yb   dP   YbdPYbdP   o.`Y8b 88""   88"Yb
# dP""""Yb 8bodP' 8bodP' 888888   88       88oodP 88  Yb  YbodP     YP  YP    8bodP' 888888 88  Yb


class AssetItem():
    
    def __init__(self, asset=None, directory="",):
        
        self.asset = asset
        self.name = asset.name
        self.type = asset.id_type

        if (bool(directory)):
            blend, inner = asset.relative_path.split(".blend") #this line won't work if the name is "dude.blend123.blend" for example
            self.path = os.path.join(directory, f"{blend}.blend")
            self.full_path = os.path.join(directory, asset.relative_path)
            assert os.path.exists(self.path)
        else:
            self.path = "current_file"
            self.full_path = "current_file" 
    
    def __repr__(self):

        return f"<AssetItem {self.type} '{self.name}' at {self.full_path}>"


#globals needed for workaround
is_current_file = None
import_type = None
selected_asset_items = None


class SCATTER5_OT_get_browser_items(bpy.types.Operator):
    """workaround, use an operrator context override to get correct cotext. areas[x].selected_asset_files just refuses to work"""

    bl_idname      = "scatter5.get_browser_items"
    bl_label       = ""
    bl_description = ""

    def execute(self, context):
        """gather asset browset items from operator context"""

        #import globals and reset
        global is_current_file , import_type , selected_asset_items
        is_current_file = import_type = selected_asset_items = None

        #no headless support
        if (not context.window):
            print("SCATTER5_OT_get_browser_items->not context.window, using blender headlessly?")
            return {'FINISHED'}
        
        #set global context
        window, area = None, None

        #is context area already correct?
        if (context.area.ui_type=="ASSETS"):
            window, area = context.window, context.area

        #else try to find AB area in context window first
        if (area is None):
            for a in context.window.screen.areas:
                if (a.ui_type=="ASSETS"):
                    window, area = context.window, a
                    break

        #else try other windows?
        if (area is None):
            for w in context.window_manager.windows:
                for a in w.screen.areas:
                    if (a.ui_type=="ASSETS"):
                        window, area = w, a
                        break

        #else raise error..
        if (area is None):
            print("SCATTER5_OT_get_browser_items->No match for windows/areas")
            return {'FINISHED'}

        #override if needed, to do so, will need to quit and relaunch this operator
        if ((context.area!=area) or (context.window!=window)):
            override = bpy.context.copy()
            override.update(area=area)
            override.update(window=window)
            bpy.ops.scatter5.get_browser_items(override)
            return {'FINISHED'}

        space = area.spaces[0]
        directory = space.params.directory.decode("utf-8")

        #write globals
        is_current_file = not bool(directory)
        import_type = space.params.import_type
        selected_asset_items = [ AssetItem(asset=ass, directory=directory) for ass in context.selected_asset_files ]
        #TODO supports "COLLECTION", will need to import collection and do object instance ourself if cannot find collection instance object
        selected_asset_items = [ Ass for Ass in selected_asset_items if (Ass.type=="OBJECT") ] 

        return {'FINISHED'}


def import_selected_assets(link=False, link_coll="Geo-Scatter Import",):
    """import selected object type assets from browser, link/append depends on technique"""

    objects_found = []

    bpy.ops.scatter5.get_browser_items()
    global is_current_file , import_type , selected_asset_items
    
    if (selected_asset_items is None) or (len(selected_asset_items)==0):
        return objects_found

    #create Geo-Scatter collections if not already
    coll_utils.create_scatter5_collections()    

    #all already in file?
    if (is_current_file):

        #get collection
        import_coll = bpy.data.collections.get(link_coll)

        for ass in selected_asset_items:

            o = bpy.data.objects.get(ass.name)
            if (o is not None): 
                objects_found.append(o)
                #put asset in collection
                if (o.name not in import_coll.objects):
                    import_coll.objects.link(o)
            continue
    
    else: #to be imported from given path perhaps? 

        #sort assets by path 
        to_import = {}
        for ass in selected_asset_items:
            if (ass.path not in to_import.keys()):
                to_import[ass.path] = []
            to_import[ass.path].append(ass.name)
            continue

        #import assets from path 
        for path,names in to_import.items():
            import_objects(
                blend_path=path,
                object_names=names,
                link=link,
                )
            for n in names:
                o = bpy.data.objects.get(n)
                if (o is not None): 
                    objects_found.append(o)
            continue
        
    return objects_found 


# 8b    d8    db    888888 888888 88""Yb 88    db    88
# 88b  d88   dPYb     88   88__   88__dP 88   dPYb   88
# 88YbdP88  dP__Yb    88   88""   88"Yb  88  dP__Yb  88  .o
# 88 YY 88 dP""""Yb   88   888888 88  Yb 88 dP""""Yb 88ood8


def import_materials(blend_path, material_names, link=False,):
    """import materials by name into blender data"""

    #if all material names are already imported, then we simply skip this function
    if all([n in bpy.data.materials for n in material_names]):
        return material_names

    r_list=[]

    with bpy.data.libraries.load(blend_path, link=link) as (data_from, data_to):
        #loop over every nodegroups in blend
        for g in data_from.materials:
            #check for name
            if (g in material_names):
                #add to return list 
                if (g not in r_list):
                    r_list.append(g)
                #check if not already imported
                if (g not in bpy.data.materials):
                    # add to import list  
                    data_to.materials.append(g)
            continue

    if (len(r_list)==0):
        return [None]

    return r_list


# 88 8b    d8    db     dP""b8 888888
# 88 88b  d88   dPYb   dP   `" 88__
# 88 88YbdP88  dP__Yb  Yb  "88 88""
# 88 88 YY 88 dP""""Yb  YboodP 888888


def import_image(fpath, hide=False, use_fake_user=False):
    """import images in bpy.data.images"""

    if (not os.path.exists(fpath)):
        return None 

    fname = os.path.basename(fpath)
    if (hide):
        fname = "." + fname

    image = bpy.data.images.get(fname)
    if (image is None):
        image = bpy.data.images.load(fpath) 
        image.name = fname

    image.use_fake_user=use_fake_user
    return image 


# 888888 Yb  dP 88""Yb  dP"Yb  88""Yb 888888     .dP"Y8 888888 88""Yb 88    db    88     88 8888P    db    888888 88  dP"Yb  88b 88
# 88__    YbdP  88__dP dP   Yb 88__dP   88       `Ybo." 88__   88__dP 88   dPYb   88     88   dP    dPYb     88   88 dP   Yb 88Yb88
# 88""    dPYb  88"""  Yb   dP 88"Yb    88       o.`Y8b 88""   88"Yb  88  dP__Yb  88  .o 88  dP    dP__Yb    88   88 Yb   dP 88 Y88
# 888888 dP  Yb 88      YbodP  88  Yb   88       8bodP' 888888 88  Yb 88 dP""""Yb 88ood8 88 d8888 dP""""Yb   88   88  YbodP  88  Y8


def serialization(d):
    """convert unknown blendertypes"""

    from mathutils import Euler, Vector, Color

    for key,value in d.items():
        #convert blender array type to list
        if (type(value) in [Euler, Vector, Color, bpy.types.bpy_prop_array]):
            d[key] = value[:] 
        #recursion needed for pattern texture data storage for example
        elif (type(value)==dict):
            d[key] = serialization(value)
        continue

    return d


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
        
    SCATTER5_OT_get_browser_items,

    )