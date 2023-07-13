import bpy
from bpy.props import IntProperty
import bmesh
from mathutils import Vector
from uuid import uuid4
import os
from shutil import copy, rmtree
import json
import re
from .. utils.registration import get_prefs, get_templates_path, reload_trimtextures, reload_trim_libraries, update_instanttrimsheetcount, get_version_from_blender, get_version_filename_from_blender
from .. utils.append import append_material
from .. utils.material import get_trimsheet_nodes, get_trimsheetgroup_from_trimsheetmat, get_trimsheet_textures, get_parallaxgroup_from_any_mat
from .. utils.material import get_decal_textures, get_decalgroup_from_decalmat, get_parallaxgroup_from_decalmat, get_heightgroup_from_parallaxgroup, get_decal_texture_nodes
from .. utils.material import remove_decalmat, get_trimsheet_material_from_faces, assign_trimsheet_material, append_and_setup_trimsheet_material, get_decalmat, remove_trimsheetmat, get_material_output
from .. utils.material import get_mix_node_input, get_mix_node_output
from .. utils.trim import create_new_trimsheet_obj, set_node_names_of_trimsheet, create_trimsheet_json, change_trimsheet_mesh_dimensions, update_trim_locations
from .. utils.trim import get_trim_map, get_instant_sheet_path, get_empty_trim_from_sheetdata, verify_instant_trimsheet, get_sheetdata_from_uuid
from .. utils.create import save_uuid, save_blend, render_thumbnail
from .. utils.system import makedir, get_new_directory_index, abspath
from .. utils.ui import warp_cursor_to_object_origin, popup_message
from .. utils.modifier import add_displace, add_nrmtransfer
from .. utils.object import update_local_view
from .. utils.decal import set_props_and_node_names_of_decal
from .. utils.uv import unwrap_to_empty_trim, set_trim_uv_channel
from .. utils.mesh import reset_material_indices, unhide_deselect
from .. utils.library import get_lib
from .. utils.pil import check_image_for_nonblack_pixels, crop_trimsheet_texture, ensure_mode, create_trim_masks_map, create_dummy_texture, create_trim_ao_curv_height_map, check_for_alpha
from .. utils.system import load_json, save_json, log
from .. import bl_info



class InitTrimSheet(bpy.types.Operator):
    bl_idname = "machin3.init_trimsheet"
    bl_label = "MACHIN3: Initialize Trim Sheet"
    bl_description = "Initialize a new Trim Sheet"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            sheet = context.active_object if context.active_object and context.active_object.DM.istrimsheet and context.active_object.select_get() else None
            return not sheet

    def execute(self, context):
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        triminstantpath = os.path.join(createpath, "triminstant")
        templatepath = get_templates_path()

        sheet = create_new_trimsheet_obj(context, uuid=str(uuid4()), index=get_new_directory_index(triminstantpath))

        mat = append_material(templatepath, "TEMPLATE_TRIMSHEET")

        if mat:
            sheet.data.materials.append(mat)
            mat.name = sheet.name
            mat.DM.trimsheetuuid = sheet.DM.trimsheetuuid
            mat.DM.trimsheetname = sheet.DM.trimsheetname

            set_node_names_of_trimsheet(sheet)

        makedir(os.path.join(triminstantpath, "%s_%s" % (sheet.DM.trimsheetindex, sheet.DM.trimsheetuuid)))

        create_trimsheet_json(sheet)

        update_instanttrimsheetcount()

        view = context.space_data

        if not view.show_gizmo:
            view.show_gizmo = True

        return {'FINISHED'}


class DuplicateTrimSheet(bpy.types.Operator):
    bl_idname = "machin3.duplicate_trimsheet"
    bl_label = "MACHIN3: Duplicate Trim Sheet"
    bl_description = "Duplicate Trim Sheet\nALT: Keep the Texture Assignments"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.DM.istrimsheet and active.active_material and active.active_material.DM.istrimsheetmat

    def invoke(self, context, event):
        mcol = context.scene.collection
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        triminstantpath = os.path.join(createpath, "triminstant")

        sheet = context.active_object

        dup = sheet.copy()
        dup.data = sheet.data.copy()
        mcol.objects.link(dup)

        bpy.ops.object.select_all(action='DESELECT')
        dup.select_set(True)
        context.view_layer.objects.active = dup

        mat = sheet.active_material.copy()
        dup.active_material = mat

        tsg = get_trimsheetgroup_from_trimsheetmat(mat)
        tsg.node_tree = tsg.node_tree.copy()

        pg = get_parallaxgroup_from_any_mat(mat)
        pg.node_tree = pg.node_tree.copy()

        heightgroups = get_trimsheet_nodes(mat).get('HEIGHTGROUP')
        hgtree = heightgroups[0].node_tree.copy()

        for hg in heightgroups:
            hg.node_tree = hgtree

        dup.DM.trimsheetuuid = str(uuid4())
        dup.DM.trimsheetindex = get_new_directory_index(triminstantpath)

        mat.DM.trimsheetuuid = dup.DM.trimsheetuuid
        mat.DM.trimsheetname = dup.name

        for trim in dup.DM.trimsCOL:
            trim.uuid = str(uuid4())

        sheetpath = makedir(os.path.join(triminstantpath, "%s_%s" % (dup.DM.trimsheetindex, dup.DM.trimsheetuuid)))

        nodes = get_trimsheet_nodes(dup.active_material)

        if event.alt:
            for trim_map in dup.DM.trimmapsCOL:
                maptype = trim_map.name.upper()
                node = nodes.get(maptype)

                if node.image:
                    imgpath = abspath(node.image.filepath)

                    if os.path.exists(imgpath):
                        newpath = os.path.join(sheetpath, "%s.png" % (maptype.lower()))

                        copy(imgpath, newpath)

                        img = bpy.data.images.load(newpath)
                        img.DM.istrimsheettex = True
                        img.DM.trimsheettextype = maptype
                        img.DM.trimsheetuuid = sheet.DM.trimsheetuuid
                        img.DM.trimsheetname = dup.name
                        img.colorspace_settings.name = 'sRGB' if maptype in ['COLOR', 'EMISSION'] else 'Non-Color'

                        node.image = img

        else:
            for trim_map in dup.DM.trimmapsCOL:
                trim_map.texture = ''
                trim_map.resolution = (1024, 1024)

                maptype = trim_map.name.upper()
                node = nodes.get(maptype)

                if node:
                    node.image = None
                    node.mute = True

                    if maptype == 'HEIGHT':
                        node = nodes.get('PARALLAXGROUP')

                        if node:
                            node.mute = True
                            node.inputs[0].default_value = 0.1

                        trim_map.avoid_update = True
                        trim_map.parallax_amount = 0.1

                    elif maptype == 'ALPHA':
                        dup.active_material.blend_method = 'OPAQUE'

                        trim_map.avoid_update = True
                        trim_map.connect_alpha = False


            oldres = tuple(dup.DM.trimsheetresolution)
            if oldres != (1024, 1024):
                dup.DM.trimsheetresolution = (1024, 1024)

                change_trimsheet_mesh_dimensions(dup, *dup.DM.trimsheetresolution)

                if dup.DM.trimsCOL:
                    update_trim_locations(dup.DM.trimsCOL, oldres, tuple(dup.DM.trimsheetresolution))

                    dup.select_set(True)

        dup.DM.trimcollection = None

        dup.DM.duplicate_sheet = True
        dup.DM.trimsheetname = dup.name

        create_trimsheet_json(dup)

        update_instanttrimsheetcount()

        view = context.space_data

        if not view.show_gizmo:
            view.show_gizmo = True

        warp_cursor_to_object_origin(context, event, dup)

        bpy.ops.transform.translate('INVOKE_DEFAULT')

        return {'FINISHED'}


class ImportTrimSheet(bpy.types.Operator):
    bl_idname = "machin3.import_trimsheet"
    bl_label = "MACHIN3: Import Trim Sheet"
    bl_description = "Import an existing Trim Sheet/Atlas created in DECALmachine"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            importpath = context.scene.DM.create_trim_import_path
            jsonpath = os.path.join(importpath, "data.json")
            return os.path.exists(jsonpath)

    def execute(self, context):
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        triminstantpath = os.path.join(createpath, "triminstant")
        templatepath = get_templates_path()

        importpath = context.scene.DM.create_trim_import_path
        jsonpath = os.path.join(importpath, "data.json")

        keep_trim_uuids = context.scene.DM.create_trim_import_keep_trim_uuids

        with open(jsonpath, mode='r') as f:
            d = json.load(f)

        name = d['name']

        if d.get('isatlas'):
            name = name.replace('Atlas', 'Sheet').replace('atlas', 'sheet').replace('ATLAS', 'SHEET')

            if name == d['name']:
                name += " Sheet"

        uuid = d['uuid']
        resolution = d['resolution']

        maps = d['maps']
        trims = d['trims']

        if triminstantpath in importpath:
            index = os.path.basename(importpath)[:3]
            sheetpath = importpath

        else:
            index = get_new_directory_index(triminstantpath)

            sheetpath = makedir(os.path.join(triminstantpath, "%s_%s" % (index, uuid)))

            copy(jsonpath, os.path.join(sheetpath, "data.json"))

            pngs = [f for f in os.listdir(importpath) if f.endswith('.png')]

            for png in pngs:
                copy(os.path.join(importpath, png), os.path.join(sheetpath, png))

        sheet = create_new_trimsheet_obj(context, name=name, uuid=uuid, index=index, resolution=resolution)

        mat = append_material(templatepath, "TEMPLATE_TRIMSHEET")

        if mat:
            self.setup_sheetmat(sheet, mat, maps, sheetpath)

        self.setup_trims(sheet, trims, keep_trim_uuids=keep_trim_uuids)

        create_trimsheet_json(sheet)

        update_instanttrimsheetcount()

        view = context.space_data

        if not view.show_gizmo:
            view.show_gizmo = True

        sheet.select_set(True)

        return {'FINISHED'}

    def setup_trims(self, sheet, trims, keep_trim_uuids=False):
        for idx, trim in enumerate(trims):
            t = sheet.DM.trimsCOL.add()

            t.avoid_update = True
            t.name = trim['name']

            if keep_trim_uuids:
                t.uuid = trim['uuid']

            else:
                t.uuid = str(uuid4())

            t.isactive = trim['isactive']

            if t.isactive:
                sheet.DM.avoid_update = True
                sheet.DM.trimsIDX = idx

            t.avoid_update = True
            t.ispanel = trim['ispanel']

            t.avoid_update = True
            t.isempty = trim['isempty']

            t.avoid_update = True
            t.hide = trim['hide']

            t.avoid_update = True
            t.hide_select = trim['hide_select']

            location = trim['location']
            scale = trim['scale']

            t.mx.col[3][:2] = location
            t.mx[0][0] = scale[0]
            t.mx[1][1] = scale[1]

    def setup_sheetmat(self, sheet, mat, maps, sheetpath):
        sheet.data.materials.append(mat)
        mat.name = sheet.name
        mat.DM.trimsheetuuid = sheet.DM.trimsheetuuid
        mat.DM.trimsheetname = sheet.DM.trimsheetname

        nodes = get_trimsheet_nodes(mat)

        for maptype, map_dict in maps.items():
            node = nodes.get(maptype)

            if node:
                imgpath = os.path.join(sheetpath, "%s.png" % (maptype.lower()))

                if os.path.exists(imgpath):
                    img = bpy.data.images.load(imgpath)
                    img.DM.istrimsheettex = True
                    img.DM.trimsheettextype = maptype
                    img.DM.trimsheetuuid = sheet.DM.trimsheetuuid
                    img.DM.trimsheetname = sheet.DM.trimsheetname
                    img.colorspace_settings.name = 'sRGB' if maptype in ['COLOR', 'EMISSION'] else 'Non-Color'

                    node.image = img
                    node.mute = False

            trim_map = sheet.DM.trimmapsCOL[maptype if maptype == 'AO' else maptype.title()]

            trim_map.texture = map_dict['texture']
            trim_map.resolution = map_dict['resolution']

            if maptype == 'HEIGHT':
                trim_map.avoid_update = True
                trim_map.parallax_amount = map_dict['parallax_amount']

                pg = nodes.get('PARALLAXGROUP')

                if pg:
                    pg.mute = False
                    pg.inputs[0].default_value = map_dict['parallax_amount']

            elif maptype == 'ALPHA':
                trim_map.avoid_update = True
                trim_map.connect_alpha = map_dict['connect_alpha']

                tree = mat.node_tree
                alpha = nodes.get('ALPHA')

                if trim_map.connect_alpha:
                    tsg = get_trimsheetgroup_from_trimsheetmat(mat)

                    tree.links.new(alpha.outputs[0], tsg.inputs['Alpha'])
                    mat.blend_method = 'BLEND'

            elif maptype not in ['SUBSET', 'MATERIAL2']:
                tree = mat.node_tree
                tsg = get_trimsheetgroup_from_trimsheetmat(mat)

                i = '%s Map' % maptype.title() if maptype in ['NORMAL', 'CURVATURE'] else 'AO Map' if maptype == 'AO' else 'Base Color' if maptype == 'COLOR' else maptype.title()
                tree.links.new(node.outputs[0], tsg.inputs[i])

        set_node_names_of_trimsheet(sheet)



class TrimSheet(bpy.types.Operator):
    bl_idname = "machin3.trimsheet"
    bl_label = "MACHIN3: Trim the Sheet"
    bl_description = "Create Trim Decals"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if get_prefs().pil and context.mode == 'OBJECT':
            active = context.active_object

            if active and active.DM.istrimsheet:
                mat = active.active_material

                if mat and mat.DM.istrimsheetmat:
                    return [trim for trim in active.DM.trimsCOL if not trim.isempty] and [trim_map for trim_map in active.DM.trimmapsCOL if trim_map.texture and trim_map.name in ['Normal', 'Color']]

    def execute(self, context):
        scene = context.scene
        mcol = scene.collection

        sheet = context.active_object
        mat = sheet.active_material
        trims = [trim for trim in sheet.DM.trimsCOL if not trim.isempty]

        triminstantpath = get_instant_sheet_path(sheet)
        templatepath = get_templates_path()

        if not verify_instant_trimsheet(triminstantpath, sheet):
            return {'CANCELLED'}

        textures = get_trimsheet_textures(mat)
        debug = scene.DM.debug

        if textures:
            bpy.ops.object.select_all(action='DESELECT')

            print("\nTrimSheet:", sheet.DM.trimsheetname)

            folders = [os.path.join(triminstantpath, f) for f in os.listdir(triminstantpath) if os.path.isdir(os.path.join(triminstantpath, f))]

            for f in folders:
                rmtree(f)

            self.remove_existing_trim_decals(context, sheet, trims, debug=debug)

            for idx, trim in enumerate(trims):

                trim_decalname = self.get_trim_decalname(idx, trim.name)
                trimpath = makedir(os.path.join(triminstantpath, trim_decalname))

                log(debug=debug)
                print("INFO: Creating trim decal:", "%s_%s" % (sheet.DM.trimsheetname, trim_decalname))

                loc, _, sca = trim.mx.decompose()

                trimtextures, decaltype = self.create_trim_decal_textures(trimpath, sheet, textures, trim, loc, sca)
                log(" textures created, decaltype:", decaltype, debug=debug)

                if trimtextures:
                    decal = self.create_trim_decal_geometry(mcol, sheet, loc, sca)
                    log(" trim decal geometry created:", decal, debug=debug)

                    self.create_decal(templatepath, sheet, trim, decal, trimtextures, decaltype, trim_decalname)
                    log(" trim decal set up:", decal.active_material, debug=debug)

                    log(" updating local view", debug=debug)
                    update_local_view(context.space_data, [(decal, True)])
                    log("  updated!", debug=debug)

                else:
                    print(" WARNING: Skipping:", trimpath)
                    rmtree(trimpath)


            alphamap = sheet.DM.trimmapsCOL.get('Alpha')

            if alphamap.connect_alpha:
                print("INFO: Disabling Trim Sheet's Alpha")
                alphamap.connect_alpha = False

            log("Finished trimming!", debug=debug)

        return {'FINISHED'}

    def create_decal(self, templatepath, sheet, trim, decalobj, trimtextures, decaltype, basename):

        decalobj.DM.isdecal = True
        decalobj.DM.istrimdecal = True

        add_displace(decalobj)

        add_nrmtransfer(decalobj)

        library = sheet.DM.trimsheetname

        decalmatname = "%s_%s" % (library, basename)
        decalname = decalmatname

        version = get_version_from_blender()

        parallax = sheet.DM.trimmapsCOL['Height'].parallax_amount if sheet.DM.trimmapsCOL['Height'].texture else None

        decalmat = append_material(templatepath, "TEMPLATE_%s" % decaltype.upper())

        if decalmat:
            decalmat.DM.istrimdecalmat = True

            decalobj.data.materials.append(decalmat)

            decalmatname = "%s_%s" % (library, basename)
            decalname = decalmatname

            decalobj.name = decalname
            decalobj.data.name = decalname
            decalmat.name = decalmatname

            textures = get_decal_textures(decalmat)

            for component in [decalobj, decalmat] + list(textures.values()):
                component.DM.uuid = trim.uuid
                component.DM.trimsheetuuid = sheet.DM.trimsheetuuid
                component.DM.version = version
                component.DM.decaltype = decaltype
                component.DM.decallibrary = library
                component.DM.decalname = decalname
                component.DM.decalmatname = decalmatname
                component.DM.creator = get_prefs().decalcreator

            decalgroup = get_decalgroup_from_decalmat(decalmat)
            decalgroup.name = "%s.%s" % (decaltype.lower(), decalmatname)

            parallaxgroup = get_parallaxgroup_from_any_mat(decalmat)

            if parallaxgroup:
                parallaxgroup.name = "parallax.%s" % (decalmatname)
                parallaxgroup.node_tree.name = "parallax.%s" % (decalmatname)
                decalmat.DM.parallaxnodename = "parallax.%s" % (decalmatname)

                if parallax:
                    maxscale = max([trim.mx[0][0], trim.mx[1][1]])
                    factor = 1 / maxscale
                    parallaxgroup.inputs[0].default_value = parallax * factor

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
                    node.image.name = ".%s.%s" % (textype.lower(), decalname)
                    node.image.filepath = trimtextures[textype]
                    node.image.DM.istrimdecaltex = True


            emission = textures.get('EMISSION')

            if emission:
                multiplier = decalgroup.inputs.get('Emission Multiplier')

                if check_image_for_nonblack_pixels(emission.filepath):
                    multiplier.default_value = 10

                else:
                    multiplier.default_value = 0

    def create_trim_decal_geometry(self, mcol, sheet, loc, sca):

        co1 = Vector((-sca.x / 2 * sheet.dimensions.x, -sca.y / 2 * sheet.dimensions.y, 0))
        co2 = Vector((sca.x / 2 * sheet.dimensions.x, -sca.y / 2 * sheet.dimensions.y, 0))
        co3 = Vector((sca.x / 2 * sheet.dimensions.x, sca.y / 2 * sheet.dimensions.y, 0))
        co4 = Vector((-sca.x / 2 * sheet.dimensions.x, sca.y / 2 * sheet.dimensions.y, 0))

        coords = [co1, co2, co3, co4]
        uv_coords = [Vector((0, 0)), Vector((1, 0)), Vector((1, 1)), Vector((0, 1))]

        decal = bpy.data.objects.new(name='TrimDecal', object_data=bpy.data.meshes.new(name='TrimDecal'))
        decal.location = sheet.matrix_world @ loc

        self.add_trim_decal_to_sheet_collection(mcol, sheet, decal)

        bm = bmesh.new()
        bm.from_mesh(decal.data)

        uvs = bm.loops.layers.uv.verify()

        verts = []

        for co in coords:
            verts.append(bm.verts.new(co))

        bm.faces.new(verts)

        loops = [v.link_loops[0] for v in verts]

        for loop, uvco in zip(loops, uv_coords):
            loop[uvs].uv = uvco

        bm.to_mesh(decal.data)
        bm.free()

        decal.data.update()

        return decal

    def add_trim_decal_to_sheet_collection(self, mcol, sheet, decal):
        if sheet.DM.trimcollection:
            col = sheet.DM.trimcollection
        else:
            col = bpy.data.collections.new(name=sheet.DM.trimsheetname)
            mcol.children.link(col)

            sheet.DM.trimcollection = col

        col.objects.link(decal)

    def create_trim_decal_textures(self, trimpath, sheet, textures, trim, loc, sca):
        trimtextures = {}

        for textype, img in textures.items():
            path = crop_trimsheet_texture(abspath(img.filepath), trimpath, loc.xy, sca.xy, sheet.dimensions.xy)

            if path:
                ensure_mode(textype, path)

                trimtextures[textype] = path

        decaltype = 'NONE'

        if 'COLOR' in trimtextures and 'NORMAL' not in trimtextures:
            decaltype = 'INFO'

        elif trim.ispanel and 'NORMAL' in trimtextures:
            decaltype = 'PANEL'

        elif 'NORMAL' in trimtextures:
            if 'SUBSET' in trimtextures and check_image_for_nonblack_pixels(trimtextures['SUBSET']):
                decaltype = 'SUBSET'

            else:
                decaltype = 'SIMPLE'

        if decaltype != 'NONE':

            trimtextures['MASKS'] = create_trim_masks_map(trimpath, trimtextures, decaltype)

            if 'EMISSION' not in trimtextures:
                trimtextures['EMISSION'] = create_dummy_texture(trimpath, 'emission.png')

            if decaltype in ['SIMPLE', 'SUBSET', 'PANEL']:
                trimtextures['AO_CURV_HEIGHT'] = create_trim_ao_curv_height_map(trimpath, trimtextures)

            deletetextures = {k: v for k, v in trimtextures.items() if (decaltype == 'INFO' and k not in ['COLOR', 'EMISSION', 'MASKS']) or (decaltype in ['SIMPLE', 'SUBSET', 'PANEL'] and k not in ['NORMAL', 'EMISSION', 'AO_CURV_HEIGHT', 'MASKS'])}

            for textype, path in deletetextures.items():
                if os.path.exists(path):
                    os.unlink(path)

                del trimtextures[textype]

            return trimtextures, decaltype

        return None, 'NONE'

    def get_trim_decalname(self, idx, name):
        nameRegex = re.compile(r"Trim [\d]*")

        if nameRegex.match(name):
            trimname = str(idx + 1).zfill(3)

        else:
            trimname = "%s_%s" % (str(idx + 1).zfill(3), name.strip())

        return trimname

    def remove_existing_trim_decals(self, context, sheet, trims, debug=False):

        col = sheet.DM.trimcollection

        if col:
            for obj in col.objects:
                print("INFO: Removing existing trim decal:", obj.name)
                bpy.data.meshes.remove(obj.data, do_unlink=True)

        log("INFO: Updating depsgraph", debug=debug)
        context.evaluated_depsgraph_get()
        log("  Updated!", debug=debug)

        uuids = [trim.uuid for trim in trims]
        mats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.uuid in uuids]

        for mat in mats:
            print("INFO: Removing existing trim decal material:", mat.name)
            remove_decalmat(mat, remove_textures=True, debug=False)


class CreateTrimSheetLibrary(bpy.types.Operator):
    bl_idname = "machin3.create_trimsheet_library"
    bl_label = "MACHIN3: Create Trim Sheet Library"
    bl_description = "Create Trim Sheet Library"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        if self.display_message:
            layout.label(text="There already is a Trim Sheet Library called '%s'!" % (self.sheet.DM.trimsheetname))
            layout.label(text="Do you want to proceed and replace it? This can not be undone!")

    @classmethod
    def poll(cls, context):
        if get_prefs().pil and context.mode == 'OBJECT':
            active = context.active_object

            if active and active.DM.istrimsheet:
                col = active.DM.trimcollection

                if col:
                    trim_decals = [obj for obj in col.objects if obj.DM.istrimdecal and obj.DM.trimsheetuuid == active.DM.trimsheetuuid and not obj.DM.isprojected and not obj.DM.issliced and not obj.parent and obj.active_material and not obj.active_material.DM.ismatched]

                    if trim_decals:
                        mat = active.active_material

                        if mat and mat.DM.istrimsheetmat:
                            return active.DM.trimsCOL and [trim_map for trim_map in active.DM.trimmapsCOL if trim_map.texture and trim_map.name in ['Normal', 'Color']]

    def invoke(self, context, event):
        self.sheet = context.active_object

        assetspath = get_prefs().assetspath
        self.sheetlibpath = os.path.join(assetspath, 'Trims', self.sheet.DM.trimsheetname)
        self.triminstantpath = get_instant_sheet_path(self.sheet)

        if not verify_instant_trimsheet(self.triminstantpath, self.sheet):
            return {'CANCELLED'}

        if os.path.exists(self.sheetlibpath):

            if os.path.exists(os.path.join(self.sheetlibpath, '.islocked')):
                popup_message("A Trim Sheet Library called '%s' exists and is force-locked, aborting." % self.sheet.DM.trimsheetname, title="Aborting")

                return {'CANCELLED'}

            else:
                if self.sheet.DM.trimsheetname in [lib.name for lib in get_lib()[1] if lib.istrimsheet and lib.islocked]:
                    popup_message(["A Trim Sheet Library called '%s' exists and is locked, aborting." % self.sheet.DM.trimsheetname, "Unlock the library to be able to replace it!"], title="Aborting")
                    return {'CANCELLED'}

            self.display_message = True
            return context.window_manager.invoke_props_dialog(self, width=400)

        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        sheet = self.sheet

        sheetlibpath = self.sheetlibpath
        triminstantpath = self.triminstantpath
        templatepath = get_templates_path()

        keep_sheet_uuid = context.scene.DM.create_trim_import_keep_sheet_uuid

        if keep_sheet_uuid:
            sheetuuid = sheet.DM.trimsheetuuid

        else:
            sheetuuid = str(uuid4())

        self.display_message = False

        if os.path.exists(sheetlibpath):
            existing = True

            print("\nReplacing existing trim sheet libary: %s" % sheet.DM.trimsheetname)
            rmtree(sheetlibpath)

        else:
            existing = False

            print("\nCreating trim sheet libary: %s" % sheet.DM.trimsheetname)

        makedir(sheetlibpath)

        for m in [get_version_filename_from_blender(), '.istrimsheet']:
            with open(os.path.join(sheetlibpath, m), 'w') as f:
                f.write('')

        data = load_json(os.path.join(triminstantpath, 'data.json'))
        data['uuid'] = sheetuuid
        save_json(data, os.path.join(sheetlibpath, 'data.json'))


        pngs = [os.path.join(triminstantpath, f) for f in os.listdir(triminstantpath) if f.endswith('.png')]

        for png in pngs:
            copy(png, sheetlibpath)

        col = sheet.DM.trimcollection

        trim_decals = {obj.DM.uuid: obj for obj in col.objects if obj.DM.istrimdecal and obj.DM.trimsheetuuid == sheet.DM.trimsheetuuid and not obj.DM.isprojected and not obj.DM.issliced and not obj.parent and obj.active_material and not obj.active_material.DM.ismatched}

        added_any_trim_decals = False

        for trim in sheet.DM.trimsCOL:
            decal = trim_decals.get(trim.uuid)

            if decal:
                decalpath = self.add_trim_decal_to_trimsheet_library(context, templatepath, sheetlibpath, sheet, decal, sheetuuid)

                if decalpath:
                    added_any_trim_decals = True

                    if trim.ispanel:
                        with open(os.path.join(decalpath, '.ispanel'), 'w') as f:
                            f.write('')


        if added_any_trim_decals:
            if existing:
                reload_trim_libraries(library=sheet.DM.trimsheetname)

            else:
                reload_trim_libraries()

        else:
            rmtree(sheetlibpath)

            if existing:
                print("WARNING: New trim sheet library, overwritting an existing one, ended up empty, removing it")
                reload_trim_libraries()

        return {'FINISHED'}

    def add_trim_decal_to_trimsheet_library(self, context, templatepath, sheetlibpath, sheet, trim_decal, sheetuuid):
        print("INFO: Adding decal '%s' to the '%s' trim sheet library" % (trim_decal.name, sheet.DM.trimsheetname))

        oldmat = trim_decal.active_material

        old_textures = get_decal_textures(oldmat)

        for textype, img in old_textures.items():
            if not os.path.exists(abspath(img.filepath)):
                print("WARNING: aborting decal %s as at least one of its texture paths can't be found: %s" % (trim_decal.name, img.filepath))
                return

        decal = trim_decal.copy()
        decal.data = trim_decal.data.copy()

        decalmat = append_material(templatepath, "TEMPLATE_%s" % oldmat.DM.decaltype, relative=False)
        decalmat.DM.istrimdecalmat = True
        decal.active_material = decalmat

        if oldmat.DM.decaltype == 'INFO':
            olddg = get_decalgroup_from_decalmat(oldmat)
            dg = get_decalgroup_from_decalmat(decalmat)

            if olddg and dg:
                for oldi, i in zip(olddg.inputs, dg.inputs):
                    i.default_value = oldi.default_value

        else:
            oldpg = get_parallaxgroup_from_decalmat(oldmat)
            pg = get_parallaxgroup_from_decalmat(decalmat)

            if oldpg and pg:
                pg.inputs[0].default_value = oldpg.inputs[0].default_value

            olddg = get_decalgroup_from_decalmat(oldmat)
            dg = get_decalgroup_from_decalmat(decalmat)

            if olddg and dg:
                oldemission = olddg.inputs['Emission Multiplier'].default_value
                dg.inputs['Emission Multiplier'].default_value = oldemission


        uuid = oldmat.DM.uuid
        creator = oldmat.DM.creator
        version = oldmat.DM.version

        set_props_and_node_names_of_decal("LIBRARY", "DECAL", decalobj=decal, uuid=uuid, version=version, creator=creator, trimsheetuuid=sheetuuid)

        decal.name = "LIBRARY_DECAL"
        decal.data.name = decal.name

        texture_paths = {}

        for idx, (textype, img) in enumerate(old_textures.items()):
            imgpath = abspath(img.filepath)

            if idx == 0:
                trimpath = os.path.dirname(imgpath)

                decalpath = makedir(os.path.join(sheetlibpath, os.path.basename(trimpath)))

            texture_paths[textype] = copy(imgpath, decalpath)

        textures = get_decal_textures(decalmat)

        for textype, img in textures.items():
            img.filepath = texture_paths[textype]

            img.DM.istrimdecaltex= True

        bpy.ops.scene.new(type='NEW')
        decalscene = context.scene
        decalscene.name = "Decal Asset"

        decalscene.collection.objects.link(decal)

        save_uuid(decalpath, uuid)

        save_blend(decal, decalpath, decalscene)

        render_thumbnail(context, decalpath, decal, decalmat, removeall=True)

        return decalpath



class LoadTrimSheetTextures(bpy.types.Operator):
    bl_idname = "machin3.load_trimsheet_textures"
    bl_label = "MACHIN3: Load Trim Sheet Textures"
    bl_description = "Load Textures to create a Trim Sheet from"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager

        wm.collecttrimtextures = True

        for img in bpy.data.images:
            i = wm.excludeimages.add()
            i.name = img.name

        bpy.ops.image.open('INVOKE_DEFAULT', display_type='THUMBNAIL', use_sequence_detection=False)

        return {'FINISHED'}


class ClearTrimSheetTextures(bpy.types.Operator):
    bl_idname = "machin3.clear_trimsheet_textures"
    bl_label = "MACHIN3: Clear Trim Sheet Textures"
    bl_description = "Clear Pool of Textures used for Trim Sheet Creation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        trimtexturespath = os.path.join(createpath, "trimtextures")

        images = [os.path.join(trimtexturespath, f) for f in os.listdir(trimtexturespath) if f != ".gitignore"]

        for img in images:
            os.unlink(img)

        reload_trimtextures()

        return {'FINISHED'}



class ClearTrimMap(bpy.types.Operator):
    bl_idname = "machin3.clear_trim_map"
    bl_label = "MACHIN3: Clear Trim Map"
    bl_description = "Remove Trim Sheet Texture"
    bl_options = {'REGISTER', 'UNDO'}

    idx: IntProperty()

    def execute(self, context):
        sheet = context.active_object
        trim_map = sheet.DM.trimmapsCOL[self.idx]

        trim_map.texture = ''
        trim_map.resolution = (1024, 1024)

        mat = sheet.active_material

        if mat:
            nodes = get_trimsheet_nodes(mat)
            maptype = trim_map.name.upper()
            node = nodes.get(maptype)

            if node:
                if node.image:
                    image = node.image

                    if os.path.exists(image.filepath):
                        os.unlink(image.filepath)

                    bpy.data.images.remove(image, do_unlink=True)

                node.mute = True

                if maptype not in ['HEIGHT', 'SUBSET', 'MATERIAL2']:
                    for link in node.outputs[0].links:
                        mat.node_tree.links.remove(link)

            if maptype == 'HEIGHT':
                node = nodes.get('PARALLAXGROUP')

                if node:
                    node.mute = True
                    node.inputs[0].default_value = 0.1

                trim_map.avoid_update = True
                trim_map.parallax_amount = 0.1

            elif maptype == 'ALPHA':
                mat.blend_method = 'OPAQUE'

                trim_map.avoid_update = True
                trim_map.connect_alpha = False


        if not any([trim_map.texture for trim_map in sheet.DM.trimmapsCOL]):
            oldres = tuple(sheet.DM.trimsheetresolution)

            if oldres != (1024, 1024):
                sheet.DM.trimsheetresolution = (1024, 1024)

                change_trimsheet_mesh_dimensions(sheet, *sheet.DM.trimsheetresolution)

                if sheet.DM.trimsCOL:
                    update_trim_locations(sheet.DM.trimsCOL, oldres, tuple(sheet.DM.trimsheetresolution))

                    sheet.select_set(True)

        create_trimsheet_json(sheet)

        return {'FINISHED'}


class UpdateTrimMap(bpy.types.Operator):
    bl_idname = "machin3.update_trim_map"
    bl_label = "MACHIN3: Update Trim Map"
    bl_description = "Update Trim Sheet Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sheet = context.active_object
        mapname = context.window_manager.trimtextures

        if mapname != 'None':
            idx, trim_maps, active = get_trim_map(sheet)
            active.texture = mapname

            context.window_manager.trimtextures = 'None'

            mat = sheet.active_material

            if mat and mat.DM.istrimsheetmat:
                nodes = get_trimsheet_nodes(mat)
                maptype = active.name.upper()
                node = nodes.get(maptype)

                if node:
                    assetspath = get_prefs().assetspath
                    createpath = os.path.join(assetspath, "Create")
                    trimtexturespath = os.path.join(createpath, "trimtextures")
                    sheetpath = get_instant_sheet_path(sheet)

                    mappath = os.path.join(trimtexturespath, mapname)

                    if os.path.exists(mappath):
                        path = copy(mappath, os.path.join(sheetpath, "%s.png" % (maptype.lower())))

                        img = bpy.data.images.load(path)
                        img.DM.istrimsheettex = True
                        img.DM.trimsheettextype = maptype
                        img.DM.trimsheetuuid = sheet.DM.trimsheetuuid
                        img.DM.trimsheetname = sheet.DM.trimsheetname
                        img.colorspace_settings.name = 'sRGB' if maptype in ['COLOR', 'EMISSION'] else 'Non-Color'
                        img.name = "%s.%s" % (maptype.lower(), sheet.DM.trimsheetname)

                        node.image = img
                        node.mute = False

                        if maptype == 'HEIGHT':
                            pg = nodes.get('PARALLAXGROUP')
                            if pg:
                                pg.mute = False

                        elif maptype not in ['ALPHA', 'SUBSET', 'MATERIAL2']:
                            tree = mat.node_tree
                            tsg = get_trimsheetgroup_from_trimsheetmat(mat)

                            i = '%s Map' % maptype.title() if maptype in ['NORMAL', 'CURVATURE'] else 'AO Map' if maptype == 'AO' else 'Base Color' if maptype == 'COLOR' else maptype.title()
                            tree.links.new(node.outputs[0], tsg.inputs[i])

                        active.resolution = img.size

                        if len([trim_map for trim_map in sheet.DM.trimmapsCOL if trim_map.texture]) == 1:
                            oldres = tuple(sheet.DM.trimsheetresolution)
                            if oldres != tuple(img.size):
                                sheet.DM.trimsheetresolution = img.size

                                change_trimsheet_mesh_dimensions(sheet, *img.size)

                                if sheet.DM.trimsCOL:
                                    update_trim_locations(sheet.DM.trimsCOL, oldres, tuple(sheet.DM.trimsheetresolution))

                                    sheet.select_set(True)


                        if maptype == 'COLOR' and not trim_maps['Alpha'].texture:
                            path = check_for_alpha(path)

                            if path:
                                trim_maps['Alpha'].texture = mapname

                                img = bpy.data.images.load(path)
                                img.DM.istrimsheettex = True
                                img.DM.trimsheettextype = 'ALPHA'
                                img.DM.trimsheetuuid = sheet.DM.trimsheetuuid
                                img.DM.trimsheetname = sheet.DM.trimsheetname
                                img.colorspace_settings.name = 'Non-Color'
                                img.name = "alpha.%s" % (sheet.DM.trimsheetname)

                                trim_maps['Alpha'].resolution = img.size

                                node = nodes.get('ALPHA')

                                if node:
                                    node.image = img
                                    node.mute = False

                        create_trimsheet_json(sheet)

        return {'FINISHED'}



class InitTrimSheetMaterial(bpy.types.Operator):
    bl_idname = "machin3.init_trimsheet_mat"
    bl_label = "MACHIN3: Init Trim Sheet Material"
    bl_description = "Initialize Trim Sheet Material\nALT: Avoid Unwrapping to Empty Trim"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'MESH' and not active.DM.isdecal and not active.DM.istrimsheet

    def invoke(self, context, event):
        active = context.active_object
        sheetdata = context.window_manager.trimsheets[context.scene.trimsheetlibs]

        set_trim_uv_channel(active)

        if active.mode == 'EDIT':
            sheetmat = self.init_sheetmat_in_edit_mode(active, sheetdata, unwrap_to_empty=not event.alt, debug=False)

        else:
            sheetmat = self.init_sheetmat_in_object_mode(active, sheetdata, unwrap_to_empty=not event.alt, debug=False)

        sheetidx = list(active.data.materials).index(sheetmat)

        if sheetidx != active.active_material_index:
            active.active_material_index = sheetidx

        return {'FINISHED'}

    def init_sheetmat_in_object_mode(self, active, sheetdata, unwrap_to_empty=True, debug=False):
        if not active.data.materials:
            reset_material_indices(active.data)

        unhide_deselect(active.data)

        slot_idx = active.active_material_index

        bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        faces = [f for f in bm.faces if f.material_index == slot_idx]

        if faces:

            for f in faces:
                f.select_set(True)

            log("faces selected via slot", debug=debug)

            mat_dict = get_trimsheet_material_from_faces(active, faces, sheetdata, force_new_material=True, debug=debug)

            assign_trimsheet_material(active, faces, mat_dict, add_material=True)
            sheetmat = mat_dict['sheetmat']

            bmesh.update_edit_mesh(active.data)

            if unwrap_to_empty:
                empty = get_empty_trim_from_sheetdata(sheetdata)

                if empty:
                    resolution = Vector(sheetdata['resolution'])
                    location = Vector(empty['location'])
                    scale = Vector(empty['scale'])

                    unwrap_to_empty_trim(active, resolution, location, scale)

        else:
            log("no faces selected", debug=True)
            sheetmat = append_and_setup_trimsheet_material(sheetdata)

            if active.active_material:
                log(" current slot is not assigned to any face, appending sheet mat to end of stack", debug=debug)
                active.data.materials.append(sheetmat)

            else:
                log(" slot is empty, filling in sheet mat", debug=debug)
                active.active_material = sheetmat

        bpy.ops.object.mode_set(mode='OBJECT')

        return sheetmat

    def init_sheetmat_in_edit_mode(self, active, sheetdata, unwrap_to_empty=True, debug=False):
        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        faces = [f for f in bm.faces if f.select]

        if faces:
            log("faces selected", debug=debug)

            mat_dict = get_trimsheet_material_from_faces(active, faces, sheetdata, force_new_material=True, debug=debug)
            sheetmat = mat_dict['sheetmat']
            index = mat_dict['index']

            if mat_dict['matchedmat']:

                log(" pbr material is matched, and sheet mat added to the end of the stack, faces asssigned to new sheet mat", debug=debug)
                assign_trimsheet_material(active, faces, sheetmat=sheetmat, index=len(active.material_slots), add_material=True)

            else:
                assign_trimsheet_material(active, faces, mat_dict, add_material=True)

                sheetmat = active.data.materials[index]

            bmesh.update_edit_mesh(active.data)

            if unwrap_to_empty:
                empty = get_empty_trim_from_sheetdata(sheetdata)

                if empty:
                    resolution = Vector(sheetdata['resolution'])
                    location = Vector(empty['location'])
                    scale = Vector(empty['scale'])

                    unwrap_to_empty_trim(active, resolution, location, scale)

        else:
            log("no faces selected", debug=debug)
            log(" just appended sheet mateterial to the end of the stack", debug=debug)

            sheetmat = append_and_setup_trimsheet_material(sheetdata)
            active.data.materials.append(sheetmat)

        return sheetmat


class SetupSubsets(bpy.types.Operator):
    bl_idname = "machin3.setup_trimsheet_subsets"
    bl_label = "MACHIN3: Setup Subsets"
    bl_description = "Setup Subsets in Trim Sheet Material's Node Tree\nALT: Use duplicate Trim Sheet Group to do so"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object and context.active_object.active_material and context.active_object.active_material.DM.istrimsheetmat:
            sheetmat = context.active_object.active_material
            sheetdata = get_sheetdata_from_uuid(sheetmat.DM.trimsheetuuid)
            if sheetdata:
                return 'SUBSET' in sheetdata['maps']

    def invoke(self, context, event):
        sheetmat = context.active_object.active_material
        tsg = get_trimsheetgroup_from_trimsheetmat(sheetmat)
        nodes = get_trimsheet_nodes(sheetmat, skip_parallax=True)
        subset = nodes['SUBSET'] if nodes.get('SUBSET') else None

        tree = sheetmat.node_tree

        if tsg and subset and len([node for node in tree.nodes if node.type == 'GROUP' and node.node_tree == tsg.node_tree]) == 1:
            for node in tree.nodes:
                node.select = False

            tree.nodes.active = None

            if event.alt and len([node for node in tree.nodes if node.type == 'GROUP' and node.node_tree == tsg.node_tree]) == 1:
                self.duplicate_tsg(sheetmat, tree, tsg, subset)

            else:
                self.add_color_mix_nodes(tree, tsg, subset)

        return {'FINISHED'}

    def duplicate_tsg(self, sheetmat, tree, tsg, subset):
        location = tsg.location

        dup = tree.nodes.new('ShaderNodeGroup')
        dup.node_tree = tsg.node_tree

        dup.location[0] = location[0]
        dup.location[1] = location[1] - (750 if bpy.app.version < (3, 0, 0) else 800)
        dup.width = tsg.width

        for idx, i in enumerate(tsg.inputs):
            if i.links:
                tree.links.new(i.links[0].from_socket, dup.inputs[idx])

        inputs = [i for i in dup.inputs if i.name in ['Base Color', 'Metallic', 'Roughness'] and not i.links]

        for i in inputs:
            if i.name == 'Base Color':
                i.default_value = (0.222, 0.222, 0.222, 1)
            elif i.name == 'Metallic':
                i.default_value = 1
            else:
                i.default_value = 0.25

        mixshader = tree.nodes.new('ShaderNodeMixShader')
        mixshader.location[0] = location[1] + 200
        mixshader.location[1] = location[1] - 650

        tree.links.new(subset.outputs[0], mixshader.inputs[0])
        tree.links.new(tsg.outputs[0], mixshader.inputs[1])
        tree.links.new(dup.outputs[0], mixshader.inputs[2])

        matoutput = get_material_output(sheetmat)
        if matoutput:
            tree.links.new(mixshader.outputs[0], matoutput.inputs[0])

            matoutput.location[0] = mixshader.location[0] + 200
            matoutput.location[1] = mixshader.location[1]

    def add_color_mix_nodes(self, tree, tsg, subset):
        location = tsg.location

        inputs = [i for i in tsg.inputs if i.name in ['Base Color', 'Metallic', 'Roughness'] and not i.links]

        for i in inputs:

            if bpy.app.version >= (3, 4, 0):
                mixnode = tree.nodes.new('ShaderNodeMix')
                mixnode.data_type = 'RGBA'

            else:
                mixnode = tree.nodes.new('ShaderNodeMixRGB')

            mixnode.location[0] = location[0] - 250

            if i.name == 'Base Color':
                offset = 200 if bpy.app.version >= (3, 4, 0) else 100
                mixnode.location[1] = location[1] + offset

                mixinB = get_mix_node_input(mixnode, inpt='B')
                mixinB.default_value = (0.222, 0.222, 0.222, 1)

            elif i.name == 'Metallic':
                offset = 50 if bpy.app.version >= (3, 4, 0) else 100

                mixnode.location[1] = location[1] - offset

                mixinB = get_mix_node_input(mixnode, inpt='B')
                mixinB.default_value = (1, 1, 1, 1)
            else:
                mixnode.location[1] = location[1] - 300

                mixinB = get_mix_node_input(mixnode, inpt='B')
                mixinB.default_value = (0.25, 0.25, 0.25, 1)

            if i.type == 'RGBA':
                mixinA = get_mix_node_input(mixnode, inpt='A')
                mixinA.default_value = i.default_value

            elif i.type == 'VALUE':
                mixinA = get_mix_node_input(mixnode, inpt='A')
                mixinA.default_value = (i.default_value, i.default_value, i.default_value, 1)

            tree.links.new(get_mix_node_output(mixnode), i)

            tree.links.new(subset.outputs[0], get_mix_node_input(mixnode, inpt='Factor'))



class RemoveInstantTrimSheet(bpy.types.Operator):
    bl_idname = "machin3.remove_instant_trim_sheet"
    bl_label = "MACHIN3: Remove Selected Instant Trim Sheet"
    bl_description = "Remove Selected Instant Trim Sheet"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        layout.label(text="This removes the selected Trim Sheet from the scene and all its textures from disk!")
        layout.label(text="Are you sure? This cannot be undone!")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object and context.active_object.DM.istrimsheet

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def execute(self, context):
        uuid = context.active_object.DM.trimsheetuuid
        idx = context.active_object.DM.trimsheetindex

        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, 'Create')
        triminstantpath = os.path.join(createpath, 'triminstant')
        sheetpath = os.path.join(triminstantpath, "%s_%s" % (idx, uuid))

        if os.path.exists(sheetpath):
            rmtree(sheetpath)

        col = context.active_object.DM.trimcollection

        if col:
            bpy.data.collections.remove(col, do_unlink=True)

        trimdecals = [obj for obj in bpy.data.objects if obj.DM.istrimdecal and obj.DM.trimsheetuuid == uuid]

        for decal in trimdecals:
            mat = get_decalmat(decal)

            if mat:
                remove_decalmat(mat, remove_textures=True, debug=False)

            bpy.data.meshes.remove(decal.data, do_unlink=True)

        sheets = [obj for obj in bpy.data.objects if obj.DM.istrimsheet and obj.DM.trimsheetuuid == uuid]

        for sheet in sheets:
            bpy.data.meshes.remove(sheet.data, do_unlink=True)

        sheetmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat and mat.DM.trimsheetuuid == uuid]

        for mat in sheetmats:
            remove_trimsheetmat(mat)

        textures = [img for img in bpy.data.images if img.DM.istrimsheettex and img.DM.trimsheetuuid == uuid]

        for img in textures:
            bpy.data.images.remove(img, do_unlink=True)

        update_instanttrimsheetcount()

        return {'FINISHED'}
