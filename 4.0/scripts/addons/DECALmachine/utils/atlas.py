import bpy
import bmesh
import os
from json import dump, dumps
from mathutils import Vector
from shutil import copy
from . modifier import add_displace
from . math import trimmx_to_img_coords, img_coords_to_mesh_coords, img_coords_to_uv_coords, flatten_matrix, img_coords_to_trimmx
from . object import parent
from . registration import get_prefs
from . library import get_atlas
from . material import get_decal_textures, get_parallax_amount, set_atlasdummy_texture_paths, set_node_names_of_atlas_material, get_atlas_textures
from . pil import scale_image, create_dummy_texture
from . system import abspath, makedir
from . append import append_material
from .. items import atlastexturetype_items, create_atlastype_textype_mapping_dict, textype_color_mapping_dict



def prepare_source_textures(atlas_type, sourcespath, materials, sources={}, prepack='NONE', debug=False):

    print("INFO: Collecting sources for %s atlas" % (atlas_type))

    decal_types = ['SIMPLE', 'SUBSET', 'PANEL', 'INFO'] if atlas_type == 'COMBINED' else ['SIMPLE', 'SUBSET', 'PANEL'] if atlas_type == 'NORMAL' else ['INFO']
    mats = [mat for mat in materials.values() if mat.DM.decaltype in decal_types]

    if mats:
        for mat in sorted(mats, key=lambda m: m.DM.decalname):
            uuid = mat.DM.uuid
            textures = get_decal_textures(mat)

            print()
            print(mat.DM.decalname)

            if any([os.path.exists(abspath(img.filepath)) for img in textures.values()]):

                resolutions = [(tuple(img.size), textype) for textype, img in sorted(textures.items(), key=lambda x: x[0])]
                maxres = max([(width, height) for (width, height), _ in resolutions], key=lambda x: x[0])

                if uuid not in sources:
                    name = mat.DM.decalname
                    ispanel = mat.DM.decaltype == 'PANEL'

                    sources[uuid] = {'name': name,
                                     'size': maxres,
                                     'original_size': maxres,
                                     'ispanel': ispanel,
                                     'prepack': prepack if ispanel else 'NONE',
                                     'repetitions': 1,
                                     'parallax': 0.1,
                                     'height': 1,
                                     'textures': {},
                                     'original_textures': {}}

                for textype in create_atlastype_textype_mapping_dict[atlas_type]:

                    if textype in textures and os.path.exists(abspath(textures[textype].filepath)):
                        img = textures[textype]

                        sources[uuid]['original_textures'][textype] = abspath(img.filepath)

                        parallax = get_parallax_amount(mat)

                        if parallax != 0.1:
                            sources[uuid]['parallax'] = parallax

                        if tuple(img.size) == maxres:
                            print("INFO: using original %s map at: %s" % (textype, abspath(img.filepath)))
                            sources[uuid]['textures'][textype] = abspath(img.filepath)

                        else:
                            decalpath = makedir(os.path.join(sourcespath, uuid))
                            destination = os.path.join(decalpath, "%s.png" % (textype.lower()))

                            copy(abspath(img.filepath), destination)
                            sources[uuid]['textures'][textype] = destination

                            print("WARNING: scaling up %s map to %dx%d: %s" % (textype, *maxres, destination))
                            scale_image(destination, size=maxres)


                    else:
                        decalpath = makedir(os.path.join(sourcespath, uuid))
                        destination = os.path.join(decalpath, "%s.png" % (textype.lower()))
                        print("WARNING: creating dummy %s map at: %s" % (textype, destination))

                        create_dummy_texture(decalpath, "%s.png" % textype.lower(), mode='RGB', resolution=maxres, color=textype_color_mapping_dict[textype])
                        sources[uuid]['textures'][textype] = destination

                        sources[uuid]['original_textures'][textype] = ''

            else:
                print("WARNING: NO textures exist, skipping decal", mat.DM.decalname)

    if debug:
        print(dumps(sources, indent=4))

    return sources



def initiate_atlas(minres, padding, prepacked_sources=[]):

    if prepacked_sources:
        vertical = sum(decal['size'][1] for _, decal in prepacked_sources) + len(prepacked_sources) * padding + padding
        horizontal = max(decal['size'][0] for _, decal in prepacked_sources)

        prepacked_minres = max([vertical, horizontal])

        if prepacked_minres > minres:
            minres = prepacked_minres

            print("INFO: Bumping minimally required resolution due to pre-packed panel decals to %dx%d." % (minres, minres))


    width = height = minres

    full_boxes = {}

    previous_y = 0

    for idx, (uuid, decal) in enumerate(prepacked_sources):
        p = round(padding / 2) if idx == 0 else padding

        full_boxes[uuid] = {'coords': [0, previous_y + p],
                            'dimensions': [width, decal['size'][1]]}

        previous_y += p + decal['size'][1]

    if prepacked_sources:
        free_boxes = [(0, previous_y + round(padding / 2), width, height - previous_y - round(padding / 2))]
    else:
        free_boxes = [(0, 0, width, height)]

    return minres, free_boxes, full_boxes


def kivy(freeboxes, padding, box, imgw, imgh):

    if box[2] > (imgw + padding):
        freeboxes.append((box[0] + (imgw + padding), box[1], box[2] - (imgw + padding), (imgh + padding)))

    if box[3] > (imgh + padding):
        freeboxes.append((box[0], box[1] + (imgh + padding), box[2], box[3] - (imgh + padding)))


def blackpawn(freeboxes, padding, box, imgw, imgh, alternative=False):

    dw = box[2] - (imgw + padding)
    dh = box[3] - (imgh + padding)

    if alternative:
        if dh > dw:
            freeboxes.append((box[0] + (imgw + padding), box[1], dw, box[3]))
            freeboxes.append((box[0], box[1] + (imgh + padding), (imgw + padding), dh))
        else:
            freeboxes.append((box[0], box[1] + (imgh + padding), box[2], dh))
            freeboxes.append((box[0] + (imgw + padding), box[1], dw, (imgh + padding)))

    else:
        if dw > dh:
            freeboxes.append((box[0] + (imgw + padding), box[1], dw, box[3]))
            freeboxes.append((box[0], box[1] + (imgh + padding), (imgw + padding), dh))
        else:
            freeboxes.append((box[0], box[1] + (imgh + padding), box[2], dh))
            freeboxes.append((box[0] + (imgw + padding), box[1], dw, (imgh + padding)))



def layout_atlas(context, templatepath, sources, solution, atlas_images, idx, uuid, name='Atlas', normalize_factor=1):

    atlas = create_new_atlas_obj(context, name=name, uuid=uuid, index=idx, resolution=solution['resolution'])

    add_atlas_trims(atlas, sources, solution, sortby='NAME', initiate=True)

    dummies = create_atlas_dummies(context, atlas)

    dummymat = append_material(templatepath, "TEMPLATE_ATLASDUMMY")

    bg_mats = [mat for mat in bpy.data.materials if mat.DM.isatlasbgmat]
    mat_bg = bg_mats[0] if bg_mats else append_material(templatepath, "ATLAS_BG")

    if dummymat and mat_bg:
        atlas.DM.atlasdummymat = dummymat

        atlas.data.materials.append(mat_bg)

        dummymat.name = atlas.name
        dummymat.DM.atlasname = atlas.DM.atlasname
        dummymat.DM.atlasuuid = atlas.DM.atlasuuid

        set_atlasdummy_texture_paths(dummymat, atlas_images)

        set_node_names_of_atlas_material(dummymat, atlas.DM.atlasname, dummy=True)

        textures = get_atlas_textures(dummymat)

        for img in textures.values():
            img.DM.atlasname = atlas.DM.atlasname
            img.DM.atlasuuid = atlas.DM.atlasuuid

        for dummy in dummies:
            dummy.data.materials.append(dummymat)

    if solution['type'] in ['NORMAL', 'COMBINED']:
        atlas.DM.atlasdummyparallax = 0.1 / normalize_factor

    solution['name'] = atlas.DM.atlasname
    solution['uuid'] = uuid

    atlas.DM['sources'] = sources
    atlas.DM['solution'] = solution

    return atlas


def create_new_atlas_obj(context, name='Atlas', uuid='', index='001', resolution=(1024, 1024)):
    atlas = bpy.data.objects.new(name=name, object_data=bpy.data.meshes.new(name=name))
    atlas.data.use_auto_texspace = False

    bm = bmesh.new()
    bm.from_mesh(atlas.data)

    uvs = bm.loops.layers.uv.verify()

    coords = img_coords_to_mesh_coords(resolution)
    uvcoords = [Vector((0, 0)), Vector((1, 0)), Vector((1, 1)), Vector((0, 1))]

    verts = []

    for co in coords:
        verts.append(bm.verts.new(co))

    bm.faces.new(verts)

    loops = [v.link_loops[0] for v in verts]

    for loop, uvco in zip(loops, uvcoords):
        loop[uvs].uv = uvco

    bm.to_mesh(atlas.data)
    bm.free()

    col = bpy.data.collections.new(name='%s (preview)' % (atlas.name))
    context.scene.collection.children.link(col)

    col.objects.link(atlas)

    atlas.DM.atlascollection = col


    bpy.ops.object.select_all(action='DESELECT')
    atlas.select_set(True)
    context.view_layer.objects.active = atlas


    atlas.DM.isatlas = True
    atlas.DM.avoid_update = True
    atlas.DM.atlasname = atlas.name
    atlas.DM.atlasuuid = uuid
    atlas.DM.atlasindex = index
    atlas.DM.atlasresolution = resolution

    atlas.location = context.scene.cursor.location
    atlas.lock_scale = True, True, True

    context.evaluated_depsgraph_get()

    return atlas


def update_atlas_obj(atlas, resolution):
    coords = img_coords_to_mesh_coords(resolution)

    bm = bmesh.new()
    bm.from_mesh(atlas.data)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    for v, co in zip(bm.verts, coords):
        v.co = co

    bm.to_mesh(atlas.data)
    bm.free()

    atlas.data.update()

    atlas.DM.atlasresolution = resolution


def add_atlas_trims(atlas, sources, solution, sortby='NAME', initiate=False):

    resolution = solution['resolution']

    if sortby == 'NAME':
        for idx, (uuid, decal) in enumerate(sources.items()):
            name = decal['name']
            ispanel = decal['ispanel']
            prepack = decal['prepack']

            coords = solution['boxes'][uuid]['coords']
            dimensions = solution['boxes'][uuid]['dimensions']

            trimmx = img_coords_to_trimmx(coords, dimensions, resolution)

            t = atlas.DM.trimsCOL.add()
            t.name = name
            t.uuid = uuid
            t.mx = flatten_matrix(trimmx)
            t.ispanel = ispanel

            t.avoid_update = True
            t.prepack = prepack

            if initiate:
                t.original_size = decal['size']

                if idx == 0:
                    t.isactive = True

    elif sortby == 'PACK':
        for idx, (uuid, decal) in enumerate(solution['boxes'].items()):
            name = sources[uuid]['name']
            ispanel = sources[uuid]['ispanel']
            prepack = sources[uuid]['prepack']

            coords = decal['coords']
            dimensions = decal['dimensions']

            trimmx = img_coords_to_trimmx(coords, dimensions, resolution)

            t = atlas.DM.trimsCOL.add()
            t.name = name
            t.uuid = uuid
            t.mx = flatten_matrix(trimmx)
            t.ispanel = ispanel

            t.avoid_update = True
            t.prepack = prepack

            if initiate:
                t.original_size = sources[uuid]['size']

                if idx == 0:
                    t.isactive = True


def refresh_atlas_trims(atlas):
    sources = atlas.DM.get('sources')
    solution = atlas.DM.get('solution')

    trims = {}

    for trim in atlas.DM.trimsCOL:
        trims[trim.uuid] = {}
        trims[trim.uuid]['dummy'] = trim.dummy
        trims[trim.uuid]['original_size'] = list(trim.original_size)
        trims[trim.uuid]['isactive'] = trim.isactive

    atlas.DM.trimsCOL.clear()

    add_atlas_trims(atlas, sources, solution, sortby=atlas.DM.atlastrimsort, initiate=True)

    for idx, trim in enumerate(atlas.DM.trimsCOL):
        if trim.uuid in trims:
            trim.dummy = trims[trim.uuid]['dummy']
            trim.original_size = trims[trim.uuid]['original_size']

            if trims[trim.uuid]['isactive']:
                trim.isactive = True
                atlas.DM.trimsIDX = idx

        else:
            trim.original_size = sources[trim.uuid]['original_size']


def create_atlas_dummies(context, atlas, trims=[]):

    dummies = []

    if not trims:
        trims = atlas.DM.trimsCOL

    for trim in trims:
        dummy = bpy.data.objects.new(name="%s Dummy %s" % (atlas.DM.atlasname, trim.name), object_data=bpy.data.meshes.new(name="%s Dummy %s" % (atlas.DM.atlasname, trim.name)))

        top_left, dimensions = trimmx_to_img_coords(trim.mx, atlas.DM.atlasresolution)

        coords = img_coords_to_mesh_coords(dimensions)
        uvcoords = img_coords_to_uv_coords(top_left, dimensions, atlas.DM.atlasresolution)

        location = Vector(((-atlas.DM.atlasresolution[0] / 2 / 1000 + ((top_left[0] + dimensions[0] / 2) / 1000), (-atlas.DM.atlasresolution[1] / 2 / 1000 + atlas.DM.atlasresolution[1] / 1000 - (top_left[1] + dimensions[1] / 2) / 1000), 0)))

        bm = bmesh.new()
        bm.from_mesh(dummy.data)

        uvs = bm.loops.layers.uv.verify()

        verts = []

        for co in coords:
            verts.append(bm.verts.new(location + co))

        bm.faces.new(verts)

        loops = [v.link_loops[0] for v in verts]

        for loop, uvco in zip(loops, uvcoords):
            loop[uvs].uv = uvco

        bm.to_mesh(dummy.data)
        bm.free()

        dummy.data.update()

        dummy.location = atlas.location

        dummy.lock_location = True, True, True
        dummy.lock_rotation = True, True, True
        dummy.lock_scale = True, True, True

        dummy.hide_select = True

        dummy.DM.isatlasdummy = True
        dummy.DM.uuid = trim.uuid

        dummy.DM.avoid_update = True
        dummy.DM.atlasname = atlas.DM.atlasname
        dummy.DM.atlasuuid = atlas.DM.atlasuuid

        atlas.DM.atlascollection.objects.link(dummy)

        add_displace(dummy, height=0.999)

        trim.dummy = dummy

        dummies.append(dummy)

    context.evaluated_depsgraph_get()

    for dummy in dummies:
        parent(dummy, atlas)

    return dummies


def update_atlas_dummy(atlas, trim, update_uvs=False):

    if trim.dummy:
        dummy = trim.dummy

        top_left, dimensions = trimmx_to_img_coords(trim.mx, atlas.DM.atlasresolution)
        location = Vector(((-atlas.DM.atlasresolution[0] / 2 / 1000 + ((top_left[0] + dimensions[0] / 2) / 1000), (-atlas.DM.atlasresolution[1] / 2 / 1000 + atlas.DM.atlasresolution[1] / 1000 - (top_left[1] + dimensions[1] / 2) / 1000), 0)))

        bm = bmesh.new()
        bm.from_mesh(dummy.data)

        uvs = bm.loops.layers.uv.verify()

        coords = [Vector((-dimensions[0] / 2 / 1000, -dimensions[1] / 2 / 1000, 0)), Vector((dimensions[0] / 2 / 1000, -dimensions[1] / 2 / 1000, 0)), Vector((dimensions[0] / 2 / 1000, dimensions[1] / 2 / 1000, 0)), Vector((-dimensions[0] / 2 / 1000, dimensions[1] / 2 / 1000, 0))]

        for v, co in zip(bm.verts, coords):
            v.co = location + co

        if update_uvs:
            uvcoords = img_coords_to_uv_coords(top_left, dimensions, atlas.DM.atlasresolution)

            loops = [v.link_loops[0] for v in bm.verts]

            for loop, uvco in zip(loops, uvcoords):
                loop[uvs].uv = uvco

        bm.to_mesh(dummy.data)
        bm.free()

        dummy.data.update()


def reset_trim_scale(atlas, trim):
    orig_size = trim.original_size

    trim.mx[0][0] = orig_size[0] / atlas.DM.atlasresolution[0]
    trim.mx[1][1] = orig_size[1] / atlas.DM.atlasresolution[1]

    if trim.ispanel:
        trim.avoid_update = True
        trim.prepack = 'NONE'

        sources = atlas.DM.get('sources')

        if sources:
            sources[trim.uuid]['prepack'] = 'NONE'

    update_atlas_dummy(atlas, trim)


def stretch_trim_scale(atlas, trim):
    trim.mx[0][0] = 1
    trim.mx[0][3] = 0

    update_atlas_dummy(atlas, trim)



def get_instant_atlas_path(atlas):
    assetspath = get_prefs().assetspath
    createpath = os.path.join(assetspath, "Create")
    atlasinstantpath = os.path.join(createpath, "atlasinstant")

    idx = atlas.DM.atlasindex
    uuid = atlas.DM.atlasuuid

    atlaspath = os.path.join(atlasinstantpath, "%s_%s" % (idx, uuid))

    if os.path.exists(atlaspath):
        return atlaspath


def get_atlas_images_from_path(path):

    images = {}

    for textype, _, _ in atlastexturetype_items[1:]:
        imgpath = os.path.join(path, "%s.png" % (textype.lower()))

        if os.path.exists(imgpath):
            images[textype] = imgpath

    return images


def get_lower_and_upper_atlas_resolution(resolution):
    value = 1

    scale = [value]

    while value <= resolution:
        value *= 2
        scale.append(value)

    return scale[-2:]


def create_atlas_json(destination, atlas, maps, size=None, new_atlas_uuid=False, debug=False):
    path = os.path.join(destination, "data.json")

    trims = []

    for trim in atlas.DM.trimsCOL:
        trimmx = trim.mx.copy()
        location = trimmx.col[3][:2]
        scale = (trimmx[0][0], trimmx[1][1])

        if size:

            if size < atlas.DM.atlasresolution[0]:
                location = [co * (size / atlas.DM.atlasresolution[0]) for co in location]
                trimmx.col[3][:2] = location

        resolution = (size, size) if size else tuple(atlas.DM.atlasresolution)

        coords, dimensions = trimmx_to_img_coords(trimmx, resolution)

        td = {"name": trim.name,
              "uuid": trim.uuid,
              "location": location,
              "scale": scale,
              "isactive": trim.isactive,
              "isempty": False,
              "ispanel": trim.ispanel,
              "hide": False,
              "hide_select": False,
              "coords": coords,
              "dimensions": dimensions}

        if trim.ispanel:
            sources = atlas.DM['sources']


            if sources[trim.uuid].get('repetitions'):
                td['repetitions'] = sources[trim.uuid]['repetitions']

        trims.append(td)

    d = {"name": atlas.DM.atlasname,
         "uuid": new_atlas_uuid if new_atlas_uuid else atlas.DM.atlasuuid,
         "resolution": resolution,
         "isatlas": True,
         "maps": maps,
         "trims": trims}


    with open(path, "w") as f:
        dump(d, f, indent=4)

    if debug:
        print(dumps(d, indent=4))



def get_atlasdata_from_atlas(atlas):

    return bpy.context.window_manager.trimsheets[atlas.name] if atlas.istrimsheet else bpy.context.window_manager.atlases[atlas.name]


def get_atlasdata_from_decaluuid(uuid, atlases=None):

    if not atlases:
        atlases = get_atlas()[1]

    for atlas in atlases:
        data = get_atlasdata_from_atlas(atlas)

        for trim in data['trims']:
            if uuid == trim['uuid']:
                return atlas, data, trim
    return None, None, None


def get_atlasdata_from_atlasmat(atlasmat):
    atlases = [atlas for atlas in get_atlas()[1]]

    for atlas in atlases:
        d = bpy.context.window_manager.trimsheets if atlas.istrimsheet else bpy.context.window_manager.atlases
        data = d.get(atlas.name)

        if data and data['uuid'] == atlasmat.DM.atlasuuid:
            return atlas, data


def get_atlaspath_from_uuid(uuid):
    for name, atlasdata in bpy.context.window_manager.atlases.items():
        if atlasdata['uuid'] == uuid:
            return os.path.join(get_prefs().assetspath, 'Atlases', name)


def get_atlastype_from_atlas(atlas):

    data = get_atlasdata_from_atlas(atlas)

    if all(textype in data['maps'] for textype in ['COLOR', 'NORMAL']):
        return 'COMBINED'
    elif 'COLOR' in data['maps']:
        return 'INFO'
    elif 'NORMAL' in data['maps']:
        return 'NORMAL'


def get_textypes_from_atlasmats(atlasmats):
    uuids = [mat.DM.atlasuuid for mat in atlasmats]

    atlases = []

    for name, data in bpy.context.window_manager.trimsheets.items():
        if data['uuid'] in uuids:
            atlases.append(data)

    for name, data in bpy.context.window_manager.atlases.items():
        if data['uuid'] in uuids:
            atlases.append(data)

    textypes = set()

    for data in atlases:
        for textype in data['maps']:
            textypes.add(textype)

    return textypes


def verify_channel_pack(textypes, item):
    channeltypes = [cht for cht in [item.red, item.green, item.blue, item.alpha] if cht != 'NONE']

    if not channeltypes:
        return

    for cht in channeltypes:
        if cht == 'SMOOTHNESS':
            if 'ROUGHNESS' not in textypes:
                return False

        elif cht == 'SUBSETOCCLUSION':
            if not all(tt in textypes for tt in ['SUBSET', 'AO']):
                return False

        elif cht == 'WHITEHEIGHT':
            if 'HEIGHT' not in textypes:
                return False

        else:
            if cht not in textypes:
                return False

    return True
