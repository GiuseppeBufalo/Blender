import bpy
import bmesh
from math import degrees, radians, sqrt
from mathutils import Vector, Matrix
from bpy.types import Operator
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d
from .ke_utils import mouse_raycast, getset_transform, get_distance, correct_normal, average_vector, \
    set_active_collection
from sys import platform
from bpy.app.handlers import persistent


# -------------------------------------------------------------------------------------------------
# Misc operators
# -------------------------------------------------------------------------------------------------
class OBJECT_OT_ke_select_by_displaytype(Operator):
    bl_idname = "object.ke_select_by_displaytype"
    bl_label = "Select by Display Type"
    bl_description = "Select objects in scene by viewport display type"
    bl_options = {'REGISTER', 'UNDO'}

    dt : bpy.props.StringProperty(name="Display Type", default="BOUNDS", options={"HIDDEN"})

    def execute(self, context):
        dt_is_bounds = False
        bounds = ['CAPSULE', 'CONE', 'CYLINDER', 'SPHERE', 'BOX']
        if self.dt in bounds:
            dt_is_bounds = True

        for o in context.scene.objects:
            if o.visible_get():
                if dt_is_bounds and o.display_type == 'BOUNDS':
                    if o.display_bounds_type == self.dt:
                        o.select_set(True)
                else:
                    if o.display_type == self.dt:
                        o.select_set(True)

        return {'FINISHED'}


class VIEW3D_OT_ke_show_in_outliner(Operator):
    bl_idname = "view3d.ke_show_in_outliner"
    bl_label = "Show in Outliner"
    bl_description = "Locate the selected object(s) in the outliner (& set parent Collection as Active)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        sel_objects = [o for o in context.selected_objects]

        override = None
        for area in context.screen.areas:
            if 'OUTLINER' in area.type:
                for region in area.regions:
                    if 'WINDOW' in region.type:
                        override = {'area': area, 'region': region}
                        break
                break

        if not sel_objects or override is None:
            self.report({"INFO"}, "Nothing selected? / Outliner not found?")
            return {"CANCELLED"}

        for obj in sel_objects:
            context.view_layer.objects.active = obj
            bpy.ops.outliner.show_active(override)

        # set_active_collection(context, sel_objects[-1])

        return {"FINISHED"}


def menu_show_in_outliner(self, context):
    self.layout.operator(VIEW3D_OT_ke_show_in_outliner.bl_idname, text=VIEW3D_OT_ke_show_in_outliner.bl_label)


class VIEW3D_OT_ke_set_active_collection(Operator):
    bl_idname = "view3d.ke_set_active_collection"
    bl_label = "Set Active Collection"
    bl_description = "Set selected object's parent collection as Active (use from Object Context Menu)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        set_active_collection(context, context.object)
        return {"FINISHED"}


def menu_set_active_collection(self, context):
    self.layout.operator(VIEW3D_OT_ke_set_active_collection.bl_idname, text=VIEW3D_OT_ke_set_active_collection.bl_label)


class MESH_OT_ke_facematch(Operator):
    bl_idname = "mesh.ke_facematch"
    bl_label = "Scale From Faces"
    bl_description = "Scales selected object(s) by the size(area) difference of selected faces to match last selected "\
                     "face\nSelect 1 Face per Object, in Multi-Edit mode\nScale will be auto-applied"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def execute(self, context):
        sel_objects = [o for o in context.selected_objects]

        if len(sel_objects) < 2:
            self.report({"INFO"}, "Invalid Selection (2+ Objects required)")
            return {"CANCELLED"}

        src_obj = context.object
        sel_obj = [o for o in sel_objects if o != src_obj]

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)
        bpy.ops.object.editmode_toggle()

        bma = bmesh.from_edit_mesh(src_obj.data)
        fa = [f for f in bma.faces if f.select]
        if fa:
            fa = fa[-1]
        else:
            self.report({"INFO"}, "Target Object has no selected faces?")
            return {"CANCELLED"}

        ratio = 1

        for o in sel_obj:
            bmb = bmesh.from_edit_mesh(o.data)
            fb = [f for f in bmb.faces if f.select]
            if fb:
                fb = fb[-1]
                try:
                    ratio = sqrt(fa.calc_area() / fb.calc_area())
                except ZeroDivisionError:
                    self.report({"INFO"}, "Zero Division Error. Invalid geometry?")

                o.scale *= ratio

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)
        bpy.ops.object.editmode_toggle()
        return {"FINISHED"}


class OBJECT_OT_ke_bbmatch(Operator):
    bl_idname = "object.ke_bbmatch"
    bl_label = "Match Active Bounding Box"
    bl_description = "Scales selected object(s) to last selected object bounding box (along axis chosen in redo)\n" \
                     "Make sure origin(s) is properly placed beforehand\nScale will be auto-applied"
    bl_options = {'REGISTER', 'UNDO'}

    mode : bpy.props.EnumProperty(
        items=[("UNIT", "Longest Axis (Unit)", "", 1),
               ("ALL", "All Axis", "", 2),
               ("X", "X Only", "", 3),
               ("Y", "Y Only", "", 4),
               ("Z", "Z Only", "", 5),
               ],
        name="Scaling", default="UNIT",
        description="Choose which Bounding Box Axis to scale with")

    match_loc : bpy.props.BoolProperty(name="Location", default=False)
    match_rot : bpy.props.BoolProperty(name="Rotation", default=False)

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "mode", expand=True)
        layout.separator(factor=0.5)
        row = layout.row()
        row.prop(self, "match_loc", toggle=True)
        row.prop(self, "match_rot", toggle=True)
        layout.separator(factor=0.5)

    def execute(self, context):
        sel_objects = [o for o in context.selected_objects]

        if not len(sel_objects) >= 2:
            self.report({"INFO"}, "Invalid Selection (2+ required)")
            return {"CANCELLED"}

        src_obj = context.object
        src_bb = src_obj.dimensions

        if self.mode == "UNIT":
            v = sorted(src_bb)[-1]
            src_bb = [v, v, v]
        elif self.mode == "X":
            v = src_bb[0]
            src_bb = [v, 1, 1]
        elif self.mode == "Y":
            v = src_bb[1]
            src_bb = [1, v, 1]
        elif self.mode == "Z":
            v = src_bb[2]
            src_bb = [1, 1, v]

        target_objects = [o for o in sel_objects if o != src_obj]

        bpy.ops.object.transform_apply(scale=True, location=False, rotation=False, )

        for o in target_objects:

            bb = o.dimensions
            if self.mode == "UNIT":
                v = sorted(bb)[-1]
                bb = [v, v, v]
            elif self.mode == "X":
                v = bb[0]
                bb = [v, 1, 1]
            elif self.mode == "Y":
                v = bb[1]
                bb = [1, v, 1]
            elif self.mode == "Z":
                v = bb[2]
                bb = [1, 1, v]

            o.scale[0] *= (src_bb[0] / bb[0])
            o.scale[1] *= (src_bb[1] / bb[1])
            o.scale[2] *= (src_bb[2] / bb[2])

            if self.match_loc:
                o.location = src_obj.location
            if self.match_rot:
                o.rotation_euler = src_obj.rotation_euler

        bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)

        return {"FINISHED"}


class MESH_OT_ke_select_flipped_normal(Operator):
    bl_idname = "mesh.ke_select_flipped_normal"
    bl_label = "Select Flipped Normal Faces"
    bl_description = "Selects flipped normal faces (the 'red' faces in 'face orientation' overlay)"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        items=[("CONNECTED", "Connected", "", 1),
               ("AVERAGE", "Average", "", 2)
               ],
        name="Method", default="CONNECTED",
        description="Choose which method used to find flipped faces.\n"
                    "Average works better for (mostly flat) disconnected mesh islands.\n"
                    "Connected works best in most other cases.")
    invert : bpy.props.BoolProperty(name="Invert Selection", default=False)

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "mode", expand=True)
        layout.separator(factor=0.5)
        layout.prop(self, "invert", toggle=True)
        layout.separator(factor=0.5)

    def execute(self, context):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        if self.mode == "AVERAGE":
            avg_normal = average_vector([f.normal for f in bm.faces])
            if self.invert:
                for f in bm.faces:
                    if avg_normal.dot(f.normal) > 0:
                        f.select_set(True)
            else:
                for f in bm.faces:
                    if avg_normal.dot(f.normal) < 0:
                        f.select_set(True)
        else:
            cbm = bm.copy()
            bmesh.ops.recalc_face_normals(cbm, faces=cbm.faces)
            if self.invert:
                for f, of in zip(cbm.faces, bm.faces):
                    if f.normal == of.normal:
                        of.select_set(True)
            else:
                for f, of in zip(cbm.faces, bm.faces):
                    if f.normal != of.normal:
                        of.select_set(True)
            cbm.free()
        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


class MESH_OT_ke_mouse_side_of_active(Operator):
    bl_idname = "mesh.ke_mouse_side_of_active"
    bl_label = "Mouse Side of Active"
    bl_description = "Side of Active, but with active vert, edge or face and mouse position " \
                     "to calculate which side of the active element to select"
    bl_options = {'REGISTER', 'UNDO'}

    mouse_pos : bpy.props.IntVectorProperty(size=2)

    axis_mode : bpy.props.EnumProperty(
        items=[("GLOBAL", "Global", "", 1),
               ("LOCAL", "Local", "", 2),
               ("NORMAL", "Normal", "", 3),
               ("GIMBAL", "Gimbal", "", 4),
               ("VIEW", "View", "", 5),
               ("CURSOR", "Cursor", "", 6),
               ("MOUSE", "Mouse Pick", "", 7)
               ],
        name="Axis Mode", default="MOUSE")

    axis_sign : bpy.props.EnumProperty(
        items=[("POS", "Positive Axis", "", 1),
               ("NEG", "Negative Axis", "", 2),
               ("ALIGN", "Aligned Axis", "", 3),
               ("MOUSE", "Mouse Pick", "", 4)
               ],
        name="Axis Sign", default="MOUSE")

    axis : bpy.props.EnumProperty(
        items=[("X", "X", "", 1),
               ("Y", "Y", "", 2),
               ("Z", "Z", "", 3),
               ("MOUSE", "Mouse Pick", "", 4)
               ],
        name="Axis", default="MOUSE")

    threshold : bpy.props.FloatProperty(min=0, max=10, default=0, name="Threshold")

    mouse_pick = ""

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.use_property_split = True
        col.prop(self, "axis_mode")
        col.prop(self, "axis_sign")
        col.prop(self, "axis")
        col.prop(self, "threshold")
        col.separator(factor=1)
        col = layout.column()
        col.active = False
        col.alignment = "RIGHT"
        col.label(text=self.mouse_pick)


    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode and
                context.space_data.type == "VIEW_3D")

    def invoke(self, context, event):
        self.mouse_pos[0] = int(event.mouse_region_x)
        self.mouse_pos[1] = int(event.mouse_region_y)
        return self.execute(context)

    def execute(self, context):

        if self.axis_mode != "MOUSE":
            m_axis_mode = self.axis_mode
        else:
            m_axis_mode = getset_transform(setglobal=False)[0]

        sel_mode = bpy.context.tool_settings.mesh_select_mode[:]
        obj = context.object
        obj_mtx = obj.matrix_world
        tm = Matrix().to_3x3()

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.verts.ensure_lookup_table()
        ae = bm.select_history.active
        og_ae = ae

        if ae is None:
            self.report({"INFO"}, "No active element selected")
            return {"CANCELLED"}

        # Set active vert to furthest from mouse if not vert mode
        if not isinstance(ae, bmesh.types.BMVert):
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action="DESELECT")

            candidate = []
            c_d = 0
            for v in ae.verts:
                sco = location_3d_to_region_2d(context.region, context.region_data, obj_mtx @ v.co)
                if sco is None:
                    # Just in case
                    print("3D to 2D position failed. Try different angle?")
                    return {"CANCELLED"}

                d = get_distance(self.mouse_pos, sco)
                if d > c_d or not candidate:
                    candidate = v
                    c_d = d

            bm.select_history.add(candidate)
            ae = candidate

        else:
            for v in bm.verts:
                v.select = False

        ae.select = True
        bmesh.update_edit_mesh(me)

        ae_wco = obj_mtx @ ae.co
        mouse_wpos = region_2d_to_location_3d(context.region, context.region_data, self.mouse_pos, ae_wco)

        # ORIENTATION  ---------------------------------------------------------------------------------------
        if m_axis_mode == "LOCAL":
            tm = obj_mtx.to_3x3()

        elif m_axis_mode == "CURSOR":
            tm = context.scene.cursor.matrix.to_3x3()

        elif m_axis_mode == "NORMAL":
            normal = correct_normal(obj_mtx, ae.normal)
            # Blender default method (for tangent/rot mtx calc) in this case? IDFK, seems to match...
            tm = normal.to_track_quat('Z', 'Y').to_matrix().to_3x3()
            # ...with compensating rotation
            tm @= Matrix.Rotation(radians(180.0), 3, 'Z')

        elif m_axis_mode == "VIEW":
            tm = context.space_data.region_3d.view_matrix.inverted().to_3x3()

        # else : GLOBAL default transf.mtx for the rest

        # AXIS CALC ---------------------------------------------------------------------------------------
        v = tm.inverted() @ Vector(mouse_wpos - ae_wco).normalized()
        x, y, z = abs(v[0]), abs(v[1]), abs(v[2])

        m_axis_sign = "POS"

        if x > y and x > z:
            m_axis = "X"
            if v[0] < 0:
                m_axis_sign = "NEG"
        elif y > x and y > z:
            m_axis = "Y"
            if v[1] < 0:
                m_axis_sign = "NEG"
        else:
            m_axis = "Z"
            if v[2] < 0:
                m_axis_sign = "NEG"

        # Check overrides
        if self.axis_sign != "MOUSE":
            sign = self.axis_sign
        else:
            sign = m_axis_sign
        if self.axis != "MOUSE":
            axis = self.axis
        else:
            axis = m_axis

        bpy.ops.mesh.select_axis(orientation=m_axis_mode, sign=sign, axis=axis, threshold=self.threshold)

        if sel_mode[1]:
            bpy.ops.mesh.select_mode(type='EDGE')
            bm.select_history.add(og_ae)
            og_ae.select_set(True)

        if sel_mode[2]:
            bpy.ops.mesh.select_mode(type='FACE')
            bm.select_history.add(og_ae)
            og_ae.select_set(True)

        if m_axis_sign == "POS":
            rs = "+      "
        else:
            rs = "-      "
        self.mouse_pick = "Mouse Pick:  " + m_axis_mode.capitalize() + " " + m_axis + rs

        return {'FINISHED'}



class VIEW3D_OT_ke_unhide_or_local(Operator):
    bl_idname = "view3d.ke_unhide_or_local"
    bl_label = "Unhide or Local Off"
    bl_description = "Unhides hidden items OR toggles Local mode OFF, if currently in Local mode"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "VIEW_3D"

    def execute(self, context):
        if context.space_data.local_view:
            bpy.ops.view3d.localview(frame_selected=False)
        else:
            bpy.ops.object.hide_view_clear(select=False)
        return {"FINISHED"}


class VIEW3D_OT_ke_lock(Operator):
    bl_idname = "view3d.ke_lock"
    bl_label = "Lock & Unlock"
    bl_description = "Lock/Lock Unselected: Disable Selection for selected/unselected object(s)\n" \
                     "(Status in Outliner (check filter))\n" \
                     "Unlock: Enables Selection for all objects"

    mode : bpy.props.EnumProperty(
        items=[("LOCK", "Lock", "", 1),
               ("LOCK_UNSELECTED", "Lock Unselected", "", 2),
               ("UNLOCK", "Unlock", "", 3)
               ],
        name="Lock & Unlock",
        options={'HIDDEN'},
        default="LOCK")

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "VIEW_3D"

    def execute(self, context):

        if self.mode == "LOCK":
            for obj in context.selected_objects:
                obj.hide_select = True

        elif self.mode == "LOCK_UNSELECTED":
            sel = context.selected_objects[:]
            for obj in context.scene.objects:
                if obj not in sel:
                    obj.hide_select = True

        elif self.mode == "UNLOCK":
            for obj in context.scene.objects:
                obj.hide_select = False

        return {'FINISHED'}


class VIEW3D_OT_ke_shading_toggle(Operator):
    bl_idname = "view3d.ke_shading_toggle"
    bl_label = "Shading Toggle"
    bl_description = "Toggles selected object(s) between Flat & Smooth shading.\nAlso works in Edit mode."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        aso = []
        cm = str(context.mode)
        tri_mode = bpy.context.scene.kekit.shading_tris

        if cm != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
            if cm == "EDIT_MESH":
                cm = "EDIT"

        for obj in context.selected_objects:

            try:
                current = obj.data.polygons[0].use_smooth
            except AttributeError:
                self.report({"WARNING"}, "Invalid Object selected for Smooth/Flat Shading Toggle - Cancelled")
                return {"CANCELLED"}

            if tri_mode:
                tmod = None
                mindex = len(obj.modifiers) - 1
                for m in obj.modifiers:
                    if m.name == "Triangulate Shading":
                        tmod = m
                        if current is False:
                            bpy.ops.object.modifier_remove(modifier="Triangulate Shading")
                        else:
                            bpy.ops.object.modifier_move_to_index(modifier="Triangulate Shading", index=mindex)

                if tmod is None and current:
                    obj.modifiers.new(name="Triangulate Shading", type="TRIANGULATE")

            val = [not current]
            values = val * len(obj.data.polygons)
            obj.data.polygons.foreach_set("use_smooth", values)
            obj.data.update()

            if not current is True:
                mode = " > Smooth"
            else:
                mode = " > Flat"
            aso.append(obj.name + mode)


        bpy.ops.object.mode_set(mode=cm)

        if len(aso) > 5:
            t = "%s objects" %str(len(aso))
        # t = "'" + "','".join(aso[:5]) + "'" + ".. " + "(%s objects)" % str(len(aso))
        else:
            t = ", ".join(aso)
        self.report({"INFO"}, "Toggled: %s" % t)

        return {"FINISHED"}


class SCREEN_OT_ke_render_visible(Operator):
    bl_idname = "screen.ke_render_visible"
    bl_label = "Render Visible"
    bl_description = "Render only what is currently visible in the viewport - Regardless of outliner settings"
    bl_options = {'REGISTER'}

    _timer = None
    stop = False
    objects = []
    og_states = []
    cycle = False

    @persistent
    def init_render(self, scene, depsgraph):
        scene.ke_is_rendering = True
    # print("Render Starting")

    @persistent
    def post_render(self, scene, depsgraph):
        scene.ke_is_rendering = False
    # print("Render Done")

    def execute(self, context):
        # Camera Check
        cam = [o for o in context.scene.objects if o.type == "CAMERA"]
        if not cam:
            self.report({'INFO'}, "No Cameras found?")
            return {"CANCELLED"}

        # Load Handlers
        handlers = [h.__name__ for h in bpy.app.handlers.render_post]
        handlers_active = True if [h == 'post_render' for h in handlers] else False
        if not handlers_active:
            bpy.app.handlers.render_init.append(self.init_render)
            bpy.app.handlers.render_post.append(self.post_render)
        # print("keKit Render Handlers Loaded")

        # Check rendering status
        rendering = bpy.context.scene.ke_is_rendering

        if not rendering:
            # Grab visibility states & setup
            cat = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'HAIR', 'GPENCIL',
                   'VOLUME', 'ARMATURE', 'EMPTY', 'LIGHT', 'LIGHT_PROBE' }
            self.objects = [o for o in context.scene.objects if o.type in cat]
            visible = [o for o in context.visible_objects if o.type in cat]
            self.og_states = [s.hide_render for s in self.objects]
            self.cycle = bpy.context.scene.kekit.renderslotcycle

            for o in self.objects:
                o.hide_render = True
            for o in visible:
                o.hide_render = False

            # # Running Modal timer hack so we can see render progress...
            self._timer = bpy.context.window_manager.event_timer_add(0.1, window=context.window)
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        else:
            return {"CANCELLED"}


    def modal(self, context, event):
        if event.type == 'TIMER':
            if self.stop or event.type == "ESC":
                if not context.scene.ke_is_rendering:
                    # remove timer
                    context.window_manager.event_timer_remove(self._timer)
                    # restore visibility states
                    for o, s in zip(self.objects, self.og_states):
                        o.hide_render = s
                    return {"FINISHED"}

            elif not self.stop:
                if self.cycle:
                    status = bpy.ops.screen.ke_render_slotcycle("INVOKE_DEFAULT")
                    if status == {"CANCELLED"}:
                        self.report({"WARNING"}, "SC: All Render Slots are full!")
                else:
                    bpy.ops.render.render("INVOKE_DEFAULT")
                self.stop = True

        return {"PASS_THROUGH"}


class SCREEN_OT_ke_render_slotcycle(Operator):
    bl_idname = "screen.ke_render_slotcycle"
    bl_label = "Render Image Slot Cycle"
    bl_description = "Render Image to the first empty render slot"
    bl_options = {'REGISTER'}

    @persistent
    def init_render(self, scene, depsgraph):
        scene.ke_is_rendering = True
    # print("Render Starting")

    @persistent
    def post_render(self, scene, depsgraph):
        scene.ke_is_rendering = False
    # print("Render Done")

    def execute(self, context):
        # Camera Check
        cam = [o for o in context.scene.objects if o.type == "CAMERA"]
        if not cam:
            self.report({'INFO'}, "No Cameras found?")
            return {"CANCELLED"}

        # Load Handlers
        handlers = [h.__name__ for h in bpy.app.handlers.render_post]
        handlers_active = True if [h == 'post_render' for h in handlers] else False
        if not handlers_active:
            bpy.app.handlers.render_init.append(self.init_render)
            bpy.app.handlers.render_post.append(self.post_render)
        # print("keKit Render Handlers Loaded")

        # Check rendering status
        rendering = bpy.context.scene.ke_is_rendering

        if not rendering:
            full_wrap = bool(bpy.context.scene.kekit.renderslotfullwrap)
            Null = '/nul' if platform == 'win32' else '/dev/null'
            r = [i for i in bpy.data.images if i.name == 'Render Result']
            # Check & set active renderslot
            if r:
                r = r[0]
                if r.has_data:
                    # AFAICT Only possible hacky way to find 1st empty
                    current = int(r.render_slots.active_index)
                    total = len(r.render_slots)
                    step = 0
                    for i in range(total):
                        r.render_slots.active_index = step
                        try:
                            r.save_render(Null)
                            step += 1
                        except RuntimeError:
                            break

                    if full_wrap and step == total:
                        if current < (total - 1):
                            r.render_slots.active_index = current + 1
                        else:
                            r.render_slots.active_index = 0
                            self.report({"INFO"}, "Render Slot Cycle FW: New cycle starting on slot 1")

                    else:
                        if step < total:
                            r.render_slots.active_index = step
                        else:
                            self.report({"WARNING"}, "Render Slot Cycle: All Render Slots are full!")
                            r.render_slots.active_index = current
                            return {"CANCELLED"}
                else:
                    r.render_slots.active_index = 0

            bpy.ops.render.render("INVOKE_DEFAULT", use_viewport=True)

        else:
            self.report({'INFO'}, "Not ready: Another render still in progress.")

        return {"FINISHED"}


class VIEW3D_OT_ke_cursor_clear_rotation(Operator):
    bl_idname = "view3d.ke_cursor_clear_rot"
    bl_label = "Clear Cursor Rotation"
    bl_description = "Clear the cursor's rotation (only)"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "VIEW_3D"

    def execute(self, context):
        c = context.scene.cursor
        if c.rotation_mode == "QUATERNION":
            c.rotation_quaternion = 1, 0, 0, 0
        elif c.rotation_mode == "AXIS_ANGLE":
            c.rotation_axis_angle = 0, 0, 1, 0
        else:
            c.rotation_euler = 0, 0, 0

        return {'FINISHED'}



class VIEW3D_OT_ke_cursor_bookmark(Operator):
    bl_idname = "view3d.ke_cursor_bookmark"
    bl_label = "Cursor Bookmarks"
    bl_description = "Store & Use Cursor Transforms"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    mode : bpy.props.EnumProperty(
        items=[("SET1", "Set Cursor Slot 1", "", 1),
               ("SET2", "Set Cursor Slot 2", "", 2),
               ("SET3", "Set Cursor Slot 3", "", 3),
               ("SET4", "Set Cursor Slot 4", "", 4),
               ("SET5", "Set Cursor Slot 5", "", 5),
               ("SET6", "Set Cursor Slot 6", "", 6),
               ("USE1", "Use Cursor Slot 1", "", 7),
               ("USE2", "Use Cursor Slot 2", "", 8),
               ("USE3", "Use Cursor Slot 3", "", 9),
               ("USE4", "Use Cursor Slot 4", "", 10),
               ("USE5", "Use Cursor Slot 5", "", 11),
               ("USE6", "Use Cursor Slot 6", "", 12)
               ],
        name="Cursor Bookmarks",
        options={'HIDDEN'},
        default="SET1")

    val : bpy.props.FloatVectorProperty(size=6, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        if properties.mode in {"SET1", "SET2","SET3", "SET4", "SET5", "SET6" }:
            return "Store Cursor Transform in slot " + properties.mode[-1]
        else:
            return "Recall Cursor Transform from slot " + properties.mode[-1]

    def execute(self, context):
        c = context.scene.cursor
        if c.rotation_mode == "QUATERNION" or c.rotation_mode == "AXIS_ANGLE":
            self.report({"INFO"}, "Cursor Mode is not Euler: Not supported - Aborted.")

        if "SET" in self.mode:
            op = "SET"
        else:
            op = "USE"

        nr = int(self.mode[-1])
        if nr == 1:
            slot = bpy.context.scene.ke_cslot1
        elif nr == 2:
            slot = bpy.context.scene.ke_cslot2
        elif nr == 3:
            slot = bpy.context.scene.ke_cslot3
        elif nr == 4:
            slot = bpy.context.scene.ke_cslot4
        elif nr == 5:
            slot = bpy.context.scene.ke_cslot5
        elif nr == 6:
            slot = bpy.context.scene.ke_cslot6

        if op == "SET":
            self.val = c.location[0], c.location[1], c.location[2], c.rotation_euler[0], c.rotation_euler[1], c.rotation_euler[2]
            slot[0] = self.val[0]
            slot[1] = self.val[1]
            slot[2] = self.val[2]
            slot[3] = self.val[3]
            slot[4] = self.val[4]
            slot[5] = self.val[5]

        elif op == "USE":
            self.val[0] = slot[0]
            self.val[1] = slot[1]
            self.val[2] = slot[2]
            self.val[3] = slot[3]
            self.val[4] = slot[4]
            self.val[5] = slot[5]

            c.location = self.val[0], self.val[1], self.val[2]
            c.rotation_euler = self.val[3], self.val[4], self.val[5]

        return {"FINISHED"}


class MESH_OT_ke_select_invert_linked(Operator):
    bl_idname = "mesh.ke_select_invert_linked"
    bl_label = "Select Invert Linked"
    bl_description = "Inverts selection only on connected/linked mesh geo"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def check_selection(self, bm, sel_mode):
        if sel_mode[2]:
            return [p for p in bm.faces if p.select]
        elif sel_mode[1]:
            return [e for e in bm.edges if e.select]
        else:
            return [v for v in bm.verts if v.select]

    def execute(self, context):
        sel_mode = bpy.context.tool_settings.mesh_select_mode[:]
        me = context.object.data
        bm = bmesh.from_edit_mesh(me)

        og_sel = self.check_selection(bm, sel_mode)

        if og_sel:
            bpy.ops.mesh.select_linked()
            re_sel = self.check_selection(bm, sel_mode)

            if len(re_sel) == len(og_sel):
                bpy.ops.mesh.select_all(action='INVERT')
            else:
                for v in og_sel:
                    v.select = False

        bm.select_flush_mode()
        bmesh.update_edit_mesh(me)

        return {'FINISHED'}


class MESH_OT_ke_select_collinear(Operator):
    bl_idname = "mesh.ke_select_collinear"
    bl_label = "Select Collinear Verts"
    bl_description = "Selects Collinear Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def is_bmvert_collinear(self, v):
        le = v.link_edges
        if len(le) == 2:
            vec1 = Vector(v.co - le[0].other_vert(v).co)
            vec2 = Vector(v.co - le[1].other_vert(v).co)
            if abs(vec1.angle(vec2)) >= 3.1415:
                return True
        return False

    def execute(self, context):
        sel_obj = [o for o in context.selected_objects if o.type == "MESH"]
        obj = context.active_object
        if not obj:
            obj = sel_obj[0]

        og_mode = [b for b in bpy.context.tool_settings.mesh_select_mode]
        context.tool_settings.mesh_select_mode = (True,False,False)
        bpy.ops.mesh.select_all(action='DESELECT')

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.select_mode = {'VERT'}

        count = 0
        for v in bm.verts:
            if self.is_bmvert_collinear(v):
                v.select = True
                count += 1

        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data)

        if count > 0:
            self.report({"INFO"}, "Total Collinear Verts Found: %s" % count)
        else:
            context.tool_settings.mesh_select_mode = og_mode
            self.report({"INFO"}, "No Collinear Verts Found")

        return {"FINISHED"}


class MESH_OT_ke_select_boundary(Operator):
    bl_idname = "mesh.ke_select_boundary"
    bl_label = "select boundary(+active)"
    bl_description = "Select Boundary edges & sets one edge active\n" \
                     "Run again on a selected boundary to toggle to inner region selection\n" \
                     "Nothing selected = Selects all -border- edges"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def execute(self, context):
        og_mode = context.tool_settings.mesh_select_mode[:]
        obj = bpy.context.active_object
        if obj is None:
            obj = context.object

        bm = bmesh.from_edit_mesh(obj.data)

        sel_verts = [v for v in bm.verts if v.select]
        og_edges = [e for e in bm.edges if e.select]

        if len(sel_verts) == 0:
            bpy.ops.mesh.select_all(action='SELECT')

        bpy.ops.mesh.region_to_loop()

        sel_edges = [e for e in bm.edges if e.select]

        if sel_edges:
            sel_check = [e for e in bm.edges if e.select]
            toggle = set(og_edges) == set(sel_check)

            if toggle:
                bpy.ops.mesh.loop_to_region()

            bm.select_history.clear()
            bm.select_history.add(sel_edges[0])
        else:
            context.tool_settings.mesh_select_mode = og_mode

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


class VIEW3D_OT_selected_to_origin(Operator):
    bl_idname = "view3d.selected_to_origin"
    bl_label = "Selection to Origin"
    bl_description = "Places Selected Object Geo or Element Mode Selection at objects Origin (Location only)\n" \
                     "Object Mode function uses Set Origin - All options available in redo panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    o_type : bpy.props.EnumProperty(
        items=[("GEOMETRY_ORIGIN", "Geometry to Origin", "", 1),
               ("ORIGIN_GEOMETRY", "Origin to Geometry", "", 2),
               ("ORIGIN_CURSOR", "Origin to 3D Cursor", "", 3),
               ("ORIGIN_CENTER_OF_MASS", "Origin to Center of Mass (Surface)", "", 4),
               ("ORIGIN_CENTER_OF_VOLUME", "Origin to Center of Mass (Volume)", "", 5)
               ],
        name="Type",
        default="GEOMETRY_ORIGIN")

    o_center : bpy.props.EnumProperty(
        items=[("MEDIAN", "Median Center", "", 1),
               ("BOUNDS", "Bounds Center", "", 2)
               ],
        name="Center",
        default="MEDIAN")

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH')

    def execute(self, context):

        sel_obj = [o for o in context.selected_objects if o.type == "MESH"]
        if not sel_obj:
            self.report({'INFO'}, "Selection Error: No object(s) selected?")
            return {"CANCELLED"}

        og_mode = str(context.mode)

        if og_mode != "OBJECT":

            if self.o_type == "GEOMETRY_ORIGIN":
                c = context.scene.cursor
                og_cursor_loc = Vector(c.location)
                og_cursor_mode = str(c.rotation_mode)
                c.rotation_mode = "XYZ"
                og_cursor_rot = Vector(c.rotation_euler)
                c.rotation_euler = 0, 0, 0

                bpy.ops.object.mode_set(mode='OBJECT')

                for o in sel_obj:
                    o.select_set(False)

                for o in sel_obj:
                    o.select_set(True)
                    bpy.context.view_layer.objects.active = o
                    bpy.ops.object.mode_set(mode='EDIT')
                    if og_mode == "OBJECT":
                        bpy.ops.mesh.select_all(action="SELECT")
                    c.location = o.location
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
                    o.select_set(False)
                    bpy.ops.object.mode_set(mode='OBJECT')

                c.location = og_cursor_loc
                c.rotation_euler = og_cursor_rot
                c.rotation_mode = og_cursor_mode

                for o in sel_obj:
                    o.select_set(True)

                bpy.ops.object.mode_set(mode='EDIT')

            else:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.origin_set(type=self.o_type, center=self.o_center)

        else:
            bpy.ops.object.origin_set(type=self.o_type, center=self.o_center)

        return {'FINISHED'}


class VIEW3D_OT_origin_to_selected(Operator):
    bl_idname = "view3d.origin_to_selected"
    bl_label = "Origin To Selected Elements"
    bl_description = "Places origin(s) at element selection average\n" \
                     "(Location Only, Apply rotation for world rotation)"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH')

    def execute(self, context):
        cursor = context.scene.cursor
        rot = cursor.rotation_quaternion.copy()
        loc = cursor.location.copy()
        ogmode = str(cursor.rotation_mode)

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                context = bpy.context.copy()
                context['area'] = area
                context['region'] = area.regions[-1]

            if bpy.context.mode != "EDIT_MESH":
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            else:
                bpy.ops.view3d.snap_cursor_to_center()
                bpy.ops.view3d.snap_cursor_to_selected()
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

                cursor.location = loc
                cursor.rotation_mode = "QUATERNION"
                cursor.rotation_quaternion = rot
                cursor.rotation_mode = ogmode
                break

        return {'FINISHED'}


class VIEW3D_OT_ke_object_to_cursor(Operator):
    bl_idname = "view3d.ke_object_to_cursor"
    bl_label = "Align Object To Cursor"
    bl_description = "Aligns selected object(s) to Cursor (Rotation & Location)"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode != "EDIT_MESH"

    def execute(self, context):
        cursor = context.scene.cursor
        c_loc = cursor.location
        c_rot = cursor.rotation_euler
        for obj in context.selected_objects:
            obj.location = c_loc
            og_rot_mode = str(obj.rotation_mode)
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = c_rot
            obj.rotation_mode = og_rot_mode

        return {'FINISHED'}


class VIEW3D_OT_ke_origin_to_cursor(Operator):
    bl_idname = "view3d.ke_origin_to_cursor"
    bl_label = "Align Origin To Cursor"
    bl_description = "Aligns selected object(s) origin(s) to Cursor (Rotation,Location or both)"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    align: bpy.props.EnumProperty(
        items=[("LOCATION", "Location Only", "", 1),
               ("ROTATION", "Rotation Only", "", 2),
               ("BOTH", "Location & Rotation", "", 3)
               ],
        name="Align",
        default="BOTH")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        column = layout.column()
        column.prop(self, "align", expand=True)

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):

        if len(context.selected_objects) == 0:
            return {"CANCELLED"}

        if context.object.type == 'MESH':
            if context.object.data.is_editmode:
                bpy.ops.object.mode_set(mode="OBJECT")

        if self.align == "BOTH":
            context.scene.tool_settings.use_transform_data_origin = True
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            bpy.ops.transform.transform(mode='ALIGN', value=(0, 0, 0, 0), orient_type='CURSOR', mirror=True,
                                        use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
                                        proportional_size=1, use_proportional_connected=False,
                                        use_proportional_projected=False)
            context.scene.tool_settings.use_transform_data_origin = False

        else:
            cursor = context.scene.cursor
            ogloc = list(cursor.location)

            if self.align =='LOCATION':
                context.scene.tool_settings.use_transform_data_origin = True
                bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
                context.scene.tool_settings.use_transform_data_origin = False

            elif self.align =='ROTATION':
                obj_loc = context.object.matrix_world.translation.copy()
                context.scene.tool_settings.use_transform_data_origin = True
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                bpy.ops.transform.transform(mode='ALIGN', value=(0, 0, 0, 0), orient_type='CURSOR', mirror=True,
                                            use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
                                            proportional_size=1, use_proportional_connected=False,
                                            use_proportional_projected=False)
                cursor.location = obj_loc
                bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
                context.scene.tool_settings.use_transform_data_origin = False
                cursor.location = ogloc

        bpy.ops.transform.select_orientation(orientation='LOCAL')

        return {'FINISHED'}


class VIEW3D_OT_align_origin_to_selected(Operator):
    bl_idname = "view3d.align_origin_to_selected"
    bl_label = "Align Origin To Selected Elements"
    bl_description = "Edit Mode: Places origin(s) at element selection (+orientation)\n" \
                     "Object Mode (1 selected): Set Origin to geo Center\n" \
                     "Object Mode (2 selected): Set Origin to 2nd Obj Origin\n"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        cursor = context.scene.cursor
        ogmode = str(cursor.rotation_mode)
        ogloc = cursor.location.copy()
        ogrot = cursor.rotation_quaternion.copy()

        if context.mode == "EDIT_MESH":
            cursor.rotation_mode = "QUATERNION"
            bpy.ops.view3d.cursor_fit_selected_and_orient()
            bpy.ops.view3d.ke_origin_to_cursor(align="BOTH")

            bpy.ops.transform.select_orientation(orientation='LOCAL')
            bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
            # bpy.ops.object.mode_set(mode="EDIT")
        else:
            target_obj = None
            sel_obj = [o for o in context.selected_objects]
            if sel_obj:
                sel_obj = [o for o in sel_obj]
            if context.active_object:
                target_obj = context.active_object
            if target_obj is None and sel_obj:
                target_obj = sel_obj[-1]
            if not target_obj:
                return {'CANCELLED'}

            sel_obj = [o for o in sel_obj if o != target_obj]

            # Center to mesh if only one object selected and active
            if not sel_obj and target_obj:
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            else:
                cursor.rotation_mode = "QUATERNION"
                cursor.location = target_obj.matrix_world.translation
                cursor.rotation_quaternion = target_obj.matrix_world.to_quaternion()

                bpy.ops.object.select_all(action='DESELECT')

                for o in sel_obj:
                    o.select_set(True)
                    bpy.ops.view3d.ke_origin_to_cursor(align="BOTH")
                    o.select_set(False)

                for o in sel_obj:
                    o.select_set(True)

        cursor.location = ogloc
        cursor.rotation_mode = "QUATERNION"
        cursor.rotation_quaternion = ogrot
        cursor.rotation_mode = ogmode

        return {"FINISHED"}


class VIEW3D_OT_ke_align_object_to_active(Operator):
    bl_idname = "view3d.ke_align_object_to_active"
    bl_label = "Align Object(s) To Active"
    bl_description = "Align selected object(s) to the Active Objects Transforms. (You may want to apply scale)"
    bl_space_type = 'VIEW_3D'
    bl_options = {'REGISTER', 'UNDO'}

    align: bpy.props.EnumProperty(
        items=[("LOCATION", "Location", "", 1),
               ("ROTATION", "Rotation", "", 2),
               ("BOTH", "Location & Rotation", "", 3)],
        name="Align", default="BOTH")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        column = layout.column()
        column.prop(self, "align", expand=True)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode != "EDIT_MESH"

    def execute(self, context):
        target_obj = None
        sel_obj = [o for o in context.selected_objects]
        if context.active_object:
            target_obj = context.active_object
        if target_obj is None and sel_obj:
            target_obj = sel_obj[-1]
        if not target_obj or len(sel_obj) < 2:
            print("Insufficent selection: Need at least 2 objects.")
            return {'CANCELLED'}

        sel_obj = [o for o in sel_obj if o != target_obj]

        for o in sel_obj:

            if self.align == "LOCATION":
                o.matrix_world.translation = target_obj.matrix_world.translation
            elif self.align == "ROTATION":
                og_pos = o.matrix_world.translation.copy()
                o.matrix_world = target_obj.matrix_world
                o.matrix_world.translation = og_pos
            elif self.align == "BOTH":
                o.matrix_world = target_obj.matrix_world

        return {"FINISHED"}


class VIEW3D_OT_ke_swap(Operator):
    bl_idname = "view3d.ke_swap"
    bl_label = "Swap Places"
    bl_description = "Swap places (transforms) for two objects. loc, rot & scale. (apply scale to avoid)"
    bl_space_type = 'VIEW_3D'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode != "EDIT_MESH"

    def execute(self, context):
        # CHECK SELECTION
        sel_obj = [o for o in context.selected_objects]
        if len(sel_obj) != 2:
            print("Incorrect Selection: Select 2 objects.")
            return {'CANCELLED'}
        # SWAP
        obj1 = sel_obj[0]
        obj2 = sel_obj[1]
        obj1_swap = obj2.matrix_world.copy()
        obj2_swap = obj1.matrix_world.copy()
        obj1.matrix_world = obj1_swap
        obj2.matrix_world = obj2_swap

        return {"FINISHED"}


class VIEW3D_OT_ke_overlays(Operator):
    bl_idname = "view3d.ke_overlays"
    bl_label = "Overlay Options & Toggles"
    bl_description = "Overlay Options & Toggles"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER'}

    overlay : bpy.props.EnumProperty(
        items=[("WIRE", "Show Wireframe", "", 1),
               ("EXTRAS", "Show Extras", "", 2),
               ("SEAMS", "Show Edge Seams", "", 3),
               ("SHARP", "Show Edge Sharp", "", 4),
               ("CREASE", "Show Edge Crease", "", 5),
               ("BEVEL", "Show Edge Bevel Weight", "", 6),
               ("FACEORIENT", "Show Face Orientation", "", 7),
               ("INDICES", "Show Indices", "", 8),
               ("ALLEDIT", "Toggle Edit Overlays", "", 9),
               ("ALL", "Toggle Overlays", "", 10),
               ("VN", "Vertex Normals", "", 11),
               ("SN", "Split Normals", "", 12),
               ("FN", "Face Normals", "", 13),
               ("BACKFACE", "Backface Culling", "", 14),
               ("ORIGINS", "Show Origins", "", 15),
               ("CURSOR", "Show Cursor", "", 16),
               ("OUTLINE", "Show Selection Outline", "", 17),
               ("WIREFRAMES", "Show Object Wireframes", "", 18),
               ("GRID", "Show Grid (3D View)", "", 19),
               ("OBJ_OUTLINE", "Show Object Outline", "", 20),
               ("WEIGHT", "Show Vertex Weights", "", 21),
               ("BONES", "Show Bones", "", 22),
               ("STATS", "Show Stats", "", 23),
               ("GRID_ORTHO", "Show Ortho Grid", "", 24),
               ("GRID_BOTH", "Show Floor & Ortho Grid", "", 25)
               ],
        name="Overlay Type",
        default="WIRE")


    def execute(self, context):
        o = context.space_data.overlay
        s = context.space_data.shading

        # Same for Edit mode and Object mode
        if self.overlay == "GRID" or self.overlay == "GRID_BOTH":
            status = o.show_floor
            o.show_floor = not status
            if not o.show_floor:
                o.show_axis_x = False
                o.show_axis_y = False
            # o.show_axis_z = False
            else:
                o.show_axis_x = True
                o.show_axis_y = True
            # o.show_axis_z = False
            if self.overlay == "GRID_BOTH":
                o.show_ortho_grid = not o.show_ortho_grid

        elif self.overlay == "GRID_ORTHO":
            o.show_ortho_grid = not o.show_ortho_grid

        elif self.overlay == "EXTRAS":
            o.show_extras = not o.show_extras

        elif self.overlay == "ALL":
            o.show_overlays = not o.show_overlays

        elif self.overlay == "ORIGINS":
            o.show_object_origins = not o.show_object_origins

        elif self.overlay == "OUTLINE":
            o.show_outline_selected = not o.show_outline_selected

        elif self.overlay == "CURSOR":
            o.show_cursor = not o.show_cursor

        elif self.overlay == "OBJ_OUTLINE":
            s.show_object_outline = not s.show_object_outline

        elif self.overlay == "BACKFACE":
            s.show_backface_culling = not s.show_backface_culling

        elif self.overlay == "FACEORIENT":
            o.show_face_orientation = not o.show_face_orientation

        elif self.overlay == "BONES":
            o.show_bones = not o.show_bones

        elif self.overlay == "STATS":
            o.show_stats = not o.show_stats

        # Mode contextual
        if bpy.context.mode == "EDIT_MESH":

            if self.overlay == "SEAMS":
                o.show_edge_seams = not o.show_edge_seams

            elif self.overlay == "SHARP":
                o.show_edge_sharp = not o.show_edge_sharp

            elif self.overlay == "CREASE":
                o.show_edge_crease = not o.show_edge_crease

            elif self.overlay == "BEVEL":
                o.show_edge_bevel_weight = not o.show_edge_bevel_weight

            elif self.overlay == "INDICES":
                o.show_extra_indices = not o.show_extra_indices

            elif self.overlay == "ALLEDIT":
                if o.show_edge_seams or o.show_edge_sharp:
                    o.show_edge_seams = False
                    o.show_edge_sharp = False
                    o.show_edge_crease = False
                    o.show_edge_bevel_weight = False
                else:
                    o.show_edge_seams = True
                    o.show_edge_sharp = True
                    o.show_edge_crease = True
                    o.show_edge_bevel_weight = True

            elif self.overlay == "VN":
                o.show_vertex_normals = not o.show_vertex_normals

            elif self.overlay == "SN":
                o.show_split_normals = not o.show_split_normals

            elif self.overlay == "FN":
                o.show_face_normals = not o.show_face_normals

            elif self.overlay == "WEIGHT":
                o.show_weight = not o.show_weight


        elif bpy.context.mode == "OBJECT":

            if self.overlay == "WIRE":
                o.show_wireframes = not o.show_wireframes

            elif self.overlay == "WIREFRAMES":
                o.show_wireframes = not o.show_wireframes

        return {'FINISHED'}


class VIEW3D_OT_ke_spacetoggle(Operator):
    bl_idname = "view3d.ke_spacetoggle"
    bl_label = "Space Toggle"
    bl_description = "Toggle between Edit and Object modes on selected object when mouse pointer is over -nothing-"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER'}

    mouse_pos = Vector((0, 0))

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'HAIR', 'GPENCIL'})

    def invoke(self, context, event):
        self.mouse_pos[0] = event.mouse_region_x
        self.mouse_pos[1] = event.mouse_region_y
        return self.execute(context)

    def execute(self, context):
        sel_mode = str(bpy.context.mode)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj, hit_wloc, hit_normal, face_index = mouse_raycast(context, self.mouse_pos)

        if not face_index:
            if sel_mode == "OBJECT":
                bpy.ops.object.mode_set(mode="EDIT")
            elif sel_mode == "EDIT_MESH":
                bpy.ops.object.mode_set(mode="OBJECT")

        return {'FINISHED'}


def get_og_overlay_ui(self):
    og_gizmo = bpy.context.space_data.show_gizmo_navigate
    og_floor = bpy.context.space_data.overlay.show_floor
    og_x = bpy.context.space_data.overlay.show_axis_x
    og_y = bpy.context.space_data.overlay.show_axis_y
    og_z = bpy.context.space_data.overlay.show_axis_z
    og_text = bpy.context.space_data.overlay.show_text
    og_extras = bpy.context.space_data.overlay.show_extras

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    og_ui = space.show_region_ui
                    og_tb = space.show_region_toolbar

    return [og_gizmo, og_floor, og_x, og_y, og_z, og_text, og_extras, og_ui, og_tb]


class VIEW3D_OT_ke_focusmode(Operator):
    bl_idname = "view3d.ke_focusmode"
    bl_label = "Focus Mode"
    bl_description = "Fullscreen+. Restores original settings when toggled back."
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'REGISTER'}

    supermode : bpy.props.BoolProperty(default=False, options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "VIEW_3D"

    def execute(self, context):

        set_focus = bpy.context.scene.ke_focus[0]
        set_super_focus = bpy.context.scene.ke_focus[10]

        if not set_focus:
            og = get_og_overlay_ui(self)

            context.scene.ke_focus_stats = bpy.context.space_data.overlay.show_stats
            context.space_data.overlay.show_stats = False

            context.space_data.show_gizmo_navigate = False
            context.space_data.overlay.show_floor = False
            context.space_data.overlay.show_axis_x = False
            context.space_data.overlay.show_axis_y = False
            context.space_data.overlay.show_axis_z = False
            context.space_data.overlay.show_text = False
            context.space_data.overlay.show_extras = False

            context.scene.ke_focus[1] = og[0]
            context.scene.ke_focus[2] = og[1]
            context.scene.ke_focus[3] = og[2]
            context.scene.ke_focus[4] = og[3]
            context.scene.ke_focus[5] = og[4]
            context.scene.ke_focus[6] = og[5]
            context.scene.ke_focus[7] = og[6]
            context.scene.ke_focus[8] = og[7]
            context.scene.ke_focus[9] = og[8]

            context.scene.ke_focus[0] = True
            if self.supermode: context.scene.ke_focus[10] = True

            bpy.ops.screen.screen_full_area(use_hide_panels=self.supermode)

            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.show_region_ui = False
                            space.show_region_toolbar = False

        else:
            og = bpy.context.scene.ke_focus[1:]
            ogs = bpy.context.scene.ke_focus_stats

            context.space_data.show_gizmo_navigate = og[0]
            context.space_data.overlay.show_floor = og[1]
            context.space_data.overlay.show_axis_x = og[2]
            context.space_data.overlay.show_axis_y = og[3]
            context.space_data.overlay.show_axis_z = og[4]
            context.space_data.overlay.show_text = og[5]
            context.space_data.overlay.show_extras = og[6]
            context.space_data.overlay.show_stats = ogs

            context.scene.ke_focus[0] = False
            context.scene.ke_focus[10] = False

            if not self.supermode and set_super_focus:
                bpy.ops.screen.screen_full_area(use_hide_panels=True)
            elif self.supermode and not set_super_focus:
                bpy.ops.screen.screen_full_area(use_hide_panels=False)
            else:
                bpy.ops.screen.screen_full_area(use_hide_panels=self.supermode)

            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.show_region_ui = og[7]
                            space.show_region_toolbar = og[8]

        return {'FINISHED'}


class MESH_OT_ke_extract_and_edit(Operator):
    bl_idname = "mesh.ke_extract_and_edit"
    bl_label = "Extract & Edit"
    bl_description = "Separate element selection into a New Object & set as Active Object in Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}

    copy : bpy.props.BoolProperty(default=False, options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def execute(self, context):
        sel_obj = [o for o in context.selected_objects if o.type == "MESH"]

        if not len(sel_obj):
            self.report({'INFO'}, "Selection Error: No valid/active object(s) selected?")
            return {"CANCELLED"}

        if self.copy:
            bpy.ops.mesh.duplicate(mode=1)

        bpy.ops.mesh.separate(type="SELECTED")
        new_obj = [o for o in context.selected_objects if o.type == 'MESH'][-1]

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action="DESELECT")
        new_obj.select_set(True)

        view_layer = bpy.context.view_layer
        view_layer.objects.active = new_obj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action="SELECT")

        return {'FINISHED'}


class OBJECT_OT_ke_straighten(Operator):
    bl_idname = "object.ke_straighten"
    bl_label = "Straighten"
    bl_description = "Snaps selected object(s) rotation to nearest set degree"
    bl_options = {'REGISTER', 'UNDO'}

    deg: bpy.props.FloatProperty(description="Degree Snap", default=90, min=0, max=90)

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        for o in context.selected_objects:
            r = [radians((round(degrees(i) / self.deg) * self.deg))  for i in o.rotation_euler]
            o.rotation_euler[0] = r[0]
            o.rotation_euler[1] = r[1]
            o.rotation_euler[2] = r[2]
        return {"FINISHED"}


class OBJECT_OT_ke_object_op(Operator):
    bl_idname = "object.ke_object_op"
    bl_label = "Object Control"
    bl_description = "Misc pie menu ops & such"
    bl_options = {'REGISTER', 'UNDO'}

    cmd : bpy.props.StringProperty(default="", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        if "ROT" in self.cmd:
            if self.cmd == "ROT_CLEAR_X":
                context.object.rotation_euler[0] = 0
            elif self.cmd == "ROT_CLEAR_Y":
                context.object.rotation_euler[1] = 0
            elif self.cmd == "ROT_CLEAR_Z":
                context.object.rotation_euler[2] = 0

        return {"FINISHED"}


class ke_popup_info(bpy.types.Operator):
    bl_idname = "ke_popup.info"
    bl_label = "Info"

    text: bpy.props.StringProperty(name="Info", description="Info", default='')

    @classmethod
    def description(cls, context, properties):
        return properties.text

    def execute(self, context):
        return {'INTERFACE'}


# -------------------------------------------------------------------------------------------------
# Class Registration & Unregistration
# -------------------------------------------------------------------------------------------------
classes = (
    MESH_OT_ke_select_boundary,
    VIEW3D_OT_origin_to_selected,
    VIEW3D_OT_selected_to_origin,
    VIEW3D_OT_ke_overlays,
    VIEW3D_OT_ke_spacetoggle,
    VIEW3D_OT_ke_focusmode,
    VIEW3D_OT_ke_object_to_cursor,
    VIEW3D_OT_ke_origin_to_cursor,
    VIEW3D_OT_align_origin_to_selected,
    MESH_OT_ke_extract_and_edit,
    MESH_OT_ke_select_collinear,
    MESH_OT_ke_select_invert_linked,
    VIEW3D_OT_ke_cursor_clear_rotation,
    VIEW3D_OT_ke_cursor_bookmark,
    VIEW3D_OT_ke_align_object_to_active,
    VIEW3D_OT_ke_swap,
    SCREEN_OT_ke_render_visible,
    SCREEN_OT_ke_render_slotcycle,
    OBJECT_OT_ke_straighten,
    OBJECT_OT_ke_object_op,
    VIEW3D_OT_ke_shading_toggle,
    VIEW3D_OT_ke_unhide_or_local,
    VIEW3D_OT_ke_lock,
    MESH_OT_ke_mouse_side_of_active,
    ke_popup_info,
    MESH_OT_ke_select_flipped_normal,
    OBJECT_OT_ke_bbmatch,
    MESH_OT_ke_facematch,
    VIEW3D_OT_ke_set_active_collection,
    VIEW3D_OT_ke_show_in_outliner,
    OBJECT_OT_ke_select_by_displaytype
)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.ke_focus = bpy.props.BoolVectorProperty(size=16)
    bpy.types.Scene.ke_focus_stats = bpy.props.BoolProperty()

    bpy.types.Scene.ke_cslot1 = bpy.props.FloatVectorProperty(size=6)
    bpy.types.Scene.ke_cslot2 = bpy.props.FloatVectorProperty(size=6)
    bpy.types.Scene.ke_cslot3 = bpy.props.FloatVectorProperty(size=6)
    bpy.types.Scene.ke_cslot4 = bpy.props.FloatVectorProperty(size=6)
    bpy.types.Scene.ke_cslot5 = bpy.props.FloatVectorProperty(size=6)
    bpy.types.Scene.ke_cslot6 = bpy.props.FloatVectorProperty(size=6)

    bpy.types.Scene.ke_is_rendering = bpy.props.BoolProperty(default=False)

    bpy.types.VIEW3D_MT_object_context_menu.append(menu_set_active_collection)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_show_in_outliner)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    try:
        del bpy.types.Scene.ke_focus
        del bpy.types.Scene.ke_cslot1
        del bpy.types.Scene.ke_cslot2
        del bpy.types.Scene.ke_cslot3
        del bpy.types.Scene.ke_cslot4
        del bpy.types.Scene.ke_cslot5
        del bpy.types.Scene.ke_cslot6

    except Exception as e:
        print('unregister fail:\n', e)
        pass

    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_set_active_collection)
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_show_in_outliner)


if __name__ == "__main__":
    register()
