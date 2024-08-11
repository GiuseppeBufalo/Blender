import bpy, os
from .ui.library import enum_previews_from_directory_items, hdri_lib_path_update
from .properties.node import get_em_strength
from .constants import photographer_folder

wb_name = 'White Balance'
blur_name = 'Blur'

def get_background(context):
    background = []
    world = context.scene.world
    if world:
        if world.use_nodes:
            nodes = world.node_tree.nodes
            links = world.node_tree.links
            for node in nodes:
                if type(node) is bpy.types.ShaderNodeBackground:
                    if not node.mute:
                        if node.outputs[0].links:
                            background.append(node)
    return background

def get_environment_tex(context):
    environment_tex = []
    world = context.scene.world
    if world:
        if world.use_nodes:
            nodes = world.node_tree.nodes
            for node in nodes:
                if type(node) is bpy.types.ShaderNodeTexEnvironment:
                    environment_tex.append(node)
    return environment_tex

def get_sky_tex(context):
    sky_tex = []
    world = context.scene.world
    if world:
        if world.use_nodes:
            nodes = world.node_tree.nodes
            for node in nodes:
                if type(node) is bpy.types.ShaderNodeTexSky:
                    sky_tex.append(node)
    return sky_tex

def get_wb_groups(context):
    wb = []
    world = context.scene.world
    if world:
        if world.use_nodes:
            nodes = world.node_tree.nodes
            wb=[n for n in nodes if n.bl_idname=='ShaderNodeGroup' and n.node_tree.name==wb_name]
    return wb

def get_blur_groups(context):
    blur = []
    world = context.scene.world
    if world:
        if world.use_nodes:
            nodes = world.node_tree.nodes
            blur=[n for n in nodes if n.bl_idname=='ShaderNodeGroup' and n.node_tree.name==blur_name]
    return blur


def get_hdri_rotation(self):
    return self.get('hdri_rotation',  0)

def set_hdri_rotation(self,value):
    self['hdri_rotation'] = value
    world = bpy.context.scene.world
    if world and world.get('is_world_hdri',False):
        if world.use_nodes:
            nodes = world.node_tree.nodes
            links = world.node_tree.links
            for node in nodes:
                if node.bl_idname == 'ShaderNodeMapping':
                    node.inputs[2].default_value[2]=value
                    world['hdri_rotation']=value
            # for link in links:
            #     if type(link.to_node) is bpy.types.ShaderNodeTexEnvironment:
            #         if type(link.from_node) is bpy.types.ShaderNodeMapping:
            #             mapping = link.from_node
            #             mapping.inputs[2].default_value[2]=value
    return None

def get_hdri_temperature(self):
    return self.get('hdri_temperature',  6500)

def set_hdri_temperature(self,value):
    self['hdri_temperature'] = value
    wb = get_wb_groups(bpy.context)
    for n in wb:
        n.inputs[3].default_value=value
    return None

def get_hdri_tint(self):
    return self.get('hdri_tint',  0)

def set_hdri_tint(self,value):
    self['hdri_tint'] = value
    wb = get_wb_groups(bpy.context)
    for n in wb:
        n.inputs[4].default_value=value
    return None

def update_hdri_use_temperature(self,context):
    wb = get_wb_groups(context)
    for n in wb:
        if self.hdri_use_temperature:
            n.inputs[1].default_value=1
        else:
            n.inputs[1].default_value=0

def get_hdri_color(self):
    return self.get('hdri_color',  (1.0,1.0,1.0,1.0))

def set_hdri_color(self,value):
    self['hdri_color'] = value
    wb = get_wb_groups(bpy.context)
    for n in wb:
        n.inputs[2].default_value=value
    return None

def get_hdri_blur(self):
    return self.get('hdri_blur',  0)

def set_hdri_blur(self,value):
    self['hdri_blur'] = value
    blur = get_blur_groups(bpy.context)
    for n in blur:
        n.inputs[1].default_value=value
    return None

def enum_previews_hdri_tex(self, context):
    # print (enum_previews_from_directory_items(self, context,'hdri'))
    return enum_previews_from_directory_items(self, context,'hdri')

def update_cam_world(self,context,world):
    # Update Cam World for Override
    if context.scene.camera:
        settings = context.scene.camera.data.photographer
        settings.cam_world = world.name
        context.scene.lightmixer.hdri_rotation = world.get('hdri_rotation',0)
        return settings.cam_world

def update_hdri_tex(self,context):
    world = context.scene.world
    if world and world.get('is_world_hdri',False):
        if world.use_nodes:
            nodes = world.node_tree.nodes
            for node in nodes:
                if type(node) is bpy.types.ShaderNodeTexEnvironment:
                    prefs = context.preferences.addons[__package__].preferences
                    if prefs.hdri_lib_path:
                        hdri_tex = context.scene.lightmixer.hdri_tex
                        world['hdri_tex'] = hdri_tex
                        world['hdri_category'] = context.scene.lightmixer.hdri_category
                        if hdri_tex not in {'empty',''}:
                            node.image = bpy.data.images.load(hdri_tex, check_existing=True)
                            # node.image.colorspace_settings.name = 'Linear'

                            name = os.path.splitext(node.image.name)[0]
                            world['hdri_name'] = name

                            # If automatic World renaming is enabled in the preferences
                            prefs = context.preferences.addons[__package__].preferences
                            if prefs.hdri_auto_world_rename:
                                # Don't increment against itself, ignoring numbers at the end
                                if world.name.rsplit('.',1)[0] != name.rsplit('.',1)[0]:
                                    counter = 0
                                    # Increment name if world already exists
                                    while name in bpy.data.worlds:
                                        counter += 1
                                        numbers = "." + str(counter).zfill(3)
                                        name = os.path.splitext(node.image.name)[0] + numbers
                                    world.name = name

                                    # Update Cam World value
                                    update_cam_world(self,context,world)


class LIGHTMIXER_OT_World_HDRI_Add(bpy.types.Operator):
    bl_idname = "lightmixer.hdri_add"
    bl_label = "Add World HDRI"
    bl_description = "Creates HDRI Environment material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):

        # world = bpy.data.worlds.new("World HDRI")
        world = context.scene.world
        world.name = "World HDRI"
        world['is_world_hdri'] = True
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Mapping
        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (-200,0)

        coord = nodes.new('ShaderNodeTexCoord')
        coord.location = (-400,0)

        # Texture
        img = nodes.new('ShaderNodeTexEnvironment')
        img.location = (0,0)
        img.name = 'World HDRI Tex'

        # Shader
        bg = nodes['Background']
        bg.location = (300,0)

        # Output
        output = nodes['World Output']
        output.location = (500,0)

        # Connect them
        links.new(coord.outputs[0], mapping.inputs['Vector'])
        links.new(mapping.outputs[0], img.inputs[0])
        links.new(img.outputs[0], bg.inputs[0])
        links.new(bg.outputs[0], output.inputs[0])

        context.scene.world = world
        update_hdri_tex(self,context)

        # Add Color controls
        bpy.ops.lightmixer.world_add_controls()

        if context.scene.render.engine == 'LUXCORE':
            world.luxcore.use_cycles_settings = True

        # Update Cam World value
        update_cam_world(self,context,world)

        return {'FINISHED'}

class LIGHTMIXER_OT_Sky_Texture_Add(bpy.types.Operator):
    bl_idname = "lightmixer.sky_add"
    bl_label = "Add Sky Texture"
    bl_description = "Creates Sky Environment material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):

        # world = bpy.data.worlds.new("Physical Sky")
        world = context.scene.world
        world.name = "Physical Sky"
        world['is_sky'] = True
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Texture
        img = nodes.new('ShaderNodeTexSky')
        img.location = (0,0)
        img.name = 'Sky Texture'

        # Shader
        bg = nodes['Background']
        bg.location = (300,0)

        # Output
        output = nodes['World Output']
        output.location = (500,0)

        # Connect them
        links.new(img.outputs[0], bg.inputs[0])
        links.new(bg.outputs[0], output.inputs[0])

        context.scene.world = world
        update_hdri_tex(self,context)

        # Add Color controls
        bpy.ops.lightmixer.world_add_controls()

        if context.scene.render.engine == 'LUXCORE':
            world.luxcore.use_cycles_settings = True

        # Update Cam World value
        update_cam_world(self,context,world)

        return {'FINISHED'}

# Light Mixer Properties functions
def update_world_enabled(self,context):
    world = context.scene.world
    if context.scene.render.engine == 'LUXCORE' and not world.luxcore.use_cycles_settings:
        if world.enabled:
            if world.luxcore.light != 'none':
                if world.luxcore.light == "sky2":
                    world.luxcore.sun_sky_gain = world.strength
                else:
                    world.luxcore.gain = world.strength
        else:
            if world.luxcore.light != 'none':
                if world.luxcore.light == "sky2":
                    world.strength = world.luxcore.sun_sky_gain
                    world.luxcore.sun_sky_gain = 0
                else:
                    world.strength = world.luxcore.gain
                    world.luxcore.gain = 0
    else:
        backgrounds = get_background(context)
        for background in backgrounds:
            if world.enabled:
                background.inputs['Strength'].default_value = background["strength"]
            else:
                background["strength"] = background.inputs['Strength'].default_value
                background.inputs['Strength'].default_value = 0

def update_world_solo(self,context):
    world = context.scene.world
    backgrounds = get_background(context)

    for background in backgrounds:
        # Store Strength value
        if world.enabled:
            background["strength"] = background.inputs['Strength'].default_value

        # World Solo Update for Lights and World
        light_objs = [o for o in bpy.data.objects if o.type == 'LIGHT']
        for light_obj in light_objs:
            if world.solo:
                context.scene.lightmixer.solo_active = True
                light_obj.hide_viewport = True
                light_obj.hide_render = True
                background.inputs['Strength'].default_value = background["strength"]
            else:
                context.scene.lightmixer.solo_active = False
                light_obj.hide_viewport = not light_obj.lightmixer.enabled
                light_obj.hide_render = not light_obj.lightmixer.enabled
                if world.enabled:
                    background.inputs['Strength'].default_value = background["strength"]
                else:
                    # world.strength = background.inputs['Strength'].default_value
                    background.inputs['Strength'].default_value = 0

    # World Solo Update for Materials
    emissive_mats = [mat for mat in bpy.data.materials if mat.get('is_emissive', False)]
    for mat in emissive_mats:
        nodes = mat.node_tree.nodes
        for node in mat.get('em_nodes', ''):
            em_node,ctrl_node, ctrl_input = get_em_strength(mat,node)
            if em_node and ctrl_node and ctrl_input:
                if world.solo:
                    em_node.lightmixer.strength = nodes[ctrl_node].inputs[ctrl_input].default_value
                    nodes[ctrl_node].inputs[ctrl_input].default_value = 0
                else:
                    nodes[ctrl_node].inputs[ctrl_input].default_value = em_node.lightmixer.strength

    if world.solo:
        context.scene.lightmixer.solo_active = True
    else:
        context.scene.lightmixer.solo_active = False

class LIGHTMIXER_OT_WorldEnable(bpy.types.Operator):
    bl_idname = "lightmixer.world_enable"
    bl_label = "Enable World"
    bl_description = "Shift-Click to Solo this light"
    bl_options = {'UNDO'}

    bpy.types.World.enabled = bpy.props.BoolProperty(default=True,update=update_world_enabled)
    bpy.types.World.strength = bpy.props.FloatProperty(precision=3)
    bpy.types.World.solo = bpy.props.BoolProperty(update=update_world_solo)
    shift: bpy.props.BoolProperty()

    @classmethod
    def poll(cls,context):
        return context.scene.world.use_nodes

    def execute(self, context):
        world = context.scene.world

        if self.shift:

            if context.scene.lightmixer.solo_active and not world.solo:
                all_objs = context.scene.collection.all_objects
                solo_light=[obj for obj in all_objs if obj.type=='LIGHT' and obj.lightmixer.solo]
                solo_mat = [mat for mat in bpy.data.materials if mat.get('is_emissive', False) and mat.lightmixer.solo]
                if solo_light:
                    solo_light[0].lightmixer.solo = False
                    world.solo = True
                elif solo_mat:
                    solo_mat[0].lightmixer.solo = False
                    world.solo = True
            else:
                world.solo = not world.solo
        else:
            if not world.solo:
                world.enabled = not world.enabled

        if context.scene.render.engine == 'LUXCORE':
            # Refresh viewport Trick
            bpy.ops.object.add(type='EMPTY')
            bpy.ops.object.delete()
        return{'FINISHED'}

    def invoke(self, context, event):
        self.shift = event.shift
        return self.execute(context)

class LIGHTMIXER_OT_World_AddControls(bpy.types.Operator):
    bl_idname = "lightmixer.world_add_controls"
    bl_label = "Add Color Controls"
    bl_description = "Adds White Balance and Blur nodes to the World material"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls,context):
        return context.scene.world.use_nodes

    def execute(self, context):
        # Using forward slashes for macOS
        dir = os.path.join(photographer_folder,"blends/node_groups.blend/NodeTree/")
        # Normalize slashes for Windows // linux
        dir = os.path.normpath(dir)

        wb_grp = [g for g in bpy.data.node_groups if g.name == wb_name]
        if wb_grp:
            wb_grp = wb_grp[0]
        else:
            # Append Node Group
            bpy.ops.wm.append(filename=wb_name, directory=dir)
            wb_grp = [g for g in bpy.data.node_groups if g.name == wb_name][0]

        blur_grp = [g for g in bpy.data.node_groups if g.name == blur_name]
        if blur_grp:
            blur_grp = blur_grp[0]
        else:
            # Append Node Group
            bpy.ops.wm.append(filename=blur_name, directory=dir)
            blur_grp = [g for g in bpy.data.node_groups if g.name == blur_name][0]

        # Get node groups
        wb = get_wb_groups(context)
        if wb:
            wb = wb[0]
        blur = get_blur_groups(context)
        if blur:
            blur = blur[0]

        world = context.scene.world
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Get Environment texture and Background nodes
        if world.get('is_world_hdri', False):
            tex = [n for n in nodes if n.bl_idname=='ShaderNodeTexEnvironment' and n.name=='World HDRI Tex']
            if tex:
                img = tex[0]
                map = img.inputs['Vector']
        # If no HDRI, check for Sky
        elif world.get('is_sky', False):
            tex = [n for n in nodes if n.bl_idname=='ShaderNodeTexSky' and n.name=='Sky Texture']
            if tex:
                img = tex[0]

        if not tex:
            return {'CANCELLED'}

        bg = [n for n in nodes if n.bl_idname=='ShaderNodeBackground']
        if not bg:
            return {'CANCELLED'}
        else:
            bg = bg[0]
            color = bg.inputs['Color']

        if world.get('is_world_hdri', False) and not blur:
            # Move nodes before the Env Texture node
            for node in nodes:
                if node.location[0] < img.location[0]:
                    node.location[0] -= 200
            blur = nodes.new('ShaderNodeGroup')
            blur.node_tree = blur_grp
            blur.location = (img.location[0]-200, img.location[1])

        if not wb:
            # Move nodes before the Background node
            for node in nodes:
                if node.location[0] < bg.location[0]:
                    node.location[0] -= 200
            wb = nodes.new('ShaderNodeGroup')
            wb.node_tree = wb_grp
            wb.location = (bg.location[0]-200,bg.location[1])

        # Insert Node groups
        if world.get('is_world_hdri', False):
            link_map = [l for l in links if l.to_node == img and l.to_socket == map]
            inc_map = link_map[0].from_node
            inc_map_socket = link_map[0].from_socket.name

            if inc_map != blur:
                links.new(inc_map.outputs[inc_map_socket], blur.inputs[0])
            links.new(blur.outputs[0], map)

        link_bg = [l for l in links if l.to_node == bg and l.to_socket == color]
        inc_color = link_bg[0].from_node
        inc_color_socket = link_bg[0].from_socket.name

        if inc_color != wb:
            links.new(inc_color.outputs[inc_color_socket], wb.inputs[0])
        links.new(wb.outputs[0], color)

        return {'FINISHED'}

class LIGHTMIXER_OT_Refresh_HDR_Categories(bpy.types.Operator):
    bl_idname = "lightmixer.refresh_hdr_categories"
    bl_label = "Refresh HDRI library"
    bl_description = "Updates HDRIs, library subfolders and thumbnails"
    # bl_options = {'UNDO'}

    def execute(self, context):
        hdri_lib_path_update(self,context)
        return {'FINISHED'}


class LIGHTMIXER_OT_Cycle_World(bpy.types.Operator):
    bl_idname = "lightmixer.cycle_world"
    bl_label = "Cycle between Worlds"
    bl_description = "Cyles through cameras in the scene"
    bl_options = {'UNDO'}

    previous: bpy.props.BoolProperty()

    def execute(self,context):
        worlds = [w.name for w in bpy.data.worlds]
        current = worlds.index(context.scene.world.name)

        if self.previous:
            next = worlds[(current-1) % len(worlds)]
        else:
            next = worlds[(current+1) % len(worlds)]
            
        context.scene.world = bpy.data.worlds[next]

        return {'FINISHED'}