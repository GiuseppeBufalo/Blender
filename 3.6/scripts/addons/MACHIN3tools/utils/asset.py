import bpy
import os
from . system import printd
from . registration import get_prefs


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
        if catalog not in catalogs:
            catalogs[catalog] = {'uuid': uuid,
                                 'simple_name': simple_name,
                                 'libname': libname,
                                 'libpath': libpath}

    if debug:
        printd(catalogs)

    return catalogs


def update_asset_catalogs(self, context):
    self.catalogs = get_catalogs_from_asset_libraries(context, debug=False)

    items = [('NONE', 'None', '')]

    for catalog in self.catalogs:
        items.append((catalog, catalog, ""))

    default = get_prefs().preferred_default_catalog if get_prefs().preferred_default_catalog in self.catalogs else 'NONE'
    bpy.types.WindowManager.M3_asset_catalogs = bpy.props.EnumProperty(name="Asset Categories", items=items, default=default)


def get_asset_details_from_space(context, space, debug=False):


    libref = space.params.asset_library_ref
    catalog_id = space.params.catalog_id
    libname = '' if libref == 'ALL' else libref
    libpath = space.params.directory.decode('utf-8')
    filename = space.params.filename
    import_type = space.params.import_type

    if debug:
        print()
        print("asset_library_ref:", libref)
        print("catalog_id:", catalog_id)
        print("libname:", libname)
        print("libpath:", libpath)
        print("filename:", filename)
        print("import_type:", import_type)

    if libname == 'LOCAL':
        if 'Object/' in filename:
            return libname, libpath, filename, import_type

    elif libname == 'ESSENTIALS':
        return None, None, None, None

    elif not libname and not libpath:
        if debug:
            print("WARNING: asset library ref is ALL and directory is not set!")

        catalogs = get_catalogs_from_asset_libraries(context, debug=False)

        for catdata in catalogs.values():
            if catalog_id == catdata['uuid']:
                libname = catdata['libname']
                libpath = catdata['libpath']

                if debug:
                    print("INFO: found libname and libpath via asset catalogs:", libname, "at", libpath)

                break

    if libpath:
        return libname, libpath, filename, import_type

    else:
        return None, None, None, None
