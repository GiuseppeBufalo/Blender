bl_info = {
    "name": "Simple Sketch",
    "author": "Chipp Walters",
    "version": (0, 9, 39),
    "blender": (2, 93, 0),
    "location": "View3D > Tool Shelf > SSketch",
    "description": "Simple Sketch Style Renderer",
    "warning": "",
    "wiki_url": "http://cw1.me/ssdocs",
    "category": "3D View",
}

import bpy
import webbrowser
#from bpy.props import StringProperty

# USED FOR DEBUGGING
import datetime
#print ("The Date Is: ",datetime.datetime.now())

class AltLineArtPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Simple Sketch"
    bl_idname = "OBJECT_PT_altlineartpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SSketch"
    
    def draw_header_preset(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("ko.open_help_url", icon='QUESTION', text="").url = "http://cw1.me/ssdocs"
        #row.operator("ss.open_help_url", icon='QUESTION', text="")
        
        row.separator()

    def draw(self, context):
                    
        layout = self.layout

        obj = context.object
        scene = context.scene

        # WARNING TO BE IN CAMERA VIEW
        row = layout.row()
        row.label(text="   *Be sure to be in Camera View!")

        # TOGGLE LINE ART
        row = layout.row()
        row.scale_y = 2.0
        row.operator("chippops.alt_line_art", icon='FILE_3D')

        # UTILS
        row = layout.row()
        row.scale_y = 2.0
        row.label(text="HANDY UTILITIES")
         
         # TOGGLE OVERLAYS
        row = layout.row()
        row.prop(bpy.context.space_data.overlay,"show_overlays", text="Show Overlays (off for render)" )

        # SHOW WIRES AND BOUNDING BOXES
        row = layout.row()
        row.prop(bpy.context.scene.my_tool2,"p_show_wires_boxes", text="Show Wires and Bounding Boxes")
        
        # SELECT WIRES AND BOUNDS
        row = layout.row()
        row.operator("chippops.alt_select_wires_bounds", text="Select Wires and Bounding Boxes")

        
        t_line_art_mode = altCheckMode()
        
        if t_line_art_mode:
            altP2 = bpy.context.scene.my_tool2
            row = layout.row()
            row.prop(bpy.context.scene.my_tool2,"p_show_lineart_collection", text="Line Art Display")
                            
#            # TOGGLE LINE ART COLLECTION          
#            row = layout.row()
#            row.scale_y = 2.0
#            if altP.p_show_lineart_collection == True:
#                row.operator("chippops.alt_toggle_lineart_collection", icon='HIDE_ON')
#            else:
#                row.operator("chippops.alt_toggle_lineart_collection", icon='HIDE_OFF')
            
            # TOGGLE EXTRAS
#            row = layout.row()
#            row.operator("chippops.alt_toggle_extras", icon='HIDE_OFF')


            
            # RENDER LINE ART
            row = layout.row()
            row.scale_y = 2.0
            row.operator("chippops.alt_render_viewport", icon='RESTRICT_RENDER_OFF')
            #RENDER ANIMATION LINE ART
            row = layout.row()
            #row.scale_y = 2.0
            row.operator("chippops.alt_render_animation", icon='OUTLINER_OB_CAMERA')


            # LINE WIDTHS
            # HEAVY
            row = layout.row()
            row.label(text="Heavy Line")
            col = self.layout.column(align=True)
            col.prop(bpy.data.objects["Line Art Heavy"].grease_pencil_modifiers["Line Art"], "thickness", text="Thickness")
            
            #THIN
            row = layout.row()
            row.label(text="Thin Line")
            col = self.layout.column(align=True)
            col.prop(bpy.data.objects["Line Art Thin"].grease_pencil_modifiers["Line Art"], "thickness", text="Thickness")
            # CREASE THRESHOLD MUST BE ENTERED IN RADIANS
            col.prop(bpy.data.objects["Line Art Thin"].grease_pencil_modifiers["Line Art"], "crease_threshold", slider=True)
            
            # SHADOW and SHADE SETTINGS
            row = layout.row()
            row.label(text="Shadow")
            col = self.layout.column(align=True)
            col.prop(bpy.context.space_data.shading,"shadow_intensity", text="Shadow")
            
            # COLOR
            row = layout.row()
            row.label(text="Colors")            
            row = layout.row()
            row.prop(bpy.context.scene.my_tool2,"p_backcolor", text="   Back Color")   
            row = layout.row()
            row.prop(bpy.context.scene.my_tool2,"p_forecolor", text="   Fore Color")   
           
            row = layout.row()
            row.operator("chippops.alt_setcolors")
            row = layout.row()

            # LIGHT DIRECTION
            row = layout.row()
            row.label(text="Shadow Direction")            
            col = self.layout.column(align=True)
            col.prop(scene.display, "light_direction", text="")
            #bpy.context.scene.display.light_direction
            
            # STROKE THICKNESS
            row = layout.row()
            row.label(text="Stroke Mode")            
            row = layout.row()
            row.prop(bpy.context.scene.my_tool2,"p_stroke_thickness_space", text="")
 
class SS_OpenHelpURL(bpy.types.Operator):
    """HELP"""
    bl_idname = "ss.open_help_url" 
    bl_label = "SIMPLE SKETCH Help"
    bl_description = 'Open SIMPLE SKETCH documentation'
    bl_options = {'INTERNAL', 'UNDO'}
    
    url : bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.wm.url_open(url = self.url)
        return {'FINISHED'}  

#    def execute(self, context):
#        url="https://docs.google.com/document/d/1Ui9rjORJ29Zg4gTEuaQvYBal6XT12SkfuJ6irL0mAFg/edit?usp=sharing"					
#        try:
#            webbrowser.open(url)
#        except Exception as e:
#            bpy.ops.wm.url_open(url=url)
#        return {'FINISHED'}	
               

class Alt_Line_Art(bpy.types.Operator):
    """Toggles ON and OFF Line Art"""
    bl_idname = "chippops.alt_line_art"
    bl_label = "Toggle SIMPLE SKETCH"

    def execute(self, context):
        
        if (2, 93, 0) > bpy.app.version:
            self.report({'ERROR'}, "You must use Blender 2.93+ to use SIMPLE SKETCH!")
            return {'FINISHED'}

        #global g_run_first_time, g_extras_on   
               
        C = bpy.context
        D = bpy.data
        altP = bpy.context.scene.my_tool
        altP2 = bpy.context.scene.my_tool2
        scene = C.scene
        
        try:
            t = altP.p_first_use
        except:
            altP.p_first_use = True
        
        if altP.p_first_use == True:

            #INITIALIZE PROPS
            altInitProps()

        if D.collections.get('Line Art'):
            # TOGGLINE LINE ART OFF
            # RESET VIEWPORT PROPS TO ORIG
            altShowExtras()
            altShowOrigScene()
            
            # LINE ART COLLECTION EXISTS SO STORE THESE PARAMS
            altP.p_thin_line = bpy.data.objects["Line Art Thin"].grease_pencil_modifiers["Line Art"].thickness
            altP.p_heavy_line = bpy.data.objects["Line Art Heavy"].grease_pencil_modifiers["Line Art"].thickness
            altP.p_thin_crease_threshold = bpy.data.objects["Line Art Thin"].grease_pencil_modifiers["Line Art"].crease_threshold
            altP.p_line_art_shadow_intensity = bpy.context.space_data.shading.shadow_intensity
            altP2.p_stroke_thickness_space = bpy.data.objects["Line Art Heavy"].data.stroke_thickness_space
            
            # LINE COLOR
            altP2.p_forecolor = bpy.data.objects["Line Art Thin"].data.layers["Lines"].tint_color 
            # BACKGROUND COLOR
            altP2.p_backcolor = bpy.context.space_data.shading.background_color
                       
            collection = D.collections['Line Art']
            #collection = bpy.data.collections.get('collection_to_del')
         
            for obj in collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            
            # DELETE CURRENT LINE ART COLLECTION   
            bpy.data.collections.remove(collection)
            
            # SAVE THEN TURN ON OVERLAYS 
            altP.p_show_overlays = bpy.context.space_data.overlay.show_overlays
            bpy.context.space_data.overlay.show_overlays = True

            # STORE LINE ART show_object_outline and RESTORE ORIG
            altP.p_show_object_outline_la = bpy.context.space_data.shading.show_object_outline 
            bpy.context.space_data.shading.show_object_outline = altP.p_show_object_outline_orig  
           
        
                        
            # RESET VIEWPORT SETTINGS
            # USE TRY FOR VERY FIRST USE OF TOGGLE
            try:
                bpy.context.space_data.shading.type = altP.p_shading_type
                bpy.context.space_data.shading.light = altP.p_shading_light
                bpy.context.space_data.shading.show_shadows = altP.p_show_shadow
                bpy.context.space_data.shading.shadow_intensity = altP.p_shadow_intensity
                bpy.context.space_data.shading.background_type = altP.p_shading_bg_type
                bpy.context.space_data.shading.background_color = altP.p_shading_bg_color
                bpy.context.space_data.shading.color_type = altP.p_shading_color_type
                bpy.context.scene.display.shadow_focus = altP.p_shadow_focus
                bpy.context.space_data.shading.show_xray = altP.p_show_xray
                bpy.context.space_data.shading.show_cavity = altP.p_show_cavity
            
            except:
                pass

        else:
            # TOGGLINE LINE ART ON
            # STORING VIEWPORT PROPS SO WE CAN RELOAD LATER
            altStoreExtras()
            altStoreOrigScene()
                
            collection = D.collections.new('Line Art')
            C.scene.collection.children.link(collection)
            C.view_layer.active_layer_collection = C.view_layer.layer_collection.children['Line Art']

            # CREATE LINE ART OBJECT 2
            bpy.ops.object.gpencil_add(align='WORLD', location=(0, 0, 0), scale=(1, 1, 1), type='LRT_SCENE')
            line_art_obj = bpy.context.object
            line_art_obj.name = "Line Art Thin"
                
            # SET LINE ART PARAMS
            line_art_obj.grease_pencil_modifiers["Line Art"].use_material = False
            line_art_obj.grease_pencil_modifiers["Line Art"].use_edge_mark = False
            line_art_obj.grease_pencil_modifiers["Line Art"].use_contour = False
            line_art_obj.grease_pencil_modifiers["Line Art"].use_edge_mark = True
            
            line_art_obj.grease_pencil_modifiers["Line Art"].thickness = altP.p_thin_line
            line_art_obj.grease_pencil_modifiers["Line Art"].crease_threshold = altP.p_thin_crease_threshold

            line_art_obj.data.layers["Lines"].use_lights = False
            line_art_obj.data.stroke_thickness_space = altP2.p_stroke_thickness_space
            
            line_art_obj.show_in_front = True
            bpy.context.object.data.layers["Lines"].tint_factor = 1
            
            # CREATE LINE ART OBJECT 1
            bpy.ops.object.gpencil_add(align='WORLD', location=(0, 0, 0), scale=(1, 1, 1), type='LRT_SCENE')
            line_art_obj = bpy.context.object
            line_art_obj.name = "Line Art Heavy"
            
            # SET LINE ART PARAMS
            line_art_obj.grease_pencil_modifiers["Line Art"].use_material = False
            line_art_obj.grease_pencil_modifiers["Line Art"].use_edge_mark = False
            line_art_obj.grease_pencil_modifiers["Line Art"].use_intersection = False
            line_art_obj.grease_pencil_modifiers["Line Art"].use_crease = False

            line_art_obj.grease_pencil_modifiers["Line Art"].thickness = altP.p_heavy_line
            
            line_art_obj.data.layers["Lines"].use_lights = False
            line_art_obj.data.stroke_thickness_space = altP2.p_stroke_thickness_space
            
            line_art_obj.show_in_front = True
            bpy.context.object.data.layers["Lines"].tint_factor = 1
            
            # FORECOLOR
            bpy.data.objects["Line Art Thin"].data.layers["Lines"].tint_color = altP2.p_forecolor
            bpy.data.objects["Line Art Heavy"].data.layers["Lines"].tint_color = altP2.p_forecolor
            # BACKCOLOR            
            bpy.context.space_data.shading.background_color = altP2.p_backcolor
            bpy.context.space_data.shading.single_color = altP2.p_backcolor           

            
            # SET UP VIEWPORT
            altP.p_shading_type = bpy.context.space_data.shading.type
            bpy.context.space_data.shading.type = 'SOLID'
            
            altP.p_shading_light = bpy.context.space_data.shading.light
            bpy.context.space_data.shading.light = 'FLAT'
            
            altP.p_show_shadow = bpy.context.space_data.shading.show_shadows
            bpy.context.space_data.shading.show_shadows = True
            
            altP.p_shadow_intensity = bpy.context.space_data.shading.shadow_intensity
            bpy.context.space_data.shading.shadow_intensity = altP.p_line_art_shadow_intensity
            
            altP.p_shading_bg_type = bpy.context.space_data.shading.background_type
            bpy.context.space_data.shading.background_type = 'VIEWPORT'
                        
            altP.p_shading_color_type = bpy.context.space_data.shading.color_type
            bpy.context.space_data.shading.color_type = 'SINGLE'
                       
            altP.p_shadow_focus = bpy.context.scene.display.shadow_focus
            bpy.context.scene.display.shadow_focus = 1.0
            
            altP.p_show_cavity = bpy.context.space_data.shading.show_cavity
            bpy.context.space_data.shading.show_cavity = False
            
            altP.p_show_object_outline_orig = bpy.context.space_data.shading.show_object_outline
            bpy.context.space_data.shading.show_object_outline = altP.p_show_object_outline_la 
            
            altP.p_show_xray = bpy.context.space_data.shading.show_xray
            bpy.context.space_data.shading.show_xray = False            
            
            
            # COLOR MGMT
            bpy.context.scene.display_settings.display_device = 'None'
            bpy.context.scene.view_settings.look = 'None'
            
            # RESTORE OVERLAYS SETTINGS
            bpy.context.space_data.overlay.show_overlays = altP.p_show_overlays
            
            #TURN ON LINE ART COLLECTION
            altP2.p_show_lineart_collection = True            

            # DESELECT ALL
            line_art_obj.select_set(False)

        return {'FINISHED'}


#class Alt_Toggle_LineArt_Collection(bpy.types.Operator):
#    """Toggles Line Art Collection for a FAST mode"""
#    bl_idname = "chippops.alt_toggle_lineart_collection"
#    bl_label = "Toggle Line Art Collection"

#    def execute(self, context):  
#        altP = bpy.context.scene.my_tool
#        if altP.p_show_lineart_collection == True:
#            #bpy.context.layer_collection["Line Art"].exclude = True
#            bpy.data.collections['Line Art'].hide_viewport = False
#            bpy.data.collections['Line Art'].hide_render = False
#            altP.p_show_lineart_collection = False
#            print("toggling line art collection:False")
#        else:            
#            bpy.data.collections['Line Art'].hide_viewport = True
#            bpy.data.collections['Line Art'].hide_render = True
#            altP.p_show_lineart_collection = True
#            print("toggling line art collection:True")
#        return {'FINISHED'}  

class Alt_Render_Viewport(bpy.types.Operator):
    """Renders a single frame.\n  Shift - turns ON Line Art before rendering"""
    bl_idname = "chippops.alt_render_viewport"
    bl_label = "Render Image"

    def invoke(self, context, event): 
        
        if event.shift:
            bpy.data.collections['Line Art'].hide_viewport = False
            bpy.data.collections['Line Art'].hide_render = False
            altP2 = bpy.context.scene.my_tool2
            altP2.p_show_lineart_collection = True
         
        altRender("image")
        return {'FINISHED'}  

class Alt_Render_Animation(bpy.types.Operator):
    """Renders full animation.\n  Shift - turns ON Line Art before rendering"""
    bl_idname = "chippops.alt_render_animation"
    bl_label = "Render Animation"

    def invoke(self, context, event): 
        
        if event.shift:
            bpy.data.collections['Line Art'].hide_viewport = False
            bpy.data.collections['Line Art'].hide_render = False
            altP2 = bpy.context.scene.my_tool2
            altP2.p_show_lineart_collection = True
         
        altRender("animation")
        return {'FINISHED'}  
    
class Alt_Toggle_Extras(bpy.types.Operator):
    """Toggles Extras: Use before rendering"""
    bl_idname = "chippops.alt_toggle_extras"
    bl_label = "Toggle Extras for Rendering"

    def execute(self, context):  
        altP = bpy.context.scene.my_tool
        if altP.p_extras_on:
            altHideExtras()
        else:
            altShowExtras()        
        return {'FINISHED'}  

def stroke_changed(self, context):
    # MAPS CUSTOM ENUM PULLDOWN MENU TO BOTH LINE ART OBJECTS
    # !!! NEEDS TO BE ABOVE AltCustomInterface WHERE THIS ENUM IS DEFINED !!!
    altP2 = bpy.context.scene.my_tool2
    bpy.data.objects["Line Art Heavy"].data.stroke_thickness_space = altP2.p_stroke_thickness_space 
    bpy.data.objects["Line Art Thin"].data.stroke_thickness_space = altP2.p_stroke_thickness_space 

def lineart_collection_display_changed(self, context):
    # TOGGLE ON/OFF Line Art Collection
    altP2 = bpy.context.scene.my_tool2 
    #print(altP2.p_show_lineart_collection)
    if altP2.p_show_lineart_collection == True:
        #bpy.context.layer_collection["Line Art"].exclude = True
        bpy.data.collections['Line Art'].hide_viewport = False
        bpy.data.collections['Line Art'].hide_render = False
        #altP2.p_show_lineart_collection = False
    else:            
        bpy.data.collections['Line Art'].hide_viewport = True
        bpy.data.collections['Line Art'].hide_render = True
        #altP2.p_show_lineart_collection = True
        #print("toggling line art collection:False")  

def wires_bounds_display_changed(self, context):
    # TOGGLE ON/OFF VISIBILITY OF OBJECTS WITH VIEWPORT DISPLAY SET TO WIRE OR BOUNDS
    altP2 = bpy.context.scene.my_tool2 
    
    obj = context.object
    scene = context.scene
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            if obj.display_type == 'BOUNDS' or obj.display_type == 'WIRE':
                obj.hide_viewport = not altP2.p_show_wires_boxes


class AltCustomInterface(bpy.types.PropertyGroup):
    # COLOR SETTINGS
    p_backcolor : bpy.props.FloatVectorProperty(min=0.0,max=1.0,subtype='COLOR')
    p_forecolor : bpy.props.FloatVectorProperty(min=0.0,max=1.0,subtype='COLOR')
    
    # ENUM FOR STROKE MODE
    p_stroke_thickness_space : bpy.props.EnumProperty(
        name= "",
        items=[('SCREENSPACE', 'Screen Space', "Larger strokes"),('WORLDSPACE', 'World Space', "Smaller strokes")],
        update= stroke_changed,
        default="SCREENSPACE"
        )
    
    p_show_lineart_collection : bpy.props.BoolProperty(
        default=True,
        name= "Toggle Line Art Display",
        update= lineart_collection_display_changed,
        description= "Toggles ON/OFF the Line Art Collection"
        )

    p_show_wires_boxes : bpy.props.BoolProperty(
        default=True,
        name= "Show wires and bounding boxes",
        update= wires_bounds_display_changed,
        description= "Toggles ON/OFF the objects with viewport display of type wire or bounds"
        )
    
class AltSetColors(bpy.types.Operator):
    """Sets foreground and background colors"""
    bl_idname = "chippops.alt_setcolors"
    bl_label = "Set Foreground and Back Colors"
    
    #p_backcolor: bpy.props.FloatVectorProperty(subtype='COLOR')

    def execute(self, context):
        altP2 = bpy.context.scene.my_tool2
        bpy.context.space_data.shading.background_color = altP2.p_backcolor
        bpy.context.space_data.shading.single_color = altP2.p_backcolor        
        bpy.data.objects["Line Art Thin"].data.layers["Lines"].tint_color = altP2.p_forecolor
        bpy.data.objects["Line Art Heavy"].data.layers["Lines"].tint_color = altP2.p_forecolor
        
        return {'FINISHED'}
    
class AltSelectWiresBounds(bpy.types.Operator):
    """Selects objects with Wire and Bounding viewport display """
    bl_idname = "chippops.alt_select_wires_bounds"
    bl_label = "Select Wires and Bounding Boxes"
    
    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                if obj.display_type == 'BOUNDS' or obj.display_type == 'WIRE':
                    try:
                        obj.select_set(True) 
                    except:
                        pass
        return {'FINISHED'}

class AltSettings(bpy.types.PropertyGroup):
    # use an annotation
    p_first_use : bpy.props.BoolProperty(default=True)
    p_extras_on : bpy.props.BoolProperty(default=True)

    # BOOLEAN
    p_show_floor : bpy.props.BoolProperty(default=True)
    p_show_ortho_grid : bpy.props.BoolProperty(default=True)
    p_show_axis_x : bpy.props.BoolProperty(default=True)
    p_show_axis_y : bpy.props.BoolProperty(default=True)
    p_show_axis_z : bpy.props.BoolProperty(default=True)
    p_show_cursor : bpy.props.BoolProperty(default=True)
    p_show_extras : bpy.props.BoolProperty(default=True)
    p_show_relationship_lines : bpy.props.BoolProperty(default=True)
    p_show_outline_selected : bpy.props.BoolProperty(default=True)
    p_show_bones : bpy.props.BoolProperty(default=True)
    p_show_motion_paths : bpy.props.BoolProperty(default=True)
    p_show_object_origins : bpy.props.BoolProperty(default=True)
    p_show_object_origins_all : bpy.props.BoolProperty(default=True)
    p_show_shadow : bpy.props.BoolProperty(default=True)
    p_show_cavity : bpy.props.BoolProperty(default=True)
    p_show_overlays : bpy.props.BoolProperty(default=True)
#    p_show_lineart_collection : bpy.props.BoolProperty(default=True)
    p_show_object_outline_la : bpy.props.BoolProperty(default=False)
    p_show_object_outline_orig : bpy.props.BoolProperty(default=False)
    p_show_xray : bpy.props.BoolProperty(default=False)
#    p_boolean : bpy.props.BoolProperty(default=True)

    # FLOAT
    p_thin_crease_threshold :  bpy.props.FloatProperty()
    p_line_art_shadow_intensity :  bpy.props.FloatProperty()
    p_shadow_intensity :  bpy.props.FloatProperty()
    p_line_art_shadow_intensity :  bpy.props.FloatProperty()
    p_shadow_focus :  bpy.props.FloatProperty()
#    p_float :  bpy.props.FloatProperty()
    
    # INT
    p_thin_line : bpy.props.IntProperty()
    p_heavy_line : bpy.props.IntProperty()
#    p_int : bpy.props.IntProperty()
    
    # STRING
    p_display_device : bpy.props.StringProperty()
    p_look : bpy.props.StringProperty()
    p_view_transform : bpy.props.StringProperty()
    p_shading_type : bpy.props.StringProperty()
    p_shading_light : bpy.props.StringProperty()
    p_shading_bg_type : bpy.props.StringProperty()
    p_shading_color_type : bpy.props.StringProperty()
#   p_string : bpy.props.StringProperty()
#   p_string : bpy.props.StringProperty()

    # FLOAT VECTOR
    p_shading_bg_color : bpy.props.FloatVectorProperty()
#    p_FloatVectorProperty : bpy.props.FloatVectorProperty()
    
#    p_enum : bpy.props.EnumProperty()

    # INT VECTOR
#    p_IntVectorProperty : bpy.props.IntVectorProperty()
    

def altCheckMode(): 
    if bpy.data.collections.get('Line Art'):
        return True
    else:
        return False

def altRender(p_mode):
        
    if p_mode == "image":    
        bpy.ops.render.opengl('INVOKE_DEFAULT')
    else:
        bpy.ops.render.opengl('INVOKE_DEFAULT', animation=True,)
        
def altStoreOrigScene():
    altP = bpy.context.scene.my_tool
    
    altP.p_display_device = bpy.context.scene.display_settings.display_device 
    altP.p_look = bpy.context.scene.view_settings.look
    altP.p_view_transform = bpy.context.scene.view_settings.view_transform


def altShowOrigScene():
    # CALLED FROM TOGGLE LINE ART BUTTON
    altP = bpy.context.scene.my_tool
    bpy.context.scene.display_settings.display_device = altP.p_display_device
    bpy.context.scene.view_settings.look = altP.p_look
    bpy.context.scene.view_settings.view_transform = altP.p_view_transform

def altStoreLineArtScene():
    altP = bpy.context.scene.my_tool
        

def altStoreExtras():
    # STORES SETTINGS FROM NON-LINE ART VIEW
    
    altP = bpy.context.scene.my_tool
    
    altP.p_show_floor = bpy.context.space_data.overlay.show_floor
    altP.p_show_ortho_grid = bpy.context.space_data.overlay.show_ortho_grid
    altP.p_show_axis_x = bpy.context.space_data.overlay.show_axis_x
    altP.p_show_axis_y = bpy.context.space_data.overlay.show_axis_y
    altP.p_show_axis_z = bpy.context.space_data.overlay.show_axis_z        
    altP.p_show_cursor = bpy.context.space_data.overlay.show_cursor
    altP.p_show_extras = bpy.context.space_data.overlay.show_extras
    altP.p_show_relationship_lines = bpy.context.space_data.overlay.show_relationship_lines
    altP.p_show_outline_selected = bpy.context.space_data.overlay.show_outline_selected
    altP.p_show_bones = bpy.context.space_data.overlay.show_bones
    altP.p_show_motion_paths = bpy.context.space_data.overlay.show_motion_paths
    altP.p_show_object_origins = bpy.context.space_data.overlay.show_object_origins
    altP.p_show_object_origins_all = bpy.context.space_data.overlay.show_object_origins_all
    
def altHideExtras():
    # HIDE EXTRAS IN LINE ART VIEW
    altP = bpy.context.scene.my_tool
    
    altP.p_extras_on = False
    
    bpy.context.space_data.overlay.show_floor = False
    bpy.context.space_data.overlay.show_ortho_grid = False
    bpy.context.space_data.overlay.show_axis_x = False
    bpy.context.space_data.overlay.show_axis_y = False
    bpy.context.space_data.overlay.show_axis_z = False
    bpy.context.space_data.overlay.show_cursor = False
    bpy.context.space_data.overlay.show_extras = False
    bpy.context.space_data.overlay.show_relationship_lines = False
    bpy.context.space_data.overlay.show_outline_selected = False
    bpy.context.space_data.overlay.show_bones = False
    bpy.context.space_data.overlay.show_motion_paths = False
    bpy.context.space_data.overlay.show_object_origins = False    
    bpy.context.space_data.overlay.show_object_origins_all = False

def altShowExtras():
    # SHOWS EXTRAS FROM STORED PROPS
    altP = bpy.context.scene.my_tool
    
    altP.p_extras_on = True
    
    bpy.context.space_data.overlay.show_floor = altP.p_show_floor
    bpy.context.space_data.overlay.show_ortho_grid = altP.p_show_ortho_grid
    bpy.context.space_data.overlay.show_axis_x = altP.p_show_axis_x
    bpy.context.space_data.overlay.show_axis_y = altP.p_show_axis_y
    bpy.context.space_data.overlay.show_axis_z = altP.p_show_axis_z
    bpy.context.space_data.overlay.show_cursor = altP.p_show_cursor
    bpy.context.space_data.overlay.show_extras = altP.p_show_extras
    bpy.context.space_data.overlay.show_relationship_lines = altP.p_show_relationship_lines
    bpy.context.space_data.overlay.show_outline_selected = altP.p_show_outline_selected
    bpy.context.space_data.overlay.show_bones = altP.p_show_bones
    bpy.context.space_data.overlay.show_motion_paths = altP.p_show_motion_paths
    bpy.context.space_data.overlay.show_object_origins = altP.p_show_object_origins
    bpy.context.space_data.overlay.show_object_origins_all = altP.p_show_object_origins_all
    

def altInitProps():
   # global g_run_first_time, g_extras_on  
    
    #INITIALIZE GLOBALS AND SCENE PROPS
    altP = bpy.context.scene.my_tool
 
    if altP.p_first_use:
        altStoreOrigScene()
               
        altP.p_thin_line = 2
        altP.p_heavy_line = 4
        altP.p_thin_crease_threshold = 2.44346
        altP.p_line_art_shadow_intensity = 0.5
        altP.p_extras_on = True  
        altP.p_show_overlays = bpy.context.space_data.overlay.show_overlays
        
        altP2 = bpy.context.scene.my_tool2 
        altP2.p_backcolor = (1,1,1)
        altP2.p_forecolor = (0,0,0)
        altP.p_show_object_outline_la = False 
        altP.p_show_object_outline_orig = bpy.context.space_data.shading.show_object_outline 

    
        ############### CHANGE TO False FOR FINAL! #############    
        altP.p_first_use = False
        

classes = [SS_OpenHelpURL,Alt_Line_Art,
            Alt_Render_Viewport, 
            Alt_Render_Animation, 
            AltSettings, 
            AltSelectWiresBounds,
            AltSetColors,
            AltCustomInterface, 
            AltLineArtPanel, 
            Alt_Toggle_Extras,
            ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # THESE ARE ALL THE SCENE PROPS THAT ARE SAVED WITH THE FILE
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=AltSettings)
    # THESE ARE ALL SCENE PROPS THAT ARE IN THE PANEL UI
    bpy.types.Scene.my_tool2 = bpy.props.PointerProperty(type=AltCustomInterface)



def unregister():
    for cls in reversed(classes):
        #for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.my_tool
    del bpy.types.Scene.my_tool2
    

if __name__ == "__main__":
    register()

