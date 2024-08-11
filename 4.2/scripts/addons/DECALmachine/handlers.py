import bpy
from bpy.app.handlers import persistent
import os
import shutil
from . import bl_info
from . utils.application import delay_execution
from . utils.material import set_match_material_enum, get_legacy_materials
from . utils.registration import get_prefs, reload_infotextures, reload_infofonts, reload_trimtextures, reload_decal_libraries, reload_trim_libraries, get_version_from_blender, get_version_as_float, get_resources_path
from . utils.object import get_active_object, get_visible_objects
from . utils.system import abspath
from . utils.draw import draw_fading_label, draw_trim_grid_VIEW3D
from . utils.workspace import get_3dview_area, get_window_region_from_area
from . colors import red, yellow, green

global_debug = False

def manage_match_material_enum():
    global global_debug

    debug = global_debug
    debug = False

    if debug:
        print("  match material enum")

    set_match_material_enum(debug=debug)

    scene = getattr(bpy.context, 'scene', None)

    if scene:
        revision = bl_info.get("revision")

        if revision and not scene.DM.revision:
            scene.DM.revision = revision

def manage_user_decal_lib():
    global global_debug

    debug = global_debug
    debug = False

    if debug:
        print("  user decal lib")

    scene = getattr(bpy.context, 'scene', None)

    if scene:
        if scene.userdecallibs:
            if scene.userdecallibs not in [lib[0] for lib in bpy.types.Scene.userdecallibs.keywords['items']]:
                if debug:
                    print(f"   active userdecallib '{scene.userdecallibs}' defined in this blend file, could not be found among the registered decal libaries")
                else:
                    print(f"WARNING: The active userdecallib '{scene.userdecallibs}' defined in this blend file, could not be found among the registered decal libaries. Updating property by reloading decal libraries. Re-saving blend file is recommended.")
                reload_decal_libraries()

        elif [lib for lib in get_prefs().decallibsCOL if not lib.istrimsheet]:
            if debug:
                print("   no unlocked Decal Libraries registered!")
            else:
                print("WARNING: No unlocked Decal Libraries registered!")

        else:
            if debug:
                print("   no valid Decal Libraries registered!")
            else:
                print("WARNING: No valid Decal Libraries registered!")

        if scene.trimsheetlibs:
            if scene.trimsheetlibs not in [lib[0] for lib in bpy.types.Scene.trimsheetlibs.keywords['items']]:
                if debug:
                    print(f"   active trimsheetlib '{scene.trimsheetlibs}' defined in this blend file, could not be found among the registered trim sheet libaries")
                else:
                    print(f"WARNING: The active trimsheetlib '{scene.trimsheetlibs}' defined in this blend file, could not be found among the registered trim sheet libaries. Updating property by reloading trim sheet libraries. Re-saving blend file is recommended.")
                reload_trim_libraries()
        else:
            if debug:
                print("   no Trimsheet Libraries registered!")
            else:
                print("WARNING: No Trimsheet Libraries registered!")

def manage_legacy_decalmats():
    global global_debug

    debug = global_debug
    debug = False

    if debug:
        print("  legacy decalmats")

    if get_prefs().show_legacy_assets_in_blend_warnings:

        file_path = bpy.data.filepath
        resources_path = get_resources_path()

        if resources_path not in file_path:
            legacy_dict = get_legacy_materials(force=True, debug=False)

            legacy_decals = legacy_dict['DECAL']
            legacy_sheets = legacy_dict['TRIM']

            if legacy_decals or legacy_sheets:
                context = bpy.context
                area = get_3dview_area(context)

                if area:
                    region, region_data = get_window_region_from_area(area)

                    with context.temp_override(area=area, region=region, region_data=region_data):
                        labels = ["ℹℹ DECALmachine WARNING ℹℹ"]

                        print()

                        if legacy_decals:
                            for version in sorted(legacy_decals):
                                msg = f"Legacy Decals of version {version} found in this .blend file"
                                labels.append(msg)

                                if debug:
                                    print(f"   {msg}")
                                else:
                                    print("WARNING:", msg)

                        if legacy_sheets:
                            for version in sorted(legacy_sheets):
                                msg = f"Legacy Trim Sheets of version {version} found in this .blend file"
                                labels.append(msg)

                                if debug:
                                    print(f"   {msg}")
                                else:
                                    print("WARNING:", msg)

                        labels.append("Please update them, before you continue to work in this file with DECALmachine")

                        if not debug:
                            print("INFO: Please update them, before you continue to work in this file with DECALmachine")
                            print()

                        draw_fading_label(context, labels, color=[red, *[yellow for i in range(len(legacy_decals) + len(legacy_sheets))], green], cancel='LEGACY_MATERIALS')

        else:
            if debug:
                print("   avoiding legacy decal/trimsheet check")
            else:
                print("INFO: avoiding legacy decal/trimsheet check")

def manage_channel_pack_collection():
    global global_debug

    debug = global_debug
    debug = False

    if debug:
        print("  export channel packs collection")

    scene = getattr(bpy.context, 'scene', None)

    if scene:
        dm = scene.DM

        channel_packs = dm.export_atlas_texture_channel_packCOL

        if not channel_packs:
            aocurvheight = channel_packs.add()
            aocurvheight.avoid_update = True
            aocurvheight.name = 'ao_curv_height'
            aocurvheight.red = 'AO'
            aocurvheight.green = 'CURVATURE'
            aocurvheight.blue = 'HEIGHT'

            masks = channel_packs.add()
            masks.avoid_update = True
            masks.name = 'masks'
            masks.red = 'ALPHA'
            masks.green = 'SUBSET'
            masks.blue = 'SUBSETOCCLUSION'

def manage_texture_sources():
    global global_debug

    debug = global_debug
    debug = False

    if debug:
        print("  texture sources")

    wm = bpy.context.window_manager

    if wm.collectinfotextures:
        lastop = wm.operators[-1] if wm.operators else None
        newimages = ([img for img in bpy.data.images if img.name not in wm.excludeimages and len(img.name) < 63 and any(img.name.lower().endswith(ending) for ending in ['.png'])])

        if (lastop and lastop.bl_idname != 'MACHIN3_OT_load_images') or newimages:
            wm.collectinfotextures = False
            wm.excludeimages.clear()

            if newimages:
                assetspath = get_prefs().assetspath
                createpath = os.path.join(assetspath, "Create")
                infopath = os.path.join(createpath, "infotextures")

                default = newimages[-1].name
                for img in newimages:
                    shutil.copy(abspath(img.filepath), os.path.join(infopath, img.name[:-3] + img.name[-3:].lower()))
                    bpy.data.images.remove(img, do_unlink=True)

                reload_infotextures(default=default)
    if wm.collectinfofonts:
        lastop = wm.operators[-1] if wm.operators else None
        newfonts = ([font for font in bpy.data.fonts if font.name not in wm.excludefonts and len(font.name) < 63])
        if (lastop and lastop.bl_idname != 'MACHIN3_OT_load_fonts') or newfonts:
            wm.collectinfofonts = False
            wm.excludefonts.clear()
            if newfonts:
                assetspath = get_prefs().assetspath
                createpath = os.path.join(assetspath, "Create")
                fontspath = os.path.join(createpath, "infofonts")

                default = newfonts[-1].name + ".ttf"
                for font in newfonts:
                    shutil.copy(abspath(font.filepath), os.path.join(fontspath, font.name + ".ttf"))
                    bpy.data.fonts.remove(font, do_unlink=True)

                reload_infofonts(default=default)

    if wm.collecttrimtextures:
        lastop = wm.operators[-1] if wm.operators else None
        newimages = [img for img in bpy.data.images if img.name not in wm.excludeimages and len(img.name) < 63 and any(img.name.lower().endswith(ending) for ending in ['.png'])]

        if (lastop and lastop.bl_idname != 'MACHIN3_OT_load_trimsheet_textures') or newimages:
            wm.collecttrimtextures = False
            wm.excludeimages.clear()

            if newimages:
                assetspath = get_prefs().assetspath
                createpath = os.path.join(assetspath, "Create")
                trimpath = os.path.join(createpath, "trimtextures")

                for img in newimages:
                    shutil.copy(abspath(img.filepath), os.path.join(trimpath, img.name[:-3] + img.name[-3:].lower()))
                    bpy.data.images.remove(img, do_unlink=True)

                reload_trimtextures()

trimgridVIEW3D = None

def manage_trimsheet_grid_VIEW3D():
    global global_debug, trimgridVIEW3D

    debug = global_debug
    debug = False

    if debug:
        print("  trimheet grid VIEW3D")

    if trimgridVIEW3D and "RNA_HANDLE_REMOVED" in str(trimgridVIEW3D):
        trimgridVIEW3D = None

    active = get_active_object(bpy.context)

    if active:
        dm = active.DM

        draw = dm.trimsnappingdraw or (dm.trimsnappingobject and dm.trimsnappingobjectedgesdraw)

        if dm.istrimsheet and dm.trimsnapping and draw:

            if not trimgridVIEW3D:
                if debug:
                    print("   adding new draw handler")

                trimgridVIEW3D = bpy.types.SpaceView3D.draw_handler_add(draw_trim_grid_VIEW3D, (bpy.context,), 'WINDOW', 'POST_VIEW')
            return
    
    if trimgridVIEW3D:
        if debug:
            print("   removing draw handler")

        bpy.types.SpaceView3D.draw_handler_remove(trimgridVIEW3D, 'WINDOW')
        trimgridVIEW3D = None

was_asset_drop_cleanup_executed = False

def manage_asset_drop_cleanup():
    global global_debug, was_asset_drop_cleanup_executed

    debug = global_debug
    debug = False

    if debug:
        print("  DM asset drop management")

    if was_asset_drop_cleanup_executed:
        if debug:
            print("   skipping second (duplicate) run")

        was_asset_drop_cleanup_executed = False
        return

    if debug:
        print("   checking for asset drop cleanup")

    C = bpy.context

    if C.mode == 'OBJECT':
        operators = C.window_manager.operators
        active = active if (active := get_active_object(C)) and active.type == 'EMPTY' and active.instance_collection and active.instance_type == 'COLLECTION' else None

        if active and operators:
            lastop = operators[-1]

            if lastop.bl_idname == 'OBJECT_OT_transform_to_mouse':
                if debug:
                    print()
                    print("    asset drop detected!")

                visible = get_visible_objects(C)

                for obj in visible:
                    if obj.DM.isbackup:
                        if debug:
                            print("     decal backup object:", obj.name)

                        for col in obj.users_collection:
                            if debug:
                                print(f"      unlinking from {col.name}")

                            col.objects.unlink(obj)

            was_asset_drop_cleanup_executed = True

@persistent
def undo_and_redo_post(scene):
    global global_debug

    if global_debug:
        print()
        print("DECALmachine undo/redo post handler:")
        print(" managing match material enum")

    delay_execution(manage_match_material_enum)

@persistent
def load_post(none):
    global global_debug

    if global_debug:
        print()
        print("DECALmachine load post handler:")

    if global_debug:
        print(" managing match material enum")

    delay_execution(manage_match_material_enum)

    if global_debug:
        print(" managing user decal lib")

    delay_execution(manage_user_decal_lib)

    if global_debug:
        print(" managing legacy decal mats")

    delay_execution(manage_legacy_decalmats)

    if global_debug:
        print(" managing channel packs")

    delay_execution(manage_channel_pack_collection)

@persistent
def depsgraph_update_post(scene):
    global global_debug

    if global_debug:
        print()
        print("DECALmachine depsgraph update post handler:")

    if global_debug:
        print(" managing texture sources")

    delay_execution(manage_texture_sources)

    if global_debug:
        print(" managing trimsheet grid VIEW3D")

    delay_execution(manage_trimsheet_grid_VIEW3D)

    if global_debug:
        print(" managing asset drop cleanup")

    delay_execution(manage_asset_drop_cleanup)
