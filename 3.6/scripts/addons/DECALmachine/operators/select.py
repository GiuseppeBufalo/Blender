import bpy
from bpy.props import BoolProperty, EnumProperty
from .. items import select_mode_items


class Select(bpy.types.Operator):
    bl_idname = "machin3.select_decals"
    bl_label = "MACHIN3: Select Decals"
    bl_options = {'REGISTER', 'UNDO'}

    decal_mode: BoolProperty(name="Decal Mode", default=False)
    select_mode: EnumProperty(name='Select Mode', items=select_mode_items, default='COMMONPARENT')
    keep_parents_selected: BoolProperty(name="Keep Decal Parents Selected", default=False)

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        if self.decal_mode:
            row = column.row()
            row.prop(self, "select_mode", expand=True)

        else:
            column.prop(self, "keep_parents_selected", toggle=True)

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        sel = context.selected_objects

        if all(obj.DM.isdecal for obj in sel):
            self.decal_mode = True

            sel_decals = [obj for obj in sel if obj.DM.isdecal]
            all_decals = [obj for obj in context.visible_objects]

            decaluuids = {obj.DM.uuid for obj in sel_decals}

            if self.select_mode == 'ALL':
                for obj in all_decals:
                    if obj.DM.uuid in decaluuids:
                        obj.select_set(True)

            elif self.select_mode == 'COMMONPARENT':
                parents = {obj.parent for obj in sel_decals if obj.parent}

                for obj in all_decals:
                    if obj.DM.uuid in decaluuids and obj.parent in parents:
                        obj.select_set(True)


        else:
            self.decal_mode = False
            decals = [obj for obj in context.visible_objects if obj.DM.isdecal and obj.parent in sel]

            if decals:
                if not self.keep_parents_selected:
                    for obj in sel:
                        obj.select_set(False)

                for decal in decals:
                    decal.select_set(True)

                context.view_layer.objects.active = decals[0]

        return {'FINISHED'}
