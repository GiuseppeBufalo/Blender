import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, EnumProperty, PointerProperty, IntProperty, BoolProperty, FloatProperty
from . utils.objects import get_modifier_with_type


status_items = [
    ("UNDEFINED", "Undefined", "", "NONE", 0),
    ("CSHARP", "CSharp", "", "NONE", 1),
    ("CSTEP", "CStep", "", "NONE", 2),
    ("BOOLSHAPE", "BoolShape", "", "NONE", 3),
    ("BOOLSHAPE2", "BoolShape2", "", "NONE", 4)]

# Array V2
axis_items = [
    ("X", "x", "", "NONE", 0),
    ("Y", "y", "", "NONE", 1),
    ("Z", "z", "", "NONE", 2)]

def active_mod_index(self, context):
    try: # for obsolete blender versions
        obj = self.id_data
        mod = obj.modifiers[self.active_modifier_index]
        obj.modifiers.active = mod
    except:
        pass

class HOpsObjectProperties(PropertyGroup):

    status: EnumProperty(name="Status", default="UNDEFINED", items=status_items)
    adaptivesegments: IntProperty("Adaptive Segments", default=3, min=-10, max=25)

    def pending_boolean(self):
        return get_modifier_with_type(self.id_data, "BOOLEAN") is not None

    is_pending_boolean: BoolProperty(name="Is Pending Boolean", get=pending_boolean)
    is_global: BoolProperty(name="Is Global", description="Auto smooth angle will be overwritten by Csharp/Ssharp operators", default=True)

    array_x: FloatProperty(name="Array gizmo x", description="Array gizmo x", default=0)
    array_y: FloatProperty(name="Array gizmo y", description="Array gizmo y", default=0)
    array_z: FloatProperty(name="Array gizmo z", description="Array gizmo z", default=0)

    last_array_axis: EnumProperty(name="array_axis", default="X", items=axis_items)

    is_poly_debug_display: BoolProperty(name="Poly Debug Display", default=False)
    active_modifier_index: IntProperty(update=active_mod_index)


class HOpsMeshProperties(PropertyGroup):
    hops_undo: BoolProperty(name="Hops Undo System", default=False)


class HOpsNodeProperties(PropertyGroup):
    maps_system: BoolProperty(name="Maps System Group", default=False)
    just_created: BoolProperty(name="Maps System Just Created", default=False)
    roughness_mix: BoolProperty(name="Maps Roughness", default=False)
    color_mix: BoolProperty(name="Maps Roughness", default=False)
    metal_mix: BoolProperty(name="Maps Roughness", default=False)
    viewer: BoolProperty(name="Maps Viewer Node", default=False)


class HOpsImgProperties(PropertyGroup):
    maps_system: BoolProperty(name="Maps System Group", default=False)
    just_created: BoolProperty(name="Maps System Just Created ", default=False)

class HOpsSceneProeprties(PropertyGroup):
    collection: PointerProperty(type=bpy.types.Collection)


classes = (
    HOpsObjectProperties,
    HOpsMeshProperties,
    HOpsNodeProperties,
    HOpsImgProperties,
    HOpsSceneProeprties
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Object.hops = PointerProperty(name="HardOps Properties", type=HOpsObjectProperties)
    bpy.types.Mesh.hops = PointerProperty(name="HardOps Mesh Props", type=HOpsMeshProperties)
    bpy.types.Node.hops = PointerProperty(name="HardOps Node Props", type=HOpsNodeProperties)
    bpy.types.Image.hops = PointerProperty(name="HardOps Node Props", type=HOpsImgProperties)
    bpy.types.Scene.hops = PointerProperty(name="HardOps Scene Props", type=HOpsSceneProeprties)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Object.hops
    del bpy.types.Mesh.hops
    del bpy.types.Node.hops
    del bpy.types.Image.hops
    del bpy.types.Scene.hops

