import bpy
from bpy.props import StringProperty, BoolProperty
import os
from ... utils.system import load_json, save_json, printd
from ... utils.registration import get_path, get_prefs
from ... utils.library import validate_presets


class LibraryVisibilityPreset(bpy.types.Operator):
    bl_idname = "machin3.decal_library_visibility_preset"
    bl_label = "MACHIN3: Visibility Preset"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Preset Name", default="1")
    store: BoolProperty(name="Store Preset", default=False)

    @classmethod
    def description(cls, context, properties):
        desc = f"Recall Preset {properties.name}\nSHIFT: Store current State as Preset {properties.name}"

        return desc

    def invoke(self, context, event):
        if validate_presets():
            self.store = event.shift
            return self.execute(context)
        else:
            return {'CANCELLED'}

    def execute(self, context):
        debug = False

        assetspath = get_prefs().assetspath
        presetspath = os.path.join(assetspath, 'presets.json')

        presets = load_json(presetspath)

        if self.store:
            self.store_preset(context, self.name, presets, get_prefs(), presetspath, debug=debug)

        else:
            self.recall_preset(self.name, presets, get_prefs(), debug=debug)

        return {'FINISHED'}

    def store_preset(self, context, name, presets, prefs, presetspath, debug=False):
        print(f"INFO: Storing preset {name}")

        presets[name] = {}

        for lib in prefs.decallibsCOL:
            presets[name][lib.name] = {'isvisible': lib.isvisible,
                                       'ispanelcycle': lib.ispanelcycle}

        if debug:
            printd(presets[name])

        save_json(presets, presetspath)

        if context.visible_objects:
            context.visible_objects[0].select_set(context.visible_objects[0].visible_get())

    def recall_preset(self, name, presets, prefs, debug=False):
        print(f"INFO: Recalling preset {name}")

        preset = presets.get(name)

        if debug:
            printd(preset, name=f"Preset: {self.name}")

        for libname in preset:
            lib = prefs.decallibsCOL.get(libname)

            if lib:
                lib.isvisible = preset[libname]['isvisible']
                lib.ispanelcycle = preset[libname]['ispanelcycle']
            else:
                print(f"WARNING: Library {libname}, looks like the preset is outdated.")
