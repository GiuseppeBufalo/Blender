import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_origin_3d
from mathutils import Vector
from .. utils.material import set_match_material_enum, match_material, remove_decalmat, get_decalmat
from .. utils.ui import draw_init, draw_title, draw_prop, init_cursor, draw_text, init_status, finish_status, popup_message, update_HUD_location
from .. utils.property import step_list
from .. utils.draw import draw_point, draw_lines2d
from .. utils.raycast import get_closest, get_two_origins_from_face
from .. utils.registration import get_version_from_blender, shape_version
from .. colors import red, blue

class Match(bpy.types.Operator):
    bl_idname = "machin3.match_material"
    bl_label = "MACHIN3: Match Material"
    bl_description = "Matches Decal Materials, Material 2 or Subset elements to Principled Shader Materials."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return [obj for obj in context.selected_objects if obj.DM.isdecal and not obj.DM.preatlasmats and not obj.DM.prejoindecals and get_decalmat(obj) and not get_decalmat(obj).DM.decaltype == "INFO"]

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)
            draw_title(self, "Match Materials")

            if self.hassub:
                draw_prop(self, "Subset", self.subset, active=self.matchsub, hint="toggle S, scroll UP/DOWN", hint_offset=280)

            if self.hasmat:
                draw_prop(self, "Material", self.material, offset=18, active=self.matchmat, hint="toggle D, SHIFT scroll UP/DOWN", hint_offset=280)

            if self.hasmat2:
                draw_prop(self, "Material 2", self.material2, offset=18, active=self.matchmat2, hint="toggle F, CTRL scroll UP/DOWN", hint_offset=280)

            if self.panels:

                indicator_coords = self.get_panel_indicator_coords(self.dg, context.region, context.space_data.region_3d, self.panels)

                for co, co2 in indicator_coords:
                    if co and co2:
                        size = 14
                        line_length = 40

                        if co[0] <= co2[0]:
                            line_coords = [co, Vector((co[0] - line_length, co[1])), co2, Vector((co2[0] + line_length, co2[1]))]

                            if co[1] >= co2[1]:
                                offsetx, offsety = 5, -0.8
                                draw_text(self, "Material", *co, size=size, offsetx=offsetx, offsety=offsety, HUDalpha=1 if self.matchmat else 0.6)

                                offsetx, offsety = -0.8, 1.6
                                draw_text(self, "Material 2", *co2, size=size, offsetx=offsetx, offsety=offsety, HUDalpha=1 if self.matchmat2 else 0.6)

                            else:
                                offsetx, offsety = 5, 1.6
                                draw_text(self, "Material", *co, size=size, offsetx=offsetx, offsety=offsety, HUDalpha=1 if self.matchmat else 0.6)

                                offsetx, offsety = -0.8, -0.8
                                draw_text(self, "Material 2", *co2, size=size, offsetx=offsetx, offsety=offsety, HUDalpha=1 if self.matchmat2 else 0.6)

                        else:
                            line_coords = [co, Vector((co[0] + line_length, co[1])), co2, Vector((co2[0] - line_length, co2[1]))]

                            if co[1] >= co2[1]:
                                offsetx, offsety = -0.8, -0.8
                                draw_text(self, "Material", *co, size=size, offsetx=offsetx, offsety=offsety, HUDalpha=1 if self.matchmat else 0.6)

                                offsetx, offsety = 6.6, 1.6
                                draw_text(self, "Material 2", *co2, size=size, offsetx=offsetx, offsety=offsety, HUDalpha=1 if self.matchmat2 else 0.6)

                            else:
                                offsetx, offsety = -0.8, 1.6
                                draw_text(self, "Material", *co, size=size, offsetx=offsetx, offsety=offsety, HUDalpha=1 if self.matchmat else 0.6)

                                offsetx, offsety = 6.6, -0.8
                                draw_text(self, "Material 2", *co2, size=size, offsetx=offsetx, offsety=offsety, HUDalpha=1 if self.matchmat2 else 0.6)

                        draw_lines2d(line_coords, width=2, alpha=0.5)

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            update_HUD_location(self, event)

        events = ['WHEELUPMOUSE', 'ONE', 'WHEELDOWNMOUSE', 'TWO', 'S', 'D', 'F']

        if event.type in events:

            match = False

            if len(self.mats) > 1:
                if event.type in {'WHEELUPMOUSE', 'ONE'} and event.value == 'PRESS':
                    if event.shift and self.matchmat:
                        self.material = step_list(self.material, self.mats, 1, loop=True)
                        match = True
                    elif event.ctrl and self.matchmat2:
                        self.material2 = step_list(self.material2, self.mats, 1, loop=True)
                        match = True
                    elif not event.shift and not event.ctrl and self.matchsub:
                        self.subset = step_list(self.subset, self.mats, 1, loop=True)
                        match = True

                elif event.type in {'WHEELDOWNMOUSE', 'TWO'} and event.value == 'PRESS':
                    if event.shift and self.matchmat:
                        self.material = step_list(self.material, self.mats, -1, loop=True)
                        match = True
                    elif event.ctrl and self.matchmat2:
                        self.material2 = step_list(self.material2, self.mats, -1, loop=True)
                        match = True
                    elif not event.shift and not event.ctrl and self.matchsub:
                        self.subset = step_list(self.subset, self.mats, -1, loop=True)
                        match = True

            if event.type == 'S' and event.value == "PRESS" and self.hassub:
                self.matchsub = not self.matchsub
                match = True

            elif event.type == 'D' and event.value == "PRESS" and self.hasmat:
                self.matchmat = not self.matchmat
                match = True

            elif event.type == 'F' and event.value == "PRESS" and self.hasmat2:
                self.matchmat2 = not self.matchmat2
                match = True

            if match:
                if any([self.matchsub, self.matchmat, self.matchmat2]):
                    for obj, init_mat in self.decals:
                        matchmatname = self.material if self.matchmat else None
                        matchmat2name = self.material2 if self.matchmat2 and init_mat.DM.decaltype == "PANEL" else None
                        matchsubname = self.subset if self.matchsub and init_mat.DM.decaltype in ["SUBSET", "PANEL"] else None

                        mat, matched_type = match_material(obj, init_mat, matchmatname=matchmatname, matchmat2name=matchmat2name, matchsubname=matchsubname)

                        if matched_type == "MATCHED":
                            self.created_mats.append(mat)

                else:
                    for obj, init_mat in self.decals:
                        obj.active_material = init_mat

        elif event.type in {'MIDDLEMOUSE'} or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}):

            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'SPACE'}:
            self.finish()

            active_mats = [obj.active_material for obj, _ in self.decals]
            purge_mats = [mat for mat in self.created_mats if mat not in active_mats]

            for mat in purge_mats:
                if mat.users < 1:
                    remove_decalmat(mat)

            self.report_version_errors()

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')

        finish_status(self)

    def cancel_modal(self):
        self.finish()

        for obj, init_mat in self.decals:
            obj.active_material = init_mat

        for mat in self.created_mats:
            remove_decalmat(mat)

    def invoke(self, context, event):
        self.mats = [mat.name for mat in set_match_material_enum()]

        self.mats.insert(0, "None")
        self.mats.insert(1, "Default")

        expected_version = get_version_from_blender(use_float=True)

        sel = [(obj, obj.active_material) for obj in context.selected_objects if obj.DM.isdecal and obj.active_material.DM.isdecalmat and not obj.DM.preatlasmats and not obj.DM.prejoindecals and get_decalmat(obj) and get_decalmat(obj).DM.decaltype != "INFO"]

        self.decals = []
        self.legacy_decals = []
        self.future_decals = []

        for obj, mat in sel:
            decal_version = shape_version(mat.DM.version)

            if decal_version == expected_version:
                self.decals.append((obj, mat))

            else:
                obj.select_set(False)

                if decal_version < expected_version:
                    self.legacy_decals.append(obj)
                else:
                    self.future_decals.append(obj)

        if self.decals:
            self.hasmat = True if any(mat.DM.decaltype in ["SIMPLE", "SUBSET", "PANEL"] for _, mat in self.decals) else False
            self.hasmat2 = True if any(mat.DM.decaltype in ["PANEL"] for _, mat in self.decals) else False
            self.hassub = True if any(mat.DM.decaltype in ["SUBSET", "PANEL"] for _, mat in self.decals) else False

            self.matchmat = True if self.hasmat and not self.hasmat2 and not self.hassub else False
            self.matchmat2 = False
            self.matchsub = True if self.hassub else False

            if len(self.decals) == 1:
                mat = self.decals[0][0].active_material

                self.material = mat.DM.matchedmaterialto.name if mat.DM.matchedmaterialto and mat.DM.matchedmaterialto.name in self.mats else self.mats[0]
                self.material2 = mat.DM.matchedmaterial2to.name if mat.DM.matchedmaterial2to and mat.DM.matchedmaterial2to.name in self.mats else self.mats[0]
                self.subset = mat.DM.matchedsubsetto.name if mat.DM.matchedsubsetto and mat.DM.matchedsubsetto.name in self.mats else self.mats[0]

            else:
                self.material = self.mats[0]
                self.material2 = self.mats[0]
                self.subset = self.mats[0]

            if any([self.matchsub, self.matchmat, self.matchmat2]):

                self.created_mats = []

                for obj, init_mat in self.decals:

                    matchmatname = self.material if self.matchmat else None
                    matchmat2name = self.material2 if self.matchmat2 and init_mat.DM.decaltype == "PANEL" else None
                    matchsubname = self.subset if self.matchsub and init_mat.DM.decaltype in ["SUBSET", "PANEL"] else None

                    mat, matched_type = match_material(obj, init_mat, matchmatname=matchmatname, matchmat2name=matchmat2name, matchsubname=matchsubname)

                    if matched_type == "MATCHED":
                        self.created_mats.append(mat)

            self.dg = context.evaluated_depsgraph_get()
            self.panels = [obj for obj, _ in self.decals if obj.DM.decaltype == 'PANEL'] if self.hasmat2 else []

            init_cursor(self, event)

            init_status(self, context, "Match Material")

            self.area = context.area
            self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), "WINDOW", "POST_PIXEL")

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        else:
            self.report_version_errors()

            return {'CANCELLED'}

    def get_panel_indicator_coords(self, depsgraph, region, rv3d, panels, debug=False):
        view_origin = region_2d_to_origin_3d(region, rv3d, (region.width / 2, region.height / 2), clamp=None)

        coords = []

        if debug:
            draw_point(view_origin, color=red, size=10, modal=False)

        for panel in panels:
            _, _, co, _, faceidx, _ = get_closest(depsgraph, [panel], view_origin, debug=debug)

            if debug:
                draw_point(co, size=6, modal=False)

            origin, origin2, _ = get_two_origins_from_face(panel.evaluated_get(depsgraph), index=faceidx, debug=debug)

            if debug:
                draw_point(origin, color=red, size=6, modal=False)
                draw_point(origin2, color=blue, size=6, modal=False)

            coords.append((location_3d_to_region_2d(region, rv3d, origin, default=None), location_3d_to_region_2d(region, rv3d, origin2, default=None)))
        if debug:
            for panel, (co, co2) in zip(panels, coords):
                print(panel.name, co, co2)

        return coords

    def report_version_errors(self):
        if self.legacy_decals or self.future_decals:
            msg = ["Matching the following decals failed:"]

            if self.legacy_decals:
                for obj in self.legacy_decals:
                    msg.append(f" • {obj.name}")

                msg.append("These are legacy decals, that need to be updated before they can be used!")

            if self.future_decals:
                if self.legacy_decals: 
                    msg.append('')

                for obj in self.future_decals:
                    msg.append(f" • {obj.name}")

                msg.append("These are next-gen decals, that can't be used in this Blender version!")

            popup_message(msg)
