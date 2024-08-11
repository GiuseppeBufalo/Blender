import bpy
from bpy.props import BoolProperty
from .. utils.ui import popup_message
from .. utils.material import get_pbrnode_from_mat, get_decalgroup_from_decalmat, get_decal_texture_nodes, create_override_node_tree, get_override_as_dict, get_trimsheetgroup_from_trimsheetmat, is_trimsheetmat_matchable, set_override_from_dict, get_decalmat
from .. utils.decal import ensure_decalobj_versions
from .. items import override_preset_mapping

class OverrideMaterials(bpy.types.Operator):
    bl_idname = "machin3.override_decal_materials"
    bl_label = "MACHIN3: Override Decal Materials"
    bl_description = "Override BSDF (and Trim Sheet) Materials of Selected Objects, as well as their Decals\nALT: Undo Override"
    bl_options = {'REGISTER', 'UNDO'}

    undo: BoolProperty(name="Undo", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if not obj.DM.isdecal]

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row(align=True)
        row.prop(self, 'undo', text = "Undo Override", toggle=True)

    def invoke(self, context, event):
        self.undo = event.alt
        return self.execute(context)

    def execute(self, context):
        override = self.ensure_override(context)

        sel, decals, legacy, future = self.get_objects(context, debug=False)

        if self.undo:
            self.undo_override(context, sel, decals, override)

            empty = bpy.data.materials.get('EmptyOverride')

            if empty and empty.users == 0:
                bpy.data.materials.remove(empty)

            if override and override.name == 'DECALmachine Override' and override.users <= (2 if override.use_fake_user else 1):

                if override.use_fake_user:
                    context.scene.DM.avoid_update = True
                    context.scene.DM.material_override = None

                else:
                    bpy.data.node_groups.remove(override)

        else:
            self.override(context, sel, decals, override)

            if legacy or future:
                msg = [f"Overriding {'some' if decals else 'all' } decal materials failed:"]

                if legacy:
                    for obj in legacy:
                        msg.append(f" • {obj.name}")

                    msg.append("These are legacy decals, that need to be updated before they can be used!")

                if future:
                    if legacy:
                        msg.append('')

                    for obj in future:
                        msg.append(f" • {obj.name}")

                    msg.append("These are next-gen decals, that can't be used in this Blender version!")

                popup_message(msg)

        return {'FINISHED'}

    def ensure_override(self, context):
        dm = context.scene.DM

        if not dm.material_override:
            override = bpy.data.node_groups.get('DECALmachine Override')

            if not override:
                override = create_override_node_tree()

                d = override_preset_mapping[dm.material_override_preset]
                set_override_from_dict(override, d)

            dm.avoid_update = True
            dm.material_override = override

        else:
            override = dm.material_override

        return override

    def get_objects(self, context, debug=False):
        sel = [obj for obj in context.selected_objects if not obj.DM.isdecal and obj.type in ['MESH', 'CURVE']]

        if debug:
            print()
            print("selection")

            for obj in sel:
                print("", obj.name)

        decals = [ob for obj in sel for ob in obj.children_recursive if ob.DM.isdecal and ob.visible_get() and not ob.DM.preatlasmats and not ob.DM.prejoindecals and get_decalmat(ob)] 

        current_decals, legacy_decals, future_decals = ensure_decalobj_versions(decals)

        if debug:
            print()
            print("decals")

            for obj in current_decals:
                print("", obj.name)

        return sel, current_decals, legacy_decals, future_decals

    def override(self, context, sel, decals, override):
        override_decalmat_components = ['Material', 'Material 2']

        if context.scene.DM.material_override_decal_subsets:
            override_decalmat_components.append('Subset')

        for obj in sel + decals:
            materials = [mat for mat in obj.data.materials if mat]

            if not materials:
                empty = bpy.data.materials.get('EmptyOverride')

                if not empty:
                    empty = bpy.data.materials.new('EmptyOverride')
                    empty.use_nodes = True

                if obj.material_slots:
                    for slot in obj.material_slots:
                        if not slot.material:
                            slot.material = empty

                else:
                    obj.data.materials.append(empty)

                materials = [empty]

            for mat in materials:
                overrides = [node for node in mat.node_tree.nodes if node.type == 'GROUP' and node.node_tree == override]

                if not overrides:

                    if mat.DM.isdecalmat:

                        if mat.DM.decaltype == 'INFO':
                            continue

                        dg = get_decalgroup_from_decalmat(mat)

                        if dg:
                            tree = mat.node_tree

                            group = tree.nodes.new(type='ShaderNodeGroup')
                            group.width = 250
                            group.location.x -= 700 if bpy.app.version < (4, 0, 0) else 200
                            group.location.y += 500 
                            group.node_tree = override
                            group.name = 'DECALMACHINE_OVERRIDE'

                            for output in group.outputs:
                                for inputprefix in override_decalmat_components:
                                    if inputprefix == 'Subset' and mat.DM.decaltype not in ['SUBSET', 'PANEL']:
                                        continue

                                    elif inputprefix == 'Material 2' and mat.DM.decaltype != 'PANEL':
                                        continue

                                    i = dg.inputs.get(f"{inputprefix} {output.name}")

                                    if i:
                                        tree.links.new(output, i)

                                if bpy.app.version >= (4, 0, 0) and context.scene.DM.coat == 'UNDER' and not context.scene.DM.material_override_decal_subsets:
                                    if mat.DM.decaltype in ['SUBSET', 'PANEL'] and output.name.startswith('Coat '):
                                        i = dg.inputs.get(f"Subset {output.name}")

                                        if i:
                                            tree.links.new(output, i)

                            if context.scene.DM.material_override_decal_emission:
                                decal_texture_nodes = get_decal_texture_nodes(mat)

                                emission = decal_texture_nodes.get('EMISSION')
                                
                                if emission:
                                    emission.mute = True

                    elif mat.DM.istrimsheetmat:
                        if is_trimsheetmat_matchable(mat):
                            tsg = get_trimsheetgroup_from_trimsheetmat(mat)

                            if tsg:
                                tree = mat.node_tree

                                group = tree.nodes.new(type='ShaderNodeGroup')

                                group.width = 250
                                group.location.x -= 550
                                group.location.y += 500 
                                group.node_tree = override
                                group.name = 'DECALMACHINE_OVERRIDE'

                                for output in group.outputs:
                                    i = tsg.inputs.get(output.name)

                                    if i:
                                        tree.links.new(output, i)

                    else:

                        bsdf = get_pbrnode_from_mat(mat)

                        if bsdf:
                            tree = mat.node_tree

                            group = tree.nodes.new(type='ShaderNodeGroup')
                            group.width = 250
                            group.location.x -= 300
                            group.location.y += 200 
                            group.node_tree = override
                            group.name = 'DECALMACHINE_OVERRIDE'

                            for output in group.outputs:
                                i = bsdf.inputs.get(output.name)

                                if i:
                                    tree.links.new(output, i)

    def undo_override(self, context, sel, decals, override):
        empty = bpy.data.materials.get('EmptyOverride')

        for obj in sel + decals:
            materials = [mat for mat in obj.data.materials if mat]

            for mat in materials:

                overrides = [node for node in mat.node_tree.nodes if node.type == 'GROUP' and node.node_tree == override]

                for group in overrides:
                    mat.node_tree.nodes.remove(group)

                    if mat.DM.isdecalmat:
                        decal_texture_nodes = get_decal_texture_nodes(mat)
                        emission = decal_texture_nodes.get('EMISSION')
                                        
                        if emission and emission.mute:
                            emission.mute = False

                if mat == empty:
                    obj.data.materials.pop(index=list(obj.data.materials).index(mat))

            if not any(mat for mat in obj.data.materials):
                obj.data.materials.clear()
