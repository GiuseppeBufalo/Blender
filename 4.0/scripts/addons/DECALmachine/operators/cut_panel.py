import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty
import bmesh
from math import degrees
from .. utils.decal import sort_panel_geometry, get_rail_centers, create_cutter
from .. utils.ui import init_cursor, wrap_cursor, draw_init, draw_title, draw_prop, init_status, finish_status, update_HUD_location
from .. utils.draw import draw_line, draw_point, draw_lines
from .. items import cutter_method_items
from .. colors import green, red, light_green, light_red
from .. utils.property import step_enum
from .. utils.mesh import unhide_deselect, join, reset_material_indices
from .. utils.object import flatten, update_local_view


draw_cuts = []


class PanelCut(bpy.types.Operator):
    bl_idname = "machin3.panel_cut"
    bl_label = "MACHIN3: Panel Cut"
    bl_description = "Construct Cutter Mesh or instantly Mesh-Cut using Panel Decals.\nALT: Create Cutter or Mesh-Cut for every Mirror instance"
    bl_options = {'REGISTER', 'UNDO'}

    method: EnumProperty(name="Method", items=cutter_method_items, default="MESHCUT")

    depth: FloatProperty(name="Depth", default=0.1, min=0)
    extend: FloatProperty(name="Extend", default=0.1, min=0)

    apply_mods: BoolProperty(name="Apply Mods", default=False)

    xray: BoolProperty(name="XRay", default=True)

    allowmodaldepth: BoolProperty(default=True)
    allowmodalextend: BoolProperty(default=False)

    passthrough = False

    def draw(self, context):
        layout = self.layout
        column = layout.column()

    def draw_HUD(self, args):
        context, event = args

        draw_init(self, event)

        draw_title(self, 'Panel Cutting ')

        draw_prop(self, "Depth", self.depth, decimal=3, active=self.allowmodaldepth, hint="move LEFT/RIGHT, toggle W, reset ALT + W")
        if self.has_non_cyclic:
            draw_prop(self, "Extend", self.extend, offset=18, decimal=3, active=self.allowmodalextend, hint="move UP/DOWN, toggle E, reset ALT + E")

        self.offset += 10

        draw_prop(self, "Method", self.method, offset=18, hint="scroll UP/DOWN")

        if self.method == 'MESHCUT':
            draw_prop(self, "Apply Mods", self.apply_mods, offset=18, hint="toggle A")

        self.offset += 10
        draw_prop(self, "XRay", self.xray, offset=18, hint="toggle X")

    @classmethod
    def poll(cls, context):
        return [obj for obj in context.selected_objects if obj.DM.isdecal and obj.DM.decaltype == 'PANEL']

    def draw_VIEW3D(self, args):
        color, color_ext = (green, light_green) if self.method == 'CONSTRUCT' else (red, light_red)

        for (panel, rail_center_sequences), (ext_sequences) in zip(self.cutters_data, self.extend_data):
            mx = panel.matrix_world
            extend_top = []
            extend_bottom = []

            for (rseq, cyclic), ext_seq in zip(rail_center_sequences, ext_sequences):
                top_coords = [co + no * self.depth for co, no in rseq]
                bottom_coords = [co - no * self.depth for co, no in rseq]

                if cyclic:
                    top_coords.append(top_coords[0])
                    bottom_coords.append(bottom_coords[0])

                draw_line(top_coords, mx=mx, color=color, width=3, alpha=1, xray=self.xray)
                draw_line(bottom_coords, mx=mx, color=color, width=3, alpha=0.4, xray=self.xray)

                start, end = ext_seq

                if start and end:
                    start_co, start_no = start[0]
                    end_co, end_no = end[1]

                    start_remote_co, _ = start[1]
                    end_remote_co, _ = end[0]

                    start_ext_co = start_co + (start_co - start_remote_co).normalized() * self.extend
                    end_ext_co = end_co + (end_co - end_remote_co).normalized() * self.extend

                    extend_top.extend([start_co + start_no * self.depth, start_ext_co + start_no * self.depth, end_co + end_no * self.depth, end_ext_co + end_no * self.depth])
                    extend_bottom.extend([start_co - start_no * self.depth, start_ext_co - start_no * self.depth, end_co - end_no * self.depth, end_ext_co - end_no * self.depth])

            draw_lines(extend_top, mx=mx, color=color_ext, width=2, alpha=1, xray=self.xray)
            draw_lines(extend_bottom, mx=mx, color=color_ext, width=2, alpha=0.4, xray=self.xray)

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)
            update_HUD_location(self, event)

        events = ['WHEELUPMOUSE', 'ONE', 'WHEELDOWNMOUSE', 'TWO', 'A', 'X', 'W', 'E']

        if any([self.allowmodaldepth, self.allowmodalextend]):
            events.append('MOUSEMOVE')

        if event.type in events:


            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                elif not event.alt:
                    divisor = 10000 if event.shift else 100 if event.ctrl else 1000

                    if self.allowmodaldepth:
                        delta_x = event.mouse_x - self.last_mouse_x
                        delta_depth = delta_x / divisor

                        self.depth += delta_depth

                    if self.allowmodalextend:
                        delta_y = event.mouse_y - self.last_mouse_y
                        delta_extend = delta_y / divisor

                        self.extend += delta_extend


            elif event.type in {'WHEELUPMOUSE', 'ONE'} and event.value == 'PRESS':
                self.method = step_enum(self.method, cutter_method_items, 1)

            elif event.type in {'WHEELDOWNMOUSE', 'TWO'} and event.value == 'PRESS':
                self.method = step_enum(self.method, cutter_method_items, -1)



            elif event.type == 'W' and event.value == "PRESS":
                if event.alt:
                    self.allowmodaldepth = False
                    self.depth = 0.1
                else:
                    self.allowmodaldepth = not self.allowmodaldepth

            elif event.type == 'E' and event.value == "PRESS":
                if event.alt:
                    self.allowmodalextend = False
                    self.extend = 0.1
                else:
                    self.allowmodalextend = not self.allowmodalextend



            elif event.type == 'A' and event.value == 'PRESS':
                if self.method == 'MESHCUT':
                    self.apply_mods = not self.apply_mods


            elif event.type == 'X' and event.value == 'PRESS':
                self.xray = not self.xray



        elif event.type in {'MIDDLEMOUSE'} or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}):
            self.passthrough = True
            return {'PASS_THROUGH'}


        elif event.type in {'LEFTMOUSE', 'SPACE'}:
            self.finish(context)

            self.extend_cuts(self.extend)

            if self.method == 'CONSTRUCT':
                self.construct_cutter(context, self.cutters_data, self.depth)

            elif self.method == 'MESHCUT':
                self.instant_cut(context, self.cutters_data, self.depth, self.apply_mods)
            return {'FINISHED'}


        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish(context)
            self.panels[0].select_set(True)

            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x
        self.last_mouse_y = event.mouse_y

        return {'RUNNING_MODAL'}

    def finish(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

        finish_status(self)

        context.space_data.overlay.show_outline_selected = True

    def invoke(self, context, event):
        self.panels = [obj for obj in context.selected_objects if obj.DM.isdecal and obj.DM.decaltype == 'PANEL']

        if not event.alt:
            mirrors = [mod for panel in self.panels for mod in panel.modifiers if mod.type == 'MIRROR' and mod.show_viewport]
            for mod in mirrors:
                mod.show_viewport = False

        dg = context.evaluated_depsgraph_get()

        if not event.alt:
            for mod in mirrors:
                mod.show_viewport = True

        if self.panels:
            self.cutters_data = []
            self.extend_data = []
            self.has_non_cyclic = False

            for panel in self.panels:
                bm = bmesh.new()
                bm.from_mesh(panel.evaluated_get(dg).to_mesh())

                sequences = sort_panel_geometry(bm, debug=False)

                rail_center_sequences = get_rail_centers(sequences, mx=panel.matrix_world, debug=False)

                self.cutters_data.append((panel, rail_center_sequences))

                ext_seq = []

                for rseq, cyclic in rail_center_sequences:
                    if cyclic:
                        ext_seq.append((None, None))

                    else:
                        self.has_non_cyclic = True

                        start = rseq[:2]
                        end = rseq[-2:]

                        ext_seq.append((start, end))

                self.extend_data.append(ext_seq)

            if self.cutters_data:

                context.space_data.overlay.show_outline_selected = False

                init_cursor(self, event)
                self.panels[0].select_set(True)

                init_status(self, context, 'Panel Cutting')

                args = (context, event)
                self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (args, ), "WINDOW", "POST_PIXEL")
                self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (args, ), 'WINDOW', 'POST_VIEW')

                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}

        return {'CANCELLED'}

    def extend_cuts(self, amount):
        if amount > 0:

            for panel, rail_center_sequences in self.cutters_data:
                for rseq, cyclic in rail_center_sequences:
                    if not cyclic:
                        start = rseq[:2]
                        end = rseq[-2:]

                        start_co, start_no = start[0]
                        end_co, end_no = end[1]

                        start_remote_co, _ = start[1]
                        end_remote_co, _ = end[0]

                        start_ext_co = start_co + (start_co - start_remote_co).normalized() * amount
                        end_ext_co = end_co + (end_co - end_remote_co).normalized() * amount

                        rseq.pop(0)
                        rseq.insert(0, (start_ext_co, start_no))

                        rseq.pop(-1)
                        rseq.append((end_ext_co, end_no))

    def construct_cutter(self, context, data, depth):
        states = []

        bpy.ops.object.select_all(action='DESELECT')

        for panel, rail_center_sequences in data:

            cutter = create_cutter(context.collection, panel, rail_center_sequences, depth=depth)
            states.append((cutter, True))

            panel.select_set(False)
            cutter.select_set(True)

            if context.active_object == panel:
                context.view_layer.objects.active = cutter

        update_local_view(context.space_data, states)

    def instant_cut(self, context, data, depth, apply_mods):
        global draw_cuts

        cuts = []
        draw_cuts = []

        for panel, rail_center_sequences in data:

            cutter = create_cutter(context.collection, panel, rail_center_sequences, depth=depth)

            target = panel.DM.slicedon if panel.DM.slicedon else panel.parent if panel.parent else None

            if target:
                cuts.append((target, cutter))

                for rseq, cyclic in rail_center_sequences:
                    coords = [co.copy() for co, _ in rseq]

                    if cyclic:
                        coords.append(coords[0])

                    draw_cuts.append((panel.matrix_world, coords))


        if cuts:
            for target, _, in cuts:
                unhide_deselect(target.data)

            dg = context.evaluated_depsgraph_get()

            for target, cutter in cuts:
                bpy.ops.object.select_all(action='DESELECT')

                self.mesh_cut(context, dg, target, cutter, apply_mods)

        if draw_cuts:
            bpy.ops.machin3.draw_meshcut()

    def mesh_cut(self, context, dg, target, cutter, apply_mods):
        target.select_set(True)
        context.view_layer.objects.active = target

        if apply_mods:
            flatten(target, dg)

        join(target, [cutter], select=[1])

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.intersect(separate_mode='ALL', solver='FAST')
        bpy.ops.object.mode_set(mode='OBJECT')

        bm = bmesh.new()
        bm.from_mesh(target.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        i = bm.faces.layers.int.verify()
        s = bm.edges.layers.string.verify()

        cutter_faces = [f for f in bm.faces if f[i] > 0]
        bmesh.ops.delete(bm, geom=cutter_faces, context='FACES')

        non_manifold = [e for e in bm.edges if not e.is_manifold]

        verts = set()

        for e in non_manifold:
            e.seam = True
            e[s] = 'MESHCUT'.encode()

            verts.update(e.verts)

        bmesh.ops.remove_doubles(bm, verts=list({v for e in non_manifold for v in e.verts}), dist=0.0001)

        straight_edged = []

        for v in verts:
            if v.is_valid and len(v.link_edges) == 2:
                e1 = v.link_edges[0]
                e2 = v.link_edges[1]

                vector1 = e1.other_vert(v).co - v.co
                vector2 = e2.other_vert(v).co - v.co

                angle = degrees(vector1.angle(vector2))

                if 179 <= angle <= 181:
                    straight_edged.append(v)

        bmesh.ops.dissolve_verts(bm, verts=straight_edged)

        bm.faces.layers.int.remove(i)

        bm.to_mesh(target.data)
        bm.clear()


class RemoveMeshCuts(bpy.types.Operator):
    bl_idname = "machin3.remove_mesh_cuts"
    bl_label = "MACHIN3: Remove Mesh Cuts"
    bl_description = "Remove Mesh Cuts\nALT: Remove Materials as well (except the first one)\nSHIFT: Select Mesh Cut Edges, instead of removing them."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' or (context.mode == 'OBJECT' and [obj for obj in context.selected_objects if obj.type =='MESH' and not obj.DM.isdecal])

    def invoke(self, context, event):
        mode = context.mode

        if mode in ['EDIT_MESH', 'OBJECT']:
            edit_mode = True if mode == 'EDIT_MESH' else False

            sel = [context.active_object] if edit_mode else [obj for obj in context.selected_objects if not obj.DM.isdecal]

            for obj in sel:
                if edit_mode:
                    bm = bmesh.from_edit_mesh(obj.data)
                    bm.normal_update()

                else:
                    bm = bmesh.new()
                    bm.from_mesh(obj.data)
                    bm.normal_update()

                s = bm.edges.layers.string.verify()

                edges = [e for e in bm.edges if e[s].decode() == 'MESHCUT']

                if event.shift:
                    for e in edges:
                        e.select_set(True)

                else:
                    bmesh.ops.dissolve_edges(bm, edges=edges, use_verts=True)

                    bm.edges.layers.string.remove(s)

                if edit_mode:
                    bmesh.update_edit_mesh(obj.data)

                else:
                    bm.to_mesh(obj.data)
                    bm.free()

                if event.alt and len(obj.data.materials) > 1:
                    firstmat = None

                    for slot in obj.material_slots:
                        if slot.material:
                            firstmat = slot.material
                            break

                    if firstmat:
                        obj.data.materials.clear()

                        if edit_mode:
                            bpy.ops.object.mode_set(mode='OBJECT')
                            reset_material_indices(obj.data)
                            bpy.ops.object.mode_set(mode='EDIT')

                        else:
                            reset_material_indices(obj.data)

                        obj.data.materials.append(firstmat)

                obj.data.update()

        return {'FINISHED'}
