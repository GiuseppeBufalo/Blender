import bpy
import os
from shutil import copytree
from zipfile import ZipFile
import json
from . registration import get_prefs, register_atlases, get_version_files, get_version_from_filename, get_version_from_blender, get_version_as_float, is_library_corrupted
from . system import splitpath, load_json, makedir, save_json, printd
from . assets import reload_all_assets

def get_short_library_path(path, assets_root=True):
    assetspath = get_prefs().assetspath
    
    split = splitpath(assetspath)

    if assets_root:
        return path.replace(assetspath, f"{split[-1]}{os.sep}")
    else:
        return path.replace(assetspath, "")

def get_lib():
    idx = get_prefs().decallibsIDX
    libs = get_prefs().decallibsCOL
    active = libs[idx] if libs else None

    return idx, libs, active

def import_library(path):
    def invalid(name):
        return f"'{name}' is not a valid DECALmachine Library!"

    def exists(name, istrimsheet):
        return f"A {'Trim Sheet' if istrimsheet else 'Decal'} Library called '{name}' exists already."

    def itsanatlas(name):
        return [f"'{name}' is not a valid  Decal or Trim Sheet Library!", "It's an Atlas, which can't be imported here, because Atlases - unlike Trim Sheets - aren't bundled with individual Decal Assets!", "Import it from the Export Tab."]

    assetspath = get_prefs().assetspath
    basename = os.path.basename(path)

    if os.path.isdir(path):
        if any([os.path.exists(os.path.join(path, f)) for f in ['.is280', '.is20', '.is21', '.is22', '.is23', '.is24', '.is25', '.is29', '.is30']]):
            isatlas = all(os.path.exists(os.path.join(path, f)) for f in ['.isatlas', 'data.json'])

            if isatlas:
                data = load_json(os.path.join(path, 'data.json'))
                name = data.get('name')
                return itsanatlas(name)

            istrimsheet = all(os.path.exists(os.path.join(path, f)) for f in ['.istrimsheet', 'data.json'])

            if istrimsheet:
                data = load_json(os.path.join(path, 'data.json'))
                name = data.get('name')

            else:
                name = basename

            dst = os.path.join(assetspath, 'Trims' if istrimsheet else 'Decals', name)

            if os.path.exists(dst):
                return exists(name, istrimsheet)

            else:
                copytree(path, dst)
                reload_all_assets()
                return ""
        else:
            return invalid(basename)

    elif os.path.isfile(path) and os.path.splitext(path)[1].lower() == ".zip":
        with ZipFile(path, mode="r") as z:
            names = z.namelist()

            isversions = [f for f in names if len(splitpath(f)) == 2 and os.path.basename(f) in ['.is280', '.is20', '.is21', '.is22', '.is23', '.is24', '.is25', '.is29', '.is30']]

            if isversions:

                isdatajsons = [f for f in names if len(splitpath(f)) == 2 and os.path.basename(f) == "data.json"]

                isatlases = [f for f in names if len(splitpath(f)) == 2 and os.path.basename(f) == ".isatlas"]

                istrimsheets = [f for f in names if len(splitpath(f)) == 2 and os.path.basename(f) == ".istrimsheet"]

                if isdatajsons and isatlases:
                    d = z.read(isdatajsons[0])
                    data = json.loads(d)
                    name = data.get('name')
                    return itsanatlas(f"{os.path.basename(path)} ({name})")

                elif isdatajsons and istrimsheets:
                    istrimsheet = True
                    d = z.read(isdatajsons[0])
                    data = json.loads(d)
                    name = data.get('name')

                else:
                    istrimsheet = False
                    name = os.path.splitext(basename)[0]

                dst = os.path.join(assetspath, 'Trims' if istrimsheet else 'Decals', name)

                if os.path.exists(dst):
                    return exists(name, istrimsheet)

                elif istrimsheet:
                    for f in names:
                        split = splitpath(f)
                        split[0] = name
                        dst = os.path.join(assetspath, 'Trims', *split)

                        if z.getinfo(f).is_dir():
                            makedir(dst)

                        else:
                            with open(dst, 'wb') as fp:
                                fp.write(z.read(f))

                    reload_all_assets()
                    return ""

                else:
                    z.extractall(path=os.path.dirname(dst))
                    reload_all_assets()

            else:
                return invalid(basename)
    else:
        return invalid(basename)

def get_atlas():
    idx = get_prefs().atlasesIDX
    atlases = get_prefs().atlasesCOL
    active = atlases[idx] if atlases else None

    return idx, atlases, active

def import_atlas(path):
    def invalid(name):
        return "%s is not a valid DECALmachine 2.0 Atlas!" % (name)

    def exists(name):
        return "An Atlas called '%s' exists already." % (name)

    assetspath = get_prefs().assetspath
    basename = os.path.basename(path)

    if os.path.isdir(path):
        jsonpath = os.path.join(path, 'data.json')

        if os.path.exists(jsonpath):
            data = load_json(jsonpath)
            name = data.get('name')

            versionpath = os.path.join(path, '.is20')
            isatlaspath = os.path.join(path, '.isatlas')

            if os.path.exists(versionpath) and os.path.exists(isatlaspath):
                dst = os.path.join(assetspath, 'Atlases', name)

                if os.path.exists(dst):
                    return exists(name)

                else:
                    copytree(path, dst)
                    register_atlases(reloading=True)
                    return ""

            else:
                return invalid(name)
        else:
            return invalid(basename)

    elif os.path.isfile(path) and os.path.splitext(path)[1].lower() == ".zip":
        with ZipFile(path, mode="r") as z:
            names = z.namelist()

            isdatajsons = [f for f in names if len(splitpath(f)) == 2 and os.path.basename(f) == "data.json"]

            if isdatajsons:
                d = z.read(isdatajsons[0])
                data = json.loads(d)
                name = data.get('name')

                isversions = [f for f in names if len(splitpath(f)) == 2 and os.path.basename(f) == ".is20"]

                isatlases = [f for f in names if len(splitpath(f)) == 2 and os.path.basename(f) == ".isatlas"]

                if isversions and isatlases:
                    dst = os.path.join(assetspath, 'Atlases', name)

                    if os.path.exists(dst):
                        return exists(name)

                    else:
                        for f in names:
                            split = splitpath(f)
                            split[0] = name
                            dst = os.path.join(assetspath, 'Atlases', *split)

                            if z.getinfo(f).is_dir():
                                makedir(dst)

                            else:
                                with open(dst, 'wb') as fp:
                                    fp.write(z.read(f))

                        register_atlases(reloading=True)
                        return ""
                else:
                    return invalid(name)
            else:
                return invalid(basename)
    else:
        return invalid(basename)

def validate_presets(debug=False):
    assetspath = get_prefs().assetspath
    presetspath = os.path.join(assetspath, 'presets.json')
    preset_names = [str(i + 1) for i in range(10)]

    if os.path.exists(presetspath):
        presets = load_json(presetspath)

        if all([name in presets for name in preset_names]):
            return True
        else:
            print("WARNING: Corruption in presets .json detected")

    else:
        print("WARNING: No presets .json found")

    print("INFO: Initializing Decal Library Visibility Presets")
    presets = {}

    for i in range(10):
        name = str(i + 1)

        presets[name] = {}

        for lib in get_prefs().decallibsCOL:
            presets[name][lib.name] = {'isvisible': lib.isvisible,
                                       'ispanelcycle': lib.ispanelcycle}

    save_json(presets, presetspath)

    if debug:
        printd(presets, 'All Presets')

def poll_trimsheetlibs():
    return bpy.types.Scene.trimsheetlibs.keywords['items']
