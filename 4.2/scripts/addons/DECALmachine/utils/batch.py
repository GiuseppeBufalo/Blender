import bpy
import os
from . material import get_decalgroup_as_dict, get_defaultmetal_as_dict, get_overridegroup, get_parallaxgroup_from_decalmat, get_decal_texture_nodes, get_decalgroup_from_decalmat, get_heightgroup_from_parallaxgroup, get_parallaxgroup_from_any_mat, get_pbrnode_as_dict, get_pbrnode_from_mat, set_decalgroup_from_dict
from . registration import get_prefs
from . system import splitpath, log, printd
from . scene import setup_surface_snapping
from . property import set_cycles_visibility

def toggle_visibility(state, types, debug=False):
    for type in types:

        if state:
            if not type.name.startswith("."):
                if debug:
                    print("Hiding %s." % (type.name))
                type.name = ".%s" % type.name

        else:
            if type.name.startswith("."):
                if debug:
                    print("Unhiding %s." % (type.name))
                type.name = type.name[1:]

def toggle_material_visibility(state, debug=False):
    decalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat]

    toggle_visibility(state, decalmats, debug=debug)

def toggle_texture_visibility(state, debug=False):
    decaltextures = [img for img in bpy.data.images if img.DM.isdecaltex]

    toggle_visibility(state, decaltextures, debug=debug)

def toggle_nodetree_visibility(state, debug=False):
    decalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat]

    decalnodetrees = set()

    for mat in decalmats:
        dg = get_decalgroup_from_decalmat(mat)

        if dg:
            decalnodetrees.add(dg.node_tree)

        pg = get_parallaxgroup_from_decalmat(mat)

        if pg:
            decalnodetrees.add(pg.node_tree)

            hg = get_heightgroup_from_parallaxgroup(pg)

            if hg:
                decalnodetrees.add(hg.node_tree)

    toggle_visibility(state, decalnodetrees, debug=debug)

def toggle_decaltype_collection_visibility(state, debug=False):
    cols = [col for col in bpy.data.collections if col.DM.isdecaltypecol]

    toggle_visibility(state, cols, debug=debug)

def toggle_decalparent_collection_visibility(state, debug=False):
    cols = [col for col in bpy.data.collections if col.DM.isdecalparentcol]

    toggle_visibility(state, cols, debug=debug)

def toggle_parallax(state, debug=False):
    decalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.decaltype in ['SIMPLE', 'SUBSET', 'PANEL']]

    for mat in decalmats:
        if debug:
            print(mat)

        pg = get_parallaxgroup_from_decalmat(mat)

        if debug:
            print(pg)

        if pg:
            pg.mute = not state

    sheetmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat or mat.DM.isatlasmat]

    for mat in sheetmats:
        if debug:
            print(mat)

        pg = get_parallaxgroup_from_any_mat(mat)

        if debug:
            print(pg)

        if pg:
            pg.mute = not state

def toggle_glossyrays(state, debug=False):
    decals = [obj for obj in bpy.data.objects if obj.DM.isdecal]

    for decal in decals:
        if debug:
            print(decal)

        set_cycles_visibility(decal, 'glossy', state)

def toggle_normaltransfer_render(state, debug=False):
    mods = [obj.modifiers.get("NormalTransfer") for obj in bpy.data.objects if obj.DM.isdecal and "NormalTransfer" in obj.modifiers]

    for mod in mods:
        if debug:
            print(mods)

        mod.show_render = state

    bpy.context.evaluated_depsgraph_get()

def toggle_normaltransfer_viewport(state, debug=False):
    mods = [obj.modifiers.get("NormalTransfer") for obj in bpy.data.objects if obj.DM.isdecal and "NormalTransfer" in obj.modifiers]

    for mod in mods:
        if debug:
            print(mods)

        mod.show_viewport = state

    bpy.context.evaluated_depsgraph_get()

def toggle_color_interpolation(state, debug=False):
    decalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.decaltype in ["INFO"]]

    for mat in decalmats:
        log(mat, debug=debug)

        nodes = get_decal_texture_nodes(mat)
        color = nodes.get('COLOR')

        if color:
            color.interpolation = state

        masks = nodes.get('MASKS')

        if masks:
            masks.interpolation = state

def switch_alpha_blendmode(state, debug=False):
    decalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat]

    for mat in decalmats:
        if debug:
            print(mat)

        mat.blend_method = state

def change_ao_strength(state, debug=False):
    decalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.decaltype in ["SIMPLE", "SUBSET", "PANEL"]]

    for mat in decalmats:
        if debug:
            print(mat)

        decalgroup = get_decalgroup_from_decalmat(mat)

        if decalgroup:
            ao = decalgroup.inputs["AO Multiplier"]

            if ao:
                ao.default_value = state

def invert_infodecals(state, debug=False):
    decalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.decaltype == "INFO"]

    for mat in decalmats:
        if debug:
            print(mat)

        decalgroup = get_decalgroup_from_decalmat(mat)

        if decalgroup:
            invert = decalgroup.inputs["Invert"]

            if invert:
                invert.default_value = int(state)

def switch_edge_highlights(state, debug=False):
    decalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.decaltype in ["SIMPLE", "SUBSET", "PANEL"]]

    for mat in decalmats:
        if debug:
            print(mat)

        decalgroup = get_decalgroup_from_decalmat(mat)

        if decalgroup:
            highlights = decalgroup.inputs["Curvature Multiplier"]

            if highlights:
                highlights.default_value = float(state)

def toggle_coat(state, debug=False):
    decalmats = [(mat, get_decalgroup_from_decalmat(mat)) for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.decaltype in ["SIMPLE", "SUBSET", "PANEL"]]
    node_trees = set(dg.node_tree for _, dg in decalmats if dg)

    for tree in node_trees:
        treetype = 'SIMPLE' if 'simple.decal_group' in tree.name else 'SUBSET' if 'subset.decal_group' in tree.name else 'PANEL' if 'panel.decal_group' in tree.name else None

        if treetype:
            components = ['Material']

            if treetype == 'PANEL':
                components.append('Material 2')

            if treetype in ['SUBSET', 'PANEL']:
                components.append('Subset')

            for comp in components:
                bsdf = tree.nodes.get(comp)
                normal = tree.nodes.get(f"{comp} Normal")
                coat_normal = tree.nodes.get(f"{comp} Coat Normal")

                if state == 'UNDER':
                    if coat_normal and bsdf:
                        i = bsdf.inputs.get("Coat Normal")
                        tree.links.new(coat_normal.outputs[0], i)

                else:
                    if normal and bsdf:
                        i = bsdf.inputs.get("Coat Normal")
                        tree.links.new(normal.outputs[0], i)

    dm = bpy.context.scene.DM
    override = dm.material_override
    override_subsets = dm.material_override_decal_subsets

    for mat, dg in decalmats:
        if mat.DM.decaltype in ['SUBSET', 'PANEL']:

            if state == 'UNDER':

                if mat.DM.matchedmaterialto:
                    materialdict = get_decalgroup_as_dict(dg)[0]

                else:
                    materialdict = get_decalgroup_as_dict(dg)[1]

                coatdict = {name: value for name, value in materialdict.items() if 'Coat' in name}

            else:

                matchmat = mat.DM.matchedsubsetto

                if matchmat:
                    bsdf = get_pbrnode_from_mat(matchmat)

                    if bsdf:
                        subsetdict = get_pbrnode_as_dict(bsdf)

                    else:
                        continue

                else:
                    subsetdict = get_defaultmetal_as_dict()
                coatdict = {name: value for name, value in subsetdict.items() if 'Coat' in name}

            set_decalgroup_from_dict(dg, subset=coatdict)

            if override:
                tree = mat.node_tree

                og = get_overridegroup(mat)

                if og:
                    coat_outputs = [out for out in og.outputs if out.name.startswith('Coat ')]

                    for out in coat_outputs:
                        i = dg.inputs.get(f"Subset {out.name}")

                        if i:

                            if state == 'UNDER':
                                tree.links.new(out, i)

                            else:
                                subset_link = None

                                for link in out.links:
                                    if link.to_node == dg and link.to_socket == i:
                                        subset_link = link
                                        break

                                if subset_link and not override_subsets:
                                    tree.links.remove(subset_link)

def toggle_pack_images(state, debug=False):
    if state == 'PACKED':
        bpy.ops.machin3.pack_decal_textures()

    elif state == 'UNPACKED':
        bpy.ops.machin3.unpack_decal_textures('INVOKE_DEFAULT')

def toggle_surface_snapping(state):
    if state:
        setup_surface_snapping(bpy.context.scene)
