import bpy
from math import radians
from ..ui.library import enum_previews_from_directory_items
from ..functions import should_update

LE_VERSION = 6

light_effects_grp_name = 'Photographer Camera Post FX'
stmap_tex_name = 'STMap Texture'
effects = {
    'lens_distortion',
    'lateral_ca',
    'lens_softness',
    'fringing',
    'lens_vignetting',
    'sharpen',
    'film_grain',
}
effects_params = {
    'lens_distortion_amount',
    'lens_distortion_scale_comp',
    'lateral_ca_amount',
    'lens_softness_amount',
    'center_softness_amount',
    'corner_softness_amount',
    'corner_softness_falloff',
    'corner_softness_mask',
    'fringing_amount',
    'fringing_size',
    'fringing_threshold',
    'lens_vignetting_amount',
    'lens_vignetting_falloff',
    'lens_vignetting_mask',
    'sharpen_amount',
    'sharpen_radius',
    'film_grain_amount',
    'film_grain_size',
}
effects_color_params = {
    'fringing_color',
}

def get_comp_group_node(context,name):
    scene = context.scene
    group_node = None
    if scene.use_nodes:
        nodes = scene.node_tree.nodes
        group_nodes=[n for n in nodes if n.bl_idname=='CompositorNodeGroup' and n.name==name]
        if group_nodes:
            group_node = group_nodes[0]
    return group_node

def get_comp_node_in_group(context, group, name):
    node = None
    if group:
        nodes =[n for n in group.node_tree.nodes if n.name==name]
        if nodes:
            node = nodes[0]
    return node

def update_post_effects(self,context):
    scene = context.scene
    pg_main_cam = bpy.data.objects.get(scene.photographer.main_camera,None)

    if self.post_effects_enabled:
        if not scene.use_nodes:
            scene.use_nodes = True
        if self == scene.camera.data.post_effects:
            update_post_effects_enabled(scene.camera.data.post_effects,context)
    elif pg_main_cam:
        update_post_effects_enabled(pg_main_cam.data.post_effects,context)
    else:
        le_node = get_comp_group_node(context,light_effects_grp_name)
        if le_node:
            le_node.mute = not self.post_effects_enabled

def update_post_effects_enabled(self,context):
    update = should_update(self,context,'post_effects_enabled',True)
    if update:
        # Get Lens Effects node. If none, create one.
        le_node = get_comp_group_node(context,light_effects_grp_name)
        if not le_node:
            if self.post_effects_enabled:
                bpy.ops.photographer.post_effects_add()
        else:
            le_node.mute = not self.post_effects_enabled

        # if self.post_effects_enabled:
        update_post_effects_params(self,context)
        update_lateral_ca_type(self,context)
        update_post_effects_color_params(self,context)
        update_lens_distortion_type(self,context)
        update_stmap_tex(self,context)
        update_film_grain_tex(self,context)
        update_streaks(self,context)

def update_lens_distortion_type(self,context):
    le_node = get_comp_group_node(context,light_effects_grp_name)
    if le_node:
        node = get_comp_node_in_group(context,le_node,'lens_distortion_type')
        if self.lens_distortion_type == 'SIMPLE':
            node.outputs[0].default_value = 0.0
        elif self.lens_distortion_type == 'STMAP':
            node.outputs[0].default_value = 1.0
            update_stmap_tex(self,context)

def update_post_effects_params(self,context):
    le_node = get_comp_group_node(context,light_effects_grp_name)
    if le_node:
        for e in effects:
            node = get_comp_node_in_group(context,le_node,e)
            if node:
                node.mute = not self.get(e,False)
                if not node.mute:
                    if node.name == 'lens_distortion':
                        update_stmap_tex(self,context)
                    elif node.name == 'film_grain':
                        update_film_grain_tex(self,context)
        for p in effects_params:
            node = get_comp_node_in_group(context,le_node,p)
            if node:
                if node.name == "corner_softness_mask":
                    node.width = self.corner_mask_width
                    node.height = self.corner_mask_height
                elif node.name == "lens_vignetting_mask":
                    node.width = self.lens_vignetting_width
                    node.height = self.lens_vignetting_height
                else:
                    default_value = self.bl_rna.properties[p].default
                    node.outputs[0].default_value = self.get(p,default_value)

def update_post_effects_color_params(self,context):
    le_node = get_comp_group_node(context,light_effects_grp_name)
    if le_node:
        for e in effects:
            node = get_comp_node_in_group(context,le_node,e)
            if node:
                node.mute = not self.get(e,False)
        for p in effects_color_params:
            node = get_comp_node_in_group(context,le_node,p)
            if node:
                # default_color = self.bl_rna.properties[p].default
                # Not working, returns a float and not a color?
                node.outputs[0].default_value = self.get(p,(0.35,0.085,0.66,1.0))

def update_lateral_ca_type(self,context):
    le_node = get_comp_group_node(context,light_effects_grp_name)
    if le_node:
        node = get_comp_node_in_group(context,le_node,'lateral_ca_type')
        if node:
            if self.lateral_ca_type == 'RED':
                node.outputs[0].default_value = (1.0,0.0,0.0,1.0)
            elif self.lateral_ca_type == 'GREEN':
                node.outputs[0].default_value = (0.0,1.0,0.0,1.0)
            elif self.lateral_ca_type == 'BLUE':
                node.outputs[0].default_value = (0.0,0.0,1.0,1.0)
            elif self.lateral_ca_type == 'DISPERSION':
                node.outputs[0].default_value = (0.0,0.0,0.0,1.0)

def update_streaks(self,context):
    le_node = get_comp_group_node(context,light_effects_grp_name)
    if le_node:
        node = get_comp_node_in_group(context,le_node,'glare_streaks')
        if node:
            node.mute = not self.get('streaks',False)
            node.mix = self.streaks_amount - 1.0
            node.threshold = self.streaks_threshold
            node.streaks = self.streaks_number
            node.angle_offset = self.streaks_angle_offset
            node.fade = self.streaks_fade


def enum_previews_stmap(self, context):
    return enum_previews_from_directory_items(self, context,'stmap')

def update_stmap_tex(self,context):
    if self.lens_distortion_type == 'STMAP':
        le_node = get_comp_group_node(context,light_effects_grp_name)
        if le_node:
            node = get_comp_node_in_group(context,le_node,'stmap_tex')
            if node:
                if self.stmap_tex != 'empty':
                    node.image = bpy.data.images.load(self.stmap_tex, check_existing=True)
                    colorspaces = ['Non-Color']
                    for cs in colorspaces:
                        try:
                            node.image.colorspace_settings.name = cs
                        except:
                            pass

def enum_previews_film_grain(self, context):
    return enum_previews_from_directory_items(self, context,'film_grain')

def update_film_grain_tex(self,context):
    if self.film_grain:
        le_node = get_comp_group_node(context,light_effects_grp_name)
        if le_node:
            node = get_comp_node_in_group(context,le_node,'film_grain_tex')
            if node:
                if self.film_grain_tex != 'empty':
                    node.image = bpy.data.images.load(self.film_grain_tex, check_existing=True)
                    colorspaces = ['Non-Color']
                    for cs in colorspaces:
                        try:
                            node.image.colorspace_settings.name = cs
                        except:
                            pass


class LensEffectsSettings(bpy.types.PropertyGroup):

    post_effects_enabled : bpy.props.BoolProperty(
        name = 'Lens Effects',
        description = "Enable Lens Effects (uses Compositing)",
        default = False,
        options = {'HIDDEN'},
        update = update_post_effects
    )
    lens_distortion : bpy.props.BoolProperty(
        name = "Distortion",
        description = "Enable Distortion",
        default = False,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lens_distortion_type : bpy.props.EnumProperty(
        name = "Distortion Type",
        description = "Choose between Simple (Blender Lens Distortion) or an STMap to create Lens Distortion",
        items = [('SIMPLE','Simple', 'Uses Blender Lens Distortion node'),('STMAP','STMap','Uses STMap. Warning: Viewport rendering is not supported yet')],
        default = 'SIMPLE',
        options = {'HIDDEN'},
        update = update_lens_distortion_type
    )
    lens_distortion_amount : bpy.props.FloatProperty(
        name = "Distortion Amount",
        description = "Barrel distortion using positive values, Pin cushion distortio using negative values",
        default = 0.25, soft_min = -1, soft_max = 1,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lens_distortion_scale_comp : bpy.props.FloatProperty(
        name = "Scale Compensation",
        description = "Percentage of scaling up to fix missing potential missing pixels after STMap distortion",
        default = 0, soft_min=0, soft_max = 10,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    stmap_tex: bpy.props.EnumProperty(
        name="STMap Image",
        items=enum_previews_stmap,
        default=0,
        update=update_stmap_tex,
    )
    lateral_ca : bpy.props.BoolProperty(
        name = "Lateral Chromatic Aberration",
        description = "Enable Lateral Chromatic Aberration",
        default = False,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lateral_ca_amount : bpy.props.FloatProperty(
        name = "Lateral Chromatic Aberration Amount",
        description = "Amount of channels and blur offset to create Lateral Chromatic Aberration on the corner of the image",
        default = 0.5, min=0.0, soft_max = 1.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lateral_ca_type : bpy.props.EnumProperty(
        name = "Lateral Chromatic Aberration Colors",
        description = "Choose Red and Cyan, Blue and Yellow or Green and Purple chromatic aberration",
        items = [('DISPERSION','Dispersion', 'Uses Blender Lens Dispersion'),
                 ('RED','Red/Cyan', 'Red and Cyan Chromatic Aberration'),
                 ('GREEN','Green/Magenta', 'Green and Magenta Chromatic Aberration'),
                 ('BLUE','Blue/Yellow', 'Blue and Yellow Chromatic Aberration'),
                 ],
        default = 'DISPERSION',
        options = {'HIDDEN'},
        update = update_lateral_ca_type,
    )
    fringing : bpy.props.BoolProperty(
        name = "Fringing",
        description = "Enable Fringing from bright areas of the image",
        default = False,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    fringing_amount : bpy.props.FloatProperty(
        name = "Fringing Amount",
        description = "Amount of Fringing",
        default = 0.5, min=0, soft_max = 1.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    fringing_size : bpy.props.FloatProperty(
        name = "Fringing Size",
        description = "Fringing bluriness",
        default = 0.25, min=0, max = 1.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    fringing_threshold : bpy.props.FloatProperty(
        name = "Fringing Threshold",
        description = "Pixels with brightness higher than this value participate to fringing",
        default = 0.9, min=0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    fringing_color : bpy.props.FloatVectorProperty(
        name='Fringing Color',
        description="Fringing from lenses is usually purple behind the focus point due to longitudinal chromatic aberration",
        subtype='COLOR', min=0.0, max=1.0, size=4, default=(0.35,0.085,0.66,1.0),
        options = {'HIDDEN'},
        update = update_post_effects_color_params,
    )
    streaks: bpy.props.BoolProperty(
        name = "Streaks",
        description = "Enable Glare Streaks",
        default = False,
        options = {'HIDDEN'},
        update = update_streaks,
    )
    streaks_amount : bpy.props.FloatProperty(
        name = "Streaks Amount",
        default = 0.5, min=0.0, max=1.0,
        options = {'HIDDEN'},
        update = update_streaks,
    )
    streaks_number : bpy.props.IntProperty(
        name = "Number of Streaks",
        description = "Usually corresponds to the number of Aperture blades",
        default = 6, min= 1, max=16,
        options = {'HIDDEN'},
        update = update_streaks,
    )
    streaks_threshold : bpy.props.FloatProperty(
        name = "Streaks Threshold",
        description = "Pixels with brightness higher than this value will create Streaks",
        default = 0.9, min=0,
        options = {'HIDDEN'},
        update = update_streaks,
    )
    streaks_angle_offset : bpy.props.FloatProperty(
        name = "Streaks Angle offset",
        default = radians(15), min=0, max=radians(180),subtype="ANGLE",
        options = {'HIDDEN'},
        update = update_streaks,
    )
    streaks_fade : bpy.props.FloatProperty(
        name = "Streaks Fade Length",
        default = 0.8, min=0.75,max=1.0,
        options = {'HIDDEN'},
        update = update_streaks,
    )
    lens_vignetting: bpy.props.BoolProperty(
        name = "Vignetting",
        description = "Enable Vignetting. Note that Optical Vignetting can also be used to achieve such effect",
        default = False,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lens_vignetting_amount : bpy.props.FloatProperty(
        name = "Vignetting Amount",
        description = "Vignetting opacity",
        default = 0.5, min=0, soft_max = 1,
        update = update_post_effects_params,
    )
    lens_vignetting_falloff : bpy.props.FloatProperty(
        name = "Vignetting Falloff",
        description = "Vignetting Mask Falloff",
        default = 0.75, min=0.0, soft_min=0.1, max=1.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lens_vignetting_width : bpy.props.FloatProperty(
        name = "Vignetting Width",
        default = 0.75, min=0, soft_max = 2,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lens_vignetting_height : bpy.props.FloatProperty(
        name = "Vignetting Height",
        default = 0.75, min=0, soft_max = 2,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    sharpen: bpy.props.BoolProperty(
        name = "Sharpen",
        description = "Enable Sharpen controls for image post-sharpening",
        default = False,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    sharpen_amount : bpy.props.FloatProperty(
        name = "Sharpen Amount",
        description = "Sharpen Amount",
        default = 0, min=-2, soft_max = 2,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    sharpen_radius : bpy.props.FloatProperty(
        name = "Sharpen Radius",
        description = "Sharpen Radius",
        default = 0.5, min=0, soft_max = 1,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lens_softness: bpy.props.BoolProperty(
        name = "Lens Softness",
        description = "Enable Lens Softness controls",
        default = False,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    lens_softness_amount : bpy.props.FloatProperty(
        name = "Lens Softness Amount",
        default = 0.5, min=0.0, max=1.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    corner_softness_amount : bpy.props.FloatProperty(
        name = "Blur Size",
        default = 0.5, min=0, soft_max = 4.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    center_softness_amount : bpy.props.FloatProperty(
        name = "Center Softness",
        default = 0.0, min=0.0, soft_max = 1.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    corner_softness_falloff : bpy.props.FloatProperty(
        name = "Corner Falloff",
        default = 0.75, min=0.0, max=1.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    corner_mask_width : bpy.props.FloatProperty(
        name = "Corner Width",
        default = 0.5, min=0, max = 2,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    corner_mask_height : bpy.props.FloatProperty(
        name = "Corner Height",
        default = 0.5, min=0, max = 2,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    film_grain: bpy.props.BoolProperty(
        name = "Film Grain",
        description = "Enable Film Grain controls",
        default = False,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    film_grain_amount : bpy.props.FloatProperty(
        name = "Film Grain Amount",
        default = 0.5, min=0.0, soft_max=1.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    film_grain_size : bpy.props.FloatProperty(
        name = "Film Grain Scale",
        default = 1.0, min=0.001, soft_max = 10.0,
        options = {'HIDDEN'},
        update = update_post_effects_params,
    )
    film_grain_tex: bpy.props.EnumProperty(
        name="Film Grain texture",
        items=enum_previews_film_grain,
        default=0,
        update=update_film_grain_tex,
    )