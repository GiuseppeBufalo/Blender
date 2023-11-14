import bpy
import os
from .. utils.registration import get_prefs, get_path, set_new_decal_index, get_addon, get_addon_prefs
from .. utils.ui import get_icon, draw_pil_warning
from .. utils.atlas import get_lower_and_upper_atlas_resolution, get_textypes_from_atlasmats
from .. utils.material import get_pbrnode_from_mat
from .. utils.library import get_atlas, get_legacy_libs, poll_trimsheetlibs
from .. import bl_info


batchops = None
machin3tools = None



class PanelDECALmachine(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_decal_machine"
    bl_label = "DECALmachine %s" % ('.'.join([str(v) for v in bl_info['version']]))
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 0

    def draw_header(self, context):
        layout = self.layout

        dm = context.scene.DM

        row = layout.row(align=True)
        row.prop(dm, "register_panel_creation", text="", icon="SHADERFX")
        row.prop(dm, "register_panel_export", text="", icon="EXPORT")
        row.prop(dm, "register_panel_update", text="", icon="FILE_BACKUP")
        row.prop(dm, "register_panel_help", text="", icon="QUESTION")

    def draw(self, context):
        layout = self.layout

        dm = context.scene.DM
        wm = context.window_manager

        global batchops

        if batchops is None:
            batchops, _, _, _ = get_addon("Batch Operations™")



        box = layout.box()
        box.prop(dm, "show_panel_defaults", text="Defaults", icon='TRIA_DOWN' if dm.show_panel_defaults else 'TRIA_RIGHT', emboss=False)

        if dm.show_panel_defaults:
            self.draw_defaults(dm, wm, box)



        sweep = [obj for obj in context.scene.objects if obj.DM.isbackup]

        if sweep:
            box = layout.box()
            column = box.column()

            row = column.row()
            row.scale_y = 1.2
            row.operator('machin3.sweep_decal_backups', text='Sweep Decal Backups')



        box = layout.box()
        column = box.column()

        column.prop(dm, "show_panel_tools", text="Tools", icon='TRIA_DOWN' if dm.show_panel_tools else 'TRIA_RIGHT', emboss=False)

        if dm.show_panel_tools:
            self.draw_tools(column)



        column.separator()

        column.prop(dm, "show_panel_utils", text="Utils", icon='TRIA_DOWN' if dm.show_panel_utils else 'TRIA_RIGHT', emboss=False)

        if dm.show_panel_utils:
            self.draw_utils(column)



        if dm.debug or getattr(bpy.types, "MACHIN3_OT_debug_whatever", False):
            column.separator()

            column.prop(dm, "show_panel_developer", text="Developer", icon='TRIA_DOWN' if dm.show_panel_developer else 'TRIA_RIGHT', emboss=False)

            if dm.show_panel_developer:
                self.draw_debug(context, dm, column)

    def draw_debug(self, context, dm, layout):
        col = layout.column(align=True)

        if getattr(bpy.types, "MACHIN3_OT_debug_whatever", False):
            row = col.row(align=True)
            row.scale_y = 1.2
            row.operator("machin3.debug_whatever", text="Debug Whatever")


        if dm.debug:
            if context.scene.userdecallibs:
                row = col.split(factor=0.33, align=True)
                row.label(text="User Decal Library")
                row.prop(context.scene, "userdecallibs", text="")

                if getattr(bpy.types, "MACHIN3_OT_rerender_decal_thumbnails", False):
                    row = col.row(align=True)
                    row.scale_y = 1.2
                    row.operator("machin3.rerender_decal_thumbnails", text="Re-Render Decal Thumbnails")

                if getattr(bpy.types, "MACHIN3_OT_update_interpolation", False):
                    row = col.row(align=True)
                    row.scale_y = 1.2
                    row.operator("machin3.update_interpolation", text="Update Interpolation")

            else:
                col.label(text="Create a new Library or Unlock an existing one.")

            if getattr(bpy.types, "MACHIN3_OT_update_decal_node_tree", False):
                row = col.row(align=True)
                row.scale_y = 1.2
                row.operator("machin3.update_decal_node_tree", text="Update Decal NodeTrees")

            if getattr(bpy.types, "MACHIN3_OT_replace_material", False):
                row = col.row(align=True)
                row.scale_y = 1.2
                row.operator("machin3.replace_material", text="Replace Material")

            if getattr(bpy.types, "MACHIN3_OT_set_props_and_name_from_material", False):
                row = col.row(align=True)
                row.scale_y = 1.2
                row.operator("machin3.set_props_and_name_from_material", text="Set Props and Name from Material")

            if getattr(bpy.types, "MACHIN3_OT_update_decal_backup", False):
                row = col.row(align=True)
                row.scale_y = 1.2
                row.operator("machin3.update_decal_backup", text="Update Decal Backup")

            if getattr(bpy.types, "MACHIN3_OT_update_add_nodes_clamping", False):
                    col.separator()

                    row = col.row(align=True)
                    row.scale_y = 1.5
                    row.operator("machin3.update_add_nodes_clamping", text="Fix AO Clamping")


    def draw_utils(self, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.remove_decal_orphans", text="Remove Decal Orphans")
        row.operator("machin3.fix_decal_texture_paths", text="Fix Texture Paths")

        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.validate_decal", text="Validate Decal")
        row.operator("machin3.clear_decal_props", text="Clear Decal Props")

    def draw_tools(self, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.join_decal", text="Join")
        row.operator("machin3.split_decal", text="Split")

        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.remove_mesh_cuts", text="Remove Mesh Cuts")

        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.init_generated_coordinates", text="Init Generated Coords")
        row.operator("machin3.uv_transfer", text="Transfer UVs")

    def draw_defaults(self, dm, wm, layout):


        b = layout.box()
        column = b.column()

        row = column.split(factor=0.33)
        row.label(text="Collections")
        r = row.row(align=True)
        r.prop(dm, "collection_decaltype", text="Type", toggle=True)
        r.prop(dm, "collection_decalparent", text="Parent", toggle=True)
        r.prop(dm, "collection_active", text="Active", toggle=True)



        b = layout.box()
        column = b.column()

        row = column.split(factor=0.33)
        row.label(text="Hide")
        r = row.row(align=True)
        r.prop(dm, "hide_materials", text="Materials", toggle=True)
        r.prop(dm, "hide_textures", text="Textures", toggle=True)
        r.prop(dm, "hide_nodetrees", text="Node Trees", toggle=True)

        if batchops:
            row = column.split(factor=0.33)
            row.label()
            r = row.row(align=True)
            r.prop(dm, "hide_decaltype_collections", text="Type Col", toggle=True)
            r.prop(dm, "hide_decalparent_collections", text="Parent Col", toggle=True)



        b = layout.box()
        column = b.column()

        row = column.row(align=True)
        row.label(text="Quality")
        row.prop(dm, "parallax", toggle=True)
        row.prop(dm, "glossyrays", toggle=True)

        row = column.row(align=True)
        row.label(text="Normal Transfer")
        row.prop(dm, "normaltransfer_viewport", text="Viewport", toggle=True)
        row.prop(dm, "normaltransfer_render", text="Render", toggle=True)



        b = layout.box()
        column = b.column()

        row = column.row()
        row.label(text="Color Interpolation")
        row.prop(dm, "color_interpolation", expand=True)

        row = column.row()
        row.label(text="Blend Mode")
        row.prop(dm, "alpha_blendmode", expand=True)

        row = column.split(factor=0.33)
        row.label(text="AO & Invert")
        row.prop(dm, "ao_strength", slider=True)
        row.prop(dm, "invert_infodecals", text="Invert", toggle=True)

        row = column.split(factor=0.33)
        row.label(text="Edge Highlights")
        r = row.row()
        r.prop(dm, "edge_highlights", expand=True)

        row = column.split(factor=0.33)
        row.label(text="Texture Storage")
        r = row.row()
        r.prop(dm, "pack_images", expand=True)



        b = layout.box()
        column = b.column()

        row = column.split(factor=0.33)
        row.label(text="Snapping")
        r = row.row()
        r.prop(dm, "enable_surface_snapping", text='Surface Snapping', toggle=True)

        row = column.split(factor=0.33)
        row.label(text="Decal Align")
        r = row.row()
        r.prop(dm, "align_mode", expand=True)


        row = column.split(factor=0.33)
        row.label(text="Auto-Match")
        r = row.row()
        r.prop(dm, "auto_match", expand=True)

        if dm.auto_match == "MATERIAL":
            row = column.split(factor=0.33)
            row.label(text="Material")
            r = row.row(align=True)
            r.prop(wm, "matchmaterial", text="")

            mat = bpy.data.materials.get(wm.matchmaterial)
            icon = "refresh" if wm.matchmaterial in ["None", "Default"] or (mat and get_pbrnode_from_mat(mat)) else "refresh_red"

            r.operator("machin3.update_match_materials", text="", icon_value=get_icon(icon))


class PanelDecalCreation(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_decal_creation"
    bl_label = "Decal, Atlas & Trim Sheet Creation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return context.scene.DM.register_panel_creation

    def draw(self, context):
        layout = self.layout

        dm = context.scene.DM
        wm = context.window_manager

        sel = context.selected_objects
        active = context.active_object
        decals = sorted([obj for obj in sel if obj.DM.isdecal and not obj.DM.isprojected and not obj.DM.issliced], key=lambda x: x.name)


        box = layout.box()
        box.label(text="Create")

        row = box.row()
        row.scale_y = 1.2
        row.prop(dm, "create_type", expand=True)

        if dm.create_type == 'DECAL':
            row = box.row()
            row.scale_y = 1.2
            row.prop(dm, "create_decaltype", expand=True)

            if dm.create_decaltype in ['SIMPLESUBSET', 'PANEL']:
                b = box.box()
                b.label(text=f"Bake Settings ({context.scene.cycles.device})")

                self.draw_simple_subset_panel_creation(context, active, dm, wm, sel, b)


            elif dm.create_decaltype == "INFO":
                b = box.box()
                b.label(text="Texture Settings")

                row = b.split(factor=0.33)
                row.label(text="Source")
                r = row.row()
                r.prop(dm, "create_infotype", expand=True)

                if dm.create_infotype == 'IMAGE':
                    self.draw_info_from_image_creation(context, dm, b)

                elif dm.create_infotype == 'FONT':
                    self.draw_info_from_text_creation(context, dm, b)

                elif dm.create_infotype == 'GEOMETRY':
                    self.draw_info_from_geometry_creation(context, active, dm, b)



            draw_pil_warning(box, needed="for decals creation")
            self.draw_create_button(dm, sel, box)



            if bpy.types.WindowManager.instantdecallib.keywords['items']:
                box = layout.box()
                action = "Remove " if get_prefs().decalremovemode else ""
                row = box.row()
                row.scale_y = 1.2
                row.label(text="%sInstant Decals" % (action))
                row.operator("machin3.open_instant_location", text="Open Folder").type = 'DECAL'

                self.draw_instant_decals(context, box)

            elif get_prefs().decalremovemode:
                box = layout.box()
                box.label(text="Toggle Remove")

                row = box.row()
                row.prop(get_prefs(), "decalremovemode", text="Remove Decals")



            if decals:
                box = layout.box()
                box.label(text="Add to Library")

                self.draw_add_to_library(context, dm, decals, box)


        elif dm.create_type == 'ATLAS':
            row = box.row()
            row.scale_y = 1.2
            row.prop(dm, "create_atlascreation_type", expand=True)

            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None
            only_atlas_is_selected = [atlas] == sel
            decals = [obj for obj in sel if obj.DM.isdecal]

            if dm.create_atlascreation_type == 'IMPORT':
                self.draw_import_atlas(dm, box)

            if only_atlas_is_selected:
                self.draw_atlas_properties(context, dm, atlas, box)

                self.draw_atlas_storage(atlas, box)

            elif atlas and decals:
                self.draw_add_decals_to_atlas(atlas, decals, box)

            elif dm.create_atlascreation_type == 'NEW':
                self.draw_packing_settings(context, dm, atlas, only_atlas_is_selected, box)



            if wm.instantatlascount > 0:
                box = layout.box()
                self.draw_instant_atlases(context, wm, box)


        elif dm.create_type == 'TRIMSHEET':
            row = box.row()
            row.scale_y = 1.2
            row.prop(dm, "create_trim_type", expand=True)


            self.draw_trimsheet_creation(context, dm, active, box)
            self.draw_trimsheet_properties(context, dm, active, box)



            draw_pil_warning(box, needed="for trim sheet creation")
            self.draw_trimsheet_create_buttons(dm, active, sel, box)



            if wm.instanttrimsheetcount > 0:
                box = layout.box()
                self.draw_instant_trimsheets(context, wm, box)



    def draw_instant_trimsheets(self, context, wm, layout):
        row = layout.split(factor=0.7)
        row.label(text="Instant Trim Sheets")
        row.label(text=str(wm.instanttrimsheetcount))

        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.open_instant_location", text="Open Folder").type = 'TRIMSHEET'
        row.operator("machin3.clear_instant", text="Clear Out Folder").type = 'TRIMSHEET'

    def draw_trimsheet_create_buttons(self, dm, active, sel, layout):
        if active and active.DM.istrimsheet:
            row = layout.split(factor=0.35, align=True)
            row.label(text="Keep Sheet UUID")
            row.prop(dm, "create_trim_import_keep_sheet_uuid", text='True' if dm.create_trim_import_keep_sheet_uuid else 'False', toggle=True)

            row = layout.split(factor=0.35, align=True)
            row.scale_y = 1.5
            row.operator("machin3.trimsheet", text="Trim it")
            row.operator("machin3.create_trimsheet_library", text="Create Trim Sheet Library")

    def draw_trimsheet_properties(self, context, dm, active, layout):
        if active and active.DM.istrimsheet:
            box = layout.box()

            self.draw_trimsheet_available_textures(self, box)

            row = box.row()
            row.label(text="Trim Sheet Properties")
            row.operator("machin3.remove_instant_trim_sheet", text="", icon_value=get_icon('cancel'), emboss=True)

            row = box.split(factor=0.3)
            row.label(text="Name")
            row.prop(active.DM, "trimsheetname", text='')

            width, height = active.DM.trimsheetresolution
            trimmaps = active.DM.trimmapsCOL

            row = box.split(factor=0.3)
            row.label(text="Resolution")
            row.label(text="%d x %d" % (width, height))

            if any([trim_map.texture and tuple(trim_map.resolution) != (width, height) for trim_map in trimmaps]):
                row.label(text="Mismatch", icon='ERROR')

            box.prop(active.DM, "show_trim_maps", text="Texture Maps (%d)" % len([True for trim_map in trimmaps if trim_map.texture]), icon='TRIA_DOWN' if active.DM.show_trim_maps else 'TRIA_RIGHT', emboss=False)

            if active.DM.show_trim_maps:
                column = box.column()
                column.active = len(bpy.types.WindowManager.trimtextures.keywords['items']) > 1
                column.template_list("MACHIN3_UL_trim_maps", "", active.DM, "trimmapsCOL", active.DM, "trimmapsIDX", rows=len(active.DM.trimmapsCOL))



            if active and (any([trim_map.texture for trim_map in trimmaps]) or active.DM.trimsCOL):
                box.prop(active.DM, "show_trims", text="Trim Setup (%d)" % len(active.DM.trimsCOL), icon='TRIA_DOWN' if active.DM.show_trims else 'TRIA_RIGHT', emboss=False)

                if active.DM.show_trims:
                    column = box.column()
                    row = column.row()

                    offset = 12

                    col = row.column(align=True)
                    col.template_list("MACHIN3_UL_trims", "", active.DM, "trimsCOL", active.DM, "trimsIDX", rows=max(len(active.DM.trimsCOL), offset))

                    col = row.column(align=True)

                    c = col.column()
                    scale = (max(len(active.DM.trimsCOL), offset) - offset) * 3.3 if active.DM.trimopspinned else 0

                    c.scale_y = scale
                    c.separator()

                    c = col.column(align=True)
                    c.prop(active.DM, "trimopspinned", text="", icon="PINNED" if active.DM.trimopspinned else "UNPINNED")
                    c.separator()
                    c.operator("machin3.add_trim", text="", icon="ADD")
                    c.operator("machin3.duplicate_trim", text="", icon="DUPLICATE")
                    c.operator("machin3.draw_trim", text="", icon="GREASEPENCIL")
                    c.separator()
                    c.operator("machin3.align_trim", text="", icon="TRIA_LEFT").side = 'LEFT'
                    c.operator("machin3.align_trim", text="", icon="TRIA_RIGHT").side = 'RIGHT'
                    c.operator("machin3.align_trim", text="", icon="TRIA_UP").side = 'TOP'
                    c.operator("machin3.align_trim", text="", icon="TRIA_DOWN").side = 'BOTTOM'
                    c.separator()
                    c.operator("machin3.hide_all_trims", text="", icon="HIDE_OFF").hide_select = False
                    c.operator("machin3.hide_all_trims", text="", icon="RESTRICT_SELECT_OFF").hide_select = True
                    c.separator()
                    icon = "cancel" if active.DM.trimsCOL else "cancel_grey"
                    c.operator("machin3.remove_trim", text="", icon_value=get_icon(icon))

    def draw_trimsheet_creation(self, context, dm, active, layout):
        box = layout.box()

        if dm.create_trim_type == 'NEW':
            row = box.row(align=True)
            row.scale_y = 1.2
            row.operator("machin3.init_trimsheet", text="Initialze")
            row.operator("machin3.duplicate_trimsheet", text="Duplicate")


        elif dm.create_trim_type == 'IMPORT':
            row = box.split(factor=0.3, align=True)
            row.label(text='Location')
            row.prop(dm, "create_trim_import_path", text='')

            row = box.split(factor=0.3, align=True)
            row.label(text='Keep Trim UUIDs')
            row.prop(dm, "create_trim_import_keep_trim_uuids", text='True' if dm.create_trim_import_keep_trim_uuids else 'False', toggle=True)

            row = box.row(align=True)
            row.scale_y = 1.5
            row.operator("machin3.import_trimsheet", text="Import Trim Sheet")

    def draw_trimsheet_available_textures(self, context, layout):
        box = layout.box()

        row = box.split(factor=0.7)
        row.label(text="Available PNG Textures:")
        row.label(text="%d" % (len(bpy.types.WindowManager.trimtextures.keywords['items']) - 1))

        row = box.row(align=True)
        row.scale_y = 1.2

        row.operator("machin3.load_trimsheet_textures", text="Load Texture(s)")
        row.operator("machin3.open_instant_location", text="Open Folder").type = 'TRIMTEXTURES'
        row.operator("machin3.clear_trimsheet_textures", text="Clear Textures")



    def draw_instant_atlases(self, context, wm, layout):
        row = layout.split(factor=0.7)
        row.label(text="Instant Atlases")
        row.label(text=str(wm.instantatlascount))

        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.open_instant_location", text="Open Folder").type = 'ATLAS'
        row.operator("machin3.clear_instant", text="Clear Out Folder").type = 'ATLAS'

    def draw_import_atlas(self, dm, layout):
        box = layout.box()

        row = box.row(align=True)
        row.prop(dm, "create_atlas_import_path", text="Location")

        row = box.row(align=True)
        row.scale_y = 1.5
        row.operator("machin3.import_atlas", text="Import Atlas")

    def draw_add_decals_to_atlas(self, atlas, decals, layout):
        sourceuuids = [uuid for uuid in atlas.DM.get('sources').to_dict()] if atlas.DM.get('sources') else []
        new_decals = [obj for obj in decals if obj.DM.uuid not in sourceuuids] if sourceuuids else []

        box = layout.box()

        box.label(text="Add to Atlas")

        column = box.column()

        row = column.split(factor=0.3)
        row.label(text="Name")
        row.label(text=atlas.DM.atlasname)

        row = column.split(factor=0.3)
        row.label(text="Resolution")
        row.label(text="%d x %d" % (atlas.DM.atlasresolution[0], atlas.DM.atlasresolution[1]))

        row = box.row()
        row.scale_y = 1.5
        row.operator("machin3.add_decals_to_atlas", text="Add %s" % ('Decal' if len(new_decals) < 2 else 'Decals'))

    def draw_atlas_storage(self, atlas, layout):
        box = layout.box()
        box.label(text="Store Atlas")

        lower, _ = get_lower_and_upper_atlas_resolution(atlas.DM.atlasresolution[0])

        if lower != atlas.DM.atlasresolution[0]:
            row = box.split(factor=0.3, align=True)
            row.label(text="Resize")
            row.prop(atlas.DM, "atlasresizedown", text="True" if atlas.DM.atlasresizedown else "False", toggle=True)
            r = row.row()
            r.active = atlas.DM.atlasresizedown
            r.label(text="%d x %d" % (lower, lower))

        draw_pil_warning(box, "for atlas storage")

        row = box.row()
        row.scale_y = 1.5

        row.operator("machin3.store_atlas", text="Store selected Atlas")

    def draw_atlas_properties(self, context, dm, atlas, layout):
        box = layout.box()

        row = box.row()
        row.prop(atlas.DM, "show_atlas_props", text="Atlas Properties", icon='TRIA_DOWN' if atlas.DM.show_atlas_props else 'TRIA_RIGHT', emboss=False)
        row.operator("machin3.remove_instant_atlas", text="", icon_value=get_icon('cancel'), emboss=True)

        row = box.split(factor=0.3)
        row.label(text="Name")
        row.prop(atlas.DM, "atlasname", text='')

        solution = atlas.DM.get('solution')

        if solution:
            resolution = atlas.DM.atlasresolution
            padding = solution.get('padding', None)
            efficiency = solution.get('efficiency', None)

            if not any(prop is None for prop in [resolution, padding, efficiency]):
                row = box.split(factor=0.3)

                if atlas.DM.show_atlas_props:
                    row.label(text="Stats")
                    row.label(text="%d x %d, %d padding, %0.1f%% efficient" % (*resolution, padding, efficiency))
                else:
                    row.label(text="Resolution")
                    row.label(text="%d x %d" % (resolution[0], resolution[1]))

                if solution['type'] in ['NORMAL', 'COMBINED']:
                    row = box.split(factor=0.3)

                    row.label(text="Parallax")
                    row.prop(atlas.DM, "atlasdummyparallax", text='', slider=True)


        if atlas.DM.show_atlas_props:
            column = box.column()
            column.label(text="Packed Decals (sorted by %s)" % ("Name" if atlas.DM.atlastrimsort == 'NAME' else "Packing Order"))

            offset = 7 if atlas.DM.atlasrefinement == 'REPACK' else 11

            row = column.row()
            col = row.column()
            col.template_list("MACHIN3_UL_atlas_trims", "", atlas.DM, "trimsCOL", atlas.DM, "trimsIDX", rows=max(len(atlas.DM.trimsCOL), offset))

            col = row.column(align=True)

            c = col.column()
            scale = (max(len(atlas.DM.trimsCOL), offset) - offset) * 3.3 if atlas.DM.trimopspinned else 0

            c.scale_y = scale
            c.separator()

            c = col.column(align=True)
            c.prop(atlas.DM, "trimopspinned", text="", icon="PINNED" if atlas.DM.trimopspinned else "UNPINNED")
            c.separator()
            c.separator()
            c.operator("machin3.toggle_atlas_trim_sort", text="", icon_value=get_icon('refresh'))
            c.separator()
            c.prop(dm, "create_atlas_non_uniform_scale", text="", icon="CON_SAMEVOL")
            c.operator("machin3.scale_atlas_trim", text="", icon="FULLSCREEN_EXIT").mode = 'DOWN'
            c.operator("machin3.scale_atlas_trim", text="", icon="FULLSCREEN_ENTER").mode = 'UP'

            if atlas.DM.atlasrefinement == 'TWEAK':
                c.separator()
                c.operator("machin3.align_atlas_trim", text="", icon="TRIA_LEFT").side = 'LEFT'
                c.operator("machin3.align_atlas_trim", text="", icon="TRIA_RIGHT").side = 'RIGHT'
                c.operator("machin3.align_atlas_trim", text="", icon="TRIA_UP").side = 'TOP'
                c.operator("machin3.align_atlas_trim", text="", icon="TRIA_DOWN").side = 'BOTTOM'

            c.separator()
            c.operator("machin3.reset_atlas_trim", text="", icon="LOOP_BACK").idx = "ALL"
            c.operator("machin3.remove_decal_from_atlas", text="", icon_value=get_icon('cancel'))

            self.draw_packing_settings(context, dm, atlas, True, box)

            draw_pil_warning(box, "for atlas creation")


            row = box.row()
            row.scale_y = 1.5

            mode = atlas.DM.atlasrefinement
            row.operator("machin3.create_atlas", text="%s selected Atlas" % ('Re-Pack' if mode == 'REPACK' else 'Tweak')).mode = mode

    def draw_packing_settings(self, context, dm, atlas, only_atlas_is_selected, layout):
        box = layout.box()

        box.label(text="%s Settings" % ("Tweak" if only_atlas_is_selected and atlas.DM.atlasrefinement == 'TWEAK' else 'Pack'))

        if only_atlas_is_selected:
            row = box.split(factor=0.33)
            row.label(text="Refinement")
            r = row.row()
            r.scale_y = 1.2
            r.prop(atlas.DM, "atlasrefinement", expand=True)

        if not only_atlas_is_selected:
            row = box.split(factor=0.33)
            row.label(text="Type")
            r = row.row()
            r.scale_y = 1.2
            r.prop(dm, "create_atlas_type", expand=True)

        if not only_atlas_is_selected or atlas.DM.atlasrefinement == 'REPACK':
            row = box.split(factor=0.33)
            row.label(text="Size")
            r = row.row()
            r.prop(dm, "create_atlas_size_mode", expand=True)

            if dm.create_atlas_size_mode == 'SPECIFIC':
                row = box.split(factor=0.33)
                row.label(text="Resolution")
                r = row.row()
                r.prop(dm, "create_atlas_resolution", text="")

            row = box.split(factor=0.33)
            row.label(text="Padding")
            row.prop(dm, "create_atlas_padding", text="")

        if only_atlas_is_selected and atlas.DM.atlasrefinement == 'TWEAK':
            row = box.split(factor=0.33)
            row.label(text="Resolution")
            r = row.row()

            if dm.create_atlas_resolution < atlas.DM.atlasresolution[0]:
                r.label(text="", icon="ERROR")

            r.prop(dm, "create_atlas_resolution", text="")

        if not only_atlas_is_selected:
            row = box.split(factor=0.33)
            row.label(text="Pre-Pack Panels")
            r = row.row()
            r.prop(dm, "create_atlas_prepack", expand=True)

        if (only_atlas_is_selected and atlas.DM.get('solution') and atlas.DM.get('solution')['type'] in ['NORMAL', 'COMBINED']) or (not only_atlas_is_selected and dm.create_atlas_type in ['NORMAL', 'COMBINED']):
            row = box.split(factor=0.33, align=True)
            row.label(text="Height")
            row.prop(dm, "create_atlas_compensate_height", text="Compensate", toggle=True)
            row.prop(dm, "create_atlas_normalize_height", text="Normalize", toggle=True)

        if not only_atlas_is_selected:
            draw_pil_warning(box, "for atlas creation")

            row = box.row()
            row.scale_y = 1.5
            row.operator("machin3.create_atlas", text="Create new Decal Atlas from %s" % ("Selection" if context.selected_objects else "Scene")).mode = 'INITIATE'



    def draw_add_to_library(self, context, dm, decals, layout):
        column = layout.column()

        if not context.scene.userdecallibs:
            text = "Create a new empty Decal Library"

            if [lib for lib in get_prefs().decallibsCOL if not lib.istrimsheet and lib.islocked]:
                text += " or unlock an existing one"

            text += "!"

            column.label(text=text, icon_value=get_icon('error'))


        else:
            decals_with_names = [obj for obj in decals if obj.DM.decaltype == 'INFO' and obj.active_material.DM.decalnamefromfile]

            wm = context.window_manager
            skip_index = dm.addlibrary_skip_index

            if not wm.newdecalidx:
                set_new_decal_index(self, context)

            basename = dm.addlibrary_decalname.strip().replace(" ", "_") if dm.addlibrary_decalname else ''
            startidx = wm.newdecalidx

            assetspath = get_prefs().assetspath
            library = context.scene.userdecallibs
            librarypath = os.path.join(assetspath, 'Decals', library)

            existingnames = [f for f in os.listdir(librarypath) if os.path.isdir(os.path.join(librarypath, f))]

            names = [decal.active_material.DM.decalnamefromfile if (decal.active_material.DM.decalnamefromfile and dm.addlibrary_use_filename) else basename for decal in decals]


            row = column.split(factor=0.33)
            row.label(text="User Decal Library")

            r = row.row(align=True)
            r.prop(context.scene, "userdecallibs", text="")
            r.operator("machin3.open_user_decal_lib", text="", icon="FILE_FOLDER")

            row = column.split(factor=0.33)
            row.label(text="Decal Name")
            col = row.column()

            row = col.row()

            if decals_with_names:
                row.prop(dm, "addlibrary_use_filename", text=f"Use File Name{'s' if len(decals_with_names) > 1 else ''}")

            if (decals_with_names and dm.addlibrary_use_filename) or dm.addlibrary_decalname:
                row.prop(dm, "addlibrary_skip_index", text=f"Skip {'Indices' if len(decals) > 1 else 'Index'}")

            if decals != decals_with_names or not dm.addlibrary_use_filename:
                col.prop(dm, "addlibrary_decalname", text="")

            decalnames = []

            for i, name in enumerate(names):
                if name:
                    decalname = f"{str(int(startidx) + i).zfill(3) + '_' if not skip_index else ''}{name}"

                else:
                    decalname = str(int(startidx) + i).zfill(3)

                decalnames.append(decalname)

            duplicate_names = len(decalnames) > len(set(decalnames))
            unavailable_names = sum([decalname in existingnames for decalname in decalnames])

            if duplicate_names or unavailable_names:
                col.separator()

                if unavailable_names:
                    col.label(text=f"Existing Folder Name{'s' if unavailable_names > 1 else ''}!", icon_value=get_icon('error'))

                if duplicate_names:
                    col.label(text="Duplicate Decal Names!", icon_value=get_icon('error'))

                col.separator()

            pathstr = []

            for decalname in decalnames:
                pathstr.append(f"{library} / {decalname}")

            row = column.split(factor=0.33)
            row.label(text="Path Preview")
            col = row.column()

            for ps in pathstr:
                col.label(text=ps, icon="FILE_FOLDER")


            column = layout.column()

            subset_decals = [obj for obj in decals if obj.DM.decaltype == 'SUBSET']

            if subset_decals:
                column.separator()

                row = column.split(factor=0.33)
                row.label(text="Subset")

                col = row.column()
                col.prop(dm, "create_bake_store_subset", text=f"Store Subset Material{'s' if len(subset_decals) > 1 else ''} on Decal Asset{'s' if len(subset_decals) > 1 else ''}")
                column.separator()


            forced = [obj.DM.is_forced_uuid for obj in decals]

            if any(forced):
                row = column.split(factor=0.33)
                row.label(text="Advanced")
                row.label(text=f"Forced UUID{'s are' if sum(forced) > 1 else ' is'} being used", icon='INFO')

            row = column.row()
            row.scale_y = 1.5
            row.operator("machin3.add_decal_to_library", text="Add %s to Library" % ("Decal" if len(decals) <= 1 else "Decals"))

    def draw_instant_decals(self, context, layout):
        wm = context.window_manager

        libraryscale = get_prefs().libraryscale
        decalsinlibraryscale = get_prefs().decalsinlibraryscale

        column = layout.column()
        column.template_icon_view(wm, "instantdecallib", show_labels=False, scale=libraryscale, scale_popup=decalsinlibraryscale)

        decalmode = get_prefs().decalmode

        if decalmode == "INSERT":
            text, icon = "", get_icon("plus")
            idname = "machin3.insert_decal"

        elif decalmode == "REMOVE":
            text, icon = ("", get_icon("cancel"))
            idname = "machin3.remove_decal"

        op = column.operator(idname, text=text, icon_value=icon)
        op.library = "INSTANT"
        op.decal = getattr(wm, "instantdecallib")
        op.instant = True

        if decalmode == "INSERT":
            op.force_cursor_align = True

        row = column.row()
        row.prop(get_prefs(), "decalremovemode", text="Remove Decals")

        if get_prefs().decalremovemode and len(bpy.types.WindowManager.instantdecallib.keywords['items']) > 1:
            row = column.row()
            row.scale_y = 1.5
            row.operator("machin3.remove_all_instant_decals", text="Remove All Instant Decals at once", icon_value=get_icon("cancel"))

    def draw_create_button(self, dm, sel, layout):
        row = layout.row()
        row.scale_y = 1.5

        if dm.create_decaltype == "SIMPLESUBSET":
            decaltype = "SIMPLE" if len(sel) == 1 else "SUBSET" if len(sel) > 1 else ""

        else:
            decaltype = dm.create_decaltype

        if dm.create_decaltype == 'INFO' and dm.create_infoimg_batch:
            row.operator("machin3.batch_create_decals", text="Batch Create %s Decals" % (decaltype))

        else:
            row.operator("machin3.create_decal", text="Create %s Decal" % (decaltype))

    def draw_info_from_geometry_creation(self, context, active, dm, layout):
        if active and not active.DM.isdecal:
            row = layout.split(factor=0.33)

            row.label(text="Anti Aliasing, Padding")
            r = row.row()
            r.prop(dm, "create_bake_supersample", expand=True)

            rr = r.row(align=True)
            rr.prop(dm, "create_infotext_padding", text="")
            rr.operator("machin3.reset_default_property", text="", icon="LOOP_BACK").mode = "PADDING"

            row = layout.split(factor=0.33)
            row.label(text="Resolution")
            r = row.row()
            r.prop(dm, "create_bake_resolution", expand=True)

            row = layout.split(factor=0.33)
            row.label(text="Emission")
            col = row.column()
            col.prop(dm, "create_bake_emissive", text="Bake Emission")

            row = layout.split(factor=0.33)
            row.label(text="Advanced")
            col = row.column()
            col.prop(dm, "create_bake_inspect")
            col.prop(dm, "create_force_uuid")

            if dm.create_force_uuid and active:
                if active.DM.forced_uuid:
                    col.prop(active.DM, "forced_uuid", text='')

                else:
                    col.label(text='No UUID set yet')

        else:
            layout.label(text="Select Decal Source Geometry", icon='INFO')

    def draw_info_from_text_creation(self, context, dm, layout):
        wm = context.window_manager
        WM = bpy.types.WindowManager

        row = layout.row(align=True)

        row.scale_y = 1.2

        row.operator("machin3.load_fonts", text="Load Font")
        row.operator("machin3.open_instant_location", text="Open Folder").type = 'INFOFONTS'
        row.operator("machin3.clear_fonts", text="Clear Fonts")

        if WM.infofonts.keywords['items']:
            layout.template_icon_view(wm, "infofonts", show_labels=True, scale=4, scale_popup=8)

            row = layout.split(factor=0.33)
            row.label(text="Font")
            row.label(text=wm.infofonts)
            row.prop(dm, "create_infotext_size", text="Size")

            row = layout.split(factor=0.33)
            row.scale_y = 1.5
            row.label(text="Text")
            row.prop(dm, "create_infotext", text="")

            row = layout.split(factor=0.33)
            row.label(text="Colors")
            row.prop(dm, "create_infotext_color", text="")

            row.prop(dm, "create_infotext_bgcolor", text="")

            if "\\n" in dm.create_infotext:
                row = layout.split(factor=0.33)
                row.label(text="Align Text")
                r = row.row()
                r.prop(dm, "create_infotext_align", expand=True)

            row = layout.split(factor=0.33)
            row.label(text="Padding, Offset")
            r = row.row()

            rs = r.row(align=True)
            rs.prop(dm, "create_infotext_padding", text="")
            rs.operator("machin3.reset_default_property", text="", icon="LOOP_BACK").mode = "PADDING"

            rs = r.row(align=True)
            rs.prop(dm, "create_infotext_offset", text="")
            rs.operator("machin3.reset_default_property", text="", icon="LOOP_BACK").mode = "OFFSET"

    def draw_info_from_image_creation(self, context, dm, layout):
        wm = context.window_manager
        WM = bpy.types.WindowManager

        row = layout.row(align=True)
        row.scale_y = 1.2

        row.operator("machin3.load_images", text="Load Image(s)")
        row.operator("machin3.open_instant_location", text="Open Folder").type = 'INFOTEXTURES'
        row.operator("machin3.clear_images", text="Clear Images")

        if WM.infotextures.keywords['items']:
            layout.template_icon_view(wm, "infotextures", show_labels=True, scale=4, scale_popup=8)

        row = layout.split(factor=0.33)
        row.label(text="Crop, Padding")
        row.prop(dm, "create_infoimg_crop", toggle=True)
        r = row.row()
        r.active = dm.create_infoimg_crop
        r.prop(dm, "create_infoimg_padding", text="")

        if len(WM.infotextures.keywords['items']) > 1:
            row = layout.split(factor=0.33)
            row.label(text="Batch Creation")
            row.prop(dm, "create_infoimg_batch", text="All source images at once")

    def draw_simple_subset_panel_creation(self, context, active, dm, wm, sel, layout):
        if active and not active.DM.isdecal:
            row = layout.split(factor=0.33)
            row.label(text="Anti Aliasing")
            r = row.row()
            r.prop(dm, "create_bake_supersample", expand=True)

            r = row.row()
            r.active = context.scene.DM.create_bake_supersample != "0"
            r.prop(dm, "create_bake_supersamplealpha", text="Alpha", toggle=True)

            row = layout.split(factor=0.33)
            row.label(text="Resolution")
            r = row.row()
            r.prop(dm, "create_bake_resolution", expand=True)

            row = layout.split(factor=0.33)
            row.label(text="AO")
            r = row.row()
            r.prop(dm, "create_bake_aosamples", expand=True)
            row.prop(dm, "create_bake_aocontrast")

            row = layout.split(factor=0.33)
            row.label(text="Curvature")
            row.prop(dm, "create_bake_curvaturewidth")
            row.prop(dm, "create_bake_curvaturecontrast")

            row = layout.split(factor=0.33)
            row.label(text="Height")
            row.prop(dm, "create_bake_heightdistance")

            row = layout.split(factor=0.33)
            row.label(text="Emission")
            col = row.column()
            col.prop(dm, "create_bake_emissive", text="Bake Emission")

            if dm.create_bake_emissive:
                col.prop(dm, "create_bake_emissive_bounce", text="Bounce Light")

                if dm.create_bake_emissive_bounce:
                    row = col.row()
                    row.prop(dm, "create_bake_emissionsamples", text="Bounce Light", expand=True)


            row = layout.split(factor=0.33)
            row.label(text="Alpha")
            col = row.column()
            col.prop(dm, "create_bake_limit_alpha_to_active", text="Limit to Active")
            col.prop(dm, "create_bake_limit_alpha_to_boundary", text="Limit to Boundary")
            col.prop(dm, "create_bake_flatten_alpha_normals", text="Flatten Normals")

            if dm.create_decaltype == "PANEL":
                row = layout.split(factor=0.33)
                row.label(text="Mask")
                row.prop(dm, "create_bake_maskmat2")

            if len(sel) > 1:
                row = layout.split(factor=0.33)
                row.label(text="Subset")

                col = row.column()
                col.prop(dm, "create_bake_store_subset", text="Store Subset Material on Decal Asset")

                if dm.create_bake_store_subset:
                    row = col.row(align=True)
                    row.prop(wm, "matchmaterial", text="")

                    mat = bpy.data.materials.get(wm.matchmaterial)
                    icon = "refresh" if wm.matchmaterial in ["None", "Default"] or (mat and get_pbrnode_from_mat(mat)) else "refresh_red"

                    row.operator("machin3.update_match_materials", text="", icon_value=get_icon(icon))

            row = layout.split(factor=0.33)
            row.label(text="Advanced")
            col = row.column()
            col.prop(dm, "create_bake_inspect")
            col.prop(dm, "create_force_uuid")

            if dm.create_force_uuid and active:
                if active.DM.forced_uuid:
                    col.prop(active.DM, "forced_uuid", text='')

                else:
                    col.label(text='No UUID set yet')

        else:
            layout.label(text="Select Decal Source Geometry", icon='INFO')


class PanelDecalExport(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_decal_export"
    bl_label = "Decal Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return context.scene.DM.register_panel_export

    def draw(self, context):
        layout = self.layout

        dm = context.scene.DM

        global machin3tools

        if machin3tools is None:
            machin3tools, _, _, _ = get_addon("MACHIN3tools")

        box = layout.box()
        box.label(text="Export")

        row = box.row()
        row.scale_y = 1.2
        row.prop(dm, "export_type", expand=True)

        if dm.export_type == 'BAKE':
            targets = [obj for obj in context.selected_objects if not obj.DM.isdecal]

            self.draw_bake_settings(context, dm, box, len(targets))

            draw_pil_warning(box, "for decal export")

            restore = [obj for obj in targets if obj.DM.prebakepreviewmats] or dm.export_bake_preview
            self.draw_bake_button(box, restore=restore)

        elif dm.export_type == 'ATLAS':

            b = box.box()
            b.label(text="Atlas Settings")

            self.draw_atlas_settings(dm, b)

            self.draw_decal_atlases(b)

            self.draw_use_atlas_button(b)

            if [obj for obj in context.visible_objects if obj.DM.preatlasmats]:
                self.draw_join_button(context, dm, box)

                self.draw_atlas_export(context, dm, get_addon_prefs('MACHIN3tools') if machin3tools else None, box)



    def draw_machin3tools_unity_export(self, context, layout):
        m3 = context.scene.M3

        row = layout.split(factor=0.25)
        row.label(text="Triangulate")
        row.prop(m3, 'unity_triangulate', text='True' if m3.unity_triangulate else 'False', toggle=True)

        layout.separator()

        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("machin3.prepare_unity_export", text="Prepare %s" % ('Selected' if context.selected_objects else 'Visible') if m3.unity_export else "Prepare %s" % ('Selected' if context.selected_objects else 'Visible')).prepare_only = True

        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.restore_unity_export", text="Restore Transformations")

    def draw_atlas_export(self, context, dm, m3prefs, layout):
        box = layout.box()

        box.label(text="Export Atlas Textures & Models")

        column = box.column()

        row = column.split(factor=0.25)
        row.label(text="Type")

        r = row.row(align=True)
        row.scale_y = 1.2
        r.prop(dm, "export_atlas_textures", text="Textures", toggle=True)
        r.prop(dm, "export_atlas_models", text="Models", toggle=True)

        column.separator()

        row = column.split(factor=0.25)
        row.label(text="Export Location")
        row.prop(dm, "export_atlas_path", text="")

        if dm.export_atlas_textures:
            row = column.split(factor=0.25)
            row.label(text="Textures Folder")
            r = row.row()
            r.prop(dm, "export_atlas_use_textures_folder", text="")
            rr = r.row()
            rr.active = dm.export_atlas_use_textures_folder
            rr.prop(dm, "export_atlas_textures_folder", text="")

        if dm.export_atlas_models:
            row = column.split(factor=0.25)
            row.label(text="Models Folder")
            r = row.row()
            r.prop(dm, "export_atlas_use_models_folder", text="")
            rr = r.row()
            rr.active = dm.export_atlas_use_models_folder
            rr.prop(dm, "export_atlas_models_folder", text="")


        decals = [obj for obj in (context.selected_objects if context.selected_objects else context.visible_objects) if obj.DM.isdecal and obj.DM.preatlasmats]
        atlasmats = {mat for decal in decals for mat in decal.data.materials if mat and mat.DM.isatlasmat}

        if dm.export_atlas_textures:
            b = column.box()
            b.label(text='Textures')

            if atlasmats:
                textypes = get_textypes_from_atlasmats(atlasmats)

                row = b.split(factor=0.25)
                row.label(text="Individual")

                r = row.row(align=True)

                col = r.column(align=True)
                rr = col.row(align=True)
                rr.active = 'ALPHA' in textypes
                rr.prop(dm, "export_atlas_texture_alpha", text="Alpha", toggle=True)
                rr = col.row(align=True)
                rr.active = 'COLOR' in textypes
                rr.prop(dm, "export_atlas_texture_color", text="Color", toggle=True)
                rr = col.row(align=True)
                rr.active = 'EMISSION' in textypes
                rr.prop(dm, "export_atlas_texture_emission", text="Emission", toggle=True)
                rr = col.row(align=True)
                rr.active = 'NORMAL' in textypes
                rr.prop(dm, "export_atlas_texture_normal", text="Normal", toggle=True)
                rr = col.row(align=True)
                rr.active = 'METALLIC' in textypes
                rr.prop(dm, "export_atlas_texture_metallic", text="Metallic", toggle=True)
                rr = col.row(align=True)
                rr.active = 'ROUGHNESS' in textypes
                rr.prop(dm, "export_atlas_texture_smoothness", text="Smoothness", toggle=True)
                rr = col.row(align=True)
                rr.active = all(textype in textypes for textype in ['SUBSET', 'AO'])
                rr.prop(dm, "export_atlas_texture_subset_occlusion", text="Subset Occlusion", toggle=True)

                col = r.column(align=True)
                rr = col.row(align=True)
                rr.active = 'AO' in textypes
                rr.prop(dm, "export_atlas_texture_ao", text="Ambient Occlusion", toggle=True)
                rr = col.row(align=True)
                rr.active = 'CURVATURE' in textypes
                rr.prop(dm, "export_atlas_texture_curvature", text="Curvature", toggle=True)
                rr = col.row(align=True)
                rr.active = 'HEIGHT' in textypes
                rr.prop(dm, "export_atlas_texture_height", text="Height", toggle=True)
                rr = col.row(align=True)
                rr.active = 'MATERIAL2' in textypes
                rr.prop(dm, "export_atlas_texture_material2", text="Material 2", toggle=True)
                rr = col.row(align=True)
                rr.active = 'ROUGHNESS' in textypes
                rr.prop(dm, "export_atlas_texture_roughness", text="Roughness", toggle=True)
                rr = col.row(align=True)
                rr.active = 'SUBSET' in textypes
                rr.prop(dm, "export_atlas_texture_subset", text="Subset", toggle=True)
                rr = col.row(align=True)
                rr.active = 'HEIGHT' in textypes
                rr.prop(dm, "export_atlas_texture_white_height", text="White Height", toggle=True)


                row = b.split(factor=0.25)
                row.label(text="Channel Packed")

                r = row.row()

                col = r.column()
                col.template_list("MACHIN3_UL_atlas_channel_pack", "", dm, "export_atlas_texture_channel_packCOL", dm, "export_atlas_texture_channel_packIDX", rows=max(len(dm.export_atlas_texture_channel_packCOL), 2))

                col = r.column()
                col.operator("machin3.add_atlas_channel_pack", text="", icon_value=get_icon('plus'))
                col.operator("machin3.remove_atlas_channel_pack", text="", icon_value=get_icon('cancel'))

            else:

                col = b.column()
                row = col.split(factor=0.1)
                row.separator()
                row.label(text="No atlased Decals %s!" % ('selected' if context.selected_objects else 'visible'), icon='INFO')

        if dm.export_atlas_models:
            b = column.box()
            b.label(text="Models")

            row = b.split(factor=0.25)
            row.label(text="Format")
            r = row.row()
            r.prop(dm, 'export_atlas_model_format', expand=True)

            if dm.export_atlas_model_format == 'FBX':
                activate_unity = getattr(m3prefs, 'activate_unity', None)

                if activate_unity:
                    col = b.column(align=True)

                    row = col.split(factor=0.25)
                    row.label(text="Unity")
                    row.prop(dm, 'export_atlas_model_unity', text='True' if dm.export_atlas_model_unity else 'False', toggle=True)

                    if dm.export_atlas_model_unity:
                        self.draw_machin3tools_unity_export(context, col)

        row = column.row()
        row.scale_y = 1.5
        row.operator("machin3.export_atlas_decals", text="Export")

    def draw_join_button(self, context, dm, layout):
        box = layout.box()
        box.label(text="Join & Split")

        column = box.column(align=True)
        column.scale_y = 1.2
        row = column.split(factor=0.7, align=True)
        row.operator("machin3.join_atlased_decals", text="Join Atlased Decals")

        r = row.row(align=True)
        r.active = True if [obj for obj in context.visible_objects if obj.DM.isdecal and obj.DM.preatlasmats] else False
        r.prop(dm, "export_atlas_join_atlased_per_parent", text="per Parent", toggle=True)
        column.operator("machin3.split_atlased_decals", text="Split Atlased Decals")

    def draw_use_atlas_button(self, layout):
        column = layout.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator("machin3.use_atlas", text="Use %s" % ("Atlases" if sum(atlas.isenabled for atlas in get_atlas()[1]) > 1 else "Atlas"))
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.restore_preatlas_decal_materials", text="Restore Pre-Atlas Decal UVs + Materials")

    def draw_decal_atlases(self, layout):
        layout.label(text="Decal Atlases")

        column = layout.column()

        row = column.row()

        col = row.column()
        prefs = get_prefs()
        col.template_list("MACHIN3_UL_export_atlases", "", prefs, "atlasesCOL", prefs, "atlasesIDX", rows=max(len(prefs.atlasesCOL), 6))

        col = row.column(align=True)
        col.operator("machin3.move_atlas", text="", icon="TRIA_UP").direction = "UP"
        col.operator("machin3.move_atlas", text="", icon="TRIA_DOWN").direction = "DOWN"
        col.separator()
        col.operator_context = "EXEC_DEFAULT"
        col.operator("wm.save_userpref", text="", icon_value=get_icon('save'))

    def draw_atlas_settings(self, dm, layout):
        row = layout.split(factor=0.5)
        row.label(text="Create Collections")
        row.prop(dm, "export_atlas_create_collections", text="True" if dm.export_atlas_create_collections else "False", toggle=True)



    def draw_bake_settings(self, context, dm, layout, targetcount):
        box = layout.box()
        box.label(text=f"Bake Settings ({context.scene.cycles.device})")

        row = box.split(factor=0.33)
        row.label(text="Anti Aliasing")
        col = row.column()
        r = col.row()
        r.prop(dm, "export_bake_supersample", expand=True)

        if int(dm.export_bake_supersample):
            row = box.split(factor=0.33)
            row.label(text="Attention", icon_value=get_icon('error'))
            col = row.column()

            if int(dm.export_bake_supersample) == 2:
                col.label(text="This significantly increases the render time!")
            elif int(dm.export_bake_supersample) == 4:
                col.label(text="This dramatically increases the render time!")

        row = box.split(factor=0.33)
        row.label(text="Resolution")
        split = row.split(factor=0.42, align=True)
        split.prop(dm, "export_bake_x", text='')
        s = split.split(factor=0.2, align=True)
        icon = 'LINKED' if dm.export_bake_linked_res else 'UNLINKED'
        s.prop(dm, "export_bake_linked_res", text='', icon=icon)
        r = s.row(align=True)
        r.active = not dm.export_bake_linked_res
        r.prop(dm, "export_bake_y", text='')

        row = box.split(factor=0.33)
        row.label(text="Properties")
        col = row.column()
        row = col.row(align=True)
        row.prop(dm, 'export_bake_samples')
        row.prop(dm, 'export_bake_margin')
        col.prop(dm, 'export_bake_distance', slider=True)
        col.prop(dm, 'export_bake_triangulate', toggle=True)

        row = box.split(factor=0.33)
        row.label(text="Maps")
        col = row.column(align=True)
        col.prop(dm, 'export_bake_color', toggle=True)
        col.prop(dm, 'export_bake_normal', toggle=True)
        col.prop(dm, 'export_bake_emission', toggle=True)
        col.prop(dm, 'export_bake_aocurvheight', toggle=True)
        col.prop(dm, 'export_bake_masks', toggle=True)

        row = box.split(factor=0.33)
        row.label(text="Post-Baking")
        col = row.column()
        if targetcount > 1:
            col.prop(dm, 'export_bake_combine_bakes')
        col.prop(dm, 'export_bake_preview')
        col.prop(dm, 'export_bake_open_folder')
        col.prop(dm, 'export_bake_substance_naming')

    def draw_bake_button(self, layout, restore=False):
        col = layout.column(align=True)

        row = col.row(align=True)
        row.scale_y = 1.5
        row.operator("machin3.bake_decals", text="Bake Decals")

        if restore:
            row = col.row(align=True)
            row.scale_y = 1.2
            row.operator("machin3.restore_pre_bakepreview_materials", text="Restore Materials + Decals")


class PanelUpdateDecals(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_update_decals"
    bl_label = "Update Decals & Trim Sheets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 3

    @classmethod
    def poll(cls, context):
        return context.scene.DM.register_panel_update

    def draw(self, context):
        layout = self.layout

        dm = context.scene.DM

        box = layout.box()

        legacylibs = get_legacy_libs()

        if any(legacylibs):
            b = box.box()
            column = b.column()

            count = sum([len(libs) for libs in legacylibs])

            if count == 1:
                text = 'Legacy Decal or Trim Sheet library detected!'
                optext = 'Update It!'

            else:
                text = 'Legacy Decal or Trim Sheet libraries detected!'
                optext = 'Update Them All!'

            column.label(text=text, icon='INFO')

            draw_pil_warning(column, needed="for library update")

            row = column.row()
            row.scale_y = 1.5
            row.operator("machin3.batch_update_decal_libraries", text=optext)

        column = box.column()
        row = column.row()
        row.label(text="Version")

        if bpy.app.version >= (3, 0, 0):
            row.prop(dm, "updatelibraryversion30", expand=True)

            if dm.updatelibraryversion30 == "18":
                self.draw_update_18(context, dm, box)

            elif dm.updatelibraryversion30 == "20":
                self.draw_update_20(context, dm, box)

            elif dm.updatelibraryversion30 == "21":
                self.draw_update_21(context, dm, box)

        else:
            row.prop(dm, "updatelibraryversion", expand=True)

            if dm.updatelibraryversion == "18":
                self.draw_update_18(context, dm, box)

            elif dm.updatelibraryversion == "20":
                self.draw_update_20(context, dm, box)

    def draw_update_21(self, context, dm, layout):
        box = layout.box()
        column = box.column()

        istrimsheet = dm.updatelibraryistrimsheet

        row = column.split(factor=0.33)
        row.label(text="Library Path")
        row.prop(context.scene.DM, "update21librarypath", text="")

        if not dm.updatelibraryinplace and not istrimsheet:
            if context.scene.userdecallibs:
                row = column.split(factor=0.33)
                row.label(text="User Decal Library")
                row.prop(context.scene, "userdecallibs", text="")
            else:
                column.label(text="Create a new Library or Unlock an existing one.")

        row = column.split(factor=0.33)
        row.label(text="Settings")

        col = row.column()

        row = col.row()
        assetspath = get_prefs().assetspath
        sourcepath = dm.update20librarypath

        row.active = False if os.path.dirname(sourcepath) == os.path.join(assetspath, 'Trims' if istrimsheet else 'Decals') else True
        row.prop(dm, "updatelibraryinplace")

        col.prop(dm, "update_keep_old_thumbnails")

        draw_pil_warning(box, needed="to update 2.1 - 2.4.1 Decal Libraries")

        if istrimsheet and not dm.updatelibraryinplace:
            sheetname = os.path.basename(context.scene.DM.update20librarypath)
            sheetlib = get_prefs().decallibsCOL.get(sheetname)

            if sheetlib and sheetlib.istrimsheet:
                column = box.column()
                column.label(text="A Trim Sheet of that name is already registered!", icon_value=get_icon('error'))

        column = box.column()

        row = column.row()
        row.scale_y = 1.5
        row.operator("machin3.update_21_decal_library", text="Update %s Library" % ('Trim Decal' if istrimsheet else 'Decal'))

        box = layout.box()
        column = box.column()
        column.label(text="Current File")

        row = column.row()
        row.scale_y = 1.5
        row.operator("machin3.update_21_blend_file", text="Decals & Trims in current .blend")

    def draw_update_20(self, context, dm, layout):
        box = layout.box()
        column = box.column()

        istrimsheet = dm.updatelibraryistrimsheet

        row = column.split(factor=0.33)
        row.label(text="Library Path")
        row.prop(context.scene.DM, "update20librarypath", text="")

        if not dm.updatelibraryinplace and not istrimsheet:
            if context.scene.userdecallibs:
                row = column.split(factor=0.33)
                row.label(text="User Decal Library")
                row.prop(context.scene, "userdecallibs", text="")
            else:
                column.label(text="Create a new Library or Unlock an existing one.")

        row = column.split(factor=0.33)
        row.label(text="Settings")

        col = row.column()

        row = col.row()
        assetspath = get_prefs().assetspath
        sourcepath = dm.update20librarypath

        row.active = False if os.path.dirname(sourcepath) == os.path.join(assetspath, 'Trims' if istrimsheet else 'Decals') else True
        row.prop(dm, "updatelibraryinplace")

        col.prop(dm, "update_keep_old_thumbnails")

        draw_pil_warning(box, needed="to update 2.0 - 2.0.1 Decal Libraries")

        if istrimsheet and not dm.updatelibraryinplace:
            sheetname = os.path.basename(context.scene.DM.update20librarypath)
            sheetlib = get_prefs().decallibsCOL.get(sheetname)

            if sheetlib and sheetlib.istrimsheet:
                column = box.column()
                column.label(text="A Trim Sheet of that name is already registered!", icon_value=get_icon('error'))

        column = box.column()

        row = column.row()
        row.scale_y = 1.5
        row.operator("machin3.update_20_decal_library", text="Update %s Library" % ('Trim Decal' if istrimsheet else 'Decal'))

        box = layout.box()
        column = box.column()
        column.label(text="Current File")

        row = column.row()
        row.scale_y = 1.5
        row.operator("machin3.update_20_blend_file", text="Update Decals & Trims in current .blend")

    def draw_update_18(self, context, dm, layout):
        box = layout.box()
        column = box.column()

        row = column.split(factor=0.33)
        row.label(text="Library Path")
        row.prop(context.scene.DM, "update18librarypath", text="")

        if not dm.updatelibraryinplace:
            if context.scene.userdecallibs:
                row = column.split(factor=0.33)
                row.label(text="User Decal Library")
                row.prop(context.scene, "userdecallibs", text="")
            else:
                column.label(text="Create a new Library or Unlock an existing one.")

        row = column.split(factor=0.33)
        row.label(text="Settings")

        col = row.column()

        row = col.row()
        assetspath = get_prefs().assetspath
        sourcepath = dm.update18librarypath

        row.active = False if os.path.dirname(sourcepath) == os.path.join(assetspath, 'Decals') else True
        row.prop(dm, "updatelibraryinplace")

        col.prop(dm, "update_keep_old_thumbnails")

        draw_pil_warning(box, needed="to update 1.8 - 1.9 Decal Libraries")

        column = box.column()

        row = column.row()
        row.scale_y = 1.5
        row.operator("machin3.update_18_decal_library", text="Update Decal Library")

        box = layout.box()
        column = box.column()
        column.label(text="Current File")

        row = column.row()
        row.scale_y = 1.5
        row.operator("machin3.update_18_blend_file", text="Update Decals in current .blend")


class PanelHelp(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_help_decal_machine"
    bl_label = "DECALmachine Help"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 4

    @classmethod
    def poll(cls, context):
        return context.scene.DM.register_panel_help

    def draw(self, context):
        layout = self.layout

        resources_path = os.path.join(get_path(), "resources")
        example_decal_basics_path = os.path.join(resources_path, "Example_Decal_Basics.blend")
        example_decal_creation_path = os.path.join(resources_path, "Example_Decal_Creation.blend")
        example_decal_bake_path = os.path.join(resources_path, "Example_Decal_Bake.blend")
        example_decal_asset_path = os.path.join(resources_path, "Example_Decal_Asset.blend")

        example_trimsheet_geometry_path = os.path.join(resources_path, "Example_Trim_Sheet_Geometry.blend")
        example_trimsheet_setup_path = os.path.join(resources_path, "Example_Trim_Sheet_Setup.blend")
        example_trimsheet_asset_path = os.path.join(resources_path, "Example_Trim_Sheet_Asset.blend")


        box = layout.box()
        box.label(text="Help")



        b = box.box()
        b.label(text="Documentation")
        column = b.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Local", icon='FILE_BACKUP').url = os.path.join(get_path(), "docs", "index.html")
        row.operator("wm.url_open", text="Online", icon='FILE_BLEND').url = "https://machin3.io/DECALmachine/docs"

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="FAQ", icon='QUESTION').url = "https://machin3.io/DECALmachine/docs/faq"
        row.operator("wm.url_open", text="Youtube", icon='FILE_MOVIE').url = "https://www.youtube.com/playlist?list=PLcEiZ9GDvSdWiU2BPQp99HglGGg1OGiHs"



        b = box.box()
        b.label(text="Support")
        column = b.column()

        row = column.row()
        row.scale_y = 1.5
        row.operator("machin3.get_decalmachine_support", text="Get Support", icon='GREASEPENCIL')



        b = box.box()
        b.label(text="Examples")

        column = b.column(align=True)

        if bpy.data.is_dirty:
            column.label(text="Your current file is not saved!", icon="ERROR")
            column.label(text="Unsaved changes will be lost,", icon="BLANK1")
            column.label(text="if you load the following examples.", icon="BLANK1")

        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator_context = 'EXEC_DEFAULT'
        op = row.operator("wm.open_mainfile", text="Decal Basics", icon="FILE_FOLDER")
        op.filepath = example_decal_basics_path
        op.load_ui = True

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator_context = 'EXEC_DEFAULT'
        op = row.operator("wm.open_mainfile", text="Create Decals", icon="FILE_FOLDER")
        op.filepath=example_decal_creation_path
        op.load_ui = True
        op = row.operator("wm.open_mainfile", text="Bake Decals", icon="FILE_FOLDER")
        op.filepath = example_decal_bake_path
        op.load_ui = True

        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator_context = 'EXEC_DEFAULT'
        op = row.operator("wm.open_mainfile", text="Decal Demo Asset", icon="FILE_FOLDER")
        op.filepath = example_decal_asset_path
        op.load_ui = True

        column = b.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator_context = 'EXEC_DEFAULT'
        op = row.operator("wm.open_mainfile", text="Trim Sheet Geometry", icon="FILE_FOLDER")
        op.filepath = example_trimsheet_geometry_path

        op.load_ui = True
        op = row.operator("wm.open_mainfile", text="Trim Sheet Setup", icon="FILE_FOLDER")
        op.filepath = example_trimsheet_setup_path
        op.load_ui = True

        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator_context = 'EXEC_DEFAULT'
        op = row.operator("wm.open_mainfile", text="Trim Sheet Demo Asset", icon="FILE_FOLDER")
        op.filepath = example_trimsheet_asset_path
        op.load_ui = True


        column = b.column(align=True)
        column.label(text="Please refer to the documentation", icon='INFO')
        column.label(text="for details on Trim Sheet and Atlas Creation")



        b = box.box()
        b.label(text="Decal Resources")
        column = b.column()

        row = column.row()
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Decal Packs", icon='RENDER_RESULT').url = "https://machin3.io/DECALmachine/docs/decal_resources"



        b = box.box()
        b.label(text="Discuss")
        column = b.column()

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Blender Artists", icon="COMMUNITY").url = "https://blenderartists.org/t/decalmachine/688181"
        row.operator("wm.url_open", text="polycount", icon="COMMUNITY").url = "https://polycount.com/discussion/210294/blender-decalmachine-surface-detailing-using-mesh-decals"



        b = box.box()
        b.label(text="Follow Development")
        column = b.column()
        column.label(text='Twitter')

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="@machin3io").url = "https://twitter.com/machin3io"
        row.operator("wm.url_open", text="#DECALmachine").url = "https://twitter.com/search?q=(%23DECALmachine)%20(from%3Amachin3io)&src=typed_query&f=live"

        column.label(text='Youtube')
        row = column.row()
        row.scale_y = 1.2
        row.operator("wm.url_open", text="MACHIN3").url = "https://www.youtube.com/c/MACHIN3"



class PanelMaterial(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_material_decal_machine"
    bl_label = "Trim Sheet"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        return poll_trimsheetlibs()

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        col = column.column(align=True)
        col.scale_y = 1.2
        col.prop(context.scene, "trimsheetlibs", text='')
        col.operator('machin3.init_trimsheet_mat', text='Init Trim Sheet Material')

        column.separator()
        row = column.row()
        row.scale_y = 1.2
        row.operator('machin3.setup_trimsheet_subsets', text='Setup Subsets')



def draw_debug(self, context):
    layout = self.layout

    layout.separator()
    layout.operator("machin3.decalmachine_debug")
