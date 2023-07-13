import bpy


class SweepDecalBackups(bpy.types.Operator):
    bl_idname = "machin3.sweep_decal_backups"
    bl_label = "MACHIN3: sweep_decal_backups"
    bl_description = "Sweep up Decal Backups, that became visible aber appending objects from other blend files"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return [obj for obj in context.scene.objects if obj.DM.isbackup]

    def execute(self, context):
        backupobjs = [obj for obj in context.scene.objects if obj.DM.isbackup]

        for obj in backupobjs:
            obj.use_fake_user = True

            for col in obj.users_collection:
                col.objects.unlink(obj)

        return {'FINISHED'}
