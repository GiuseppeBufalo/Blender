import bpy
from .. utils.math import trimmx_to_img_coords, mul
from .. utils.atlas import get_textypes_from_atlasmats, verify_channel_pack



class DecalLibsUIList(bpy.types.UIList):
    bl_idname = "MACHIN3_UL_decal_libs"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        isvisibleicon = "HIDE_OFF" if item.isvisible else "HIDE_ON"
        islockedicon = "LOCKED" if item.islocked else "BLANK1"
        ispanelcycleicon = "CHECKBOX_HLT" if item.ispanelcycle else "CHECKBOX_DEHLT"

        row = layout.row()
        row.prop(item, "isvisible", text="", icon=isvisibleicon, emboss=False)

        split = row.split(factor=0.7)

        r = split.row()
        r.active = item.isvisible
        r.label(text=item.name)

        rs = split.split(factor=0.2)

        if item.ispanel or item.istrimsheet:
            rs.prop(item, "ispanelcycle", text="", icon=ispanelcycleicon, emboss=False)
        else:
            rs.separator()

        if item.istrimsheet:
            rs.label(text='Trim Sheet')
        else:
            rs.prop(item, "ispanel", text="Panel")

        row.prop(item, "islocked", text="", icon=islockedicon, emboss=False)


class SimpleDecalLibsUIList(bpy.types.UIList):
    bl_idname = "MACHIN3_UL_simple_decal_libs"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        isvisibleicon = "HIDE_OFF" if item.isvisible else "HIDE_ON"
        ispanelcycleicon = "CHECKBOX_HLT" if item.ispanelcycle else "CHECKBOX_DEHLT"

        row = layout.row()
        row.prop(item, "isvisible", text="", icon=isvisibleicon, emboss=False)

        split = row.split(factor=0.6)

        r = split.row()
        r.active = item.isvisible
        r.label(text=item.name)

        rs = split.split(factor=0.2)

        if item.ispanel or item.istrimsheet:
            rs.prop(item, "ispanelcycle", text="", icon=ispanelcycleicon, emboss=False)
        else:
            rs.separator()

        if item.istrimsheet:
            rs.label(text='Trim Sheet')
        elif item.ispanel:
            rs.label(text='Panel')
        else:
            rs.label(text='')



class TrimsUIList(bpy.types.UIList):
    bl_idname = "MACHIN3_UL_trims"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        isemptyicon = "SHADING_BBOX" if item.isempty else "CHECKBOX_DEHLT"
        hide_icon = "HIDE_ON" if item.hide else "HIDE_OFF"
        hide_select_icon = "RESTRICT_SELECT_ON" if item.hide_select else "RESTRICT_SELECT_OFF"

        split = layout.split(factor=0.4)

        row = split.row()

        row.prop(item, "isempty", text="", icon=isemptyicon, emboss=False)

        if item.isempty:
            row.label(text="EMPTY")
        else:
            row.prop(item, 'name', text="", emboss=False)

        row = split.row()
        row.prop(item, 'ispanel', text='Panel')
        row.prop(item, 'hide_select', text='', icon=hide_select_icon, emboss=False)
        row.prop(item, 'hide', text='', icon=hide_icon, emboss=False)


class TrimMapsUIList(bpy.types.UIList):
    bl_idname = "MACHIN3_UL_trim_maps"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        sheetres = tuple(context.active_object.DM.trimsheetresolution)
        mapres = tuple(item.resolution)
        icon = 'ERROR' if item.texture and sheetres != mapres else 'TEXTURE'

        split = layout.split(factor=0.3)

        row = split.row()
        row.label(text=item.name, icon=icon)

        row = split.row()

        if item.texture:
            r = row.split(factor=0.3)

            if item.name == 'Height':
                r.prop(item, 'parallax_amount', text='')

            elif item.name == 'Alpha':
                r.prop(item, 'connect_alpha', text='Show', toggle=True)

            else:
                r.separator()


            rr = r.split(factor=0.7)
            rr.label(text=item.texture)
            rr.operator("machin3.clear_trim_map", text="", icon="CANCEL", emboss=False).idx = index

        elif index == data.trimmapsIDX:
            row.prop(context.window_manager, "trimtextures", text="")



class AtlasesUIList(bpy.types.UIList):
    bl_idname = "MACHIN3_UL_atlases"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        isenabledicon = "CHECKBOX_HLT" if item.isenabled else "CHECKBOX_DEHLT"
        islockedicon = "LOCKED" if item.islocked else "BLANK1"

        row = layout.row()
        row.prop(item, "isenabled", text="", icon=isenabledicon, emboss=False)

        split = row.split(factor=0.7)

        r = split.row()
        r.active = item.isenabled
        r.label(text=item.name)

        r = split.row()

        if item.istrimsheet:
            r.label(text='Trim Sheet')
        else:
            r.label(text='')

        row.prop(item, "islocked", text="", icon=islockedicon, emboss=False)


class AtlasTrimsUIList(bpy.types.UIList):
    bl_idname = "MACHIN3_UL_atlas_trims"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        atlas = context.active_object

        orig_size = list(item.original_size)
        cur_size = trimmx_to_img_coords(item.mx, atlas.DM.atlasresolution)[1]

        split = layout.split(factor=0.6)

        row = split.row()
        if mul(*orig_size) != mul(*cur_size):
            row.operator("machin3.reset_atlas_trim", text="", icon="LOOP_BACK", emboss=False).idx = str(index)
        else:
            row.label(text="", icon="CHECKBOX_DEHLT")

        row.label(text=item.name)

        if item.ispanel:
            row = split.row()
            if item.ispanel:
                row.prop(item, 'prepack', text='')


class ExportAtlasesUIList(bpy.types.UIList):
    bl_idname = "MACHIN3_UL_export_atlases"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        isenabledicon = "CHECKBOX_HLT" if item.isenabled else "CHECKBOX_DEHLT"

        row = layout.row()
        row.prop(item, "isenabled", text="", icon=isenabledicon, emboss=False)

        split = row.split(factor=0.6)

        r = split.row()
        r.active = item.isenabled
        r.label(text=item.name)

        r = split.row()

        if item.istrimsheet:
            r.label(text='Trim Sheet')
        else:
            r.label(text='')


class AtlasChannelPackUIList(bpy.types.UIList):
    bl_idname = "MACHIN3_UL_atlas_channel_pack"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        isenabledicon = "CHECKBOX_HLT" if item.isenabled else "CHECKBOX_DEHLT"


        decals = [obj for obj in (context.selected_objects if context.selected_objects else context.visible_objects) if obj.DM.isdecal and obj.DM.preatlasmats]
        atlasmats = {mat for decal in decals for mat in decal.data.materials if mat and mat.DM.isatlasmat}
        textypes = get_textypes_from_atlasmats(atlasmats)

        isvalid = verify_channel_pack(textypes, item)

        row = layout.row()
        row.prop(item, "isenabled", text="", icon=isenabledicon, emboss=False)

        if item.isenabled:
            split = row.split(factor=0.25)

            r = split.row()

            if item.isenabled and not isvalid:
                r.label(text="", icon='ERROR')

            r.active = item.isenabled
            r.prop(item, "name", text='', emboss=False)


            r = split.row(align=True)
            r.active = item.isenabled
            r.prop(item, "red", text='')
            r.prop(item, "green", text='')
            r.prop(item, "blue", text='')
            r.prop(item, "alpha", text='')

        else:
            row.prop(item, "name", text='', emboss=False)
