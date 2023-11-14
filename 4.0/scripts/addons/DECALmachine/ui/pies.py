import bpy
import math
from .. utils.registration import get_prefs, get_addon
from .. utils.ui import get_icon
from .. utils.modifier import get_shrinkwrap, get_subd, get_displace
from .. import bl_info


grouppro = None


class PieDecalMachine(bpy.types.Menu):
    bl_idname = "MACHIN3_MT_decal_machine"
    bl_label = "DECALmachine %s" % ('.'.join([str(v) for v in bl_info['version']]))

    def draw(self, context):
        mode = context.mode
        decalmode = get_prefs().decalmode

        active = context.active_object
        sel = context.selected_objects

        decallibsCOL = get_prefs().decallibsCOL

        scene = context.scene

        if mode == "OBJECT":

            decallibs = [lib for lib in decallibsCOL if lib.isvisible]

            layout = self.layout
            pie = layout.menu_pie()

            self.draw_decal_libraries(pie, decalmode, decallibs, side="LEFT")

            self.draw_decal_libraries(pie, decalmode, decallibs, side="RIGHT")

            self.draw_extra(pie, context, active, scene, sel)

            box = pie.split()
            column = box.column(align=False)

            self.draw_update_check(column)
            self.draw_tools(column, context, active, sel)


        elif mode == "EDIT_MESH":
            trimlibs = [lib for lib in decallibsCOL if lib.isvisible and lib.istrimsheet]

            layout = self.layout
            pie = layout.menu_pie()

            self.draw_trim_libraries(pie, trimlibs, side="LEFT")

            self.draw_trim_libraries(pie, trimlibs, side="RIGHT")

            pie.separator()

            box = pie.split()
            column = box.column()

            self.draw_update_check(column)
            self.draw_trim_tools(column, context, active, sel)

            pie.separator()

            pie.separator()

            pie.separator()

            pie.separator()

    def draw_update_check(self, layout):
        if get_prefs().update_available:
            layout.label(text="A new version is available", icon_value=get_icon("refresh_green"))



    def draw_trim_libraries(self, layout, trimlibs, side):
        libraryscale = get_prefs().trimlibraryscale

        def draw_trimsheet_library(layout, library):
            trimsinlibraryscale = get_prefs().trimsinlibraryscale

            showtrimcount = get_prefs().showtrimcount
            showtrimnames = get_prefs().showtrimnames
            showtrimbuttonname = get_prefs().showtrimbuttonname

            wmt = bpy.types.WindowManager
            wm = bpy.context.window_manager

            if showtrimcount:
                decalcount = len(getattr(wmt, "trimlib_" + library.name).keywords['items'])
                liblabel = "%s, %d" % (library.name, decalcount)
            else:
                liblabel = library.name

            layout.label(text=liblabel, icon='SELECT_SET')

            row = layout.row()
            lib = "trimlib_%s" % library.name
            row.template_icon_view(wm, lib, show_labels=showtrimnames, scale=libraryscale, scale_popup=trimsinlibraryscale)


            trimname = getattr(wm, "trimlib_" + library.name) if library.istrimsheet else getattr(wm, "decallib_" + library.name)

            text, icon = (trimname, 0) if showtrimbuttonname else ("", get_icon("plus"))
            op = layout.operator("machin3.trim_unwrap", text=text, icon_value=icon)
            op.library_name = library.name
            op.trim_name = trimname

        libraryrows = get_prefs().trimlibraryrows
        libraryoffset = get_prefs().trimlibraryoffset
        trimlibscount = len(trimlibs)

        if side == "LEFT":
            count = math.ceil(trimlibscount / 2)
            side_libs = trimlibs[0:count + libraryoffset]

        elif side == "RIGHT":
            count = math.floor(trimlibscount / 2)
            side_libs = trimlibs[count + libraryoffset + trimlibscount % 2:]


        libs = [side_libs[i * libraryrows:i * libraryrows + libraryrows] for i in range(math.ceil(len(side_libs) / libraryrows))]

        box = layout.split()

        for libraries in libs:

            col = box.column()
            col.ui_units_x = libraryscale

            for library in libraries:
                draw_trimsheet_library(col, library)

    def draw_trim_tools(self, layout, context, active, sel):
        if context.space_data.type == 'VIEW_3D':

            row = layout.row(align=True)
            row.scale_y = 1.2
            row.operator("machin3.epanel", text="EPanel", icon="AXIS_TOP")

            layout.separator()



        column = layout.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.quad_unwrap", text="Quad Unwrap", icon="AXIS_TOP")
        row.operator("machin3.box_unwrap", text="Box Unwrap", icon="AXIS_TOP")


        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.trim_unwrap_to_empty", text="(W) Unwrap to Empty Trim", icon="AXIS_TOP")

        layout.separator()



        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.trim_adjust", text="Adjust", icon="AXIS_TOP")

        if context.space_data.type == 'VIEW_3D':
            sel = [obj for obj in sel if obj != active and obj.DM.isdecal]

            if active and sel and len(sel) == 1 and tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False):
                row.operator("machin3.align_decal_to_edge", text="Align to Edge", icon="AXIS_TOP")

            else:
                row.operator("machin3.stitch", text="Stitch", icon="AXIS_TOP")

        elif context.space_data.type == 'IMAGE_EDITOR':
            row.operator("machin3.stitch", text="Stitch", icon="AXIS_TOP")
            row.operator("machin3.mirror_trim", text="Mirror Trim", icon="AXIS_TOP")



    def draw_tools(self, layout, context, active, sel):
        decals = [obj for obj in sel if obj.DM.isdecal]

        if len(sel) == 1 and active in sel and active.type == 'MESH' and not active.data.polygons and active.data.edges:
            epanel_src = active

        elif len(sel) == 2:
            sel_objs = [obj for obj in sel if obj != active and obj.type == 'MESH']
            epanel_src = sel_objs[0] if sel_objs and not sel_objs[0].data.polygons and sel_objs[0].data.edges else None

        else:
            epanel_src = None



        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.panel_cut", text="(C) Panel Cut", icon="AXIS_TOP")
        row.operator("machin3.trim_cut", text="(T) Trim Cut", icon="AXIS_TOP")



        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.get_backup_decal", text="(B) Get Backup", icon="AXIS_TOP")
        row.operator("machin3.match_material", text="(V) Match", icon="AXIS_TOP")


        row = layout.row(align=True)
        row.scale_y = 1.5
        r = row.row(align=True)
        r.operator("machin3.project_decal", text="(D) Project", icon="AXIS_TOP")



        if decals and any(get_shrinkwrap(obj) or get_subd(obj) for obj in decals):
            r.operator("machin3.unshrinkwrap_decal", text="", icon="NORMALS_FACE")


        if decals and all(obj.DM.decaltype == "PANEL" and obj.DM.issliced for obj in decals):
            row.operator("machin3.panel_decal_unwrap", text="Unwrap", icon="AXIS_TOP")


        elif active and active.type == "GPENCIL":
            row.operator("machin3.gpanel", text="GPanel", icon="AXIS_TOP")


        elif epanel_src:
            row.operator("machin3.epanel", text="EPanel", icon="AXIS_TOP")


        else:
            row.operator("machin3.slice_decal", text="Slice", icon="AXIS_TOP")



        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("machin3.adjust_decal", text="Adjust", icon="AXIS_TOP")


        row.operator("machin3.reapply_decal", text="Re-Apply", icon="AXIS_TOP")


        if get_prefs().show_join_in_pie:
            row = layout.row(align=True)
            row.scale_y = 1.2
            row.operator("machin3.join_decal", text="Join", icon="AXIS_TOP")
            row.operator("machin3.split_decal", text="Split", icon="AXIS_TOP")

    def draw_decal_libraries(self, layout, decalmode, decallibs, side):
        libraryscale = get_prefs().libraryscale

        def draw_decal_library(layout, decalmode, library):
            decalsinlibraryscale = get_prefs().decalsinlibraryscale

            showdecalcount = get_prefs().showdecalcount
            showdecalnames = get_prefs().showdecalnames
            showdecalbuttonname = get_prefs().showdecalbuttonname

            wmt = bpy.types.WindowManager
            wm = bpy.context.window_manager

            if showdecalcount:
                decalcount = len(getattr(wmt, "trimlib_" + library.name).keywords['items']) if library.istrimsheet else len(getattr(wmt, "decallib_" + library.name).keywords['items'])
                liblabel = "%s, %d" % (library.name, decalcount)
            else:
                liblabel = library.name

            layout.label(text=liblabel, icon='SELECT_SET' if library.istrimsheet else 'NONE')


            row = layout.row()
            lib = "lockeddecallib" if decalmode == "REMOVE" and library.islocked else "trimlib_%s" % library.name if library.istrimsheet else "decallib_%s" % library.name
            row.template_icon_view(wm, lib, show_labels=showdecalnames, scale=libraryscale, scale_popup=decalsinlibraryscale)


            decalname = getattr(wm, "trimlib_" + library.name) if library.istrimsheet else getattr(wm, "decallib_" + library.name)

            if decalmode == "REMOVE" and library.islocked:
                layout.label(text="LOCKED")

            else:
                if decalmode == "INSERT":
                    text, icon = (decalname, 0) if showdecalbuttonname else ("", get_icon("plus"))
                    op = layout.operator("machin3.insert_decal", text=text, icon_value=icon)
                    op.force_cursor_align = False
                    op.batch = True

                elif decalmode == "REMOVE":
                    text, icon = ("", get_icon("cancel"))
                    op = layout.operator("machin3.remove_decal", text=text, icon_value=icon)

                op.library = library.name
                op.decal = decalname
                op.instant = False
                op.trim = library.istrimsheet

        libraryrows = get_prefs().libraryrows
        libraryoffset = get_prefs().libraryoffset
        decallibscount = len(decallibs)

        if side == "LEFT":
            count = math.ceil(decallibscount / 2)
            side_libs = decallibs[0:count + libraryoffset]

        elif side == "RIGHT":
            count = math.floor(decallibscount / 2)
            side_libs = decallibs[count + libraryoffset + decallibscount % 2:]


        libs = [side_libs[i * libraryrows:i * libraryrows + libraryrows] for i in range(math.ceil(len(side_libs) / libraryrows))]

        box = layout.split()

        for libraries in libs:

            col = box.column()
            col.ui_units_x = libraryscale

            for library in libraries:
                draw_decal_library(col, decalmode, library)

    def draw_extra(self, layout, context, active, scene, sel):
        def draw_decal_scale(layout, active, scene, sel):
            row = layout.row(align=True)

            r = row.row(align=True)
            r.prop(scene.DM, "globalscale")

            if round(scene.DM.globalscale, 3) != 1:
                r.operator("machin3.reset_default_property", text="", icon="LOOP_BACK").mode = 'SCALE'

            if active and len(sel) == 1 and active in sel and active.DM.isdecal and not active.DM.isprojected and not active.DM.issliced:
                uuid = active.DM.uuid
                scales = scene.DM.individualscales
                _, _, active_scale = active.matrix_world.decompose()

                if uuid in scales:
                    if [round(s, 6) for s in scales[uuid].scale] == [round(s, 6) for s in active_scale]:
                        icon = "RADIOBUT_ON"
                    else:
                        icon = "PROP_ON"
                else:
                    icon = "RADIOBUT_OFF"

                r = row.row(align=True)
                r.operator("machin3.store_individual_decal_scale", text="", icon=icon)
                if active.DM.uuid in scene.DM.individualscales:
                    r.operator("machin3.clear_individual_decal_scale", text="", icon_value=get_icon("cancel"))

        def draw_panel_width(layout, scene):
            row = layout.row(align=True)
            row.prop(scene.DM, "panelwidth")

            if round(scene.DM.panelwidth, 2) != 0.04:
                row.operator("machin3.reset_default_property", text="", icon="LOOP_BACK").mode = 'WIDTH'

        def draw_decal_height(layout, active, scene):
            row = layout.row(align=True)
            row.prop(scene.DM, "height")

            displace = get_displace(active) if active else False

            if active and active.DM.isdecal and displace and round(displace.mid_level, 4) != round(scene.DM.height, 4):
                    row.operator("machin3.set_default_property", text="", icon="SORT_ASC").mode = 'HEIGHT'

            if round(scene.DM.height, 4) != 0.9998:
                row.operator("machin3.reset_default_property", text="", icon="LOOP_BACK").mode = 'HEIGHT'

        def draw_more(layout, active):
            removemode = get_prefs().decalremovemode
            icon = "cancel" if removemode else "cancel_grey"

            layout.separator()
            row = layout.row(align=True)
            row.operator("machin3.decal_library_visibility", text="(H) Visibility", icon="HIDE_OFF")
            row.prop(get_prefs(), "decalremovemode", text="Removal", icon_value=get_icon(icon))

        box = layout.split()
        column = box.column(align=True)

        draw_decal_scale(column, active, scene, sel)
        draw_panel_width(column, scene)
        draw_decal_height(column, active, scene)
        draw_more(column, active)
