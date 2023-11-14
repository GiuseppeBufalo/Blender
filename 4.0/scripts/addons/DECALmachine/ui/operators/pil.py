import bpy
from bpy.props import BoolProperty
import os
import platform
from ... utils.registration import get_prefs, get_path
from ... utils.system import makedir, write_log, get_python_paths, install_pip, update_pip, install_wheel, install_PIL, easy_install_PIL, test_import_PIL, remove_PIL


version = "9.0.1"


class InstallPIL(bpy.types.Operator):
    bl_idname = "machin3.install_pil"
    bl_label = "MACHIN3: Install PIL"
    bl_description = "Install pip and PIL on the User Level\nALT: Suppress Debug Output"
    bl_options = {'REGISTER'}

    debug: BoolProperty(name="Log Debug Output", default=True)

    def invoke(self, context, event):

        self.debug = not event.alt

        return self.execute(context)

    def execute(self, context):
        global version

        log = []
        logspath = makedir(os.path.join(get_path(), "logs"))

        print("\nDECALmachine: Installing PIL %s\n" % version)
        print("Platform:", platform.system())

        log.append("\nDECALmachine: Installing PIL %s\n" % version)
        log.append("Platform: %s" % (platform.system()))

        pythonbinpath, pythonlibpath, ensurepippath, modulespaths, sitepackagespath, usersitepackagespath, _, _ = get_python_paths(log)

        remove_PIL(sitepackagespath, usersitepackagespath, modulespaths, log)

        print()
        log.append("\n")

        if not self.debug:
            log.append('Supressing Debug Output!')

        installed = install_pip(pythonbinpath, ensurepippath, log, mode='USER', debug=self.debug)

        if installed:
            installed = update_pip(pythonbinpath, log, mode='USER', debug=self.debug)

            install_wheel(pythonbinpath, log, mode='USER', debug=self.debug)

            installed = install_PIL(pythonbinpath, log, version=version, mode='USER', debug=self.debug)

            get_prefs().pil, get_prefs().pilrestart = test_import_PIL(installed, log, usersitepackagespath)

        logpath = os.path.join(logspath, "pil.log")
        write_log(logpath, log)

        return {'FINISHED'}


class InstallPILAdmin(bpy.types.Operator):
    bl_idname = "machin3.install_pil_admin"
    bl_label = "MACHIN3: Install PIL (Admin)"
    bl_description = "Install pip and PIL for Blender's Python\nALT: Suppress Debug Output"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if platform.system() == "Darwin" and "AppTranslocation" in bpy.app.binary_path:
            return False
        return True

    def invoke(self, context, event):
        global version

        debug = not event.alt

        log = []
        logspath = makedir(os.path.join(get_path(), "logs"))

        print("\nDECALmachine: Installing PIL %s (Admin)\n" % version)
        print("Platform:", platform.system())

        log.append("\nDECALmachine: Installing PIL %s (Admin)\n" % version)
        log.append("Platform: %s" % (platform.system()))

        pythonbinpath, pythonlibpath, ensurepippath, modulespaths, sitepackagespath, usersitepackagespath, _, _ = get_python_paths(log)

        remove_PIL(sitepackagespath, usersitepackagespath, modulespaths, log)

        print()
        log.append("\n")

        if not debug:
            log.append('Supressing Debug Output!')

        installed = install_pip(pythonbinpath, ensurepippath, log, mode='ADMIN', debug=debug)

        if installed:
            installed = update_pip(pythonbinpath, log, mode='ADMIN', debug=debug)

            installed = install_PIL(pythonbinpath, log, version=version, mode='ADMIN', debug=debug)

            get_prefs().pil, get_prefs().pilrestart = test_import_PIL(installed, log)

        logpath = os.path.join(logspath, "pil.log")
        write_log(logpath, log)

        return {'FINISHED'}


class EasyInstallPILAdmin(bpy.types.Operator):
    bl_idname = "machin3.easy_install_pil_admin"
    bl_label = "MACHIN3: Easy Install PIL (Admin)"
    bl_description = "Easy Installs PIL for Blender's Python\nALT: Suppress Debug Output"
    bl_options = {'REGISTER'}


    @classmethod
    def poll(cls, context):
        if platform.system() == "Darwin" and "AppTranslocation" in bpy.app.binary_path:
            return False
        return True


    def invoke(self, context, event):
        global version

        debug = not event.alt

        log = []
        logspath = makedir(os.path.join(get_path(), "logs"))

        print("\nDECALmachine: Easy Installing PIL %s (Admin)\n" % version)
        print("Platform:", platform.system())

        log.append("\nDECALmachine: Easy Installing PIL %s (Admin)\n" % version)
        log.append("Platform: %s" % (platform.system()))

        pythonbinpath, pythonlibpath, ensurepippath, modulespaths, sitepackagespath, usersitepackagespath, easyinstallpath, easyinstalluserpath = get_python_paths(log)

        remove_PIL(sitepackagespath, usersitepackagespath, modulespaths, log)

        print()
        log.append("\n")

        if not debug:
            log.append('Supressing Debug Output!')

        installed = install_pip(pythonbinpath, ensurepippath, log, mode='ADMIN', debug=debug)

        if installed:
            installed = update_pip(pythonbinpath, log, mode='ADMIN', debug=debug)

            installed = easy_install_PIL(pythonbinpath, easyinstallpath, easyinstalluserpath, log, version=version, mode='ADMIN', debug=debug)

            get_prefs().pil, get_prefs().pilrestart = test_import_PIL(installed, log)

        logpath = os.path.join(logspath, "pil.log")
        write_log(logpath, log)

        return {'FINISHED'}


class PurgePIL(bpy.types.Operator):
    bl_idname = "machin3.purge_pil"
    bl_label = "MACHIN3: Purge PIL"
    bl_description = "Attempt to remove PIL from the current user profile and Blender Python's site-packages."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        log = []
        logspath = makedir(os.path.join(get_path(), "logs"))

        print("\nDECALmachine: Purging PIL\n")
        print("Platform:", platform.system())

        log.append("\nDECALmachine: Purging PIL\n")
        log.append("Platform: %s" % (platform.system()))

        _, _, _, modulespaths, sitepackagespath, usersitepackagespath, _, _ = get_python_paths(log)

        remove_PIL(sitepackagespath, usersitepackagespath, modulespaths, log)

        get_prefs().pil = False
        get_prefs().pilrestart = False

        logpath = os.path.join(logspath, "pil.log")
        write_log(logpath, log)

        return {'FINISHED'}
