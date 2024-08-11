import bpy
import os
import sys
import json
import platform
import site
import subprocess
import shutil
import re
from pprint import pprint
from . import registration as r
from .. import bl_info

enc = sys.getdefaultencoding()

def abspath(path):
    return os.path.abspath(bpy.path.abspath(path))

def normpath(path):
    return os.path.normpath(path)

def relpath(path):
    return bpy.path.relpath(path)

def splitpath(path):
    path = bpy.path.native_pathsep(normpath(path))
    return path.split(os.sep)

def quotepath(path):
    if " " in path:
        path = '"%s"' % (path)
    return path

def get_safe_filename(string):
    invalid = '<>:"/\\|?*'

    valid = ''.join(s if s not in invalid else '_' for s in string)

    return valid[:255]

    return

def get_file_size(path):
    try:
        size = os.path.getsize(path)
        return size

    except OSError as e:
        return None

def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        os.system('xdg-open "%s" %s &' % (path, "> /dev/null 2> /dev/null"))  # > sends stdout,  2> sends stderr

def get_new_directory_index(path):
    dirs = [f for f in sorted(os.listdir(path)) if os.path.isdir(os.path.join(path, f))]

    index = "001"

    while dirs:
        last = dirs.pop(-1)
        try:
            index = str(int(last[:3]) + 1).zfill(3)
            break
        except:
            pass

    return index

def makedir(pathstring, debug=False):
    if not os.path.exists(pathstring):
        if debug:
            print(f"WARNING: Creating {pathstring}, as the folder doesn't exist yet.")

        os.makedirs(pathstring)
    return pathstring

def get_folder_contents(path):
    if os.path.exists(path):
        contents = sorted([f for f in os.listdir(path)])

        folders = [c for c in contents if os.path.isdir(os.path.join(path, c))]
        files = [c for c in contents if os.path.isfile(os.path.join(path, c))]

        return folders, files

    else:
        return None, None

def remove_folder(path):
    if (exists := os.path.exists(path)) and (isfolder := os.path.isdir(path)):
        try:
            shutil.rmtree(path)
            return True

        except Exception as e:
            print(f"WARNING: Error while trying to remove {path}: {e}")

    elif exists:
        print(f"WARNING: Couldn't remove {path}, it's not a folder!")
    else:
        print(f"WARNING: Couldn't remove {path}, it doesn't exist!")

    return False

def load_json(pathstring):
    with open(pathstring, 'r') as f:
        jsondict = json.load(f)
    return jsondict

def save_json(jsondict, pathstring):
    try:
        with open(pathstring, 'w') as f:
            json.dump(jsondict, f, indent=4)

    except PermissionError:
        import traceback
        print()
        traceback.print_exc()

        print(80 * "-")
        print()
        print(" ! FOLLOW THE INSTALLATION INSTRUCTIONS ! ")
        print()
        print("You are not supposed to put DECALmachine into C:\Program Files\Blender Foundation\... etc.")
        print()
        print("https://machin3.io/DECALmachine/docs/installation/")
        print()
        print(80 * "-")

def printd(d, name='', sort=False):
    if name:
        print(f"\n{name}")
    pprint(d, sort_dicts=sort)

def get_python_paths(log):
    pythonbinpath = sys.executable

    if platform.system() == "Windows":
        pythonlibpath = os.path.join(os.path.dirname(os.path.dirname(pythonbinpath)), "lib")

    else:
        pythonlibpath = os.path.join(os.path.dirname(os.path.dirname(pythonbinpath)), "lib", os.path.basename(pythonbinpath))

    ensurepippath = os.path.join(pythonlibpath, "ensurepip")
    sitepackagespath = os.path.join(pythonlibpath, "site-packages")
    usersitepackagespath = site.getusersitepackages()

    easyinstallpath = os.path.join(sitepackagespath, "easy_install.py")
    easyinstalluserpath = os.path.join(usersitepackagespath, "easy_install.py")

    modulespaths = [os.path.join(path, 'modules') for path in bpy.utils.script_paths() if path.endswith('scripts')]

    print("Python Binary: %s %s" % (pythonbinpath, os.path.exists(pythonbinpath)))
    print("Python Library: %s %s" % (pythonlibpath, os.path.exists(pythonlibpath)))
    print("Ensurepip: %s %s\n" % (ensurepippath, os.path.exists(ensurepippath)))

    for path in modulespaths:
        print("Modules: %s %s" % (path, os.path.exists(path)))

    print("Site-Packages: %s %s" % (sitepackagespath, os.path.exists(sitepackagespath)))
    print("User Site-Packages: %s %s" % (usersitepackagespath, os.path.exists(usersitepackagespath)))
    print("EasyInstall Path: %s %s" % (easyinstallpath, os.path.exists(easyinstallpath)))
    print("EasyInstall User Path: %s %s\n" % (easyinstalluserpath, os.path.exists(easyinstalluserpath)))

    log.append("Python Binary: %s %s" % (pythonbinpath, os.path.exists(pythonbinpath)))
    log.append("Python Library: %s %s" % (pythonlibpath, os.path.exists(pythonlibpath)))
    log.append("Ensurepip: %s %s\n" % (ensurepippath, os.path.exists(ensurepippath)))

    for path in modulespaths:
        log.append("Modules: %s %s" % (path, os.path.exists(path)))

    log.append("Site-Packages: %s %s" % (sitepackagespath, os.path.exists(sitepackagespath)))
    log.append("User Site-Packages: %s %s" % (usersitepackagespath, os.path.exists(usersitepackagespath)))
    log.append("EasyInstall Path: %s %s" % (easyinstallpath, os.path.exists(easyinstallpath)))
    log.append("EasyInstall User Path: %s %s\n" % (easyinstalluserpath, os.path.exists(easyinstalluserpath)))

    return pythonbinpath, pythonlibpath, ensurepippath, modulespaths, sitepackagespath, usersitepackagespath, easyinstallpath, easyinstalluserpath

def remove_PIL(sitepackagespath, usersitepackagespath, modulespaths, log):
    for sitepath in [sitepackagespath, usersitepackagespath] + modulespaths:
        if os.path.exists(sitepath):
            folders = [(f, os.path.join(sitepath, f)) for f in os.listdir(sitepath)]

            for folder, path in folders:
                msg = "Existing PIL/Pillow found, removing: %s" % (path)

                if (folder.startswith("Pillow") and folder.endswith("egg")) or folder.startswith("Pillow") or folder == "PIL":
                    print(msg)
                    log.append(msg)

                    shutil.rmtree(path, ignore_errors=True)

def install_pip(pythonbinpath, ensurepippath, log, mode='USER', debug=True):
    if mode == 'USER':
        cmd = [pythonbinpath, ensurepippath, "--upgrade", "--user"]

    elif mode == 'ADMIN':
        cmd = [pythonbinpath, ensurepippath, "--upgrade"]

    pip = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if debug:
        pipout = [out.strip() for out in pip.stdout.decode(enc).split("\n") if out]
        piperr = [err.strip() for err in pip.stderr.decode(enc).split("\n") if err]

        log += pipout
        log += piperr

    if pip.returncode == 0:
        if debug:
            for out in pipout + piperr:
                print(" •", out)

        print("Sucessfully installed pip!\n")
        return True

    else:
        if debug:
            for out in pipout + piperr:
                print(" •", out)

        print("Failed to install pip!\n")
        return False

def update_pip(pythonbinpath, log, mode='USER', debug=True):
    if mode == 'USER':
        cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "--user", "pip"]

    elif mode == 'ADMIN':
        cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "pip"]

    update = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if debug:
        updateout = [out.strip() for out in update.stdout.decode(enc).split("\n") if out]
        updateerr = [err.strip() for err in update.stderr.decode(enc).split("\n") if err]

        log += updateout
        log += updateerr

    if update.returncode == 0:
        if debug:
            for out in updateout + updateerr:
                print(" •", out)

        print("Sucessfully updated pip!\n")
        return True
    else:
        if debug:
            for out in updateout + updateerr:
                print(" •", out)

        print("Failed to update pip!\n")
        return False

def install_wheel(pythonbinpath, log, mode='USER', debug=True):
    if mode == 'USER':
        cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "--user", "wheel"]

    else:
        cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "wheel"]

    wheel = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if debug:
        wheelout = [out.strip() for out in wheel.stdout.decode(enc).split("\n") if out]
        wheelerr = [err.strip() for err in wheel.stderr.decode(enc).split("\n") if err]

        log += wheelout
        log += wheelerr

    if wheel.returncode == 0:

        if debug:
            for out in wheelout + wheelerr:
                print(" •", out)

        print("Sucessfully installed wheel!\n")
        return True
    else:
        if debug:
            for out in wheelout + wheelerr:
                print(" •", out)

        print("Failed to install wheel!\n")
        return False

def install_PIL(pythonbinpath, log, version=None, mode='USER', debug=True):
    if mode == 'USER':
        if version:
            cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "--user", "Pillow==%s" % (version)]
        else:
            cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "--user", "Pillow"]

    else:
        if version:
            cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "Pillow==%s" % (version)]
        else:
            cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "Pillow"]

    pil = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if debug:

        pilout = [out.strip() for out in pil.stdout.decode(enc).split("\n") if out]
        pilerr = [err.strip() for err in pil.stderr.decode(enc).split("\n") if err]

        log += pilout
        log += pilerr

    if pil.returncode == 0:

        if debug:
            for out in pilout + pilerr:
                print(" •", out)

        print("Sucessfully installed PIL!\n")
        return True
    else:
        if debug:
            for out in pilout + pilerr:
                print(" •", out)

        print("Failed to install PIL!\n")
        return False

def easy_install_PIL(pythonbinpath, easyinstallpath, easyinstalluserpath, log, version=None, mode='USER', debug=True):
    easypath = easyinstallpath if os.path.exists(easyinstallpath) else easyinstalluserpath if os.path.exists(easyinstalluserpath) else None

    if easypath:
        if mode == 'USER':
            if version:
                cmd = [pythonbinpath, easypath, "--user", "Pillow==%s" % (version)]
            else:
                cmd = [pythonbinpath, easypath, "--user", "Pillow"]

        elif mode == 'ADMIN':
            if version:
                cmd = [pythonbinpath, easypath, "Pillow==%s" % (version)]
            else:
                cmd = [pythonbinpath, easypath, "Pillow"]

        pil = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if debug:
            pilout = [out.strip() for out in pil.stdout.decode(enc).split("\n") if out]
            pilerr = [err.strip() for err in pil.stderr.decode(enc).split("\n") if err]

            log += pilout
            log += pilerr

        if pil.returncode == 0:
            if debug:
                for out in pilout + pilerr:
                    print(" •", out)

            print("Sucessfully installed PIL!\n")
            return True
        else:
            if debug:
                for out in pilout + pilerr:
                    print(" •", out)

            print("Failed to install pip!\n")
            return False
    else:
        print("Easy install could not be found!\n")

        return False

def update_sys_path(usersitepackagespath, log):
    if usersitepackagespath in sys.path:
        print("\nFound %s in sys.path." % (usersitepackagespath))
        log.append("\nFound %s in sys.path." % (usersitepackagespath))

    else:
        sys.path.append(usersitepackagespath)

        print("\nAdded %s to sys.path" % (usersitepackagespath))
        log.append("\nAdded %s to sys.path" % (usersitepackagespath))

def verify_user_sitepackages():
    usersitepackagespath = site.getusersitepackages()

    if os.path.exists(usersitepackagespath) and usersitepackagespath not in sys.path:
        sys.path.append(usersitepackagespath)

def test_import_PIL(installed, log, usersitepackagespath=None):
    if installed:
        if usersitepackagespath:
            update_sys_path(usersitepackagespath, log)

        bpy.utils.refresh_script_paths()

        try:
            from PIL import Image

            print("Successfully imported PIL's Image module. PIL is ready to go.")
            log.append("Successfully imported PIL's Image module. PIL is ready to go.")

            return True, False

        except:
            print("Failed to import PIL's Image module. Restart is required.")
            log.append("Failed to import PIL's Image module. Restart is required.")

            return False, True

    else:
        return False, False

def get_PIL_image_module_path(Image=None):
    try:
        if not Image:
            from PIL import Image

        PILRegex = re.compile(r"<module 'PIL._imaging' from '([^']+)'>")

        mo = PILRegex.match(str(Image.core))

        return mo.group(1)

    except:
        return None

def log(text='', *texts, debug=True):
    if debug:
        output = [text] + list(texts) if texts else [text]
        print(*output)

def get_env():
    log = ["\nENVIRONMENT\n"]

    for key, value in os.environ.items():
        log.append("%s: %s\n" % (key, value))

    return log

def write_log(path, log):
    oldlog = []
    env = get_env()

    if os.path.exists(path):
        with open(path, mode="r") as f:
            oldlog = f.readlines()

    with open(os.path.join(path), mode="w") as f:
        f.writelines(oldlog + [l + "\n" for l in log] + env)

update_files = None

def get_update_files(force=False):
    global update_files

    if update_files is None or force:
        update_files = []

        home_dir = os.path.expanduser('~')

        if os.path.exists(home_dir):
            download_dir = os.path.join(home_dir, 'Downloads')

            home_files = [(f, os.path.join(home_dir, f)) for f in os.listdir(home_dir) if f.startswith(bl_info['name']) and f.endswith('.zip')]
            dl_files = [(f, os.path.join(download_dir, f)) for f in os.listdir(download_dir) if f.startswith(bl_info['name']) and f.endswith('.zip')] if os.path.exists(download_dir) else []

            zip_files = home_files + dl_files

            for filename, path in zip_files:
                split = filename.split('_')

                if len(split) == 2:
                    tail = split[1].replace('.zip', '')
                    s = tail.split('.')

                    if len(s) >= 3:
                        try:
                            version = tuple(int(v) for v in s[:3])

                        except:
                            continue

                        if tail == '.'.join(str(v) for v in bl_info['version']):
                            continue

                        update_files.append((path, tail, version))

        update_files = sorted(update_files, key=lambda x: (x[2], x[1]))

    return update_files

def get_bl_info_from_file(path):
    if os.path.exists(path):
        lines = ""
        
        with open(path) as f:
            for line in f:
                if line := line.strip():
                    lines += (line)
                else:
                    break

        try:
            blinfo = eval(lines.replace('bl_info = ', ''))

        except:
            print(f"WARNING: failed reading bl_info from {path}")
            return

        if 'name' in blinfo and 'version' in blinfo:
            name = blinfo['name']
            version = blinfo['version']

            if name == bl_info['name']:
                if version != bl_info['version']:
                    return blinfo

                else:
                    print(f"WARNING: Versions are identical, an update would be pointless")

            else:
                print(f"WARNING: Addon Mismatch, you can't update {bl_info['name']} to {name}")

    else:
        print(f"WARNING: failed reading bl_info from {path}, path does not exist")

def verify_update():
    path = r.get_prefs().path
    update_path = os.path.join(path, '_update')

    if os.path.exists(update_path):
        init_path = os.path.join(update_path, bl_info['name'], '__init__.py')

        blinfo = get_bl_info_from_file(init_path)

        if blinfo:
            r.get_prefs().update_msg = f"{blinfo['name']} {'.'.join(str(v) for v in blinfo['version'])} is ready to be installed."
            r.get_prefs().show_update = True

        else:
            remove_folder(update_path)

        return

    if r.get_prefs().show_update:
        r.get_prefs().show_update = False

    if r.get_prefs().update_msg:
        r.get_prefs().update_msg = ''

def install_update(keep_assets=True):
    path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    update_path = os.path.join(path, '_update')

    if os.path.exists(update_path):
        src = os.path.join(update_path, bl_info['name'])

        if os.path.exists(src):

            dst = os.path.join(os.path.dirname(path), f"_update_{bl_info['name']}")

            if keep_assets:
                assets_src = os.path.join(path, "assets")
                assets_dst = os.path.join(src, "assets")

                remove_folder(assets_dst)

                os.rename(assets_src, assets_dst)

            if os.path.exists(dst):
                remove_folder(dst)

            os.rename(src, dst)

            remove_folder(path)

            os.rename(dst, path)
