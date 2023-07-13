import bpy
import os
import sys
import socket
from ... utils.registration import get_path, get_prefs, get_version_files, get_version_from_filename, get_version_from_blender, is_library_corrupted
from ... utils.system import makedir, open_folder, get_PIL_image_module_path
from ... import bl_info


enc = sys.getdefaultencoding()


class GetSupport(bpy.types.Operator):
    bl_idname = "machin3.get_decalmachine_support"
    bl_label = "MACHIN3: Get DECALmachine Support"
    bl_description = "Generate Log Files and Instructions for a Support Request."
    bl_options = {'REGISTER'}

    def execute(self, context):
        logpath = makedir(os.path.join(get_path(), "logs"))
        resourcespath = makedir(os.path.join(get_path(), "resources"))
        assetspath = get_prefs().assetspath


        pillog = []

        if not os.path.exists(os.path.join(logpath, "pil.log")):
            pillog.append("'pil.log' not found!")

            try:
                import PIL
                pillog.append(f"PIL {PIL.__version__} imported successfully")
                pil = True

            except:
                pillog.append("PIL could not be imported")
                pil = False

            if pil:
                try:
                    from PIL import Image
                    pillog.append(f"PIL's Image module imported successfull from '{get_PIL_image_module_path(Image)}'")

                except:
                    pillog.append("PIL's Image module could not be imported")


            with open(os.path.join(logpath, "pil.log"), "w") as f:
                f.writelines([l + "\n" for l in pillog])



        sysinfopath = os.path.join(logpath, "system_info.txt")
        bpy.ops.wm.sysinfo(filepath=sysinfopath)

        self.add_system_info(context, sysinfopath, assetspath)



        with open(os.path.join(resourcespath, "readme.html"), "r") as f:
            html = f.read()

        html = html.replace("VERSION", ".".join((str(v) for v in bl_info['version'])))

        with open(os.path.join(logpath, "README.html"), "w") as f:
            f.write(html)



        open_folder(logpath)

        return {'FINISHED'}

    def add_system_info(self, context, sysinfopath, assetspath):
        if os.path.exists(sysinfopath):
            with open(sysinfopath, 'r+', encoding=enc) as f:
                lines = f.readlines()
                newlines = lines.copy()

                for line in lines:
                    if all(string in line for string in ['version:', 'branch:', 'hash:']):
                        idx = newlines.index(line)
                        newlines.pop(idx)
                        newlines.insert(idx, line.replace(', type:', f", revision: {bl_info['revision']}, type:"))

                    elif line.startswith('DECALmachine'):
                        idx = newlines.index(line)

                        new = [f"Assets: {get_version_from_blender()} {get_prefs().assetspath}"]

                        for folder in ['Atlases', 'Decals', 'Trims']:
                            new.append('  %s:' % (folder))

                            libs = [(f, ', '.join([get_version_from_filename(v) for v in get_version_files(libpath)])) for f in sorted(os.listdir(os.path.join(assetspath, folder))) if os.path.isdir(libpath := os.path.join(assetspath, folder, f))]

                            for name, versions in libs:
                                if is_library_corrupted(os.path.join(assetspath, folder, name)):
                                    if versions:
                                        corrupted = ' - corrupted'
                                    else:
                                        corrupted = 'corrupted'
                                else:
                                    corrupted = ''

                                new.append(f"    {name}: {versions}{corrupted}")

                        new.extend(['',
                                    'Color Management',
                                    f"  View Transform: {context.scene.view_settings.view_transform}",
                                    f"            Look: {context.scene.view_settings.look}",
                                    f"       Sequencer: {context.scene.sequencer_colorspace_settings.name}",
                                    ''])

                        for n in new:
                            idx += 1
                            newlines.insert(idx, '  %s\n' % (n))

                f.seek(0)
                f.writelines(newlines)
