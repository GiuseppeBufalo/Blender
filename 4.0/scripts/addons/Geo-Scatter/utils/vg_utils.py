
#bunch of fuctions i use when working with vertex-groups

import bpy 
import numpy as np
from mathutils.kdtree import KDTree

from . import override_utils
from . str_utils import word_wrap

from .. resources.translate import translate
from .. widgets.infobox import SC5InfoBox, generic_infobox_setup


def get_weight(o, vg_name, eval_modifiers=True):
    """get weight dict"""
    
    #eval modifiers
    if eval_modifiers == True:
           depsgraph = bpy.context.evaluated_depsgraph_get()
           eo = o.evaluated_get(depsgraph)
           ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else:  ob = o.data    

    #forced to loop, as we cannot foreach_get vertex weight in blender...
    w = {}
    for v in ob.vertices:
        w[v.index] = 0.0 
        #if vert have weight, then fill dict
        for g in v.groups:
            if o.vertex_groups[vg_name].index == g.group:
                w[v.index] = g.weight
    return w

def fill_vg(o, vg, fill, method="REPLACE", ):
    """fill vg from given values (can be int,float,list,np array,dict)"""

    #type is float/int/bool ? 
    if (type(fill) is int) or (type(fill) is float) or (type(fill) is bool):

        verts = [i for i,v in enumerate(o.data.vertices)]
        vg.add(verts, fill, method)

        return None 

    #type is array ? numpy ?
    elif (type(fill) is list) or (type(fill).__module__ == np.__name__):

        for i,v in enumerate(fill):
            vg.add([i], v, method) #TODO importve with for_each set method, now available perhaps?

        return None 

    #type is dict ? 
    elif (type(fill) is dict):

        for k,v in fill.items():
            vg.add([k], v, method)

        return None 

    return None 

def create_vg(o, vg_name, fill=None, method="REPLACE", set_active=True):
    """create or refresh vg with given value(s) if not None"""

    vg = o.vertex_groups.get(vg_name)
    if (not vg):
        vg = o.vertex_groups.new(name=vg_name)

    fill_vg(o, vg, fill, method=method,)

    if (set_active):
        o.vertex_groups.active_index = vg.index

    return vg 

def create_vcol(o, vcol_name, fill=(0,0,0,1,), set_active=True):
    """create or refresh vcol with given value if not None"""
    
    #not ideal...
    bpy.context.view_layer.objects.active = o
    bpy.ops.geometry.color_attribute_add(domain='CORNER', color=fill, name=vcol_name,)
    
    vcol = o.data.color_attributes[o.data.color_attributes.active_color_index]
    
    return vcol
        
def set_vg_active_by_name(o, group_name, mode="vg"):
    """Set vg active if exist"""

    old = None

    #set active vg 
    if (mode=="vg"):
        
        vgs = o.vertex_groups
        if ( (len(vgs)==0) or (group_name not in vgs)):
            return "ERROR_NOT_FOUND"

        old = vgs[vgs.active_index].name

        for i,g in enumerate(vgs):
            if (g.name==group_name):
                vgs.active_index = i 

    #set active vcol-attr
    elif (mode=="vcol"):

        vcols = o.data.color_attributes 
        if ( (len(vcols)==0) or (group_name not in vcols)):
            return "ERROR_NOT_FOUND"

        old = vcols[vcols.active_color_index].name

        for i,g in enumerate(vcols):
            if (g.name==group_name):
                vcols.active_color_index = i 

    #return old active for overrides
    return old

def reverse_vg(o,vg):
    """reverse vg with ops.vertex_group_invert()"""

    #override selection/active ob
    with override_utils.mode_override(selection=[o], active=o, mode="OBJECT"):
        #set active vg
        oan = set_vg_active_by_name(o,vg.name)
        #operation
        bpy.ops.object.vertex_group_invert()
        #reset active 
        set_vg_active_by_name(o,oan)

    return None


def smooth_vg(o, vg, intensity):
    """reverse vg with ops.vertex_group_invert()"""

    if (not intensity):
        return None 

    #override selection/active ob & mode
    with override_utils.mode_override(selection=[o], active=o, mode="PAINT_WEIGHT"):
        #set active vg
        oan = set_vg_active_by_name(o,vg.name)
        #operation
        bpy.ops.object.vertex_group_smooth(factor=0.2, repeat=intensity,)
        #reset active 
        set_vg_active_by_name(o,oan)

    return None


def expand_weights(o, vg, iter=2):
    """expand given weight"""

    for i in range(iter):
        
        o.vertex_groups.active_index = vg.index
        me = o.data

        weights = [0.0] * len(me.vertices)
        for f in me.polygons:
            flag = False
            for vi in f.vertices:
                w = vg.weight(vi)
                if(w > 0.0):
                    flag = True
                    break
            if(flag):
                for vi in f.vertices:
                    weights[vi] = 1.0

        for i, w in enumerate(weights):
            vg.add([i], w, 'ADD', )

    return None 


def kd_trees_rays(ob, verts_idx=None, distance=1, offset=0):

    vert_len = len(ob.vertices)
    non_target = []
    w = [0.0] * vert_len
    Tree = KDTree(vert_len)

    for v in ob.vertices:
        if (v.index in verts_idx):
            Tree.insert(v.co, v.index)
            w[v.index] = 1.0
        else:
            non_target.append(v)

    Tree.balance()

    for nb in non_target:
        fvs = Tree.find_range(nb.co, offset + distance)
        ds = []
        for fv, fi, fd in fvs:
            ds.append(fd)
        val = 0.0
        if (len(ds)):
            delta = (distance - offset)
            if (delta!=0):
                val = 1.0 - ((min(ds) - offset) / delta)
        w[nb.index] = val

    return w


def is_vg_active(o, vg_name):

    if (vg_name==""):
        return False
    
    if (bpy.context.mode=="PAINT_WEIGHT"):

        if (vg_name not in o.vertex_groups):
            return False

        for i,vg in enumerate(o.vertex_groups):
            if (vg.name==vg_name):
                return (i==o.vertex_groups.active_index)

    elif (bpy.context.mode=="PAINT_VERTEX"):

        if (vg_name not in o.data.color_attributes):
            return False

        for i,vg in enumerate(o.data.color_attributes):
            if (vg.name==vg_name):
                return (i==o.data.color_attributes.active_color_index)

    return False


# oooooo     oooo                 ooooooooooooo                                          .o88o.
#  `888.     .8'                  8'   888   `8                                          888 `"
#   `888.   .8'    .oooooooo           888      oooo d8b  .oooo.   ooo. .oo.    .oooo.o o888oo   .ooooo.  oooo d8b
#    `888. .8'    888' `88b            888      `888""8P `P  )88b  `888P"Y88b  d88(  "8  888    d88' `88b `888""8P
#     `888.8'     888   888            888       888      .oP"888   888   888  `"Y88b.   888    888ooo888  888
#      `888'      `88bod8P'            888       888     d8(  888   888   888  o.  )88b  888    888    .o  888
#       `8'       `8oooooo.           o888o     d888b    `Y888""8o o888o o888o 8""888P' o888o   `Y8bod8P' d888b
#                 d"     YD
#                 "Y88888P'


class SCATTER5_OT_vg_transfer(bpy.types.Operator):

    bl_idname  = "scatter5.vg_transfer"
    bl_label   = translate("Transfer Weight from source to destination")
    bl_options = {'REGISTER', 'INTERNAL'}

    obj_name : bpy.props.StringProperty()
    vg_source : bpy.props.StringProperty()
    vg_destination : bpy.props.StringProperty()
    display_des : bpy.props.BoolProperty()
    method : bpy.props.EnumProperty(items=[('ADD',translate('Add'),''),('SUBTRACT',translate('Subtract'),''),('REPLACE',translate('Replace'),''),], default='REPLACE')
    eval_mod : bpy.props.BoolProperty(description=translate("Try to evaluate modifiers that might affect vertex-group when transferring data from source to destination"),)

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return bpy.context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        if (self.vg_source==""):
            return {'FINISHED'}
        if (self.vg_destination==""):
            return {'FINISHED'}

        if self.obj_name:
              obj = bpy.data.objects[self.obj_name]
        else: obj = bpy.context.object

        w = get_weight(obj, self.vg_source, eval_modifiers=self.eval_mod )
        create_vg(obj, self.vg_destination, fill=w, method=self.method )

        #UNDO_PUSH 
        bpy.ops.ed.undo_push(message=translate("Transfer Weight"))

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        if (self.obj_name):
              obj = bpy.data.objects[self.obj_name]
        else: obj = bpy.context.object

        layout.prop_search(self, "vg_source", obj, "vertex_groups", text=translate("source"))
        if (self.display_des):
            layout.prop_search(self, "vg_destination", obj, "vertex_groups", text=translate("description"))

        layout.prop(self,"method",text=translate("Mix Mode"))
        layout.prop(self,"eval_mod",text=translate("Try to Evaluale Modifiers"))

        return 


#   .oooooo.                   o8o            oooo             ooooooooo.              o8o                  .
#  d8P'  `Y8b                  `"'            `888             `888   `Y88.            `"'                .o8
# 888      888    oooo  oooo  oooo   .ooooo.   888  oooo        888   .d88'  .oooo.   oooo  ooo. .oo.   .o888oo
# 888      888    `888  `888  `888  d88' `"Y8  888 .8P'         888ooo88P'  `P  )88b  `888  `888P"Y88b    888
# 888      888     888   888   888  888        888888.          888          .oP"888   888   888   888    888
# `88b    d88b     888   888   888  888   .o8  888 `88b.        888         d8(  888   888   888   888    888 .
#  `Y8bood8P'Ybd'  `V88V"V8P' o888o `Y8bod8P' o888o o888o      o888o        `Y888""8o o888o o888o o888o   "888"


class SCATTER5_OT_vg_quick_paint(bpy.types.Operator):
    """operator used to quickly create or paint vg or vcol, with mutli-surface support, for the active psy or active group context or else
    due to the nature of the geoscatter multi-surface workflow, this tool will set up a painting mode on many objects simultaneously"""

    bl_idname  = "scatter5.vg_quick_paint"
    bl_label   = translate("Create a New Vertex-Data")
    bl_options = {'REGISTER', 'INTERNAL'}

    group_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #just enter paint mode on a group name? if create new leave empty
    mode : bpy.props.StringProperty(default="vg", options={"SKIP_SAVE",},) #create or enter in vg/vcol
    api : bpy.props.StringProperty() #if create new, set given api string

    context_surfaces : bpy.props.StringProperty(default="*PSY_CONTEXT*", options={"SKIP_SAVE",},)
    
    new_name : bpy.props.StringProperty(name="Name", options={"SKIP_SAVE",},) #if creation of a new data, user can choose name
    base_color : bpy.props.FloatVectorProperty(default=(0,0,0,1,), size=4, options={"SKIP_SAVE",},) #canvas color if user create vcol
    set_color : bpy.props.FloatVectorProperty(default=(-1,-1,-1), size=3, options={"SKIP_SAVE",},) #set brush color if user enter vcol mode


    @classmethod
    def description(cls, context, properties): 
        p = properties
        des = ""
        if (p.group_name==""):
            des += translate("Create a new vertex data shared across all surfaces")
        else:
            des += translate("Set this data active across all surfaces, if found") 
            des += " " + translate("and enter the context paint mode")  
        return des

    def __init__(self):
        """store surfaces target"""
        
        #find surfaces automatically depending on group/psy interface context
        if (self.context_surfaces=="*PSY_CONTEXT*"):
            
            #get active psy, or group
            emitter = bpy.context.scene.scatter5.emitter
            itm = emitter.scatter5.get_psy_active()
            if (itm is None):
                itm = emitter.scatter5.get_group_active()
            
            #get their surfaces
            self.surfaces = itm.get_surfaces()
            
        #find surfaces simply using the active emitter
        elif (self.context_surfaces=="*EMITTER_CONTEXT*"):
            self.surfaces = [bpy.context.scene.scatter5.emitter]
            
        #custom surface context
        else: 
            self.surfaces = [ bpy.data.objects[sn] for sn in self.context_surfaces.split("_!#!_") ]
        
        return None 

    def invoke(self, context, event):

        #create new group if given group is empty?
        if (self.group_name==""):
            #set a default name
            self.new_name="Vcol" if (self.mode=="vcol") else "Vgroup"
            #call draw(), after confirm will call exec()
            return bpy.context.window_manager.invoke_props_dialog(self)

        return self.execute(context)

    def draw(self, context):
        """if create new data, user need to confirm name in dialog box"""

        layout = self.layout
        layout.use_property_split = True
        layout.prop(self,"new_name",)

        return None

    def context_attributes(self, o):
        """return list of attributes, vgs or vcols, depending on chosen mode"""

        return o.data.color_attributes if (self.mode=="vcol") else o.vertex_groups

    def enter_paint_mode(self, context):

        #set the attr active over all surfaces 
        for o in self.surfaces:
            r = set_vg_active_by_name(o, self.group_name, mode=self.mode)
            
            #handle error, if group don't exist, then create the missing one!
            if (r=="ERROR_NOT_FOUND"):
                
                if (self.mode=="vcol"):
                    create_vcol(o, self.group_name,)
                elif (self.mode=="vg"):
                    create_vg(o, self.group_name,)

        #need to enter paint mode? perhaps already in
        if ((self.mode=="vcol") and (context.mode!="PAINT_VERTEX")) or ((self.mode=="vg") and (context.mode!="PAINT_WEIGHT")):
            
            target_paint = bpy.context.object

            #need to set an object as active?
            if (target_paint not in self.surfaces):
                for o in self.surfaces:
                    if (self.group_name in self.context_attributes(o)):
                        target_paint = o
                        break
            try: 
                #go in context painting mode
                bpy.context.view_layer.objects.active = target_paint
                bpy.ops.object.mode_set(mode="VERTEX_PAINT" if (self.mode=="vcol") else "WEIGHT_PAINT")

            except Exception as error: 
                #warn users if not possible
                bpy.ops.scatter5.popup_menu(
                    title=translate("Action Impossible"),
                    msgs=translate("We cannot paint on this surface: ")+f"'{target_paint.name}'",
                    icon="ERROR",
                    )
                print(error)
                return None

        #set color
        if ( (self.mode=="vcol") and (self.set_color!=(-1,-1,-1)) ):
            paint_sett = context.scene.tool_settings.unified_paint_settings
            paint_sett.use_unified_color = True
            paint_sett.color = self.set_color

        return None

    def create_new_data(self, context):

        #find name not taken, across all surfaces
        i = 1
        chosen_name = self.new_name
        while self.new_name in [d.name for o in self.surfaces for d in self.context_attributes(o)]:
            self.new_name = f"{chosen_name}.{i:03}"
            i+=1

        #create the layers, for each objects
        for o in self.surfaces: 

            if (self.mode=="vcol"):
                new = create_vcol(o, self.new_name,)
            elif (self.mode=="vg"):
                new = create_vg(o, self.new_name,)

        #set scatter api 
        if (self.api!=""):
            emitter = context.scene.scatter5.emitter
            exec(f"{self.api}='{self.new_name}'")

        return None 

    def execute(self, context):
        """dispatch between create new or enter painting"""

        if (self.group_name==""):
              self.create_new_data(context)
        else: self.enter_paint_mode(context)

        return {'FINISHED'}
        

#       .o.             .o8        .o8       oooooo     oooo                 oooooooooooo       .o8   o8o      .
#      .888.           "888       "888        `888.     .8'                  `888'     `8      "888   `"'    .o8
#     .8"888.      .oooo888   .oooo888         `888.   .8'    .oooooooo       888          .oooo888  oooo  .o888oo
#    .8' `888.    d88' `888  d88' `888          `888. .8'    888' `88b        888oooo8    d88' `888  `888    888
#   .88ooo8888.   888   888  888   888           `888.8'     888   888        888    "    888   888   888    888
#  .8'     `888.  888   888  888   888            `888'      `88bod8P'        888       o 888   888   888    888 .
# o88o     o8888o `Y8bod88P" `Y8bod88P"            `8'       `8oooooo.       o888ooooood8 `Y8bod88P" o888o   "888"
#                                                            d"     YD
#                                                            "Y88888P'


class SCATTER5_OT_vg_add_falloff(bpy.types.Operator): 
    """add vg edit, == map curve graph for vg, OPERATOR FOR PROCEDURAL MASK VG ONLY"""

    bl_idname = "scatter5.vg_add_falloff"
    bl_label = translate("Add Weight Remap")
    bl_description = ""
    bl_options = {'INTERNAL','UNDO'}

    mask_name : bpy.props.StringProperty()

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter 
        masks = emitter.scatter5.mask_systems
        mod_name = f"Scatter5 Remapping {self.mask_name}"

        if (mod_name in emitter.modifiers) or (self.mask_name not in masks) or (self.mask_name not in emitter.vertex_groups):
            return {'FINISHED'}
                    
        m = emitter.modifiers.new(name=mod_name, type="VERTEX_WEIGHT_EDIT" )
        m.falloff_type  = "CURVE"
        m.vertex_group  = self.mask_name
        m.show_expanded = False

        #add newly created modifier to mask mod_list
        masks[self.mask_name].mod_list += mod_name+"_!#!_"
            
        return {'FINISHED'}
    

# oooooooooooo                                     .oooooo..o           oooo                          .    o8o
# `888'     `8                                    d8P'    `Y8           `888                        .o8    `"'
#  888          .oooo.    .ooooo.   .ooooo.       Y88bo.       .ooooo.   888   .ooooo.   .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  888oooo8    `P  )88b  d88' `"Y8 d88' `88b       `"Y8888o.  d88' `88b  888  d88' `88b d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#  888    "     .oP"888  888       888ooo888           `"Y88b 888ooo888  888  888ooo888 888         888    888  888   888  888   888
#  888         d8(  888  888   .o8 888    .o      oo     .d8P 888    .o  888  888    .o 888   .o8   888 .  888  888   888  888   888
# o888o        `Y888""8o `Y8bod8P' `Y8bod8P'      8""88888P'  `Y8bod8P' o888o `Y8bod8P' `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o


class SCATTER5_OT_facesel_to_vcol(bpy.types.Operator):

    bl_idname = "scatter5.facesel_to_vcol"
    bl_label = ""
    bl_description = translate("Select Face(s)")
    bl_options = {'REGISTER'}

    #name of the layer is hardcoded for now, maybe later we'll allow custom layer?
    vcol_name = ".S5FacePreview"

    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #use "_!#!_" to separate surfaces obj names

    @classmethod
    def poll(cls, context,):
        return (context.window_manager.scatter5.mode!="FACE_SEL")

    def __init__(self):
        
        self.surfaces = [ bpy.data.objects[n] for n in self.surfaces_names.split("_!#!_") if (n in bpy.data.objects) ]
        self.restore_active_vcol = {}
        self.restore_shading = ""

        return None 

    class InfoBox_facesel_to_vcol(SC5InfoBox):
        """append an instance of the infobox"""
        pass

    def invoke(self, context, event,):
        
        #user did not defined surfaces?
        if (len(self.surfaces)==0):
            return {'FINISHED'}

        #prepare selection
        for o in context.selected_objects:
            o.select_set(False)
        for o in self.surfaces: 
            o.select_set(True)
        context.view_layer.objects.active = self.surfaces[0]

        #set vcol as active
        for o in self.surfaces:
            #store old active vcol layer 
            if o.data.color_attributes.active:
                self.restore_active_vcol[o.name] = o.data.color_attributes.active.name
            #create new vcol if needed?
            vcol = o.data.color_attributes.get(self.vcol_name)
            if (vcol is None):
                o.data.vertex_colors.new(name=self.vcol_name)
                vcol = o.data.color_attributes.get(self.vcol_name)
            #set vcol as active 
            o.data.color_attributes.active_color = vcol
            continue 

        #set shading visual cue, if user is from view3d
        if (context.space_data.type=="VIEW_3D"):
            self.restore_shading = context.space_data.shading.color_type
            context.space_data.shading.color_type = 'VERTEX'
        
        #go in edit mode 
        bpy.ops.object.mode_set(mode="EDIT")
        #set selection to faces
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type="FACE",)

        #draw infobox on screen
        t = generic_infobox_setup(translate("Faces Preview Selection"),
                                  translate("Select preview region of this emitter"),
                                  ["• "+translate("Quit Edit-Mode to Confirm"),
                                   "• "+translate("Press 'ENTER' to Confirm"),
                                   "• "+translate("Press 'ESC' to Cancel"),
                                  ],)
        self.InfoBox_facesel_to_vcol.init(t)
        
        #update scatter5 mode property     
        context.window_manager.scatter5.mode = "FACE_SEL"

        #start modal 
        context.window_manager.modal_handler_add(self)  

        return {'RUNNING_MODAL'}

    def modal(self, context, event,):

        if (context.mode!="EDIT_MESH"):
            self.confirm(context)
            self.exit(context)
            return {'FINISHED'}

        elif (event.type=='RET'):
            self.confirm(context)
            self.exit(context)
            return {'FINISHED'}

        elif (event.type=='ESC'):
            self.exit(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def confirm(self, context,): 
        """write selection into vertex color layers for each surfaces"""

        #set environment 
        paint_settings = context.scene.tool_settings.unified_paint_settings
        paint_settings.use_unified_color = True
        old_color = paint_settings.color[:]

        for o in self.surfaces: 

            #set the object active 
            context.view_layer.objects.active = o
            old_use_paint_mask = o.data.use_paint_mask

            #go in vcol
            bpy.ops.object.mode_set(mode="VERTEX_PAINT")

            #set all color to black
            o.data.use_paint_mask = False
            paint_settings.color = (0,0,0)
            bpy.ops.paint.vertex_color_set()

            #set selection color to white
            o.data.use_paint_mask = True
            paint_settings.color = (1,1,1)
            bpy.ops.paint.vertex_color_set()

            #reset local
            o.data.use_paint_mask = old_use_paint_mask

            #save square area preview for density estimation
            o.scatter5.s_visibility_facepreview_area = o.scatter5.estimate_square_area(get_selection=True,)
            continue 

        #reset environment 
        paint_settings.color = old_color

        return None 

    def exit(self, context,):
        """called when quitting the modal"""
        
        #back to object mode
        bpy.ops.object.mode_set(mode="OBJECT")

        #remove screen indication 
        self.InfoBox_facesel_to_vcol.deinit()

        #restore original shading state
        if (self.restore_shading):
            context.space_data.shading.color_type = self.restore_shading

        #restore original active vcolor
        if (self.restore_active_vcol):
            for k,v in self.restore_active_vcol.items():
                o = bpy.data.objects[k]
                if (v in o.data.color_attributes):
                    o.data.color_attributes.active_color = o.data.color_attributes[v]

        #update scatter5 mode property
        context.window_manager.scatter5.mode = ""

        return None

#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (

    SCATTER5_OT_vg_transfer,
    SCATTER5_OT_vg_quick_paint,
    SCATTER5_OT_vg_add_falloff,
    SCATTER5_OT_facesel_to_vcol,

    )