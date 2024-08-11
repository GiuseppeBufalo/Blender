import bpy
from . import plating_generator
from . import plating_props


def get_pattern_type_name(pattern_type):
    for prop in plating_props.pattern_type_props: 
        if prop[0] == pattern_type:
            return prop[1]

# draw out a custom interface as there are a lot of properties.
def draw(self, context, layout):
    col = layout.column()

    box = col.box()
    row = box.row()
    row.prop(self, "show_plating_pattern_panel",
        icon="TRIA_DOWN" if self.show_plating_pattern_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Plating Pattern")

    if self.show_plating_pattern_panel:
        plates_panel = box.column()
        plates_panel.label(text="Pattern Type:")
        plates_panel.prop_menu_enum(self, "pattern_type", text=get_pattern_type_name(self.pattern_type))
        plates_panel.separator()
        plates_opts_panel = plates_panel.column()
        if self.pattern_type == '1':
            plates_opts_panel.enabled = False
        elif self.pattern_type == '0':
            plates_opts_panel.prop(self, "random_seed")
            plates_opts_panel.prop(self, "amount")
            plates_opts_panel.prop(self, "pre_subdivisions")
        elif self.pattern_type == '2':
            plates_opts_panel.prop(self, "random_seed")
            plates_opts_panel.prop(self, "amount")
            plates_opts_panel.prop(self, "pre_subdivisions")
            plates_opts_panel.label(text="Triangles")
            plates_opts_panel.prop(self, "triangle_random_seed", text="Triangles Random Seed")
            plates_opts_panel.prop(self, "triangle_percentage", text="Amount of triangles")
        elif self.pattern_type == '3':
            plates_opts_panel.prop(self, "rectangle_random_seed")
            plates_opts_panel.prop(self, "rectangle_amount", text="Rectangle Amount")
            plates_opts_panel.prop(self, "rectangle_width_min", text="Rectangle Width Min")
            plates_opts_panel.prop(self, "rectangle_width_max", text="Rectangle Width Max")
            plates_opts_panel.prop(self, "rectangle_height_min", text="Rectangle Height Min")
            plates_opts_panel.prop(self, "rectangle_height_max", text="Rectangle Height Max")
            plates_opts_panel.prop(self, "pre_subdivisions")
        elif self.pattern_type == '4':
            
            plates_opts_panel.prop(self, "rectangle_random_seed")
            plates_opts_panel.prop(self, "rectangle_amount", text="Rectangle Amount")
            plates_opts_panel.prop(self, "rectangle_width_min", text="Rectangle Width Min")
            plates_opts_panel.prop(self, "rectangle_width_max", text="Rectangle Width Max")
            plates_opts_panel.prop(self, "rectangle_height_min", text="Rectangle Height Min")
            plates_opts_panel.prop(self, "rectangle_height_max", text="Rectangle Height Max")
            plates_opts_panel.separator()
            plates_opts_panel.prop(self, "random_seed", text="Slices random seed")
            plates_opts_panel.prop(self, "amount", text="Slices Amount")
            plates_opts_panel.separator()
            plates_opts_panel.prop(self, "triangle_random_seed", text="Triangles Random Seed")
            plates_opts_panel.prop(self, "triangle_percentage", text="Amount of triangles in slice")
            plates_opts_panel.separator()
            plates_opts_panel.prop(self, "pre_subdivisions")
        elif self.pattern_type == '6':
            plates_opts_panel.prop(self, "ruby_dragon_random_seed")
            plates_opts_panel.prop(self, "ruby_dragon_percentage")
            plates_opts_panel.prop(self, "pre_subdivisions")
            # plates_opts_panel.prop(self, "triangle_random_seed", text="Triangles Random Seed")
            # plates_opts_panel.prop(self, "triangle_percentage", text="Amount of triangles")


        plates_opts_panel.separator()
        plates_opts_panel.prop(self, 'cut_at_faces')
        angle_limit_row = plates_opts_panel.row(align=True)
        angle_limit_row.enabled = self.cut_at_faces
        split = angle_limit_row.split(factor=0.8, align=True)
        split.prop(self, 'face_angle_limit')
        split.prop(self, 'face_angle_dev', text="+/-")
        
            
    box = col.box()
    row = box.row()
    row.prop(self, "show_plates_panel",
        icon="TRIA_DOWN" if self.show_plates_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Plates")
    if self.show_plates_panel:
        plate_taper_panel = box.column()
        plate_taper_panel.label(text="Plate Taper")
        plate_taper_panel.prop(self, "plate_taper", text="Amount")

        plate_heights_panel = box.column()
        plate_heights_panel.label(text="Plate Heights")
        
        plate_heights_panel.prop(self, "sync_heights", text="Match Heights")
        plate_heights_panel.prop(self, "plate_min_height", text="Min Height")
        plate_heights_panel_var = plate_heights_panel.column()
        plate_heights_panel_var.enabled = not self.sync_heights
        plate_heights_panel_var.prop(self, "plate_max_height", text="Max Height")
        plate_heights_panel_var.prop(self, "plate_height_random_seed", text="Random Seed")

        plate_bevel_panel = box.column()
        plate_bevel_panel.label(text="Plate Bevel")
        plate_bevel_panel.prop(self, "bevel_amount", text="Amount")
        plate_bevel_panel.prop(self, "bevel_segments", text="Segments")
        plate_bevel_panel.prop_menu_enum(self, "bevel_outer_bevel_type")

    box = col.box()
    row = box.row()
    row.prop(self, "show_grooves_panel",
        icon="TRIA_DOWN" if self.show_grooves_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Grooves")
    if self.show_grooves_panel:
        grooves_panel = box.column()
        grooves_panel.prop(self, "clamp_grooves")
        grooves_panel.prop(self, "groove_width", text="Width")
        if not self.remove_grooves:
            grooves_panel.prop(self, "groove_depth", text="Depth")
        if not self.remove_inner_grooves:
            grooves_panel.prop(self, "groove_segments")
        if not self.remove_grooves:
            grooves_panel.prop(self, "side_segments", text="Side Segments")

        if not self.remove_grooves:
            groove_bevel_panel = box.column()
            groove_bevel_panel.label(text="Groove Bevel")
            groove_bevel_panel.prop(self, "groove_bevel_amount", text="Amount")
            groove_bevel_panel.prop(self, "groove_bevel_segments", text="Segments")
            groove_bevel_panel.prop_menu_enum(self, "groove_bevel_outer_bevel_type")

    box = col.box()
    row = box.row()
    row.prop(self, "show_corners_panel",
        icon="TRIA_DOWN" if self.show_corners_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Corners")
    if self.show_corners_panel:
        corners_panel = box.column()


        corners_panel.prop(self, "sync_corners", text="Match Corners")
        corners_panel.label(text="Major Corners")
        corners_panel.prop(self, "corner_width", text="Amount")
        corners_panel.prop(self, "corner_bevel_segments", text="Segments")
        corners_panel.prop_menu_enum(self, "corner_outer_bevel_type")

        corners_panel_var = corners_panel.column()
        corners_panel_var.enabled = not self.sync_corners



        corners_panel_var.label(text="Minor Corners")
        corners_panel_var.prop(self, "minor_corner_width", text="Amount")
        corners_panel_var.prop(self, "minor_corner_bevel_segments", text="Segments")
        corners_panel_var.prop_menu_enum(self, "minor_corner_outer_bevel_type")

    box = col.box()
    row = box.row()
    row.prop(self, "show_rivets_panel",
        icon="TRIA_DOWN" if self.show_rivets_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Rivets")
    if self.show_rivets_panel:
        rivets_panel = box.column()
        rivets_panel.prop(self, "use_rivets")
        rivet_columns = rivets_panel.column()
        rivet_columns.enabled = self.use_rivets
        rivet_columns.prop(self, "rivet_corner_distance")
        rivet_columns.prop(self, "rivet_diameter")
        rivet_columns.prop(self, "rivet_subdivisions")
        rivet_columns.prop(self, "rivet_material_index")

    box = col.box()
    row = box.row()
    row.prop(self, "show_selection_panel",
        icon="TRIA_DOWN" if self.show_selection_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Selection")
    if self.show_selection_panel:
        selection_panel = box.column()
        selection_panel.prop(self, "select_grooves", text="Select Groove Geometry")
        selection_panel.prop(self, "select_plates", text="Select Plate Geometry")


    box = col.box()
    row = box.row()
    row.prop(self, "show_materials_panel",
        icon="TRIA_DOWN" if self.show_materials_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Materials")
    if self.show_materials_panel:
        materials_panel = box.column()

        materials_groove_panel = materials_panel.box()
        materials_groove_panel.label(text="Groove Material:")
        materials_groove_panel.prop_search(self, "groove_material", bpy.data, "materials", text="")

        materials_plating_panel = materials_panel.box()
        materials_plating_panel.label(text="Plating Materials:")
        materials_plating_panel.prop(self, "no_plating_materials", text="No. of Plating Materials" )


        i=0
        for plating_material in self.plating_materials:
            materials_plating_panel.prop_search(plating_material, "name", bpy.data, "materials", text=str(i))
            i+=1

        if self.no_plating_materials > 0:
            materials_plating_panel.prop(self, "plating_materials_random_seed")


        materials_panel.separator()

        materials_vertex_colors_panel = materials_plating_panel.column()
        materials_vertex_colors_panel.prop(self, "add_vertex_colors_to_plates")
        materials_vertex_colors_panel_seed = materials_plating_panel.column()
        materials_vertex_colors_panel_seed.enabled = self.add_vertex_colors_to_plates
        materials_vertex_colors_panel_seed.prop(self, "vertex_colors_random_seed")
        materials_vertex_colors_panel_seed.prop(self, "vertex_colors_layer_name", text="Layer")

    box = col.box()
    row = box.row()
    row.prop(self, "show_other_options_panel",
        icon="TRIA_DOWN" if self.show_other_options_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Other Options")
    if self.show_other_options_panel:
        other_options_panel = box.column()
        other_options_panel.prop(self, "mark_seams")
        other_options_panel.prop(self, "edge_split")
        other_options_panel.prop(self, "remove_grooves")
        # if self.__class__.__name__ == 'MESH_OT_PlateGeneratorCreateNewOperator':
        other_options_panel.prop(self, "remove_inner_grooves")
        other_options_panel.prop(self, "edge_selection_only")
