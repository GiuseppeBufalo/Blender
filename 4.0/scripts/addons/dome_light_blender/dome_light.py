# ///////////////////////////////////////////////////////////////
#
# Blender Dome Light
# by: WANDERSON M. PIMENTA
# version: 2.0.0
#
# This Addon is inspired by EasyHDRI after it has been without
# updates for a long time I created new versions derived from
# it and within the GPL terms.
# Credits from the EasyHDRI creator:
# http://codeofart.com/easy-hdri-2-8/
#
# ///////////////////////////////////////////////////////////////

import bpy, os
import bpy.utils.previews
from bpy.props import *
from bpy.types import Panel, Operator, Menu, Panel
from bpy_extras.io_utils import ImportHelper

version = '2.0.2 Beta'

#CREATE NODES
def create_world_nodes():
    
    scn = bpy.context.scene
    worlds = bpy.data.worlds
    enable_mix_hdr = bpy.context.scene.enable_mix_hdr
    
    # Make sure the render engine is Cycles or Eevee
    if not scn.render.engine in ['CYCLES', 'BLENDER_EEVEE']:
        scn.render.engine = 'BLENDER_EEVEE'
    # Add a new world "EasyHDR", or reset the existing one
    if not 'World' in worlds:
        world = bpy.data.worlds.new("World")        
    else:
        world = worlds['World']
    scn.world = world       
    # Enable Use nodes
    world.use_nodes= True    

    # Create Nodes
    create_nodes(world, enable_mix_hdr)
    
def create_nodes(nodes_tree, enable_mix_hdr):
    # Delete all the nodes
    nodes_tree.node_tree.nodes.clear()

    # Adding new nodes
    tex_coord = nodes_tree.node_tree.nodes.new(type="ShaderNodeTexCoord")   
    mapping = nodes_tree.node_tree.nodes.new(type="ShaderNodeMapping") 
    env = nodes_tree.node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    env.show_texture = True
    env_2 = nodes_tree.node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    mix_rgb = nodes_tree.node_tree.nodes.new(type="ShaderNodeMixRGB")
    background = nodes_tree.node_tree.nodes.new(type="ShaderNodeBackground")
    gamma = nodes_tree.node_tree.nodes.new(type="ShaderNodeGamma")
    saturation = nodes_tree.node_tree.nodes.new(type="ShaderNodeHueSaturation")
    color = nodes_tree.node_tree.nodes.new(type="ShaderNodeMixRGB")
    math_multiply = nodes_tree.node_tree.nodes.new(type="ShaderNodeMath")
    math_divide = nodes_tree.node_tree.nodes.new(type="ShaderNodeMath")
    math_add = nodes_tree.node_tree.nodes.new(type="ShaderNodeMath")
    output = nodes_tree.node_tree.nodes.new(type="ShaderNodeOutputWorld")
       
    # Change the parameters
    tex_coord.name = 'Texture_Coordinate'
    mapping.name = 'Mapping'
    env.name = 'Environment'
    env_2.name = 'Environment_2'
    background.name = 'Background'
    mapping.name = 'Mapping'
    mix_rgb.name = 'Mix_BG_RGB'
    mix_rgb.inputs[0].default_value = 0.5
    if enable_mix_hdr:
        mix_rgb.mute = False
    else:
        mix_rgb.mute = True
    saturation.name = 'Saturation'
    color.name = 'Color'
    math_multiply.name = 'Math_multiply'
    math_multiply.operation = 'MULTIPLY'
    math_multiply.inputs[1].default_value = 0.0
    math_divide.name = 'Math_divide'
    math_divide.operation = 'DIVIDE'
    math_divide.inputs[1].default_value = 100.0
    math_add.name = 'Math_add'   
    math_add.operation = 'ADD'   
    math_add.inputs[1].default_value = 1.0
    color.blend_type = 'MULTIPLY'  
    color.inputs[0].default_value = 0.0
    
    # Link nodes
    nodes_tree.node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs[0])
    nodes_tree.node_tree.links.new(mapping.outputs[0], env.inputs[0])
    nodes_tree.node_tree.links.new(mapping.outputs[0], env_2.inputs[0])
    nodes_tree.node_tree.links.new(env.outputs[0], mix_rgb.inputs[1])
    nodes_tree.node_tree.links.new(env_2.outputs[0], mix_rgb.inputs[2])
    nodes_tree.node_tree.links.new(mix_rgb.outputs['Color'], gamma.inputs[0])
    nodes_tree.node_tree.links.new(mix_rgb.outputs['Color'], math_multiply.inputs[0])
    nodes_tree.node_tree.links.new(gamma.outputs[0], saturation.inputs[4])
    nodes_tree.node_tree.links.new(saturation.outputs[0], color.inputs[1])
    nodes_tree.node_tree.links.new(math_multiply.outputs[0], math_divide.inputs[0])
    nodes_tree.node_tree.links.new(math_divide.outputs[0], math_add.inputs[0])
    nodes_tree.node_tree.links.new(math_add.outputs[0], background.inputs[1])
    nodes_tree.node_tree.links.new(color.outputs[0], background.inputs[0])
    nodes_tree.node_tree.links.new(background.outputs[0], output.inputs[0])    
    
    # Nodes location    
    tex_coord.location = (-80, 200)
    mapping.location = (90, 200)
    env.location = (300, 450)
    env_2.location = (300, 0)
    mix_rgb.location = (650, 200)
    gamma.location = (960, 350)
    saturation.location = (1120, 350)
    color.location = (1290, 350)
    math_multiply.location = (960, 100)
    math_divide.location = (1120, 100)
    math_add.location = (1290, 100)
    background.location = (1500, 252)
    output.location = (1660, 252)
    
# Remove Unused Images Method
def remove_images():
    images = bpy.data.images
    for img in bpy.data.images:
        if not img.users or (img.users == 1 and img.use_fake_user):
            bpy.data.images.remove(img)

# Check the World's node tree
def Verify_World_Nodes():
    nodes_list = ['Texture_Coordinate', 'Mapping', 'Environment', 'Environment_2',
                  'Gamma', 'Saturation', 'Math_multiply', 'Math_divide',
                  'World Output', 'Math_add', 'Color', 'Mix_BG_RGB',
                  'Background', ]
    all_found = True              
    scn = bpy.context.scene
    worlds = bpy.data.worlds
    if not scn.world:
        return 'Fix'        
    if not 'World' in worlds:
        return 'Create'
    else:
        world = worlds['World']
        nodes = world.node_tree.nodes
        if len(nodes) > 0:
            for n in nodes_list:
                if not n in nodes:
                    all_found = False
            if not all_found:
                return 'Fix'
        else:
            return 'Fix'
    if not scn.world.name == 'World':
        return 'Fix'

#CLASS CREATE DOME LIGHT            
class BUTTON_PT_Create_Dome_Light(Operator):
    bl_idname = "view3d.domelight"
    bl_label = "FIX DOME LIGHT"
    bl_description = "Create Dome Light"
    
    def execute(self, context):
        create_world_nodes()
        bpy.context.space_data.shading.use_scene_lights_render = True
        bpy.context.space_data.shading.use_scene_world_render = True
        bpy.context.space_data.shading.use_scene_lights = True
        bpy.context.space_data.shading.use_scene_world = True
        bpy.context.space_data.shading.type = 'MATERIAL'
        
        self.report({'INFO'}, 'Dome Light created successfully! Now choose an HDR.')
        return {'FINISHED'}

# Remove Unused Images
class WORLD_OT_Remove_Unused_Images(Operator):
    bl_idname = "world.remove_images"
    bl_label = "Remove unused images"
    bl_description = "Remove unused user images"
    
    def execute(self, context):
        remove_images()
        
        self.report({'INFO'}, 'All unused images have been removed!')
        return {'FINISHED'}

# Open HDR 1
class OBJECT_OT_Open_HDR_1(Operator, ImportHelper):
    bl_idname = "view3d.open_hdr_1"
    bl_label = "Select HDR file"
    bl_description = "Open HDR File"
    
    filename_ext = ".hdr;.exr;.png;.jpg"
    filter_glob : StringProperty(default="*.hdr;*.exr;*.png;*.jpg;*.jpeg", options={'HIDDEN'})
    filepath : StringProperty(subtype='FILE_PATH')
    files : CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement
    )
    def execute(self, context):
        """Load file."""        
        # Change image
        try:
            bpy.data.images.load(filepath=self.filepath, check_existing=True)
            limit = 2
            index = 1
            for file in self.files:
                bpy.data.worlds["World"].node_tree.nodes["Environment"].image = bpy.data.images[file.name]
                
                index += 1
                if index == limit:
                    break
            
            self.report({'INFO'}, 'HDR Successfully Selected!')
        except:
            self.report({'WARNING'}, 'Dome Light could not find the selected image!')
            
        return {'FINISHED'}

# Open HDR 2
class OBJECT_OT_Open_HDR_2(Operator, ImportHelper):
    bl_idname = "view3d.open_hdr_2"
    bl_label = "Open Second HDR File"
    bl_description = "Open HDR File"
    
    filename_ext = ".hdr;.exr;.png;.jpg"
    filter_glob : StringProperty(default="*.hdr;*.exr;*.png;*.jpg;*.jpeg", options={'HIDDEN'})
    filepath : StringProperty(subtype='FILE_PATH')
    files : CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement
    )
    def execute(self, context):
        """Load file."""        
        # Change image
        try:
            bpy.data.images.load(filepath=self.filepath, check_existing=True)
            limit = 1
            index = 1
            for file in self.files:
                bpy.data.worlds["World"].node_tree.nodes["Environment_2"].image = bpy.data.images[file.name]
                
                index += 1
                if index == limit:
                    break
                
            self.report({'INFO'}, 'HDR Successfully Selected!')
        except:
            self.report({'WARNING'}, 'Dome Light could not find the selected image!')
            
        return {'FINISHED'}

#PAINEL INFO
class PAINEL_UI_Dome_Light(Panel) :
    bl_idname = "BUTTON_PT_Create_Dome_Light"
    bl_label = "Dome Light"
    bl_category = "Dome Light"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        # View Shading
        layout = self.layout
        world = bpy.context.space_data.shading
        view = context.space_data 
        
        # Navegation
        scn = context.scene
        cscene = scn.cycles
        engine = scn.render.engine
        view_settings = scn.view_settings
        
        # Layout
        col = layout.column()
        box = col.box()
        col = box.column()
        col.label(text = 'Move Camera:', icon = 'OUTLINER_OB_CAMERA')
        col.prop(view, "lock_camera", text="Camera to View")      
        
        # Scene Nodes
        scn = context.scene
        col = layout.column()
        box = col.box()
        col = box.column()
        
        # Node Properties
        nodes = scn.world.node_tree.nodes
        enable_mix_hdr = bpy.context.scene.enable_mix_hdr
        
        # Shading Props
        if world.type == 'RENDERED':
            col.label(text = 'Rendered:', icon = 'SHADING_RENDERED')
            if world.use_scene_lights_render:
                col.prop(world, "use_scene_lights_render", text='Show Scene Lights', icon='OUTLINER_OB_LIGHT')
            else:
                col.prop(world, "use_scene_lights_render", text='Show Scene Lights', icon='LIGHT_DATA')
            if world.use_scene_world_render:
                col.prop(world, "use_scene_world_render", text='Show HDR Light', icon='OUTLINER_OB_LIGHT')
            else:
                col.prop(world, "use_scene_world_render", text='Show HDR Light', icon='LIGHT_DATA')
            col.prop(scn.render, "film_transparent", text="Transparent BG")
        elif world.type == 'MATERIAL':
            col.label(text = 'Material Preview:', icon = 'SHADING_TEXTURE')
            if world.use_scene_lights:
                col.prop(world, "use_scene_lights", text='Show Scene Lights', icon='OUTLINER_OB_LIGHT')
            else:
                col.prop(world, "use_scene_lights", text='Show Scene Lights', icon='LIGHT_DATA')
            if world.use_scene_world:
                col.prop(world, "use_scene_world", text='Show HDR Light', icon='OUTLINER_OB_LIGHT')
            else:
                col.prop(world, "use_scene_world", text='Show HDR Light', icon='LIGHT_DATA')
            col.prop(scn.render, "film_transparent", text="Transparent BG")

        col = box.column()
        col.label(text = 'Render Engine:', icon = 'RESTRICT_RENDER_OFF')
        col.prop(scn.render, "engine", text='', expand=False)

           
        if Verify_World_Nodes() == 'Create':
            col = layout.column()
            box = col.box()
            col = box.column()
            col.label(text = 'Fix Dome Light:', icon = 'OUTLINER_OB_LIGHT')
            col.operator("view3d.domelight", text = 'FIX DOME LIGHT', icon='WORLD_DATA')
        elif Verify_World_Nodes() == 'Fix':
            col = layout.column()
            box = col.box()
            col = box.column()
            col.label(text = 'Create Dome Light:', icon = 'OUTLINER_OB_LIGHT')
            col.operator("view3d.domelight", text = 'CREATE DOME LIGHT', icon='WORLD_DATA')
        else:
            col = layout.column()
            # HDR 1          
            box = col.box()
            col = box.column(align=False)
            col.label(text = 'Open HDR:', icon = 'WORLD_DATA')
            col.operator('view3d.open_hdr_1', text = "Open HDR")
            col.prop(nodes['Environment'], "image", text = '', icon='NONE')          
            col.prop(nodes['Environment'], "projection", text = '')
            
            # HDR 2
            col = box.column(align=True)
            box = col.box()
            col = box.column(align=False)
            if not context.scene.enable_mix_hdr:
                col.prop(context.scene, 'enable_mix_hdr', text='Enable Mix HDR', icon = 'UV_SYNC_SELECT')
            else:
                col.prop(context.scene, 'enable_mix_hdr', text='Disable Mix HDR', icon = 'RENDERLAYERS')
            if enable_mix_hdr:                
                col = box.column(align=False)
                col.operator('view3d.open_hdr_2', text = "Open Second HDR")
                col.prop(nodes['Environment_2'], "image", text = '', icon='NONE')          
                col.prop(nodes['Environment_2'], "projection", text = '')
                
                # Try Show Node Rotation
                try:
                    env_node_1 = nodes['Environment_2']
                    mapping = env_node_1.texture_mapping
                    col.prop(mapping, "rotation", text = 'Offset Rotation')
                    
                    col = box.column(align=False)
                    col.label(text = 'Mix HDR:', icon = 'PLUS')
                    col = box.column(align=True)
                    col.prop(nodes['Mix_BG_RGB'], "blend_type", text = '', icon='NONE')
                    col.prop(nodes['Mix_BG_RGB'].inputs[0], "default_value", text = 'Mix', icon='NONE')
                except:
                    pass
            
            col = layout.column()
            box = col.box()
            col = box.column(align=True) 
            col.label(text = 'Dome Light Settings:', icon = 'WORLD_DATA')    
            if 'Math_add' in nodes:
                col.prop(nodes['Math_add'].inputs[1], "default_value", text = 'Intensity')
            if 'Math_multiply' in nodes:
                col.prop(nodes['Math_multiply'].inputs[1], "default_value", text = 'Sun Intensity')
            if 'Gamma' in nodes:
                col.prop(nodes['Gamma'].inputs[1], "default_value", text = "Gamma")
            if 'Saturation' in nodes:
                col.prop(nodes['Saturation'].inputs[1], "default_value", text = "Saturation")
            if 'Color' in nodes:
                col.prop(nodes['Color'].inputs[2], "default_value", text = "Tint")        
                col.prop(nodes['Color'].inputs[0], "default_value", text = "Intensity")
                
            col = layout.column()
            box = col.box()
            col = box.column(align=True)
            col.label(text = "Exposure", icon = 'SCENE')
            if engine == 'CYCLES':
                col.prop(cscene, "film_exposure", text = "Cycles Exposure")
            col.prop(view_settings, "exposure", text = "Color Exposure")
          
            col = layout.column()
            box = col.box()
            col = box.column(align=True) 
            col.prop(nodes["Mapping"].inputs[2], "default_value", text = "Rotation", icon = 'FILE_REFRESH')
            col.label(text = "Default rotation shortcut:", icon = 'FILE_REFRESH')
            col.label(text = "crtl + shift + alt + right mouse")
        
            col = layout.column()
            box = col.box()
            box.operator("world.remove_images", text = 'Remove Unused Images', icon = 'TRASH')
        
        col = layout.column()
        col.label(text = f'Version: {version}', icon = 'INFO')
        
class WORLD_OT_RotateMapping(Operator):
    bl_idname = "world.rotate_hdri_mapping"
    bl_label = "Rotate HDRI Mapping"

    ctrl_shift_pressed: bpy.props.BoolProperty(default=False)
    middlemouse_dragging: bpy.props.BoolProperty(default=False)
    prev_x: bpy.props.FloatProperty(default=0)
    delta_x: bpy.props.FloatProperty(default=0)

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            delta_x = event.mouse_x - self.prev_x
            mapping_node = bpy.context.scene.world.node_tree.nodes.get("Mapping")
            if mapping_node:
                mapping_node.inputs[2].default_value[2] += delta_x * 0.01
            self.prev_x = event.mouse_x

        elif event.value == 'RELEASE':
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.ctrl_shift_pressed = False
        self.middlemouse_dragging = False
        self.prev_x = event.mouse_x
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
addon_keymaps = []

# Update MIX HDR When Change Status        
def update_hdr_2(self, context):
    mix_node = bpy.data.worlds["World"].node_tree.nodes["Mix_BG_RGB"]
    enable_mix_hdr = bpy.context.scene.enable_mix_hdr
    
    if enable_mix_hdr:
        mix_node.mute = False
    else:
        mix_node.mute = True

def register():
    bpy.utils.register_class(BUTTON_PT_Create_Dome_Light)
    bpy.utils.register_class(PAINEL_UI_Dome_Light)
    bpy.utils.register_class(OBJECT_OT_Open_HDR_1)
    bpy.utils.register_class(OBJECT_OT_Open_HDR_2)
    bpy.utils.register_class(WORLD_OT_Remove_Unused_Images)
    bpy.utils.register_class(WORLD_OT_RotateMapping)
    
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new('world.rotate_hdri_mapping', 'RIGHTMOUSE', 'PRESS', ctrl=True, shift=True, alt=True)
    addon_keymaps.append((km, kmi))
    
    bpy.types.Scene.enable_mix_hdr = bpy.props.BoolProperty(
        name = 'Enable Mix HDR',
        default = False,
        options={'HIDDEN'},
        update = update_hdr_2
    )


def unregister():
    bpy.utils.unregister_class(BUTTON_PT_Create_Dome_Light)
    bpy.utils.unregister_class(PAINEL_UI_Dome_Light)
    bpy.utils.unregister_class(OBJECT_OT_Open_HDR_1)
    bpy.utils.unregister_class(OBJECT_OT_Open_HDR_2)
    bpy.utils.unregister_class(WORLD_OT_Remove_Unused_Images)
    bpy.utils.unregister_class(WORLD_OT_RotateMapping)
    
    wm = bpy.context.window_manager
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    del bpy.types.Scene.enable_mix_hdr


if __name__ == "__main__":
    register()