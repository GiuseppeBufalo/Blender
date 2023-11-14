import bpy
import bmesh
from mathutils import Vector
import os
from json import dump
from . registration import get_prefs, update_instanttrimsheetcount
from . system import get_new_directory_index, abspath, makedir
from . material import set_node_names_of_trimsheet_material, get_trimsheet_textures
from . uv import get_selection_uv_bbox, get_trim_uv_bbox
from . math import trimmx_to_img_coords
from . ui import popup_message



def create_new_trimsheet_obj(context, name="TrimSheet", uuid="", index="001", resolution=(1024, 1024)):
    sheet = bpy.data.objects.new(name=name, object_data=bpy.data.meshes.new(name=name))

    bm = bmesh.new()
    bm.from_mesh(sheet.data)

    uvs = bm.loops.layers.uv.verify()

    width = resolution[0] / 1000
    height = resolution[1] / 1000

    coords = [Vector((-width / 2, -height / 2, 0)), Vector((width / 2, -height / 2, 0)), Vector((width / 2, height / 2, 0)), Vector((-width / 2, height / 2, 0))]
    uvcoords = [Vector((0, 0)), Vector((1, 0)), Vector((1, 1)), Vector((0, 1))]

    verts = []

    for co in coords:
        verts.append(bm.verts.new(co))

    bm.faces.new(verts)

    loops = [v.link_loops[0] for v in verts]

    for loop, uvco in zip(loops, uvcoords):
        loop[uvs].uv = uvco

    bm.to_mesh(sheet.data)
    bm.free()

    context.scene.collection.objects.link(sheet)

    bpy.ops.object.select_all(action='DESELECT')
    sheet.select_set(True)
    context.view_layer.objects.active = sheet

    sheet.DM.avoid_update = True
    sheet.DM.trimsheetname = sheet.name
    sheet.DM.istrimsheet = True
    sheet.DM.trimsheetuuid = uuid
    sheet.DM.trimsheetindex = index
    sheet.DM.trimsheetresolution = resolution

    sheet.location = context.scene.cursor.location
    sheet.lock_scale = True, True, True

    maps = sheet.DM.trimmapsCOL

    for maptype in ['Normal', 'AO', 'Curvature', 'Height', 'Color', 'Metallic', 'Roughness', 'Emission', 'Alpha', 'Subset', 'Material2']:
        map = maps.add()
        map.name = maptype

    return sheet



def get_trim(sheet):
    idx = sheet.DM.trimsIDX
    trims = sheet.DM.trimsCOL
    active = trims[idx] if trims else None

    return idx, trims, active


def get_trim_map(sheet):
    idx = sheet.DM.trimmapsIDX
    trim_maps = sheet.DM.trimmapsCOL
    active = trim_maps[idx] if trim_maps else None

    return idx, trim_maps, active



def set_node_names_of_trimsheet(sheet, reset_heightnode_names=False):
    mat = sheet.active_material

    if mat and mat.DM.istrimsheetmat:
        set_node_names_of_trimsheet_material(mat, sheet.name, reset_heightnode_names=reset_heightnode_names)


def change_trimsheet_mesh_dimensions(sheet, width, height):
    width = width / 1000
    height = height / 1000

    coords = [Vector((-width / 2, -height / 2, 0)), Vector((width / 2, -height / 2, 0)), Vector((width / 2, height / 2, 0)), Vector((-width / 2, height / 2, 0))]

    bm = bmesh.new()
    bm.from_mesh(sheet.data)

    for v, co in zip(bm.verts, coords):
        v.co = co

    bm.to_mesh(sheet.data)
    bm.free()


def update_trim_locations(trims, oldres, newres):
    for trim in trims:
        trim.mx.col[3][0] *= newres[0] / oldres[0]
        trim.mx.col[3][1] *= newres[1] / oldres[1]




def get_instant_sheet_path(sheet):
    assetspath = get_prefs().assetspath
    createpath = os.path.join(assetspath, "Create")
    triminstantpath = os.path.join(createpath, "triminstant")

    idx = sheet.DM.trimsheetindex
    uuid = sheet.DM.trimsheetuuid

    path = os.path.join(triminstantpath, "%s_%s" % (idx, uuid))

    if os.path.exists(path):
        return path

    else:
        idx = get_new_directory_index(triminstantpath)
        sheet.DM.trimsheetindex = idx

        path = os.path.join(triminstantpath, "%s_%s" % (idx, uuid))
        makedir(path)
        return path


def create_trimsheet_json(sheet):
    sheetpath = get_instant_sheet_path(sheet)

    path = os.path.join(sheetpath, "data.json")
    initializing = not os.path.exists(path)

    maps = {}

    for trim_map in sheet.DM.trimmapsCOL:
        if trim_map.texture:
            maptype = trim_map.name.upper()

            maps[maptype] = {'texture': trim_map.texture,
                             'resolution': tuple(trim_map.resolution)}

            if maptype == 'HEIGHT':
                maps[maptype]['parallax_amount'] = trim_map.parallax_amount

            elif maptype == 'ALPHA':
                maps[maptype]['connect_alpha'] = trim_map.connect_alpha


    trims = []

    for trim in sheet.DM.trimsCOL:
        location = trim.mx.col[3][:2]
        scale = (trim.mx[0][0], trim.mx[1][1])

        coords, dimensions = trimmx_to_img_coords(trim.mx, tuple(sheet.DM.trimsheetresolution))

        td = {"name": trim.name,
              "uuid": trim.uuid,
              "location": location,
              "scale": scale,
              "isactive": trim.isactive,
              "isempty": trim.isempty,
              "ispanel": trim.ispanel,
              "hide": trim.hide,
              "hide_select": trim.hide_select,
              "coords": coords,
              "dimensions": dimensions}

        if trim.ispanel:
            td['repetitions'] = 1

        trims.append(td)


    d = {"name": sheet.DM.trimsheetname,
         "uuid": sheet.DM.trimsheetuuid,
         "resolution": tuple(sheet.DM.trimsheetresolution),
         "isatlas": False,
         "maps": maps,
         "trims": trims}

    with open(path, "w") as f:
        dump(d, f, indent=4)

    if initializing:
        update_instanttrimsheetcount()


def verify_instant_trimsheet(path, sheet):

    if not os.path.exists(os.path.join(path, 'data.json')):
        print("WARNING: data.json not found, re-creating")
        create_trimsheet_json(sheet)


    textures = get_trimsheet_textures(sheet.active_material)

    if textures:

        for textype, img in textures.items():
            imgpath = os.path.join(path, "%s.png" % (textype.lower()))

            if img.filepath != imgpath:
                print("WARNING: updating trim sheet texture path")
                print(" from", img.filepath)
                print("   to", imgpath)

                img.filepath = imgpath

            if os.path.exists(imgpath) and img.size[0] == 0:
                img.reload()

        if not all([os.path.exists(abspath(img.filepath)) for img in textures.values()]):
            msg = ["Some or all of the trim sheet textures are missing.",
                   "",
                   "This shouldn't happen normally, unless you are working on a sheet, whose instant folder has been removed.",
                   "This folder will now have been recreated, but at least some of the sheet's textures are still missing.",
                   "",
                   "Open the Instant Trim Sheet folder to investigate.",
                   "You can manually place the necessary textures in this folder,",
                   "Or re-assign the maps in the Texture Maps section above."]

            popup_message(msg, title="Aborting")
            return False
    return True



def get_sheetdata_from_uuid(uuid):
    for name, sheetdata in bpy.context.window_manager.trimsheets.items():
        if sheetdata['uuid'] == uuid:
            return sheetdata


def get_sheetpath_from_uuid(uuid):
    for name, sheetdata in bpy.context.window_manager.trimsheets.items():
        if sheetdata['uuid'] == uuid:
            return os.path.join(get_prefs().assetspath, 'Trims', name)


def get_trim_uuid_from_library_and_name(context, libraryname, trimname):

    uuids = context.window_manager.decaluuids

    for uuid, decals in uuids.items():
        for decal in decals:
            decalname, sheetlibrary, libtype = decal

            if libtype == 'Trims' and sheetlibrary == libraryname and decalname == trimname:
                return uuid


def read_uuid_from_file(assetspath, libraryname, trimname):

    uuidpath = os.path.join(assetspath, 'Trims', libraryname, trimname, 'uuid')

    with open(uuidpath) as f:
        uuid = f.read().replace("\n", "")

    return uuid


def get_trim_from_uuid(sheetdata, uuid):
    for trim in sheetdata['trims']:
        if trim.get('uuid') == uuid:
            return trim


def get_empty_trim_from_sheetdata(sheetdata):
    if sheetdata:
        for trim in sheetdata['trims']:
            if trim['isempty']:
                return trim


def get_empty_trim_from_sheetmat(mat):
    sheetdata = get_sheetdata_from_uuid(mat.DM.trimsheetuuid)

    if sheetdata:
        return get_empty_trim_from_sheetdata(sheetdata)


def get_trim_from_selection_via_midpoint_proximity(active, sheetdata, meshdata={}):

    if meshdata:
        faces = meshdata['faces']
        loops = meshdata['loops']
        uvs = meshdata['uvs']

    else:
        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        faces = [f for f in bm.faces if f.select]

        uvs = bm.loops.layers.uv.active

        loops = [loop for face in faces for loop in face.loops]

    _, selmid, _ = get_selection_uv_bbox(uvs, loops)

    if selmid:
        trim_distances = []

        sheetresolution = Vector(sheetdata.get('resolution'))

        for trim in sheetdata['trims']:
            trimlocation = Vector(trim.get('location'))
            trimscale = Vector(trim.get('scale'))

            _, trimmid = get_trim_uv_bbox(sheetresolution, trimlocation, trimscale)

            trim_distances.append(((trimmid - selmid).length, trim))

        return min(trim_distances, key=lambda x: x[0])[1]


def get_trim_from_selection_via_bbox_containment(active, sheetdata, meshdata={}):

    if meshdata:
        faces = meshdata['faces']
        loops = meshdata['loops']
        uvs = meshdata['uvs']

    else:
        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        faces = [f for f in bm.faces if f.select]

        uvs = bm.loops.layers.uv.active

        loops = [loop for face in faces for loop in face.loops]

    _, selmid, _ = get_selection_uv_bbox(uvs, loops)

    if selmid:
        selmid = Vector((selmid.x % 1, selmid.y % 1))

        if selmid:
            sheetresolution = Vector(sheetdata.get('resolution'))

            matches = []

            for trim in sheetdata['trims']:
                trimlocation = Vector(trim.get('location'))
                trimscale = Vector(trim.get('scale'))

                bbox, trimmid = get_trim_uv_bbox(sheetresolution, trimlocation, trimscale)

                minu, minv = bbox[0]
                maxu, maxv = bbox[1]

                if minu < selmid.x < maxu and minv < selmid.y < maxv:
                    distance = (trimmid - selmid).length
                    matches.append((distance, trim))

            if matches:
                return min(matches, key=lambda x: x[0])[1]


def get_trim_from_selection(active, sheetdata, meshdata={}):

    trim = get_trim_from_selection_via_bbox_containment(active, sheetdata, meshdata=meshdata)

    if not trim:
        trim = get_trim_from_selection_via_midpoint_proximity(active, sheetdata, meshdata=meshdata)
    return trim
