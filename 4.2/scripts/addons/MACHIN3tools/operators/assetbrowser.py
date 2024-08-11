import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
import os
from mathutils import Vector, Matrix
import numpy as np
from .. utils.asset import get_asset_ids, get_asset_library_reference, get_most_used_local_catalog_id, is_local_assembly_asset, set_asset_library_reference, update_asset_catalogs, get_assetbrowser_bookmarks, get_catalogs_from_asset_libraries, get_libref_and_catalog, set_assetbrowser_bookmarks, validate_libref_and_catalog, get_display_size_from_area
from .. utils.draw import draw_fading_label, draw_points, draw_point
from .. utils.math import average_locations, create_coords_bbox, get_loc_matrix
from .. utils.object import get_eval_bbox, get_object_tree, get_parent, has_bbox, is_instance_collection, is_linked_object, remove_obj, duplicate_objects
from .. utils.registration import get_addon, get_path 
from .. utils.render import is_cycles_view
from .. utils.ui import force_ui_update, get_icon, popup_message
from .. utils.view import ensure_visibility, get_view_bbox, get_view_origin_and_dir
from .. utils.workspace import get_3dview_area, get_window_region_from_area
from .. items import create_assembly_asset_empty_location_items, asset_browser_bookmark_props
from .. colors import white, yellow, blue, green, red

decalmachine = None
meshmachine = None

class CreateAssemblyAsset(bpy.types.Operator):
    bl_idname = "machin3.create_assembly_asset"
    bl_label = "MACHIN3: Create Assembly Asset"
    bl_description = "Create Assembly Asset from the selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Asset Name", default="AssemblyAsset")
    move: BoolProperty(name="Move instead of Copy", description="Move Objects into Asset Collection, instead of copying\nThis will unlink them from any existing collections", default=False)
    location: EnumProperty(name="Empty Location", items=create_assembly_asset_empty_location_items, description="Location of Asset's Empty", default='AVGFLOOR')
    unlink_asset: BoolProperty(name="Unlink Assembly Asset", description="Remove the Asset Empty from the current Scene", default=True)
    render_thumbnail: BoolProperty(name="Render Thumbnail", default=True)
    avoid_update: BoolProperty()

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def draw(self, context):
        global decalmachine, meshmachine

        layout = self.layout

        box = layout.box()
        box.label(text="Asset Info")
        column = box.column(align=True)

        column.prop(self, 'name')
        column.prop(context.window_manager, 'M3_asset_catalogs', text='Catalog')

        box = layout.box()
        box.label(text="Asset Empty")
        column = box.column(align=True)

        split = column.split(factor=0.2, align=True)
        row = split.row(align=True)
        row.active = False
        row.alignment = 'RIGHT'
        row.label(text="Position")
        row = split.row(align=True)
        row.prop(self, 'location', expand=True)

        split = column.split(factor=0.2, align=True)
        row = split.row(align=True)
        row.active = False
        row.alignment = 'RIGHT'
        row.label(text="Unlink")
        row = split.row(align=True)
        row.prop(self, 'unlink_asset', toggle=True)

    def invoke(self, context, event):
        global decalmachine, meshmachine

        if decalmachine is None:
            decalmachine = get_addon('DECALmachine')[0]

        if meshmachine is None:
            meshmachine = get_addon('MESHmachine')[0]

        update_asset_catalogs(self, context)

        return context.window_manager.invoke_props_dialog(self, width=400)

    def execute(self, context):
        global decalmachine, meshmachine

        name = self.name.strip()

        if name:
            print(f"\nINFO: Creation Assembly Asset: {name}")

            objects = self.get_assembly_asset_objects(context)

            loc = self.get_empty_location(context, objects, debug=False)

            duplicates = duplicate_objects(context, objects)

            for obj in duplicates:
                obj.M3.hide = not obj.visible_get()

                obj.M3.hide_viewport = obj.hide_viewport

            if decalmachine:
                self.delete_decal_backups(duplicates)
            
            if meshmachine:
                self.delete_stashes(duplicates)

            empty, empty_cols = self.create_asset_instance_collection(context, name, duplicates, loc)

            self.switch_asset_browser_to_LOCAL(context, empty)

            asset_bbox, asset_dimensions = self.get_asset_bbox(duplicates)

            if asset_bbox and self.render_thumbnail:
                self.create_asset_thumbnail(context, empty, asset_bbox)

            self.finalize(context, empty, empty_cols, asset_dimensions)

            if not asset_bbox:
                draw_fading_label(context, text="Could not create Asset Thumbnail from current Selection of Objects", color=red, move_y=30, time=3)

            return {'FINISHED'}

        else:
            popup_message("The chosen asset name can't be nothing", title="Illegal Name")
            return {'CANCELLED'}

    def get_assembly_asset_objects(self, context):
        objects = set()

        for obj in context.selected_objects:
            tops = get_parent(obj, recursive=True, debug=True)
            top = tops[-1] if tops else obj

            obj_tree = [top]
            get_object_tree(top, obj_tree, mod_objects=True, find_disabled_mods=False, check_if_on_viewlayer=True)

            objects.update(obj_tree)

        return objects

    def get_empty_location(self, context, objects, debug=False):
        if self.location in ['AVG', 'AVGFLOOR']:
            rootobjs = [obj for obj in objects if not obj.parent]

            loc = average_locations([obj.matrix_world.decompose()[0] for obj in rootobjs])
            color = yellow

            if self.location == 'AVGFLOOR':
                loc.z = 0
                color = green

        elif self.location == 'CURSOR':
            loc = context.scene.cursor.location
            color = blue

        else:
            loc = Vector((0, 0, 0))
            color = white

        if debug:
            draw_point(loc, color=color, modal=False)
            context.area.tag_redraw()

        return loc

    def delete_decal_backups(self, objects):
        decals_with_backups = [obj for obj in objects if obj.DM.isdecal and obj.DM.decalbackup]

        for decal in decals_with_backups:
            if decal.DM.decalbackup:
                decal.DM.decalbackup = None

    def delete_stashes(self, objects):
        objs_with_stashes = [obj for obj in objects if obj.MM.stashes]

        for obj in objs_with_stashes:
            obj.MM.stashes.clear()

    def finalize(self, context, empty, empty_cols, asset_dimensions):
        if not self.unlink_asset:
            empty = empty.copy()

            for col in empty_cols:
                col.objects.link(empty)

            context.view_layer.objects.active = empty

            if asset_dimensions:
                self.offset_asset_empty_towards_view(context, empty, asset_dimensions)

    def create_asset_instance_collection(self, context, name, objects, loc):
        master_col = context.scene.collection

        main_asset_col = bpy.data.collections.get('_Assets')

        if not main_asset_col:
            main_asset_col = bpy.data.collections.new("_Assets")

        if main_asset_col.name not in master_col.children:
            master_col.children.link(main_asset_col)

        context.view_layer.layer_collection.children[main_asset_col.name].exclude = False

        asset_col = bpy.data.collections.new(f"_{name}")
        asset_col.M3.is_asset_collection = True

        main_asset_col.children.link(asset_col)

        object_cols = {col for obj in objects for col in obj.users_collection}

        empty_cols = [col for col in object_cols if all(ob.name in col.objects for ob in objects)]

        if not empty_cols:
            empty_cols = [master_col]

        for obj in objects:
            for col in obj.users_collection:
                if col in object_cols:
                    col.objects.unlink(obj)

        for obj in objects:
            asset_col.objects.link(obj)

            if obj.display_type in ['WIRE', 'BOUNDS'] or (obj.type == 'EMPTY' and not obj.instance_collection):
                obj.hide_set(True)

                obj.hide_viewport = True

        empty = bpy.data.objects.new(name, object_data=None)
        empty.instance_collection = asset_col
        empty.instance_type = 'COLLECTION'

        empty.location = loc

        empty.M3.asset_version = "1.1"

        asset_col.instance_offset = loc

        empty.asset_mark()

        catalog = context.window_manager.M3_asset_catalogs

        if catalog and catalog != 'NONE':
            for uuid, catalog_data in self.catalogs.items():
                if catalog == catalog_data['catalog']:
                    empty.asset_data.catalog_id = uuid

        context.view_layer.layer_collection.children[main_asset_col.name].exclude = True

        return empty, empty_cols

    def switch_asset_browser_to_LOCAL(self, context, asset):
        asset_browsers = [area for screen in context.workspace.screens for area in screen.areas if area.type == 'FILE_BROWSER' and area.ui_type == 'ASSETS']

        if len(asset_browsers) == 1:
            for space in asset_browsers[0].spaces:
                if space.type == 'FILE_BROWSER':
                    if get_asset_library_reference(space.params) != 'LOCAL':
                        set_asset_library_reference(space.params, 'LOCAL')

                    space.params.catalog_id = asset.asset_data.catalog_id

                    space.show_region_tool_props = True

                    space.activate_asset_by_id(asset, deferred=True)

    def get_asset_bbox(self, objects, debug=False):
        def get_instance_collection_bbox_recursively(col_coords, obj, col, mx):
            offsetmx = get_loc_matrix(col.instance_offset)
            instance_mx = mx @ obj.matrix_world @ offsetmx.inverted_safe()

            for ob in obj.instance_collection.objects:
                if ob.display_type not in ['WIRE', 'BOUNDS'] and not ob.M3.hide and has_bbox(ob):
                    bbox = [instance_mx @ ob.matrix_world @ co for co in get_eval_bbox(ob)]
                    col_coords.extend(bbox)

                elif icol := is_instance_collection(ob):
                    get_instance_collection_bbox_recursively(col_coords, ob, icol, instance_mx)

        coords = []

        for obj in objects:

            if obj.display_type not in ['WIRE', 'BOUNDS'] and not obj.M3.hide and has_bbox(obj):
                bbox = [obj.matrix_world @ co for co in get_eval_bbox(obj)]
                coords.extend(bbox)

            elif col := is_instance_collection(obj):
                col_coords = []
                get_instance_collection_bbox_recursively(col_coords, obj, col, Matrix())
                coords.extend(col_coords)

        if coords:
            bbox, _, dimensions = create_coords_bbox(coords)

            if debug:
                draw_points(coords, color=yellow, modal=False)
                draw_points(bbox, color=blue, modal=False)

            return bbox, dimensions
        return None, None

    def offset_asset_empty_towards_view(self, context, empty, asset_dimensions):
        mx = empty.matrix_world

        axes = [('X', mx.to_quaternion() @ Vector((1, 0, 0))),
                ('X', mx.to_quaternion() @ Vector((-1, 0, 0))),
                ('Y', mx.to_quaternion() @ Vector((0, 1, 0))),
                ('Y', mx.to_quaternion() @ Vector((0, -1, 0)))]

        _, view_dir = get_view_origin_and_dir(context)

        aligned = []

        for label, axis in axes:
            aligned.append((label, axis, axis.dot(view_dir)))

        label, axis = min(aligned, key=lambda x: x[2])[:2]

        amount = asset_dimensions[0] if label == 'X' else asset_dimensions[1]
        empty.matrix_world @= get_loc_matrix(axis * amount * 1.1) 

    def create_asset_thumbnail(self, context, obj, bbox):
        def get_square_view_bbox(debug=False):
            render_bbox = get_view_bbox(context, bbox, margin=20, border_gap=0, debug=False)

            if debug:
                print("render bbox:", render_bbox)

            render_bbox_width = (render_bbox[1] - render_bbox[0]).length
            render_bbox_height = (render_bbox[2] - render_bbox[1]).length

            if debug:
                print("  bbox width:", render_bbox_width)
                print(" bbox height:", render_bbox_height)

            if render_bbox_width > render_bbox_height:
                delta = int((render_bbox_width - render_bbox_height) / 2)

                xmin = render_bbox[0].x
                xmax = render_bbox[1].x

                ymin = max(min(render_bbox[1].y - delta, region_height), 0)
                ymax = max(min(render_bbox[2].y + delta, region_height), 0)

                square_bbox = [Vector((xmin, ymin)), Vector((xmax, ymin)), Vector((xmax, ymax)), Vector((xmin, ymax))]

            elif render_bbox_width < render_bbox_height:
                delta = int((render_bbox_height - render_bbox_width) / 2)

                xmin = max(min(render_bbox[0].x - delta, region_width), 0)
                xmax = max(min(render_bbox[1].x + delta, region_width), 0)

                ymin = render_bbox[1].y
                ymax = render_bbox[2].y

                square_bbox = [Vector((xmin, ymin)), Vector((xmax, ymin)), Vector((xmax, ymax)), Vector((xmin, ymax))]

            else:
                square_bbox = render_bbox

            square_bbox_width = (square_bbox[1] - square_bbox[0]).length
            square_bbox_height = (square_bbox[2] - square_bbox[1]).length
            
            if debug:
                print("square bbox:", square_bbox)
                print(" square bbox width:", square_bbox_width)
                print("square bbox height:", square_bbox_height)

            return square_bbox, (int(square_bbox_width), int(square_bbox_height))

        def render_viewport():
            view = context.space_data
            cam = context.scene.camera
            render = context.scene.render

            is_cam_view = cam and view.region_3d.view_perspective == 'CAMERA'
            is_forced_cam = False
            is_cycles = is_cycles_view(context)

            initial = {'resolution_x': render.resolution_x,
                       'resolution_y': render.resolution_y,
                       'resolution_percentage': render.resolution_percentage,
                       'file_format': render.image_settings.file_format,
                       'show_overlays': view.overlay.show_overlays}

            if is_cam_view:
                initial['lens'] = cam.data.lens

            if is_cycles:
                cycles = context.scene.cycles

                settings = { 'use_adaptive_sampling': cycles.use_adaptive_sampling,
                             'adaptive_threshold': cycles.adaptive_threshold,
                             'samples': cycles.samples,
                             'use_denoising': cycles.use_denoising,
                             'denoising_input_passes': cycles.denoising_input_passes,
                             'denoising_prefilter': cycles.denoising_prefilter,
                             'denoising_quality': cycles.denoising_quality,
                             'denoising_use_gpu': cycles.denoising_use_gpu}

                initial['cycles'] = settings

                if not is_cam_view:

                    initial['camera'] = context.scene.camera

                    initial['active'] = context.active_object
                    initial['selected'] = context.selected_objects

                    bpy.ops.object.camera_add()

                    cam = context.active_object
                    context.scene.camera = cam

                    bpy.ops.view3d.camera_to_view()

                    cam.data.lens = view.lens
                    cam.data.sensor_width = 72

                    is_cam_view = True
                    is_forced_cam = True

            if is_cam_view and not is_forced_cam:
                init_resolution_ratio = render.resolution_x / render.resolution_y
                region_ratio = region_width / region_height
                factor = init_resolution_ratio / region_ratio

                if round(factor) > 1:
                    factor = region_ratio

            render.resolution_x = region_width
            render.resolution_y = region_height
            render.resolution_percentage = 100
            render.image_settings.file_format = 'PNG'
            view.overlay.show_overlays = False

            if is_cycles:
                 cycles.use_adaptive_sampling = True
                 cycles.adaptive_threshold = 0.1
                 cycles.samples = 4
                 cycles.use_denoising = True
                 cycles.denoising_input_passes = 'RGB'
                 cycles.denoising_prefilter = 'FAST'
                 cycles.denoising_quality = 'FAST'
                 cycles.denoising_use_gpu = True

            if is_cam_view and not is_forced_cam:
                cam.data.lens *= factor

            if is_cycles_view(context):
                bpy.ops.render.render(write_still=False)

            else:
                bpy.ops.render.opengl()

            result = bpy.data.images.get('Render Result')

            if result:
                filepath = os.path.join(get_path(), 'resources', 'asset_thumbnail_render.png')
                result.save_render(filepath=filepath)

            context.scene.render.resolution_x = initial['resolution_x']
            context.scene.render.resolution_y = initial['resolution_y']
            context.scene.render.resolution_percentage = initial['resolution_percentage']
            context.scene.render.image_settings.file_format = initial['file_format']
            view.overlay.show_overlays = initial['show_overlays']

            if is_cycles:
                cycles.use_adaptive_sampling = initial['cycles']['use_adaptive_sampling']
                cycles.adaptive_threshold = initial['cycles']['adaptive_threshold']
                cycles.samples = initial['cycles']['samples']
                cycles.use_denoising = initial['cycles']['use_denoising']
                cycles.denoising_input_passes = initial['cycles']['denoising_input_passes']
                cycles.denoising_prefiltert = initial['cycles']['denoising_prefilter']
                cycles.denoising_quality = initial['cycles']['denoising_quality']
                cycles.denoising_use_gpu = initial['cycles']['denoising_use_gpu']

            if is_forced_cam:
                bpy.data.cameras.remove(cam.data, do_unlink=True)

                if cam := initial['camera']:
                    context.scene.camera = cam

                if active := initial['active']:
                    context.view_layer.objects.active = active

                for obj in initial['selected']:
                    obj.select_set(True)

            if is_cam_view and not is_forced_cam:
                cam.data.lens = initial['lens']

            if result:
                 image = bpy.data.images.load(filepath=filepath)
                 return image

        def crop_image(image, crop_box, dimensions, debug=False):
            width, height = dimensions

            pixels = np.array(image.pixels[:])

            pixels = pixels.reshape((region_height, region_width, 4))

            left = int(crop_box[0].x)
            right = int(crop_box[1].x)
            top = int(crop_box[1].y)
            bottom = int(crop_box[2].y)

            cropped_pixels = pixels[top:bottom, left:right, :]

            cropped = bpy.data.images.new("Cropped Asset Render", width=width, height=height)

            try:
                cropped.pixels[:] = cropped_pixels.flatten()         # see CodeMaX below, the difference here is minor though, but extreme for the image_pixels_float

            except Exception as e:
                print("something failed ugh here already actually")
                print(e)

                print("cropped pixels")
                print(cropped_pixels)

            if debug:
                print("cropped width:", width)
                print("cropped height:", height)

            scale_factor = max(width, height) / 256

            if scale_factor > 1:
                if debug:
                    print("scale down by:", scale_factor)

                cropped.scale(int(width / scale_factor), int(height / scale_factor))

            return cropped

        region_width = context.region.width
        region_height = context.region.height

        square_bbox, cropped_dimensions = get_square_view_bbox(debug=False)

        if image := render_viewport():
            cropped = crop_image(image, square_bbox, cropped_dimensions)

            obj.preview_ensure()
            obj.preview.image_size = cropped.size

            try:
                obj.preview.image_pixels_float[:] = cropped.pixels   # CodeManX is a legend, see https://blender.stackexchange.com/a/3678/33919
            except Exception as e:
                print("something failed ugh")
                print(e)

                print("cropped pixels")
                print(cropped.pixels)

            os.unlink(image.filepath)

            bpy.data.images.remove(image, do_unlink=True)
            bpy.data.images.remove(cropped, do_unlink=True)  

class UpdateAssetThumbnail(bpy.types.Operator):
    bl_idname = "machin3.update_asset_thumbnail"
    bl_label = "MACHIN3: Update Asset Thumbnail"
    bl_description = "Update the Asset Thumbnail via a Viewport Render of the Active Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT' and context.area:
            if context.area.type == 'FILE_BROWSER' and context.area.ui_type == 'ASSETS':
                if get_3dview_area(context) and context.selected_objects:
                    active, id_type, local_id = get_asset_ids(context)
                    return active and id_type == 'OBJECT' and local_id

            elif context.area.type == 'VIEW_3D':
                active = context.active_object
                return bool(active and is_local_assembly_asset(active))

    def execute(self, context):
        is_3d_view = context.area.type == 'VIEW_3D'

        if is_3d_view:

            active = context.active_object
            local_id = is_local_assembly_asset(active)
            
            sel = [active]

        else:
            _, _, local_id = get_asset_ids(context)

            sel = [obj for obj in context.selected_objects]

        asset_bbox, _ = CreateAssemblyAsset.get_asset_bbox(self, sel, debug=False)

        if asset_bbox:
            if is_3d_view:
                CreateAssemblyAsset.create_asset_thumbnail(self, context, local_id, asset_bbox)

            else:
                area = get_3dview_area(context)
                region, region_data = get_window_region_from_area(area)

                with context.temp_override(area=area, region=region, region_data=region_data):
                    CreateAssemblyAsset.create_asset_thumbnail(self, context, local_id, asset_bbox)

        else:
            draw_fading_label(context, text="Could not create Asset Thumbnail from current Selection of Objects", color=red, move_y=30, time=3)
            return {'CANCELLED'}
        return {'FINISHED'}

class RemoveAssemblyAsset(bpy.types.Operator):
    bl_idname = "machin3.remove_assembly_asset"
    bl_label = "MACHIN3: Remove Assembly Asset"
    bl_description = "description"
    bl_options = {'REGISTER', 'UNDO'}

    remove_asset: BoolProperty(name="Remove entire Local Asset")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if is_instance_collection(obj)]

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

        column.label(text="This will remove the entire asset from the .blend file!", icon_value=get_icon('error'))
        column.label(text="It will no longer be available in the asset browser after this operation.", icon='BLANK1')

    @classmethod
    def description(cls, context, properties):
        if properties.remove_asset:
            return "Remove entire Local Assembly Asset from the file. Careful, this removes it from from the Asset Browser too"
        else:
            return "Remove Assembly Object.\nIf its instance collection has no other users, remove it and the contained objects too"

    def invoke(self, context, event):
        if self.remove_asset:
            return context.window_manager.invoke_props_dialog(self, width=400)

        return self.execute(context)

    def execute(self, context):
        draw_legacy_message = False

        assemblies = [obj for obj in context.selected_objects if is_instance_collection(obj)]

        asset_cols = set(obj.instance_collection for obj in assemblies if not obj.library)

        if self.remove_asset:
            other_assemblies = [obj for obj in bpy.data.objects if obj not in assemblies and is_instance_collection(obj) and obj.instance_collection in asset_cols]

        legacy_offset_map = {}

        for obj in assemblies:
            if not obj.instance_collection.M3.is_asset_collection:
                legacy_offset_map[obj.instance_collection] = obj.matrix_world.copy()

        for obj in assemblies:
            bpy.data.objects.remove(obj, do_unlink=True)

        if self.remove_asset:
            for obj in other_assemblies:
                bpy.data.objects.remove(obj, do_unlink=True)

        for col in asset_cols:
            if not col.users_dupli_group:

                if col.M3.is_asset_collection:
                    for obj in col.objects:
                        remove_obj(obj)

                else:
                    ensure_visibility(context, list(col.objects), select=True)

                    for obj in col.objects:
                        if not obj.parent:
                            obj.matrix_world = legacy_offset_map[col] @ obj.matrix_world

                    draw_legacy_message = True

                bpy.data.collections.remove(col, do_unlink=True)

        main_asset_col = bpy.data.collections.get('_Assets')

        if main_asset_col and not (main_asset_col.children or main_asset_col.objects):
            bpy.data.collections.remove(main_asset_col, do_unlink=True)

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        if draw_legacy_message:
            draw_fading_label(context, text=["Legacy Asset Objects have been disassembled, but not removed automatically!", "This is because MACHIN3tools can't be sure they aren't the original objects", "Please remove manually, if desired"], color=[yellow, white], move_y=60, time=6)

        return {'FINISHED'}

class DisassembleAssembly(bpy.types.Operator):
    bl_idname = "machin3.disassemble_assembly"
    bl_label = "MACHIN3: Disassemble Assembly"
    bl_description = "Make Assembly Objects (Instance Collection) accessible"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if is_instance_collection(obj)]

    def execute(self, context):
        assemblies = [obj for obj in context.selected_objects if is_instance_collection(obj)]

        MakeIDLocal.make_obj_data_icol_local(self, context)

        objects = []

        for obj in assemblies:
            objects.extend(self.disassemble_assembly(context, obj))

        root_objects = [obj for obj in objects if not get_parent(obj)]

        if root_objects:
            context.view_layer.objects.active = root_objects[0]
            root_objects[0].select_set(True)

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        return {'FINISHED'}

    def disassemble_assembly(self, context, obj): 
        master_col = context.scene.collection

        mx = obj.matrix_world.copy()
        cols = [col for col in obj.users_collection]

        asset_col = obj.instance_collection
        asset_objects = [obj for obj in asset_col.objects]

        bpy.data.objects.remove(obj, do_unlink=True)

        for obj in asset_objects:
            if obj.name not in master_col.objects:     # just a pre-caution, should never be needed
                master_col.objects.link(obj)

        if asset_col.users_dupli_group:
            objects = duplicate_objects(context, asset_objects)   # NOTE: also ensures visibility on local view and takes care of visibility states including hide_viewport

            for obj in asset_objects:
                master_col.objects.unlink(obj)

        else:
            objects = asset_objects

        for obj in objects:
            for col in obj.users_collection:
                col.objects.unlink(obj)

        for obj in objects:
            for col in cols:
                col.objects.link(obj)

        for obj in objects:
            obj.hide_set(obj.M3.hide)
            obj.hide_viewport = obj.M3.hide_viewport

        for obj in objects:
            if not obj.parent:
                offsetmx = get_loc_matrix(asset_col.instance_offset)
                obj.matrix_world = mx @ offsetmx.inverted_safe() @ obj.matrix_world

        if any(obj.rigid_body for obj in objects):
            if not context.scene.rigidbody_world:
                bpy.ops.rigidbody.world_add()

            for obj in objects:
                if obj.rigid_body:

                    with context.temp_override(object=obj):
                        bpy.ops.rigidbody.object_add(type=obj.rigid_body.type)

            bpy.ops.ptcache.bake_all(bake=True)

        return objects

class MakeIDLocal(bpy.types.Operator):
    bl_idname = "machin3.make_id_local"
    bl_label = "MACHIN3: Make IDs Local"
    bl_options = {'REGISTER', 'UNDO'}

    force: BoolProperty(name="Force Making Everything Local")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if is_linked_object(obj)]

    @classmethod
    def description(cls, context, properties):
        count = 0

        for obj in context.selected_objects:
            count += len(is_linked_object(obj))

        if count and not any(obj.library for obj in context.selected_objects):
            desc = "Make object data, including instance collections local"

        else:
            desc = "Make linked objects local"
            desc += "\nSHIFT: make object data, including instance collections local"

        desc += f"\n\nSelection contains {count} linked data blocks"
        return desc

    def invoke(self, context, event):
        self.force = event.shift
        return self.execute(context)

    def execute(self, context):
        if any(obj.library for obj in context.selected_objects) and not self.force:
            bpy.ops.object.make_local(type="SELECT_OBJECT")
    
        else:
            self.make_obj_data_icol_local(context)

        return {'FINISHED'}

    def make_obj_data_icol_local(self, context):
        objects = []
        collections = []

        bpy.ops.object.make_local(type="SELECT_OBDATA")

        for obj in context.selected_objects:
            if linked := is_linked_object(obj):
                for id in linked:
                    if type(id) is bpy.types.Collection:
                        collections.append(id)

                    elif type(id) is bpy.types.Object:
                        objects.append(id)

        for col in collections:
            col.make_local(clear_proxy=True, clear_liboverride=True, clear_asset_data=True)

        if objects:
            with context.temp_override(selected_objects=objects):
                bpy.ops.object.make_local(type="SELECT_OBDATA")

class AssetBrowserBookmark(bpy.types.Operator):
    bl_idname = "machin3.assetbrowser_bookmark"
    bl_label = "MACHIN3: Assetbrowser Bookmark"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index", default=1, min=0, max=10)
    save_bookmark: BoolProperty(name="Save Bookmark", default=False)
    clear_bookmark: BoolProperty(name="Clear Bookmark", default=False)
    @classmethod
    def poll(cls, context):
        if context.area:
            return context.area.type == 'FILE_BROWSER' and context.area.ui_type == 'ASSETS'

    @classmethod
    def description(cls, context, properties):
        idx = str(properties.index)
        desc = f"Bookmark: {idx}"

        if idx == '0':
            desc += "\n Library: Current File"
            return desc

        bookmarks = get_assetbrowser_bookmarks(force=True)
        bookmark = bookmarks[idx]

        libref, _, catalog = get_libref_and_catalog(context, bookmark=bookmark)

        if catalog:
            if libref == 'ALL':
                desc += f"\n Library: ALL ({libref})"
            else:
                desc += f"\n Library: {libref}"

            desc += f"\n Catalog: {catalog['catalog']}"

        elif libref:
            desc += f"\n Library: {libref}"

        else:
            desc += "\n None"

        if catalog:
            desc += "\n\nClick: Jump to this Bookmark's Library and Catalog"
        else:
            desc += "\n"

        desc += "\nSHIFT: Save the current Library and Catalog on this Bookmark"

        if catalog:
            desc += "\nCTRL: Remove the stored Bookmark"

        return desc

    def draw(self, context):
        layout = self.layout
        _column = layout.column(align=True)

    def invoke(self, context, event):
        self.save_bookmark = event.shift
        self.clear_bookmark = event.ctrl

        space = context.space_data
        catalogs = get_catalogs_from_asset_libraries(context, debug=False)
        bookmarks = get_assetbrowser_bookmarks(force=True)

        if self.save_bookmark:
            libref = get_asset_library_reference(space.params)
            catalog_id = space.params.catalog_id
            display_size = space.params.display_size
            display_type = space.params.display_type

            if catalog_id in catalogs:
                bookmark = {'libref': libref,
                            'catalog_id': catalog_id,
                            'display_size': display_size,
                            'display_type': display_type,
                            'valid': True}

                bookmarks[str(self.index)] = bookmark

                set_assetbrowser_bookmarks(bookmarks)

                if getattr(context.window_manager, 'M3_screen_cast', False):
                    force_ui_update(context)

            else:

                print("  WARNING: no catalog found under this id! Reload the blend file? Restart Blender?")
                return {'CANCELLED'}

        elif self.clear_bookmark:
            bookmark = bookmarks.get(str(self.index), None)
            
            if bookmark:

                bookmarks[str(self.index)] = {key: None for key in asset_browser_bookmark_props}
                
                set_assetbrowser_bookmarks(bookmarks)

                if getattr(context.window_manager, 'M3_screen_cast', False):
                    force_ui_update(context)

            else:
                print(f" WARNING: no bookmark found for {self.index}. This should not happen! Reload the blend file.")
                return {'CANCELLED'}

        else:

            if self.index == 0:
                set_asset_library_reference(space.params, 'LOCAL')

                if catalog_id := get_most_used_local_catalog_id():
                    space.params.catalog_id = catalog_id

                    space.params.display_size = get_display_size_from_area(context)

            else:
                bookmark = bookmarks.get(str(self.index), None)

                if bookmark:
                    libref = bookmark.get('libref', None)
                    catalog_id = bookmark.get('catalog_id', None)
                    display_size = bookmark.get('display_size', None)
                    display_type = bookmark.get('display_type', None)
                    valid = bookmark.get('valid', None)

                    if libref and catalog_id:

                        if validate_libref_and_catalog(context, libref, catalog_id):
                            params = space.params

                            set_asset_library_reference(params, libref)
                            params.catalog_id = catalog_id
                            params.display_size = display_size
                            params.display_type = display_type

                            if not valid:
                                bookmark['valid'] = True

                                set_assetbrowser_bookmarks(bookmarks)

                        else:
                            bookmark['valid'] = False

                            set_assetbrowser_bookmarks(bookmarks)

                else:
                    print(f" WARNING: no bookmark found for {self.index}. This should not happen! Reload the blend file.")
                    return {'CANCELLED'}

        return {'FINISHED'}
