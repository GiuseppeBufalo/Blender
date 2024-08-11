import bpy
import os
from . system import makedir
from . mesh import reset_material_indices
from . pil import scale_image
from . modifier import add_solidify, add_triangulate
from . material import get_decalmats, get_parallaxgroup_from_decalmat, get_material_output, get_decal_texture_nodes, append_material, get_pbrnode_from_mat
from . material import get_mix_node_input
from .. items import export_baketype_decaltype_mapping_dict

def create_bakebasepath(bakespath, blendname):
    if blendname:
        counter = 0
        folderpath = os.path.join(bakespath, blendname)

        while os.path.exists(folderpath):
            counter += 1
            folderpath = os.path.join(bakespath, "%s_%s" % (blendname, str(counter).zfill(3)))

    else:
        counter = 1
        folderpath = os.path.join(bakespath, '001')

        while os.path.exists(folderpath):
            counter += 1
            folderpath = os.path.join(bakespath, str(counter).zfill(3))

    return makedir(folderpath)

def set_bakepath(bakeimg, bakebasepath, name, baketype):
    bakepath = os.path.join(bakebasepath, "%s_%s.png" % (name, baketype.lower()))

    bakeimg.filepath = bakepath
    return bakepath

def prepare_active(context, scene, target, width, height, triangulate):
    if triangulate:
        if not any([mod.type == 'TRIANGULATE' for mod in target.modifiers]):
            add_triangulate(target)

    active = target.copy()
    active.data = target.data.copy()

    active.data.materials.clear()
    reset_material_indices(active.data)

    scene.collection.objects.link(active)

    if context.space_data.local_view:
        active.local_view_set(context.space_data, True)

    active.select_set(True)
    context.view_layer.objects.active = active

    add_solidify(active, thickness=0.00001)

    img = bpy.data.images.new('BakeImage', width=width, height=height)
    img.file_format = 'PNG'
    img.colorspace_settings.name = 'Non-Color'

    mat = bpy.data.materials.new(name='BakeMat')
    mat.use_nodes = True

    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.select = True
    mat.node_tree.nodes.active = node
    node.image = img

    active.data.materials.append(mat)

    return active, img, mat

def prepare_decals(context, view_layer, bakescene, target, baketype, debug=False):
    all_decals = [obj for obj in target.children if obj.DM.isdecal and not obj.DM.isbackup and obj.name in view_layer.objects and obj.visible_get(view_layer=view_layer)]

    decals = []

    for decal in all_decals:
        decalmats = get_decalmats(decal)

        if decalmats and any([mat.DM.decaltype in export_baketype_decaltype_mapping_dict[baketype] for mat in decalmats]):
            bakescene.collection.objects.link(decal)
            decal.select_set(True)

            mats = []

            for mat in decalmats:

                if mat.DM.decaltype in export_baketype_decaltype_mapping_dict[baketype]:

                    pg = get_parallaxgroup_from_decalmat(mat)

                    if pg and not pg.mute:
                        pg.mute = True
                        mats.append((mat, pg))

                    else:
                        mats.append((mat, None))

            decals.append((decal, mats))

    if context.space_data.local_view:
        for obj, _ in decals:
            obj.local_view_set(context.space_data, True)

    if debug:
        for decal, _ in decals:
            print(" • %s" % (decal.name))

    return decals

def setup_baking(bakescene, baketype, margin=3, to_active=True, ray_distance=0, extrusion_distance=0):
    if baketype == 'NORMAL':
        bakescene.cycles.bake_type = 'NORMAL'
        bakescene.render.bake.normal_b = 'NEG_Z'
    elif baketype == 'EMIT':
        bakescene.cycles.bake_type = 'EMIT'

    bakescene.render.bake.margin = margin
    bakescene.render.bake.use_selected_to_active = to_active
    bakescene.render.bake.cage_extrusion = ray_distance
    bakescene.render.bake.cage_extrusion = extrusion_distance

def bake_target_mask(bakescene, bakebasepath, targetname, bakename, bakeimg, bakemat, margin=3, ray_distance=0, extrusion_distance=0):
    setup_baking(bakescene, 'EMIT', margin=margin, to_active=False, ray_distance=ray_distance, extrusion_distance=extrusion_distance)
    bakepath = set_bakepath(bakeimg, bakebasepath, targetname, bakename)

    print("Info: Baking %s's %s: %s" % (targetname, bakename, bakepath))

    tree = bakemat.node_tree

    output = get_material_output(bakemat)
    emit = tree.nodes.new('ShaderNodeEmission')
    tree.links.new(emit.outputs[0], output.inputs[0])

    bpy.ops.object.bake(type='EMIT')
    bakeimg.save()
    bakeimg.source = 'GENERATED'

    tree.nodes.remove(emit)

    return bakepath

def bake_decals_margin_mask(bakescene, bakebasepath, targetname, bakename, bakeimg, decals, margin=3, ray_distance=0, extrusion_distance=0):
    setup_baking(bakescene, 'EMIT', margin=margin, ray_distance=ray_distance, extrusion_distance=extrusion_distance)
    bakepath = set_bakepath(bakeimg, bakebasepath, "%s_%s_%s" % (targetname, bakename, 'margin_%s' % (margin)), 'mask')

    print("Info: Baking %s's %s decals mask, with margin %d: %s" % (targetname, bakename, margin, bakepath))

    decalmats = {mat for _, decalmats in decals for mat, _ in decalmats}

    trees = []

    for mat in decalmats:
        tree = mat.node_tree

        texture_nodes = get_decal_texture_nodes(mat)
        masks = texture_nodes.get('MASKS')

        output = get_material_output(mat)
        lastnode_socket = output.inputs[0].links[0].from_socket

        emit = tree.nodes.new('ShaderNodeEmission')
        sep = tree.nodes.new('ShaderNodeSeparateRGB')

        tree.links.new(emit.outputs[0], output.inputs[0])
        tree.links.new(masks.outputs[0], sep.inputs[0])
        tree.links.new(sep.outputs[0], emit.inputs[0])

        trees.append((tree, lastnode_socket, output.inputs[0], emit, sep))

    bpy.ops.object.bake(type='EMIT')
    bakeimg.save()
    bakeimg.source = 'GENERATED'

    for tree, socket_out, socket_in, emit, sep in trees:
        tree.nodes.remove(emit)
        tree.nodes.remove(sep)
        tree.links.new(socket_out, socket_in)

    return bakepath

def bake(bakescene, bakebasepath, decals, targetname, baketype, bakeimg, margin=3, ray_distance=0, extrusion_distance=0):
    if baketype in ['NORMAL']:
        setup_baking(bakescene, baketype, margin=margin, ray_distance=ray_distance, extrusion_distance=extrusion_distance)

    elif baketype in ['COLOR']:
        bakeimg.colorspace_settings.name = 'sRGB'

        setup_baking(bakescene, 'EMIT', margin=margin, ray_distance=ray_distance, extrusion_distance=extrusion_distance)

        decalmats = {mat for _, decalmats in decals for mat, _ in decalmats}

        trees = []

        for mat in decalmats:
            tree = mat.node_tree

            texture_nodes = get_decal_texture_nodes(mat)
            color = texture_nodes.get('COLOR')

            output = get_material_output(mat)
            lastnode_socket = output.inputs[0].links[0].from_socket

            emit = tree.nodes.new('ShaderNodeEmission')

            tree.links.new(emit.outputs[0], output.inputs[0])
            tree.links.new(color.outputs[0], emit.inputs[0])

            trees.append((tree, lastnode_socket, output.inputs[0], emit))

    elif baketype in ['EMISSION_NORMAL']:
        bakeimg.colorspace_settings.name = 'sRGB'

        setup_baking(bakescene, 'EMIT', margin=margin, ray_distance=ray_distance, extrusion_distance=extrusion_distance)

    elif baketype in ['AO_CURV_HEIGHT']:
        setup_baking(bakescene, 'EMIT', margin=margin, ray_distance=ray_distance, extrusion_distance=extrusion_distance)

        decalmats = {mat for _, decalmats in decals for mat, _ in decalmats}

        trees = []

        for mat in decalmats:
            tree = mat.node_tree

            texture_nodes = get_decal_texture_nodes(mat)
            aocurvheight = texture_nodes.get('AO_CURV_HEIGHT')

            output = get_material_output(mat)
            lastnode_socket = output.inputs[0].links[0].from_socket

            emit = tree.nodes.new('ShaderNodeEmission')

            tree.links.new(emit.outputs[0], output.inputs[0])
            tree.links.new(aocurvheight.outputs[0], emit.inputs[0])

            trees.append((tree, lastnode_socket, output.inputs[0], emit))

    elif baketype in ['SUBSET']:
        setup_baking(bakescene, 'EMIT', margin=margin, ray_distance=ray_distance, extrusion_distance=extrusion_distance)

        decalmats = {mat for _, decalmats in decals for mat, _ in decalmats}

        trees = []

        for mat in decalmats:
            tree = mat.node_tree

            texture_nodes = get_decal_texture_nodes(mat)
            masks = texture_nodes.get('MASKS')

            output = get_material_output(mat)
            lastnode_socket = output.inputs[0].links[0].from_socket

            emit = tree.nodes.new('ShaderNodeEmission')
            sep = tree.nodes.new('ShaderNodeSeparateRGB')

            tree.links.new(emit.outputs[0], output.inputs[0])
            tree.links.new(sep.outputs[1], emit.inputs[0])
            tree.links.new(masks.outputs[0], sep.inputs[0])

            trees.append((tree, lastnode_socket, output.inputs[0], emit, sep))

    path = set_bakepath(bakeimg, bakebasepath, targetname, baketype)
    print("Info: Baking %s's %s map: %s" % (targetname, baketype.lower(), path))

    if baketype == 'NORMAL':
        bpy.ops.object.bake(type=baketype)
    elif baketype in ['COLOR', 'AO_CURV_HEIGHT', 'SUBSET', 'EMISSION_NORMAL', 'EMISSION_COLOR']:
        bpy.ops.object.bake(type='EMIT')

    bakeimg.save()
    bakeimg.source = 'GENERATED'
    bakeimg.colorspace_settings.name = 'Non-Color'

    if baketype in ['COLOR', 'AO_CURV_HEIGHT']:
        for tree, socket_out, socket_in, emit in trees:
            tree.nodes.remove(emit)
            tree.links.new(socket_out, socket_in)

    elif baketype == 'SUBSET':
        for tree, socket_out, socket_in, emit, sep in trees:
            tree.nodes.remove(emit)
            tree.nodes.remove(sep)
            tree.links.new(socket_out, socket_in)

    return path

def resample(bakes, factor):
    for target, baketypedict in bakes.items():
        for baketype, path in baketypedict.items():
            if baketype == 'MASKS':
                for p in path:
                    print("Info: Resampling bake: %s" % (p))
                    scale_image(p, scale=factor)

            else:
                print("Info: Resampling bake: %s" % (path))
                scale_image(path, scale=factor)

    print()

def apply_substance_naming(bakes):
    for target, baketypedict in bakes.items():
        for baketype, path in baketypedict.items():

            if baketype == 'NORMAL':
                newpath = path.replace('_normal.png', '_normal_base.png')
                os.rename(path, newpath)
                bakes[target][baketype] = newpath

            elif baketype == 'AO':
                newpath = path.replace('_ao.png', '_ambient_occlusion.png')
                os.rename(path, newpath)
                bakes[target][baketype] = newpath

            elif baketype == 'CURV':
                newpath = path.replace('_curv.png', '_curvature.png')
                os.rename(path, newpath)
                bakes[target][baketype] = newpath

            elif baketype == 'SUBSET':
                newpath = path.replace('_subset.png', '_id.png')
                os.rename(path, newpath)
                bakes[target][baketype] = newpath

            elif baketype == 'MASKS':
                newpaths = []

                for p in path:
                    if '_color_mask.png' in p:
                        newpath = p.replace('_color_mask.png', '_color_opacity.png')
                        newpaths.append(newpath)

                        os.rename(p, newpath)
                    else:
                        newpaths.append(p)

                bakes[target][baketype] = newpaths

def preview(templatepath, bakes, combine_bakes):
    def match_pbr_nodes(mat, original_pbrnode, preview_pbrnode):
        for i, pi in zip(original_pbrnode.inputs, preview_pbrnode.inputs):
            pi.default_value = i.default_value
            if pi.name == 'Base Color':
                mixnode = mat.node_tree.nodes.get('Mix.COLOR')

                i = get_mix_node_input(mixnode, inpt='A')

                i.default_value = pi.default_value
                mixnode = mat.node_tree.nodes.get('Mix.AO')

                i = get_mix_node_input(mixnode, inpt='A')

                i.default_value = pi.default_value
            elif pi.name == 'Roughness':
                valuenode = mat.node_tree.nodes.get('Roughness Value')
                valuenode.outputs[0].default_value = pi.default_value
    def set_textures(mat, bakes):
        for baketype, img in bakes.items():
            imgnode = mat.node_tree.nodes.get("BAKE_PREVIEW_%s" % (baketype.lower()))
            imgnode.image = img
            imgnode.mute = False

            if baketype == 'COLOR':
                mat.node_tree.nodes.get('Mix.COLOR').mute = False
                mat.node_tree.nodes.get('Mix.COLOR.2').mute = False

            elif baketype == 'AO':
                mat.node_tree.nodes.get('Mix.AO').mute = False
                mat.node_tree.nodes.get('Mix.AO.2').mute = False

                mat.node_tree.nodes.get('Mix.ROUGHNESS').mute = False
                mat.node_tree.nodes.get('Mix.AO').mute = False

                mat.node_tree.nodes.get('Mix.ROUGHNESS.2').mute = False

            elif baketype == 'SUBSET':
                mat.node_tree.nodes.get('Mix Shader').mute = False

            elif baketype == 'EMISSION':
                mat.node_tree.nodes.get('Mix.EMISSION').mute = False

    preview_mat = append_material(templatepath, 'BAKE_PREVIEW')

    if preview_mat:

        preview_maps = {}

        for target, baketypedict in bakes.items():

            if target == 'COMBINED':
                continue

            preview_maps[target] = {}

            for baketype, path in baketypedict.items():

                if baketype in ['COLOR', 'NORMAL', 'AO', 'SUBSET', 'EMISSION']:
                    preview_maps[target][baketype] = bakes['COMBINED'][baketype] if combine_bakes else path

        for target, baketypedict in preview_maps.items():

            decals = [obj for obj in target.children if obj.DM.isdecal and not obj.DM.isbackup]

            for decal in decals:
                decal.hide_set(True)

            baked = {}

            for baketype, path in baketypedict.items():
                img = bpy.data.images.load(path)

                if baketype not in ['COLOR', 'EMISSION']:
                    img.colorspace_settings.name = 'Non-Color'

                baked[baketype] = img

            if target.material_slots:

                for idx, slot in enumerate(target.material_slots):
                    col = target.DM.prebakepreviewmats.add()
                    col.index = idx

                    if slot.material:
                        col.name = slot.material.name
                        col.material = slot.material

                        if slot.material.use_nodes and get_pbrnode_from_mat(slot.material):

                            original_pbrnode = get_pbrnode_from_mat(slot.material)

                            preview_material = preview_mat.copy()
                            preview_pbrnode = preview_material.node_tree.nodes.get('Principled BSDF')

                            slot.material = preview_material

                            match_pbr_nodes(slot.material, original_pbrnode, preview_pbrnode)

                            set_textures(slot.material, baked)

                        else:
                            slot.material = preview_mat.copy()
                            set_textures(slot.material, baked)

                    else:
                        slot.material = preview_mat.copy()
                        set_textures(slot.material, baked)

            else:
                col = target.DM.prebakepreviewmats.add()
                col.name = 'NO_SLOTS'

                preview_material = preview_mat.copy()

                target.data.materials.append(preview_material)
                set_textures(preview_material, baked)

        bpy.data.materials.remove(preview_mat, do_unlink=True)
