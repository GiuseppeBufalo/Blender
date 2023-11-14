import bpy
from .. utils.decal import apply_decal, set_defaults
from .. utils.collection import sort_into_collections
from .. utils.ui import popup_message
from .. utils.material import get_decalmat


class ReApply(bpy.types.Operator):
    bl_idname = "machin3.reapply_decal"
    bl_label = "MACHIN3: Re-Apply Decal"
    bl_description = "Re-Apply Decal to (new) Object. Parents Decal, Sets Up Custom Normals and Auto-Matches Materials\nALT: Forcibly auto-match Material, even if a specific Material is selected."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(obj for obj in context.selected_objects if obj.DM.isdecal and not obj.DM.preatlasmats and not obj.DM.prejoindecals and get_decalmat(obj))

    def invoke(self, context, event):
        dg = context.evaluated_depsgraph_get()

        decals = [obj for obj in context.selected_objects if obj.DM.isdecal and not obj.DM.preatlasmats and not obj.DM.prejoindecals and get_decalmat(obj)]
        target = context.active_object if context.active_object and context.active_object in context.selected_objects and not context.active_object.DM.isdecal else None

        failed = []

        for obj in decals:

            applied = apply_decal(dg, obj, target=target, force_automatch=event.alt)

            if applied:

                set_defaults(decalobj=obj, decalmat=obj.active_material, ignore_material_blend_method=True)

                sort_into_collections(context, obj)

                dg.update()

            else:
                failed.append(obj)

        if failed:
            msg = ["Re-applying the following decals failed:"]

            for obj in failed:
                msg.append(" • " + obj.name)

            msg.append("Try again on a different area of the model!")
            msg.append("You can also force apply to an non-decal object by selecting it last.")

            popup_message(msg)

        return {'FINISHED'}
