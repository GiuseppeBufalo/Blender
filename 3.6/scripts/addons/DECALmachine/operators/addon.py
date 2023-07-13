import bpy
from bpy.props import IntProperty, BoolProperty
from .. utils.registration import get_addon
from .. utils.collection import sort_into_collections, purge_decal_collections


class GroupProDissolve(bpy.types.Operator):
    bl_idname = "machin3.grouppro_dissolve"
    bl_label = "MACHIN3: GroupPro Dissolve"
    bl_description = "Dissolve Group. Sorts Decals into Collections again and restores Decal Backup relationships.\nALT: Custom Dissolve, that brings back the original objects"
    bl_options = {'REGISTER', 'UNDO'}

    restore_originals: BoolProperty(name="Restore Orignal Objects", description="Restore original group objects, not duplicates", default=False)
    maxDept: IntProperty(name="Max Depth", description="Maximum depth for which groups will be converted to geometry. 0-infinite depth, default=1 ", default=1, min=0)


    def draw(self, context):
        layout = self.layout

        column = layout.column()

        column.prop(self, "restore_originals")

        if not self.restore_originals:
            column.prop(self, 'maxDept')


    def invoke(self, context, event):
        self.restore_originals = event.alt

        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        grouppro, _, _, _ = get_addon('Group Pro')

        if grouppro:
            groups = [obj for obj in context.selected_objects if obj.type == 'EMPTY' and obj.instance_collection]

            for group in groups:
                bpy.ops.object.select_all(action='DESELECT')

                context.view_layer.objects.active = group
                group.select_set(True)

                if self.restore_originals:
                    mx = group.matrix_world

                    groupcol = group.instance_collection
                    acol = context.view_layer.active_layer_collection.collection

                    decals = []

                    for obj in groupcol.objects:
                        acol.objects.link(obj)
                        obj.use_fake_user = False
                        if not obj.parent:
                            obj.matrix_world = mx @ obj.matrix_world

                        if obj.DM.isdecal:
                            decals.append(obj)

                    for obj in decals:
                        sort_into_collections(context, obj, purge=False)

                    bpy.data.collections.remove(groupcol, do_unlink=True)
                    bpy.data.objects.remove(group, do_unlink=True)


                else:
                    bpy.ops.object.gpro_converttogeo(maxDept=self.maxDept)

                    decals = [obj for obj in context.selected_objects if obj.DM.isdecal]

                    for decal in decals:
                        sort_into_collections(context, decal, purge=False)

                        if decal.parent:
                            if decal.DM.projectedon:
                                decal.DM.projectedon = decal.parent

                            if decal.DM.slicedon:
                                decal.DM.slicedon = decal.parent

                purge_decal_collections(debug=True)

        return {'FINISHED'}
