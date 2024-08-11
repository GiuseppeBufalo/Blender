import bpy
from .. utils.asset import is_local_assembly_asset
from .. utils.collection import get_instance_collections_recursively, is_instance_collection
from .. utils.group import get_group_base_name, get_group_polls
from .. utils.registration import get_prefs
from .. utils.ui import get_icon
from .. import bl_info

class PanelMACHIN3tools(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_machin3_tools"
    bl_label = "MACHIN3tools %s" % ('.'.join([str(v) for v in bl_info['version']]))
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 20

    @classmethod
    def poll(cls, context):
        p = get_prefs()

        if p.show_sidebar_panel:
            if context.mode == 'OBJECT':
                return p.activate_smart_drive or p.activate_unity or p.activate_group or p.activate_assetbrowser_tools
            elif context.mode == 'EDIT_MESH':
                return p.activate_extrude

    def draw(self, context):
        layout = self.layout

        m3 = context.scene.M3
        p = get_prefs()

        if context.mode == 'OBJECT':

            if p.activate_smart_drive:
                box = layout.box()
                box.prop(m3, "show_smart_drive", text="Smart Drive", icon='TRIA_DOWN' if m3.show_smart_drive else 'TRIA_RIGHT', emboss=False)

                if m3.show_smart_drive:
                    self.draw_smart_drive(m3, box)

            if p.activate_unity:
                box = layout.box()

                box.prop(m3, "show_unity", text="Unity", icon='TRIA_DOWN' if m3.show_unity else 'TRIA_RIGHT', emboss=False)

                if m3.show_unity:
                    self.draw_unity(context, m3, box)

            if p.activate_group:
                box = layout.box()

                box.prop(m3, "show_group", text="Group", icon='TRIA_DOWN' if m3.show_group else 'TRIA_RIGHT', emboss=False)

                if m3.show_group:
                    self.draw_group(context, m3, box)

            if p.activate_assetbrowser_tools:
                box = layout.box()

                box.prop(m3, "show_assetbrowser_tools", text="Assetbrowser Tools", icon='TRIA_DOWN' if m3.show_assetbrowser_tools else 'TRIA_RIGHT', emboss=False)

                if m3.show_assetbrowser_tools:
                    self.draw_assetbrowser_tools(context, box)

        elif context.mode == 'EDIT_MESH':

            if p.activate_extrude:
                box = layout.box()

                box.prop(m3, "show_extrude", text="Extrude", icon='TRIA_DOWN' if m3.show_extrude else 'TRIA_RIGHT', emboss=False)

                if m3.show_extrude:
                    self.draw_extrude(context, m3, box)

        if bpy.ops.machin3.m3_debug.poll():
            layout.separator()
            column = layout.column()
            column.scale_y = 2
            column.operator('machin3.m3_debug', text='Button')

    def draw_smart_drive(self, m3, layout):
        column = layout.column()

        b = column.box()
        b.label(text="Driver")

        col = b.column(align=True)

        row = col.split(factor=0.25, align=True)
        row.label(text="Values")
        r = row.row(align=True)
        op = r.operator("machin3.set_driver_value", text='', icon='SORT_ASC')
        op.mode = 'DRIVER'
        op.value = 'START'
        r.prop(m3, 'driver_start', text='')
        r.operator("machin3.switch_driver_values", text='', icon='ARROW_LEFTRIGHT').mode = 'DRIVER'
        r.prop(m3, 'driver_end', text='')
        op = r.operator("machin3.set_driver_value", text='', icon='SORT_ASC')
        op.mode = 'DRIVER'
        op.value = 'END'

        row = col.split(factor=0.25, align=True)
        row.label(text="Transform")
        r = row.row(align=True)
        r.prop(m3, 'driver_transform', expand=True)

        row = col.split(factor=0.25, align=True)
        row.scale_y = 0.9
        row.label(text="Axis")
        r = row.row(align=True)
        r.prop(m3, 'driver_axis', expand=True)

        row = col.split(factor=0.25, align=True)
        row.label(text="Space")
        r = row.row(align=True)
        r.prop(m3, 'driver_space', expand=True)

        b = column.box()
        b.label(text="Driven")

        col = b.column(align=True)

        row = col.split(factor=0.25, align=True)
        row.label(text="Values")
        r = row.row(align=True)
        op = r.operator("machin3.set_driver_value", text='', icon='SORT_ASC')
        op.mode = 'DRIVEN'
        op.value = 'START'
        r.prop(m3, 'driven_start', text='')
        r.operator("machin3.switch_driver_values", text='', icon='ARROW_LEFTRIGHT').mode = 'DRIVEN'
        r.prop(m3, 'driven_end', text='')
        op = r.operator("machin3.set_driver_value", text='', icon='SORT_ASC')
        op.mode = 'DRIVEN'
        op.value = 'END'

        row = col.split(factor=0.25, align=True)
        row.label(text="Transform")
        r = row.row(align=True)
        r.prop(m3, 'driven_transform', expand=True)

        row = col.split(factor=0.25, align=True)
        row.scale_y = 0.9
        row.label(text="Axis")
        r = row.row(align=True)
        r.prop(m3, 'driven_axis', expand=True)

        row = col.split(factor=0.25, align=True)
        row.label(text="Limit")
        r = row.row(align=True)
        r.prop(m3, 'driven_limit', expand=True)

        r = column.row()
        r.scale_y = 1.2
        r.operator("machin3.smart_drive", text='Drive it!', icon='AUTO')

    def draw_unity(self, context, m3, layout):
        all_prepared = True if context.selected_objects and all([obj.M3.unity_exported for obj in context.selected_objects]) else False

        column = layout.column(align=True)

        row = column.split(factor=0.3)
        row.label(text="Export")
        row.prop(m3, 'unity_export', text='True' if m3.unity_export else 'False', toggle=True)

        row = column.split(factor=0.3)
        row.label(text="Triangulate")
        row.prop(m3, 'unity_triangulate', text='True' if m3.unity_triangulate else 'False', toggle=True)

        column.separator()

        if m3.unity_export:
            column.prop(m3, 'unity_export_path', text='')

            if all_prepared:
                row = column.row(align=True)
                row.scale_y = 1.5

                if m3.unity_export_path:
                    row.operator_context = 'EXEC_DEFAULT'

                op = row.operator("export_scene.fbx", text='Export')
                op.use_selection = True
                op.apply_scale_options = 'FBX_SCALE_ALL'

                if m3.unity_export_path:
                    op.filepath = m3.unity_export_path

        if not m3.unity_export or not all_prepared:
            row = column.row(align=True)
            row.scale_y = 1.5
            row.operator("machin3.prepare_unity_export", text="Prepare + Export %s" % ('Selected' if context.selected_objects else 'Visible') if m3.unity_export else "Prepare %s" % ('Selected' if context.selected_objects else 'Visible')).prepare_only = False

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.restore_unity_export", text="Restore Transformations")

    def draw_group(self, context, m3, layout):
        column = layout.column(align=True)
        p = get_prefs()

        active_group, active_child, group_empties, groupable, ungroupable, addable, removable, selectable, duplicatable, groupifyable = get_group_polls(context)

        box = layout.box()

        if group_empties:

            if active_group:
                empty = context.active_object

                prefix, basename, suffix = get_group_base_name(empty.name)

                b = box.box()
                b.label(text='Active Group')

                row = b.row(align=True)
                row.alignment = 'LEFT'
                row.label(text='', icon='SPHERE')

                if prefix:
                    r = row.row(align=True)
                    r.alignment = 'LEFT'
                    r.active = False
                    r.label(text=prefix)

                r = row.row(align=True)
                r.alignment = 'LEFT'
                r.active = True
                r.label(text=basename)

                if suffix:
                    r = row.row(align=True)
                    r.alignment = 'LEFT'
                    r.active = False
                    r.label(text=suffix)

                row = b.row()
                row.scale_y = 1.25

                if m3.affect_only_group_origin:
                    row.prop(m3, "affect_only_group_origin", text="Disable, when done!", toggle=True, icon_value=get_icon('error'))
                else:
                    row.prop(m3, "affect_only_group_origin", text="Adjust Group Origin", toggle=True, icon='OBJECT_ORIGIN')

        b = box.box()
        b.label(text='Settings')

        column = b.column(align=True)

        row = column.split(factor=0.3, align=True)
        row.label(text="Auto Select")
        r = row.row(align=True)

        if not p.use_group_sub_menu:
            r.prop(m3, 'show_group_select', text='', icon='HIDE_OFF' if m3.show_group_select else 'HIDE_ON')

        r.prop(m3, 'group_select', text='True' if m3.group_select else 'False', toggle=True)

        row = column.split(factor=0.3, align=True)
        row.label(text="Recursive")
        r = row.row(align=True)

        if not p.use_group_sub_menu:
            r.prop(m3, 'show_group_recursive_select', text='', icon='HIDE_OFF' if m3.show_group_recursive_select else 'HIDE_ON')

        r.prop(m3, 'group_recursive_select', text='True' if m3.group_recursive_select else 'False', toggle=True)

        row = column.split(factor=0.3, align=True)
        row.label(text="Hide Empties")
        r = row.row(align=True)

        if not p.use_group_sub_menu:
            r.prop(m3, 'show_group_hide', text='', icon='HIDE_OFF' if m3.show_group_hide else 'HIDE_ON')

        r.prop(m3, 'group_hide', text='True' if m3.group_hide else 'False', toggle=True)

        b = box.box()
        b.label(text='Tools')

        column = b.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        r = row.row(align=True)
        r.active = groupable
        r.operator("machin3.group", text="Group")
        r = row.row(align=True)
        r.active = ungroupable
        r.operator("machin3.ungroup", text="Un-Group")
        r = row.row(align=True)

        row = column.row(align=True)
        row.scale_y = 1
        r.active = groupifyable
        row.operator("machin3.groupify", text="Groupify")

        column.separator()
        column = column.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        r = row.row(align=True)
        r.active = selectable
        r.operator("machin3.select_group", text="Select Group")
        r = row.row(align=True)
        r.active = duplicatable
        r.operator("machin3.duplicate_group", text="Duplicate Group")

        column = column.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        r = row.row(align=True)
        r.active = addable and (active_group or active_child)
        r.operator("machin3.add_to_group", text="Add to Group")
        r = row.row(align=True)
        r.active = removable
        r.operator("machin3.remove_from_group", text="Remove from Group")

    def draw_extrude(self, context, m3, layout):
        column = layout.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.cursor_spin", text='Cursor Spin')
        row.operator("machin3.punch_it_a_little", text='Punch It (a little)', icon_value=get_icon('fist'))

    def draw_assetbrowser_tools(self, context, layout):
        active = context.active_object
        col = None

        is_linked = bool(active and active.library)
        is_assembly = bool(active and (col := is_instance_collection(active)))
        is_local_asset = bool(active and (asset := is_local_assembly_asset(active)))

        if is_assembly:
            box = layout.box()
            column = box.column(align=True)

            icols = {}
            get_instance_collections_recursively(icols, col)

            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="Assembly") 

            if is_local_asset:
                r = row.row(align=False)
                r.active = False
                r.alignment = 'LEFT'
                r.label(text=f"is {'recursive ' if icols else''}Local Asset Instance")

                if asset.preview:
                    row = column.row(align=True)
                    row.template_icon(icon_value=asset.preview.icon_id, scale=15)

                    row = column.row(align=True)
                    row.scale_y = 1.2
                    row.operator("machin3.update_asset_thumbnail", text='Update Thumbnail')
                    column.separator()

            elif icols or is_linked:
                r = row.row(align=False)
                r.active = False

                if icols and is_linked:
                    r.label(text="is recursive and linked")
                elif icols:
                    r.label(text="is recursive")
                else:
                    r.label(text="is linked")

            split = column.split(factor=0.3, align=True)
            split.enabled = is_local_asset
            row = split.row()
            row.active = False
            row.alignment = 'RIGHT'
            row.label(text="Asset Collection")
            split.prop(col, 'name', text='')

            split = column.split(factor=0.3, align=True)
            row = split.row()
            row.active = False
            row.alignment = 'RIGHT'

            if is_local_asset:
                row.label(text="Asset Name")
                split.prop(asset, 'name', text='')

            else:
                row.label(text="Instance Name")
                split.prop(active, 'name', text='')

            if icols:
                split = column.split(factor=0.3, align=True)
                row = split.row()
                row.active = False
                row.alignment = 'RIGHT'
                row.label(text="Children")

                col = split.column(align=True)

                for depth, cols in icols.items():
                    unique_cols = set(cols)

                    for icol in unique_cols:
                        row = col.row(align=True)
                        row.alignment = 'LEFT'

                        depth_str = (depth - 1) * '  '
                        row.label(text=f"{depth_str} ◦ {icol.name}")

                        if (count := cols.count(icol)) > 1:
                            r = row.row(align=True)
                            r.alignment = 'LEFT'
                            r.active = False
                            r.label(text=f"x {count}")

            column.separator()

        column = layout.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator("machin3.create_assembly_asset", text='Create Assembly Asset', icon='ASSET_MANAGER')

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.disassemble_assembly", text='Disassemble', icon='NETWORK_DRIVE')
        row.operator("machin3.remove_assembly_asset", text='Remove Assembly', icon='TRASH').remove_asset = False

        if is_local_asset:
            row = column.row(align=True)
            row.operator("machin3.remove_assembly_asset", text='Remove Asset', icon_value=get_icon('cancel')).remove_asset = True
