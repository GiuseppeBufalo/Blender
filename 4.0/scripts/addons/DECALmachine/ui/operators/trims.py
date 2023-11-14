import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty, StringProperty
from mathutils import Vector
from uuid import uuid4
from ... utils.trim import get_trim, create_trimsheet_json
from ... utils.math import flatten_matrix, average_locations, box_coords_to_trimmx, trimmx_to_box_coords, trimmx_to_img_coords
from ... utils.raycast import cast_obj_ray_from_mouse
from ... utils.draw import draw_point, draw_points, draw_lines
from ... utils.ui import init_cursor, draw_init, draw_title, draw_prop, draw_lines2d
from ... utils.decal import remove_trim_decals
from ... utils.atlas import reset_trim_scale, update_atlas_dummy, refresh_atlas_trims
from ... utils.property import step_enum
from ... items import align_trim_items, create_atlas_trim_sort_items



class Add(bpy.types.Operator):
    bl_idname = "machin3.add_trim"
    bl_label = "MACHIN3: Add Trim"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add a new trim, encompassing the entire sheet"

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'MESH' and active.DM.istrimsheet

    def execute(self, context):
        sheet = context.active_object

        idx, trims, active = get_trim(sheet)

        trim = trims.add()
        trim.uuid = str(uuid4())

        trim.avoid_update = True
        trim.name = "Trim %d" % len(trims)

        sheet.DM.trimsIDX = len(trims) - 1

        sheet.select_set(True)

        create_trimsheet_json(sheet)

        return {'FINISHED'}


class Remove(bpy.types.Operator):
    bl_idname = "machin3.remove_trim"
    bl_label = "MACHIN3: Remove Trim"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Remove selected trim"

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'MESH' and active.DM.istrimsheet and active.DM.trimsCOL

    def execute(self, context):
        sheet = context.active_object

        idx, trims, active = get_trim(sheet)

        remove_trim_decals(sheet, active)

        trims.remove(idx)
        sheet.DM.trimsIDX = max([idx - 1, 0])

        sheet.select_set(True)

        create_trimsheet_json(sheet)

        return {'FINISHED'}


class Duplicate(bpy.types.Operator):
    bl_idname = "machin3.duplicate_trim"
    bl_label = "MACHIN3: Duplicate Trim"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Duplicate an existing trim"

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'MESH' and active.DM.istrimsheet and active.DM.trimsCOL

    def execute(self, context):
        sheet = context.active_object

        idx, trims, active = get_trim(sheet)

        trim = trims.add()
        trim.uuid = str(uuid4())

        trim.avoid_update = True
        trim.name = "Trim %d" % len(trims)

        trim.mx = flatten_matrix(active.mx)
        trim.ispanel = active.ispanel

        sheet.DM.trimsIDX = len(trims) - 1

        active.hide_select = True

        create_trimsheet_json(sheet)

        return {'FINISHED'}


class Draw(bpy.types.Operator):
    bl_idname = "machin3.draw_trim"
    bl_label = "MACHIN3: Draw Trim"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create trim by drawing a rectangle"

    crosshair_size: IntProperty(name="Crosshair Size", default=250, min=0)

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'MESH' and active.DM.istrimsheet

    def draw_HUD(self, args):
        context, event = args

        draw_init(self, event, HUDy_offset=30)

        draw_title(self, "Draw Trim")

        draw_crosshair = context.space_data.region_3d.is_orthographic_side_view and not self.dragging
        draw_prop(self, "Crosshair Size", self.crosshair_size, active=draw_crosshair, hint="ALT scroll UP/DOWN", hint_offset=170)

        if draw_crosshair:
            x = event.mouse_x - self.region_offset_x
            y = event.mouse_y - self.region_offset_y

            size = self.crosshair_size

            coords = [Vector((x, y - size)), Vector((x, y + size)), Vector((x - size, y)), Vector((x + size, y))]

            draw_lines2d(coords, alpha=0.5)

    def draw_VIEW3D(self, args):
        if self.coords:
            start = self.coords[0]
            end = self.coords[-1]

            coords = [start, Vector((start.x, end.y, 0)), end, Vector((end.x, start.y, 0))]
            indices = [(0, 1), (1, 2), (2, 3), (3, 0)]

            draw_lines(coords, indices=indices, mx=self.mx, width=3, alpha=0.5)
            draw_points([start, end], mx=self.mx)

            draw_point(average_locations([start, end]), mx=self.mx, alpha=0.5)

    def modal(self, context, event):
        context.area.tag_redraw()

        if self.dragging:
            mousepos = (event.mouse_region_x, event.mouse_region_y)

            _, loc, _, _, _ = cast_obj_ray_from_mouse(mousepos, candidates=[self.sheet], debug=False)
            if loc:
                self.coords.append(self.sheet.matrix_world.inverted_safe() @ loc)

        if event.type in {'LEFTMOUSE'} and event.value == 'PRESS':
            self.dragging = True

        elif event.type in {'LEFTMOUSE'} and event.value == 'RELEASE':
            if self.dragging:
                if len(self.coords) > 1:
                    bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')
                    bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
                    context.window.cursor_set('DEFAULT')

                    trimmx = box_coords_to_trimmx(self.coords[0], self.coords[-1], self.sheet.dimensions)
                    _, trims, _ = get_trim(self.sheet)

                    trim = trims.add()
                    trim.uuid = str(uuid4())

                    trim.avoid_update = True
                    trim.name = "Trim %d" % len(trims)

                    trim.mx = flatten_matrix(trimmx)

                    self.sheet.DM.trimsIDX = len(trims) - 1

                    create_trimsheet_json(self.sheet)

                    return {'FINISHED'}

                else:
                    self.cancel_modal(context)
                return {'CANCELLED'}

        if event.alt and event.type in {'WHEELDOWNMOUSE', 'WHEELUPMOUSE', 'ONE', 'TWO'}:

            if event.type in ['WHEELUPMOUSE', 'ONE']:
                self.crosshair_size += 10

            elif event.type in ['WHEELDOWNMOUSE', 'TWO']:
                self.crosshair_size -= 10

        elif event.type in {'MIDDLEMOUSE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE'}:
            return {'PASS_THROUGH'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def cancel_modal(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        context.window.cursor_set('DEFAULT')

    def invoke(self, context, event):
        self.sheet = context.active_object

        self.dragging = False
        self.coords = []
        self.mx = self.sheet.matrix_world
        context.window.cursor_set('CROSSHAIR')

        init_cursor(self, event)

        args = (context, event)
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (args, ), 'WINDOW', 'POST_VIEW')
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (args, ), "WINDOW", "POST_PIXEL")

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class Align(bpy.types.Operator):
    bl_idname = "machin3.align_trim"
    bl_label = "MACHIN3: Align Trim"
    bl_options = {'REGISTER', 'UNDO'}

    side: EnumProperty(name="Align Direction", items=align_trim_items, default='RIGHT')

    @classmethod
    def poll(cls, context):
        active = context.active_object
        if active and active.type == 'MESH' and active.DM.istrimsheet and active.DM.trimsCOL:
            _, _, trim = get_trim(active)
            return not trim.hide_select

    @classmethod
    def description(cls, context, properties):
        return "Align trim to sheet's %s boundary" % (properties.side.lower())

    def execute(self, context):
        sheet = context.active_object

        idx, trims, active = get_trim(sheet)

        start, end = trimmx_to_box_coords(active.mx, sheet.dimensions)

        if self.side == 'LEFT':
            start = Vector((-sheet.dimensions.x / 2, start.y, 0))

        elif self.side == 'RIGHT':
            end = Vector((sheet.dimensions.x / 2, end.y, 0))

        elif self.side == 'TOP':
            start = Vector((start.x, sheet.dimensions.y / 2, 0))

        elif self.side == 'BOTTOM':
            end = Vector((end.x, - sheet.dimensions.y / 2, 0))

        trimmx = box_coords_to_trimmx(start, end, sheet.dimensions)
        active.mx = flatten_matrix(trimmx)

        sheet.select_set(True)

        create_trimsheet_json(sheet)

        remove_trim_decals(sheet, active)

        return {'FINISHED'}


class HideAll(bpy.types.Operator):
    bl_idname = "machin3.hide_all_trims"
    bl_label = "MACHIN3: Hide All Trims"
    bl_options = {'REGISTER', 'UNDO'}

    hide_select: BoolProperty()

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'MESH' and active.DM.istrimsheet and active.DM.trimsCOL

    @classmethod
    def description(cls, context, properties):
        if properties.hide_select:
            return "Toggle selectability for all trims"
        else:
            return "Toggle visibility for all trims"

    def execute(self, context):
        sheet = context.active_object

        idx, trims, active = get_trim(sheet)

        hide = trims[0].hide_select if self.hide_select else trims[0].hide

        for trim in trims:
            trim.avoid_update = True  # skip updating until the end

            if self.hide_select:
                trim.hide_select = not hide
            else:
                trim.hide = not hide

        sheet.select_set(True)

        create_trimsheet_json(sheet)

        return {'FINISHED'}




class ResetAtlasTrim(bpy.types.Operator):
    bl_idname = "machin3.reset_atlas_trim"
    bl_label = "MACHIN3: Reset Decal"
    bl_options = {'REGISTER', 'UNDO'}

    idx: StringProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None
            if atlas and atlas.DM.trimsCOL:
                return any(list(trim.original_size) != trimmx_to_img_coords(trim.mx, atlas.DM.atlasresolution)[1] for trim in atlas.DM.trimsCOL)

    @classmethod
    def description(cls, context, properties):
        if properties.idx == 'ALL':
            return "Reset all scaled Decals in Atlas"
        else:
            return "Reset selected Decal scale"

    def execute(self, context):
        atlas = context.active_object

        if self.idx == 'ALL':
            for trim in atlas.DM.trimsCOL:
                reset_trim_scale(atlas, trim)

        else:
            trim = atlas.DM.trimsCOL[int(self.idx)]

            reset_trim_scale(atlas, trim)

        atlas.select_set(True)

        return {'FINISHED'}


class ScaleAtlasTrim(bpy.types.Operator):
    bl_idname = "machin3.scale_atlas_trim"
    bl_label = "MACHIN3: Scale Decal"
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty(name="Scaling Mode", default="UP")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None
            return atlas and atlas.DM.trimsCOL

    @classmethod
    def description(cls, context, properties):
        return "Scale Decal %s\nSHIFT: Scale using smaller Amounts\nCTRL: Scale all Decals" % (properties.mode.capitalize())

    def invoke(self, context, event):
        atlas = context.active_object
        idx, trims, active = get_trim(atlas)

        if self.mode == 'UP':
            amount = 1.1 if event.shift else 2

        elif self.mode == 'DOWN':
            amount = 0.9090909090909090 if event.shift else 0.5

        if event.ctrl:
            for trim in trims:
                self.scale_trim(atlas, trim, amount)

        else:
            self.scale_trim(atlas, active, amount)

        atlas.select_set(True)

        return {'FINISHED'}

    def scale_trim(self, atlas, trim, amount):
        scale = (trim.mx[0][0], trim.mx[1][1])

        trim.mx[0][0] = scale[0] * amount
        trim.mx[1][1] = scale[1] * amount

        update_atlas_dummy(atlas, trim)


class AlignAtlasTrim(bpy.types.Operator):
    bl_idname = "machin3.align_atlas_trim"
    bl_label = "MACHIN3: Align Decal"
    bl_options = {'REGISTER', 'UNDO'}

    side: EnumProperty(name="Align Direction", items=align_trim_items, default='RIGHT')

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None
            return atlas and atlas.DM.trimsCOL

    @classmethod
    def description(cls, context, properties):
        return "Align Decal to Atlas' %s boundary" % (properties.side.lower())

    def execute(self, context):
        atlas = context.active_object
        idx, trims, active = get_trim(atlas)

        start, end = trimmx_to_box_coords(active.mx, atlas.dimensions)

        if self.side == 'LEFT':
            start = Vector((-atlas.dimensions.x / 2, start.y, 0))

        elif self.side == 'RIGHT':
            end = Vector((atlas.dimensions.x / 2, end.y, 0))

        elif self.side == 'TOP':
            start = Vector((start.x, atlas.dimensions.y / 2, 0))

        elif self.side == 'BOTTOM':
            end = Vector((end.x, - atlas.dimensions.y / 2, 0))

        trimmx = box_coords_to_trimmx(start, end, atlas.dimensions)
        active.mx = flatten_matrix(trimmx)

        update_atlas_dummy(atlas, active)

        atlas.select_set(True)

        return {'FINISHED'}


class ToggleAtlasTrimSort(bpy.types.Operator):
    bl_idname = "machin3.toggle_atlas_trim_sort"
    bl_label = "MACHIN3: Toggle Decal Sorting"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None
            return atlas and atlas.DM.trimsCOL and atlas.DM.get('sources') and atlas.DM.get('solution')

    @classmethod
    def description(cls, context, properties):
        atlas = context.active_object
        return "Change sorting from %s to %s" % (atlas.DM.atlastrimsort, step_enum(atlas.DM.atlastrimsort, create_atlas_trim_sort_items, 1))

    def execute(self, context):
        atlas = context.active_object

        atlas.DM.atlastrimsort = step_enum(atlas.DM.atlastrimsort, create_atlas_trim_sort_items, 1)

        refresh_atlas_trims(atlas)

        atlas.select_set(True)

        return {'FINISHED'}
