import bpy
from .. utils.object import flatten, lock
from .. utils.modifier import add_displace
from .. utils.collection import sort_into_collections
from .. utils.ui import popup_message


class Join(bpy.types.Operator):
    bl_idname = "machin3.join_decal"
    bl_label = "MACHIN3: Join Decal"
    bl_description = "Join multiple Decals to a single Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return len([obj for obj in context.selected_objects if obj.DM.isdecal]) > 1

    def execute(self, context):

        active, decals, atlased = self.get_decals(context)

        if len(decals) <= 1:
            popup_message(["Your selection includes a mix of standard and atlased decals. Joining mixed selections is not permitted", "As a result, only one decal is left to join, aborting."], title="Illegal Selection")
            return {'CANCELLED'}

        joined, collections = self.create_duplicates(context, decals)

        bpy.ops.object.join()

        bpy.ops.object.material_slot_remove_unused()

        add_displace(joined, height=1)

        joined.DM.prejoindecals.clear()

        joined.DM.decalbackup = None

        lock(joined)

        for col in collections:
            if joined.name not in col.objects:
                col.objects.link(joined)

        for decal in decals:
            d = joined.DM.prejoindecals.add()
            d.name = decal.name
            d.obj = decal

            if decal == active:
                d.isactive = True

        joined.DM.isjoinedafteratlased = atlased

        return {'FINISHED'}

    def create_duplicates(self, context, decals):

        duplicates = []
        collections = set()

        for idx, decal in enumerate(decals):
            isactive = context.view_layer.objects.active == decal

            decal.use_fake_user = True
            decal.DM.wasjoined = True

            dup = decal.copy()
            dup.data = decal.data.copy()
            duplicates.append(dup)

            for col in decal.users_collection:
                col.objects.unlink(decal)
                col.objects.link(dup)

                collections.add(col)

            if isactive:
                context.view_layer.objects.active = dup

            dup.select_set(True)

        dg = context.evaluated_depsgraph_get()

        for dup in duplicates:
            flatten(dup, depsgraph=dg)

        return context.active_object, collections

    def get_decals(self, context):

        all_decals = sorted([obj for obj in context.selected_objects if obj.DM.isdecal], key=lambda x: x.name)

        atlased_decals = [obj for obj in all_decals if obj.DM.preatlasmats]
        standard_decals = [obj for obj in all_decals if not obj.DM.preatlasmats]

        decals = standard_decals if len(standard_decals) >= len(atlased_decals) else atlased_decals

        active = decals[0] if context.active_object not in decals else context.active_object
        context.view_layer.objects.active = active

        bpy.ops.object.select_all(action='DESELECT')

        for decal in decals:
            decal.select_set(True)

        return active, decals, len(atlased_decals) > len(standard_decals)


class JoinAtlased(bpy.types.Operator):
    bl_idname = "machin3.join_atlased_decals"
    bl_label = "MACHIN3: Join Atlased Decals"
    bl_description = "Automatically select and join all visible atlased Decals, per Atlas, and optionally per Parent"
    bl_options = {'REGISTER', 'UNDO'}
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.visible_objects if obj.DM.isdecal and obj.DM.preatlasmats]

    def execute(self, context):
        atlased_decals = [obj for obj in context.visible_objects if obj.DM.isdecal and obj.DM.preatlasmats]

        join, skipped = self.create_join_dict(context, atlased_decals, debug=False)

        self.join_decals(context, join, debug=False)

        if skipped:
            popup_message(["The following decals were not joined, because they carry different atlas materials:", *[" • %s" % (decal.name) for decal in skipped]])

        return {'FINISHED'}

    def join_decals(self, context, join, debug=False):

        joined = []

        for parent, atlasdecals in join.items():
            if debug:
                print()
                print("parent:", parent)

            for mat, decals in atlasdecals.items():
                if debug:
                    print()
                    print(" mat:", mat.name)
                    print(" decals:", [decal.name for decal in decals])

                if len(decals) > 1:
                    if debug:
                        print(" decals:", [decal.name for decal in decals])

                    bpy.ops.object.select_all(action='DESELECT')

                    for decal in decals:
                        decal.select_set(True)

                    context.view_layer.objects.active = decals[0]

                    bpy.ops.machin3.join_decal()

                    context.active_object.name = "%s_%s" % (parent.name, mat.DM.atlasname) if parent else mat.DM.atlasname

                    joined.append(context.active_object)

        if joined:
            if debug:
                print("Joined decals", [decal.name for decal in joined])

            for decal in joined:
                decal.select_set(True)

            context.view_layer.objects.active = joined[0]

    def create_join_dict(self, context, atlased_decals, debug=False):

        join = {}
        skipped = []

        for decal in atlased_decals:
            parent = decal.parent if context.scene.DM.export_atlas_join_atlased_per_parent else None
            atlasmats = {mat for mat in decal.data.materials if mat and mat.DM.isatlasmat}

            if debug:
                print()
                print(decal.name)
                print(" parent:", parent.name if parent else 'None')
                print(" atlas mats:", [mat.name for mat in atlasmats])

            if not atlasmats:
                if debug:
                    print(" skipping, no atlases found")
                continue

            elif len(atlasmats) > 1:
                if debug:
                    print(" skipping, multiple atlases found")
                skipped.append(decal)
                continue

            else:
                if parent not in join:
                    join[parent] = {}

                mat = atlasmats.pop()
                if debug:
                    print(" mat:", mat.name)

                if mat not in join[parent]:
                    join[parent][mat] = []

                join[parent][mat].append(decal)

        return join, skipped


class Split(bpy.types.Operator):
    bl_idname = "machin3.split_decal"
    bl_label = "MACHIN3: Split Decal"
    bl_description = "Separate previously joined Decals into their original, Individual Decals"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if obj.DM.isdecal and obj.DM.prejoindecals]

    def execute(self, context):
        joined_decals = [obj for obj in context.selected_objects if obj.DM.isdecal and obj.DM.prejoindecals]

        for joined in joined_decals:
            nondecalcollections = [col for col in joined.users_collection if not any([col.DM.isdecaltypecol, col.DM.isdecalparentcol])]

            for d in joined.DM.prejoindecals:
                decal = d.obj if d.obj else None

                if decal:
                    decal.use_fake_user = False
                    decal.DM.wasjoined = False
                    sort_into_collections(context, decal, purge=False)

                    for col in nondecalcollections:
                        if decal.name not in col.objects:
                            col.objects.link(decal)

                    if d.isactive:
                        context.view_layer.objects.active = decal

            bpy.data.meshes.remove(joined.data, do_unlink=True)

        return {'FINISHED'}


class SplitAtlased(bpy.types.Operator):
    bl_idname = "machin3.split_atlased_decals"
    bl_label = "MACHIN3: Split Atased Decals"
    bl_description = "Automatically separate all visible joined and atlased Decals into their original, individual Decals"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.visible_objects if obj.DM.isdecal and obj.DM.prejoindecals and obj.DM.isjoinedafteratlased]

    def execute(self, context):
        joined_atlased_decals = [obj for obj in context.visible_objects if obj.DM.isdecal and obj.DM.prejoindecals and obj.DM.isjoinedafteratlased]

        bpy.ops.object.select_all(action='DESELECT')

        for decal in joined_atlased_decals:
            decal.select_set(True)

        bpy.ops.machin3.split_decal()

        return {'FINISHED'}
