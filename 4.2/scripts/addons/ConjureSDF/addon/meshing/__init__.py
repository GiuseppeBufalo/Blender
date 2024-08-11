import bpy

from .install import CSDF_OT_INSTALL_MODERNGL

from .main import CSDF_OT_SDF_TO_MESH
from .operator import CSDF_OT_ADDBOUNDS, CSDF_OT_CLEANMESH

from .settings import CSDF_Meshing_Props

from .panels import CSDF_PT_MESHING

# Classes to (un)register as part of this addon
classes = (
    CSDF_OT_INSTALL_MODERNGL,

    CSDF_OT_SDF_TO_MESH,
    CSDF_OT_ADDBOUNDS, CSDF_OT_CLEANMESH,
    
    CSDF_Meshing_Props,

    CSDF_PT_MESHING,
)

def register_meshing():
    """Register panels, operators, and the render engine itself"""
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.csdf_meshingprops = bpy.props.PointerProperty(type=CSDF_Meshing_Props)


def unregister_meshing():
    """Unload everything previously registered"""

    del bpy.types.Scene.csdf_meshingprops

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
