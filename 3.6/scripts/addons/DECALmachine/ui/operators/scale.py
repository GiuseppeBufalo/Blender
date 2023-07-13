import bpy


class StoreIndividualDecalScale(bpy.types.Operator):
    bl_idname = "machin3.store_individual_decal_scale"
    bl_label = "MACHIN3: Store Individual Decal Scale"
    bl_description = "Store current Decal's Scale\nEMPTY: nothing stored for this type of decal\nHALF: scale is stored for this type of decal, but it's different than the current decal\nFULL: the current decal's scale is stored"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.DM.isdecal

    def execute(self, context):
        decal = context.active_object
        _, _, scale = decal.matrix_world.decompose()

        individualscales = context.scene.DM.individualscales

        if decal.DM.uuid in individualscales:
            ds = individualscales[decal.DM.uuid]
        else:
            ds = individualscales.add()
            ds.name = decal.DM.uuid

        ds.scale = scale

        return {'FINISHED'}


class ClearIndividualDecalScale(bpy.types.Operator):
    bl_idname = "machin3.clear_individual_decal_scale"
    bl_label = "MACHIN3: Clear Individual Decal Scale"
    bl_description = "Clear the Scale for this type of Decal"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.DM.isdecal

    def execute(self, context):
        decal = context.active_object
        individualscales = context.scene.DM.individualscales

        idx = individualscales.keys().index(decal.DM.uuid)

        individualscales.remove(idx)

        return {'FINISHED'}
