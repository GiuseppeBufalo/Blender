import bpy
from .. utils.asset import get_asset_ids, get_assetbrowser_bookmarks, get_libref_and_catalog
from .. utils.group import get_group_polls
from .. utils.object import is_instance_collection
from .. utils.registration import get_prefs, get_addon
from .. utils.ui import get_icon

hypercursor = None

class MenuMACHIN3toolsObjectContextMenu(bpy.types.Menu):
    bl_idname = "MACHIN3_MT_machin3tools_object_context_menu"
    bl_label = "MACHIN3tools"

    def draw(self, context):
        global hypercursor

        if hypercursor is None:
            hypercursor = get_addon('HyperCursor')[0]

        layout = self.layout
        p = get_prefs()

        if p.activate_align:
            layout.operator("machin3.align_relative", text="Align Relative")

        if p.activate_mirror:
            layout.operator("machin3.unmirror", text="Un-Mirror")

        if p.activate_select:
            layout.operator("machin3.select_center_objects", text="Select Center Objects")
            layout.operator("machin3.select_wire_objects", text="Select Wire Objects")
            layout.operator("machin3.select_hierarchy", text="Select Hierarchy")

        if p.activate_apply:
            layout.operator("machin3.apply_transformations", text="Apply Transformations")

        if p.activate_mesh_cut:
            layout.operator("machin3.mesh_cut", text="Mesh Cut")

        if p.activate_material_picker:
            layout.operator("machin3.material_picker", text="Material Picker", icon='EYEDROPPER')

class MenuMACHIN3toolsMeshContextMenu(bpy.types.Menu):
    bl_idname = "MACHIN3_MT_machin3tools_mesh_context_menu"
    bl_label = "MACHIN3tools"

    def draw(self, context):
        layout = self.layout

        if get_prefs().activate_thread:
            layout.operator("machin3.add_thread", text="Add Thread")

class MenuGroupObjectContextMenu(bpy.types.Menu):
    bl_idname = "MACHIN3_MT_group_object_context_menu"
    bl_label = "Group"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"

        m3 = context.scene.M3

        active_group, active_child, group_empties, groupable, ungroupable, addable, removable, selectable, duplicatable, groupifyable = get_group_polls(context)

        row = layout.row()
        row.active = group_empties
        row.prop(m3, "group_select")

        row = layout.row()
        row.active = group_empties
        row.prop(m3, "group_recursive_select")

        row = layout.row()
        row.active = group_empties
        row.prop(m3, "group_hide")

        layout.separator()

        row = layout.row()
        row.active = groupable
        row.operator("machin3.group", text="Group")

        row = layout.row()
        row.active = ungroupable
        row.operator("machin3.ungroup", text="Un-Group")

        row = layout.row()
        row.active = groupifyable
        row.operator("machin3.groupify", text="Groupify")

        layout.separator()

        row = layout.row()
        row.active = selectable
        row.operator("machin3.select_group", text="Select Group")

        row = layout.row()
        row.active = duplicatable
        row.operator("machin3.duplicate_group", text="Duplicate Group")

        layout.separator()

        row = layout.row()
        row.active = addable and (active_group or active_child)
        row.operator("machin3.add_to_group", text="Add to Group")

        row = layout.row()
        row.active = removable
        row.operator("machin3.remove_from_group", text="Remove from Group")

def object_context_menu(self, context):
    layout = self.layout
    m3 = context.scene.M3
    p = get_prefs()

    if p.activate_material_picker and p.matpick_draw_in_top_level_context_menu:
        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("machin3.material_picker", text="Material Picker", icon="EYEDROPPER").is_keymap = False
        layout.operator_context = "EXEC_REGION_WIN"

    if any([p.activate_align, p.activate_mirror, p.activate_select, p.activate_apply, p.activate_mesh_cut, p.activate_material_picker and not p.matpick_draw_in_top_level_context_menu]):
        layout.menu("MACHIN3_MT_machin3tools_object_context_menu")
        layout.separator()

    if p.activate_group:

        if p.use_group_sub_menu:
            layout.menu("MACHIN3_MT_group_object_context_menu")
            layout.separator()

        else:
            active_group, active_child, group_empties, groupable, ungroupable, addable, removable, selectable, duplicatable, groupifyable = get_group_polls(context)

            if group_empties and any([m3.show_group_select, m3.show_group_recursive_select, m3.show_group_hide]):
                if m3.show_group_select:
                    layout.prop(m3, "group_select")

                if m3.show_group_recursive_select:
                    layout.prop(m3, "group_recursive_select")

                if m3.show_group_hide:
                    layout.prop(m3, "group_hide")

                if groupable or group_empties or selectable or duplicatable or groupifyable or (addable and (active_group or active_child)) or removable:

                    row = layout.row()
                    row.scale_y = 0.3
                    row.label(text="")

            if groupable:
                layout.operator_context = "INVOKE_REGION_WIN"
                layout.operator("machin3.group", text="Group")
                layout.operator_context = "EXEC_REGION_WIN"

            if ungroupable:
                layout.operator_context = "INVOKE_REGION_WIN"
                layout.operator("machin3.ungroup", text="(X) Un-Group")
                layout.operator_context = "EXEC_REGION_WIN"

            if groupifyable:
                layout.operator("machin3.groupify", text="Groupify")

            if selectable:
                row = layout.row()
                row.scale_y = 0.3
                row.label(text="")

                layout.operator_context = "INVOKE_REGION_WIN"
                layout.operator("machin3.select_group", text="Select Group")
                layout.operator_context = "EXEC_REGION_WIN"

            if duplicatable:

                if not selectable:
                    row = layout.row()
                    row.scale_y = 0.3
                    row.label(text="")

                layout.operator_context = "INVOKE_REGION_WIN"
                layout.operator("machin3.duplicate_group", text="Duplicate Group")
                layout.operator_context = "EXEC_REGION_WIN"

            if (addable and (active_group or active_child)) or removable:

                row = layout.row()
                row.scale_y = 0.3
                row.label(text="")

                layout.operator_context = "INVOKE_REGION_WIN"
                if addable and (active_group or active_child):
                    layout.operator("machin3.add_to_group", text="Add to Group")

                if removable:
                    layout.operator("machin3.remove_from_group", text="Remove from Group")
                layout.operator_context = "EXEC_REGION_WIN"

            if group_empties or groupable or (addable and (active_group or active_child)) or removable or groupifyable:
                layout.separator()

def mesh_context_menu(self, context):
    layout = self.layout
    p = get_prefs()

    if p.activate_material_picker and p.matpick_draw_in_top_level_context_menu:
        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("machin3.material_picker", text="Material Picker", icon="EYEDROPPER").is_keymap = False
        layout.operator_context = "EXEC_REGION_WIN"

    if any([p.activate_thread]):
        layout.menu("MACHIN3_MT_machin3tools_mesh_context_menu")
        layout.separator()

def add_object_buttons(self, context):
    self.layout.operator("machin3.quadsphere", text="Quad Sphere", icon='SPHERE')

def extrude_menu(self, context):
    is_cursor_spin = getattr(bpy.types, 'MACHIN3_OT_cursor_spin', False)
    is_punch_it = getattr(bpy.types, 'MACHIN3_OT_punch_it_a_little', False)
    is_punchit = getattr(bpy.types, 'MACHIN3_OT_punchit', False)

    if any([is_cursor_spin, is_punch_it]):
        self.layout.separator()

        if is_cursor_spin:
            self.layout.operator("machin3.cursor_spin", text="Cursor Spin")

        if is_punch_it and not is_punchit:
            self.layout.operator("machin3.punch_it_a_little", text="Punch It (a little)", icon_value=get_icon('fist'))

def material_pick_button(self, context):
    p = get_prefs()

    workspaces = [ws.strip() for ws in p.matpick_workspace_names.split(',')]
    shading = context.space_data.shading

    view_shading_types = []
    if p.matpick_shading_type_material:
        view_shading_types.append('MATERIAL')

    if p.matpick_shading_type_render:
        view_shading_types.append('RENDERED')

    if shading.type == 'SOLID' and shading.color_type == 'MATERIAL':
        view_shading_types.append('SOLID')

    if any([s in context.workspace.name for s in workspaces]) or shading.type in view_shading_types:
        if getattr(bpy.types, 'MACHIN3_OT_material_picker', False):
            row = self.layout.row()
            row.scale_x = 1.25
            row.scale_y = 1.1
            row.separator(factor=p.matpick_spacing_obj if context.mode == 'OBJECT' else p.matpick_spacing_edit)
            row.operator("machin3.material_picker", text="", icon="EYEDROPPER").is_keymap = False

def asset_browser_bookmark_buttons(self, context):
    p = get_prefs()

    if p.activate_assetbrowser_tools:

        current_libref, current_catalog_id, current_catalog = get_libref_and_catalog(context)
        
        bookmarks = get_assetbrowser_bookmarks()

        self.layout.separator(factor=1)
        row = self.layout.row(align=True)

        r = row.row(align=True)
        r.scale_x = 1.3
        is_current = current_libref == 'LOCAL'
        r.operator("machin3.assetbrowser_bookmark", text='', depress=is_current, icon='FILE_BLEND').index = 0

        for idx in range(10):
            bookmark = bookmarks[str(idx + 1)]

            libref = bookmark['libref']
            catalog_id = bookmark['catalog_id']
            valid = bookmark['valid']

            is_current = libref == current_libref and catalog_id == current_catalog_id
            is_available = bool(libref and catalog_id)
            is_invalid = is_available and not valid

            r = row.row(align=True)
            r.scale_x = 0.8
            r.active = is_available
            r.alert = is_invalid
            r.operator("machin3.assetbrowser_bookmark", text=str(idx + 1), depress=is_current).index = idx + 1

        icon = 'IMGDISPLAY' if (display_type := context.space_data.params.display_type) == 'THUMBNAIL' else 'SHORTDISPLAY' if display_type == 'LIST_HORIZONTAL' else 'LONGDISPLAY'

        row.separator()
        r = row.row()
        r.scale_x = 1.5
        r.operator('machin3.filebrowser_toggle', text='', icon=icon).type = 'DISPLAY_TYPE'
        
        if not context.space_data.show_region_toolbar:
            libref = current_libref.replace('LOCAL', 'Current File').title()

            if current_catalog:
                text = f"{libref} - {current_catalog['catalog']}"
                row.label(text=text, icon="RIGHTARROW_THIN")

            elif libref:
                row.label(text=libref, icon="RIGHTARROW_THIN")

def asset_browser_metadata(self, context):
    p = get_prefs()

    if p.activate_assetbrowser_tools:
        active, id_type, local_id = get_asset_ids(context)

        if local_id and is_instance_collection(local_id):
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # says "No animation." in space_filebrowser.py, but leaving it out here causes an odd negative indent/offset

            layout.prop(local_id.instance_collection, "name", text="Collection Name")

def asset_browser_update_thumbnail(self, context):
    p = get_prefs()

    if p.activate_assetbrowser_tools:
        active, id_type, local_id = get_asset_ids(context)

        if active and id_type == 'OBJECT' and local_id:
            layout = self.layout
            layout.operator("machin3.update_asset_thumbnail", text='Update Thumbnail')

def outliner_group_toggles(self, context):
    if getattr(bpy.types, 'MACHIN3_OT_group', False) and get_prefs().use_group_outliner_toggles:

        if get_group_polls(context)[2]:
            m3 = context.scene.M3
            self.layout.prop(m3, "group_select", text='', icon='GROUP_VERTEX')
            self.layout.prop(m3, "group_recursive_select", text='', icon='CON_SIZELIKE')
            self.layout.prop(m3, "group_hide", text='', icon='HIDE_ON' if m3.group_hide else 'HIDE_OFF', emboss=False)

def group_origin_adjustment_toggle(self, context):
    if get_prefs().activate_group:
        m3 = context.scene.M3

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        heading = 'Disable, when done!' if m3.affect_only_group_origin else ''
        column = layout.column(heading=heading, align=True)

        if (context.active_object and context.active_object.M3.is_group_empty) or m3.affect_only_group_origin:
            column.prop(m3, "affect_only_group_origin", text="Group Origin")

def render_menu(self, context):
    if getattr(bpy.types, 'MACHIN3_OT_render', False):
        layout = self.layout

        layout.separator()

        op = layout.operator("machin3.render", text="Quick Render")
        op.seed = False
        op.final = False

        op = layout.operator("machin3.render", text="Final Render")
        op.seed = False
        op.final = True

        row = layout.row()
        row.scale_y = 0.3
        row.label(text='')

        row = layout.row()
        row.active = True if context.scene.camera else False
        row.prop(get_prefs(), 'render_seed_count', text="Seed Count")

        op = layout.operator("machin3.render", text="Seed Render")
        op.seed = True
        op.final = False

        op = layout.operator("machin3.render", text="Final Seed Render")
        op.seed = True
        op.final = True

def render_buttons(self, context):
    if getattr(bpy.types, 'MACHIN3_OT_render', False) and get_prefs().render_show_buttons_in_light_properties and context.scene.camera:
        layout = self.layout

        column = layout.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        op = row.operator("machin3.render", text="Quick Render")
        op.seed = False
        op.final = False

        op = row.operator("machin3.render", text="Final Render")
        op.seed = False
        op.final = True

        column.separator()

        row = column.row(align=True)
        row.active = True if context.scene.camera else False
        row.prop(get_prefs(), 'render_seed_count', text="Seed Render Count")

        row = column.row(align=True)
        row.scale_y = 1.2
        op = row.operator("machin3.render", text="Seed Render")
        op.seed = True
        op.final = False

        op = row.operator("machin3.render", text="Final Seed Render")
        op.seed = True
        op.final = True
