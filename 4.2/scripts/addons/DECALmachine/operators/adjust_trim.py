import bpy
from bpy.props import BoolProperty, IntProperty, EnumProperty
import bmesh
from mathutils import Vector, Matrix
from math import radians
from bpy_extras.view3d_utils import region_2d_to_origin_3d
from .. utils.trim import get_sheetdata_from_uuid, get_trim_from_selection
from .. utils.uv import get_selection_uv_bbox, get_trim_uv_bbox, set_trim_uv_channel
from .. utils.ui import popup_message, init_cursor, draw_init, draw_title, draw_prop, wrap_cursor, init_status, finish_status, update_HUD_location
from .. utils.property import step_list, step_enum
from .. utils.registration import get_prefs
from .. utils.material import get_most_used_sheetmat_from_selection
from .. utils.math import absvector
from .. items import trimadjust_fit_items, uv_up_axis_mapping_dict
from .. utils.draw import draw_vector, draw_point

fit = None

class TrimAdjust(bpy.types.Operator):
    bl_idname = "machin3.trim_adjust"
    bl_label = "MACHIN3: Adjust Trim"
    bl_description = "Fit, Move, Scale, Rotate and Change Trims"
    bl_options = {'REGISTER', 'UNDO'}

    fit: EnumProperty(name="Fit unwrapped faces to trim", items=trimadjust_fit_items, default='NONE')
    rotate: IntProperty(name="Rotate", default=0)
    quick_scale: BoolProperty(name="Quick Scale", default=False)
    x_lock: BoolProperty(default=False)
    y_lock: BoolProperty(default=False)
    allowmodalmove: BoolProperty(default=False)
    allowmodalscale: BoolProperty(default=False)
    passthrough = False
    toggled_overlays = False

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            draw_title(self, "Adjust Trim", subtitle=self.library_name, subtitleoffset=180)

            draw_prop(self, "Fit", self.fit, offset=0, hint="cycle F, SHIFT + F: backwards", hint_offset=220)

            draw_prop(self, "Trim", self.trim_name, offset=18, hint="CTRL scroll UP/DOWN", hint_offset=220)
            self.offset += 10

            draw_prop(self, "Move", self.allowmodalmove, offset=18, hint="move MOUSE, toggle W/G, reset ALT + W/G", hint_offset=220)
            if not self.quick_scale:
                draw_prop(self, "Scale", self.allowmodalscale, offset=18, hint="move MOUSE, toggle S, reset ALT + S", hint_offset=220)
            draw_prop(self, "Rotate", self.rotate, offset=18, hint="scroll UP/DOWN, SHIFT: 5°, CTRL + SHIFT: 1°", hint_offset=220)
            if self.trim['ispanel']:
                draw_prop(self, "Quick Scale", self.quick_scale, offset=18, hint="toggle Q", hint_offset=220)
            self.offset += 10

            draw_prop(self, "Lock X", self.x_lock, offset=18, hint="toggle X", hint_offset=220)
            draw_prop(self, "Lock Y", self.y_lock, offset=18, hint="toggle Y/Z", hint_offset=220)

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object
            bm = bmesh.from_edit_mesh(active.data)
            if bm.loops.layers.uv.active:
                sheetmats = [mat for mat in active.data.materials if mat and mat.DM.istrimsheetmat]
                return sheetmats and [f for f in bm.faces if f.select]

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)
            update_HUD_location(self, event)

        events = ['WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'ONE', 'TWO', 'F', 'W', 'G', 'S', 'X', 'Y', 'Z', 'Q']

        if any([self.allowmodalmove, self.allowmodalscale]):
            events.append('MOUSEMOVE')

        global fit

        if event.type in events:

            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                    self.uv_right, self.uv_up = self.get_uv_axes(context, context.active_object, debug=False)

                elif not event.alt:
                    if self.allowmodalmove:
                        divisor = 5000 if event.shift else 50 if event.ctrl else 500

                        delta_x = event.mouse_x - self.last_mouse_x
                        delta_move_x = delta_x / divisor

                        delta_y = event.mouse_y - self.last_mouse_y
                        delta_move_y = delta_y / divisor

                        u_amount = self.uv_right * delta_move_x
                        v_amount = self.uv_up * delta_move_y

                        self.move -= u_amount if self.x_lock else v_amount if self.y_lock else u_amount + v_amount

                    elif self.allowmodalscale:
                        divisor = 3000 if event.shift else 30 if event.ctrl else 300

                        delta_x = event.mouse_x - self.last_mouse_x
                        delta_scale_x = delta_x / divisor

                        delta_y = event.mouse_y - self.last_mouse_y
                        delta_scale_y = delta_y / divisor

                        u_amount = absvector(self.uv_right) * delta_scale_x
                        v_amount = absvector(self.uv_up) * delta_scale_y

                        self.scale -= u_amount if self.x_lock else v_amount if self.y_lock else u_amount + v_amount

            elif event.type in {'WHEELUPMOUSE', 'ONE'} and event.value == 'PRESS':

                if event.ctrl and event.shift:
                    self.rotate -= 1
                elif event.shift:
                    self.rotate -= 5
                elif not event.ctrl:
                    self.rotate -= 90

                elif event.ctrl:
                    self.trim = step_list(self.trim, self.all_trims, -1)

                    trim = context.window_manager.decaluuids.get(self.trim['uuid'])
                    if trim:
                        self.trim_name = trim[0][0]

                    self.fit = 'AUTO' if fit in [None, 'NONE'] else fit

                    self.move = Vector((0, 0))
                    self.scale = Vector((1, 1))

            elif event.type in {'WHEELDOWNMOUSE', 'TWO'} and event.value == 'PRESS':

                if event.ctrl and event.shift:
                    self.rotate += 1
                elif event.shift:
                    self.rotate += 5
                elif not event.ctrl:
                    self.rotate += 90

                elif event.ctrl:
                    self.trim = step_list(self.trim, self.all_trims, 1)

                    trim = context.window_manager.decaluuids.get(self.trim['uuid'])
                    if trim:
                        self.trim_name = trim[0][0]

                    self.fit = 'AUTO' if fit in [None, 'NONE'] else fit

                    self.move = Vector((0, 0))
                    self.scale = Vector((1, 1))

            elif event.type == 'F' and event.value == "PRESS":
                if event.shift:
                    self.fit = step_enum(self.fit, trimadjust_fit_items, step=-1)
                else:
                    self.fit = step_enum(self.fit, trimadjust_fit_items, step=1)

                fit = self.fit

                self.quick_scale = False

            elif event.type in ['W', 'G'] and event.value == "PRESS":
                self.allowmodalmove = not self.allowmodalmove

                if event.alt:
                    self.allowmodalmove = False
                    self.move = Vector((0, 0))

                if self.allowmodalmove:
                    self.allowmodalscale = False

            elif event.type == 'S' and event.value == "PRESS":
                self.allowmodalscale = not self.allowmodalscale

                if event.alt:
                    self.allowmodalscale = False
                    self.scale = Vector((1, 1))

                if self.allowmodalscale:
                    self.allowmodalmove = False

            elif self.trim['ispanel'] and event.type == 'Q' and event.value == "PRESS":
                self.quick_scale = not self.quick_scale

            elif event.type == 'X' and event.value == "PRESS":
                self.x_lock = not self.x_lock

                if self.x_lock:
                    self.y_lock = False

            elif event.type in ['Y', 'Z'] and event.value == "PRESS":
                self.y_lock = not self.y_lock

                if self.y_lock:
                    self.x_lock = False

            self.main()

            if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'ONE', 'TWO'} and event.value == 'PRESS':
                self.uv_right, self.uv_up = self.get_uv_axes(context, context.active_object, debug=False)

        elif event.type in {'MIDDLEMOUSE'} or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'SPACE'}:
            self.finish(context)

            if getattr(context.window_manager, "trimlib_" + self.library_name) != self.trim_name:
                mode = get_prefs().decalmode
                get_prefs().decalmode = "NONE"
                setattr(context.window_manager, "trimlib_" + self.library_name, self.trim_name)
                get_prefs().decalmode = mode

            if self.toggled_overlays:
                context.space_data.overlay.show_overlays = True

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal(context)

            if self.toggled_overlays:
                context.space_data.overlay.show_overlays = True

            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x
        self.last_mouse_y = event.mouse_y

        return {'RUNNING_MODAL'}

    def finish(self, context):
        if context.space_data.type == 'VIEW_3D':
            bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        elif context.space_data.type == 'IMAGE_EDITOR':
            bpy.types.SpaceImageEditor.draw_handler_remove(self.HUD, 'WINDOW')

        finish_status(self)

    def cancel_modal(self, context):
        self.finish(context)

        active, initbm, _ = self.data

        bpy.ops.object.mode_set(mode='OBJECT')
        initbm.to_mesh(active.data)
        bpy.ops.object.mode_set(mode='EDIT')

    def invoke(self, context, event):
        active = context.active_object

        mat, _, _ = get_most_used_sheetmat_from_selection(active)

        if mat:
            self.allowmodalmove = False
            self.allowmodalscale = False
            self.move = Vector((0, 0))
            self.scale = Vector((1, 1))
            self.quick_scale = False
            self.rotate = 0
            self.fit = 'NONE'
            self.toggled_overlays = False

            set_trim_uv_channel(active)

            sheetdata = get_sheetdata_from_uuid(mat.DM.trimsheetuuid)

            if sheetdata:
                self.library_name = sheetdata['name']

                self.trim = get_trim_from_selection(active, sheetdata)

                if self.trim:

                    self.uv_right, self.uv_up = self.get_uv_axes(context, active, debug=False)

                    if self.trim['isempty']:
                        popup_message(["Selected faces are of an empty trim and can't be adjusted.", "You can unwrap them to another trim at any time - either manually in the UV editor,", "or using the Trim Sheet libraries in the DECALmachine's edit mode pie."], title="Illegal Selection")

                    else:
                        if self.trim['ispanel']:
                            self.all_trims = [trim for trim in sheetdata['trims'] if trim['ispanel'] and not trim['isempty']]

                        else:
                            self.all_trims = [trim for trim in sheetdata['trims'] if not trim['ispanel'] and not trim['isempty']]

                        trim = context.window_manager.decaluuids.get(self.trim['uuid'])
                        self.trim_name = trim[0][0] if trim else ''

                        active.update_from_editmode()

                        initbm = bmesh.new()
                        initbm.from_mesh(active.data)
                        initbm.normal_update()

                        self.data = (active, initbm, sheetdata)

                        init_cursor(self, event)

                        init_status(self, context, 'Adjust Trim')

                        self.area = context.area
                        if context.space_data.type == 'VIEW_3D':

                            if context.space_data.overlay.show_overlays:
                                context.space_data.overlay.show_overlays = False
                                self.toggled_overlays = True

                            self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')

                        elif context.space_data.type == 'IMAGE_EDITOR':
                            self.HUD = bpy.types.SpaceImageEditor.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')

                        context.window_manager.modal_handler_add(self)
                        return {'RUNNING_MODAL'}

                else:
                    popup_message("Trim could not be determined from selection, likely because the faces have not been unwrapped.", title="Illegal Selection")
            else:
                popup_message("The Trim Sheet the current Trim Sheet Material is created from is not registered!", title="Trim Sheet not found!")

        else:
            popup_message("Selected faces don't have a sheet material applied", title="Illegal Selection")

        return {'CANCELLED'}

    def main(self):
        bpy.ops.object.mode_set(mode='OBJECT')

        active, initbm, sheetdata = self.data

        sheetresolution = Vector(sheetdata.get('resolution'))
        trimlocation = Vector(self.trim.get('location'))
        trimscale = Vector(self.trim.get('scale'))

        bm = initbm.copy()

        faces = [f for f in bm.faces if f.select]

        uvs = bm.loops.layers.uv.active
        loops = [loop for face in faces for loop in face.loops]

        rmx = Matrix.Rotation(radians(self.rotate), 2)

        if self.fit != 'NONE':

            for loop in loops:
                loop[uvs].uv = rmx @ loop[uvs].uv

            rmx = Matrix(((1, 0), (0, 1)))

            selbbox, selmid, selscale = get_selection_uv_bbox(uvs, loops)

            trimbbox, trimmid = get_trim_uv_bbox(sheetresolution, trimlocation, trimscale)

            selratio = selscale.x / selscale.y
            trimratio = trimscale.x / trimscale.y

            if self.fit == 'AUTO':
                if self.trim['ispanel']:
                    smx = Matrix.Scale(trimscale.y / selscale.y, 2)

                else:
                    smx = Matrix(((trimscale.x / selscale.x, 0), (0, trimscale.y / selscale.y)))

            elif self.fit == 'STRETCH':
                smx = Matrix(((trimscale.x / selscale.x, 0), (0, trimscale.y / selscale.y)))

            elif self.fit == 'FITINSIDE':
                smx = Matrix.Scale(trimscale.y / selscale.y, 2) if selratio < trimratio else Matrix.Scale(trimscale.x / selscale.x, 2)

            elif self.fit == 'FITOUTSIDE':
                smx = Matrix.Scale(trimscale.y / selscale.y, 2) if selratio > trimratio else Matrix.Scale(trimscale.x / selscale.x, 2)

            for loop in loops:
                loop[uvs].uv = trimmid + smx @ (loop[uvs].uv - selmid)

        selbbox, selmid, selscale = get_selection_uv_bbox(uvs, loops)

        if self.trim['ispanel'] and self.quick_scale:
            smx = Matrix(((trimscale.x / selscale.x / 2, 0), (0, 1)))

        else:
            smx = Matrix(((self.scale[0], 0), (0, self.scale[1])))

        for loop in loops:
            loop[uvs].uv = self.move + selmid + rmx @ smx @ (loop[uvs].uv - selmid)

        bm.to_mesh(active.data)
        bm.free()

        bpy.ops.object.mode_set(mode='EDIT')

    def get_uv_axes(self, context, active, debug=False):
        if context.space_data.type == 'VIEW_3D':
            r3d = context.space_data.region_3d

            view_origin = region_2d_to_origin_3d(context.region, r3d, (context.region.width / 2, context.region.height / 2), clamp=None)

            view_right = r3d.view_rotation @ Vector((1, 0, 0))
            view_up = r3d.view_rotation @ Vector((0, 1, 0))

            if debug:
                draw_point(view_origin.copy(), size=10, modal=False)
                draw_vector(view_up, origin=view_origin, color=(0, 0, 1), modal=False)
                draw_vector(view_right, origin=view_origin, color=(1, 0, 0), modal=False)

            mx = active.matrix_world

            bm = bmesh.from_edit_mesh(active.data)
            uvs = bm.loops.layers.uv.active

            faces = [f for f in bm.faces if f.select]

            face = min([((mx @ f.calc_center_median() - view_origin).length, f) for f in faces])[1]

            if debug:
                draw_point(face.calc_center_median(), mx=active.matrix_world, color=(1, 1, 0), modal=False)

            loops = []

            for l in face.loops:
                loop_dir = (mx.to_3x3() @ (l.link_loop_next.vert.co - l.vert.co)).normalized()

                if debug:
                    draw_vector(loop_dir, origin=mx @ l.vert.co, color=(0, 1, 0), modal=False)

                dot = view_right.dot(loop_dir)
                loops.append((dot, l))

            loop = max(loops, key=lambda x: abs(x[0]))

            flip_direction = True if loop[0] < 0 else False
            view_right_loop = loop[1]

            if debug:
                print(view_right_loop, flip_direction)

            uv_loop_dir = (view_right_loop.link_loop_next[uvs].uv - view_right_loop[uvs].uv).normalized()

            if debug:
                print(uv_loop_dir)

            axes = []

            for axis in [Vector((1, 0)), Vector((0, 1)), Vector((-1, 0)), Vector((0, -1))]:
                dot = uv_loop_dir.dot(axis)

                axes.append((dot, axis))

            uv_right = max(axes, key=lambda x: x[0])[1]

            if flip_direction:
                uv_right.negate()

            uv_up = Vector(uv_up_axis_mapping_dict[tuple(uv_right)])

            if debug:
                print("was flipped:", flip_direction)
                print("moving right moves along:", uv_right, "was flipped:", flip_direction)
                print("moving up moves along:", uv_up)

                context.area.tag_redraw()

            return uv_right, uv_up
        return Vector((-1, 0)), Vector((0, -1))
