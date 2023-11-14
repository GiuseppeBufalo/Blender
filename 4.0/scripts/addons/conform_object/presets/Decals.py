import bpy
op = bpy.context.active_operator

op.make_copy = False
op.collapse_modifiers = False
op.falloff = 4.0
op.vertical_subdivisions = 20
op.source_object_offset = 0.0
op.hide_grid = True
op.grid_transform_x = 0.0
op.grid_transform_y = 0.0
op.grid_transform_z = 0.0
op.grid_size_x = 1.0
op.grid_rotation = 0.0
op.grid_size_y = 1.0
op.parent_grid_to_source = True
op.place_mod_at_start = False
op.is_graduated = False
op.gradient_end = 1.0
op.is_blend_normals = False
op.blend_gradient_end = 1.0
op.is_blend_whole_obj = False
op.add_subsurf_simple = True
op.subsurf_divisions = 1
