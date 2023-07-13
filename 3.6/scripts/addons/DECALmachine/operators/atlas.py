import bpy
from bpy.props import EnumProperty
import bmesh
from mathutils import Vector, Matrix
import os
from shutil import copy, rmtree
from math import sqrt
from uuid import uuid4
from time import time
from .. utils.decal import get_decals, get_decal_library_and_name_from_uuid
from .. utils.registration import get_prefs, get_path, get_templates_path, register_atlases, update_instantatlascount, get_addon, get_addon_prefs, get_version_as_float
from .. utils.system import makedir, get_new_directory_index, save_json, splitpath, load_json
from .. utils.atlas import prepare_source_textures, initiate_atlas, kivy, blackpawn, create_atlas_dummies, update_atlas_dummy, update_atlas_obj, refresh_atlas_trims
from .. utils.atlas import get_instant_atlas_path, create_atlas_json, get_lower_and_upper_atlas_resolution, get_atlas_images_from_path, get_atlasdata_from_decaluuid, get_atlasdata_from_atlas, get_atlasdata_from_atlasmat, get_textypes_from_atlasmats, verify_channel_pack
from .. utils.atlas import layout_atlas
from .. utils.pil import get_image_size, scale_image, create_dummy_texture, create_atlas, get_delta, create_channel_packed_atlas_map, create_smoothness_map, create_subset_occlusion_map, create_white_height_map, split_ao_curv_height, split_masks
from .. utils.ui import popup_message
from .. utils.math import img_coords_to_trimmx, flatten_matrix, trimmx_to_img_coords, mul, create_trimmx_from_location_and_scale
from .. utils.append import append_material
from .. utils.material import get_unique_by_uuid_decalmats_from_decals, set_atlasdummy_texture_paths, set_node_names_of_atlas_material, get_atlas_textures, get_parallax_amount, get_atlas_nodes, append_and_setup_atlas_material, remove_atlasmat, remove_decalmat
from .. utils.library import get_atlas
from .. utils.trim import get_trim
from .. utils.uv import get_selection_uv_bbox, get_trim_uv_bbox, verify_uv_transfer
from .. utils.collection import get_atlas_collection
from .. items import textype_color_mapping_dict, create_atlas_mode_items


class CreateAtlas(bpy.types.Operator):
    bl_idname = "machin3.create_atlas"
    bl_label = "MACHIN3: Create Atlas"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(name="Atlasing Mode", items=create_atlas_mode_items, default='INITIATE')

    @classmethod
    def poll(cls, context):
        if get_prefs().pil and context.mode == 'OBJECT':
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None

            if atlas:
                if [atlas] == context.selected_objects:
                    return True

            sel = context.selected_objects
            sources = sel if sel else context.visible_objects
            return [obj for obj in sources if obj.DM.isdecal and not obj.DM.preatlasmats]

    @classmethod
    def description(cls, context, properties):
        if properties.mode == 'INITIATE':
            return "Create new Decal Atlas"
        elif properties.mode == 'REPACK':
            return "Re-arrange Decals, aiming for a tightest packing solution"
        elif properties.mode == 'TWEAK':
            return "Apply manual changes and re-create Atlas Textures accordingly"

    def execute(self, context):
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, 'Create')
        atlasinstantpath = os.path.join(createpath, 'atlasinstant')
        templatepath = get_templates_path()

        dm = context.scene.DM
        padding = dm.create_atlas_padding
        size_mode = dm.create_atlas_size_mode
        resolution = dm.create_atlas_resolution
        resolution_increase = dm.create_atlas_resolution_increase
        prepack = dm.create_atlas_prepack
        compensate = dm.create_atlas_compensate_height
        normalize = dm.create_atlas_normalize_height
        normalize_factor = 1

        if self.mode == 'INITIATE':
            decals = get_decals(context)

            decalmats = get_unique_by_uuid_decalmats_from_decals(decals)

            if decalmats:
                idx = get_new_directory_index(atlasinstantpath)
                uuid = str(uuid4())
                atlas_type = dm.create_atlas_type

                resolution = resolution if size_mode == 'SPECIFIC' else None

                atlaspath = makedir(os.path.join(atlasinstantpath, "%s_%s" % (idx, uuid)))
                sourcespath = makedir(os.path.join(atlaspath, "sources"))

                sources = prepare_source_textures(atlas_type, sourcespath, decalmats, sources={}, prepack=prepack, debug=False)

                if sources:
                    solution = self.pack_atlas(sources, atlas_type, resolution=resolution, padding=padding, resolution_increase=resolution_increase, debug=False)

                    if atlas_type in ['NORMAL', 'COMBINED']:
                        normalize_factor = self.set_height_adjustment(sources, solution, compensate=compensate, normalize=normalize, debug=False)

                    atlas_images = self.create_atlas_images(atlaspath, sources, solution)

                    atlas = layout_atlas(context, templatepath, sources, solution, atlas_images, idx, uuid, normalize_factor=normalize_factor)

                    maps = self.create_maps_dict(atlas, atlas_images)
                    create_atlas_json(atlaspath, atlas, maps, debug=False)

                    if context.scene.DM.debug:
                        save_json(sources, os.path.join(sourcespath, 'sources.json'))
                        save_json(solution, os.path.join(atlaspath, 'solution.json'))

                else:
                    rmtree(atlaspath)
                    popup_message("Atlas could not be created because no source images could be found", title="Atlas Creation Aborted")


        elif self.mode in ['REPACK', 'TWEAK']:
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None

            if atlas:
                sources = atlas.DM.get('sources')
                prev_solution = atlas.DM.get('solution')
                atlas_type = prev_solution['type']

                atlas.DM.atlasnewdecaloffset = 10

                if sources and prev_solution:
                    if self.validate_source_textures(context, assetspath, atlasinstantpath, atlas, sources):
                        atlaspath = makedir(os.path.join(atlasinstantpath, "%s_%s" % (atlas.DM.atlasindex, atlas.DM.atlasuuid)))

                        if self.mode == 'REPACK':

                            resolution = resolution if size_mode == 'SPECIFIC' else None

                            sources, solution = self.repack_atlas(atlas, resolution=resolution, padding=padding, resolution_increase=resolution_increase, debug=False)

                        elif self.mode == 'TWEAK':

                            sources, solution = self.tweak_atlas(atlas, resolution=resolution if prev_solution['resolution'][0] != resolution else None)

                        solution['type'] = atlas_type

                        if atlas_type in ['NORMAL', 'COMBINED']:

                            self.update_parallax(sources)

                            normalize_factor = self.set_height_adjustment(sources, solution, compensate=compensate, normalize=normalize)

                        atlas_images = self.create_atlas_images(atlaspath, sources, solution)

                        self.update_atlas_layout(context, sources, solution, atlas, normalize_factor)

                        maps = self.create_maps_dict(atlas, atlas_images)
                        create_atlas_json(atlaspath, atlas, maps, debug=False)

                        if context.scene.DM.debug:
                            sourcespath = makedir(os.path.join(atlaspath, "sources"))
                            save_json(sources, os.path.join(sourcespath, 'sources.json'))
                            save_json(solution, os.path.join(atlaspath, 'solution.json'))

                    else:
                        popup_message("Atlas could not be %s, because at least one of the packed decals could no longer be found among the registered decal or trim sheet libraries." % ('re-packed' if self.mode == 'REPACK' else 'tweaked'), title="Atlas %s Aborted" % ('Repacking' if self.mode == 'REPACK' else 'Tweaking'))

        update_instantatlascount()

        return {'FINISHED'}

    def create_maps_dict(self, atlas, atlas_images):

        maps = {}

        for textype, path in atlas_images.items():
            maps[textype] = {'texture': os.path.basename(path),
                             'resolution': tuple(atlas.DM.atlasresolution)}

            if textype == 'HEIGHT':
                maps[textype]['parallax_amount'] = atlas.DM.atlasdummyparallax

            elif textype == 'ALPHA':
                maps[textype]['connect_alpha'] = False

        return maps

    def update_parallax(self, sources):

        materials = {}

        for mat in bpy.data.materials:
            if mat.DM.isdecalmat and mat.DM.version and get_version_as_float(mat.DM.version) >= 2:
                if mat.DM.uuid in sources and mat.DM.uuid not in materials:

                    materials[mat.DM.uuid] = mat

        for uuid, decal in sources.items():
            if uuid in materials:
                parallax = get_parallax_amount(materials[uuid])

                if parallax != decal['parallax']:
                    print("INFO: %s's parallax has changed from" % (decal['name']), decal['parallax'], "to", parallax)
                    sources[uuid]['parallax'] = parallax

        return materials

    def update_atlas_layout(self, context, sources, solution, atlas, normalize_factor):

        resolution = solution['resolution']

        update_atlas_obj(atlas, resolution)

        for trim in atlas.DM.trimsCOL:
            coords = solution['boxes'][trim.uuid]['coords']
            dimensions = solution['boxes'][trim.uuid]['dimensions']

            trimmx = img_coords_to_trimmx(coords, dimensions, resolution)
            trim.mx = flatten_matrix(trimmx)

            if trim.dummy:
                update_atlas_dummy(atlas, trim, update_uvs=True)

        new_trims = [trim for trim in atlas.DM.trimsCOL if not trim.dummy]

        if new_trims:
            dummies = create_atlas_dummies(context, atlas, trims=new_trims)

            for dummy in dummies:
                dummy.data.materials.append(atlas.DM.atlasdummymat)

        textures = [img for img in bpy.data.images if img.DM.isatlasdummytex and img.DM.uuid == atlas.DM.uuid]

        for img in textures:
            img.reload()

        nodes = get_atlas_nodes(atlas.DM.atlasdummymat, skip_parallax=True)

        for node in nodes.values():
            node.mute = False

        if solution['type'] in ['NORMAL', 'COMBINED']:
            atlas.DM.atlasdummyparallax = 0.1 / normalize_factor

        atlas.DM['sources'] = sources
        atlas.DM['solution'] = solution

    def tweak_atlas(self, atlas, resolution=None):

        sources = atlas.DM['sources'].to_dict()
        solution = atlas.DM['solution'].to_dict()


        for trim in atlas.DM.trimsCOL:

            top_left, dimensions = trimmx_to_img_coords(trim.mx, atlas.DM.atlasresolution)

            sources[trim.uuid]['size'] = dimensions

            solution['boxes'][trim.uuid]['coords'] = top_left
            solution['boxes'][trim.uuid]['dimensions'] = dimensions


        if resolution:
            for trim in atlas.DM.trimsCOL:
                trimmx = trim.mx

                offsetx = (resolution / 2 - atlas.DM.atlasresolution[0] / 2) / 1000
                offsety = (resolution / 2 - atlas.DM.atlasresolution[1] / 2) / 1000

                location = trimmx.col[3][:2]
                location = (location[0] - offsetx, location[1] + offsety)

                factorx = atlas.DM.atlasresolution[0] / resolution
                factory = atlas.DM.atlasresolution[1] / resolution
                scale = (trimmx[0][0] * factorx, trimmx[1][1] * factory)

                trimmx.col[3][:2] = location
                trimmx[0][0] = scale[0]
                trimmx[1][1] = scale[1]

                top_left, dimensions = trimmx_to_img_coords(trimmx, [resolution, resolution])

                if trim.ispanel and trim.prepack in ['STRETCH', 'REPEAT']:
                    dimensions[0] = resolution

                solution['boxes'][trim.uuid]['coords'] = top_left
                solution['boxes'][trim.uuid]['dimensions'] = dimensions

                sources[trim.uuid]['size'] = dimensions

            solution['resolution'] = [resolution, resolution]

        return sources, solution

    def repack_atlas(self, atlas, resolution=None, padding=4, resolution_increase=10, debug=False):

        sources = atlas.DM['sources'].to_dict()

        for trim in atlas.DM.trimsCOL:
            _, dimensions = trimmx_to_img_coords(trim.mx, atlas.DM.atlasresolution)
            sources[trim.uuid]['size'] = dimensions

        return sources, self.pack_atlas(sources, resolution=resolution, padding=padding, resolution_increase=resolution_increase, debug=debug)

    def validate_source_textures(self, context, assetspath, atlasinstantpath, atlas, sources):

        def rebuild_path(path):
            if path:
                split = splitpath(path)

                if split[-4] in ['Decals', 'Trims']:
                    newpath = os.path.join(assetspath, *split[-4:])

                elif split[-3] == 'sources':
                    newpath = os.path.join(assetspath, 'Create', *split[-5:])

                elif split[-3] == 'decalinstant':
                    newpath = os.path.join(assetspath, 'Create', *split[-3:])

                if path != newpath:
                    path = newpath
                    atlas.DM['sources'][uuid]['textures'][textype] = newpath
                    print("INFO: stored atlas source path has changed, but was updated:", path)

            return path


        for uuid, decal in sources.items():

            paths = decal['textures']
            orig_paths = decal['original_textures']

            for textype, path in paths.items():

                path = rebuild_path(path)
                orig_path = rebuild_path(orig_paths[textype])

                if not os.path.exists(path):

                    atlaspath = makedir(os.path.join(atlasinstantpath, "%s_%s" % (atlas.DM.atlasindex, atlas.DM.atlasuuid)))
                    decalpath = makedir(os.path.join(atlaspath, "sources", uuid))

                    if path == orig_path:
                        print("WARNING: decal texture source and original texture no longer exist, aborting:", path)
                        return False

                    elif os.path.exists(orig_path):
                        print("WARNING: decal texture source does not exist, re-creating:", path)

                        if get_image_size(orig_path) != tuple(decal['size']):
                            copy(orig_path, path)

                            print("INFO: scaling up %s map to %dx%d" % (textype, *decal['size']))
                            scale_image(path, size=tuple(decal['size']))

                    elif not orig_path:
                        print("WARNING: re-creating dummy %s map at: %s" % (textype, path))
                        create_dummy_texture(decalpath, "%s.png" % textype.lower(), mode='RGB', resolution=tuple(decal['size']), color=textype_color_mapping_dict[textype])

        return True

    def create_atlas_images(self, atlaspath, sources, solution):

        textypes = list(list(sources.values())[0]['textures'].keys())

        paths = {}

        print()

        for textype in textypes:
            path = create_atlas(atlaspath, sources, solution, textype)
            paths[textype] = path

            print("INFO: Created %s atlas image: %s" % (textype, path))

            if textype in ['AO_CURV_HEIGHT', 'MASKS']:
                print("INFO: Splitting %s map" % (textype))

                eval("split_%s(atlaspath, path, paths)" % (textype.lower()))

                print("INFO: Removed %s map" % (textype))

                os.unlink(path)
                del paths[textype]

        if solution['type'] == 'INFO':
            for textype in ['SUBSET', 'MATERIAL2']:
                path = paths[textype]

                os.unlink(path)
                del paths[textype]

        return paths

    def set_height_adjustment(self, sources, solution, compensate, normalize, debug=False):

        atlassize = solution['resolution'][0]

        for uuid, decal in sources.items():
            path = decal['textures']['AO_CURV_HEIGHT']

            if os.path.exists(path):
                parallax = decal['parallax']
                ispanel = decal['ispanel']
                isstretched = decal['prepack'] in ['STRETCH', 'REPEAT']

                parallax_factor = parallax / 0.1

                if compensate:
                    box = solution['boxes'][uuid]

                    if ispanel and isstretched:
                        size_factor = ((box['dimensions'][1] / sources[uuid]['original_size'][1]) * (max(*sources[uuid]['original_size'])) / atlassize)
                    else:
                        size_factor = max(*box['dimensions']) / atlassize

                else:
                    size_factor = 1

                sources[uuid]['height'] = parallax_factor * size_factor

                if debug:
                    print()
                    print(decal['name'])
                    print(" parallax", parallax_factor)
                    print(" size", size_factor)

        if normalize:
            deltas = []

            for uuid, decal in sources.items():
                path = decal['textures']['AO_CURV_HEIGHT']
                amount = decal['height']

                delta = get_delta(path, amount=amount)
                deltas.append(delta)

            min_delta = min(deltas)
            normalize_factor = -128 / (min_delta - 128)

            if debug:
                print()
                print("Normalizing", normalize_factor)

            for uuid in sources:
                sources[uuid]['height'] *= normalize_factor

            return normalize_factor
        return 1

    def pack_atlas(self, sources, atlas_type=None, resolution=None, padding=4, resolution_increase=10, debug=False):

        minres = round(sqrt(sum(mul(*decal['size']) for decal in sources.values())))
        minarea = minres * minres

        if resolution:
            print("\nINFO: The target resolution is %dx%d.\n" % (resolution, resolution))

            startres = minres = resolution

        else:
            print("\nINFO: The minimally required resolution to fit the decals into a single atlas based on texture area is %dx%d.\n" % (minres, minres))

            startres = minres

        solutions = []
        atlasing_start = time()

        prepacked_sources = self.get_prepacked_sources(sources, debug=False)

        for sort in ['WIDTH', 'HEIGHT', 'AREA']:
            sorted_sources = self.sort_sources(sources, sort_by=sort, debug=False)

            for algo in ['KIVY', 'BLACKPAWN', 'BLACKPAWNALT']:
                packing_start = time()
                completed = False

                print("INFO: Starting atlas pack, sorted by %s, algorithm %s." % (sort, algo))

                c = 0
                while not completed:
                    c += 1

                    minres, free_boxes, full_boxes = initiate_atlas(minres, padding, prepacked_sources=prepacked_sources)

                    if debug:
                        print()
                        print("  starting atlas", c, minres, minres)
                        print(" ", free_boxes)
                        print(" ", full_boxes)

                    for uuid, decal in sorted_sources:
                        name = decal['name']
                        img_w, img_h = decal['size']

                        if debug:
                            print()
                            print("  decal", name, img_w, img_h)

                        for box in free_boxes:
                            if debug:
                                print("   trying free box %s" % (str(box)))

                            if (img_w + padding) <= box[2] and (img_h + padding) <= box[3]:
                                if debug:
                                    print("   inserting %s (%d, %d) into free_box (%d, %d)" % (name, img_w, img_h, box[2], box[3]))

                                free_boxes.remove(box)

                                kivy(free_boxes, padding, box, img_w, img_h) if algo == 'KIVY' else blackpawn(free_boxes, padding, box, img_w, img_h) if algo == 'BLACKPAWN' else blackpawn(free_boxes, padding, box, img_w, img_h, alternative=True)

                                free_boxes = sorted(free_boxes, key=lambda b: b[2] if sort == 'WIDTH' else b[3] if sort == 'HEIGHT' else b[2] * b[3])

                                full_boxes[uuid] = {'coords': [box[0] + round(padding / 2), box[1] + round(padding / 2)],
                                                    'dimensions': [img_w, img_h]}
                                break

                        if uuid not in full_boxes:
                            if debug:
                                print("  couldn't insert decal", name, "need to restart packing with bigger resolution, increasing by", resolution_increase)
                            minres += resolution_increase
                            break

                    if len(full_boxes) == len(sources):

                        efficiency = minarea / (minres * minres) * 100

                        gap = minres - max(box['coords'][1] + box['dimensions'][1] for box in full_boxes.values())

                        solutions.append((full_boxes, float("%0.4f" % efficiency), gap, (minres, minres), sort, algo, padding))

                        print("INFO: Atlas is complete after %d attempts and %f seconds. Pack is %0.1f%% effcient, at %dx%d.\n" % (c, time() - packing_start, efficiency, minres, minres))

                        minres = startres
                        completed = True

        best_solution = max(solutions, key=lambda s: (s[1], s[2]))
        solution = {'boxes': best_solution[0],
                    'efficiency': best_solution[1],
                    'gap': best_solution[2],
                    'resolution': best_solution[3],
                    'sort': best_solution[4],
                    'algo': best_solution[5],
                    'padding': best_solution[6]}

        if atlas_type:
            solution['type'] = atlas_type

        print("\nINFO: Atlasing completed after %f seconds. Best solution is %0.1f%% efficient, at %dx%d, sorted by %s using %s algorithm with padding %d." % (time() - atlasing_start, solution['efficiency'], *solution['resolution'], solution['sort'], solution['algo'], solution['padding']))

        return solution

    def get_prepacked_sources(self, sources, debug=False):

        prepacked_sources = [(uuid, decal) for uuid, decal in sources.items() if decal['ispanel'] and decal['prepack'] in ['STRETCH', 'REPEAT']]

        if debug:
            for uuid, decal in prepacked_sources:
                print()
                print(uuid)
                print(decal['name'], decal['ispanel'], decal['prepack'])

        return prepacked_sources

    def sort_sources(self, sources, sort_by='WIDTH', debug=False):

        sorted_sources = sorted([(uuid, decal) for uuid, decal in sources.items() if decal['prepack'] == 'NONE'], key=lambda x: x[1]['size'][0] if sort_by == 'WIDTH' else x[1]['size'][1] if sort_by == 'HEIGHT' else mul(*x[1]['size']), reverse=True)

        if debug:
            for uuid, decal in sorted_sources:
                name = decal['name']
                size = decal['size']

                print()
                print(uuid)
                print(name, size, mul(*size))

        return sorted_sources


class ImportAtlas(bpy.types.Operator):
    bl_idname = "machin3.import_atlas"
    bl_label = "MACHIN3: Import Atlas"
    bl_description = "Import an existing Atlas/Trim Sheet created in DECALmachine"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            importpath = context.scene.DM.create_atlas_import_path
            jsonpath = os.path.join(importpath, "data.json")
            return os.path.exists(jsonpath)

    def execute(self, context):
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        atlasinstantpath = os.path.join(createpath, "atlasinstant")
        templatepath = get_templates_path()

        importpath = context.scene.DM.create_atlas_import_path
        jsonpath = os.path.join(importpath, "data.json")

        data = load_json(jsonpath)

        trims = [trim for trim in data['trims'] if not trim.get('isempty')]

        if self.verify_trims(context, trims):
            name = data['name']

            if not data.get('isatlas'):
                name = name.replace('Sheet', 'Atlas').replace('sheet', 'atlas').replace('SHEET', 'ATLAS')

                if name == data['name']:
                    name += " Atlas"

            atlasuuid = data['uuid']
            resolution = data['resolution']
            maps = data['maps']

            index = get_new_directory_index(atlasinstantpath)

            atlaspath = makedir(os.path.join(atlasinstantpath, "%s_%s" % (index, atlasuuid)))
            sourcespath = makedir(os.path.join(atlaspath, "sources"))

            atlas_type = 'COMBINED' if all(textype in maps for textype in ['COLOR', 'NORMAL']) else 'NORMAL' if 'NORMAL' in maps else 'INFO' if 'COLOR' in maps else None

            if atlas_type:

                decalmats, trimsdict = self.get_decalmats_from_trims(context, assetspath, trims)

                sources = prepare_source_textures(atlas_type, sourcespath, decalmats, sources={}, debug=False)

                self.update_sources(sources, trimsdict)

                solution = self.create_solution_from_trims(atlas_type, name, atlasuuid, resolution, trimsdict, sources)

                atlas_images, parallax = self.get_atlas_images(importpath, atlaspath, maps, debug=False)

                layout_atlas(context, templatepath, sources, solution, atlas_images, index, atlasuuid, name=name, normalize_factor=0.1 / parallax if parallax else 1)

                for mat in decalmats.values():
                    remove_decalmat(mat, remove_textures=True, debug=False)

                if context.scene.DM.debug:
                    save_json(sources, os.path.join(sourcespath, 'sources.json'))
                    save_json(solution, os.path.join(atlaspath, 'solution.json'))

            update_instantatlascount()


        else:
            popup_message("Atlas can't be imported, because it references Decals that aren't registered!")


        return {'FINISHED'}

    def get_atlas_images(self, importpath, atlaspath, maps, debug=False):

        atlas_images = {}
        parallax = None

        for textype, map in maps.items():
            src = os.path.join(importpath, '%s.png' % (textype.lower()))
            dst = os.path.join(atlaspath, '%s.png' % (textype.lower()))

            if os.path.exists(src):
                copy(src, dst)
                atlas_images[textype] = dst

                if textype == 'HEIGHT':
                    parallax = map.get('parallax_amount')

        if debug:
            for textype, path in atlas_images.items():
                print(textype, path)

        return atlas_images, parallax

    def create_solution_from_trims(self, atlas_type, name, atlasuuid, resolution, trims, sources):
        solution = {'boxes': {},
                    "efficiency": 0,
                    "gap": 0,
                    "resolution": resolution,
                    "sort": "NONE",
                    "algo": "NONE",
                    "padding": 4,
                    "type": atlas_type,
                    "name": name,
                    "uuid": atlasuuid}

        for uuid, trim in trims.items():
            if trim.get('coords') and trim.get('dimensions'):
                coords = trim['coords']
                dimensions = trim['dimensions']

            else:
                trimmx = create_trimmx_from_location_and_scale(trim['location'], trim['scale'])
                coords, dimensions = trimmx_to_img_coords(trimmx, resolution)

                dimensions = (sources[uuid]['original_size'])

            solution['boxes'][uuid] = {'coords': coords,
                                       'dimensions': dimensions}

        return solution

    def update_sources(self, sources, trimsdict):

        for uuid, decal in sources.items():
            if decal.get('ispanel'):
                trim = trimsdict[uuid]

                if trim.get('repetitions') and trim.get('repetitions') > 1:
                    sources[uuid]['repetitions'] = trim.get('repetitions')
                    sources[uuid]['prepack'] = 'REPEAT'

                elif trim.get('location')[0] == 0 and trim.get('scale')[0] == 1:
                    sources[uuid]['prepack'] = 'STRETCH'

    def get_decalmats_from_trims(self, context, assetspath, trims):

        decalmats = {}
        trimsdict = {}

        for trim in trims:
            uuid = trim.get('uuid')

            trimsdict[uuid] = trim

            name, library, libtype = get_decal_library_and_name_from_uuid(context, uuid)
            decalpath = os.path.join(assetspath, libtype, library, name)
            blendpath = os.path.join(decalpath, 'decal.blend')

            mat = append_material(blendpath, 'LIBRARY_DECAL')
            mat.DM.decalname = "%s_%s" % (library, name)

            decalmats[uuid] = mat

        return decalmats, trimsdict

    def verify_trims(self, context, trims):

        decaluuids = context.window_manager.decaluuids

        for trim in trims:
            if trim.get('uuid') not in decaluuids:
                print("WARNING: Decal with UUID %s is missing, aborting Atlas import!" % trim.get('uuid'))
                return False
        return True


class AddDecalsToAtlas(bpy.types.Operator):
    bl_idname = "machin3.add_decals_to_atlas"
    bl_label = "MACHIN3: Add Decals to Atlas"
    bl_description = "Add selected Decals to active Atlas"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None

            if atlas:
                sources = atlas.DM.get('sources')
                solution = atlas.DM.get('solution')

                if sources and solution:
                    return [obj for obj in context.selected_objects if obj.DM.isdecal and obj.DM.uuid not in sources]

    def execute(self, context):
        dm = context.scene.DM
        prepack = dm.create_atlas_prepack

        atlas = context.active_object

        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, 'Create')
        atlasinstantpath = os.path.join(createpath, 'atlasinstant')
        atlaspath = makedir(os.path.join(atlasinstantpath, "%s_%s" % (atlas.DM.atlasindex, atlas.DM.atlasuuid)))
        sourcespath = makedir(os.path.join(atlaspath, "sources"))
        templatepath = get_templates_path()

        sources = atlas.DM.get('sources').to_dict()
        solution = atlas.DM.get('solution').to_dict()
        prev_atlas_type = solution['type']

        decals = [obj for obj in context.selected_objects if obj.DM.isdecal and obj.DM.uuid not in sources]
        decalmats = self.get_new_decalmats(decals, sources, debug=False)

        for mat in decalmats.values():
            print("INFO: Adding decal %s to atlas." % (mat.DM.decalname))

        atlas_type = self.update_atlas_type(sourcespath, prev_atlas_type, decalmats, sources, solution)

        sources = prepare_source_textures(atlas_type, sourcespath, decalmats, sources=sources, prepack=prepack, debug=False)

        sources = dict(sorted([(uuid, decal) for uuid, decal in sources.items()], key=lambda x: x[1]['name']))

        self.update_solution(atlas, decalmats, sources, solution)

        atlas.DM['sources'] = sources
        atlas.DM['solution'] = solution

        refresh_atlas_trims(atlas)

        if atlas_type != prev_atlas_type:
            self.replace_atlasdummymat(atlas, prev_atlas_type, templatepath, atlaspath)

        for decal in decals:
            decal.select_set(False)

        return {'FINISHED'}

    def replace_atlasdummymat(self, atlas, prev_atlas_type, templatepath, atlaspath):

        dummymat = atlas.DM.atlasdummymat

        if dummymat:
            textures = get_atlas_textures(dummymat)
            remove_atlasmat(dummymat)

            for img in textures.values():
                bpy.data.images.remove(img, do_unlink=True)


        dummymat = append_material(templatepath, "TEMPLATE_ATLASDUMMY")

        if dummymat:
            atlas.DM.atlasdummymat = dummymat

            dummymat.name = atlas.name
            dummymat.DM.atlasname = atlas.DM.atlasname
            dummymat.DM.atlasuuid = atlas.DM.atlasuuid

            atlas_images = {textype: os.path.join(atlaspath, "%s.png" % (textype.lower())) for textype in ['ALPHA', 'AO', 'COLOR', 'CURVATURE', 'EMISSION', 'HEIGHT', 'NORMAL', 'SUBSET']}

            set_atlasdummy_texture_paths(dummymat, atlas_images)

            set_node_names_of_atlas_material(dummymat, atlas.DM.atlasname, dummy=True)

            nodes = get_atlas_nodes(dummymat, skip_height=True)

            for nodetype, node in nodes.items():
                if nodetype == 'PARALLAXGROUP':
                    node.inputs[0].default_value = atlas.DM.atlasdummyparallax

                    if prev_atlas_type == 'INFO':
                        node.mute = True

                elif node.type == 'TEX_IMAGE':
                    img = node.image
                    if img:
                        img.DM.atlasname = atlas.DM.atlasname
                        img.DM.atlasuuid = atlas.DM.atlasuuid

                        if prev_atlas_type == 'INFO' and nodetype in ['AO', 'CURVATURE', 'NORMAL', 'SUBSET']:
                            node.mute = True

                        elif prev_atlas_type == 'NORMAL' and nodetype == 'COLOR':
                            node.mute = True


            for trim in atlas.DM.trimsCOL:
                if trim.dummy:
                    trim.dummy.material_slots[0].material = dummymat

    def update_solution(self, atlas, decalmats, sources, solution):

        offset = atlas.DM.atlasnewdecaloffset

        for uuid in sorted([uuid for uuid, mat in decalmats.items()], key=lambda x: decalmats[x].DM.decalname):
            box = {'coords': [solution['resolution'][0] + offset, 0],
                   'dimensions': sources[uuid]['size']}

            solution['boxes'][uuid] = box

            offset += box['dimensions'][0] + 10

        atlas.DM.atlasnewdecaloffset = offset

    def update_atlas_type(self, sourcespath, atlas_type, decalmats, sources, solution):

        if atlas_type in ['NORMAL', 'INFO']:
            update_type = False

            for mat in decalmats.values():
                if atlas_type == 'NORMAL' and mat.DM.decaltype == 'INFO':
                    update_type = True
                    break

                elif atlas_type == 'INFO' and mat.DM.decaltype in ['SIMPLE', 'SUBSET', 'PANEL']:
                    update_type = True
                    break

            if update_type:
                print("INFO: Changing atlas type to COMBINED, creating new dummy textures for existing sources!")

                atlas_type = 'COMBINED'
                solution['type'] = atlas_type

                for uuid, decal in sources.items():
                    decalpath = makedir(os.path.join(sourcespath, uuid))

                    textures = decal['textures']
                    size = tuple(decal['original_size'])

                    for textype in ['NORMAL', 'AO_CURV_HEIGHT', 'COLOR']:
                        if textype not in textures:
                            path = create_dummy_texture(decalpath, "%s.png" % textype.lower(), mode='RGB', resolution=size, color=textype_color_mapping_dict[textype])
                            print("INFO: Created dummy %s map at: %s" % (textype, path))

                            sources[uuid]['textures'][textype] = path
                            sources[uuid]['original_textures'][textype] = ''

        return atlas_type

    def get_new_decalmats(self, decals, sources, debug=False):

        decalmats = get_unique_by_uuid_decalmats_from_decals(decals)

        duplicates = [uuid for uuid in decalmats if uuid in sources]

        for uuid in duplicates:
            if debug:
                print("removing", uuid)

            del decalmats[uuid]

        if debug:
            for uuid, mat in decalmats.items():
                print("new decal:", uuid, mat.DM.decalname)

        return decalmats


class RemoveDecalFromAtlas(bpy.types.Operator):
    bl_idname = "machin3.remove_decal_from_atlas"
    bl_label = "MACHIN3: Remove Decal from Atlas"
    bl_description = "Remove active Decal from Atlas"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        layout.label(text="This removes the selected Decal from the Atlas!")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None
            return atlas and atlas.DM.trimsCOL and atlas.DM.get('sources') and atlas.DM.get('solution')

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def execute(self, context):
        atlas = context.active_object
        idx, trims, active = get_trim(atlas)

        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, 'Create')
        atlasinstantpath = os.path.join(createpath, 'atlasinstant')
        atlaspath = makedir(os.path.join(atlasinstantpath, "%s_%s" % (atlas.DM.atlasindex, atlas.DM.atlasuuid)))
        templatepath = get_templates_path()

        sources = atlas.DM.get('sources').to_dict()
        solution = atlas.DM.get('solution').to_dict()

        print("WARNING: Removing decal %s from atlas!" % (sources[active.uuid]['name']))

        if active.dummy:
            bpy.data.meshes.remove(active.dummy.data, do_unlink=True)

        del sources[active.uuid]
        del solution['boxes'][active.uuid]

        trims.remove(idx)
        atlas.DM.trimsIDX = max([idx - 1, 0])

        atlas_type = solution['type']

        if atlas_type == 'COMBINED':
            new_atlas_type = self.update_atlas_type(sources, solution)

            if new_atlas_type:
                self.replace_atlasdummymat(atlas, new_atlas_type, templatepath, atlaspath)

        atlas.DM['sources'] = sources
        atlas.DM['solution'] = solution

        return {'FINISHED'}

    def replace_atlasdummymat(self, atlas, atlas_type, templatepath, atlaspath):

        dummymat = atlas.DM.atlasdummymat

        if dummymat:
            textures = get_atlas_textures(dummymat)
            remove_atlasmat(dummymat)

            for img in textures.values():
                bpy.data.images.remove(img, do_unlink=True)

        dummymat = append_material(templatepath, "TEMPLATE_ATLASDUMMY")

        if dummymat:
            atlas.DM.atlasdummymat = dummymat

            dummymat.name = atlas.name
            dummymat.DM.atlasname = atlas.DM.atlasname
            dummymat.DM.atlasuuid = atlas.DM.atlasuuid

            if atlas_type == 'NORMAL':
                atlas_images = {textype: os.path.join(atlaspath, "%s.png" % (textype.lower())) for textype in ['ALPHA', 'AO', 'CURVATURE', 'EMISSION', 'HEIGHT', 'NORMAL', 'SUBSET']}
            if atlas_type == 'INFO':
                atlas_images = {textype: os.path.join(atlaspath, "%s.png" % (textype.lower())) for textype in ['ALPHA', 'COLOR', 'EMISSION']}

            set_atlasdummy_texture_paths(dummymat, atlas_images)

            set_node_names_of_atlas_material(dummymat, atlas.DM.atlasname, dummy=True)

            nodes = get_atlas_nodes(dummymat, skip_height=True)

            for nodetype, node in nodes.items():
                if nodetype == 'PARALLAXGROUP':
                    node.inputs[0].default_value = atlas.DM.atlasdummyparallax

                elif node.type == 'TEX_IMAGE':
                    img = node.image
                    if img:
                        img.DM.atlasname = atlas.DM.atlasname
                        img.DM.atlasuuid = atlas.DM.atlasuuid

            for trim in atlas.DM.trimsCOL:
                if trim.dummy:
                    trim.dummy.material_slots[0].material = dummymat

    def update_atlas_type(self, sources, solution):
        def get_new_atlastype(sources):

            color_paths = [decal['original_textures']['COLOR'] for decal in sources.values()]

            if not any(color_paths):
                return 'NORMAL'

            normal_paths = [decal['original_textures']['NORMAL'] for decal in sources.values()]

            if not any(normal_paths):
                return 'INFO'

        atlas_type = get_new_atlastype(sources)

        if atlas_type:
            print("INFO: Changing atlas type to", atlas_type)

            solution['type'] = atlas_type

            for uuid, decal in sources.items():

                if atlas_type == 'NORMAL':
                    del sources[uuid]['textures']['COLOR']
                    del sources[uuid]['original_textures']['COLOR']

                if atlas_type == 'INFO':
                    del sources[uuid]['textures']['NORMAL']
                    del sources[uuid]['textures']['AO_CURV_HEIGHT']
                    del sources[uuid]['original_textures']['NORMAL']
                    del sources[uuid]['original_textures']['AO_CURV_HEIGHT']

        return atlas_type


class RemoveInstantAtlas(bpy.types.Operator):
    bl_idname = "machin3.remove_instant_atlas"
    bl_label = "MACHIN3: Remove Instant Atlas"
    bl_description = "Remove Selected Instant Atlas"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        layout.label(text="This removes the selected Atlas from the scene and all its temporary textures from disk!")
        layout.label(text="Are you sure? This cannot be undone!")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object and context.active_object.DM.isatlas

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def execute(self, context):
        uuid = context.active_object.DM.atlasuuid
        idx = context.active_object.DM.atlasindex

        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, 'Create')
        atlasinstantpath = os.path.join(createpath, 'atlasinstant')
        atlaspath = os.path.join(atlasinstantpath, "%s_%s" % (idx, uuid))

        if os.path.exists(atlaspath):
            rmtree(atlaspath)

        col = context.active_object.DM.atlascollection

        if col:
            bpy.data.collections.remove(col, do_unlink=True)

        dummies = [obj for obj in bpy.data.objects if obj.DM.isatlasdummy and obj.DM.atlasuuid == uuid]

        for dummy in dummies:
            bpy.data.meshes.remove(dummy.data, do_unlink=True)

        atlases = [obj for obj in bpy.data.objects if obj.DM.isatlas and obj.DM.atlasuuid == uuid]

        for atlas in atlases:
            bpy.data.meshes.remove(atlas.data, do_unlink=True)

        dummymats = [mat for mat in bpy.data.materials if mat.DM.isatlasdummymat and mat.DM.atlasuuid == uuid]

        for mat in dummymats:
            remove_atlasmat(mat)

        textures = [img for img in bpy.data.images if img.DM.isatlasdummytex and img.DM.atlasuuid == uuid]

        for img in textures:
            bpy.data.images.remove(img, do_unlink=True)

        atlasbgmats = [mat for mat in bpy.data.materials if mat.DM.isatlasbgmat]

        for bgmat in atlasbgmats:
            if bgmat.users == 0:
                bpy.data.materials.remove(bgmat, do_unlink=True)

        update_instantatlascount()

        return {'FINISHED'}


class StoreAtlas(bpy.types.Operator):
    bl_idname = "machin3.store_atlas"
    bl_label = "MACHIN3: Store Atlas"
    bl_description = "Store Atlas for Export Use"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        if self.display_message:
            layout.label(text="There already is an Atlas called '%s' registered!" % (self.atlas.DM.atlasname))
            layout.label(text="Do you want to proceed and replace it? This can not be undone!")

    @classmethod
    def poll(cls, context):
        if get_prefs().pil and context.mode == 'OBJECT':
            atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None
            if atlas and atlas.DM.get('solution'):
                return get_instant_atlas_path(atlas)

    def invoke(self, context, event):
        self.atlas = context.active_object

        assetspath = get_prefs().assetspath
        self.atlaslibpath = os.path.join(assetspath, 'Atlases', self.atlas.DM.atlasname)

        self.atlaspath = get_instant_atlas_path(self.atlas)

        if os.path.exists(self.atlaslibpath):

            if not context.scene.DM.debug:
                if os.path.exists(os.path.join(self.atlaslibpath, '.islocked')):
                    popup_message("An Atlas called '%s' exists and is force-locked, aborting." % self.atlas.DM.atlasname, title="Aborting")

                    return {'CANCELLED'}

                else:
                    if self.atlas.DM.atlasname in [atlas.name for atlas in get_atlas()[1] if atlas.islocked]:
                        popup_message(["An Atlas called '%s' exists and is locked, aborting." % (self.atlas.DM.atlasname), "Unlock the Atlas to be able to replace it!"], title="Aborting")
                        return {'CANCELLED'}

            self.display_message = True
            return context.window_manager.invoke_props_dialog(self, width=400)

        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        atlas = self.atlas
        atlaslibpath = self.atlaslibpath
        atlaspath = self.atlaspath

        self.display_message = False

        if os.path.exists(atlaslibpath):
            print("\nINFO: Replacing existing atlas: %s" % atlas.DM.atlasname)
            rmtree(atlaslibpath)

        else:
            print("\nINFO: Storing new Atlas: %s" % atlas.DM.atlasname)

        makedir(atlaslibpath)

        atlas_images = get_atlas_images_from_path(atlaspath)

        maps, size = self.create_final_atlas_textures(atlaslibpath, atlas, atlas_images)

        create_atlas_json(atlaslibpath, atlas, maps, size, new_atlas_uuid=str(uuid4()), debug=False)

        for m in ['.is20', '.isatlas']:
            with open(os.path.join(atlaslibpath, m), 'w') as f:
                f.write('')

        register_atlases(reloading=True)

        return {'FINISHED'}

    def create_final_atlas_textures(self, atlaslibpath, atlas, atlas_images):

        resolution = atlas.DM.atlasresolution
        resizedown = atlas.DM.atlasresizedown

        lower, _ = get_lower_and_upper_atlas_resolution(resolution[0])

        maps = {}

        for textype, path in atlas_images.items():
            dst = os.path.join(atlaslibpath, "%s.png" % (textype.lower()))

            copy(path, dst)

            if resizedown and lower != resolution[0]:

                print("INFO: Shrinking %s map to %dx%d" % (textype, lower, lower))
                scale_image(dst, size=(lower, lower))

                maps[textype] = {'texture': os.path.basename(dst),
                                 'resolution': (lower, lower)}

            else:
                maps[textype] = {'texture': os.path.basename(dst),
                                 'resolution': tuple(resolution)}

            if textype == 'HEIGHT':
                maps[textype]['parallax_amount'] = atlas.DM.atlasdummyparallax

            elif textype == 'ALPHA':
                maps[textype]['connect_alpha'] = False

        size = lower if resizedown and lower != resolution[0] else None

        return maps, size


class UseAtlas(bpy.types.Operator):
    bl_idname = "machin3.use_atlas"
    bl_label = "MACHIN3: Use Atlas"
    bl_description = "Adjust Decal UVs to fit Atlas and apply Atlas Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            decals = get_decals(context)
            return any(atlas.isenabled for atlas in get_atlas()[1]) and [obj for obj in decals if not obj.DM.preatlasmats]

    def execute(self, context):
        dm = context.scene.DM
        atlas_collections = dm.export_atlas_create_collections

        atlases = [atlas for atlas in get_atlas()[1] if atlas.isenabled]

        alluuids = self.get_all_available_uuids(context, atlases)

        decals = get_decals(context)

        decalmats = self.get_used_decalmats_from_decals(decals, alluuids, debug=False)

        if decalmats:
            if len(decalmats) != len(decals):
                print("WARNING: Not all of the %s decals are found in the enabled atlases!" % ("selected" if context.selected_objects else "visible"))

            atlasmats = self.atlasify_decals(context, atlases, decalmats, atlas_collections=atlas_collections, debug=False)

            for atlas, decals in atlasmats.items():
                atlasdata = get_atlasdata_from_atlas(atlas)

                atlasmats = sorted([mat for mat in bpy.data.materials if mat.DM.isatlasmat and mat.DM.atlasuuid == atlasdata['uuid']], key=lambda x: x.name)

                if atlasmats:
                    atlasmat = atlasmats[0]

                else:
                    atlasmat = append_and_setup_atlas_material(atlasdata, istrimsheet=atlas.istrimsheet)

                for decal, idx in decals:
                    decal.material_slots[idx].material = atlasmat


        else:
            popup_message("None of the enabled Atlases contain the %s Decals!" % ("selected" if context.selected_objects else "visible"), title="Atlasing Aborted")


        return {'FINISHED'}

    def atlasify_decals(self, context, atlases, decalmats, atlas_collections, debug=False):
        bpy.ops.object.select_all(action='DESELECT')

        atlasmats = {}

        for decal, mats in decalmats.items():
            decal.select_set(True)
            context.view_layer.objects.active = decal

            if debug:
                print()
                print("Atlasing", decal.name)

            preatlasmats = decal.DM.preatlasmats

            if not preatlasmats:
                atlas_uvs = decal.data.uv_layers.active
                atlas_uvs.name = "Atlas UVs"
                decal.data.uv_layers.new(name="Decal UVs")

            verify_uv_transfer(context, decal)

            bm = bmesh.new()
            bm.from_mesh(decal.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            uvs = bm.loops.layers.uv.active

            for idx, mat in mats:
                if debug:
                    print(" material", mat.name, "at index", idx)

                premat = preatlasmats.add()
                premat.name = mat.name
                premat.material = mat
                premat.material_index = idx

                ispanel = any([decal.DM.decaltype == 'PANEL', mat.DM.decaltype == 'PANEL'])

                atlas, atlasdata, trim = get_atlasdata_from_decaluuid(mat.DM.uuid, atlases=atlases)

                resolution = Vector(atlasdata.get('resolution'))
                trimlocation = Vector(trim.get('location'))
                trimscale = Vector(trim.get('scale'))

                faces = [f for f in bm.faces if f.material_index == idx]
                loops = [loop for face in faces for loop in face.loops]

                dbbox, dmid, dscale = self.get_decal_uv_bbox(uvs, loops, ispanel=ispanel)
                trimbbox, trimmid = get_trim_uv_bbox(resolution, trimlocation, trimscale)

                if ispanel and trimlocation[0] == 0 and trimscale[0] == 1 and trim.get('repetitions'):
                    smx = Matrix.Scale(trimscale.y / dscale.y, 2)

                    repetitions = trim.get('repetitions', 1)

                    pscale = dscale.y / (repetitions * trimscale.y)

                    smx[0][0] *= pscale

                else:
                    smx = Matrix(((trimscale.x / dscale.x, 0), (0, trimscale.y / dscale.y)))

                for loop in loops:
                    loop[uvs].uv = trimmid + smx @ (loop[uvs].uv - dmid)

                if atlas in atlasmats:
                    atlasmats[atlas].append((decal, idx))

                else:
                    atlasmats[atlas] = [[decal, idx]]

                if atlas_collections:
                    acol = get_atlas_collection(context, atlas)

                    if decal.name not in acol.objects:
                        acol.objects.link(decal)

                if len(decal.data.materials) == 1:
                    mirrors = [mod for mod in decal.modifiers if mod.type == 'MIRROR']

                    for mod in mirrors:
                        if mod.use_mirror_u:
                            mod.mirror_offset_u = trimmid.x - (1 - trimmid.x)

                        if mod.use_mirror_v:
                            mod.mirror_offset_v = trimmid.y - (1 - trimmid.y)

            bm.to_mesh(decal.data)
            bm.free()

        return atlasmats

    def get_decal_uv_bbox(self, uvs, loops, ispanel=False):

        if ispanel:
            return get_selection_uv_bbox(uvs, loops)

        else:
            return (Vector((0.0, 0.0)), Vector((1.0, 1.0))), Vector((0.5, 0.5)), Vector((1, 1))

    def get_used_decalmats_from_decals(self, decals, uuids, debug=False):

        decalmats = {}

        for decal in decals:

            seq = [0] * len(decal.data.polygons)
            decal.data.polygons.foreach_get('material_index', seq)
            matids = list(set(seq))

            materials = []

            for idx in matids:
                if idx < len(decal.data.materials):
                    mat = decal.data.materials[idx]

                    if mat and mat.DM.isdecalmat and mat.DM.uuid in uuids:
                        preatlasmats = decal.DM.preatlasmats

                        if (idx, mat) not in [(premat.material_index, premat.material) for premat in preatlasmats]:
                            materials.append((idx, mat))

                        elif debug:
                            print("skipping %s, already atlased earlier" % (mat.name))

            if materials:
                decalmats[decal] = materials

        if debug:
            for decal, decalmats in decalmats.items():
                print(decal.name)
                for idx, mat in decalmats:
                    print(" ", idx, mat.name)

        return decalmats

    def get_all_available_uuids(self, context, atlases):

        alluuids = set()

        for atlas in atlases:
            d = context.window_manager.trimsheets if atlas.istrimsheet else context.window_manager.atlases
            data = d.get(atlas.name)

            if data:
                uuids = [trim['uuid'] for trim in data['trims']]
                alluuids.update(uuids)

        return alluuids


class RestorePreAtlasDecalMaterials(bpy.types.Operator):
    bl_idname = "machin3.restore_preatlas_decal_materials"
    bl_label = "MACHIN3: Restore Pre-Atlas Decal Materials"
    bl_description = "Restore original Decal UVs and Materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            decals = get_decals(context)
            return [obj for obj in decals if obj.DM.preatlasmats and not obj.DM.isjoinedafteratlased and all(obj.data.uv_layers.get(name) for name in ['Atlas UVs', 'Decal UVs'])]

    def execute(self, context):
        source = context.selected_objects if context.selected_objects else context.visible_objects
        decals = [obj for obj in source if obj.DM.isdecal and obj.DM.preatlasmats and all(obj.data.uv_layers.get(name) for name in ['Atlas UVs', 'Decal UVs']) and not obj.DM.isjoinedafteratlased]

        atlasmats = set()
        collections = set()

        for decal in decals:
            preatlasmats = decal.DM.preatlasmats

            for premat in preatlasmats:
                idx = premat.material_index
                mat = premat.material

                if mat and idx < len(decal.data.materials):
                    atlasmat = decal.material_slots[idx].material

                    if atlasmat and atlasmat.DM.isatlasmat:
                        atlasmats.add(atlasmat)

                    decal.material_slots[idx].material = mat

                    atlascol = bpy.data.collections.get(atlasmat.DM.atlasname)

                    if atlascol:
                        collections.add(atlascol)

                        if decal.name in atlascol.objects:
                            atlascol.objects.unlink(decal)

                            if not decal.users_collection:
                                mcol = context.scene.collection
                                mcol.objects.link(decal)

            preatlasmats.clear()

            atlasuvs = decal.data.uv_layers.get('Atlas UVs')
            decal.data.uv_layers.remove(atlasuvs)

            decaluvs = decal.data.uv_layers.get('Decal UVs')
            decaluvs.name = 'UVMap'

            verify_uv_transfer(context, decal)

            mirrors = [mod for mod in decal.modifiers if mod.type == 'MIRROR']

            for mod in mirrors:
                if mod.use_mirror_u:
                    mod.mirror_offset_u = 0

                if mod.use_mirror_v:
                    mod.mirror_offset_v = 0

        for mat in atlasmats:
            if mat.users < 1:
                remove_atlasmat(mat, remove_textures=True, debug=False)

        for col in collections:
            if len(col.objects) == 0:
                bpy.data.collections.remove(col, do_unlink=True)

        return {'FINISHED'}


class AddAtlasChannelPack(bpy.types.Operator):
    bl_idname = "machin3.add_atlas_channel_pack"
    bl_label = "MACHIN3: Add Atlas Channel Pack"
    bl_description = "Add new Channel Packed Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.DM.export_atlas_texture_channel_packCOL.add()
        context.scene.DM.export_atlas_texture_channel_packIDX = len(context.scene.DM.export_atlas_texture_channel_packCOL) - 1

        return {'FINISHED'}


class RemoveAtlasChannelPack(bpy.types.Operator):
    bl_idname = "machin3.remove_atlas_channel_pack"
    bl_label = "MACHIN3: Remove Atlas Channel Pack"
    bl_description = "Remove active Channel Packed Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        channel_pack = context.scene.DM.export_atlas_texture_channel_packCOL
        idx = context.scene.DM.export_atlas_texture_channel_packIDX

        channel_pack.remove(idx)

        if idx >= len(channel_pack):
            context.scene.DM.export_atlas_texture_channel_packIDX = len(channel_pack) - 1

        return {'FINISHED'}


class Export(bpy.types.Operator):
    bl_idname = "machin3.export_atlas_decals"
    bl_label = "MACHIN3: Export Atlas Decals"
    bl_description = "Export Atlas Textures and Models"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            dm = context.scene.DM
            if dm.export_atlas_textures:
                decals = [obj for obj in (context.selected_objects if context.selected_objects else context.visible_objects) if obj.DM.isdecal and obj.DM.preatlasmats]
                atlasmats = {mat for decal in decals for mat in decal.data.materials if mat and mat.DM.isatlasmat}

                if atlasmats:
                    return True

            return dm.export_atlas_models

    @classmethod
    def description(cls, context, properties):
        dm = context.scene.DM
        textures = dm.export_atlas_textures
        models = dm.export_atlas_models

        if textures and models:
            return "Export Atlas Textures and %s Models" % ('selected' if context.selected_objects else 'visible')
        elif textures:
            return "Export Atlas Textures"
        else:
            return "Export %s Models" % ('selected' if context.selected_objects else 'visible')

    def execute(self, context):
        dm = context.scene.DM

        export_path = dm.export_atlas_path
        export_textures = dm.export_atlas_textures
        export_models = dm.export_atlas_models

        if export_textures:
            textures_folder = dm.export_atlas_textures_folder
            use_textures_folder = dm.export_atlas_use_textures_folder
            channel_packs = [pack for pack in dm.export_atlas_texture_channel_packCOL if pack.isenabled]

            decals = [obj for obj in (context.selected_objects if context.selected_objects else context.visible_objects) if obj.DM.isdecal and obj.DM.preatlasmats]
            atlasmats = {mat for decal in decals for mat in decal.data.materials if mat and mat.DM.isatlasmat}

            for mat in atlasmats:
                print("\nINFO: Exporting %s's textures" % (mat.DM.atlasname))

                atlas, atlasdata = get_atlasdata_from_atlasmat(mat)

                self.export_individual_textures(dm, atlas, atlasdata, export_path, textures_folder if use_textures_folder else '')

                self.export_channel_packed_textures(atlas, atlasdata, mat, channel_packs, export_path, textures_folder if use_textures_folder else '')

        if export_models:
            models_folder = dm.export_atlas_models_folder
            use_models_folder = dm.export_atlas_use_models_folder
            format = dm.export_atlas_model_format

            self.export_models(context, dm, format, export_path, models_folder if use_models_folder else '')

        return {'FINISHED'}

    def export_models(self, context, dm, format, path, folder):
        destination = makedir(os.path.join(path, folder))
        blendname = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        filepath = os.path.join(destination, blendname)

        if format == 'OBJ':
            bpy.ops.export_scene.obj('INVOKE_DEFAULT', filepath=filepath, use_selection=True if context.selected_objects else False)

        elif format == 'FBX':
            machin3tools, _, _, _ = get_addon("MACHIN3tools")
            m3prefs = get_addon_prefs('MACHIN3tools') if machin3tools else None
            activate_unity = getattr(m3prefs, 'activate_unity', None)
            apply_scale = 'FBX_SCALE_ALL' if activate_unity and dm.export_atlas_model_unity else 'FBX_SCALE_NONE'

            bpy.ops.export_scene.fbx('INVOKE_DEFAULT', filepath=filepath, use_selection=True if context.selected_objects else False, apply_scale_options=apply_scale)

        elif format == 'GLTF':
            bpy.ops.export_scene.gltf('INVOKE_DEFAULT', filepath=filepath, export_selected=True if context.selected_objects else False)

    def export_channel_packed_textures(self, atlas, atlasdata, mat, channel_packs, path, folder):
        textypes = get_textypes_from_atlasmats([mat])

        for pack in channel_packs:
            if verify_channel_pack(textypes, pack):
                atlaspath = os.path.join(get_prefs().assetspath, 'Trims' if atlas.istrimsheet else 'Atlases', atlas.name)
                destination = makedir(os.path.join(path, folder))

                channels = [ch for ch in [pack.red, pack.green, pack.blue, pack.alpha]]

                keys = ['RED', 'GREEN', 'BLUE', 'ALPHA']
                sources = {key: {} for key in keys}

                for idx, ch in enumerate(channels):
                    if ch in ['SMOOTHNESS', 'SUBSETOCCLUSION', 'WHITEHEIGHT']:
                        sources[keys[idx]]['mode'] = 'CREATE'
                        sources[keys[idx]]['type'] = ch

                        if ch == 'SMOOTHNESS':
                            sources[keys[idx]]['path'] = os.path.join(atlaspath, "roughness.png")

                        elif ch == 'WHITEHEIGHT':
                            sources[keys[idx]]['path'] = os.path.join(atlaspath, "height.png")

                        elif ch == 'SUBSETOCCLUSION':
                            sources[keys[idx]]['paths'] = [os.path.join(atlaspath, "subset.png"), os.path.join(atlaspath, "ao.png")]

                    elif ch == 'NONE':
                        continue

                    else:
                        sources[keys[idx]]['mode'] = 'LOAD'
                        sources[keys[idx]]['path'] = os.path.join(atlaspath, "%s.png" % (ch.lower()))

                dst = os.path.join(destination, "%s_%s.png" % (atlas.name, pack.name))
                print("INFO: Creating %s channel packed %s map: %s" % (atlas.name, pack.name.upper(), dst))

                create_channel_packed_atlas_map(sources, atlasdata['resolution'], dst)

    def export_individual_textures(self, dm, atlas, atlasdata, path, folder):
        textypes = atlasdata.get('maps').keys()

        atlaspath = os.path.join(get_prefs().assetspath, 'Trims' if atlas.istrimsheet else 'Atlases', atlas.name)
        destination = makedir(os.path.join(path, folder))

        if dm.export_atlas_texture_alpha and 'ALPHA' in textypes:
            src = os.path.join(atlaspath, 'alpha.png')
            dst = os.path.join(destination, '%s_alpha.png' % (atlas.name))

            print("INFO: Copying %s ALPHA map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_ao and 'AO' in textypes:
            src = os.path.join(atlaspath, 'ao.png')
            dst = os.path.join(destination, '%s_ao.png' % (atlas.name))

            print("INFO: Copying %s AO map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_color and 'COLOR' in textypes:
            src = os.path.join(atlaspath, 'color.png')
            dst = os.path.join(destination, '%s_color.png' % (atlas.name))

            print("INFO: Copying %s COLOR map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_curvature and 'CURVATURE' in textypes:
            src = os.path.join(atlaspath, 'curvature.png')
            dst = os.path.join(destination, '%s_curvature.png' % (atlas.name))

            print("INFO: Copying %s CURVATURE map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_emission and 'EMISSION' in textypes:
            src = os.path.join(atlaspath, 'emission.png')
            dst = os.path.join(destination, '%s_emission.png' % (atlas.name))

            print("INFO: Copying %s EMISSION map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_height and 'HEIGHT' in textypes:
            src = os.path.join(atlaspath, 'height.png')
            dst = os.path.join(destination, '%s_height.png' % (atlas.name))

            print("INFO: Copying %s HEIGHT map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_normal and 'NORMAL' in textypes:
            src = os.path.join(atlaspath, 'normal.png')
            dst = os.path.join(destination, '%s_normal.png' % (atlas.name))

            print("INFO: Copying %s NORMAL map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_material2 and 'MATERIAL2' in textypes:
            src = os.path.join(atlaspath, 'material2.png')
            dst = os.path.join(destination, '%s_material2.png' % (atlas.name))

            print("INFO: Copying %s MATERIAL2 map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_metallic and 'METALLIC' in textypes:
            src = os.path.join(atlaspath, 'metallic.png')
            dst = os.path.join(destination, '%s_metallic.png' % (atlas.name))

            print("INFO: Copying %s METALLIC map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_roughness and 'ROUGHNESS' in textypes:
            src = os.path.join(atlaspath, 'roughness.png')
            dst = os.path.join(destination, '%s_roughness.png' % (atlas.name))

            print("INFO: Copying %s ROUGHNESS map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_smoothness and 'ROUGHNESS' in textypes:
            src = os.path.join(atlaspath, 'roughness.png')
            dst = os.path.join(destination, '%s_smoothness.png' % (atlas.name))

            print("INFO: Creating %s SMOOTHNESS map from ROUGHNESS map: %s" % (atlas.name, dst))
            create_smoothness_map(src, dst)

        if dm.export_atlas_texture_subset and 'SUBSET' in textypes:
            src = os.path.join(atlaspath, 'subset.png')
            dst = os.path.join(destination, '%s_subset.png' % (atlas.name))

            print("INFO: Copying %s SUBSET map to %s" % (atlas.name, dst))
            copy(src, dst)

        if dm.export_atlas_texture_subset_occlusion and all(tt in textypes for tt in ['AO', 'SUBSET']):
            subsetrc = os.path.join(atlaspath, 'subset.png')
            aosrc = os.path.join(atlaspath, 'ao.png')
            dst = os.path.join(destination, '%s_subset_occlusion.png' % (atlas.name))

            print("INFO: Creating %s SUBSET OCCLUSION map from AO and SUBSET maps: %s" % (atlas.name, dst))
            create_subset_occlusion_map(subsetrc, aosrc, dst)

        if dm.export_atlas_texture_white_height and 'HEIGHT' in textypes:
            src = os.path.join(atlaspath, 'height.png')
            dst = os.path.join(destination, '%s_white_height.png' % (atlas.name))

            print("INFO: Creating %s WHITE HEIGHT map from HEIGHT map: %s" % (atlas.name, dst))
            create_white_height_map(src, dst)
