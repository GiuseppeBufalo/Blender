import bpy
import bmesh
import os
from mathutils import Vector, Matrix
from . modifier import add_displace, add_nrmtransfer, get_displace
from . append import append_material, append_scene
from . material import get_decal_textures, get_decalgroup_from_decalmat, get_parallaxgroup_from_decalmat, get_heightgroup_from_parallaxgroup, get_decal_texture_nodes, get_pbrnode_from_mat, remove_decalmat, set_subset_component_from_matname
from . pil import scale_image, change_contrast, crop_image, create_material2_mask, check_image_for_nonblack_pixels
from . registration import get_prefs, get_path, get_templates_path, get_version_from_blender
from . system import open_folder
from . mesh import loop_index_update, init_uvs
from . object import update_local_view
from . math import create_bbox, get_midpoint
from . property import set_cycles_visibility
from .. import bl_info



def get_decal_source_objects(context, dg, scene, sel, active=None, clear_mats=False, debug=False):
    source_objs = []
    all_coords = []
    new_active = None

    for obj in sel:
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
        source = bpy.data.objects.new(name=obj.name, object_data=mesh)
        source.matrix_world = obj.matrix_world

        if clear_mats:
            source.data.materials.clear()

        scene.collection.objects.link(source)

        source.hide_render = False
        source.hide_viewport = False
        source.hide_select = False

        source.select_set(True)

        if obj == active:
            new_active = source

        source_objs.append(source)
        all_coords += [source.matrix_world @ v.co for v in source.data.vertices]

    update_local_view(context.space_data, [(obj, True) for obj in source_objs])

    coords, _, _ = create_bbox(coords=all_coords)

    if debug:
        for co in coords:
            empty = bpy.data.objects.new("empty", None)
            scene.collection.objects.link(empty)
            empty.location = co

    return source_objs, coords, new_active


def create_decal_geometry(context, scene, coords, height):
    decal = bpy.data.objects.new("Decal", object_data=bpy.data.meshes.new(name="Decal"))
    scene.collection.objects.link(decal)

    location = get_midpoint(coords[4:])

    decal.location = location

    context.view_layer.objects.active = decal
    decal.select_set(True)

    bpy.ops.transform.translate(value=(0, 0, 0))

    bm = bmesh.new()
    bm.from_mesh(decal.data)

    uvs = bm.loops.layers.uv.verify()

    verts = []

    for co in coords[4:]:
        v = bm.verts.new()
        v.co = decal.matrix_world.inverted_safe() @ Vector(co)
        verts.append(v)

    face = bm.faces.new(verts)

    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    loop_index_update(bm)

    for loop in face.loops:
        if loop.index == 0:
            loop[uvs].uv = (0, 0)
        elif loop.index == 1:
            loop[uvs].uv = (1, 0)
        elif loop.index == 2:
            loop[uvs].uv = (1, 1)
        elif loop.index == 3:
            loop[uvs].uv = (0, 1)


    bm.to_mesh(decal.data)

    decal.matrix_world.translation.z += height * 0.01

    return decal, location


def create_info_decal_textures(context, dm, templatepath, bakepath, scene, decal, source_objs, bbox_coords, width, depth, padding):
    def bake(context, path, scene, decal, size, bake_size, bake, bakename="", colorspace="sRGB", samples=1, pass_filter=set()):
        image_width, image_height = bake_size

        scene.cycles.samples = samples

        image = bpy.data.images.new("BakeImage", width=image_width, height=image_height)
        image.file_format = 'PNG'
        image.colorspace_settings.name = colorspace

        mat = bpy.data.materials.new(name="BakeMat")
        mat.use_nodes = True

        decal.data.materials.append(mat)

        node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.select = True
        mat.node_tree.nodes.active = node
        node.image = image

        if not bakename:
            bakename = bake.lower()

        bakepath = os.path.join(path, bakename + ".png")
        image.filepath = bakepath

        print(" • Baking decal %s map." % (bakename))

        bpy.ops.object.bake(type=bake, pass_filter=pass_filter, use_clear=True, use_selected_to_active=True, margin=0, normal_space='TANGENT')
        image.save()

        bpy.data.materials.remove(mat, do_unlink=True)
        decal.data.materials.clear()

        bpy.data.images.remove(image, do_unlink=True)

        if size != bake_size:
            print("    scaling from", bake_size, "to", size)
            scale_image(bakepath, size=size)

        return bakepath

    supersample = int(dm.create_bake_supersample)
    resolution = int(dm.create_bake_resolution)

    emissive = dm.create_bake_emissive

    inspect = dm.create_bake_inspect

    ratio = width / depth
    size = (resolution, round(resolution / ratio)) if ratio >= 1 else (round(resolution * ratio), resolution)

    bake_size = tuple([s * supersample for s in size]) if supersample else size

    if padding != (0, 0):
        scalex = 1 + width / bake_size[0] * padding[0]
        scaley = 1 + depth / bake_size[1] * padding[1]

        bm = bmesh.new()
        bm.from_mesh(decal.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        bmesh.ops.scale(bm, vec=(scalex, scaley, 1), verts=bm.verts)

        bm.to_mesh(decal.data)
        bm.clear()

        bake_size = (round(bake_size[0] * scalex), round(bake_size[1] * scaley))

    textures = []

    for obj in source_objs:
        obj.select_set(True)



    textures.append(bake(context, bakepath, scene, decal, size, bake_size, 'DIFFUSE', colorspace="sRGB", pass_filter={'COLOR'}))



    if emissive:
        textures.append(bake(context, bakepath, scene, decal, size, bake_size, 'EMIT', 'emission'))



    for obj in source_objs:
        obj.data.materials.clear()

    alphamat = append_material(templatepath, "EMISSIVE")
    mattemat = append_material(templatepath, "MATTE")

    for obj in source_objs:
        obj.data.materials.append(alphamat)
        obj.data.materials.append(mattemat)

    textures.append(bake(context, bakepath, scene, decal, size, bake_size, "EMIT", "alpha"))

    bpy.data.materials.remove(alphamat, do_unlink=True)
    bpy.data.materials.remove(mattemat, do_unlink=True)

    for obj in source_objs:
        bpy.data.meshes.remove(obj.data, do_unlink=True)

    bpy.data.worlds.remove(scene.world, do_unlink=True)
    bpy.data.scenes.remove(scene, do_unlink=True)


    if inspect:
        open_folder(bakepath)


    return textures, size


def create_decal_textures(context, dm, templatepath, bakepath, scene, decal, active, source_objs, bbox_coords, width, depth):
    def flatten_alpha_normals(active, boundary):
        active.data.calc_normals_split()

        loop_normals = []
        for loop in active.data.loops:
            loop_normals.append(loop.normal.normalized())

        bm = bmesh.new()
        bm.from_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        if not all([f.smooth for f in bm.faces]):
            print(f"WARNING: Skipping surface-face normal flattening, as {active.name} is not completely smooth shaded")
            return

        active.data.use_auto_smooth = True

        for e in bm.edges:
            if e.calc_face_angle(0) > active.data.auto_smooth_angle:
                e.smooth = False

        verts = []

        for f in bm.faces:
            dot = round((active.matrix_world.to_3x3() @ f.normal).normalized().dot(Vector((0.0, 0.0, 1.0))), 6)

            if dot == 1:
                if all([round(v.co[2], 6) == 0 for v in f.verts]):
                    if all([e.smooth for e in f.edges]):
                        if boundary:
                            if any([not e.is_manifold for e in f.edges]):
                                verts.extend(f.verts)
                        else:
                            verts.extend(f.verts)

        for v in verts:
            for loop in v.link_loops:
                loop_normals[loop.index] = Vector((0, 0, 1))

        bm.to_mesh(active.data)
        bm.clear()

        active.data.normals_split_custom_set(loop_normals)

    def create_panel_dups(scene, active, source_objs, width):
        dups = []

        for obj in source_objs:
            dup = obj.copy()
            dup.data = obj.data.copy()
            dup.matrix_world.translation.x += width
            scene.collection.objects.link(dup)
            dup.select_set(True)
            dups.append(dup)

            dup = obj.copy()
            dup.data = obj.data.copy()
            dup.matrix_world.translation.x -= width
            scene.collection.objects.link(dup)
            dup.select_set(True)
            dups.append(dup)

        return dups

    def bake(context, path, scene, decal, size, bake_size, bake, bakename="", colorspace="Non-Color", samples=1, use_float=False, contrast=1, pass_filter=set(), passimage=False):
        image_width, image_height = bake_size

        scene.cycles.samples = samples

        image = bpy.data.images.new("BakeImage", width=image_width, height=image_height)
        image.file_format = 'PNG'
        image.colorspace_settings.name = colorspace

        image.use_generated_float = use_float
        scene.render.image_settings.color_depth = '16' if use_float else '8'


        mat = bpy.data.materials.new(name="BakeMat")
        mat.use_nodes = True

        decal.data.materials.append(mat)

        node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.select = True
        mat.node_tree.nodes.active = node
        node.image = image

        if not bakename:
            bakename = bake.lower()

        print("INFO: Baking decal %s map." % (bakename), bake_size)

        bakepath = os.path.join(path, bakename + ".png")
        image.filepath = bakepath

        bpy.ops.object.bake(type=bake, pass_filter=pass_filter, use_clear=True, use_selected_to_active=True, margin=0, normal_space='TANGENT')

        bpy.data.materials.remove(mat, do_unlink=True)
        decal.data.materials.clear()

        if passimage:
            return image

        else:
            if size != bake_size and use_float:
                image.scale(*size)

            image.save_render(bakepath, scene=scene) if use_float else image.save()

            if contrast != 1:
                change_contrast(bakepath, contrast)

            if size != bake_size and not use_float:
                scale_image(bakepath, size=size)

            bpy.data.images.remove(image, do_unlink=True)

            return bakepath

    def prepare_height_bake(templatepath, source_objs, active, coords, distance, debug=False):
        heightmat = append_material(templatepath, "POSITIONHEIGHT")

        for obj in source_objs:
            obj.data.materials.append(heightmat)

        active_z = active.matrix_world.translation.z
        min_z = coords[0][2]
        max_z = coords[4][2]

        distance_bottom = active_z - min_z
        distance_top = max_z - active_z

        distance_max = max([distance_bottom, distance_top])

        if distance and distance > distance_max:
            distance_max = distance

        if debug:
            print("active z:", active_z)
            print("min z:", min_z)
            print("max z:", max_z)
            print("distance bottom:", distance_bottom)
            print("distance top:", distance_top)
            print("distance max:", distance_max)

        node_scale = heightmat.node_tree.nodes.get("Scale")
        node_offset = heightmat.node_tree.nodes.get("Offset")

        if node_scale and node_offset:
            node_scale.inputs[1].default_value = 2 * distance_max
            node_offset.inputs[1].default_value = - active_z / 2 * distance_max

        return heightmat

    def create_curvature_map(context, path, scene, decal, size, bake_size, curvaturewidth, panel, contrast=1):
        normal = bake(context, path, scene, decal, size, (bake_size[0] * 3, bake_size[1]) if panel else bake_size, 'NORMAL', bakename='curvature', colorspace="Linear", passimage=True)

        node_normal = context.scene.node_tree.nodes.get("Normal Map")
        node_normal.image = normal

        node_nrm2curv = context.scene.node_tree.nodes.get("Normal2Curvature")
        node_nrm2curv.inputs[1].default_value = curvaturewidth

        scene.render.resolution_x = normal.size[0]
        scene.render.resolution_y = normal.size[1]

        curvaturepath = os.path.join(path, "curvature.png")
        scene.render.filepath = curvaturepath

        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'BW'

        bpy.ops.render.render(write_still=True)

        if panel:
            crop_image(imagepath=scene.render.filepath, cropbox=(bake_size[0], 0, 2 * bake_size[0], scene.render.resolution_y))

        if contrast != 1:
            change_contrast(curvaturepath, contrast)

        if size != bake_size:
            scale_image(scene.render.filepath, size=size)

        bpy.data.images.remove(normal, do_unlink=True)

        bpy.data.node_groups.remove(node_nrm2curv.node_tree, do_unlink=True)

        return curvaturepath

    def prepare_alpha_bake(templatepath, source_objs, active, boundary):
        alphamat = append_material(templatepath, "EMISSIVE")
        mattemat = append_material(templatepath, "MATTE")

        for obj in source_objs:
            obj.data.materials.append(alphamat)
            obj.data.materials.append(mattemat)

        if active:
            source_objs = [active]

        for obj in source_objs:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            for f in bm.faces:
                f.material_index = 0
                dot = round((obj.matrix_world.to_3x3() @ f.normal).normalized().dot(Vector((0.0, 0.0, 1.0))), 6)

                if dot == 1:
                    if all([round(v.co[2], 6) == 0 for v in f.verts]):
                        if boundary:
                            if any([not e.is_manifold for e in f.edges]):
                                f.material_index = 1
                        else:
                            f.material_index = 1


            bm.to_mesh(obj.data)
            bm.clear()

        return alphamat, mattemat

    def create_material2_map(path, context, size, bake_size, scene, decal, active, source_objs, alphamat, mattemat):
        active.data.materials.clear()
        active.data.materials.append(alphamat)
        active.data.materials.append(mattemat)

        subsets = [obj for obj in source_objs if obj != active]

        for obj in subsets:
            obj.hide_viewport = True

        bm = bmesh.new()
        bm.from_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        seamedges = [e for e in bm.edges if e.seam]

        if seamedges:
            for f in bm.faces:
                f.select = False

            northvert = sorted([v for v in bm.verts], key=lambda x: (active.matrix_world @ x.co).y, reverse=True)[0]

            face = northvert.link_faces[0]
            faces = []
            check = [face]

            while check:
                face = check[0]
                faces.append(face)

                new_faces = [face for e in face.edges if not e.seam for face in e.link_faces if face not in check and face not in faces]

                check += new_faces
                check.remove(face)


            for f in bm.faces:
                if f in faces:
                    f.material_index = 0
                else:
                    f.material_index = 1

            bm.to_mesh(active.data)
            bm.clear()

            mat2path = bake(context, path, scene, decal, size, bake_size, "EMIT", "material2", samples=1)

            for obj in subsets:
                obj.hide_viewport = False

        else:
            print("INFO: Creating decal material2 map.", size)
            mat2path = os.path.join(path, "material2.png")
            create_material2_mask(mat2path, *size)

        return mat2path

    supersample = int(dm.create_bake_supersample)
    supersamplealpha = dm.create_bake_supersamplealpha
    resolution = int(dm.create_bake_resolution)

    aosamples = int(dm.create_bake_aosamples)
    aocontrast = dm.create_bake_aocontrast

    curvaturewidth = dm.create_bake_curvaturewidth * supersample if supersample else dm.create_bake_curvaturewidth
    curvaturecontrast = dm.create_bake_curvaturecontrast

    heightdistance = dm.create_bake_heightdistance

    emissive = dm.create_bake_emissive
    emissive_bounce = dm.create_bake_emissive_bounce

    limit_alpha_to_active = dm.create_bake_limit_alpha_to_active
    limit_alpha_to_boundary = dm.create_bake_limit_alpha_to_boundary
    flatten_normals = dm.create_bake_flatten_alpha_normals
    inspect = dm.create_bake_inspect
    panel = dm.create_decaltype == "PANEL"
    maskmat2 = dm.create_bake_maskmat2

    ratio = width / depth
    size = (resolution, round(resolution / ratio)) if ratio >= 1 else (round(resolution * ratio), resolution)

    bake_size = tuple([s * supersample for s in size]) if supersample else size

    textures = []

    for obj in source_objs:
        obj.select_set(True)

    if flatten_normals:
        flatten_alpha_normals(active, boundary=limit_alpha_to_boundary)

    if panel:
        paneldups = create_panel_dups(scene, active, source_objs, width)



    textures.append(bake(context, bakepath, scene, decal, size, bake_size, 'AO', colorspace="sRGB", samples=aosamples, contrast=aocontrast))



    textures.append(bake(context, bakepath, scene, decal, size, bake_size, 'NORMAL', use_float=get_prefs().use_decal_float_normals))




    if emissive:
        textures.append(bake(context, bakepath, scene, decal, size, bake_size, 'EMIT', 'emission'))

        if emissive_bounce:
            emissionsamples = int(dm.create_bake_emissionsamples)
            textures.append(bake(context, bakepath, scene, decal, size, bake_size, 'DIFFUSE', 'emission_bounce', samples=emissionsamples, pass_filter={'INDIRECT'}))

        for obj in source_objs:
            obj.data.materials.clear()



    heightmat = prepare_height_bake(templatepath, source_objs, active, bbox_coords, heightdistance, debug=False)

    textures.append(bake(context, bakepath, scene, decal, size, bake_size, "EMIT", "height"))

    for obj in source_objs:
        obj.data.materials.clear()

    bpy.data.materials.remove(heightmat, do_unlink=True)


    if panel:
        decal.scale.x = 3

    textures.append(create_curvature_map(context, bakepath, scene, decal, size, bake_size, curvaturewidth, panel, contrast=curvaturecontrast))

    if panel:
        decal.scale.x = 1

        for obj in paneldups:
            bpy.data.meshes.remove(obj.data, do_unlink=True)



    alphamat, mattemat = prepare_alpha_bake(templatepath, source_objs, active=active if limit_alpha_to_active else False, boundary=limit_alpha_to_boundary)

    textures.append(bake(context, bakepath, scene, decal, size, bake_size if supersamplealpha else size, "EMIT", "alpha"))



    if len(source_objs) > 1:
        active.data.materials.pop(index=0)

        textures.append(bake(context, bakepath, scene, decal, size, bake_size, "EMIT", "subset"))



    if panel and maskmat2:
        textures.append(create_material2_map(bakepath, context, size, bake_size, scene, decal, active, source_objs, alphamat, mattemat))

    bpy.data.materials.remove(alphamat, do_unlink=True)
    bpy.data.materials.remove(mattemat, do_unlink=True)

    for obj in source_objs:
        bpy.data.meshes.remove(obj.data, do_unlink=True)

    bpy.data.worlds.remove(scene.world, do_unlink=True)
    bpy.data.scenes.remove(scene, do_unlink=True)


    if inspect:
        open_folder(bakepath)

    return textures, size


def create_decal_blend(context, templatepath, decalpath, packed, decaltype, decalobj=None, size=None, uuid='', decalnamefromfile='', set_emission=False, set_subset=False):
    bpy.ops.scene.new(type='NEW')
    decalscene = context.scene
    decalscene.name = "Decal Asset"

    if decalobj:
        decalscene.collection.objects.link(decalobj)

        factor = size[0] / decalobj.dimensions[0] / 1000

        bm = bmesh.new()
        bm.from_mesh(decalobj.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        bmesh.ops.scale(bm, vec=(factor, factor, factor), verts=bm.verts)

        bm.to_mesh(decalobj.data)
        bm.clear()

        decalobj.location = (0, 0, 0)

    else:
        bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0), rotation=(0, 0, 0))

        decalobj = context.active_object
        size = packed['SIZE']

        bm = bmesh.new()
        bm.from_mesh(decalobj.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        bmesh.ops.scale(bm, vec=(size[0] / 2000, size[1] / 2000, 1), verts=bm.verts)

        bm.to_mesh(decalobj.data)
        bm.clear()

        init_uvs(decalobj.data)


    decalobj.DM.isdecal = True

    add_displace(decalobj)

    add_nrmtransfer(decalobj)


    library = "LIBRARY"
    basename = "DECAL"

    decalmatname = "%s_%s" % (library, basename)
    decalname = decalmatname

    version = get_version_from_blender()


    decalmat = append_material(templatepath, "TEMPLATE_%s" % decaltype.upper())

    if decalmat:
        decalobj.data.materials.append(decalmat)

        decalmatname = "%s_%s" % (library, basename)
        decalname = decalmatname

        decalobj.name = decalname
        decalobj.data.name = decalname
        decalmat.name = decalmatname

        if decalnamefromfile:
            decalmat.DM.decalnamefromfile = decalnamefromfile

        textures = get_decal_textures(decalmat)

        for component in [decalobj] + [decalmat] + list(textures.values()):
            component.DM.uuid = uuid
            component.DM.version = version
            component.DM.decaltype = decaltype
            component.DM.decallibrary = library
            component.DM.decalname = decalname
            component.DM.decalmatname = decalmatname
            component.DM.creator = get_prefs().decalcreator

        decalgroup = get_decalgroup_from_decalmat(decalmat)
        decalgroup.name = "%s.%s" % (decaltype.lower(), decalmatname)

        parallaxgroup = get_parallaxgroup_from_decalmat(decalmat)

        if parallaxgroup:
            parallaxgroup.name = "parallax.%s" % (decalmatname)
            parallaxgroup.node_tree.name = "parallax.%s" % (decalmatname)
            decalmat.DM.parallaxnodename = "parallax.%s" % (decalmatname)

            heightgroups = get_heightgroup_from_parallaxgroup(parallaxgroup, getall=True)

            if heightgroups:
                for idx, hg in enumerate(heightgroups):
                    if idx == 0:
                        hg.node_tree.name = "height.%s" % (decalmatname)

                    hg.name = "height.%s" % (decalmatname)

        else:
            decalmat.DM.parallaxnodename = ""


        imgnodes = get_decal_texture_nodes(decalmat, height=True)

        for textype, node in imgnodes.items():
            node.name = "%s_%s" % (decalmatname, textype.lower())

            if textype != "HEIGHT":
                node.image.name = ".%s_%s" % (decalmatname, textype.lower())
                node.image.filepath = packed[textype]

        emission = textures.get('EMISSION')

        if set_emission and emission:
            multiplier = decalgroup.inputs.get('Emission Multiplier')

            if check_image_for_nonblack_pixels(emission.filepath):
                multiplier.default_value = 10

            else:
                multiplier.default_value = 0

        if set_subset:
            set_subset_component_from_matname(decalmat, set_subset)

        save_uuid(decalpath, uuid)

        save_blend(decalobj, decalpath, decalscene)

    return decalobj, decalmat, size



def save_uuid(path, uuid, legacy=False):
    if legacy:
        path = os.path.join(os.path.splitext(path)[0] + ".uuid")

    else:
        path = os.path.join(path, "uuid")

    with open(path, "w") as f:
        f.write(uuid)


def save_blend(obj, path, scene):
    obj.parent = None

    set_cycles_visibility(obj, 'shadow', False)
    set_cycles_visibility(obj, 'diffuse', False)

    obj.matrix_world = Matrix.Identity(4)

    displace = get_displace(obj)
    if displace:
        displace.mid_level = 0.9999

    bpy.data.libraries.write(filepath=os.path.join(path, "decal.blend"), datablocks={scene}, path_remap='RELATIVE_ALL')

    bpy.data.scenes.remove(scene, do_unlink=True)


def render_thumbnail(context, decalpath, decal, decalmat, size=None, removeall=True):
    def set_emission_indicator(name):

        textures = get_decal_textures(decalmat)
        emission = textures.get('EMISSION')
        dg = get_decalgroup_from_decalmat(decalmat)
        emission_input = dg.inputs.get('Emission')

        if dg and (name == 'INFO' or emission):

            info_emits = True if name == 'INFO' and emission_input and emission_input.default_value[:3] != (0, 0, 0) else False
            map_checks_out = True if emission and check_image_for_nonblack_pixels(emission.filepath) else False

            if info_emits or map_checks_out:
                indicator = bpy.data.objects.get('Indicator_%s_EMISSION' % name)

                if indicator:
                    indicator.hide_render = False

                    if not info_emits:
                        emission_amount = dg.inputs.get('Emission Multiplier').default_value

                        if emission_amount == 0:
                            pbr = get_pbrnode_from_mat(indicator.active_material)

                            pbr.inputs['Emission'].default_value = (0, 0, 0, 1)
                            pbr.inputs['Alpha'].default_value = 0.75

    templatepath = get_templates_path()

    thumbscene = append_scene(templatepath, "Thumbnail")
    context.window.scene = thumbscene

    thumbscene.collection.objects.link(decal)

    default_light_col = thumbscene.collection.children.get('DECAL_THUMB_LIGHTS_DEFAULT')
    info_light_col = thumbscene.collection.children.get('DECAL_THUMB_LIGHTS_INFO')

    context.view_layer.objects.active = decal
    decal.select_set(True)

    if size:
        res = max(size)
        width = (128 / res) * size[0] / 1000

    else:
        size = [int(d * 1000) for d in decal.dimensions[:2]]

        width = None

    factor = 1 / (max(s for s in size) / 128)

    bpy.ops.transform.resize(value=[factor] * 3)

    bpy.ops.transform.translate()

    paneldups = []

    if decalmat.DM.decaltype == "PANEL":
        if not width:
            width = decal.dimensions[0]

        for i in [-2, -1, 1, 2]:
            dup = decal.copy()
            dup.data = decal.data.copy()
            paneldups.append(dup)

            dup.matrix_world.translation.x += width * i
            thumbscene.collection.objects.link(dup)

    if decalmat.DM.decaltype == "INFO":
        thumbscene.camera = bpy.data.objects['Camera_INFO']

        default_light_col.hide_render = True
        info_light_col.hide_render = False

        set_emission_indicator('INFO')

    else:
        thumbscene.camera = bpy.data.objects['Camera_INFO'] if decalmat.DM.istrimdecalmat else bpy.data.objects['Camera_NORMAL']

        if decalmat.DM.istrimdecalmat and decalmat.DM.decaltype == 'PANEL':
            mxc = thumbscene.camera.matrix_world
            vec_z = Vector((0, 0, 1)) @ mxc.inverted_safe()
            thumbscene.camera.matrix_world = Matrix.Translation(-0.1 * vec_z) @ mxc

        default_light_col.hide_render = False
        info_light_col.hide_render = True

        set_emission_indicator('INFO' if decalmat.DM.istrimdecalmat else 'NORMAL')

        dg = get_decalgroup_from_decalmat(decalmat)

        if dg:
            matrough = dg.inputs.get('Material Roughness')
            mat2rough = dg.inputs.get('Material 2 Roughness')
            subrough = dg.inputs.get('Subset Roughness')

            if matrough:
                matrough.default_value = 0.325

            if mat2rough:
                mat2rough.default_value = 0.325

            if subrough:
                subrough.default_value = 0.325

        if decalmat.DM.decaltype == 'SUBSET':
            transmission = dg.inputs.get('Subset Transmission')

            if transmission.default_value > 0:
                print("INFO: Enable SSR for transmissive Subset Rendering")

                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True

    thumbscene.render.filepath = os.path.join(decalpath, "decal.png")

    bpy.ops.render.render(write_still=True)

    for dup in paneldups:
        bpy.data.meshes.remove(dup.data, do_unlink=True)

    if removeall:
        bgmat = bpy.data.materials.get('THUMBNAILBG')
        if bgmat:
            bpy.data.materials.remove(bgmat, do_unlink=True)

        indicatormat = bpy.data.materials.get('INDICATOR_EMISSION')
        if indicatormat:
            bpy.data.materials.remove(indicatormat, do_unlink=True)

        remove_decalmat(decalmat, remove_textures=True)

        render_result = bpy.data.images.get('Render Result')

        if render_result:
            bpy.data.images.remove(render_result)

        for obj in thumbscene.objects:
            if obj.type == "MESH":
                bpy.data.meshes.remove(obj.data, do_unlink=True)

            elif obj.type == "CAMERA":
                bpy.data.cameras.remove(obj.data, do_unlink=True)

            elif obj.type == "LIGHT":
                bpy.data.lights.remove(obj.data, do_unlink=True)

        bpy.data.collections.remove(default_light_col, do_unlink=True)
        bpy.data.collections.remove(info_light_col, do_unlink=True)

    bpy.data.worlds.remove(thumbscene.world, do_unlink=True)

    context.evaluated_depsgraph_get()

    bpy.data.scenes.remove(thumbscene, do_unlink=True)
