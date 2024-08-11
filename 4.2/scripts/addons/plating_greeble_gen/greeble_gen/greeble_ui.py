from .. import preferences
from . import greeble_props
import re

# draw out a custom interface as there are a lot of properties.
def draw(self, context, layout):

    pref = preferences.preference()

    col = layout.column()
    #col.row().separator()

    #Greebles!
    box = col.box()
    row = box.row()

    row.prop(self, "show_greeble_pattern_panel",
        icon="TRIA_DOWN" if self.show_greeble_pattern_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Greeble Pattern")

    if self.show_greeble_pattern_panel:
        greeble_pattern_panel = box.column()

        row = greeble_pattern_panel.row()
        split = row.split(factor=0.4)
        split.label(text="Pattern Type: ")
        split.prop_menu_enum(self, "greeble_pattern_type", 
                                                text=greeble_props.greeble_pattern_type_items[int(getattr(self, "greeble_pattern_type"))][1])
        
        greeble_opts_panel = greeble_pattern_panel.column()
        greeble_opts_panel.prop(self, "greeble_random_seed")
        if self.greeble_pattern_type == '0':
            greeble_opts_panel.prop(self, "greeble_amount")
        elif self.greeble_pattern_type == '1':
            greeble_opts_panel.prop(self, "coverage_amount")
            greeble_opts_panel.prop(self, "greeble_subd_levels")
            greeble_opts_panel.prop(self, "greeble_deviation")


    box = col.box()
    row = box.row()
    row.prop(self, "show_greeble_parameters_panel",
        icon="TRIA_DOWN" if self.show_greeble_parameters_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="General Parameters")
    if self.show_greeble_parameters_panel:
        greeble_parameters_panel = box.column()
        greeble_parameters_panel.label(text="Relative dimensions")
        greeble_parameters_panel.prop(self, "greeble_min_width", text="Min Width")
        greeble_parameters_panel.prop(self, "greeble_max_width", text="Max Width")
        greeble_parameters_panel.prop(self, "greeble_min_length", text="Min Length")
        greeble_parameters_panel.prop(self, "greeble_max_length", text="Max Length")
        greeble_parameters_panel.prop(self, "greeble_min_height", text="Min Height")
        greeble_parameters_panel.prop(self, "greeble_max_height", text="Max Height")

        greeble_parameters_panel.label(text="Random Vertex Colors")
        # greeble_parameters_panel.prop(self, "add_vertex_colors_to_greebles", text="Add Random Vertex Colors")

        materials_vertex_colors_panel = greeble_parameters_panel.column()
        materials_vertex_colors_panel.prop(self, "add_vertex_colors_to_greebles")
        materials_vertex_colors_panel_seed = greeble_parameters_panel.column()
        materials_vertex_colors_panel_seed.enabled = self.add_vertex_colors_to_greebles
        materials_vertex_colors_panel_seed.prop(self, "vertex_colors_random_seed")
        materials_vertex_colors_panel_seed.prop(self, "vertex_colors_layer_name", text="Layer")
        

    box = col.box()
    row = box.row()
    row.prop(self, "show_default_greebles_panel",
        icon="TRIA_DOWN" if self.show_default_greebles_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Greeble Objects from Library")
    if self.show_default_greebles_panel:

        default_greebles_panel = box.column()

        col1 = default_greebles_panel.column()

        row1 = col1.row(align=True)
        row1.prop(self, "category_to_add_remove", text="")
        row1.prop(self, 'add_greeble_lib', icon="ADD", icon_only=True, emboss=True)
        row1.prop(self, "add_greebles_from_lib", icon="IMPORT",  icon_only=True, emboss=True)
        row1.prop(self, "remove_greebles_from_lib",  icon="EXPORT", icon_only=True, emboss=True)
        

        default_greebles_panel = default_greebles_panel = box.column(align=True)

        if len(self.library_greebles):
            row1 = default_greebles_panel.row(align=True)
            row1.alignment="RIGHT"
            row1.prop(self, "all_keep_aspect_ratio", icon="MOD_EDGESPLIT", icon_only=True)
            row1.prop(self, "all_override_materials", icon="MATERIAL", icon_only=True)
            row1.prop(self, "all_override_height", icon="EMPTY_SINGLE_ARROW", icon_only=True)
            row1.prop(self, 'clear_greeble_lib', icon="CANCEL", icon_only=True, emboss=True)

        default_greebles_panel_box = default_greebles_panel.box()

        for default_greeble in self.library_greebles:

            box1 = default_greebles_panel_box.box()

            rowA = box1.row()
            
            rowA.template_icon_view(default_greeble, 'thumbnail', show_labels=False, scale=2)

            col1 = rowA.column()
            
            row1 = col1.row(align=True)
            row1.alignment = 'EXPAND'
            row1.prop(default_greeble, 'category', text="")
            row1.prop(default_greeble, "keep_aspect_ratio", icon="MOD_EDGESPLIT", icon_only=True)
            row1.prop(default_greeble, "override_materials", icon="MATERIAL", icon_only=True)
            row1.prop(default_greeble, "override_height", icon="EMPTY_SINGLE_ARROW", icon_only=True)
            row1.prop(default_greeble, 'remove_greeble', icon="CANCEL", icon_only=True, emboss=True)

            col3 = col1.column(align=True)
            col3.prop(default_greeble, "coverage", text="Coverage")

            if default_greeble.override_materials:
                col3.prop(default_greeble, "material_index")
            if default_greeble.override_height:
                col3.prop(default_greeble, "height_override")

            default_greebles_panel_box.separator()
        
        
    box = col.box()
    row = box.row()
    row.prop(self, "show_custom_greebles_panel",
        icon="TRIA_DOWN" if self.show_custom_greebles_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Greeble Objects from Scene")
    if self.show_custom_greebles_panel:
        default_greebles_panel1 = box.column()
        col1 = default_greebles_panel1.row(align=True)
        col1.prop(self, 'add_greeble_cust', icon="ADD", text='Add', icon_only=False, emboss=True)

        default_greebles_panel = box.column(align=True)

        if len(self.custom_greebles):
            row1 = default_greebles_panel.row(align=True)
            row1.alignment="RIGHT"
            row1.prop(self, "all_custom_keep_aspect_ratio", icon="MOD_EDGESPLIT", icon_only=True)
            row1.prop(self, "all_custom_override_materials", icon="MATERIAL", icon_only=True)
            row1.prop(self, "all_custom_override_height", icon="EMPTY_SINGLE_ARROW", icon_only=True)
            row1.prop(self, 'clear_greeble_cust', icon="CANCEL", icon_only=True, emboss=True)

        for default_greeble in self.custom_greebles:
            
            box1 = default_greebles_panel.box()
            col1 = box1.column()
            
            row1 = col1.row(align=True)

            row1.alignment = 'EXPAND'
            if not self.is_property_group:
                row1.prop_search(data = default_greeble,
                                property = "scene_ref",
                                search_data = self,
                                search_property = 'scene_objects',
                                text = '')
            else:
               row1.prop(default_greeble, 'scene_object', text='') 
            row1.prop(default_greeble, "keep_aspect_ratio", icon="MOD_EDGESPLIT", icon_only=True)
            row1.prop(default_greeble, "override_materials", icon="MATERIAL", icon_only=True)
            row1.prop(default_greeble, "override_height", icon="EMPTY_SINGLE_ARROW", icon_only=True)
            row1.prop(default_greeble, 'remove_greeble', icon="CANCEL", icon_only=True, emboss=True)

            col3 = col1.column(align=True)
            col3.prop(default_greeble, "coverage", text="Coverage")

            if default_greeble.override_materials:
                col3.prop(default_greeble, "material_index")
            if default_greeble.override_height:
                col3.prop(default_greeble, "height_override")

            default_greebles_panel.separator()

    box = col.box()
    row = box.row()

    row.prop(self, "show_greeble_orientation_panel",
        icon="TRIA_DOWN" if self.show_greeble_orientation_panel else "TRIA_RIGHT",
        icon_only=True, emboss=False
    )
    row.label(text="Greeble Orientation")

    if self.show_greeble_orientation_panel:
        greeble_orientation_panel = box.column()
        greeble_orientation_panel.prop(self, "is_custom_normal_direction")
        greeble_orientation_normal_panel = greeble_orientation_panel.column()
        greeble_orientation_normal_panel.enabled = self.is_custom_normal_direction
        greeble_orientation_normal_panel.prop(self, "custom_normal_direction")
        greeble_rotate_seed_panel = greeble_orientation_panel.column()
        greeble_rotate_seed_panel.label(text="Rotation")
        greeble_rotate_seed_panel.enabled = not self.is_custom_rotation
        greeble_rotate_seed_panel.prop(self, 'greeble_rotation_seed')
        greeble_orientation_panel.prop(self, "is_custom_rotation")
        greeble_custom_rotate_panel = greeble_orientation_panel.column()
        greeble_custom_rotate_panel.enabled = self.is_custom_rotation
        greeble_custom_rotate_panel.prop(self, "custom_rotate_amount")
