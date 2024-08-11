import bpy
import os
from . object import is_instance_collection
from . registration import get_prefs
from . system import printd, save_json, load_json
from . ui import get_scale
from .. items import asset_browser_bookmark_props

def get_registered_library_references(context):
    base_libs = ['LOCAL']

    if bpy.app.version >= (3, 5, 0):
        base_libs.insert(0, 'ALL')
        base_libs.append('ESSENTIALS')

    librefs = base_libs + [lib.name for lib in context.preferences.filepaths.asset_libraries]
    return librefs

def get_asset_library_reference(params):
    if bpy.app.version >= (4, 0, 0):
        return params.asset_library_reference
    else:
        return params.asset_library_ref

def set_asset_library_reference(params, name):
    if name in get_registered_library_references(bpy.context):
        if bpy.app.version >= (4, 0, 0):
            params.asset_library_reference = name
        else:
            params.asset_library_ref = name
        return True
    return False

def get_asset_import_method(params):
    if bpy.app.version >= (4, 0, 0):
        return params.import_method
    else:
        return params.import_type

def set_asset_import_method(params, name):
    if bpy.app.version >= (4, 0, 0):
        params.import_method = name
    else:
        params.import_type = name

def get_asset_ids(context):
    if bpy.app.version >= (4, 0, 0):
        active = context.asset

    else:
        active = context.active_file

    if active:
        return active, active.id_type, active.local_id

    return None, None, None

def get_display_size_from_area(context):
    scale = get_scale(context)

    gap = 5 if scale < 2 else 10
    label = 18

    for region in context.area.regions:
        if region.type == 'WINDOW':

            if region.width > region.height:
                return int(((region.height - (gap * 2)) / scale) - label)

            else:
                return int((region.width - (gap * 2)) / scale)

    return 64

def get_catalogs_from_asset_libraries(context, debug=False):
    asset_libraries = context.preferences.filepaths.asset_libraries
    all_catalogs = []

    for lib in asset_libraries:
        libname = lib.name
        libpath = lib.path

        cat_path = os.path.join(libpath, 'blender_assets.cats.txt')

        if os.path.exists(cat_path):
            if debug:
                print(libname, cat_path)

            with open(cat_path) as f:
                lines = f.readlines()

            for line in lines:
                if line != '\n' and not any([line.startswith(skip) for skip in ['#', 'VERSION']]) and len(line.split(':')) == 3:
                    all_catalogs.append(line[:-1].split(':') + [libname, libpath])

    catalogs = {}

    for uuid, catalog, simple_name, libname, libpath in all_catalogs:
        if uuid not in catalogs:
            catalogs[uuid] = {'catalog': catalog,
                              'simple_name': simple_name,
                              'libname': libname,
                              'libpath': libpath}

    if debug:
        printd(catalogs)

    return catalogs

def update_asset_catalogs(self, context):
    self.catalogs = get_catalogs_from_asset_libraries(context, debug=False)

    catalog_names = []
    items = [('NONE', 'None', '')]

    for uuid, catalog_data in self.catalogs.items():
        catalog = catalog_data['catalog']

        if catalog not in catalog_names:
            catalog_names.append(catalog)
            items.append((catalog, catalog, ''))

    default = get_prefs().preferred_default_catalog if get_prefs().preferred_default_catalog in catalog_names else 'NONE'
    bpy.types.WindowManager.M3_asset_catalogs = bpy.props.EnumProperty(name="Asset Categories", items=items, default=default)

def get_most_used_local_catalog_id():
    id_types = [bpy.data.collections,
                bpy.data.materials, 
                bpy.data.node_groups, 
                bpy.data.objects, 
                bpy.data.worlds]

    catalog_ids = {}

    for id_type in id_types:
        for id in id_type:
            if id.asset_data:
                if (catalog_id := id.asset_data.catalog_id) in catalog_ids:
                    catalog_ids[catalog_id] += 1
                else:
                    catalog_ids[catalog_id] = 1

    if catalog_ids:
        return max(catalog_ids, key=lambda x: catalog_ids[x])

def get_asset_details_from_space(context, space, asset_type='OBJECT', debug=False):

    lib_reference = get_asset_library_reference(space.params)
    catalog_id = space.params.catalog_id
    libname = '' if lib_reference == 'ALL' else lib_reference
    libpath = space.params.directory.decode('utf-8')
    filename = space.params.filename
    import_method = get_asset_import_method(space.params)

    if debug:
        print()
        print("get_asset_details_from_space()")
        print(" asset_library_reference:", lib_reference)
        print(" catalog_id:", catalog_id)
        print(" libname:", libname)
        print(" libpath:", libpath)
        print(" filename:", filename)
        print(" import_method:", import_method)
        print()

    if not filename:
        if debug:
            print(" WARNING: no asset selected!")

        return None, None, '', None

    elif asset_type and f"{asset_type.title()}/" not in filename:
        if debug:
            print(f" WARNING: unsupported asset type selected, expected '{asset_type}'")

        return None, None, '', None

    elif libname == 'ESSENTIALS':
        return None, None, '', None

    elif asset_type and libname == 'LOCAL':
        if f"{asset_type.title()}/" in filename:
            return libname, libpath, filename, import_method

    elif asset_type and '.blend' not in filename:
        if debug:
            print(" WARNING: LOCAL library, but ALL or library is chosen (instead of current file)!")

        if f"{asset_type.title()}/" in filename:
            return 'LOCAL', '', filename, import_method

    elif not libname and not libpath:
        if debug:
            print(" WARNING: EXTERNAL library, but library ref is ALL and directory is not set!")

        catalogs = get_catalogs_from_asset_libraries(context, debug=False)

        for uuid, catdata in catalogs.items():
            if catalog_id == uuid:
                catalog = catdata['catalog']
                libname = catdata['libname']
                libpath = catdata['libpath']

                if debug:
                    print(f" INFO: found catalog {catalog}'s libname and libpath via asset catalogs:", libname, "at", libpath)

                break

    if debug:
        print()

    if libpath:
        return libname, libpath, filename, import_method

    else:
        return None, None, '', None

def get_libref_and_catalog(context, bookmark=None):
    if context.area.type == 'FILE_BROWSER' and context.area.ui_type == 'ASSETS':
        space = context.space_data

        if bookmark:
            libref = bookmark['libref']
            catalog_id = bookmark['catalog_id']

        else:
            libref = get_asset_library_reference(space.params)
            catalog_id = space.params.catalog_id

        catalogs = get_catalogs_from_asset_libraries(context, debug=False)
        catalog = catalogs.get(catalog_id, None)

        if catalog:

            if libref == catalog['libname'] or libref in ['ALL', 'LOCAL']:
                return libref, catalog_id, catalog

        return libref, None, None
    return None, None, None

def validate_libref_and_catalog(context, libref, catalog_id):
    base_libs = ['ALL', 'ESSENTIALS']

    asset_libraries = base_libs + [lib.name for lib in context.preferences.filepaths.asset_libraries]

    if libref in asset_libraries:
        catalogs = get_catalogs_from_asset_libraries(context)

        return catalog_id in catalogs

    return False

def is_local_assembly_asset(obj):
    if col := is_instance_collection(obj):
        if (local_assets := [obj for obj in bpy.data.objects if not obj.library and obj.asset_data and is_instance_collection(obj) and obj.instance_collection == col]):
            return local_assets[0]
    return False

bookmarks = None

def validate_assetbrowser_bookmarks(debug=False):
    bookmarks_path = os.path.join(bpy.utils.user_resource('CONFIG'), 'assetbrowser_bookmarks.json')
    bookmark_indices = [str(i + 1) for i in range(10)]
    bookmark_props = asset_browser_bookmark_props

    if os.path.exists(bookmarks_path):
        bookmarks = load_json(bookmarks_path)

        if bookmarks:

            if all([idx in bookmarks and all(prop in bookmarks[idx] for prop in bookmark_props) for idx in bookmark_indices]):
                context = bpy.context
                catalogs = get_catalogs_from_asset_libraries(context)

                new_bookmarks = {}

                for idx, bookmark in bookmarks.items():
                    libref = bookmark['libref']
                    catalog_id = bookmark['catalog_id']
                    display_size = bookmark['display_size']
                    display_type = bookmark['display_type']

                    valid = validate_libref_and_catalog(context, libref, catalog_id)

                    if bpy.app.version >= (4, 0, 0):
                        if isinstance(display_size, str):
                            display_size = 128
                    else:
                        if isinstance(display_size, int):
                            display_size = 'NORMAL'

                    if not valid:
                        if catalog_id in catalogs:

                            catalog = catalogs[catalog_id]

                            libref = catalog['libname']
                            valid = True

                    new_bookmarks[idx] = {'libref': libref,
                                          'catalog_id': catalog_id,
                                          'display_size': display_size,
                                          'display_type': display_type,
                                          'valid': valid}

                if new_bookmarks != bookmarks:
                    set_assetbrowser_bookmarks(new_bookmarks)

                return True

        print("WARNING: Corruption in assetbrowser_bookmarks.json detected")

    else:
        print("WARNING: No presets .json found")

    print("INFO: Initializing Assetbrowser Bookmarks")
    bookmarks = {}

    for idx in bookmark_indices:
        bookmarks[idx] = {key: None for key in bookmark_props}

    save_json(bookmarks, bookmarks_path)

    if debug:
        printd(bookmarks, 'All Presets')

    return bookmarks

def get_assetbrowser_bookmarks(force=False):
    global bookmarks

    if bookmarks and not force:
        return bookmarks

    bookmarks_path = os.path.join(bpy.utils.user_resource('CONFIG'), 'assetbrowser_bookmarks.json')

    if os.path.exists(bookmarks_path):
        bookmarks = load_json(bookmarks_path)

    else:
        bookmarks = validate_assetbrowser_bookmarks()

    return bookmarks

def set_assetbrowser_bookmarks(bookmarks):
    bookmarks_path = os.path.join(bpy.utils.user_resource('CONFIG'), 'assetbrowser_bookmarks.json')

    save_json(bookmarks, bookmarks_path)

    get_assetbrowser_bookmarks(force=True)
