import bpy
from bpy.props import (
        IntProperty,
        BoolProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty
        )

from ..orchestration import decorators
from . import plating_functions


pattern_type_props = (('0', 'Criss Cross', ''),
                        ('6', 'Ruby Dragon', ''),
                        ('2', 'Triangular', ''),
                        ('3', 'Rectangles', ''),
                        ('4', 'Morse-Brown', ''),
                        ('5', 'UV Seams', ''),
                        ('1', 'Selected Edges', ''),
                        )



def update_prop(self, context):

    if self.is_property_group and \
            context.active_object and \
                context.active_object.plating_generator.auto_update and \
                context.active_object.plating_generator.is_plating_obj:
        # get ref to level
        level = context.active_object.plating_generator.levels[context.active_object.plating_generator.level_index]
        if level.is_enabled:
            decorators.decorate(context.active_object, context)

    return None

def update_mat_prop(self, context):

    if self.is_property_group and \
            context.active_object and \
                context.active_object.plating_generator.auto_update and \
                context.active_object.plating_generator.is_plating_obj:
        # get ref to level
        level = context.active_object.plating_generator.levels[context.active_object.plating_generator.level_index]
        if level.is_enabled:
            decorators.decorate(context.active_object, context)

    return None


class PlatingGeneratorMaterial(bpy.types.PropertyGroup):
    """A class representing the properties of a material."""
    is_property_group : BoolProperty(default=False)
    name : bpy.props.StringProperty(name="Name", default="", update=update_mat_prop)

#
# Class that contains plate creation logic.
#
class PlatingGeneratorProps():
    is_property_group : BoolProperty(default=False)

    pattern_type : bpy.props.EnumProperty(items=pattern_type_props,
                                                     name = "Pattern Type", default='0', update=update_prop)


    random_seed : IntProperty(
        name="Random Seed",
        description="Seed for generating plating pattern",
        default=123456,
        update=update_prop
        )

    pre_subdivisions : IntProperty(
        name="Subdivisions",
        description="Number of times the faces are subdivided before applying the edge pattern",
        min=0,
        default=0,
        soft_max=10,
        update=update_prop
        )

    amount : FloatProperty(
        name="Percentage",
        description="Number of times a plate cut will be made",
        min=0,
        max=100,
        default=50,
        subtype="PERCENTAGE",
        update=update_prop
        )

    rectangle_random_seed : IntProperty(
        name="Rectangle Random Seed",
        description="Seed for generating rectangles in the pattern",
        default=123456,
        update=update_prop
        )

    rectangle_amount : IntProperty(
        name="Amount of Rectangles",
        description="Number of times a plate rectangle will be made",
        min=0,
        default=10,
        update=update_prop
        )


    rectangle_width_min : IntProperty(
        name="Rectangle Width",
        description="Rectangle Width in Edges",
        min=1,
        default=5,
        update=update_prop
        )

    rectangle_width_max : IntProperty(
        name="Rectangle Width",
        description="Rectangle Width in Edges",
        min=1,
        default=5,
        update=update_prop
        )

    rectangle_height_min : IntProperty(
        name="Rectangle Height",
        description="Rectangle Height in Edges",
        min=1,
        default=5,
        update=update_prop
        )

    rectangle_height_max : IntProperty(
        name="Rectangle Height",
        description="Rectangle Height in Edges",
        min=1,
        default=5,
        update=update_prop
        )


    triangle_random_seed : IntProperty(
        name="Triangles Random Seed",
        description="Seed for generating triangles in the pattern",
        default=123456,
        update=update_prop
        )

        
    triangle_percentage : FloatProperty(
            name="Amount of triangles",
            description="Amount of triangles to introduce into the pattern",
            subtype="PERCENTAGE",
            min=0,
            max=100,
            default=5,
            step=1,
            update=update_prop
            )

    ruby_dragon_random_seed : IntProperty(
        name="Random Seed",
        description="Seed for generating the pattern",
        default=123456,
        update=update_prop
        )

        
    ruby_dragon_percentage : FloatProperty(
            name="Percentage",
            description="Amount to introduce into the pattern",
            subtype="PERCENTAGE",
            min=0,
            max=100,
            default=75,
            step=1,
            update=update_prop
            )

    groove_width : FloatProperty(
            name="Groove Width",
            description="Bevel width of grooves",
            min=0,
            default=0.01,
            precision=3,
            step=1,
            update=update_prop
            )

    clamp_grooves : BoolProperty(
            name="Clamp Groove Width",
            description="Attempt to prevent grooves from overlapping",
            default=False,
            update=update_prop
            )

    groove_depth : FloatProperty(
        name="Groove Depth",
        description="Depth of grooves",
        default=0.01,
        precision=3,
        step=1,
        update=update_prop
        )

    groove_segments : IntProperty (
            name="Groove Segments",
            description="Number of segments inside the grooves",
            min=1,
            max=10,
            default=1,
            update=update_prop
    )

    side_segments : IntProperty (
            name="Plate Side Segments",
            description="Number of segments on the side of the plates",
            min=1,
            max=10,
            default=1,
            update=update_prop
    )

    bevel_amount : FloatProperty(
            name="Plate Bevel Amount",
            description="How bevelled are the top of the plates",
            min=0.000,
            default=0.000,
            precision=3,
            step=1,
            update=update_prop
            )

    bevel_segments : IntProperty(
            name="Plate Bevel Segments",
            description="How many segments the plate bevel has",
            min=1,
            default=1,
            update=update_prop
            )

    bevel_outer_bevel_type : bpy.props.EnumProperty(items= (('OFFSET', 'Offset', ''),
                                                     ('WIDTH', 'Width', ''),
                                                     ('DEPTH', 'Depth', ''),
                                                     ('PERCENT', 'Percent', '')),
                                                     name = "Plate Bevel Type", default='OFFSET', update=update_prop)

    groove_bevel_amount : FloatProperty(
            name="Groove Bevel Amount",
            description="How bevelled are the grooves between the plates",
            min=0.000,
            default=0.000,
            precision=3,
            step=1,
            update=update_prop
            )

    groove_bevel_segments : IntProperty(
            name="Groove Bevel Segments",
            description="How many segments the groove bevel has",
            min=1,
            default=1,
            update=update_prop
            )

    groove_bevel_outer_bevel_type : bpy.props.EnumProperty(items= (('OFFSET', 'Offset', ''),
                                                     ('WIDTH', 'Width', ''),
                                                     ('DEPTH', 'Depth', ''),
                                                     ('PERCENT', 'Percent', '')),
                                                     name = "Groove Bevel Type", default='OFFSET', update=update_prop)


    def update_sync_heights(self, context):
        if self.sync_heights:
            self.plate_max_height = self.plate_min_height
        update_prop(self, context)
        return None

    sync_heights : BoolProperty(
            name="Match Heights",
            description="Keep Min height and Max Height the same.",
            default=False,
            update=update_sync_heights
            )

    def update_min_height(self, context):
        if self.sync_heights:
            if self.plate_min_height != self.plate_max_height:
                self.plate_max_height = self.plate_min_height
        update_prop(self, context)
        return None

    plate_min_height : FloatProperty(
            name="Min Plate Height",
            description="Minimum Plate Height",
            default=0.000,
            precision=3,
            step=1,
            update=update_min_height
            )

    def update_max_height(self, context):
        if self.sync_heights:
            if self.plate_min_height != self.plate_max_height:
                self.plate_min_height = self.plate_max_height
        update_prop(self, context)
        return None

    plate_max_height : FloatProperty(
            name="Max Plate Height",
            description="Maximum Plate Height",
            default=0.000,
            precision=3,
            step=1,
            update=update_max_height
            )

    plate_height_random_seed : IntProperty(
        name="Plate Height Random Seed",
        description="Seed for generating plating heights",
        default=123456,
        update=update_prop
        )

    plate_taper : FloatProperty(
            name="Plate Taper",
            description="Plate taper amount",
            default=0.000,
            precision=3,
            step=1,
            update=update_prop
            )

    select_grooves : BoolProperty(
            name="Select Grooves",
            description="Select groove topology",
            default=False,
            update=update_prop
            )

    select_plates : BoolProperty(
            name="Select Plates",
            description="Select plate topology",
            default=True,
            update=update_prop
            )

    select_sides : BoolProperty(
            name="Select Plates",
            description="Select plate topology",
            default=True,
            update=update_prop
            )

    mark_seams : BoolProperty(
            name="Mark UV Seams",
            description="Mark UV Seams for texture mapping",
            default=False,
            update=update_prop
            )

    edge_split : BoolProperty(
            name="Edge Split",
            description="Apply an edge split to clearly display the grooves",
            default=False,
            update=update_prop
            )

    remove_grooves : BoolProperty(
            name="Remove Grooves",
            description="Remove the grooves to just leave the plates",
            default=False,
            update=update_prop
            )

    remove_inner_grooves : BoolProperty(
            name="Remove Inner Grooves",
            description="Remove the inner grooves, not the bevels, to just leave the plates",
            default=False,
            update=update_prop
            )

    edge_selection_only : BoolProperty(
            name="Edge Selection Only",
            description="Only output the edge selection on the mesh",
            default=False,
            update=update_prop
            )

    cut_at_faces : BoolProperty(
            name="Add Grooves by Face Angle",
            description="Automatically add grooves between faces at a specified angle",
            default=True,
            update=update_prop
            )

    face_angle_limit : FloatProperty(
            name="Edge Angle",
            description="Deliberately place panel lines along faces at this angle ",
            min=0,
            default=90,
            update=update_prop

    )

    face_angle_dev : FloatProperty(
            name="Edge Angle Deviation",
            description="Deviation from face angle to select ",
            min=0,
            max=1,
            default=0.1,
            update=update_prop

    )

    def update_sync_corners(self, context):
        if hasattr(self, 'name') and self.name:
            self.corner_width = self.minor_corner_width
            self.corner_bevel_segments = self.minor_corner_bevel_segments
        update_prop(self, context)
        return None

    sync_corners : BoolProperty(
            name="Match Corners",
            description="Keep Major and Minor Corners the same.",
            default=True,
            update=update_sync_corners
            )

    def update_corner(self, context):
        if self.sync_corners:
            if self.minor_corner_width != self.corner_width:
                self.minor_corner_width = self.corner_width
            if self.minor_corner_bevel_segments != self.corner_bevel_segments:
                self.minor_corner_bevel_segments = self.corner_bevel_segments
            if self.minor_corner_outer_bevel_type != self.corner_outer_bevel_type:
                self.minor_corner_outer_bevel_type = self.corner_outer_bevel_type
        update_prop(self, context)
        return None

    corner_width : FloatProperty(
            name="Main Corner Width",
            description="Bevel width of corners",
            min=0.000,
            default=0.0,
            precision=3,
            step=1,
            update=update_corner
            )

    corner_bevel_segments : IntProperty(
            name="Main Corner Bevel Segments",
            description="How bevelled are the corners of the selection",
            min=1,
            default=1,
            update=update_corner  
            )

    corner_outer_bevel_type : bpy.props.EnumProperty(items= (('OFFSET', 'Offset', ''),
                                                     ('WIDTH', 'Width', ''),
                                                     ('DEPTH', 'Depth', ''),
                                                     ('PERCENT', 'Percent', '')),
                                                     name = "Major Corner Bevel Type", default='OFFSET', update=update_corner)


    def update_minor_corner(self, context):
        if self.sync_corners:
            if self.minor_corner_width != self.corner_width:
                self.corner_width = self.minor_corner_width
            if self.minor_corner_bevel_segments != self.corner_bevel_segments:
                self.corner_bevel_segments = self.minor_corner_bevel_segments
            if self.minor_corner_outer_bevel_type != self.corner_outer_bevel_type:
                self.corner_outer_bevel_type = self.minor_corner_outer_bevel_type
        update_prop(self, context)
        return None


    minor_corner_width : FloatProperty(
            name="Minor Corner Width",
            description="Bevel width of corners",
            min=0.000,
            default=0.0,
            precision=3,
            step=1,
            update=update_minor_corner
            )

    minor_corner_bevel_segments : IntProperty(
            name="Minor Corner Bevel Segments",
            description="How bevelled are the corners of the selection",
            min=1,
            default=1,
            update=update_minor_corner
            )

    minor_corner_outer_bevel_type : bpy.props.EnumProperty(items= (('OFFSET', 'Offset', ''),
                                                     ('WIDTH', 'Width', ''),
                                                     ('DEPTH', 'Depth', ''),
                                                     ('PERCENT', 'Percent', '')),
                                                     name = "Minor Corner Bevel Type", default='OFFSET', update=update_minor_corner)

    use_rivets : BoolProperty(
            name="Use Rivets",
            description="Whether to add rivet shapes to the plates",
            default=False,
            update=update_prop
            )

    rivet_corner_distance : FloatProperty(
            name="Distance from Corner",
            description="distance of rivets from corners",
            min=0.000,
            default=0.05,
            precision=3,
            step=1,
            update=update_prop
            )

    rivet_diameter : FloatProperty(
            name="Diameter",
            description="Diameter of rivets",
            min=0.000,
            default=0.01,
            precision=3,
            step=1,
            update=update_prop
            )

    rivet_subdivisions : IntProperty(
            name="Subdivisions",
            description="rivet sphere subdivisions",
            min=1,
            max=8,
            default=1,
            update=update_prop
            )

    rivet_material_index : IntProperty(
            name="Material Index",
            description="rivet material index slot",
            default=-1,
            update=update_prop
            )

    groove_material : StringProperty(
            name="Groove Material",
            description="A material for the grooves",
            update=update_prop
    )

    def update_materials(self, context):
        if (self.no_plating_materials > len(self.plating_materials)):
            for i in range(self.no_plating_materials):
                self.plating_materials.add()
        if (self.no_plating_materials < len(self.plating_materials)):
            for i in range(self.no_plating_materials, len(self.plating_materials)):
                self.plating_materials.remove(i)
        update_prop(self, context)
        return None

    no_plating_materials : IntProperty(
            name="No Plating Materials",
            description="number of materials to apply to plates",
            min=0,
            default=0,
            update=update_materials
            )

    plating_materials : bpy.props.CollectionProperty(
        type=PlatingGeneratorMaterial
    )

    plating_materials_random_seed : IntProperty(
        name="Plating Random Seed",
        description="Seed for assigning plating materials",
        default=123456,
        update=update_prop
        )

    add_vertex_colors_to_plates : BoolProperty(
            name="Add Random Vertex Colors",
            description="Add random vertex coloring to the plates",
            default=False,
            update=update_prop
            )

    vertex_colors_random_seed : IntProperty(
        name="Vertex Color Random Seed",
        description="Seed for assigning vertex colors",
        default=123456,
        update=update_prop
        )

    vertex_colors_layer_name : StringProperty(
        name="Vertex Color Layer Name",
        description="Name of vertex color layer",
        default="plating_color",
        update=update_prop
        )

    #cosmetics
    update_draw_only : BoolProperty(default=False, options={'SKIP_SAVE'})
    def update_draw(self, context):
        self.update_draw_only = True

    show_plating_pattern_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_grooves_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_plates_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_corners_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_selection_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_materials_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_rivets_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_other_options_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})


class PlatingGeneratorMaterialPropertyGroup(bpy.types.PropertyGroup):
    """A class representing the properties of a material."""
    is_property_group : BoolProperty(default=True)
    name : bpy.props.StringProperty(name="Name", default="", update=update_mat_prop)


class PlatingGeneratorPropsPropertyGroup(PlatingGeneratorProps, bpy.types.PropertyGroup):
    is_property_group : BoolProperty(default=True)

    plating_materials : bpy.props.CollectionProperty(
        type=PlatingGeneratorMaterialPropertyGroup
    )

