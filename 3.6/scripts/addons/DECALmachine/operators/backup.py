import bpy
from mathutils import Matrix
from .. utils.object import parent, update_local_view
from .. utils.math import flatten_matrix



class GetBackup(bpy.types.Operator):
    bl_idname = "machin3.get_backup_decal"
    bl_label = "MACHIN3: Get Backup Decal"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Default: Retrieve Decal Backup\nAlt: Delete Projected/Sliced Decal"


    def draw(self, context):
        layout = self.layout
        col = layout.column()

    @classmethod
    def poll(cls, context):
        return any(obj for obj in context.selected_objects if obj.DM.isdecal and obj.DM.decalbackup)

    def invoke(self, context, event):
        decals = [obj for obj in context.selected_objects if obj.DM.isdecal and obj.DM.decalbackup]
        active = context.active_object

        for decal in decals:

            if event.alt:
                backup = decal.DM.decalbackup

            else:
                backup = decal.DM.decalbackup.copy()
                backup.data = decal.DM.decalbackup.data.copy()

            if backup.DM.isdecal:
                cols = [col for col in decal.users_collection]

                for col in cols:
                    col.objects.link(backup)

            else:
                context.scene.collection.objects.link(backup)


            if decal.parent:
                backup.matrix_world = decal.parent.matrix_world @ backup.DM.backupmx

                if decal.parent != backup.parent:
                    parent(backup, decal.parent)

            backup.DM.isbackup = False
            backup.use_fake_user = False

            backup.select_set(True)

            if decal == active:
                context.view_layer.objects.active = backup

            if event.alt:
                bpy.data.meshes.remove(decal.data, do_unlink=True)

            else:
                decal.select_set(False)

            update_local_view(context.space_data, [(backup, True)])

        return {'FINISHED'}
