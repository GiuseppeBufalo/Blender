bl_info = {
    "name": "DECALmachine",
    "author": "MACHIN3, AR, MX, proxeIO",
    "version": (2, 7, 2),
    "blender": (3, 3, 0),
    "location": "Pie Menu: D key, MACHIN3 N Panel",
    "revision": "f2520fffc921649bae4d35b98c7914156b9348fc",
    "description": "A complete mesh-decal and trim sheet pipeline: Use decals as objects or use trims on the mesh level, design your own custom decals or import trim sheets, export decal assets via atlasing or baking, etc",
    "warning": "",
    "doc_url": "https://machin3.io/DECALmachine/docs",
    "tracker_url": "https://machin3.io/DECALmachine/docs/faq/#get-support",
    "category": "Mesh"}


def reload_modules(name):

    import os
    import importlib

    utils_modules = sorted([name[:-3] for name in os.listdir(os.path.join(__path__[0], "utils")) if name.endswith('.py')])

    for module in utils_modules:
        impline = "from . utils import %s" % (module)

        print("reloading %s" % (".".join([name] + ['utils'] + [module])))

        exec(impline)
        importlib.reload(eval(module))

    from . import registration
    importlib.reload(registration)

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
            impline = "from . %s import %s" % (".".join(path), module)
        else:
            impline = "from . import %s" % (module)

        print("reloading %s" % (".".join([name] + path + [module])))

        exec(impline)
        importlib.reload(eval(module))


if 'bpy' in locals():
    reload_modules(bl_info['name'])


import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, CollectionProperty, IntVectorProperty
from . properties import DecalSceneProperties, DecalObjectProperties, DecalMaterialProperties, DecalImageProperties, DecalCollectionProperties, ExcludeCollection
from . utils.registration import get_core, get_menus, get_tools, get_gizmos, get_prefs, register_classes, unregister_classes, register_keymaps, unregister_keymaps
from . utils.registration import verify_assetspath, register_decals, unregister_decals, register_instant_decals, unregister_instant_decals, register_lockedlib, unregister_lockedlib
from . utils.registration import register_trims, unregister_trims, register_atlases
from . utils.registration import register_icons, unregister_icons, register_infotextures, unregister_infotextures, register_infofonts, unregister_infofonts, register_trimtextures, unregister_trimtextures
from . utils.system import get_PIL_image_module_path, verify_user_sitepackages
from . handlers import update_match_material_enum, update_texture_sources, update_userdecallibs_enum, init_channel_packs


def update_check():
    def hook(resp, *args, **kwargs):
        if resp:
            if resp.text == 'true':
                get_prefs().update_available = True

    import platform
    from . modules.requests_futures.sessions import FuturesSession

    get_prefs().update_available = False

    headers = {'User-Agent': f"DECALmachine/{'.'.join([str(v) for v in bl_info.get('version')])} Blender/{'.'.join([str(v) for v in bpy.app.version])} ({platform.uname()[0]}; {platform.uname()[2]}; {platform.uname()[4]})"}
    session = FuturesSession()

    try:
        session.post("https://drum.machin3.io/update", data={'revision': bl_info['revision']}, headers=headers, hooks={'response': hook})
    except:
        pass


def register():
    global classes, keymaps, icons


    core_classes = register_classes(get_core())



    bpy.types.Scene.DM = PointerProperty(type=DecalSceneProperties)
    bpy.types.Object.DM = PointerProperty(type=DecalObjectProperties)
    bpy.types.Material.DM = PointerProperty(type=DecalMaterialProperties)
    bpy.types.Image.DM = PointerProperty(type=DecalImageProperties)
    bpy.types.Collection.DM = PointerProperty(type=DecalCollectionProperties)

    bpy.types.WindowManager.matchmaterial = EnumProperty(name="Materials, that can be matched", items=[("None", "None", "", 0, 0),
                                                                                                       ("Default", "Default", "", 0, 1)])

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



    bpy.app.handlers.undo_post.append(update_match_material_enum)
    bpy.app.handlers.redo_post.append(update_match_material_enum)
    bpy.app.handlers.load_post.append(update_match_material_enum)

    bpy.app.handlers.load_post.append(update_userdecallibs_enum)

    bpy.app.handlers.depsgraph_update_post.append(update_texture_sources)

    bpy.app.handlers.load_post.append(init_channel_packs)


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



    print(f"Registered {bl_info['name']} {'.'.join([str(i) for i in bl_info['version']])} with {len(decals)} decal libraries, {len(trims)} trim sheet libraries and {len(atlases)} atlases.", f"PIL {PIL.__version__} Image Module: {path}" if get_prefs().pil else "PIL is not installed.")
    print("Decals, Trimsheets and Atlases are located in", assetspath)

    for libname, libtype, _ in decals + trims:
        print(f" • {libtype} library: {libname}")

    for atlas in atlases:
        print(f" • atlas: {atlas}")



    update_check()


def unregister():
    global classes, keymaps, icons


    bpy.app.handlers.undo_post.remove(update_match_material_enum)
    bpy.app.handlers.redo_post.remove(update_match_material_enum)
    bpy.app.handlers.load_post.remove(update_match_material_enum)

    bpy.app.handlers.load_post.remove(update_userdecallibs_enum)

    bpy.app.handlers.depsgraph_update_post.remove(update_texture_sources)

    bpy.app.handlers.load_post.remove(init_channel_packs)



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

    print("Unregistered %s %s" % (bl_info["name"], ".".join([str(i) for i in bl_info['version']])))
