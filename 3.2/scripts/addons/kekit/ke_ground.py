import bpy
from .ke_utils import point_axis_raycast


def zmove(value, zonly=True):
    if zonly:
        values = (0, 0, value)
    else:
        values = value
    bpy.ops.transform.translate(value=values, orient_type='GLOBAL',
                                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                                mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
                                proportional_size=1, use_proportional_connected=False,
                                use_proportional_projected=False, release_confirm=True)


class VIEW3D_OT_ke_ground(bpy.types.Operator):
    bl_idname = "view3d.ke_ground"
    bl_label = "Ground (or Center)"
    bl_description = "Ground (or Center) selected Object(s), or selected elements (snap to world Z0 only)"
    bl_options = {'REGISTER', 'UNDO'}

    ke_ground_option: bpy.props.EnumProperty(
        items=[("GROUND", "Ground to Z0", "", 1),
               ("CENTER", "Ground & Center on Z", "", 2),
               ("CENTER_ALL", "Center XYZ", "", 3),
               ("CENTER_GROUND", "Center XY & Ground Z", "", 4),
               ("UNDER", "(Under)Ground to Z0", "", 5),
               ("CUSTOM", "Ground to custom Z", "", 6),
               ("CUSTOM_CENTER", "Center to custom Z", "", 7)],
        name="Operation",
        default="GROUND")

    ke_ground_custom: bpy.props.FloatProperty(
        name="Custom Z Location:", description="Set custom coordinate on Z axis", default=0)

    ke_ground_raycasting: bpy.props.BoolProperty(
        name="Raycast:", description="Stops on obstructions on the way down (Nothing: Z0)", default=True)

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        sel_obj = [o for o in context.selected_objects]
        if not sel_obj:
            self.report({"INFO"}, "Ground: Selection Error?")
            return {'CANCELLED'}

        offset = 0
        if context.object.type == "MESH":
            editmode = bool(context.object.data.is_editmode)
        else:
            editmode = False

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action="DESELECT")

        for o in sel_obj:
            o.select_set(True)
            context.view_layer.objects.active = o

            if o.type == 'MESH':
                if editmode:
                    vc = [o.matrix_world @ v.co for v in o.data.vertices if v.select]
                else:
                    vc = [o.matrix_world @ v.co for v in o.data.vertices]
                vz = []
                for co in vc:
                    vz.append(co[2])
                zs = sorted(vz)
            else:
                vc = [o.location, o.location]
                zs = [vc[0][2], vc[1][2]]


            if self.ke_ground_raycasting and vc:
                coords = sorted(vc, key=lambda x: x[2])
                point = coords[0]
                point[2] -= 0.0001  # hack so it doesn't trace itself...

                raycast = point_axis_raycast(context, vec_point=point, axis=2)
                if raycast[1] is not None:
                    hit = raycast[1]
                    hit[2] -= 0.0001  # hack some more
                    dist = coords[0][2] - hit[2]
                    zs[-1] = dist + (zs[-1] - zs[0])
                    zs[0] = dist

                    if zs[0] == 0:
                        print("Ground: Raycast error. Aborting.")
                        for ob in sel_obj:
                            ob.select_set(True)
                        return {"CANCELLED"}

            if editmode:
                bpy.ops.object.mode_set(mode='EDIT')

            if vc:
                if self.ke_ground_option == "GROUND":
                    offset = round(zs[0], 6) * -1

                elif self.ke_ground_option == "CENTER":
                    offset = round(zs[0] + ((zs[-1] - zs[0]) / 2), 6) * -1

                elif self.ke_ground_option == "CENTER_ALL":
                    zx = sorted([c[0] for c in vc])
                    zy = sorted([c[1] for c in vc])
                    xo = round(zx[0] + ((zx[-1] - zx[0]) / 2), 6) * -1
                    yo = round(zy[0] + ((zy[-1] - zy[0]) / 2), 6) * -1
                    zo = round(zs[0] + ((zs[-1] - zs[0]) / 2), 6) * -1
                    zmove((xo, yo, zo), zonly=False)

                elif self.ke_ground_option == "CENTER_GROUND":
                    zx = sorted([c[0] for c in vc])
                    zy = sorted([c[1] for c in vc])
                    xo = round(zx[0] + ((zx[-1] - zx[0]) / 2), 6) * -1
                    yo = round(zy[0] + ((zy[-1] - zy[0]) / 2), 6) * -1
                    zo = round(zs[0], 6) * -1
                    zmove((xo, yo, zo), zonly=False)

                elif self.ke_ground_option == "UNDER":
                    offset = round(zs[-1], 6) * -1

                elif self.ke_ground_option == "CUSTOM":
                    offset = (round(zs[0], 6) - self.ke_ground_custom) * -1

                elif self.ke_ground_option == "CUSTOM_CENTER":
                    offset = (round(zs[0] + ((zs[-1] - zs[0]) / 2), 6) - self.ke_ground_custom) * -1

                if offset and self.ke_ground_option != "CENTER_ALL":
                    zmove(offset)

            bpy.ops.object.mode_set(mode='OBJECT')
            o.select_set(False)

        for ob in sel_obj:
            ob.select_set(True)

        if editmode:
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


# -------------------------------------------------------------------------------------------------
# Class Registration & Unregistration
# -------------------------------------------------------------------------------------------------
def register():
    bpy.utils.register_class(VIEW3D_OT_ke_ground)


def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_ke_ground)


if __name__ == "__main__":
    register()
