bl_info = {
    "name": "DECALmachine",
    "author": "MACHIN3, AR, MX, proxeIO, mem, Justo Figueroa",
    "version": (2, 11, 2),
    "blender": (3, 6, 0),
    "location": "Pie Menu: D key, MACHIN3 N Panel",
    "revision": "f2520fffc921649bae4d35b98c7914156b9348fc",
    "description": "A complete mesh-decal and trim sheet pipeline: Use decals as objects or use trims on the mesh level, design your own custom decals or import trim sheets, export decal assets via atlasing or baking, etc",
    "warning": "",
    "doc_url": "https://machin3.io/DECALmachine/docs",
    "tracker_url": "https://machin3.io/DECALmachine/docs/faq/#get-support",
    "category": "3D View"}

def reload_modules(name):
    import os
    import importlib

    dbg = False

    from . import registration, items, colors

    for module in [registration, items, colors]:
        importlib.reload(module)

    utils_modules = sorted([name[:-3] for name in os.listdir(os.path.join(__path__[0], "utils")) if name.endswith('.py')])

    for module in utils_modules:
        impline = "from . utils import %s" % (module)

        if dbg:
            print(f"reloading {name}.utils.{module}")

        exec(impline)
        importlib.reload(eval(module))

    from . import handlers
    
    if dbg:
        print("reloading", handlers.__name__)

    importlib.reload(handlers)

    modules = []

    for label in registration.classes:
        entries = registration.classes[label]
        for entry in entries:
            path = entry[0].split('.')
            module = path.pop(-1)

            if (path, module) not in modules:
                modules.append((path, module))

    for path, module in modules:
        if path:
            impline = f"from . {'.'.join(path)} import {module}"
        else:
            impline = f"from . import {module}"

        if dbg:
            print(f"reloading {name}.{'.'.join(path)}.{module}")

        exec(impline)
        importlib.reload(eval(module))

if 'bpy' in locals():
    reload_modules(bl_info['name'])

from typing import Tuple
import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, CollectionProperty, IntVectorProperty
import os
from time import time
from . properties import DecalSceneProperties, DecalObjectProperties, DecalMaterialProperties, DecalImageProperties, DecalCollectionProperties, ExcludeCollection
from . utils.assets import verify_assetspath
from . utils.registration import get_path, get_core, get_menus, get_tools, get_gizmos, get_prefs, register_classes, unregister_classes, register_keymaps, unregister_keymaps
from . utils.registration import register_decals, unregister_decals, register_instant_decals, unregister_instant_decals, register_lockedlib, unregister_lockedlib
from . utils.registration import register_trims, unregister_trims, register_atlases
from . utils.registration import register_icons, unregister_icons, register_infotextures, unregister_infotextures, register_infofonts, unregister_infofonts, register_trimtextures, unregister_trimtextures
from . utils.system import get_PIL_image_module_path, verify_user_sitepackages, verify_update, install_update
from . handlers import undo_and_redo_post, load_post, depsgraph_update_post

def update_check():
    def hook(resp, *args, **kwargs):
        if resp:
            if resp.text == 'true':
                get_prefs().update_available = True

            else:
                get_prefs().update_available = False

            if debug:
                print(" received response:", resp.text)

            write_update_check(update_path, time(), debug=debug)

    def init_update_check(debug=False):
        if debug:
            print()
            print("initiating update check for version", bl_info['version'])

        import platform
        import hashlib
        from . modules.requests_futures.sessions import FuturesSession

        machine = hashlib.sha1(platform.node().encode('utf-8')).hexdigest()[0:7]

        headers = {'User-Agent': f"{bl_info['name']}/{'.'.join([str(v) for v in bl_info.get('version')])} Blender/{'.'.join([str(v) for v in bpy.app.version])} ({platform.uname()[0]}; {platform.uname()[2]}; {platform.uname()[4]}; {machine})"}
        session = FuturesSession()

        try:
            if debug:
                print(" sending update request")

            session.post("https://drum.machin3.io/update", data={'revision': bl_info['revision']}, headers=headers, hooks={'response': hook})
        except:
            pass

    def write_update_check(update_path, update_time, debug=False):
        if debug:
            print()
            print("writing update check data")

        update_available = get_prefs().update_available

        msg = [f"version: {'.'.join(str(v) for v in bl_info['version'])}",
               f"update time: {update_time}",
               f"update available: {update_available}\n"]

        with open(update_path, mode='w') as f:
            f.write('\n'.join(m for m in msg))

        if debug:
            print(" written to", update_path)

        return update_time, update_available

    def read_update_check(update_path, debug=False) -> Tuple[bool, tuple, float, bool]:
        if debug:
            print()
            print(f"reading {bl_info['name']} update check data")

        with open(update_path) as f:
            lines = [l[:-1] for l in f.readlines()]

        if len(lines) == 3:
            version_str = lines[0].replace('version: ', '')
            update_time_str = lines[1].replace('update time: ', '')
            update_available_str = lines[2].replace('update available: ', '')

            if debug:
                print(" fetched update available:", update_available_str)
                print(" fetched update time:", update_time_str)

            try:
                version = tuple(int(v) for v in version_str.split('.'))
            except:
                version = None

            try:
                update_time = float(update_time_str)
            except:
                update_time = None

            try:
                update_available = True if update_available_str == 'True' else False if update_available_str == 'False' else None
            except:
                update_available = None

            if version is not None and update_time is not None and update_available is not None:
                return True, version, update_time, update_available

        return False, None, None, None

    debug = False

    update_path = os.path.join(get_path(), 'update_check')

    if not os.path.exists(update_path):
        if debug:
            print(f"init {bl_info['name']} update check as file does not exist")

        init_update_check(debug=debug)

    else:
        valid, version, update_time, update_available = read_update_check(update_path, debug=debug)

        if valid:

            if debug:
                print(f" comparing stored {bl_info['name']} version:", version, "with bl_info['version']:", bl_info['version'])

            if version != bl_info['version']:
                if debug:
                    print(f"init {bl_info['name']} update check, as the versions differ due to user updating the addon since the last update check")

                init_update_check(debug=debug)
                return

            now = time()
            delta_time = now - update_time

            if debug:
                print(" comparing", now, "and", update_time)
                print("  delta time:", delta_time)

            if delta_time > 72000:
                if debug:
                    print(f"init {bl_info['name']} update check, as it has been over 20 hours since the last one")

                init_update_check(debug=debug)
                return

            if debug:
                print(f"no {bl_info['name']} update check required, setting update available prefs from stored file")

            get_prefs().update_available = update_available

        else:
            if debug:
                print(f"init {bl_info['name']} update check as fetched file is invalid")

            init_update_check(debug=debug)

def register():
    global classes, keymaps, icons

    core_classes = register_classes(get_core())

    bpy.types.Scene.DM = PointerProperty(type=DecalSceneProperties)
    bpy.types.Object.DM = PointerProperty(type=DecalObjectProperties)
    bpy.types.Material.DM = PointerProperty(type=DecalMaterialProperties)
    bpy.types.Image.DM = PointerProperty(type=DecalImageProperties)
    bpy.types.Collection.DM = PointerProperty(type=DecalCollectionProperties)

    bpy.types.WindowManager.matchmaterial = EnumProperty(name="Materials, that can be matched", description="Match specificly selected Material only", items=[("None", "None", "Blender White", 0, 0), ("Default", "Default", "DECALmachine Metal", 0, 1)])

    bpy.types.WindowManager.collectinfotextures = BoolProperty()
    bpy.types.WindowManager.excludeimages = CollectionProperty(type=ExcludeCollection)

    bpy.types.WindowManager.collectinfofonts = BoolProperty()
    bpy.types.WindowManager.excludefonts = CollectionProperty(type=ExcludeCollection)
    bpy.types.WindowManager.collecttrimtextures = BoolProperty()

    bpy.types.WindowManager.decal_mousepos = IntVectorProperty(name="Mouse Position for Decal Insertion", size=2)

    assetspath = verify_assetspath()

    decals = register_decals()
    trims = register_trims()
    atlases = register_atlases()
    register_instant_decals()
    register_lockedlib()

    register_infotextures()
    register_infofonts()
    register_trimtextures()

    menu_classlists, menu_keylists = get_menus()
    tool_classlists, tool_keylists = get_tools()
    gizmo_classlists = get_gizmos()

    classes = register_classes(menu_classlists + tool_classlists + gizmo_classlists) + core_classes
    keymaps = register_keymaps(menu_keylists + tool_keylists)

    icons = register_icons()

    bpy.app.handlers.undo_post.append(undo_and_redo_post)
    bpy.app.handlers.redo_post.append(undo_and_redo_post)

    bpy.app.handlers.load_post.append(load_post)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post)

    try:
        verify_user_sitepackages()

        import PIL
        from PIL import Image

        Image.MAX_IMAGE_PIXELS = None

        get_prefs().pil = True
        get_prefs().pilrestart = False
        path = get_PIL_image_module_path(Image)
    except:
        get_prefs().pil = False
        get_prefs().pilrestart = False
        path = ''

    if get_prefs().registration_debug:

        print(f"Registered {bl_info['name']} {'.'.join([str(i) for i in bl_info['version']])} with {len(decals)} decal libraries, {len(trims)} trim sheet libraries and {len(atlases)} atlases.", f"PIL {PIL.__version__} Image Module: {path}" if get_prefs().pil else "PIL is not installed.")
        print("Decals, Trimsheets and Atlases are located in", assetspath)

        for libname, libtype, _ in decals + trims:
            print(f" • {libtype} library: {libname}")

        for atlas in atlases:
            print(f" • atlas: {atlas}")

    update_check()

    verify_update()

def unregister():
    global classes, keymaps, icons

    debug = get_prefs().registration_debug
    keep_assets = get_prefs().update_keep_assets

    from . handlers import trimgridVIEW3D

    if trimgridVIEW3D and "RNA_HANDLE_REMOVED" not in str(trimgridVIEW3D):
        bpy.types.SpaceView3D.draw_handler_remove(trimgridVIEW3D, 'WINDOW')

    bpy.app.handlers.redo_post.remove(undo_and_redo_post)
    bpy.app.handlers.undo_post.remove(undo_and_redo_post)

    bpy.app.handlers.load_post.remove(load_post)
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post)

    unregister_decals()
    unregister_instant_decals()
    unregister_lockedlib()

    unregister_trims()

    unregister_infotextures()
    unregister_infofonts()
    unregister_trimtextures()

    unregister_keymaps(keymaps)

    unregister_icons(icons)

    del bpy.types.Scene.DM
    del bpy.types.Object.DM
    del bpy.types.Material.DM
    del bpy.types.Image.DM
    del bpy.types.Collection.DM

    del bpy.types.WindowManager.matchmaterial

    del bpy.types.Scene.userdecallibs
    del bpy.types.WindowManager.newdecalidx
    del bpy.types.WindowManager.decaluuids
    del bpy.types.WindowManager.paneldecals
    del bpy.types.WindowManager.instantdecaluuids

    del bpy.types.WindowManager.trimsheets
    del bpy.types.WindowManager.atlases

    del bpy.types.WindowManager.collectinfotextures
    del bpy.types.WindowManager.excludeimages

    del bpy.types.WindowManager.collectinfofonts
    del bpy.types.WindowManager.excludefonts
    del bpy.types.WindowManager.decal_mousepos

    del bpy.types.WindowManager.instanttrimsheetcount
    del bpy.types.WindowManager.instantatlascount

    unregister_classes(classes)

    if debug:
        print("Unregistered %s %s" % (bl_info["name"], ".".join([str(i) for i in bl_info['version']])))

    install_update(keep_assets=keep_assets)
