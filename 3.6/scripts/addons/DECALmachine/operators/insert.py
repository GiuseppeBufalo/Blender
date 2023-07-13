import bpy
from bpy.props import StringProperty, BoolProperty
import os
import shutil
from .. utils.decal import insert_single_decal, batch_insert_decals, remove_single_decal, remove_decal_from_blend
from .. utils.material import get_atlas_textures, get_trimsheet_textures, get_decalmat, get_decal_textures
from .. utils.registration import get_prefs, reload_instant_decals, update_instantatlascount, update_instanttrimsheetcount
from .. utils.system import save_json, splitpath
from .. utils.ui import popup_message


class Insert(bpy.types.Operator):
    bl_idname = "machin3.insert_decal"
    bl_label = "MACHIN3: Insert Decal"
    bl_description = "Insert Selected Decal\nALT: Batch Insert entire Library"
    bl_options = {'REGISTER', 'UNDO'}

    library: StringProperty()
    decal: StringProperty()

    instant: BoolProperty(default=False)
    trim: BoolProperty(default=False)
    batch: BoolProperty(default=False)

    force_cursor_align: BoolProperty(default=False)

    def invoke(self, context, event):

        if self.batch and event.alt:
            batch_insert_decals(context, self.library, self.decal, trim=self.trim)

        else:
            insert_single_decal(context, self.library, self.decal, instant=self.instant, trim=self.trim, force_cursor_align=self.force_cursor_align)

        return {"FINISHED"}


class QuickInsert(bpy.types.Operator):
    bl_idname = "machin3.quick_insert_decal"
    bl_label = "MACHIN3: Quick Insert Decal"
    bl_description = "Quickly Insert the same Decal as before, directly under the Mouse"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        scene = context.scene
        dm = scene.DM
        wm = context.window_manager

        libraryname = scene.DM.quickinsertlibrary
        decalname = scene.DM.quickinsertdecal
        instant = scene.DM.quickinsertisinstant
        trim = scene.DM.quickinsertistrim

        if libraryname and decalname:
            if dm.align_mode == "RAYCAST":
                wm.decal_mousepos = [event.mouse_region_x, event.mouse_region_y]

            elif dm.align_mode == "CURSOR":
                cursorloc = context.scene.cursor.location.copy()
                context.scene.cursor.rotation_mode = 'QUATERNION'
                cursorrot = context.scene.cursor.rotation_quaternion.copy()

                bpy.ops.view3d.cursor3d('INVOKE_DEFAULT', use_depth=True, orientation='GEOM')

            insert_single_decal(context, libraryname, decalname, instant=instant, trim=trim)

            if dm.align_mode == "CURSOR":
                scene.cursor.location = cursorloc
                scene.cursor.rotation_quaternion = cursorrot

        return {'FINISHED'}


class ClearInstant(bpy.types.Operator):
    bl_idname = "machin3.clear_instant"
    bl_label = "MACHIN3: Clear Instant"
    bl_options = {'REGISTER', 'UNDO'}

    type: StringProperty(name="Instant Type", default='ATLAS')

    @classmethod
    def description(cls, context, properties):
        if properties.type == 'ATLAS':
            return "Clear out Instant Atlas Location, except for the currently selected Atlas"
        elif properties.type == 'TRIMSHEET':
            return "Clear out Instant Trim Sheet Location, except for the currently selected Trim Sheet"

    def execute(self, context):
        assetspath = get_prefs().assetspath
        instantpath = os.path.join(assetspath, 'Create', 'atlasinstant' if self.type == 'ATLAS' else 'triminstant')

        active = context.active_object if context.active_object and (context.active_object.DM.isatlas if self.type == 'ATLAS' else context.active_object.DM.istrimsheet) else None
        ignore = None

        if active:
            if active.DM.isatlas:
                index = active.DM.atlasindex
                uuid = active.DM.atlasuuid
                ignore = "%s_%s" % (index, uuid)

            elif active.DM.istrimsheet:
                index = active.DM.trimsheetindex
                uuid = active.DM.trimsheetuuid
                ignore = "%s_%s" % (index, uuid)

        folders = [f for f in sorted(os.listdir(instantpath)) if os.path.isdir(os.path.join(instantpath, f)) and f != ignore]

        for f in folders:
            path = os.path.join(instantpath, f)
            shutil.rmtree(path)
            print(" ! REMOVED Instant %s:" % ('Atlas' if self.type == 'ATLAS' else 'Trim Sheet'), os.path.basename(path))

        if ignore:
            ignorepath = os.path.join(instantpath, ignore)

            print("\n ! IGNORED Instant %s:" % ('Atlas' if self.type == 'ATLAS' else 'Trim Sheet'), ignore)

            if index != "001":

                basename = "001_%s" % (uuid)

                if os.path.exists(ignorepath):
                    newpath = os.path.join(instantpath, basename)
                    os.rename(ignorepath, newpath)

                    print(" • renamed to:", basename)

                    if active.DM.isatlas:

                        active.DM.atlasindex = "001"

                        dummymat = active.DM.atlasdummymat

                        if dummymat:
                            textures = get_atlas_textures(dummymat)

                            for _, img in textures.items():
                                img.filepath = os.path.join(newpath, os.path.basename(img.filepath))

                        sources = active.DM.get('sources')

                        if sources:
                            for uuid, decal in sources.items():
                                for textype, path in decal['textures'].items():
                                    sources[uuid]['textures'][textype] = path.replace(ignorepath, newpath)

                            save_json(sources.to_dict(), os.path.join(newpath, 'sources', 'sources.json'))

                            popup_message('The selected Atlas was changed, please save your .blend file now!', title="Please save the .blend")


                    elif active.DM.istrimsheet:

                        active.DM.trimsheetindex = "001"

                        sheetmat = active.active_material if active.active_material.DM.istrimsheetmat else None

                        if sheetmat:
                            textures = get_trimsheet_textures(sheetmat)

                            for _, img in textures.items():
                                img.filepath = os.path.join(newpath, os.path.basename(img.filepath))

                        col = active.DM.trimcollection

                        if col:
                            for obj in col.objects:
                                mat = get_decalmat(obj)

                                if mat:
                                    textures = get_decal_textures(mat)

                                    for _, img in textures.items():
                                        decalname = splitpath(img.filepath)[-2]
                                        img.filepath = os.path.join(newpath, decalname, os.path.basename(img.filepath))

        if self.type == 'ATLAS':
            update_instantatlascount()

        elif self.type == 'TRIMSHEET':
            update_instanttrimsheetcount()

        return {'FINISHED'}


class Remove(bpy.types.Operator):
    bl_idname = "machin3.remove_decal"
    bl_label = "MACHIN3: Remove Decal"
    bl_description = "Remove Selected Decal"

    library: StringProperty()
    decal: StringProperty()

    instant: BoolProperty(default=False)
    trim: BoolProperty(default=False)

    def execute(self, context):
        if self.decal and self.library:
            print(" ! REMOVING Decal:", self.library, self.decal)
            remove_single_decal(context, self.library, self.decal, instant=self.instant, trim=self.trim)

        return {'FINISHED'}


class RemoveAllInstantDecals(bpy.types.Operator):
    bl_idname = "machin3.remove_all_instant_decals"
    bl_label = "MACHIN3: Remove All Instant Decals"
    bl_description = "Remove all Instant Decals from the hard drive"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_prefs().decalremovemode

    def execute(self, context):
        assetspath = get_prefs().assetspath
        librarypath = os.path.join(assetspath, "Create", "decalinstant")

        folders = [f for f in sorted(os.listdir(librarypath)) if os.path.isdir(os.path.join(librarypath, f))]

        if folders:
            for decal in folders:
                print(" ! REMOVING Instant Decals:", decal)

                decalpath = os.path.join(librarypath, decal)
                uuidpath = os.path.join(decalpath, "uuid")

                if os.path.exists(uuidpath):
                    with open(uuidpath, "r") as f:
                        uuid = f.read()

                    remove_decal_from_blend(uuid)

                shutil.rmtree(decalpath)

            reload_instant_decals(default=None)

            get_prefs().decalremovemode = False
        return {'FINISHED'}
