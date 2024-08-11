import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.utils import register_class, unregister_class, previews
import os
import re
from . system import get_new_directory_index, load_json, save_json, makedir, printd, get_folder_contents
from . assets import get_assets_dict, remove_empty_folders
from .. registration import keys as keysdict
from .. registration import classes as classesdict
from .. items import asset_folders

def get_path():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def get_name():
    return os.path.basename(get_path())

def get_prefs():
    return bpy.context.preferences.addons[get_name()].preferences

def get_addon(addon, debug=False):
    import addon_utils

    for mod in addon_utils.modules():
        name = mod.bl_info["name"]
        version = mod.bl_info.get("version", None)
        foldername = mod.__name__
        path = mod.__file__
        enabled = addon_utils.check(foldername)[1]

        if name == addon:
            if debug:
                print(name)
                print("  enabled:", enabled)
                print("  folder name:", foldername)
                print("  version:", version)
                print("  path:", path)
                print()

            return enabled, foldername, version, path
    return False, None, None, None

def get_addon_prefs(addon):
    _, foldername, _, _ = get_addon(addon)
    return bpy.context.preferences.addons.get(foldername).preferences

def get_resources_path():
    return os.path.join(get_path(), "resources")

def get_templates_path():
    if bpy.app.version < (3, 0, 0):
        return os.path.join(get_path(), "resources", "Templates_2.93.blend")
    elif bpy.app.version < (4, 0, 0):
        return os.path.join(get_path(), "resources", "Templates_3.0.blend")
    else:
        return os.path.join(get_path(), "resources", "Templates_4.0.blend")

def get_version_from_blender(use_float=False):
    if bpy.app.version < (3, 0, 0):
        return 2.1 if use_float else '2.1.0'
    elif bpy.app.version < (4, 0, 0):
        return 2.5 if use_float else '2.5.0'
    else:
        return 2.9 if use_float else '2.9.0'

def get_version_as_float(versionstring):
    if versionstring:
        return float('.'.join([v for v in versionstring.split('.')[:2]]))
    else:
        return 1.8

def shape_version(version):
    if type(version) == str:
        version = get_version_as_float(version)

    if version < 2:
        return 1.8
    
    elif version < 2.1:
        return 2.0

    elif version < 2.5:
        return 2.1
    
    elif version < 2.9:
        return 2.5

    elif version == 2.9:
        return 2.9

    else:
        return 3.0

def get_version_filename_from_blender(atlas=False):
    if atlas:
        return '.is20'

    else:
        if bpy.app.version < (3, 0, 0):
            return '.is21'
        elif bpy.app.version < (4, 0, 0):
            return '.is25'
        else:
            return '.is29'

def get_version_filename_from_version(version):
    if version == 1.8:
        return '.is280'

    else:
        return '.is' + ''.join(str(version).split('.'))

def get_version_from_filename(filename):
    if filename == '.is280':
        return '1.8'

    stripped = filename.replace('.is', '')
    return stripped[:1] + '.' + stripped[1:]

def get_version_files(path):
    versionRegex = re.compile(r'\.is[\d]+')
    return sorted(([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and versionRegex.match(f)]))

def is_decal_folder_valid(path):
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return all([f in files for f in ["decal.blend", "decal.png", "uuid"]])

def is_library_corrupted(libpath, verbose=False):
    if verbose:
        corrupted = []

    folders = [f for f in sorted(os.listdir(libpath)) if os.path.isdir(os.path.join(libpath, f))]

    for folder in folders:
        if not is_decal_folder_valid(os.path.join(libpath, folder)):
            if verbose:
                corrupted.append(folder)
            else:
                return True

    if verbose:
        return corrupted
    else:
        return False

def is_library_obsolete(libpath):
    folders = [f for f in sorted(os.listdir(libpath)) if os.path.isdir(os.path.join(libpath, f))]

    if 'blends' in folders and 'icons' in folders:
        blendspath = os.path.join(libpath, 'blends')

        if os.path.exists(texturespath := os.path.join(blendspath, 'textures')) and os.path.isdir(texturespath):
            return True

    return False

def is_library_trimsheet(path, verbose=False):
    if os.path.exists(path):
        folders, files = get_folder_contents(path)

        mandatory = ['.istrimsheet', 'data.json']
        required = ['normal.png', 'color.png']

        if verbose:
            return all(m in files for m in mandatory) and any(r in files for r in required), [folders, files]

        else:
            return all(m in files for m in mandatory) and any(r in files for r in required)

    if verbose:
        return False, [None, None]

    else:
        return False

def is_library_in_assetspath(path):
    is_in_assetspath =  os.path.dirname(path) == os.path.join(get_prefs().assetspath, 'Trims' if is_library_trimsheet(path) else 'Decals')

    return is_in_assetspath

def is_atlas(path):
    if os.path.exists(path):
        mandatory = ['.isatlas', 'data.json']
        contents = [f.lower() for f in os.listdir(path)]

        return all(m in contents for m in mandatory)

    return False

def register_classes(classlists, debug=False):
    classes = []

    for classlist in classlists:
        for fr, imps in classlist:
            impline = "from ..%s import %s" % (fr, ", ".join([i[0] for i in imps]))
            classline = "classes.extend([%s])" % (", ".join([i[0] for i in imps]))

            exec(impline)
            exec(classline)

    for c in classes:
        if debug:
            print("REGISTERING", c)

        register_class(c)

    return classes

def unregister_classes(classes, debug=False):
    for c in classes:
        if debug:
            print("UN-REGISTERING", c)

        unregister_class(c)

def register_keymaps(keylists):
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    keymaps = []

    if kc:
        for keylist in keylists:
            for item in keylist:
                keymap = item.get("keymap")
                space_type = item.get("space_type", "EMPTY")

                if keymap:
                    km = kc.keymaps.new(name=keymap, space_type=space_type)

                    if km:
                        idname = item.get("idname")
                        type = item.get("type")
                        value = item.get("value")

                        shift = item.get("shift", False)
                        ctrl = item.get("ctrl", False)
                        alt = item.get("alt", False)

                        kmi = km.keymap_items.new(idname, type, value, shift=shift, ctrl=ctrl, alt=alt)

                        if kmi:
                            properties = item.get("properties")

                            if properties:
                                for name, value in properties:
                                    setattr(kmi.properties, name, value)

                            keymaps.append((km, kmi))
    else:
        print("WARNING: Keyconfig not availabe, skipping DECALmachine keymaps")

    return keymaps

def unregister_keymaps(keymaps):
    for km, kmi in keymaps:
        km.keymap_items.remove(kmi)

def register_icons():
    path = os.path.join(get_prefs().path, "icons")
    icons = previews.new()

    for i in sorted(os.listdir(path)):
        if i.endswith(".png"):
            iconname = i[:-4]
            filepath = os.path.join(path, i)

            icons.load(iconname, filepath, 'IMAGE')

    return icons

def unregister_icons(icons):
    previews.remove(icons)

def get_core():
    return [classesdict["CORE"]]

def get_menus():
    classlists = []
    keylists = []

    classlists.append(classesdict["PIE_MENU"])
    keylists.append(keysdict["PIE_MENU"])

    classlists.append(classesdict["PANEL"])

    return classlists, keylists

def get_tools():
    classlists = []
    keylists = []

    classlists.append(classesdict["INSERTREMOVE"])
    classlists.append(classesdict["ADJUST"])
    classlists.append(classesdict["REAPPLY"])
    classlists.append(classesdict["PROJECT"])
    classlists.append(classesdict["SLICE"])
    classlists.append(classesdict["GETBACKUP"])
    classlists.append(classesdict["PANELCUT"])
    classlists.append(classesdict["UNWRAP"])
    classlists.append(classesdict["MATCH"])
    classlists.append(classesdict["SELECT"])

    classlists.append(classesdict["CREATE"])

    classlists.append(classesdict["BAKE"])

    classlists.append(classesdict["UTILS"])

    classlists.append(classesdict["TEXTURECOORDINATES"])

    classlists.append(classesdict["TRIMSHEET"])
    classlists.append(classesdict["TRIMUNWRAP"])
    classlists.append(classesdict["TRIMADJUST"])
    classlists.append(classesdict["TRIMCUT"])

    classlists.append(classesdict["ATLAS"])

    classlists.append(classesdict["ALIGN"])
    classlists.append(classesdict["STITCH"])
    classlists.append(classesdict["MIRROR"])
    classlists.append(classesdict["JOIN"])

    classlists.append(classesdict["OVERRIDE"])

    classlists.append(classesdict["DEBUG"])

    keylists.append(keysdict["QUICK_INSERT"])
    keylists.append(keysdict["SELECT"])

    return classlists, keylists

def get_gizmos():
    classlists = []

    classlists.append(classesdict["GIZMO"])

    return classlists

def get_assetspath_dict(debug=False):
    
    assetspath = get_prefs().assetspath

    assetsdict = {'VALID': [],

                  'AMBIGUOUS': [],
                  'INVALID': [],
                  'CORRUPT': [],

                  'OBSOLETE': [],
                  'LEGACY': [],
                  'CURRENT': [],
                  'FUTURE': [], 

                  'CLUTTER': [],
                  'DECLUTTERED': [],

                  'COLLIDED': [],
                  'QUARANTINED': [],
                  'SKIPPED': [],

                  'ATLASES': [],
                  'DECALS': [],
                  'TRIMS': []
                  }

    if debug:
        print()
        print("assetspath:", assetspath)

    for libtype in ['Decals', 'Trims']:
        libtypepath = os.path.join(assetspath, libtype)

        if debug:
            print("", libtype, libtypepath)

        contents = sorted([f for f in os.listdir(libtypepath)])

        for cont in contents:
            contpath = os.path.join(libtypepath, cont)

            if os.path.isdir(contpath):

                is_trimsheet = is_library_trimsheet(contpath)

                if is_corrupt := (is_library_corrupted(contpath) or (libtype == 'Trims' and not is_trimsheet)):
                    assetsdict['CORRUPT'].append(contpath)

                if is_obsolete := is_library_obsolete(contpath):
                    assetsdict['OBSOLETE'].append(contpath)

                versions = get_version_files(contpath)

                if debug:
                    print(" folder:", cont)
                    print("  trimsheet:", is_trimsheet)
                    print("  corrupted:", is_corrupt)
                    print("  obsolete:", is_obsolete)
                    print("  versions:", versions)

                if len(versions) == 1:
                    if not is_corrupt:
                        assetsdict['VALID'].append(contpath)

                        version_filename = versions[0]

                        if version_filename == get_version_filename_from_blender():
                            assetsdict['CURRENT'].append(contpath)

                        else:
                            version = get_version_as_float(get_version_from_filename(version_filename))

                            if version > get_version_as_float(get_version_from_blender()):
                                assetsdict['FUTURE'].append(contpath)

                            else:
                                assetsdict['LEGACY'].append(contpath)

                elif len(versions) < 1:
                    assetsdict['INVALID'].append(contpath)

                else:
                    assetsdict['AMBIGUOUS'].append(contpath)

            else:
                if debug:
                    print(" file (clutter):", cont)

                assetsdict['CLUTTER'].append(contpath)

    contents = set(f for f in os.listdir(assetspath))

    mandatory = {'Atlases', 'Clutter', 'Create', 'Decals', 'Export', 'Trims', 'presets.json'}

    leftovers = contents - mandatory

    for f in sorted(leftovers):

        if f in ['Decals_Quarantine', 'Trims_Quarantine']:
            continue

        if any(f.startswith(s) for s in ['Atlases_Collision', 'Decals_Collision', 'Trims_Collision']):
            continue

        if any(f.startswith(s) for s in ['Decals_Skipped', 'Trims_Skipped']):
            continue

        assetsdict['CLUTTER'].append(os.path.join(assetspath, f))

    if os.path.exists(clutterpath := os.path.join(assetspath, 'Clutter')):
        contents = sorted(os.listdir(clutterpath))

        for f in contents:
            assetsdict['DECLUTTERED'].append(os.path.join(clutterpath, f))

    assets_root_contents = sorted([f for f in os.listdir(assetspath) if os.path.isdir(os.path.join(assetspath, f))])

    for libtype in ['Atlases', 'Decals', 'Trims']:
        collisiontype = f"{libtype}_Collision"

        for folder in assets_root_contents:
            if folder.startswith(collisiontype):
                folderpath = os.path.join(assetspath, folder)

                libs = [lib for lib in os.listdir(folderpath) if os.path.isdir(os.path.join(folderpath, lib))]

                for lib in libs:
                    assetsdict['COLLIDED'].append(os.path.join(folderpath, lib))

    for libtype in ['Decals', 'Trims']:
        quarantinetype = f"{libtype}_Quarantine"

        for folder in assets_root_contents:
            if folder.startswith(quarantinetype):
                folderpath = os.path.join(assetspath, folder)

                libs = [lib for lib in os.listdir(folderpath) if os.path.isdir(os.path.join(folderpath, lib))]

                for lib in libs:
                    assetsdict['QUARANTINED'].append(os.path.join(folderpath, lib))

    for libtype in ['Decals', 'Trims']:
        skiptype = f"{libtype}_Skipped"

        for folder in assets_root_contents:
            if folder.startswith(skiptype):
                folderpath = os.path.join(assetspath, folder)

                libs = [lib for lib in os.listdir(folderpath) if os.path.isdir(os.path.join(folderpath, lib))]

                for lib in libs:
                    assetsdict['SKIPPED'].append(os.path.join(folderpath, lib))

    for libtype in ['Atlases', 'Decals', 'Trims']:
        libtypepath = os.path.join(assetspath, libtype)

        folders = [f for f in os.listdir(libtypepath) if os.path.isdir(os.path.join(libtypepath, f))]

        for f in folders:
            path = os.path.join(libtypepath, f)

            if libtype == 'Atlases':
                if is_atlas(path):
                    versions = get_version_files(path)

                    if len(versions) == 1 and versions[0] == get_version_filename_from_blender(atlas=True):
                        assetsdict[libtype.upper()].append(str(path))

            else:
                if path in assetsdict['CURRENT']:
                    assetsdict[libtype.upper()].append(path)

    if debug:
        printd(assetsdict, name='assets dict')

    return assetsdict

decal_libraries = []

def register_decals(library="ALL", default=None, reloading=False):
    p = get_prefs()

    decallibpaths = get_assets_dict()['DECALS']

    p.decallibsIDX = 0

    saveddecallibs = sorted([lib.name for lib in p.decallibsCOL if not lib.istrimsheet])

    for name in saveddecallibs:
        libpath = os.path.join(p.assetspath, 'Decals', name)

        if libpath not in decallibpaths:
            index = p.decallibsCOL.keys().index(name)  # the index needs to be retrieved every time, because it changes with each removal
            p.decallibsCOL.remove(index)
            print(f"WARNING: Previously registered Decal Library '{name}' can no longer be found! Save your preferences!")

    decallibs = []

    if library == "ALL":

        for path in decallibpaths:
            name = os.path.basename(path)

            decallibs.append(name)

            if name not in p.decallibsCOL:
                lib = p.decallibsCOL.add()
                lib.name = name

                if os.path.exists(os.path.join(path, ".ishidden")):
                    p.decallibsCOL[name].isvisible = False

                if os.path.exists(os.path.join(path, ".ispanelhidden")):
                    p.decallibsCOL[name].ispanelcycle = False

            if os.path.exists(os.path.join(path, ".ispanel")):
                p.decallibsCOL[name].avoid_update = True
                p.decallibsCOL[name].ispanel = True

            if os.path.exists(os.path.join(path, ".islocked")):
                p.decallibsCOL[name].avoid_update = True
                p.decallibsCOL[name].islocked = True

        unlockedlibs = sorted([(lib.name, lib.name, "") for lib in p.decallibsCOL if not lib.istrimsheet and not lib.islocked], reverse=False)

        enum = EnumProperty(name="User Decal Library", items=unlockedlibs, update=set_new_decal_index, default=unlockedlibs[-1][0] if unlockedlibs else None)
        setattr(bpy.types.Scene, "userdecallibs", enum)

        setattr(bpy.types.WindowManager, "newdecalidx", StringProperty(name="User Decal Library Index"))

    else:
        decallibs = [library]

    global decal_libraries

    uuids = bpy.types.WindowManager.decaluuids if reloading else {}

    for libname in decallibs:
        col = previews.new()
        items = populate_preview_collection(col, p.assetspath, libname, uuids, libtype='Decals')

        decal_libraries.append((libname, 'decal', col))

        enum = EnumProperty(items=items, update=insert_or_remove_decal(libname), default=default)
        setattr(bpy.types.WindowManager, "decallib_" + libname, enum)

        if reloading:
            if libname in saveddecallibs:
                print(" • reloaded decal library: %s" % (libname))
            else:
                print(" • loaded new decal library: %s" % (libname))

    setattr(bpy.types.WindowManager, "decaluuids", uuids)

    items = get_panel_decal_items()
    setattr(bpy.types.WindowManager, "paneldecals", EnumProperty(name='Panel Types', items=items, default=items[0][0] if items else None))
    return decal_libraries

def unregister_decals(library="ALL"):
    global decal_libraries

    if library == "ALL":
        decallibs = decal_libraries

    else:
        decallibs = [(library, 'decal', [col for libname, libtype, col in decal_libraries if libname == library][0])]

    remove = []

    for libname, libtype, col in decallibs:
        delattr(bpy.types.WindowManager, "decallib_" + libname)

        remove.append((libname, libtype, col))

        previews.remove(col)

        for uuid, decallist in list(bpy.types.WindowManager.decaluuids.items()):
            for decal, lib, libtype in decallist:
                if lib == libname:
                    decallist.remove((decal, lib, libtype))

            if not decallist:
                del bpy.types.WindowManager.decaluuids[uuid]

        if get_prefs().registration_debug:
            print(" • unloaded decal library: %s" % (libname))

    for r in remove:
        decal_libraries.remove(r)

def get_panel_decal_items():
    panellibs = [lib.name for lib in get_prefs().decallibsCOL if lib.ispanel]

    tuplelist = []

    if panellibs:
        assetspath = get_prefs().assetspath

        for lib in panellibs:
            libpath = os.path.join(assetspath, 'Decals', lib)
            panellist = getattr(bpy.types.WindowManager, "decallib_" + lib).keywords['items']

            for name, _, _, _, _ in panellist:

                uuid = None

                with open(os.path.join(libpath, name, "uuid"), "r") as f:
                    uuid = f.read()

                if uuid:
                    tuplelist.append((uuid, name, lib))

    return sorted(tuplelist, key=lambda x: (x[2], x[1]))

def insert_or_remove_decal(libraryname='', instant=False):
    from . decal import insert_single_decal, remove_single_decal

    def function_template(self, context):
        if get_prefs().decalmode == "NONE":
            return

        else:
            if get_prefs().decalmode == "INSERT":
                if instant:
                    insert_single_decal(context, libraryname='INSTANT', decalname=getattr(bpy.context.window_manager, "instantdecallib"), instant=True, trim=False, force_cursor_align=True, push_undo=True)

                else:
                    insert_single_decal(context, libraryname=libraryname, decalname=getattr(bpy.context.window_manager, "decallib_" + libraryname), instant=False, trim=False, force_cursor_align=False, push_undo=True)

            elif get_prefs().decalmode == "REMOVE":
                if instant:
                    remove_single_decal(context, libraryname="INSTANT", decalname=getattr(bpy.context.window_manager, "instantdecallib"), instant=True, trim=False)

                else:
                    remove_single_decal(context, libraryname=libraryname, decalname=getattr(bpy.context.window_manager, "decallib_" + libraryname), instant=False, trim=False)

    return function_template

def set_new_decal_index(self, context):
    if context.scene.userdecallibs:
        userlibpath = os.path.join(get_prefs().assetspath, 'Decals', context.scene.userdecallibs)

        if os.path.exists(userlibpath):
            context.window_manager.newdecalidx = get_new_directory_index(userlibpath)

def populate_preview_collection(col, assetspath, library, uuids, libtype='Decals', panel_trims=None):
    libpath = os.path.join(assetspath, libtype, library)

    items = []

    folders = sorted([(f, os.path.join(libpath, f)) for f in os.listdir(libpath) if os.path.isdir(os.path.join(libpath, f))], key=lambda x: x[0], reverse=get_prefs().reversedecalsorting)

    for decalname, decalpath in folders:
        files = os.listdir(decalpath)

        if all([f in files for f in ["decal.blend", "decal.png", "uuid"]]):
            iconpath = os.path.join(decalpath, "decal.png")
            preview = col.load(decalname, iconpath, 'IMAGE')

            items.append((decalname, decalname, "%s %s" % (library, decalname), preview.icon_id, preview.icon_id))

            with open(os.path.join(decalpath, "uuid"), "r") as f:
                uuid = f.read().replace("\n", "")

            if uuid not in uuids:
                uuids[uuid] = []

            uuids[uuid].append((decalname, library, libtype))

            if panel_trims is not None:
                if os.path.exists(os.path.join(decalpath, '.ispanel')):
                    panel_trims.append((uuid, decalname, library))

    return items

def reload_decal_libraries(library="ALL", default=None):
    if library == "ALL":
        unregister_decals()
        register_decals(reloading=True)

    else:
        unregister_decals(library=library)
        register_decals(library=library, default=default, reloading=True)
        if default:
            mode = get_prefs().decalmode
            get_prefs().decalmode = "NONE"
            setattr(bpy.context.window_manager, "decallib_" + library, default)
            get_prefs().decalmode = mode

    lib = bpy.context.scene.userdecallibs

    if lib not in [lib[0] for lib in bpy.types.Scene.userdecallibs.keywords['items']]:
        libs = bpy.types.Scene.userdecallibs.keywords['items']
        if libs:
            setattr(bpy.context.scene, "userdecallibs", libs[0][0])

def is_decal_registered(uuid):
    return bpy.context.window_manager.decaluuids.get(uuid)

trim_libraries = []

def register_trims(library="ALL", default=None, reloading=False):
    p = get_prefs()

    trimlibpaths = get_assets_dict(force=reloading)['TRIMS']

    savedlibs = [lib.name for lib in p.decallibsCOL if lib.istrimsheet]

    for lib in savedlibs:
        libpath = os.path.join(p.assetspath, 'Trims', lib)

        if libpath not in trimlibpaths:
            index = p.decallibsCOL.keys().index(lib)  # the index needs to be retrieved every time, because it changes with each removal
            p.decallibsCOL.remove(index)
            print(f"WARNING: Previously registered Trimsheet Library '{lib}' can no longer be found! Save your preferences!")

    trimlibs = []

    if library == "ALL":
        for path in trimlibpaths:
            name = os.path.basename(path)

            trimlibs.append(name)

            if name not in p.decallibsCOL:
                lib = p.decallibsCOL.add()
                lib.name = name

                if os.path.exists(os.path.join(path, ".ishidden")):
                    p.decallibsCOL[name].isvisible = False

                if os.path.exists(os.path.join(path, ".ispanelhidden")):
                    p.decallibsCOL[name].ispanelcycle = False

            p.decallibsCOL[name].istrimsheet = True

            if os.path.exists(os.path.join(path, ".islocked")):
                p.decallibsCOL[name].avoid_update = True
                p.decallibsCOL[name].islocked = True

            datapath = os.path.join(path, "data.json")
            data = load_json(datapath)

            data_name = data.get('name')

            if data_name and data_name != name:
                data['name'] = name
                save_json(data, datapath)
                print(f"WARNING: Trimsheet '{name}' name not in sync, was originally stored as '{data_name}' instead, and has been updated to now!")

        sheetlibs = sorted([(lib.name, lib.name, "") for lib in p.decallibsCOL if lib.istrimsheet], reverse=False)
        enum = EnumProperty(name="Active Trim Sheet", items=sheetlibs)
        setattr(bpy.types.Scene, "trimsheetlibs", enum)

    else:
        trimlibs = [library]

    global trim_libraries

    trim_panel_items = []

    sheets = getattr(bpy.types.WindowManager, "trimsheets") if reloading else {}

    for libname in trimlibs:
        col = previews.new()
        items = populate_preview_collection(col, p.assetspath, libname, bpy.types.WindowManager.decaluuids, libtype='Trims', panel_trims=trim_panel_items)

        trim_libraries.append((libname, 'trim sheet', col))

        enum = EnumProperty(items=items, update=insert_or_unwrap_trim(libname), default=default)
        setattr(bpy.types.WindowManager, "trimlib_" + libname, enum)

        sheets[libname] = load_json(os.path.join(p.assetspath, 'Trims', libname, 'data.json'))

        if reloading:
            if libname in savedlibs:
                print(" • reloaded trim sheet library: %s" % (libname))
            else:
                print(" • loaded new trim sheet library: %s" % (libname))

    setattr(bpy.types.WindowManager, "trimsheets", sheets)

    existing_panel_decals = getattr(bpy.types.WindowManager, "paneldecals").keywords['items']
    items = existing_panel_decals + trim_panel_items
    setattr(bpy.types.WindowManager, "paneldecals", EnumProperty(name='Panel Types', items=items, default=items[0][0] if items else None))
    update_instanttrimsheetcount()

    return trim_libraries

def unregister_trims(library="ALL"):
    global trim_libraries

    if library == "ALL":
        trimlibs = trim_libraries

    else:
        trimlibs = [(library, 'trim sheet', [col for libname, libtype, col in trim_libraries if libname == library][0])]

    remove = []

    for libname, libtype, col in trimlibs:
        delattr(bpy.types.WindowManager, "trimlib_" + libname)

        remove.append((libname, libtype, col))

        previews.remove(col)

        del bpy.types.WindowManager.trimsheets[libname]

        for uuid, decallist in list(bpy.types.WindowManager.decaluuids.items()):
            for decal, lib, libtype in decallist:
                if lib == libname:
                    decallist.remove((decal, lib, libtype))

            if not decallist:
                del bpy.types.WindowManager.decaluuids[uuid]

        if get_prefs().registration_debug:
            print(" • unloaded trim sheet library: %s" % (libname))

    for r in remove:
        trim_libraries.remove(r)

def insert_or_unwrap_trim(libraryname=''):
    from . decal import insert_single_decal, remove_single_decal

    def function_template(self, context):
        if get_prefs().decalmode == "NONE":
            return

        elif bpy.context.mode == 'OBJECT':
            if get_prefs().decalmode == "INSERT":
                insert_single_decal(context, libraryname=libraryname, decalname=getattr(bpy.context.window_manager, "trimlib_" + libraryname), instant=False, trim=True, force_cursor_align=False, push_undo=True)

            elif get_prefs().decalmode == "REMOVE":
                remove_single_decal(context, libraryname=libraryname, decalname=getattr(bpy.context.window_manager, "trimlib_" + libraryname), instant=False, trim=True)

        elif bpy.context.mode == 'EDIT_MESH':
            bpy.ops.machin3.trim_unwrap('INVOKE_DEFAULT', library_name=libraryname, trim_name=getattr(bpy.context.window_manager, "trimlib_" + libraryname))

    return function_template

def reload_trim_libraries(library="ALL", default=None, atlas=True):
    if library == "ALL":
        unregister_trims()
        register_trims(reloading=True)
    else:
        unregister_trims(library=library)
        register_trims(library=library, default=default, reloading=True)
        if default:
            mode = get_prefs().decalmode
            get_prefs().decalmode = "NONE"
            setattr(bpy.context.window_manager, "trimlib_" + library, default)
            get_prefs().decalmode = mode

    if atlas:
        register_atlases(reloading=True)

    lib = bpy.context.scene.trimsheetlibs

    if lib not in [lib[0] for lib in bpy.types.Scene.trimsheetlibs.keywords['items']]:
        libs = bpy.types.Scene.trimsheetlibs.keywords['items']
        if libs:
            setattr(bpy.context.scene, "trimsheetlibs", libs[0][0])

def update_instanttrimsheetcount():
    assetspath = get_prefs().assetspath
    triminstantpath = os.path.join(assetspath, 'Create', 'triminstant')
    count = len([f for f in os.listdir(triminstantpath) if os.path.isdir(os.path.join(triminstantpath, f))])
    setattr(bpy.types.WindowManager, "instanttrimsheetcount", count)

def is_trimsheet_registered(uuid):
    for name, sheetdata in bpy.context.window_manager.trimsheets.items():
        if sheetdata['uuid'] == uuid:
            return sheetdata

def register_atlases(reloading=False):
    p = get_prefs()

    assets_dict = get_assets_dict(force=reloading)
    atlaspaths = assets_dict['ATLASES'] + assets_dict['TRIMS']

    p.atlasesIDX = 0

    savedatlases = [(atlas.name, atlas.istrimsheet) for atlas in p.atlasesCOL]

    for name, is_trimsheet in savedatlases:
        folder = 'Trims' if is_trimsheet else 'Atlases'
        atlaspath = os.path.join(p.assetspath, 'Trims' if is_trimsheet else 'Atlases', name)

        if atlaspath not in atlaspaths:
            index = p.atlasesCOL.keys().index(name)  # the index needs to be retrieved every time, because it changes with each removal
            p.atlasesCOL.remove(index)
            print(f"WARNING: Atlas '{name}' can no longer be found! Save your preferences!")

    for path in atlaspaths:
        name = os.path.basename(path)
        is_trimsheet = path in assets_dict['TRIMS']

        if name not in p.atlasesCOL:
            atlas = p.atlasesCOL.add()
            atlas.name = name

        p.atlasesCOL[name].istrimsheet = is_trimsheet

        if os.path.exists(os.path.join(path, ".islocked")):
            p.atlasesCOL[name].avoid_update = True
            p.atlasesCOL[name].islocked = True

        if not is_trimsheet:
            datapath = os.path.join(path, "data.json")
            data = load_json(datapath)

            data_name = data.get('name')

            if data_name and data_name != name:
                data['name'] = name
                save_json(data, datapath)
                print(f"WARNING: Atlas '{name}' name not in sync, was originally stored as '{data_name}' instead, and has been updated now!")

    atlases = {}

    for atlas in p.atlasesCOL:

        if not atlas.istrimsheet:

            atlases[atlas.name] = load_json(os.path.join(p.assetspath, 'Atlases', atlas.name, 'data.json'))

            if reloading:
                if atlas.name in [name for name, _ in savedatlases]:
                    print(" • reloaded atlas: %s" % (atlas.name))
                else:
                    print(" • loaded new atlas: %s" % (atlas.name))

    setattr(bpy.types.WindowManager, "atlases", atlases)

    update_instantatlascount()

    return [name for name in atlases]

def update_instantatlascount():
    assetspath = get_prefs().assetspath
    atlasinstantpath = os.path.join(assetspath, 'Create', 'atlasinstant')
    count = len([f for f in os.listdir(atlasinstantpath) if os.path.isdir(os.path.join(atlasinstantpath, f))])
    setattr(bpy.types.WindowManager, "instantatlascount", count)

locked = None

def register_lockedlib():
    global locked

    locked = previews.new()

    lockedpath = os.path.join(get_path(), "resources", 'locked.png')
    assert os.path.exists(lockedpath), "%s not found" % lockedpath

    preview = locked.load("LOCKED", lockedpath, 'IMAGE')
    items = [("LOCKED", "LOCKED", "LIBRARY is LOCKED", preview.icon_id, preview.icon_id)]

    enum = EnumProperty(items=items)
    setattr(bpy.types.WindowManager, "lockeddecallib", enum)

def unregister_lockedlib():
    global locked

    delattr(bpy.types.WindowManager, "lockeddecallib")
    previews.remove(locked)

instantdecals = None

def register_instant_decals(default=None, reloading=False):
    global instantdecals

    assetspath = get_prefs().assetspath
    instantpath = os.path.join(assetspath, 'Create', 'decalinstant')

    items = []
    instantdecals = previews.new()

    uuids = {} if not reloading else bpy.types.WindowManager.instantdecaluuids

    folders = sorted([(f, os.path.join(instantpath, f)) for f in os.listdir(instantpath) if os.path.isdir(os.path.join(instantpath, f))], key=lambda x: x[0], reverse=False)

    for decalname, decalpath in folders:
        files = os.listdir(decalpath)

        if all([f in files for f in ["decal.blend", "decal.png", "uuid"]]):

            iconpath = os.path.join(decalpath, "decal.png")
            preview = instantdecals.load(decalname, iconpath, 'IMAGE')

            items.append((decalname, decalname, "%s %s" % ("INSTANT", decalname), preview.icon_id, preview.icon_id))

            with open(os.path.join(decalpath, "uuid"), "r") as f:
                uuid = f.read().replace("\n", "")

            if uuid not in uuids:
                uuids[uuid] = []

            uuids[uuid].append(decalname)

    enum = EnumProperty(items=items, update=insert_or_remove_decal(instant=True), default=default)
    setattr(bpy.types.WindowManager, "instantdecallib", enum)

    setattr(bpy.types.WindowManager, "instantdecaluuids", uuids)

def unregister_instant_decals():
    global instantdecals

    delattr(bpy.types.WindowManager, "instantdecallib")
    previews.remove(instantdecals)

    for uuid, decallist in list(bpy.types.WindowManager.instantdecaluuids.items()):
        for decal in decallist:
            decallist.remove(decal)

        if not decallist:
            del bpy.types.WindowManager.instantdecaluuids[uuid]

def reload_instant_decals(default=None):
    unregister_instant_decals()
    register_instant_decals(default=default, reloading=True)
    if default:
        mode = get_prefs().decalmode
        get_prefs().decalmode = "NONE"
        bpy.context.window_manager.instantdecallib = default
        get_prefs().decalmode = mode

infotextures = None

def register_infotextures(default=None):
    global infotextures

    infotextures = previews.new()

    assetspath = get_prefs().assetspath
    infopath = os.path.join(assetspath, 'Create', 'infotextures')

    images = [f for f in os.listdir(infopath) if f.endswith(".png") or f.endswith(".jpg")]

    items = []

    for img in sorted(images):
        imgpath = os.path.join(infopath, img)
        imgname = img

        preview = infotextures.load(imgname, imgpath, 'IMAGE')

        items.append((imgname, imgname, "", preview.icon_id, preview.icon_id))

    enum = EnumProperty(items=items, default=default)
    setattr(bpy.types.WindowManager, "infotextures", enum)

def unregister_infotextures():
    global infotextures

    delattr(bpy.types.WindowManager, "infotextures")
    previews.remove(infotextures)

def reload_infotextures(default=None):
    unregister_infotextures()
    register_infotextures(default=default)

infofonts = None

def register_infofonts(default=None):
    global infofonts

    infofonts = previews.new()

    assetspath = get_prefs().assetspath
    fontspath = os.path.join(assetspath, 'Create', 'infofonts')

    fontfiles = [f for f in os.listdir(fontspath) if f.endswith(".ttf") or f.endswith(".TTF")]

    items = []

    for font in sorted(fontfiles):
        fontpath = os.path.join(fontspath, font)
        fontname = font

        preview = infofonts.load(fontname, fontpath, 'FONT')

        items.append((fontname, fontname, "", preview.icon_id, preview.icon_id))

    enum = EnumProperty(items=items, default=default)
    setattr(bpy.types.WindowManager, "infofonts", enum)

def unregister_infofonts():
    global infofonts

    delattr(bpy.types.WindowManager, "infofonts")
    previews.remove(infofonts)

def reload_infofonts(default=None):
    unregister_infofonts()
    register_infofonts(default=default)

trimtextures = None

def register_trimtextures():
    global trimtextures

    trimtextures = previews.new()

    assetspath = get_prefs().assetspath
    trimpath = os.path.join(assetspath, 'Create', 'trimtextures')

    images = [f for f in os.listdir(trimpath) if f.endswith(".png")]

    items = [("None", "None", "", 0, 0)]

    for img in sorted(images):
        imgpath = os.path.join(trimpath, img)
        imgname = img

        preview = trimtextures.load(imgname, imgpath, 'IMAGE')

        items.append((imgname, imgname, "", preview.icon_id, preview.icon_id))

    def update_trim_map(self, context):
        bpy.ops.machin3.update_trim_map()

    enum = EnumProperty(items=items, name="Trim Sheet Textures", description="Available Trim Sheet Texture Maps", default="None", update=update_trim_map)
    setattr(bpy.types.WindowManager, "trimtextures", enum)

def unregister_trimtextures():
    global trimtextures

    delattr(bpy.types.WindowManager, "trimtextures")
    previews.remove(trimtextures)

def reload_trimtextures():
    unregister_trimtextures()
    register_trimtextures()
