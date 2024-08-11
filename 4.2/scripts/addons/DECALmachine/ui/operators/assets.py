import bpy
import os
from shutil import move
from ... utils.registration import get_path, get_prefs, get_version_files, is_decal_folder_valid, is_library_corrupted, is_library_trimsheet
from ... utils.assets import declutter_assetspath, get_assets_dict, get_indexed_suffix_name, reload_all_assets, get_ambiguous_libs, get_invalid_libs, get_corrupt_libs
from ... utils.library import get_short_library_path, get_version_from_filename
from ... utils.time import get_time_code
from ... utils.system import makedir
from ... utils.ui import popup_message

class ResetDECALmachineAssetsLocation(bpy.types.Operator):
    bl_idname = "machin3.reset_decalmachine_assets_location"
    bl_label = "Reset DECALmachine Assets Location"
    bl_description = "Resets Assets Location to DECALmachine/assets/ in Blender's addons folder"

    def execute(self, context):
        get_prefs().avoid_update = True
        get_prefs().assetspath = get_prefs().defaultpath
        get_prefs().oldpath = get_prefs().defaultpath
        reload_all_assets()
        return {'FINISHED'}

class QuarantineLibrary(bpy.types.Operator):
    bl_idname = "machin3.quarantine_asset_lib"
    bl_label = "MACHIN3: Quarantine Asset Library"
    bl_description = "Quarantine Obsolete, Invalid and Corrupted Asset Libraries"
    bl_options = {'INTERNAL'}

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

    def execute(self, context):
        quanrantine_info = []

        decluttered = declutter_assetspath()

        if decluttered:
            for old_path, new_path in decluttered:
                shortpath = get_short_library_path(old_path)
                is_dir = os.path.isdir(new_path)

                quanrantine_info.append(f"🗑️ Decluttered {shortpath}{'/' if is_dir else ''}. This {'Folder' if is_dir else 'File'} should not be there!")

            quanrantine_info.append('')

        assetspath = get_prefs().assetspath
        decalspath = os.path.join(assetspath, 'Decals')
        trimspath = os.path.join(assetspath, 'Trims')

        assets_dict = get_assets_dict(force=bool(decluttered))

        obsolete = assets_dict['OBSOLETE']
        invalid = get_invalid_libs()
        corrupt = get_corrupt_libs()

        for path in obsolete + invalid + corrupt:
            shortpath = get_short_library_path(path)
            asset_type = 'DECALS' if decalspath in path else 'TRIMS' if trimspath in path else None

            if asset_type:
                quarantine_type = 'OBSOLETE' if path in obsolete else'INVALID' if path in invalid else 'CORRUPT'
                quarantine_path = makedir(os.path.join(assetspath, f"{asset_type.title()}_Quarantine"))

                dst = os.path.join(quarantine_path, os.path.basename(path))

                if os.path.exists(dst):
                    new_name = get_indexed_suffix_name(os.listdir(quarantine_path), os.path.basename(path))
                    dst = os.path.join(quarantine_path, new_name)

                log = []

                if quarantine_type == 'OBSOLETE':
                    print(f"INFO: Library {get_short_library_path(path)} is obsolete, moving into Quaranting at {get_short_library_path(dst)}")

                    log.append("Library is obsolete, it predates DECALmachine 1.8 for Blender 2.80 and can't be user-updated anymore.\n")
                    log.append("If you need to update it, you can do so using DECALmachine 1.8 - 2.0 in Blender 2.80 - 2.83 accordingly.\n")
                    log.append("\nOtherwise contact decal@machin3.io, if you require assistance.\n")

                    quanrantine_info.append(f"☢  Quarantined {shortpath}. Library is obsolete. It predates DECALmachine 1.8/Blender 2.80 and can't be user-updated anymore!")

                elif quarantine_type == 'INVALID':
                    print(f"INFO: Library {get_short_library_path(path)} is invalid, moving into Quarantine at {get_short_library_path(dst)}")

                    log.append("This folder is not a valid Decal Library, it contains no version indicator file!\n")

                    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

                    pngs = []
                    other_images = []

                    for f in files:
                        if f.lower().endswith('.png'):
                            pngs.append(f)

                        elif any(f.lower().endswith(end) for end in ['.jpg', '.jpeg', '.gif', '.tga']):
                            other_images.append(f) 

                    if pngs:
                        log.append("\nSince it contains .png image files, Info Decals can be batch-created from it.\n")

                    if other_images:
                        log.append("\nSince it contains non-png image files, you need to first convert them to .pngs, from which you can then batch-create Info Decals.\n")

                    if pngs or other_images:
                        log.append("Check the documentation for details: https://machin3.io/DECALmachine/docs/decal_creation_batch/\n")

                    quanrantine_info.append(f"☢  Quarantined {shortpath}. Library is invalid. It contains no version indicator file!")

                    if path in assets_dict['CORRUPT']:
                        folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
                        corrupted = is_library_corrupted(path, verbose=True)

                        log.append(f"\nIn addition, this library is corrupt as well. {len(corrupted)} / {len(folders)} folders in this Library are not Decal folders, as they don't contain all of the following 3 files: decal.blend AND decal.png AND uuid:\n")

                        for folder in corrupted:
                            log.append(f"📁 {folder} - invalid Decal folder\n")

                elif quarantine_type == 'CORRUPT':
                    print(f"INFO: Library {get_short_library_path(path)} is corrupt, moving into Quarantine at {get_short_library_path(dst)}")

                    is_trimsheet, contents = is_library_trimsheet(path, verbose=True)

                    if asset_type == 'TRIMS' and not is_trimsheet:
                        log.append("This library is corrupt. It's in the Trims location, but does not appear to be a valid Trimsheet library.\n")

                        folders, files = contents

                        for f in folders:
                            log.append(f"📁 {f} - {'valid' if is_decal_folder_valid(os.path.join(path, f)) else 'invalid'} Decal folder\n")

                        for f in files:
                            log.append(f"📄 {f}\n")

                        quanrantine_info.append(f"☢  Quarantined {shortpath}. Library is corrupt. It was in the Trims location, but not a valid Trimsheet Library!")

                    else:
                        folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
                        corrupted = is_library_corrupted(path, verbose=True)

                        log.append(f"This library is corrupt. {len(corrupted)} / {len(folders)} folders in this Library are not Decal folders, as they don't contain all of the following 3 files: decal.blend AND decal.png AND uuid:\n")

                        for folder in corrupted:
                            log.append(f"📁 {folder} - invalid Decal folder\n")

                        quanrantine_info.append(f"☢  Quarantined {shortpath}. Library is corrupt. There are non-Decal folders in it!")

                    if path in assets_dict['AMBIGUOUS']:
                        versions = get_version_files(path)

                        log.append(f"\nIn addition, this library is ambiguous as well, as there are multiple indicated library versions:\n")

                        for fl in versions:
                            log.append(f"📄 {fl} - version {get_version_from_filename(fl)}\n")

                move(path, dst)

                time_code = get_time_code().split(' ')
                log_path = os.path.join(dst, "log.txt")

                with open(log_path, 'w') as f:
                   f.write(f"This file was generated by DECALmachine on {time_code[0]} at {time_code[1]} when the {'Decal' if asset_type == 'DECALS' else 'Trimsheet'} Library '{os.path.basename(path)}' was moved to Quarantine.\n\n")

                   for line in log:
                       f.write(line)

        reload_all_assets()

        if quanrantine_info:

            logspath = makedir(os.path.join(get_path(), 'logs'))
            name = get_indexed_suffix_name(os.listdir(logspath), 'quarantined', end='.log')

            time_code = get_time_code().split(' ')
            log_path = os.path.join(os.path.join(logspath, name))

            with open(log_path, 'w') as f:
               f.write(f"This file was generated by DECALmachine on {time_code[0]} at {time_code[1]} when the moving the following {len(obsolete + invalid + corrupt)} folders into Quarantine\n\n")

               for line in quanrantine_info:
                   f.write(f"{line}\n")

               f.writelines(['\n', 'ℹ  If you require assistance with these quarantined libraries, you can get in touch with decal@machin3.io!\n', '   Make sure to use the Get Support tool, if you do so!\n'])

            quanrantine_info.append('')
            quanrantine_info.append('ℹ  If you require assistance with these quarantined libraries, you can get in touch with decal@machin3.io!')
            quanrantine_info.append('      Make sure to use the Get Support tool, if you do so!')

            popup_message(quanrantine_info, title="Quarantine")

        return {'FINISHED'}

class Declutter(bpy.types.Operator):
    bl_idname = "machin3.declutter_assetspath"
    bl_label = "MACHIN3: Declutter Assetspath"
    bl_description = "De-clutter assets location"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        assets_dict = get_assets_dict()
        return assets_dict['CLUTTER']

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

    def execute(self, context):
        decluttered = declutter_assetspath()

        if decluttered:
            reload_all_assets()

        return {'FINISHED'}
