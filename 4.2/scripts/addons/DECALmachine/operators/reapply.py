import bpy
from .. utils.decal import apply_decal, set_defaults, ensure_decalobj_versions
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

        current_decals, legacy_decals, future_decals = ensure_decalobj_versions(decals)

        target = context.active_object if context.active_object and context.active_object in context.selected_objects and not context.active_object.DM.isdecal else None

        failed_decals = []

        for obj in current_decals:

            applied = apply_decal(dg, obj, target=target, force_automatch=event.alt)

            if applied:

                set_defaults(decalobj=obj, decalmat=obj.active_material, ignore_material_blend_method=True, ignore_normal_transfer_visibility=True)
                sort_into_collections(context, obj)

                dg.update()

            else:
                failed_decals.append(obj)

        if any((failed_decals, legacy_decals, future_decals)):
            msg = ["Re-applying the following decals failed:"]

            if failed_decals:
                for obj in failed_decals:
                    msg.append(f" • {obj.name}")

                msg.append("Try again on a different area of the model!")
                msg.append("You can also force apply to an non-decal object by selecting it last.")

            if legacy_decals:
                if failed_decals:
                    msg.append('')

                for obj in legacy_decals:
                    msg.append(f" • {obj.name}")

                msg.append("These are legacy decals, that need to be updated before they can be used!")

            if future_decals:
                if failed_decals or legacy_decals: 
                    msg.append('')

                for obj in future_decals:
                    msg.append(f" • {obj.name}")

                msg.append("These are next-gen decals, that can't be used in this Blender version!")

            popup_message(msg)

        return {'FINISHED'}
