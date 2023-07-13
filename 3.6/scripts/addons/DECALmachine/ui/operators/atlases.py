import bpy
import os
from bpy.props import StringProperty, EnumProperty
from shutil import rmtree
import json
from ... utils.ui import popup_message, get_icon
from ... utils.registration import get_prefs, register_atlases
from ... utils.library import get_atlas


class Move(bpy.types.Operator):
    bl_idname = "machin3.move_atlas"
    bl_label = "MACHIN3: Move Atlas"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Move Atlas up or down.\nThis controls which Atlas is considered first, when a Decal is found in multiple registered Atlases."

    direction: EnumProperty(items=[("UP", "Up", ""),
                                   ("DOWN", "Down", "")])

    @classmethod
    def poll(cls, context):
        _, _, active = get_atlas()
        return active

    def execute(self, context):
        idx, atlases, _ = get_atlas()

        if self.direction == "UP":
            nextidx = max(idx - 1, 0)
        elif self.direction == "DOWN":
            nextidx = min(idx + 1, len(atlases) - 1)

        atlases.move(idx, nextidx)
        get_prefs().atlasesIDX = nextidx

        return {'FINISHED'}


class Reload(bpy.types.Operator):
    bl_idname = "machin3.reload_atlases"
    bl_label = "MACHIN3: Reload Atlases"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Reload all Atlases. Propagates lock settings.\nSave prefs to complete the process"

    def execute(self, context):
        register_atlases(reloading=True)

        return {'FINISHED'}


class Rename(bpy.types.Operator):
    bl_idname = "machin3.rename_atlas"
    bl_label = "Rename Atlas"
    bl_description = "Rename selected Atlas"

    newname: StringProperty(name="New Name")

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        row = column.split(factor=0.25)
        row.label(text="Old Name:")
        row.label(text=self.active.name)

        row = column.split(factor=0.25)
        row.label(text="New Name:")
        row.prop(self, "newname", text="")

    @classmethod
    def poll(cls, context):
        _, _, active = get_atlas()
        return active and not active.istrimsheet and not active.islocked

    def invoke(self, context, event):
        _, _, self.active = get_atlas()

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        assetspath = get_prefs().assetspath

        oldpath = os.path.join(assetspath, 'Atlases', self.active.name)
        oldname = self.active.name

        newname = self.newname.strip()

        if newname:
            if newname != oldname:
                newpath = os.path.join(assetspath, 'Atlases', newname)

                if not os.path.exists(newpath):
                    os.rename(oldpath, newpath)

                    jsonpath = os.path.join(newpath, 'data.json')

                    if os.path.exists(jsonpath):
                        with open(jsonpath, 'r') as f:
                            data = json.load(f)

                        data['name'] = newname

                        with open(jsonpath, 'w') as f:
                            json.dump(data, f, indent=4)

                        register_atlases(reloading=True)

                    print(" • Renamed atlas %s to %s" % (oldname, newname))

                    self.newname = ""
                else:
                    popup_message("This atlas exists already, choose another name!", title="Failed to rename atlas", icon="ERROR")
            else:
                popup_message("The new name needs to be different from the old one.", title="Failed to rename atlas", icon="ERROR")
        else:
            popup_message("No new name chosen.", title="Failed to rename atlas", icon="ERROR")

        return {'FINISHED'}


class Remove(bpy.types.Operator):
    bl_idname = "machin3.remove_atlas"
    bl_label = "Remove Atlas"
    bl_description = "Remove selected atlas"

    def draw(self, context):
        layout = self.layout

        layout.label(text="This removes the atlas '%s'!" % (self.active.name), icon_value=get_icon("error"))
        layout.label(text="Are you sure? This cannot be undone!")

    @classmethod
    def poll(cls, context):
        _, _, active = get_atlas()
        return active and not active.istrimsheet and not active.islocked

    def invoke(self, context, event):
        self.idx, self.atlases, self.active = get_atlas()

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def execute(self, context):
        assetspath = get_prefs().assetspath

        path = os.path.join(assetspath, 'Atlases', self.active.name)

        if os.path.exists(path):
            rmtree(path)

            get_prefs().atlasesIDX = min([len(self.atlases) - 2, self.idx])

        else:
            popup_message("Have you already removed it manualy, while Blender was running?", title="Atlas '%s' not found" % (self.active.name), icon="ERROR")

        register_atlases(reloading=True)

        return {'FINISHED'}
