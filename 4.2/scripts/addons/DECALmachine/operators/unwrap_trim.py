import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
import bmesh
from mathutils import Vector, Matrix
from math import radians
from .. utils.registration import get_prefs
from .. utils.ui import init_cursor, draw_init, draw_title, draw_prop, popup_message, draw_info, init_status, finish_status, update_HUD_location
from .. utils.material import get_most_common_material_index, get_trimsheet_material_from_faces, remove_trimsheetmat, assign_trimsheet_material, is_legacy_material
from .. utils.selection import get_selection_islands, get_boundary_edges, get_edges_vert_sequences
from .. utils.property import step_enum, step_list
from .. utils.uv import get_selection_uv_bbox, get_trim_uv_bbox, unwrap_to_empty_trim, set_trim_uv_channel, quad_unwrap
from .. utils.trim import get_empty_trim_from_sheetdata, get_trim_from_uuid, get_trim_uuid_from_library_and_name
from .. utils.system import printd
from .. colors import orange
from .. items import trimunwrap_fit_items

class Settings:
    _settings = {}

    def save_settings(self):
        ignore = ['bl_rna', 'rna_type', 'library_name', 'trim_name', 'trim', 'wrn', 'all_trims', 'toggled_overlays']
        for d in dir(self.properties):
            if d in ignore:
                continue
            try:
                self.__class__._settings[d] = self.properties[d]
            except KeyError:
                continue

    def load_settings(self):
        for d in self.__class__._settings:
            self.properties[d] = self.__class__._settings[d]

class TrimUnwrap(bpy.types.Operator, Settings):
    bl_idname = "machin3.trim_unwrap"
    bl_label = "MACHIN3: Unwrap Trim"
    bl_description = "Unwrap selected faces to selected trim\nALT: Unwrap the inverted selection to the Empty Trim\nCTRL: Unwrap using CONFORMAL method, instead of ANGLE_BASED"
    bl_options = {'REGISTER', 'UNDO'}

    library_name: StringProperty()
    trim_name: StringProperty()

    fit: EnumProperty(name="Fit unwrapped faces to trim", items=trimunwrap_fit_items, default='AUTO')
    rotate: IntProperty(name="Rotate", default=0)
    wrn: StringProperty()

    passthrough = False
    toggled_overlays = False

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            draw_title(self, "Unwrap Trim", subtitle=self.library_name, subtitleoffset=180)

            draw_prop(self, "Fit", self.fit, offset=0, hint="cycle F, SHIFT: backwards", hint_offset=220)
            draw_prop(self, "Rotate", self.rotate, offset=18, hint="scroll UP/DOWN, SHIFT: 5°, CTRL + SHIFT: 1°", hint_offset=220)

            self.offset += 10
            draw_prop(self, "Trim", self.trim_name, offset=18, hint="CTRL scroll UP/DOWN", hint_offset=220)

            if self.wrn:
                self.offset += 10
                draw_info(self, self.wrn, size=12, offset=18, HUDcolor=orange, HUDalpha=1)

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            update_HUD_location(self, event)

        events = ['WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'ONE', 'TWO', 'F']

        if event.type in events:

            if event.type in {'WHEELUPMOUSE', 'ONE'} and event.value == 'PRESS':

                if event.ctrl and event.shift:
                    self.rotate -= 1
                elif event.shift:
                    self.rotate -= 5
                elif not event.ctrl:
                    self.rotate -= 90

                elif event.ctrl:
                    self.trim = step_list(self.trim, self.all_trims, -1)

                    trim = context.window_manager.decaluuids.get(self.trim['uuid'])
                    self.trim_name = trim[0][0] if trim else ''

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
                    self.trim_name = trim[0][0] if trim else ''

            elif event.type == 'F' and event.value == "PRESS":
                if event.shift:
                    self.fit = step_enum(self.fit, trimunwrap_fit_items, step=-1)
                else:
                    self.fit = step_enum(self.fit, trimunwrap_fit_items, step=1)

            self.unwrap_trim()

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

            self.save_settings()
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal(context)

            if self.toggled_overlays:
                context.space_data.overlay.show_overlays = True

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        if context.space_data.type == 'VIEW_3D':
            bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        elif context.space_data.type == 'IMAGE_EDITOR':
            bpy.types.SpaceImageEditor.draw_handler_remove(self.HUD, 'WINDOW')

        finish_status(self)

    def cancel_modal(self, context):
        self.finish(context)

        initbm, _, active, _, mat_dict = self.data

        if mat_dict['appended']:
            remove_trimsheetmat(mat_dict['sheetmat'], remove_textures=True, debug=False)

        if mat_dict['matchedmat']:
            active.material_slots[mat_dict['index']].material = mat_dict['matchedmat']

        bpy.ops.object.mode_set(mode='OBJECT')

        initbm.to_mesh(active.data)

        bpy.ops.object.material_slot_remove_unused()

        bpy.ops.object.mode_set(mode='EDIT')

    def invoke(self, context, event):
        self.load_settings()

        active = context.active_object
        sheetdata = context.window_manager.trimsheets[self.library_name]

        trimuuid = get_trim_uuid_from_library_and_name(context, self.library_name, self.trim_name)
        self.trim = get_trim_from_uuid(sheetdata, trimuuid)

        if trimuuid and self.trim:
            if self.trim['ispanel']:
                self.all_trims = [trim for trim in sheetdata['trims'] if trim['ispanel'] and not trim['isempty']]

            else:
                self.all_trims = [trim for trim in sheetdata['trims'] if not trim['ispanel'] and not trim['isempty']]

            active.update_from_editmode()

            initbm = bmesh.new()
            initbm.from_mesh(active.data)
            initbm.normal_update()

            faces = [f for f in initbm.faces if f.select]

            if active.data.materials:
                slot_idx, _ = get_most_common_material_index(faces)

                if mat := active.data.materials[slot_idx]:
                    if version := is_legacy_material(mat):
                        popup_message("The material used of the current face selection is a legacy material, and needs to be updated", title=f"{version} Legacy Material detected!")
                        return {'CANCELLED'}

            empty = get_empty_trim_from_sheetdata(sheetdata)

            if (event.alt or not active.data.uv_layers) and empty:
                self.unwrap_inverted_selection_to_empty(active, sheetdata, empty)

            set_trim_uv_channel(active)

            selected = self.validate_selection(active, debug=False)

            if selected:
                if self.trim['ispanel']:
                    success, self.wrn = self.unwrap_panel(active, method='CONFORMAL' if event.ctrl else 'ANGLE_BASED', debug=False)

                    if not success:
                        if success is False:
                            popup_message(self.wrn, title="Invalid Selection")
                        return {'CANCELLED'}

                    self.orient_panel_uvs(active, sheetdata)

                else:
                    bpy.ops.uv.unwrap(method='CONFORMAL' if event.ctrl else 'ANGLE_BASED', margin=0)

                active.update_from_editmode()

                uvedbm = bmesh.new()
                uvedbm.from_mesh(active.data)
                uvedbm.normal_update()
                uvedbm.verts.ensure_lookup_table()

                mat_dict = get_trimsheet_material_from_faces(active, faces, sheetdata)

                self.data = [initbm, uvedbm, active, sheetdata, mat_dict]

                self.unwrap_trim(init=True)

                init_cursor(self, event)

                init_status(self, context, "Unwrap Trim")

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

        return {'CANCELLED'}

    def unwrap_trim(self, init=False):
        bpy.ops.object.mode_set(mode='OBJECT')

        _, uvedbm, active, sheetdata, mat_dict = self.data

        sheetresolution = Vector(sheetdata.get('resolution'))
        trimlocation = Vector(self.trim.get('location'))
        trimscale = Vector(self.trim.get('scale'))

        bm = uvedbm.copy()

        faces = [f for f in bm.faces if f.select]

        uvs = bm.loops.layers.uv.active
        loops = [loop for face in faces for loop in face.loops]

        rmx = Matrix.Rotation(radians(self.rotate), 2)

        for loop in loops:
            loop[uvs].uv = rmx @ loop[uvs].uv

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

        assign_trimsheet_material(active, faces, mat_dict, add_material=init)

        if not self.trim['ispanel']:
            boundary = get_boundary_edges(faces)

            for e in boundary:
                e.seam = True

        bm.to_mesh(active.data)
        bm.free()

        bpy.ops.object.mode_set(mode='EDIT')

    def orient_panel_uvs(self, active, sheetdata):
        sheetresolution = Vector(sheetdata.get('resolution'))
        trimlocation = Vector(self.trim.get('location'))
        trimscale = Vector(self.trim.get('scale'))

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        faces = [f for f in bm.faces if f.select]

        uvs = bm.loops.layers.uv.active
        loops = [loop for face in faces for loop in face.loops]

        selbbox, selmid, selscale = get_selection_uv_bbox(uvs, loops)

        trimbbox, trimmid = get_trim_uv_bbox(sheetresolution, trimlocation, trimscale)

        selratio = selscale.x / selscale.y
        trimratio = trimscale.x / trimscale.y

        self.rotate = 0

        if not ((selratio >= 1 and trimratio >= 1) or (selratio <= 1 and trimratio <= 1)):
            rmx = Matrix.Rotation(radians(-90), 2)

            for loop in loops:
                loop[uvs].uv = rmx @ loop[uvs].uv

            bmesh.update_edit_mesh(active.data)

    def unwrap_panel(self, active, method, reset=False, debug=False):
        def mark_seam(bm, sequences, boundary_edges):
            rail_candidates = [e for e in bm.edges if e.select and e not in boundary_edges]

            sideA = sequences[0][0]
            sideB = sequences[1][0]

            start_edges = [e for e in rail_candidates if any(v in sideA for v in e.verts)]

            edge = start_edges[0]
            vert = [v for v in edge.verts if v in sideA][0]
            loop = [l for l in edge.link_loops if l.vert == vert][0]

            seams = []

            while rail_candidates:
                if edge in rail_candidates:
                    rail_candidates.remove(edge)

                else:
                    return None

                seams.append(edge)

                next_loop = loop.link_loop_next

                if next_loop.vert in sideB:
                    break

                elif next_loop.vert in sideA:
                    edge = start_edges[0]
                    vert = [v for v in edge.verts if v in sideA][0]
                    loop = [l for l in edge.link_loops if l.vert == vert][0]

                    seams = []

                else:
                    loop = next_loop.link_loop_radial_next.link_loop_next
                    edge = loop.edge
                    vert = loop.vert

            for e in seams:
                e.seam = True

            return seams

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        uvs = bm.loops.layers.uv.verify()

        faces = [f for f in bm.faces if f.select]

        quads = [f for f in faces if len(f.verts) == 4]
        isallquads = len(faces) == len(quads)

        if isallquads:
            if debug:
                print("Selection is all quads!")

            quad_unwrap(bm, uvs, faces, active_face=bm.faces.active)
            
            bmesh.update_edit_mesh(active.data)
            return True, ""

        else:
            if debug:
                print("Selection contains tris or n-gons!")

            boundary_edges = get_boundary_edges(faces)
            boundary_verts = list({v for e in boundary_edges for v in e.verts})

            sequences = get_edges_vert_sequences(boundary_verts, boundary_edges)

            if len(sequences) == 2:
                seams = mark_seam(bm, sequences, boundary_edges)

                if seams:
                    if debug:
                        print(" Selection is cyclic")

                    bpy.ops.uv.unwrap(margin=0)

                    for e in seams:
                        e.seam = False

                    bmesh.update_edit_mesh(active.data)
                    return True, "Selection contains tris or n-gons! And it is cyclic!"

                else:
                    if debug:
                        print(" Selection is not actually cyclic, but contains a hole, also resulting in 2 sequences, making it seam cyclic!")

                    bpy.ops.uv.unwrap(margin=0)

                    bmesh.update_edit_mesh(active.data)
                    return True, "Selecton contains a hole!"

            elif len(sequences) == 1:
                bpy.ops.uv.unwrap(method=method, margin=0)

                if debug:
                    print(" Selection is not cyclic")

                bmesh.update_edit_mesh(active.data)
                return True, "Selection contains tris or n-gons!"

            else:
                if debug:
                    print(" Selection is cyclic and contains holes, not supported")
                return False, "Selection is cyclic and contains holes! Holes are only supportend for non-cyclic selections"

    def unwrap_inverted_selection_to_empty(self, active, sheetdata, empty):
        sheetresolution = Vector(sheetdata.get('resolution'))
        trimlocation = Vector(empty.get('location'))
        trimscale = Vector(empty.get('scale'))

        bpy.ops.mesh.select_all(action='INVERT')

        unwrap_to_empty_trim(active, sheetresolution, trimlocation, trimscale, remove_seams=True)

        bpy.ops.mesh.select_all(action='INVERT')

    def validate_selection(self, active, debug):
        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        faces = [f for f in bm.faces if f.select]

        islands = get_selection_islands(faces, debug=False)

        if islands:

            if len(islands) > 1:
                for _, _, faces in islands[1:]:
                    for f in faces:
                        f.select_set(False)

                if debug:
                    print("Selection encompassed multiple islands, unselected smaller islands.")

            seams = [e for e in bm.edges if e.select and e.seam]

            for e in seams:
                e.seam = False

            bmesh.update_edit_mesh(active.data)

            return True

        elif debug:
            print("Nothing selected, nothing done")
