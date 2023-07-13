import bpy
import os
from ... utils.registration import get_path
from ... utils.system import makedir, open_folder
from ... import bl_info


class GetSupport(bpy.types.Operator):
    bl_idname = "machin3.get_punchit_support"
    bl_label = "MACHIN3: Get PUNCHit Support"
    bl_description = "Generate Log Files and Instructions for a Support Request."
    bl_options = {'REGISTER'}

    def execute(self, context):
        logpath = makedir(os.path.join(get_path(), "logs"))
        resourcespath = makedir(os.path.join(get_path(), "resources"))



        sysinfopath = os.path.join(logpath, "system_info.txt")
        bpy.ops.wm.sysinfo(filepath=sysinfopath)



        with open(os.path.join(resourcespath, "readme.html"), "r") as f:
            html = f.read()

        html = html.replace("VERSION", ".".join((str(v) for v in bl_info['version'])))

        with open(os.path.join(logpath, "README.html"), "w") as f:
            f.write(html)



        open_folder(logpath)

        return {'FINISHED'}
