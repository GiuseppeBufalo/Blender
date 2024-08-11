import bpy

from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, FloatProperty, IntProperty, CollectionProperty, BoolProperty, BoolVectorProperty

import os.path

from ..engine.sdf.builder import PRIMITIVE_NON_ROUNDED
from ..util.data.nodegroups import append_geo_node_tree
from ..util.addon import get_prefs
from ..util.object import get_selected_active
from ..util.csdf_primitives import generate_csdf_prim_ID, add_csdf_scene_node

from ..resources import iconloader


geo_nodes_path = os.path.join('resources', 'blend', 'CSDF_Primitives.blend')


def change_primitive(self, value):

    prefs = get_prefs()

    context = value
    ob = context.active_object

    # https://blenderartists.org/t/how-to-remove-a-modifier-in-2-8/1213998

    if len(ob.modifiers) == 0:
        return

    gn_mod = ob.modifiers[0]
    ob.modifiers.remove(gn_mod)

    # change geometry node tree used
    node_tree = "CSDF_" + self.primitive_type

    success = append_geo_node_tree(ob, geo_nodes_path, node_tree)
    if not success:
        self.report({'WARNING'}, "geonode tree not found")

    gn_mod = ob.modifiers[0]
    gn_mod["Input_2"] = ob

    if not prefs.prims.keep_scale:
        primitive_defaults(ob, self.primitive_type)


    # doesn't work for certain non default names like box.apples.001 (but who names their objects like that??)
    prim_names = [item[0] for item in PRIMITIVE_ENUM_LIST]
    if ob.name.split(".")[0] in prim_names:
        prim_name = get_available_name(self.primitive_type)
        ob.name = prim_name

    recompile_shader(self, value)

def change_operation(self, value):

    context = value
    settings = context.scene.csdf
    selection = context.selected_objects
    csdf_scene_nodes = context.scene.CSDF_SceneNodes

    # to support multiple objects and holding alt to change properties on all in one go
    if settings.draw_wire:
        for obj in selection:
            if obj.get('csdfData'):
                op_type = obj.csdfData.operation_type

                new_display_type = 'BOUNDS'

                if op_type == 'Union':
                    new_display_type = 'TEXTURED'

                obj_node = [node for node in csdf_scene_nodes if node.obj == obj][0]

                update_display_recursively(csdf_scene_nodes, obj_node, new_display_type)


    # has to be run after update_display_recursively
    # as it will set set union prims to textured, without regard for its parents being non union at any point

    from ..engine.viewport.overlays import update_wire_displace_recursively
    root_node = csdf_scene_nodes[0]
    wire_draw_enable = settings.draw_wire
    
    display_options = ('TEXTURED', 'BOUNDS')
    new_display_type = display_options[int(wire_draw_enable)]
    update_wire_displace_recursively(csdf_scene_nodes, root_node, new_display_type, False)


    recompile_shader(self, value)


def update_display_recursively(csdf_scene_nodes, node, new_display_type):

    # if we're switching to bounds, everything should switch
    # if we're switching to textured, only unions should switch

    if new_display_type == 'BOUNDS':
        node.obj.display_type = new_display_type
    elif node.obj.csdfData.operation_type == 'Union':
        node.obj.display_type = new_display_type

    if node.childCount:
        child_nodes = [csdf_scene_nodes[childidx.idx] for childidx in node.childIndices]

        for child_node in child_nodes:
            update_display_recursively(csdf_scene_nodes, child_node, new_display_type)


def recompile_shader(self, value):
    settings = bpy.context.scene.csdf
    settings.force_reload = True



PRIMITIVE_ENUM_LIST = [
                    ('Box', "Cube", "", iconloader.id('sdf_Box'), 0),
                    ('Sphere', "Sphere", "", iconloader.id('sdf_Sphere'), 1), #
                    ('Cylinder', "Cylinder", "", iconloader.id('sdf_Cylinder'), 2),
                    ('Link', "Link", "", iconloader.id('sdf_Link'), 3),
                    ('Torus', "Torus", "", iconloader.id('sdf_Torus'), 4),

                    ('HexPrism', "Hexagon", "", iconloader.id('sdf_HexPrism'), 5),
                    ('Coin', "Coin", "", iconloader.id('sdf_Coin'), 6),
                    ('CapCone', "Capped Cone", "", iconloader.id('sdf_CapCone'), 7),
                    ('Ellipsoid', "Ellipsoid", "", iconloader.id('sdf_Ellipsoid'), 8), #
                    ('LongCylinder', "Elongated Cylinder", "", iconloader.id('sdf_LongCylinder'), 9),
                    ('BiCapsule', "BiCapsule", "", iconloader.id('sdf_BiCapsule'), 10),
                    ('Capsule', "Capsule", "", iconloader.id('sdf_Capsule'), 11),
                    ]



# for custom icons, the unique identifier is also needed
OP_TYPES = [
            ('Union', "Union", "Union", iconloader.id('sdf_union'), 0),
            ('Diff', "Difference", "Difference", iconloader.id('sdf_difference'), 1),
            ('Inters', "Intersect", "Intersect", iconloader.id('sdf_intersect'), 2),
            ('Inset', "Inset", "Inset", iconloader.id('sdf_inset'), 3)
            ]


OP_BLEND_TYPES = [
                ('n', "None", "None", iconloader.id('sdf_blend_none'), 0),
                ('s', "Smooth", "Smooth", iconloader.id('sdf_blend_smooth'), 1),
                ('c', "Chamfered", "Chamfered", iconloader.id('sdf_blend_chamfered'), 2),
                ('ir', "Inverted Round", "Inverted Round", iconloader.id('sdf_blend_inverted_round'), 3),
                ]



class csdfData(bpy.types.PropertyGroup):

    ID : IntProperty(
        name="Identifier",
        description="Unique integer between 0 and 9999",
        default=-1
    )

    is_csdf_prim : BoolProperty(
        name="is csdf prim",
        description="is a CSDF object",
        default=False
    )

    is_root : BoolProperty(
        name="is root",
        description="is the root of an SDF object",
        default=False
    )

    rounding : FloatProperty(
        name="Rounding",
        description="",
        default=0.0,
        min=0.0,
        soft_min=0.0,
        soft_max=1,
        unit='NONE',
        # update=none
    )

    parm01 : FloatProperty(
        name="Parameter 01",
        description="additional parameter",
        default=0.0,
        min=0.0,
        soft_min=0.0,
        soft_max=1,
        unit='NONE',
        # update=none    
    )

    primitive_type : EnumProperty(name="Operation Type", 
                    items=PRIMITIVE_ENUM_LIST, 
                    update=change_primitive
    )

    is_rounded : BoolProperty(name="Rounded",
                                description="Is a rounded SDF",
                                default=False,
                                update=recompile_shader
                                )

    operation_type: EnumProperty(name="Operation Type", 
                    items=OP_TYPES, 
                    default="Union",
                    update=change_operation
                    )

    operation_blend: EnumProperty(name="Blending", 
                    items=OP_BLEND_TYPES, 
                    default="s",
                    update=recompile_shader
                    )

    operation_strength: FloatProperty(name="Operation Strength",
                        description="How big the influence of the operation type is",
                        default=0.1,
                        soft_min = 0,
                        soft_max = 5)
    
    mirror_world: BoolVectorProperty(name="World Mirroring",
                                     description="Mirror the SDF around the world origin in X Y or Z",
                                     size=3,
                                     default=(False, False, False),
                                     subtype='XYZ',
                                     update=recompile_shader
                                     )
    
    mirror_smooth: BoolProperty(name="smooth mirror",
                                description="smooths the area around the mirror plane",
                                default=False,
                                update=recompile_shader
                                )

    mirror_smooth_strength: FloatProperty(name="smooth mirroring strength",
                                          description="how large the smoothing area is around the mirror plane",
                                          default=0.05,
                                          min=0.0)

    mirror_flips: BoolVectorProperty(name="Flip direction",
                                     description="Mirror from - to + instead of from + to -",
                                     size=3,
                                     default=(False, False, False),
                                     subtype='XYZ',
                                     update=recompile_shader
                                     )

    ignore_mirror: BoolProperty(name="Ignore Mirror",
                                description="Primitive is not affected by root mirror settings",
                                default=False,
                                update=recompile_shader
                                )

    solidify: BoolProperty(name="solidify",
                                description="Makes the primitive hollow",
                                default=False,
                                update=recompile_shader
                                )

    solidify_strength: FloatProperty(name="solidify thickness",
                                          description="Thickness of the surface",
                                          default=0.05,
                                          min=0.0)
    
    show_viewport: BoolProperty(name="Show in Viewport",
                                description="Displays the primitive if toggled on",
                                default=True,
                                update=recompile_shader
                                )


def primitive_defaults(newprim, primtype):

    newprim.scale[0] = 1.0
    newprim.scale[1] = 1.0
    newprim.scale[2] = 1.0

    if primtype in ('Link', 'Coin'):
        newprim.scale[2] = 0.2
    if primtype in ('Torus'):
        newprim.scale[2] = 0.25
    if primtype in ('CapCone', 'LongCylinder', ):
        newprim.scale[1] = 0.5
        # csdfData.parm02 = 0.5
    if primtype in ('BiCapsule'):
        newprim.scale[0] = 0.4
        newprim.scale[1] = 0.2
    if primtype in ('Ellipsoid'):
        newprim.scale[1] = 0.8
        newprim.scale[2] = 0.6        


class CSDF_OT_ADD_PRIM(Operator):
    """Add CSDF primitive. \nprimitive is added under active object. \nNo active object adds primitive to root level"""
    bl_idname = "mesh.csdf_addprim"
    bl_label = "CSDF"
    bl_options = {'UNDO', 'REGISTER'}


    prim: EnumProperty(name="Primitive", 
                    items=PRIMITIVE_ENUM_LIST, 
                    default="Sphere")

    op: EnumProperty(name="Operation Type", 
                    items=OP_TYPES, 
                    default="Union"
                    )

    op_blend: EnumProperty(name="Blending", 
                    items=OP_BLEND_TYPES, 
                    default="s",
                    )
    
    rounded: BoolProperty(name="Rounded",
                           description="Creates Rounded SDF if available",
                           default=True
                           )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.active_object.csdfData.is_csdf_prim:
                return True
        if bpy.context.scene.objects.get("CSDF Root"): 
            return True

    def execute(self, context):

        SDF_Coll = bpy.data.collections.get("CSDF Primitives")

        settings = context.scene.csdf
        settings.block_selection_handler = True
        
        # getting data this early to avoid getting the object created in this function with ID of -1
        existing_IDs = [obj.csdfData.ID for obj in context.scene.objects if obj.csdfData.is_csdf_prim]

        # if an object is selected and active, it's the CSDF parent
        # TODO : check if parent is a CSDF object. If not how to handle? poll function, error message? idk
        csdf_parent = get_selected_active(bpy.context)

        # if an object active but not selected, or there is no active/selected object at all
        # assume prim is added to the scene root
        if not csdf_parent:
            csdf_parent = bpy.context.scene.objects["CSDF Root"]
        

        loc = bpy.context.scene.cursor.location
        bpy.ops.mesh.primitive_cube_add(size=2, align='WORLD', location= loc)

        newprim = bpy.context.active_object
        csdfData = newprim.csdfData

        for col in newprim.users_collection:
            col.objects.unlink(newprim)

        # don't need to check if it exists, as prims can only be added once a root has been added (which creates this collection)
        # and if it does error, better to know it
        SDF_Coll.objects.link(newprim)
        context.view_layer.objects.active = newprim

        csdfData.rounding = 0.05
        csdfData.primitive_type = self.prim
        
        if self.rounded:
            csdfData.is_rounded = True

        

        csdfData.operation_type = self.op
        csdfData.operation_blend = self.op_blend
        csdfData.operation_strength = .05

        

        primitive_defaults(newprim, self.prim)

        # mark object as CSDF object, this is used for object filtering during shader compilation
        newprim['CSDF_obj'] = True
        # New way
        csdfData.is_csdf_prim = True

        prim_name = get_available_name(self.prim)
        newprim.name = prim_name

        # TODO : parenting should be the way to go
        # but due to scaling being used for parameters this is not an option atm
        # reimplement this after active tool and prim data redesign

        # newprim.parent = csdf_parent
        # use this instead so primitives aren't scaled relative to their parents
        # constraint_child_of = newprim.constraints.new(type='CHILD_OF')
        # constraint_child_of.use_scale_x = False
        # constraint_child_of.use_scale_y = False
        # constraint_child_of.use_scale_z = False
        # constraint_child_of.target = csdf_parent

        random_ID = generate_csdf_prim_ID(existing_IDs)
        csdfData.ID = random_ID

        add_csdf_scene_node(newprim, csdf_parent, context)

        settings = context.scene.csdf

        if settings.draw_wire and self.op in ('Diff', 'Inset', 'Inters'):
            newprim.display_type = 'BOUNDS'


        # WARNING : NEEDS TO BE DONE AT THE END
        # ELSE DEPSGRAPH UPDATES GET MESSED UP

        # if self.prim in ('Link', 'HexPrism', 'CapCone', 'LongCylinder', 'BiCapsule'):

        node_tree = "CSDF_" + self.prim
        
        success = append_geo_node_tree(newprim, geo_nodes_path, node_tree)
        if not success:
            self.report({'WARNING'}, "geonode tree not found")

        gn_mod = newprim.modifiers[0]
        gn_mod["Input_2"] = newprim

        # from ..util.data.drivers import add_driver
        # gn_mod = newprim.modifiers[0]

        # add_driver(gn_mod, "Input_2", gn_mod, "scale[0]")
        # gn_mod["Input_1"]

        # TODO : should this be a setting? to make it easier to add multiple objects
        # newprim.select_set(False)
        # csdf_parent.select_set(True)
        # context.view_layer.objects.active = csdf_parent

        return {'FINISHED'}



def get_available_name(name):

    i = 0

    while True:
        suffix = "." + str(i).zfill(3)

        prim_name = name+suffix

        if not bpy.data.objects.get(prim_name):
            return prim_name
        else:
            i += 1
