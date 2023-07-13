import bpy
op = bpy.context.active_operator

op.pattern_type = '0'
op.random_seed = 123456
op.pre_subdivisions = 0
op.amount = 50
op.rectangle_random_seed = 123456
op.rectangle_amount = 10
op.rectangle_width_min = 1
op.rectangle_width_max = 10
op.rectangle_height_min = 3
op.rectangle_height_max = 7
op.triangle_random_seed = 123456
op.triangle_percentage = 20.0
op.groove_width = 0.009999999776482582
op.clamp_grooves = False
op.groove_depth = 0.009999999776482582
op.groove_segments = 1
op.side_segments = 1
op.bevel_amount = 0.0
op.bevel_segments = 1
op.bevel_outer_bevel_type = 'OFFSET'
op.groove_bevel_amount = 0.0
op.groove_bevel_segments = 1
op.groove_bevel_outer_bevel_type = 'OFFSET'
op.plate_min_height = -0.05100000277161598
op.plate_max_height = 0.1340000033378601
op.plate_height_random_seed = 123456
op.plate_taper = 0.0
op.select_grooves = False
op.select_plates = True
op.mark_seams = False
op.edge_split = False
op.remove_grooves = False
op.remove_inner_grooves = False
op.edge_selection_only = False
op.corner_width = 0.0
op.corner_bevel_segments = 1
op.corner_outer_bevel_type = 'OFFSET'
op.minor_corner_width = 0.0
op.minor_corner_bevel_segments = 1
op.minor_corner_outer_bevel_type = 'OFFSET'
op.use_rivets = False
op.rivet_corner_distance = 0.05000000074505806
op.rivet_diameter = 0.009999999776482582
op.rivet_subdivisions = 1
op.rivet_material_index = -1
op.groove_material = ''
op.no_plating_materials = 0
op.plating_materials.clear()
op.plating_materials_random_seed = 123456
op.add_vertex_colors_to_plates = False
op.vertex_colors_random_seed = 123456
op.vertex_colors_layer_name = 'plating_color'
