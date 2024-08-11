import bpy
import os
from bpy.props import StringProperty, EnumProperty
from shutil import rmtree
import json
from ... utils.ui import popup_message, get_icon
from ... utils.registration import get_prefs, reload_decal_libraries, reload_trim_libraries
from ... utils.assets import get_assets_dict, verify_assetspath
from ... utils.library import get_lib

class Move(bpy.types.Operator):
    bl_idname = "machin3.move_decal_or_trim_library"
    bl_label = "MACHIN3: Move Decal or Trim Library"
    bl_options = {'INTERNAL'}
    bl_description = "Move library up or down.\nThis controls the position in the DECALmachine pie menus.\nSave prefs to remember"

    direction: EnumProperty(items=[("UP", "Up", ""),
                                   ("DOWN", "Down", "")])

    @classmethod
    def poll(cls, context):
        _, _, active = get_lib()
        return active

    def execute(self, context):
        idx, libs, _ = get_lib()

        if self.direction == "UP":
            nextidx = max(idx - 1, 0)
        elif self.direction == "DOWN":
            nextidx = min(idx + 1, len(libs) - 1)

        libs.move(idx, nextidx)
        get_prefs().decallibsIDX = nextidx

        return {'FINISHED'}

class Clear(bpy.types.Operator):
    bl_idname = "machin3.clear_decal_and_trim_libraries"
    bl_label = "MACHIN3: Clear Decal and Trim Libraries"
    bl_options = {'INTERNAL'}
    bl_description = "Clear library prefs, resets them into their original state.\nNo decals will be lost!\nSave prefs and restart Blender to complete the process"

    @classmethod
    def poll(cls, context):
        return get_prefs().decallibsCOL

    def execute(self, context):
        get_prefs().decallibsCOL.clear()
        get_assets_dict(force=True)

        return {'FINISHED'}

class Reload(bpy.types.Operator):
    bl_idname = "machin3.reload_decal_and_trim_libraries"
    bl_label = "MACHIN3: Reload Decal and Trim Libraries"
    bl_options = {'INTERNAL'}
    bl_description = "Reload all libraries. Propagates lock and slice settings.\nSave prefs to complete the process"

    def execute(self, context):
        verify_assetspath()

        reload_decal_libraries()
        reload_trim_libraries()

        return {'FINISHED'}

class Rename(bpy.types.Operator):
    bl_idname = "machin3.rename_decal_or_trim_library"
    bl_label = "Rename Decal or Trim Sheet Library"
    bl_options = {'INTERNAL'}
    bl_description = "Rename selected library"

    newlibname: StringProperty(name="New Name")

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        row = column.split(factor=0.25)
        row.label(text="Old Name:")
        row.label(text=self.active.name)

        row = column.split(factor=0.25)
        row.label(text="New Name:")
        row.prop(self, "newlibname", text="")

    @classmethod
    def poll(cls, context):
        _, _, active = get_lib()
        return active and not active.islocked

    def invoke(self, context, event):
        _, _, self.active = get_lib()

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        assetspath = get_prefs().assetspath

        libtype = 'Trims' if self.active.istrimsheet else 'Decals'

        oldlibpath = os.path.join(assetspath, libtype, self.active.name)
        oldlibname = self.active.name

        newlibname = self.newlibname.strip()

        if newlibname:
            if newlibname != oldlibname:
                newlibpath = os.path.join(assetspath, libtype, newlibname)
                if not os.path.exists(newlibpath):
                    os.rename(oldlibpath, newlibpath)

                    get_assets_dict(force=True)

                    if self.active.istrimsheet:
                        jsonpath = os.path.join(newlibpath, 'data.json')

                        if os.path.exists(jsonpath):
                            with open(jsonpath, 'r') as f:
                                sheetdata = json.load(f)

                            sheetdata['name'] = newlibname

                            with open(jsonpath, 'w') as f:
                                json.dump(sheetdata, f, indent=4)

                        reload_trim_libraries()

                    else:
                        reload_decal_libraries()

                    print(f" • Renamed {'trim' if self.active.istrimsheet else 'decal'} library {oldlibname} to {newlibname}")
                    self.newlibname = ""
                else:
                    popup_message("This library exists already, choose another name!", title="Failed to add library", icon="ERROR")
            else:
                popup_message("The new name needs to be different from the old one.", title="Failed to rename library", icon="ERROR")
        else:
            popup_message("No new name chosen.", title="Failed to rename library", icon="ERROR")

        return {'FINISHED'}

class Remove(bpy.types.Operator):
    bl_idname = "machin3.remove_decal_or_trim_library"
    bl_label = "Remove Decal or Trim Library"
    bl_description = "Remove selected decal or trim sheet library and all the contained decal assets and trim sheet data"

    def draw(self, context):
        layout = self.layout

        layout.label(text=f"This removes the {'trim' if self.active.istrimsheet else 'decal'} library '{self.active.name}' and all its Decals!", icon_value=get_icon("error"))
        layout.label(text="Are you sure? This cannot be undone!")

    @classmethod
    def poll(cls, context):
        _, _, active = get_lib()
        return active and not active.islocked

    def invoke(self, context, event):
        self.idx, self.libs, self.active = get_lib()

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def execute(self, context):
        assetspath = get_prefs().assetspath

        path = os.path.join(assetspath, 'Trims' if self.active.istrimsheet else 'Decals', self.active.name)

        if os.path.exists(path):
            rmtree(path)

            get_prefs().decallibsIDX = min([len(self.libs) - 2, self.idx])

        else:
            popup_message("Have you already removed it manualy, while Blender was running?", title=f"{'Trim' if self.active.istrimsheet else 'Decal'} Library '{self.active.name}' not found", icon="ERROR")

        get_assets_dict(force=True)
        reload_trim_libraries() if self.active.istrimsheet else reload_decal_libraries()

        return {'FINISHED'}
