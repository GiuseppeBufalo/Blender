import bpy

from bpy.types import PropertyGroup


class CSDF_Meshing_Props(PropertyGroup):

    triangle_density : bpy.props.FloatProperty(
        name="Density",
        description="Triangles per Meter",
        default=100,
        min=0.1,
        soft_max=500
    )

    last_chunk_count : bpy.props.IntProperty(
        name="last chunk count",
        description="Number of chunks on last meshing operation",
        default=1,
    )

    last_chunk_time : bpy.props.FloatProperty(
        name="last chunk time",
        description="Time it took to perform last meshing operation, in seconds",
        default=0.0,
        precision=3,
    )
