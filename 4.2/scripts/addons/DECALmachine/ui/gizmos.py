import bpy
from mathutils import Vector, Matrix
from .. colors import white, red, yellow, grey, blue, green
from .. utils.math import flatten_matrix, get_sca_matrix, get_snapped_trim_mx, trimmx_to_box_coords, trimmx_to_img_coords, mul
from .. utils.trim import create_trimsheet_json
from .. utils.decal import remove_trim_decals
from .. utils.atlas import update_atlas_dummy

trim_edited = None

class GizmoGroupTrimSheet(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_trimsheet"
    bl_label = "TrimSheet Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    sheet = None
    trimscount = 0
    resolution = [1024, 1024]

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and [active] == context.selected_objects and active.DM.istrimsheet and active.DM.trimsCOL

    def setup(self, context):
        self.sheet = context.active_object
        self.trimscount = len(self.sheet.DM.trimsCOL)
        self.resolution = tuple(self.sheet.DM.trimsheetresolution)

        self.initialize_trim_gizmos()

    def refresh(self, context):
        view = context.space_data

        if not view.show_gizmo:
            view.show_gizmo = True

        if self.sheet and self.sheet != context.active_object:
            self.sheet = context.active_object

            self.reset_trim_gizmos()

        elif self.trimscount != len(context.active_object.DM.trimsCOL):
            self.reset_trim_gizmos()

        elif self.resolution != tuple(self.sheet.DM.trimsheetresolution):
            self.reset_trim_gizmos()

        else:
            self.update_trim_gizmos()

            global trim_edited

            if trim_edited:
                sheet, trim = trim_edited
                trim_edited = None

                remove_trim_decals(sheet, trim)

    def update_trim_gizmos(self):
        sheet = self.sheet
        trims = sheet.DM.trimsCOL

        for idx, gzm in enumerate(self.gizmos):
            trim = trims[idx]

            gzm.matrix_basis = sheet.matrix_world.normalized()

            gzm.line_width = 3 if trim.isactive else 2

            gzm.color = red if trim.isactive else blue if trim.isempty else grey if trim.hide_select else white

            gzm.hide = trim.hide
            gzm.hide_select = trim.hide_select

    def reset_trim_gizmos(self):
        self.trimscount = len(self.sheet.DM.trimsCOL)
        self.resolution = tuple(self.sheet.DM.trimsheetresolution)

        self.gizmos.clear()
        self.initialize_trim_gizmos()

    def initialize_trim_gizmos(self):
        sheet = self.sheet
        trims = sheet.DM.trimsCOL

        for trim in trims:
            gzm = self.gizmos.new("GIZMO_GT_cage_2d")

            gzm.matrix_basis = sheet.matrix_world.normalized()
            gzm.dimensions = [res / 1000 for res in sheet.DM.trimsheetresolution]

            gzm.draw_style = 'BOX_TRANSFORM' if bpy.app.version >= (3, 5, 0) else 'CIRCLE'
            gzm.transform = {'TRANSLATE', 'SCALE'}

            gzm.color = red if trim.isactive else blue if trim.isempty else grey if trim.hide_select else white
            gzm.color_highlight = yellow

            gzm.line_width = 3 if trim.isactive else 2

            gzm.hide = trim.hide
            gzm.hide_select = trim.hide_select

            gzm.target_set_handler("matrix", get=trim_getter(sheet, trim), set=trim_setter(sheet, trims, trim))

def trim_getter(sheet, trim):
    def function_template():
        if sheet.DM.trimsnapping:
            snapped_mx = get_snapped_trim_mx(sheet, trim.mx)
            return flatten_matrix(snapped_mx)

        else:
            return flatten_matrix(trim.mx)

    return function_template

def trim_setter(sheet, trims, trim):
    def function_template(value):
        trim.mx = value
        trim.isactive = True

        for idx, t in enumerate(trims):
            if t == trim:
                sheet.DM.trimsIDX = idx

            else:
                t.isactive = False

        create_trimsheet_json(sheet)

        global trim_edited
        trim_edited = (sheet, trim)

    return function_template

atlas_trim_edited = None

class GizmoGroupAtlas(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_atlas"
    bl_label = "Atlas Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    atlas = None
    trimscount = 0
    resolution = [1024, 1024]

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and [active] == context.selected_objects and active.DM.isatlas and active.DM.trimsCOL

    def setup(self, context):
        self.atlas = context.active_object
        self.trimscount = len(self.atlas.DM.trimsCOL)
        self.resolution = tuple(self.atlas.DM.atlasresolution)

        self.initialize_atlas_gizmos(context)

    def refresh(self, context):
        view = context.space_data

        if not view.show_gizmo:
            view.show_gizmo = True

        if self.atlas and self.atlas != context.active_object:
            self.atlas = context.active_object

            self.reset_atlas_gizmos(context)

        elif self.trimscount != len(context.active_object.DM.trimsCOL):
            self.reset_atlas_gizmos(context)

        elif self.resolution != tuple(self.atlas.DM.atlasresolution):
            self.reset_atlas_gizmos(context)

        else:
            self.update_atlas_gizmos(context)

            global atlas_trim_edited

            if atlas_trim_edited:
                atlas, trim = atlas_trim_edited
                atlas_trim_edited = None

                update_atlas_dummy(atlas, trim)

    def update_atlas_gizmos(self, context):
        atlas = self.atlas
        trims = atlas.DM.trimsCOL

        for idx, gzm in enumerate(self.gizmos):
            trim = trims[idx]

            gzm.matrix_basis = atlas.matrix_world.normalized()

            transform = {'SCALE'} if context.scene.DM.create_atlas_non_uniform_scale else {'SCALE', 'SCALE_UNIFORM'}

            if atlas.DM.atlasrefinement == 'TWEAK':
                transform.update({'TRANSLATE'})

            gzm.transform = transform

            orig_size = list(trim.original_size)
            cur_size = trimmx_to_img_coords(trim.mx, atlas.DM.atlasresolution)[1]

            gzm.color = white if mul(*orig_size) == mul(*cur_size) else green if mul(*cur_size) < mul(*orig_size) else red
            gzm.line_width = 4 if trim.isactive else 2

    def reset_atlas_gizmos(self, context):
        self.trimscount = len(self.atlas.DM.trimsCOL)
        self.resolution = tuple(self.atlas.DM.atlasresolution)

        self.gizmos.clear()
        self.initialize_atlas_gizmos(context)

    def initialize_atlas_gizmos(self, context):
        atlas = self.atlas
        trims = atlas.DM.trimsCOL

        for trim in trims:
            gzm = self.gizmos.new("GIZMO_GT_cage_2d")

            gzm.matrix_basis = atlas.matrix_world.normalized()
            gzm.dimensions = [res / 1000 for res in atlas.DM.atlasresolution]

            gzm.draw_style = 'BOX_TRANSFORM' if bpy.app.version >= (3, 5, 0) else 'CIRCLE'

            transform = {'SCALE'} if context.scene.DM.create_atlas_non_uniform_scale else {'SCALE', 'SCALE_UNIFORM'}

            if atlas.DM.atlasrefinement == 'TWEAK':
                transform.update({'TRANSLATE'})

            gzm.transform = transform

            gzm.color_highlight = yellow

            gzm.target_set_handler("matrix", get=atlas_getter(trim), set=atlas_setter(atlas, trims, trim))

            orig_size = list(trim.original_size)
            cur_size = trimmx_to_img_coords(trim.mx, atlas.DM.atlasresolution)[1]

            gzm.color = white if mul(*orig_size) == mul(*cur_size) else green if mul(*cur_size) < mul(*orig_size) else red
            gzm.line_width = 4 if trim.isactive else 2

def atlas_getter(trim):
    def function_template():
        return flatten_matrix(trim.mx)

    return function_template

def atlas_setter(atlas, trims, trim):
    def function_template(value):
        trim.mx = value
        trim.isactive = True

        for idx, t in enumerate(trims):
            if t == trim:
                atlas.DM.trimsIDX = idx

            else:
                t.isactive = False

        if trim.dummy:
            global atlas_trim_edited
            atlas_trim_edited = (atlas, trim)

    return function_template
