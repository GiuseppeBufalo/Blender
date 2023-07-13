
#####################################################################################################
#
# oooooooooo.                      oooo
# `888'   `Y8b                     `888
#  888     888  .ooooo.   .ooooo.   888   .ooooo.   .oooo.   ooo. .oo.
#  888oooo888' d88' `88b d88' `88b  888  d88' `88b `P  )88b  `888P"Y88b
#  888    `88b 888   888 888   888  888  888ooo888  .oP"888   888   888
#  888    .88P 888   888 888   888  888  888    .o d8(  888   888   888
# o888bood8P'  `Y8bod8P' `Y8bod8P' o888o `Y8bod8P' `Y888""8o o888o o888o
#
#####################################################################################################




import bpy

from ... import utils 
from ... utils.str_utils import no_names_in_double

from ... ui import ui_templates
from ... resources.icons import cust_icon
from ... resources.translate import translate


url = "https://www.geoscatter.com/" #just link to website?




# oooooooooo.
# `888'   `Y8b
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888      888  888      .oP"888    `88..]88..8'
#  888     d88'  888     d8(  888     `888'`888'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'




def draw_settings(layout,i):

    scat_scene  = bpy.context.scene.scatter5
    emitter     = scat_scene.emitter
    masks       = emitter.scatter5.mask_systems
    m           = masks[i]
    mod         = emitter.modifiers.get("Scatter5 Dynamic Paint Canvases")
    if mod:
        surface =  mod.canvas_settings.canvas_surfaces[m.name]
        col     = surface.brush_collection 

    if (mod is None) or (not col):

        warn = layout.row(align=True)
        warn.alignment = "CENTER"
        warn.active = False
        warn.scale_y = 0.9
        warn.label(text=translate("Modifier Missing, Please Refresh"),icon="ERROR")

        return 

    layout.separator(factor=0.5)

    #layout setup 

    row = layout.row()
    row.row()
    row.scale_y = 0.9

    row1 = row.row()
    row1.scale_x = 1.1
    lbl = row1.column()
    lbl.alignment="RIGHT"

    row2 = row.row()
    prp = row2.column()

    #settings

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    collarea= prp.column(align=True)

    #do a box of Boolean object with add ect. 
    if len(col.objects):

        for idx,o in enumerate(col.objects):

            box = collarea.box()
            box.scale_y = 0.70

            if idx == 0:
                  lbl.label(text=translate("Object(s)")) 
            else: lbl.separator(factor=3.9)

            app = box.row(align=True)
            app.label(text=str(o.name))
            op = app.operator("scatter5.mask_boolean_parameters",text="",icon="MODIFIER_OFF",emboss=False)
            op.obj_name = o.name
            op.surface_name=surface.name;
            op = app.operator("scatter5.exec_line",text="",icon="TRASH",emboss=False)
            op.api = f"o=bpy.data.objects['{o.name}']; bpy.data.collections['{col.name}'].objects.unlink(o)"


    else:
        lbl.label(text=translate("Object(s)")) 
        box = collarea.box()
        box.scale_y = 0.70
        msg = box.row()
        msg.active = False
        msg.label(text=translate("Add Object(s) Below"))


    lbl.label(text="")
    collarea.operator("scatter5.mask_boolean_add_to_coll",icon="ADD",text=translate("Add Selected")).surface_name = m.name

    lbl.separator(factor=3.7)
    prp.separator(factor=3.7)

    lbl.label(text=translate("Modifiers")) #fake refresh, just needed to refresh dynamic paint
    re = prp.operator("scatter5.refresh_mask",text=translate("Refresh"),icon="FILE_REFRESH")
    re.mask_type = m.type
    re.mask_idx = i 

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Remap"))
    mod_name   = f"Scatter5 Remapping {m.name}"
    if (mod_name in emitter.modifiers) and (emitter.modifiers[mod_name].falloff_type=="CURVE"):
        mod = emitter.modifiers[mod_name]
        remap = prp.row(align=True)
        o = remap.operator("scatter5.graph_dialog",text=translate("Remap Values"),icon="FCURVE")
        o.source_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}']"
        o.mapping_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}'].map_curve"
        o.mask_name = m.name
        
        butt = remap.row(align=True)
        butt.operator("scatter5.property_toggle",
               text="",
               icon="RESTRICT_VIEW_OFF" if mod.show_viewport else"RESTRICT_VIEW_ON",
               depress=mod.show_viewport,
               ).api = f"bpy.context.scene.scatter5.emitter.modifiers['{mod_name}'].show_viewport"
    else:
        o = prp.operator("scatter5.vg_add_falloff",text=translate("Add Remap"),icon="FCURVE")
        o.mask_name = m.name

    layout.separator()

    return 



#       .o.             .o8        .o8
#      .888.           "888       "888
#     .8"888.      .oooo888   .oooo888
#    .8' `888.    d88' `888  d88' `888
#   .88ooo8888.   888   888  888   888
#  .8'     `888.  888   888  888   888
# o88o     o8888o `Y8bod88P" `Y8bod88P"



def create_dynamic_paint_canvas(o, canvas_name):
    """create dynamic paint canvas set-up"""
    #used in clipping and boolean mask 
    
    #only one dynamic paint modifier is allowed per object
    if "DYNAMIC_PAINT" not in [m.type for m in o.modifiers]:
       m = o.modifiers.new(name="Scatter5 Dynamic Paint Canvases",type="DYNAMIC_PAINT")
       m.ui_type = 'CANVAS'
       m.show_expanded = False
       #try to create a new canvas, forced to use ops..
       try: len(m.canvas_settings.canvas_surfaces) #dynamic paint api is bad... 
       except: bpy.ops.dpaint.type_toggle({"object":o},type='CANVAS')
    else:
        m = [m for m in o.modifiers if m.type == "DYNAMIC_PAINT"][0]
        
    s = m.canvas_settings.canvas_surfaces
    if canvas_name not in s:
        bpy.ops.dpaint.surface_slot_add({"object":o})
        s[-1].name = canvas_name

    return m


def create_dynamic_paint_brush(o, boolean=True):
    """create dynamic paint canvas for brush"""
    #used in clipping and boolean mask 
    
    #only one dynamic paint modifier is allowed per object
    if "DYNAMIC_PAINT" not in [m.type for m in o.modifiers]:
       m = o.modifiers.new(name="Scatter5 Dynamic Paint Brush",type="DYNAMIC_PAINT")
       m.ui_type = 'BRUSH'
       bpy.ops.dpaint.type_toggle({"object":o}, type='BRUSH')
    else:
        m = [m for m in o.modifiers if m.type == "DYNAMIC_PAINT"][0]
    
    return m 


def _refresh_create_set_up( emitter, mask_name,):

    #create the distance culling
    vg = utils.vg_utils.create_vg(emitter, mask_name, fill=1.0, )
    vg.lock_weight = True

    #add default collection if not alread
    utils.coll_utils.create_scatter5_collections()

    #add dynamic paint set up for canvas
    canvas_name = mask_name
    m = create_dynamic_paint_canvas(emitter , canvas_name)
    c = m.canvas_settings.canvas_surfaces[canvas_name]
    c.surface_format = 'VERTEX'
    c.surface_type   = 'WEIGHT'
    c.frame_start = 0
    c.frame_end   = 9999
    c.output_name_a = mask_name
    c.use_dissolve = True
    c.dissolve_speed = 1
    c.use_dissolve_log = False

    #add new mask boolean collection 
    if not c.brush_collection:
        col_brush = utils.coll_utils.create_new_collection("Geo-Scatter Proximity Brushes", parent_name="Geo-Scatter Extra", prefix=True )
        c.brush_collection = col_brush

    #update dynamic paint 
    if bpy.context.scene.frame_current <= 0:
        bpy.context.scene.frame_current = 1 #dynamic paint don't calculate anything on frame 0
    v = c.brush_influence_scale
    c.brush_influence_scale +=1
    c.brush_influence_scale = v

    return 




def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type = "boolean"
    m.icon = "MOD_DYNAMICPAINT"
    m.name = m.user_name = no_names_in_double("DynamicPaint", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

    #create whole set-up 
    _refresh_create_set_up(emitter,m.name)

    #already scatter selection
    bpy.ops.scatter5.mask_boolean_add_to_coll(
        surface_name= m.name,
        )

    return 




# ooooooooo.              .o88o.                             oooo
# `888   `Y88.            888 `"                             `888
#  888   .d88'  .ooooo.  o888oo  oooo d8b  .ooooo.   .oooo.o  888 .oo.
#  888ooo88P'  d88' `88b  888    `888""8P d88' `88b d88(  "8  888P"Y88b
#  888`88b.    888ooo888  888     888     888ooo888 `"Y88b.   888   888
#  888  `88b.  888    .o  888     888     888    .o o.  )88b  888   888
# o888o  o888o `Y8bod8P' o888o   d888b    `Y8bod8P' 8""888P' o888o o888o




def refresh(i,obj=None):

    if obj: 
          emitter = obj
    else: emitter = bpy.context.scene.scatter5.emitter

    masks    = emitter.scatter5.mask_systems
    m        = masks[i]

    #refresh whole set up 
    _refresh_create_set_up(emitter,m.name)

    return 



# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.  oooo    ooo  .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b  `88.  .8'  d88' `88b
#  888`88b.    888ooo888  888   888   888  888   888   `88..8'   888ooo888
#  888  `88b.  888    .o  888   888   888  888   888    `888'    888    .o
# o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'     `8'     `Y8bod8P'




def remove(i):

    #remove whole dynamic cam paint set-up (clipping & culling)
    emitter  = bpy.context.scene.scatter5.emitter
    masks    = emitter.scatter5.mask_systems
    m        = masks[i]
    surfaces = emitter.modifiers["Scatter5 Dynamic Paint Canvases"].canvas_settings.canvas_surfaces
    surface  = surfaces[m.name]
    brush_collection = surface.brush_collection

    #link all objects in coll back in scene collection

    #delete collection 
    if brush_collection: 

        #remove object modifier then unlink
        for o in brush_collection.objects:
            #o.modifiers.remove(o.modifiers["Scatter5 Dynamic Paint Brush"]) 
            brush_collection.objects.unlink(o)

        #remove collection
        bpy.data.collections.remove(brush_collection)
    
    #remove dynamic paint surface (extremely bad api)
    with utils.override_utils.mode_override(selection=[emitter], active=emitter, mode="OBJECT"):

        for si,s in enumerate(surfaces):
            if (s == surface):
                break

        surfaces.active_index = si

        bpy.ops.dpaint.surface_slot_remove()

    #remove mask clipping from mask list,vg edit, vg 
    from ..remove import general_mask_remove
    general_mask_remove(obj_name=emitter.name, mask_idx=i) #remove vg, vgedit, mask from list, refresh viewport

    return 




#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P'



def selection_valid(selection):
    """filter selection""" 

    #get list of all objects already used by boolean in this scene
    brush_starts  = f"Scatter5 Proximity Brushes"
    mask_col      = bpy.data.collections.get("Geo-Scatter Extra")
    boolean_objs  = [o for col in mask_col.children if col.name.startswith("Geo-Scatter Proximity Brushes") for o in col.objects  ] 

    return [ o for o in selection  
                if  (o.type =="MESH") #must be mesh 
                #and (o not in boolean_objs) #must not be used by other collection already
                and ( len(o.scatter5.particle_systems)==0 ) #must not be an object that emit particles
                and (o is not bpy.context.scene.scatter5.emitter) #must not be emitter target
           ]  

def update_dynamic(surface_name):
    #update dynamic paint 
    emitter = bpy.context.scene.scatter5.emitter 
    if bpy.context.scene.frame_current <= 0:
        bpy.context.scene.frame_current = 1 #dynamic paint don't calculate anything on frame 0
    s = emitter.modifiers["Scatter5 Dynamic Paint Canvases"].canvas_settings.canvas_surfaces[surface_name]
    v = s.brush_influence_scale
    s.brush_influence_scale +=1
    s.brush_influence_scale = v
    return 

def paint_distance_upd(self,context):
    if not self.obj_name:
        return None
    o = bpy.data.objects[self.obj_name]
    m = o.modifiers["Scatter5 Dynamic Paint Brush"]
    m.brush_settings.paint_distance = self.paint_distance 
    update_dynamic(self.surface_name)
    return None 

def paint_source_upd(self,context):
    if not self.obj_name:
        return None
    o = bpy.data.objects[self.obj_name]
    m = o.modifiers["Scatter5 Dynamic Paint Brush"]
    m.brush_settings.paint_source = self.paint_source 
    update_dynamic(self.surface_name)
    return None 




class SCATTER5_OT_mask_boolean_add_to_coll(bpy.types.Operator):
    """add new objects in the boolean collection and set as boolean brush"""

    bl_idname  = "scatter5.mask_boolean_add_to_coll"
    bl_label   = translate("Add New Boolean Object")
    bl_options = {'INTERNAL','UNDO'}

    surface_name : bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        emitter     = bpy.context.scene.scatter5.emitter 
        mod         = emitter.modifiers["Scatter5 Dynamic Paint Canvases"]
        surface     = mod.canvas_settings.canvas_surfaces[self.surface_name]
        col         = surface.brush_collection 

        if not col: 
            return {'FINISHED'}


        s = selection_valid(bpy.context.selected_objects)
        
        #only if selection is not none 
        if len(s)==0:
            return {'FINISHED'}

        for o in s: 
            
            #add object in boolean collection
            if o.name not in col.objects:
                col.objects.link(o)

            #add dynamic paint brush set up 
            m = create_dynamic_paint_brush(o)
            m.brush_settings.paint_source = "VOLUME_DISTANCE"
            m.brush_settings.paint_distance = 3

        return {'FINISHED'}



class SCATTER5_OT_mask_boolean_parameters(bpy.types.Operator):
    """change boolean object properties"""

    bl_idname  = "scatter5.mask_boolean_parameters"
    bl_label   = translate("Boolean Object Properties")
    bl_options = {'REGISTER','INTERNAL'}

    obj_name : bpy.props.StringProperty()
    surface_name : bpy.props.StringProperty()

    paint_distance : bpy.props.FloatProperty(min=0,max=500,subtype="DISTANCE",update=paint_distance_upd )

    paint_source : bpy.props.EnumProperty(
        name = translate("Proximity"),
        default    = "VOLUME_DISTANCE",
        update     = paint_source_upd,
        items      = [
                      ("POINT"           ,translate("Proximity from Origin")           ,"" ,"EMPTY_AXIS"      ,1 ),
                      ("DISTANCE"        ,translate("Proximity from Faces")            ,"" ,"DRIVER_DISTANCE" ,2 ),
                      ("VOLUME"          ,translate("Inside Volume")                   ,"" ,"MESH_CUBE"       ,3 ),
                      ("VOLUME_DISTANCE" ,translate("Proximity from Faces/Volume")     ,"" ,"META_CUBE"       ,4 ),
                      ],) 

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):

        #get param right
        obj = bpy.data.objects[self.obj_name]
        m = obj.modifiers["Scatter5 Dynamic Paint Brush"]
        self.paint_distance = m.brush_settings.paint_distance 
        self.paint_source  = m.brush_settings.paint_source 

        #set selected for visual clue
        for o in bpy.data.objects:
            o.select_set(state=False)
        obj.select_set(state=True)

        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        row = self.layout.row()
        row.label(text=translate("Method")+":")
        row.prop(self,"paint_source",text="")

        if self.paint_source != "VOLUME":
            row = self.layout.row()
            row.label(text=translate("Proximity")+":")
            row.prop(self,"paint_distance",text="")

        return 