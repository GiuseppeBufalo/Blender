import os
from distutils.dir_util import copy_tree
from shutil import copyfile, move
from typing import Tuple
from . import registration as r
from . system import makedir, abspath, normpath, splitpath, printd
from . property import get_indexed_suffix_name
from .. items import asset_folders

assets_dict = None 

def verify_assetspath():
    p = r.get_prefs()

    for folders in asset_folders:
        path = os.path.join(p.assetspath, *folders)
        makedir(path, debug=True)

    remove_empty_folders()

    assets_dict = get_assets_dict(force=True)

    return p.assetspath

def reload_all_assets():
    print("\nINFO: Reloading All DECALmachine Assets")

    verify_assetspath()

    r.reload_decal_libraries()
    r.reload_trim_libraries(atlas=False)
    r.register_atlases(reloading=True)

    r.reload_instant_decals()
    r.reload_infotextures()
    r.reload_infofonts()

    r.reload_trimtextures()

    r.update_instanttrimsheetcount()
    r.update_instantatlascount()

def get_assets_dict(force=False):
    global assets_dict

    if force or assets_dict is None:
        assets_dict = r.get_assetspath_dict()

    return assets_dict

def get_ambiguous_libs():
    global assets_dict

    if assets_dict:
        return sorted(set(assets_dict['AMBIGUOUS']) - set(assets_dict['CORRUPT']))

    return []

def get_invalid_libs():
    global assets_dict

    if assets_dict:
        return sorted(set(assets_dict['INVALID']) - set(assets_dict['OBSOLETE']))

    return []

def get_corrupt_libs():
    global assets_dict

    if assets_dict:
        return sorted(set(assets_dict['CORRUPT']) - set(assets_dict['OBSOLETE']) - set(assets_dict['INVALID']))
    return []

def move_assets(old_path, new_path, debug=False):
    debug = True
    debug = False

    p = r.get_prefs()

    if normpath(new_path) == normpath(old_path):
        if debug:
            print(" path hasn't actually changed, doing nothing...")

    else:
        if debug:
            print(" path has changed, moving assets...")

        versioned_asset_folders = [folders for folders in asset_folders if folders[0] in ['Atlases', 'Decals', 'Trims']]
        unversioned_asset_folders = [folders for folders in asset_folders if folders[0] in ['Create', 'Export']]

        for folders in unversioned_asset_folders:
            src_path = os.path.join(normpath(old_path), *folders)
            dst_path = os.path.join(normpath(new_path), *folders)

            if debug:
                print()
                print(" ", ' • '.join(folders))

                if os.path.exists(src_path):
                    print("   copying:", src_path, "to", dst_path)
                else:
                    print("   expected source path:", src_path, "does not exist")

            if os.path.exists(src_path):
                copy_tree(src_path, dst_path)

        for folders in versioned_asset_folders:
            src_path = os.path.join(normpath(old_path), *folders)
            dst_path = os.path.join(normpath(new_path), *folders)

            if debug:
                print()
                print(" ", ' • '.join(folders))

            if os.path.exists(src_path):
                libs = os.listdir(src_path)

                for lib in libs:
                    src = os.path.join(src_path, lib)
                    dst = os.path.join(dst_path, lib)

                    lib_type = 'atlas' if folders[0] == 'Atlases' else 'library'

                    if debug:
                        print()
                        print(f"   {lib_type}:", lib)

                    if os.path.exists(dst):
                        collision_path = get_assets_collision_path(folders[0], lib)

                        if debug:
                            print(f"    target destination for {lib_type} {lib} already exists")
                            print("     moving", dst, "out of the way to", collision_path)

                        move(dst, collision_path)

                    if debug:
                        print("    copying:", src, "to", dst)

                    copy_tree(src, dst)

        presetspath = os.path.join(old_path, 'presets.json')

        if os.path.exists(presetspath):
            copyfile(presetspath, os.path.join(new_path, 'presets.json'))

def get_assets_collision_path(assets_type, lib):
    p = r.get_prefs()
    collision_path = os.path.join(normpath(p.assetspath), f"{assets_type}_Collision", lib)
    index = 0

    while os.path.exists(collision_path):
        index += 1
        collision_path = os.path.join(normpath(p.assetspath), f"{assets_type}_Collision_{str(index).zfill(3)}", lib)

    return collision_path

def get_skipped_update_path(assets_type, libname, decalname):
    p = r.get_prefs()
    skipped_path = os.path.join(normpath(p.assetspath), f"{assets_type}_Skipped", libname, decalname)
    index = 0

    while os.path.exists(skipped_path):
        index += 1
        skipped_path = os.path.join(normpath(p.assetspath), f"{assets_type}_Skipped_{str(index).zfill(3)}", libname, decalname)

    return skipped_path

def declutter_assetspath(force=True, debug=False):
    p = r.get_prefs()

    clutter = get_assets_dict(force=force)['CLUTTER']

    clutter_paths = []

    if clutter:
        clutterpath = makedir(os.path.join(p.assetspath, 'Clutter'))

        print(f"\nINFO: Decluttering assetspath! The following files/folders are being moved into {clutterpath}")

        for src in clutter:

            if os.path.join(p.assetspath, 'Decals') in src:
                if not os.path.exists(os.path.join(clutterpath, 'Decals')):
                    makedir(os.path.join(clutterpath, 'Decals'))

                dst = os.path.join(clutterpath, 'Decals', os.path.basename(src))

            elif os.path.join(p.assetspath, 'Trims') in src:
                if not os.path.exists(os.path.join(clutterpath, 'Trims')):
                    makedir(os.path.join(clutterpath, 'Trims'))

                dst = os.path.join(clutterpath, 'Trims', os.path.basename(src))

            else:
                dst = os.path.join(clutterpath, os.path.basename(src))

            if os.path.exists(dst):
                dirname = os.path.dirname(dst)
                basename = os.path.basename(dst)

                dst_name = get_indexed_suffix_name(os.listdir(dirname), basename)
                dst = os.path.join(dirname, dst_name)

            move(src, dst)

            clutter_paths.append((src, dst))

    return clutter_paths

def remove_empty_folders():
    p = r.get_prefs()
    assetspath = p.assetspath

    folders = [f for f in os.listdir(assetspath) if os.path.isdir(os.path.join(assetspath, f))]

    removal_check = ['Clutter',
                     'Atlases_Collision', 'Decals_Collision', 'Trims_Collision',
                     'Decals_Quarantine', 'Trims_Quarantine',
                     'Decals_Skipped', 'Trims_Skipped']

    for f in folders:
        if any(f.startswith(s) for s in removal_check):
            if not os.listdir(path := os.path.join(assetspath, f)):
                print("INFO: Removing empty folder:", path)
                os.rmdir(path)
