import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from math import radians
from uuid import uuid4
from .. utils.object import parent
from .. utils.mesh import get_coords, unhide_deselect, smooth
from .. utils.modifier import add_boolean, add_displace
from .. utils.ui import draw_title, draw_prop, draw_init, draw_text, init_cursor, init_status, finish_status, update_HUD_location
from .. utils.draw import draw_mesh_wire
from .. utils.property import step_enum
from .. utils.registration import get_prefs
from .. utils.system import printd
from .. items import boolean_method_items, boolean_solver_items
from .. colors import yellow, blue, red, normal, green


def draw_add_boolean(self, context):
    layout = self.layout

    row = layout.row(align=True)
    row.label(text='Add Boolean')

    row.label(text="", icon='EVENT_SPACEKEY')
    row.label(text="Finish")

    row.label(text="", icon='MOUSE_LMB')
    row.label(text="Finish and select Cutters")

    if context.window_manager.keyconfigs.active.name.startswith('blender'):
        row.label(text="", icon='MOUSE_MMB')
        row.label(text="Viewport")

    row.label(text="", icon='MOUSE_RMB')
    row.label(text="Cancel")


class Boolean(bpy.types.Operator):
    bl_idname = "machin3.boolean"
    bl_label = "MACHIN3: Boolean"
    bl_description = "Add Boolean Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    method: EnumProperty(name="Method", items=boolean_method_items, default='DIFFERENCE')
    solver: EnumProperty(name="Solver", items=boolean_solver_items, default='FAST')

    auto_smooth: BoolProperty(name="Auto-Smooth", default=True)
    auto_smooth_angle: IntProperty(name="Angle", default=20)

    time: FloatProperty(name="Time (s", default=1.25)
    steps: FloatProperty(default=0.05)
    passthrough = None

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            sel = [obj for obj in context.selected_objects if obj != active]
            return active and sel

    def draw_HUD(self, args):
        context, event = args

        draw_init(self, event)
        alpha = self.countdown / (self.time * get_prefs().modal_hud_timeout)


        draw_title(self, "Add Boolean", subtitle="to %s" % (self.active.name), subtitleoffset=160, HUDalpha=alpha)


        for idx, name in enumerate([obj.name for obj in self.sel]):
            text = "%s" % (name)
            draw_text(self, text, 11, offset=0 if idx == 0 else 18, HUDcolor=yellow, HUDalpha=alpha)

        self.offset += 10

        draw_prop(self, "Method", self.method, offset=18, hint="scroll UP/DOWN,", hint_offset=210)
        draw_prop(self, "Solver", self.solver, offset=18, hint="Set E/F", hint_offset=210)
        self.offset += 10

        draw_prop(self, "Auto-Smooth", self.auto_smooth, offset=18, hint="toggle S", hint_offset=210)

        if self.auto_smooth:
            draw_prop(self, "Angle", self.auto_smooth_angle, offset=18, hint="ALT scroll UP/DOWN", hint_offset=210)

    def draw_VIEW3D(self, args):
        alpha = self.countdown / (self.time * get_prefs().modal_hud_timeout)

        color = red if self.method == 'DIFFERENCE' else blue if self.method == 'UNION' else normal if self.method == 'INTERSECT' else green

        for batch in self.batches:
            if not self.passthrough:
                draw_mesh_wire(batch, color=color, alpha=alpha)

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            update_HUD_location(self, event)

        events = ['WHEELUPMOUSE', 'UP_ARROW', 'ONE', 'WHEELDOWNMOUSE', 'DOWN_ARROW', 'S', 'E', 'F']

        if event.type in events:


            if event.type in {'WHEELUPMOUSE', 'UP_ARROW', 'ONE', 'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO', 'E', 'F'} and event.value == 'PRESS':
                if event.type in {'WHEELUPMOUSE', 'UP_ARROW', 'ONE'} and event.value == 'PRESS':
                    if event.alt:
                        self.auto_smooth_angle += 5

                    else:
                        self.method = step_enum(self.method, boolean_method_items, 1, loop=True)

                elif event.type in {'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO'} and event.value == 'PRESS':
                    if event.alt:
                        self.auto_smooth_angle -= 5

                    else:
                        self.method = step_enum(self.method, boolean_method_items, -1, loop=True)

                if event.type == 'E' and event.value == 'PRESS':
                    self.solver = 'EXACT'

                elif event.type == 'F' and event.value == 'PRESS':
                    self.solver = 'FAST'


                for mod in self.mods:

                    if self.method == 'SPLIT':
                        mod.operation = 'DIFFERENCE'
                        mod.show_viewport = False

                    else:
                        mod.operation = self.method
                        mod.show_viewport = True


                    mod.solver = self.solver

                    mod.name = self.method.title()


                self.active.data.auto_smooth_angle = radians(self.auto_smooth_angle)



            elif event.type == 'S' and event.value == 'PRESS':
                self.auto_smooth = not self.auto_smooth

                for obj in self.sel:
                    obj.data.use_auto_smooth = self.auto_smooth
                    smooth(obj.data, self.auto_smooth)


            self.countdown = self.time * get_prefs().modal_hud_timeout



        elif event.type in {'MIDDLEMOUSE'} or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}) or event.type.startswith('NDOF'):
            self.countdown = self.time * get_prefs().modal_hud_timeout
            self.passthrough = True

            return {'PASS_THROUGH'}

        elif event.type == 'MOUSEMOVE':
            if self.passthrough:
                self.passthrough = False



        if event.type == 'TIMER' and not self.passthrough:
            self.countdown -= self.steps



        if self.countdown < 0:
            self.finish(context)

            if self.method == 'SPLIT':
                self.setup_split_boolean(context)

            return {'FINISHED'}



        elif event.type in {'LEFTMOUSE', 'SPACE'} and not event.alt:
            self.finish(context)

            cutters = self.sel

            if self.method == 'SPLIT':
                cutters.extend(self.setup_split_boolean(context))

            if event.type == 'LEFTMOUSE':
                for obj in cutters:
                    obj.hide_set(False)
                    obj.select_set(True)

                context.view_layer.objects.active = cutters[0]

            return {'FINISHED'}



        elif event.type in {'RIGHTMOUSE', 'ESC'} and not event.alt:
            self.cancel_modal(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        context.window_manager.event_timer_remove(self.TIMER)

        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

        finish_status(self)

    def setup_split_boolean(self, context):

        view = context.space_data
        cutter_dups = []

        for cutter, mod in zip(self.sel, self.mods):

            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = self.active
            self.active.select_set(True)

            mod.name = "Split (Difference)"
            mod.show_viewport = True

            children = {str(uuid4()): (obj, obj.visible_get()) for obj in self.active.children_recursive if obj.name in context.view_layer.objects}

            for dup_hash, (obj, vis) in children.items():
                obj.MM.dup_hash = dup_hash

                if not vis:
                    if view.local_view and not obj.local_view_get(view):
                        obj.local_view_set(view, True)

                obj.hide_set(False)
                obj.select_set(True)


            bpy.ops.object.duplicate(linked=False)

            active_dup = context.active_object
            dup_mod = active_dup.modifiers.get(mod.name)
            dup_mod.operation = 'INTERSECT'
            dup_mod.name ='Split (Intersect)'

            dup_children = [obj for obj in active_dup.children_recursive if obj.name in context.view_layer.objects]

            for dup in dup_children:
                orig, vis = children[dup.MM.dup_hash]

                orig.hide_set(not vis)
                dup.hide_set(not vis)

                if orig == cutter:

                    dupmesh = dup.data
                    dup.data = orig.data

                    bpy.data.meshes.remove(dupmesh, do_unlink=False)

                    cutter_dups.append(dup)

                orig.MM.dup_hash = ''
                dup.MM.dup_hash = ''

            add_displace(dup_mod.object, mid_level=0, strength=0)

        bpy.ops.object.select_all(action='DESELECT')

        return cutter_dups

    def cancel_modal(self, context):
        self.finish(context)

        for mod in self.mods:
            self.active.modifiers.remove(mod)

        for obj in self.sel:
            obj.display_type = 'TEXTURED'
            obj.hide_set(False)
            obj.select_set(True)

    def invoke(self, context, event):
        self.active = context.active_object
        self.sel = [obj for obj in context.selected_objects if obj != self.active]
        self.split = {}

        for obj in self.sel:
            parent(obj, self.active)

        unhide_deselect(self.active.data)

        self.batches = []
        self.countdown = self.time * get_prefs().modal_hud_timeout

        init_cursor(self, event)

        self.mods = []

        self.existing_mods = [mod.name for mod in self.active.modifiers]

        for obj in self.sel:
            mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
            self.mods.append(mod)

            obj.display_type = 'WIRE'
            obj.hide_render = True

            unhide_deselect(obj.data)

            obj.hide_set(True)

            self.auto_smooth = self.active.data.use_auto_smooth

            if self.auto_smooth:
                obj.data.use_auto_smooth = True
                smooth(obj.data, smooth=True)

            coords, indices = get_coords(obj.data, mx=obj.matrix_world, indices=True)
            self.batches.append((coords, indices))

        if self.auto_smooth:
            self.active.data.use_auto_smooth = True
            self.active.data.auto_smooth_angle = radians(self.auto_smooth_angle)

        init_status(self, context, func=draw_add_boolean)

        args = (context, event)
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (args, ), 'WINDOW', 'POST_PIXEL')
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (args, ), 'WINDOW', 'POST_VIEW')
        self.TIMER = context.window_manager.event_timer_add(self.steps, window=context.window)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
