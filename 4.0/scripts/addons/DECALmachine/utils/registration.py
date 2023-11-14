import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.utils import register_class, unregister_class, previews
import os
import re
from . system import get_new_directory_index, load_json, save_json, makedir
from .. registration import keys as keysdict
from .. registration import classes as classesdict



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


def get_templates_path():

    if bpy.app.version < (3, 0, 0):
        return os.path.join(get_path(), "resources", "Templates_2.93.blend")
    else:
        return os.path.join(get_path(), "resources", "Templates_3.0.blend")



def get_version_from_blender():

    if bpy.app.version < (3, 0, 0):
        return '2.1.0'
    else:
        return '2.5.0'


def get_version_filename_from_blender():
    if bpy.app.version < (3, 0, 0):
        return '.is21'
    else:
        return '.is25'


def get_version_from_filename(filename):

    if filename == '.is280':
        return '1.8'

    stripped = filename.replace('.is', '')
    return stripped[:1] + '.' + stripped[1:]


def get_version_files(path):
    versionRegex = re.compile(r'\.is[\d]+')
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and versionRegex.match(f)]


def get_version_as_float(versionstring):
    return float('.'.join([v for v in versionstring.split('.')[:2]]))



def is_library_corrupted(libpath):

    folders = [f for f in sorted(os.listdir(libpath)) if os.path.isdir(os.path.join(libpath, f))]

    for folder in folders:
        decalpath = os.path.join(libpath, folder)
        files = os.listdir(decalpath)

        if not all([f in files for f in ["decal.blend", "decal.png", "uuid"]]):
            return True



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

    classlists.append(classesdict["ADDON"])
    classlists.append(classesdict["DEBUG"])

    keylists.append(keysdict["QUICK_INSERT"])
    keylists.append(keysdict["SELECT"])

    return classlists, keylists


def get_gizmos():
    classlists = []

    classlists.append(classesdict["GIZMO"])

    return classlists



def verify_assetspath():

    assetspath = get_prefs().assetspath

    makedir(os.path.join(assetspath, 'Atlases'))

    makedir(os.path.join(assetspath, 'Decals'))

    makedir(os.path.join(assetspath, 'Create', 'atlasinstant'))
    makedir(os.path.join(assetspath, 'Create', 'decalinstant'))
    makedir(os.path.join(assetspath, 'Create', 'infofonts'))
    makedir(os.path.join(assetspath, 'Create', 'infotextures'))
    makedir(os.path.join(assetspath, 'Create', 'triminstant'))
    makedir(os.path.join(assetspath, 'Create', 'trimtextures'))

    makedir(os.path.join(assetspath, 'Export', 'atlas'))
    makedir(os.path.join(assetspath, 'Export', 'bakes'))

    makedir(os.path.join(assetspath, 'Trims'))

    return assetspath



decal_libraries = []


def register_decals(library="ALL", default=None, reloading=False):
    p = get_prefs()
    assetspath = p.assetspath

    version = get_version_from_blender()[:-2]
    version_filename = get_version_filename_from_blender()


    p.decallibsIDX = 0

    savedlibs = sorted([lib.name for lib in p.decallibsCOL if not lib.istrimsheet])

    for lib in savedlibs:
        libpath = os.path.join(assetspath, 'Decals', lib)

        if os.path.exists(libpath):

            if is_library_corrupted(libpath):
                index = p.decallibsCOL.keys().index(lib)
                p.decallibsCOL.remove(index)
                continue

            version_files = get_version_files(os.path.join(assetspath, 'Decals', lib))

            if version_files:
                if len(version_files) > 1:
                    index = p.decallibsCOL.keys().index(lib)
                    p.decallibsCOL.remove(index)

                elif len(version_files) == 1 and not os.path.exists(os.path.join(libpath, version_filename)):
                        index = p.decallibsCOL.keys().index(lib)
                        p.decallibsCOL.remove(index)

            else:
                index = p.decallibsCOL.keys().index(lib)
                p.decallibsCOL.remove(index)

        else:
            index = p.decallibsCOL.keys().index(lib)
            p.decallibsCOL.remove(index)
            print(f"WARNING: Saved Decal Library '{lib}' can no longer be found! Save your preferences!")


    decallibs = []



    if library == "ALL":

        p.libs_corrupted = False
        p.libs_incompatible = False
        p.libs_ambiguous = False
        p.libs_invalid = False

        for f in sorted(os.listdir(os.path.join(assetspath, 'Decals'))):
            libpath = os.path.join(assetspath, 'Decals', f)

            if os.path.isdir(libpath):

                if is_library_corrupted(libpath):
                    print(f"WARNING: Decal Library '{f}' is corrupted, it contains non-Decal folders, ignoring!")
                    p.libs_corrupted = True
                    continue

                version_files = get_version_files(libpath)

                if version_files:
                    if len(version_files) == 1:
                        if os.path.exists(os.path.join(libpath, version_filename)):

                            decallibs.append(f)

                            if f not in p.decallibsCOL:
                                item = p.decallibsCOL.add()
                                item.name = f

                                if os.path.exists(os.path.join(libpath, ".ishidden")):
                                    p.decallibsCOL[f].isvisible = False

                                if os.path.exists(os.path.join(libpath, ".ispanelhidden")):
                                    p.decallibsCOL[f].ispanelcycle = False

                            if os.path.exists(os.path.join(libpath, ".ispanel")):
                                p.decallibsCOL[f].avoid_update = True
                                p.decallibsCOL[f].ispanel = True

                            if os.path.exists(os.path.join(libpath, ".islocked")):
                                p.decallibsCOL[f].avoid_update = True
                                p.decallibsCOL[f].islocked = True

                        else:
                            libversion = get_version_from_filename(version_files[0])
                            print(f"WARNING: Decal Library '{f}' is version {libversion}, but needs to be {version}!")
                            p.libs_incompatible = True

                    else:
                        print(f"WARNING: Decal Library '{f}' has ambiguous version indicators, ignoring!")
                        p.libs_ambiguous = True

                else:
                    print(f"WARNING: Folder '{f}' is not a valid Decal Library due to missing version indicator, ignoring!")
                    p.libs_invalid = True


        p.decallibsIDX = 0

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
        items = populate_preview_collection(col, assetspath, libname, uuids, libtype='Decals')

        decal_libraries.append((libname, 'decal', col))

        enum = EnumProperty(items=items, update=insert_or_remove_decal(libname), default=default)
        setattr(bpy.types.WindowManager, "decallib_" + libname, enum)

        if reloading:
            if libname in savedlibs:
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
    assetspath = get_prefs().assetspath
    library = context.scene.userdecallibs
    decalpath = os.path.join(assetspath, 'Decals', library)

    context.window_manager.newdecalidx = get_new_directory_index(decalpath)


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




trim_libraries = []


def register_trims(library="ALL", default=None, reloading=False):
    p = get_prefs()
    assetspath = p.assetspath

    version = get_version_from_blender()[:-2]
    version_filename = get_version_filename_from_blender()

    savedlibs = [lib.name for lib in p.decallibsCOL if lib.istrimsheet]

    for lib in savedlibs:
        libpath = os.path.join(assetspath, 'Trims', lib)

        if os.path.exists(libpath) and os.path.exists(os.path.join(libpath, '.istrimsheet')) and os.path.exists(os.path.join(libpath, 'data.json')):

            if is_library_corrupted(libpath):
                index = p.decallibsCOL.keys().index(lib)
                p.decallibsCOL.remove(index)
                continue

            version_files = get_version_files(libpath)

            if version_files:

                if len(version_files) > 1:
                    index = p.decallibsCOL.keys().index(lib)
                    p.decallibsCOL.remove(index)

                elif len(version_files) == 1 and not os.path.exists(os.path.join(libpath, version_filename)):
                    index = p.decallibsCOL.keys().index(lib)
                    p.decallibsCOL.remove(index)

            else:
                index = p.decallibsCOL.keys().index(lib)
                p.decallibsCOL.remove(index)


        else:
            index = p.decallibsCOL.keys().index(lib)
            p.decallibsCOL.remove(index)
            print(f"WARNING: Trimsheet Library '{lib}' can no longer be found! Save your preferences!")


    trimlibs = []

    if library == "ALL":

        p.trim_libs_corrupted = False
        p.trim_libs_incompatible = False
        p.trim_libs_ambiguous = False
        p.trim_libs_invalid = False

        for f in sorted(os.listdir(os.path.join(assetspath, 'Trims'))):
            libpath = os.path.join(assetspath, 'Trims', f)

            if os.path.isdir(libpath):

                if is_library_corrupted(libpath):
                    print(f"WARNING: Trimsheet Library '{f}' is corrupted, it contains non-Decal folders, ignoring!")
                    p.trim_libs_corrupted = True
                    continue

                version_files = get_version_files(os.path.join(assetspath, 'Trims', f))

                if version_files:

                    if len(version_files) == 1:
                        if os.path.exists(os.path.join(libpath, version_filename)) and os.path.exists(os.path.join(libpath, '.istrimsheet')) and os.path.exists(os.path.join(libpath, 'data.json')):
                            trimlibs.append(f)

                            if f not in p.decallibsCOL:
                                item = p.decallibsCOL.add()
                                item.name = f

                                if os.path.exists(os.path.join(libpath, ".ishidden")):
                                    p.decallibsCOL[f].isvisible = False

                                if os.path.exists(os.path.join(libpath, ".ispanelhidden")):
                                    p.decallibsCOL[f].ispanelcycle = False

                            p.decallibsCOL[f].istrimsheet = True

                            if os.path.exists(os.path.join(libpath, ".islocked")):
                                p.decallibsCOL[f].avoid_update = True
                                p.decallibsCOL[f].islocked = True

                            datapath = os.path.join(libpath, "data.json")
                            data = load_json(datapath)

                            name = data.get('name')

                            if name and name != f:
                                data['name'] = f
                                save_json(data, datapath)
                                print(f"WARNING: Trimsheet '{f}' name not in sync, was stored as '{name}' instead, and has been updated now!")
                        else:
                            libversion = get_version_from_filename(version_files[0])
                            print(f"WARNING: Trimsheet Library '{f}' is version {libversion}, but needs to be {version}!")
                            p.trim_libs_incompatible = True

                    else:
                        print(f"WARNING: Trimsheet Library '{f}' has ambiguous version indicators, ignoring!")
                        p.trim_libs_ambiguous = True

                else:
                    print(f"WARNING: Folder '{f}' is not a valid Trimsheet Library due to missing version indicator, ignoring!")
                    p.trim_libs_invalid = True


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
        items = populate_preview_collection(col, assetspath, libname, bpy.types.WindowManager.decaluuids, libtype='Trims', panel_trims=trim_panel_items)

        trim_libraries.append((libname, 'trim sheet', col))

        enum = EnumProperty(items=items, update=insert_or_unwrap_trim(libname), default=default)
        setattr(bpy.types.WindowManager, "trimlib_" + libname, enum)

        sheets[libname] = load_json(os.path.join(assetspath, 'Trims', libname, 'data.json'))

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



def register_atlases(reloading=False):
    p = get_prefs()
    assetspath = p.assetspath

    version = get_version_from_blender()[:-2]
    version_filename = get_version_filename_from_blender()


    p.atlasesIDX = 0

    savedatlases = [(atlas.name, atlas.istrimsheet) for atlas in p.atlasesCOL]

    for atlas, istrimsheet in savedatlases:
        folder = 'Trims' if istrimsheet else 'Atlases'
        atlaspath = os.path.join(assetspath, folder, atlas)

        if os.path.exists(atlaspath) and os.path.exists(os.path.join(atlaspath, '.istrimsheet' if istrimsheet else '.isatlas')) and os.path.exists(os.path.join(atlaspath, 'data.json')):

            if folder == 'Trims' and is_library_corrupted(atlaspath):
                continue

            version_files = get_version_files(atlaspath)

            if version_files:
                if len(version_files) > 1:
                    index = p.atlasesCOL.keys().index(atlas)
                    p.atlasesCOL.remove(index)

                elif len(version_files) == 1 and not os.path.exists(os.path.join(atlaspath, version_filename if istrimsheet else '.is20')):
                        index = p.atlasesCOL.keys().index(atlas)
                        p.atlasesCOL.remove(index)

            else:
                index = p.atlasesCOL.keys().index(atlas)
                p.atlasesCOL.remove(index)


        else:
            index = p.atlasesCOL.keys().index(atlas)
            p.atlasesCOL.remove(index)
            print(f"WARNING: Atlas '{atlas}' can no longer be found! Save your preferences!")



    for folder in ['Atlases', 'Trims']:
        for f in sorted(os.listdir(os.path.join(assetspath, folder))):
            atlaspath = os.path.join(assetspath, folder, f)

            if os.path.isdir(atlaspath):
                if folder == 'Trims' and is_library_corrupted(atlaspath):
                    print(f"WARNING: Atlas '{f}' is corrupted, it contains non-Decal folders, ignoring!")
                    continue

                version_files = get_version_files(os.path.join(atlaspath))

                if version_files:
                    if len(version_files) == 1:
                        if os.path.exists(os.path.join(atlaspath, version_filename if folder == 'Trims' else '.is20')) and os.path.exists(os.path.join(atlaspath, '.istrimsheet' if folder == 'Trims' else '.isatlas')) and os.path.exists(os.path.join(atlaspath, 'data.json')):

                            if f not in p.atlasesCOL:
                                item = p.atlasesCOL.add()
                                item.name = f

                            if folder == 'Trims':
                                p.atlasesCOL[f].istrimsheet = True

                            if os.path.exists(os.path.join(atlaspath, ".islocked")):
                                p.atlasesCOL[f].avoid_update = True
                                p.atlasesCOL[f].islocked = True

                            if folder == 'Atlases':
                                datapath = os.path.join(atlaspath, "data.json")
                                data = load_json(datapath)

                                name = data.get('name')

                                if name and name != f:
                                    data['name'] = f
                                    save_json(data, datapath)
                                    print(f"WARNING: Atlas '{f}' name not in sync, was stored as '{name}' instead, and has been updated now!")
                        else:
                            atlasversion = get_version_from_filename(version_files[0])
                            print(f"WARNING: Atlas '{f}' is version {atlasversion}, but needs to be {version if folder == 'Trims' else '2.0'}!")

                    else:
                        print(f"WARNING: Atlas '{f}' has ambiguous version indicators, ignoring!")

                else:
                    print(f"WARNING: Folder '{f}' is not a valid Atlas due to missing version indicator, ignoring!")


    atlases = {}

    for atlas in p.atlasesCOL:

        if not atlas.istrimsheet:

            atlases[atlas.name] = load_json(os.path.join(assetspath, 'Atlases', atlas.name, 'data.json'))

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



def reload_all_assets():
    print("\nINFO: Reloading All DECALmachine Assets")

    reload_decal_libraries()
    reload_trim_libraries(atlas=False)
    register_atlases(reloading=True)

    reload_instant_decals()
    reload_infotextures()
    reload_infofonts()

    reload_trimtextures()

    update_instanttrimsheetcount()
    update_instantatlascount()
