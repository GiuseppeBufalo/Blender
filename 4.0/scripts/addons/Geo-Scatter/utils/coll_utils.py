
#Bunch of functions related to collection 

import bpy


def exclude_view_layers(collection, scenes="all", hide=True,):
    """exclude a collection from all view layers f all scenes"""
    
    did_act = False

    def recur_all_layer_collection(layer_collection,all_vl,):
        if (len(layer_collection.children)!=0):
            all_vl += layer_collection.children
            for ch in layer_collection.children:
                recur_all_layer_collection(ch,all_vl)
        return all_vl

    if (scenes=="all"):
        scenes = bpy.data.scenes[:]

    for s in scenes:
        for v in s.view_layers:
            for lc in recur_all_layer_collection(v.layer_collection,[]):
                
                if (lc.collection==collection):
                    
                    if (lc.exclude!=hide):
                        lc.exclude = hide
                        did_act = True
    
    return did_act


def collection_clear_obj(collection):
    """unlink all obj from a collection"""

    for obj in collection.objects:
        collection.objects.unlink(obj)

    return None


def get_viewlayer_coll(active_coll, collname):
    """Get viewlayer from collection name."""
    
    if (active_coll.name == collname): return active_coll
    found = None
    
    for layer in active_coll.children:
        found = get_viewlayer_coll(layer, collname)
        if (found):
            return found

    return None 


def set_collection_active(name="", scene=False):
    """Set collection active by name, return False if failed."""

    if (scene):
        name = bpy.context.scene.collection.name
        
    current_active = bpy.context.view_layer.layer_collection
    active_coll = get_viewlayer_coll(current_active, name)
    
    if (active_coll):
        bpy.context.view_layer.active_layer_collection = active_coll
        
    return (active_coll !=None)


def close_collection_areas():
    """close level on all outliner viewlayer area"""

    override = bpy.context.copy()
    for a in bpy.context.window.screen.areas:
        if (a.type=="OUTLINER"):
            if (a.spaces[0].display_mode=="VIEW_LAYER"):
                a.tag_redraw()
                override["area"] = a
                override["regions"] = a.regions[0]
                override["space"] = a.spaces[0]
                bpy.ops.outliner.show_one_level((override),open=False)
                bpy.ops.outliner.show_one_level((override),open=False)
                bpy.ops.outliner.show_one_level((override),open=False)
                a.tag_redraw()

    return None 
    

def create_new_collection(name, parent_name=None, prefix=False, exclude_scenes=None,):
    """Create new collection and link in given parent (if not None)."""
        
    #if prefix, == will guarantee to create a new colleciton each time, 
    #otherwise will just get the existing colleciton with given name 
    #should be called "suffix" not prefix... anyway...
    if (prefix):
        from .. utils.str_utils import find_suffix
        name = find_suffix(name,bpy.data.collections,)
    
    #Create the new collection if not exists
    new_col = bpy.data.collections.get(name)
    if (not new_col):
        new_col = bpy.data.collections.new(name=name)
        
        #get the parent collection
        parent = bpy.context.scene.collection
        if (parent_name!=None) and (parent_name in bpy.data.collections):
            parent = bpy.data.collections.get(parent_name)
            
        #if new then need to link it in parent 
        if (new_col.name not in parent.children):
            parent.children.link(new_col)
            
        #and also excluded? 
        if (exclude_scenes):
            exclude_view_layers(new_col, scenes=exclude_scenes, hide=True,)

    return new_col 


def create_scatter5_collections():
    """Create scatter collection set-up for this scene"""
        
    #versioning: legacy collection rename
    for col in bpy.data.collections:
        if (col.name.startswith("Scatter5")):
            col.name = col.name.replace("Scatter5","Geo-Scatter")
            
    initial_creation = ("Geo-Scatter" not in bpy.data.collections)
    is_relink = not initial_creation and ("Geo-Scatter" not in bpy.context.scene.collection.children)
            
    maincoll = create_new_collection("Geo-Scatter",)
    gscoll = create_new_collection("Geo-Scatter Geonode", parent_name=maincoll.name,)
    create_new_collection("Geo-Scatter Ins Col", parent_name=maincoll.name, exclude_scenes="all",)
    create_new_collection("Geo-Scatter Import", parent_name=maincoll.name, exclude_scenes="all",)
    create_new_collection("Geo-Scatter Extra", parent_name=maincoll.name, exclude_scenes="all",)
    create_new_collection("Geo-Scatter User Col", parent_name=maincoll.name, prefix=False,)
    create_new_collection("Geo-Scatter Surfaces", parent_name=maincoll.name, prefix=False,)

    #we need to close the collection by default if this is the first time we create everything 
    if (initial_creation):

        def will_close():
            close_collection_areas()
        bpy.app.timers.register(will_close, first_interval=0.555)
        
    #if this is the first time we link this scatter, supposedly to a new scene, we hide some collection from viewlayer to avoid confusion
    if (is_relink):
        
        bpy.context.scene.collection.children.link(maincoll)

        for col in bpy.context.scene.collection.children_recursive:
            if (col.name.startswith("psy : ") or col.name.startswith("ins_col : ")):
                exclude_view_layers(col, scenes=[bpy.context.scene], hide=True,)
            elif (col.name in ("Geo-Scatter Ins Col","Geo-Scatter Surfaces","Geo-Scatter Import","Geo-Scatter Extra")):
                exclude_view_layers(col, scenes=[bpy.context.scene], hide=True,)
            continue
                
    return None 


#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o


from .. resources.translate import translate


class SCATTER5_OT_create_coll(bpy.types.Operator):

    bl_idname      = "scatter5.create_coll"
    bl_label       = translate("Create a new collection with selected object(s)")
    bl_description = translate("Create a new collection with selected object(s)")
    bl_options = {'REGISTER',}

    api : bpy.props.StringProperty()
    pointer_type : bpy.props.StringProperty() #expect "str" or "data"?  

    coll_name : bpy.props.StringProperty(name="Name", options={"SKIP_SAVE",},)
    parent_name : bpy.props.StringProperty(name="Geo-Scatter User Col", options={"SKIP_SAVE",},)

    @classmethod
    def poll(cls, context):
        return (context.mode=="OBJECT")

    def __init__(self):
        self.selection = bpy.context.selected_objects
        return None 

    def invoke(self, context, event):
        self.alt = event.alt #TODO ALT SUPPORT!
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self,"coll_name")
        return None 

    def execute(self, context):

        if (len(self.selection)==0):
            bpy.ops.scatter5.popup_menu(msgs=translate("No Compatible Object(s) Selected"), title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}

        new_coll = create_new_collection(self.coll_name, parent_name=self.parent_name, prefix=True)
        for o in self.selection:
            new_coll.objects.link(o)

        #execute code
        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        
        psy_active = emitter.scatter5.get_psy_active()
        group_active = emitter.scatter5.get_group_active()

        if (self.pointer_type=='str'):
              exec(f"{self.api}='{new_coll.name}'")
        else: exec(f"{self.api}=new_coll")

        #UNDO_PUSH
        bpy.ops.ed.undo_push(message=translate("Create a new collection with selected object(s)"),)

        return {'FINISHED'}


class SCATTER5_OT_add_to_coll(bpy.types.Operator):

    bl_idname = "scatter5.add_to_coll"
    bl_label       = translate("Add the compatible object(s) selected in the viewport to this collection")
    bl_description = translate("Add the compatible object(s) selected in the viewport to this collection.\nHold ALT to batch apply this action also to the collections of the selected system(s)")
    bl_options     = {'REGISTER',}

    coll_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    alt_support : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)

    @classmethod
    def poll(cls, context):
        return (context.mode=="OBJECT")

    def __init__(self):
        self.selection = bpy.context.selected_objects
        return None 

    def invoke(self, context, event):
        #alt support & passed context from GUI
        self.alt = (event.alt and self.alt_support)
        return self.execute(context)

    def execute(self, context):
            
        if (len(self.selection)==0):
            bpy.ops.scatter5.popup_menu(msgs=translate("No Compatible Object(s) Selected"), title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}

        #collect all our collections

        if (self.alt):

            colls = []
            ctxt_api = context.pass_ui_arg_prop_name.path_from_id().split(".")[-1].replace("passctxt_","")
            for p in context.scene.scatter5.emitter.scatter5.get_psys_selected():
                collname = getattr(p,ctxt_api)
                coll = bpy.data.collections.get(collname)
                if (coll is not None):
                    colls.append(coll)
        else:

            coll = bpy.data.collections.get(self.coll_name)
            if (coll is None):
                print(f"ERROR : {self.coll_name} not found")
                return {'FINISHED'}
            colls = [coll]

        #for all collection

        for coll in colls:
            for o in self.selection:
                if (o.name not in coll.objects):
                    coll.objects.link(o)
        
        #UNDO_PUSH
        bpy.ops.ed.undo_push(message=translate("Add selected object(s) to the context collection(s)"),)

        return {'FINISHED'}


class SCATTER5_OT_remove_from_coll(bpy.types.Operator):

    bl_idname = "scatter5.remove_from_coll"
    bl_label       = translate("Remove this object from the context collection")
    bl_description = translate("Remove this object from the context collection.\nHold ALT to batch apply this action also to the collections of the selected system(s)")
    bl_options     = {'REGISTER',}

    obj_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    coll_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    alt_support : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)

    def invoke(self, context, event):
        #alt support & passed context from GUI
        self.alt = (event.alt and self.alt_support)
        return self.execute(context)

    def execute(self, context):

        o = bpy.data.objects.get(self.obj_name)
        if (o is None):
            print(f"ERROR :  {self.obj_name} not found")
            return {'FINISHED'}

        #collect all our collections

        if (self.alt):

            colls = []
            ctxt_api = context.pass_ui_arg_prop_name.path_from_id().split(".")[-1].replace("passctxt_","")
            for p in context.scene.scatter5.emitter.scatter5.get_psys_selected():
                collname = getattr(p,ctxt_api)
                coll = bpy.data.collections.get(collname)
                if (coll is not None):
                    colls.append(coll)

        else:

            coll = bpy.data.collections.get(self.coll_name)
            if (coll is None):
                print(f"ERROR : {self.coll_name} not found")
                return {'FINISHED'}
            colls = [coll]

        #for all our collections, remove obj, if present in there

        for coll in colls:
            if (o.name in coll.objects):
                coll.objects.unlink(o)
                continue

        #UNDO_PUSH
        bpy.ops.ed.undo_push(message=translate("Remove an object from the context collection(s)"),)

        return {'FINISHED'}


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_create_coll,
    SCATTER5_OT_add_to_coll,
    SCATTER5_OT_remove_from_coll,
    
    )