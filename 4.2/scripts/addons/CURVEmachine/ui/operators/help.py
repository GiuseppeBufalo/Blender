import bpy
import os
import sys
import socket
from ... utils.registration import get_path, get_prefs
from ... utils.system import makedir, open_folder
from ... import bl_info


enc = sys.getdefaultencoding()


class GetSupport(bpy.types.Operator):
    bl_idname = "machin3.get_curvemachine_support"
    bl_label = "MACHIN3: Get CURVEmachine Support"
    bl_description = "Generate Log Files and Instructions for a Support Request."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        logpath = makedir(os.path.join(get_path(), "logs"))
        resourcespath = makedir(os.path.join(get_path(), "resources"))



        sysinfopath = os.path.join(logpath, "system_info.txt")
        bpy.ops.wm.sysinfo(filepath=sysinfopath)

        self.add_system_info(context, sysinfopath)



        with open(os.path.join(resourcespath, "readme.html"), "r") as f:
            html = f.read()

        html = html.replace("VERSION", ".".join((str(v) for v in bl_info['version'])))

        with open(os.path.join(logpath, "README.html"), "w") as f:
            f.write(html)



        open_folder(logpath)

        return {'FINISHED'}

    def add_system_info(self, context, sysinfopath):
        if os.path.exists(sysinfopath):
            with open(sysinfopath, 'r+', encoding=enc) as f:
                lines = f.readlines()
                newlines = lines.copy()

                for line in lines:
                    if all(string in line for string in ['version:', 'branch:', 'hash:']):
                        idx = newlines.index(line)
                        newlines.pop(idx)

                        newlines.insert(idx, line.replace(', type:', f", revision: {bl_info['revision']}, type:"))

                f.seek(0)
                f.writelines(newlines)
