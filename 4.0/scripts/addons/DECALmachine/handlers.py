import bpy
from bpy.app.handlers import persistent
import os
import shutil
from . import bl_info
from . utils.material import set_match_material_enum
from . utils.registration import get_prefs, reload_infotextures, reload_infofonts, reload_trimtextures, reload_decal_libraries, reload_trim_libraries
from . utils.system import abspath


@persistent
def update_match_material_enum(none):
    set_match_material_enum()

    scene = bpy.context.scene
    revision = bl_info.get("revision")

    if revision and not scene.DM.revision:
        scene.DM.revision = revision


@persistent
def update_userdecallibs_enum(none):
    scene = bpy.context.scene

    if scene.userdecallibs:
        if scene.userdecallibs not in [lib[0] for lib in bpy.types.Scene.userdecallibs.keywords['items']]:
            print(f"WARNING: The active userdecallib '{scene.userdecallibs}' defined in this blend file, could not be found among the registered decal libaries. Updating property by reloading decal libraries. Re-saving blend file is recommended.")
            reload_decal_libraries()
    elif [lib for lib in get_prefs().decallibsCOL if not lib.istrimsheet]:
        print("WARNING: No unlocked Decal Libraries registered!")
    else:
        print("WARNING: No valid Decal Libraries registered!")


    if scene.trimsheetlibs:
        if scene.trimsheetlibs not in [lib[0] for lib in bpy.types.Scene.trimsheetlibs.keywords['items']]:
            print(f"WARNING: The active trimsheetlib '{scene.trimsheetlibs}' defined in this blend file, could not be found among the registered trim sheet libaries. Updating property by reloading trim sheet libraries. Re-saving blend file is recommended.")
            reload_trim_libraries()
    else:
        print("WARNING: No Trimsheet Libraries registered!")


@persistent
def update_texture_sources(none):
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


@persistent
def init_channel_packs(none):
    dm = bpy.context.scene.DM

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
