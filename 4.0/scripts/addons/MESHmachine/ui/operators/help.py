import bpy
import os
import sys
import socket
from ... utils.registration import get_path, get_prefs
from ... utils.system import makedir, open_folder
from ... import bl_info


enc = sys.getdefaultencoding()


class GetSupport(bpy.types.Operator):
    bl_idname = "machin3.get_meshmachine_support"
    bl_label = "MACHIN3: Get MESHmachine Support"
    bl_description = "Generate Log Files and Instructions for a Support Request."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        logpath = makedir(os.path.join(get_path(), "logs"))
        resourcespath = makedir(os.path.join(get_path(), "resources"))
        assetspath = get_prefs().assetspath



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

                    elif line.startswith('MESHmachine'):
                        idx = newlines.index(line)

                        new = ['Assets:']
                        libs = [f for f in sorted(os.listdir(assetspath)) if os.path.isdir(os.path.join(assetspath, f))]

                        for lib in libs:
                            new.append('    %s' % (lib))

                        for n in new:
                            idx += 1
                            newlines.insert(idx, '  %s\n' % (n))

                f.seek(0)
                f.writelines(newlines)
