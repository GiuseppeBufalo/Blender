import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
import os
from uuid import uuid4
from .. utils.decal import clear_decalobj_props, remove_decal_orphans, get_decal_library_and_name_from_uuid, set_props_and_node_names_of_decal, set_decalobj_props_from_material
from .. utils.trim import get_sheetpath_from_uuid
from .. utils.atlas import get_atlaspath_from_uuid
from .. utils.ui import popup_message
from .. utils.object import unlock, unparent
from .. utils.registration import get_prefs, get_version_from_blender, get_version_as_float
from .. utils.system import splitpath
from .. utils.material import get_decalmat, get_decal_textures, get_parallaxgroup_from_decalmat, get_heightgroup_from_parallaxgroup, get_decalgroup_from_decalmat, set_node_names_of_trimsheet_material, set_node_names_of_atlas_material
from .. utils.ui import get_icon
from .. items import decaltype_items
from .. registration import keys as keysdict
from .. import bl_info


class RemoveOrphans(bpy.types.Operator):
    bl_idname = "machin3.remove_decal_orphans"
    bl_label = "MACHIN3: Remove Decal Orphans"
    bl_description = "Remove Decal Orphans"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        backup_count, joined_count, decal_count = remove_decal_orphans(debug=True)

        msg = ["Removed decal orphans:"]

        if backup_count:
            msg.append(" • %d orphan backups" % (backup_count))

        if joined_count:
            msg.append(" • %d orphan joined" % (joined_count))

        if decal_count:
            msg.append(" • %d orphan decals" % (decal_count))

        dg = context.evaluated_depsgraph_get()

        material_orphans = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.users == 0]

        if material_orphans:
            for idx, mat in enumerate(material_orphans):
                bpy.data.materials.remove(mat, do_unlink=True)

            msg.append(" • %d orphan materials" % (idx + 1))

        dg.update()

        image_orphans = [img for img in bpy.data.images if img.DM.isdecaltex and img.users == 0]

        if image_orphans:
            for idx, img in enumerate(image_orphans):
                bpy.data.images.remove(img, do_unlink=True)

            msg.append(" • %d orphan textures" % (idx + 1))

        if len(msg) > 1:
            popup_message(msg)

        bpy.ops.outliner.orphans_purge(do_recursive=True)

        return {'FINISHED'}


class FixTexturePaths(bpy.types.Operator):
    bl_idname = "machin3.fix_decal_texture_paths"
    bl_label = "MACHIN3: Fix Decal Texture Paths"
    bl_description = "Fix Decal, Trim Sheet and Atlas Texture Paths\nALT: Force rebuilding paths completely from decal UUIDs\nCTRL: Rebuild paths of locally unpacked textures too"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return [img for img in bpy.data.images if img.DM.isdecaltex or img.DM.istrimsheettex or img.DM.istrimdecaltex]

    def invoke(self, context, event):
        assetspath = get_prefs().assetspath

        if event.ctrl:
            textures = [img for img in bpy.data.images if (img.DM.isdecaltex or img.DM.istrimdecaltex or img.DM.istrimsheettex or img.DM.isatlasdummytex or img.DM.isatlastex) and not img.packed_file]
        else:
            textures = [img for img in bpy.data.images if (img.DM.isdecaltex or img.DM.istrimdecaltex or img.DM.istrimsheettex or img.DM.isatlasdummytex or img.DM.isatlastex) and not img.packed_file and not img.filepath.startswith('//textures')]

        fix = []
        decal_rebuilt = []
        sheet_rebuilt = []
        atlas_rebuilt = []

        for img in textures:
            split = splitpath(img.filepath)

            if 'Create' in split and any(s in split for s in ['instant', 'decalinstant', 'triminstant', 'atlasinstant']):
                if img.DM.istrimsheettex:
                    newpath = os.path.join(assetspath, 'Create', 'triminstant', *split[-2:])

                elif img.DM.istrimdecaltex:
                    newpath = os.path.join(assetspath, 'Create', 'triminstant', *split[-3:])

                elif img.DM.isatlasdummytex:
                    newpath = os.path.join(assetspath, 'Create', 'atlasinstant', *split[-2:])

                elif img.DM.isdecaltex:
                    newpath = os.path.join(assetspath, 'Create', 'decalinstant', *split[-2:])


            else:
                if img.DM.istrimsheettex:
                    newpath = os.path.join(assetspath, 'Trims', *split[-2:])

                elif img.DM.istrimdecaltex:
                    newpath = os.path.join(assetspath, 'Trims', *split[-3:])

                elif img.DM.isatlastex:
                    newpath = os.path.join(assetspath, 'Atlases', *split[-2:])

                elif img.DM.isdecaltex:
                    newpath = os.path.join(assetspath, 'Decals', *split[-3:])

            textype = 'TRIMSHEET' if img.DM.istrimsheettex else 'TRIMDECAL' if img.DM.istrimdecaltex else 'ATLASDUMMY' if img.DM.isatlasdummytex else 'ATLAS' if img.DM.isatlastex else 'DECAL' if img.DM.isdecaltex else 'NONE'
            fix.append((img, textype, img.filepath, newpath))


        for img, textype, oldpath, newpath in sorted(fix, key=lambda x: (x[1], x[0].DM.decallibrary, x[0].DM.decalname, x[0].name)):

            if event.alt:
                if img.DM.isdecaltex:
                    wasrebuilt = self.rebuild_path_from_decal_uuid(context, assetspath, oldpath, img, textype, rebuildtype='Forced')

                    if wasrebuilt:
                        if isinstance(wasrebuilt, bpy.types.Image):
                            decal_rebuilt.append(wasrebuilt)
                        continue

                elif img.DM.istrimsheettex:
                    wasrebuilt = self.rebuild_path_from_sheet_uuid(oldpath, img, rebuildtype='Forced')

                    if isinstance(wasrebuilt, bpy.types.Image):
                        sheet_rebuilt.append(wasrebuilt)
                        continue

                elif img.DM.isatlastex:
                    wasrebuilt = self.rebuild_path_from_atlas_uuid(oldpath, img, rebuildtype='Forced')

                    if isinstance(wasrebuilt, bpy.types.Image):
                        atlas_rebuilt.append(wasrebuilt)
                        continue

            if oldpath != newpath and os.path.exists(newpath):
                print()
                print("INFO: Fixing %s %s" % (textype, img.name))
                print(" old path:", oldpath)
                print(" new path:", newpath)

                img.filepath = newpath

            elif not os.path.exists(newpath):
                print()
                print("WARNING: image does not exists: %s" % (newpath))

                if img.DM.isdecaltex:
                    wasrebuilt = self.rebuild_path_from_decal_uuid(context, assetspath, oldpath, img, textype, rebuildtype='Fallback')

                    if wasrebuilt:
                        if isinstance(wasrebuilt, bpy.types.Image):
                            decal_rebuilt.append(wasrebuilt)
                        continue

                    else:
                        print("WARNING: Failed rebuilding path from decal UUID")

                    print("\nINFO: Attempting to reconstruct path using decalname and decallibrary props")

                    name = img.DM.decalname
                    library = img.DM.decallibrary

                    reconstructedpath = os.path.join(assetspath, 'Trims' if img.DM.istrimdecaltex else 'Decals', library, name.replace(library + '_', ''), os.path.basename(img.filepath))
                    print("reconstructed path:", reconstructedpath)

                    if os.path.exists(reconstructedpath):
                        img.filepath = reconstructedpath

                    else:
                        print("WARNING: reconstructed path does not exists either: %s" % (reconstructedpath))

                elif img.DM.istrimsheettex:
                    wasrebuilt = self.rebuild_path_from_sheet_uuid(oldpath, img, rebuildtype='Fallback')

                    if wasrebuilt:
                        if isinstance(wasrebuilt, bpy.types.Image):
                            sheet_rebuilt.append(wasrebuilt)
                        continue


                elif img.DM.isatlastex:
                    wasrebuilt = self.rebuild_path_from_atlas_uuid(oldpath, img, rebuildtype='Fallback')

                    if wasrebuilt:
                        if isinstance(wasrebuilt, bpy.types.Image):
                            atlas_rebuilt.append(wasrebuilt)
                        continue


        if decal_rebuilt:
            decals = [obj for obj in bpy.data.objects if obj.DM.isdecal]

            decalmats = {}

            for obj in decals:
                decalmat = get_decalmat(obj)

                textures = get_decal_textures(decalmat)

                if all([img in decal_rebuilt for img in textures.values()]):
                    split = splitpath(list(textures.values())[0].filepath)

                    library = split[-3]
                    name = split[-2]

                    if decalmat in decalmats:
                        decalmats[decalmat]['decalobjs'].append(obj)

                    else:
                        decalmats[decalmat] = {'decalobjs': [obj],
                                               'textures': list(textures.values()),
                                               'library': library,
                                               'name': name}

            for mat, decals in decalmats.items():
                decalobjs = decals['decalobjs']
                textures = decals['textures']
                library = decals['library']
                name = decals['name']
                olddecalname = mat.DM.decalname

                set_props_and_node_names_of_decal(library, name, decalmat=mat, decaltextures=textures)

                for obj in decalobjs:
                    set_decalobj_props_from_material(obj, mat)
                    obj.name = obj.name.replace(olddecalname, mat.DM.decalname)

        if sheet_rebuilt:
            sheetuuids = {}

            for img in sheet_rebuilt:
                sheetname = splitpath(img.filepath)[-2]

                img.DM.trimsheetname = sheetname

                if img.DM.trimsheetuuid not in sheetuuids:
                    sheetuuids[img.DM.trimsheetuuid] = sheetname

            sheetobjmats = {obj.active_material for obj in bpy.data.objects if obj.DM.istrimsheet if obj.active_material and obj.active_material.DM.istrimsheetmat}
            sheetmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat and mat.DM.trimsheetuuid in sheetuuids and mat not in sheetobjmats]

            for mat in sheetmats:
                oldname = mat.DM.trimsheetname
                sheetname = sheetuuids[mat.DM.trimsheetuuid]

                set_node_names_of_trimsheet_material(mat, sheetname)

                mat.DM.trimsheetname = sheetname

                mat.name = mat.name.replace(oldname, sheetname)

        if atlas_rebuilt:

            atlasuuids = {}

            for img in atlas_rebuilt:
                atlasname = splitpath(img.filepath)[-2]

                img.DM.trimsheetname = atlasname

                if img.DM.atlasuuid not in atlasuuids:
                    atlasuuids[img.DM.atlasuuid] = atlasname

            atlasmats = [mat for mat in bpy.data.materials if mat.DM.isatlasmat and mat.DM.atlasuuid in atlasuuids]

            for mat in atlasmats:
                oldname = mat.DM.atlasname
                atlasname = atlasuuids[mat.DM.atlasuuid]

                set_node_names_of_atlas_material(mat, atlasname)

                mat.DM.atlasname = atlasname

                mat.name = mat.name.replace(oldname, atlasname)


        return {'FINISHED'}

    def rebuild_path_from_atlas_uuid(self, oldpath, img, rebuildtype='Forced'):
        atlasuuid = img.DM.atlasuuid
        atlaspath = get_atlaspath_from_uuid(atlasuuid)

        if atlaspath:
            rebuiltpath = os.path.join(atlaspath, os.path.basename(img.filepath))

            if rebuiltpath != oldpath and os.path.exists(rebuiltpath):
                print()
                print("INFO: %s path rebuilding from atlas UUID" % (rebuildtype))
                print(" old path:", oldpath)
                print(" new path:", rebuiltpath)

                img.filepath = rebuiltpath

                if img.DM.atlasname != os.path.basename(atlaspath):
                    return img
                return True

    def rebuild_path_from_sheet_uuid(self, oldpath, img, rebuildtype='Forced'):
        trimsheetuuid = img.DM.trimsheetuuid
        sheetpath = get_sheetpath_from_uuid(trimsheetuuid)

        if sheetpath:
            rebuiltpath = os.path.join(sheetpath, os.path.basename(img.filepath))

            if rebuiltpath != oldpath and os.path.exists(rebuiltpath):
                print()
                print("INFO: %s path rebuilding from trim sheet UUID" % (rebuildtype))
                print(" old path:", oldpath)
                print(" new path:", rebuiltpath)

                img.filepath = rebuiltpath

                if img.DM.trimsheetname != os.path.basename(sheetpath):
                    return img
                return True

    def rebuild_path_from_decal_uuid(self, context, assetspath, oldpath, img, textype, rebuildtype='Forced'):
        name, library, libtype = get_decal_library_and_name_from_uuid(context, img.DM.uuid)

        if (textype == 'DECAL' and libtype == 'Decals') or (textype == 'TRIMDECAL' and libtype == 'Trims'):
            rebuiltpath = os.path.join(assetspath, libtype, library, name, os.path.basename(img.filepath))

            if rebuiltpath != oldpath and os.path.exists(rebuiltpath):
                print()
                print("INFO: %s path rebuilding from decal UUID" % (rebuildtype))
                print(" old path:", oldpath)
                print(" new path:", rebuiltpath)

                img.filepath = rebuiltpath

                if img.DM.decallibrary != library or img.DM.decalname != name:
                    return img
                return True


class Validate(bpy.types.Operator):
    bl_idname = "machin3.validate_decal"
    bl_label = "MACHIN3: Validate Decal"
    bl_description = "Validate Decal, useful for debugging Decals and at times for Decal Creation"

    fixmissingtextures: BoolProperty(name="Fix missing Textures", default=False)

    generateuuid: BoolProperty(name="Generate new UUID", default=False)
    disableforceduuid: BoolProperty(name="Disable forced UUID", default=False)

    setdecaltype: BoolProperty(name="Set new decaltype", default=False)
    decaltype: EnumProperty(name="Decal Type", items=reversed(decaltype_items))

    setdecallibrary: BoolProperty(name="Set new decallibrary", default=False)
    decallibrary: StringProperty(name="Library")

    setdecalname: BoolProperty(name="Set new decalname", default=False)
    decalname: StringProperty(name="Name")

    setdecalmatname: BoolProperty(name="Set new decalmatname", default=False)
    decalmatname: StringProperty(name="Material Name")

    setdecalcreator: BoolProperty(name="Set new creator", default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout



        if any([self.invalid, self.legacy, self.future]):

            box = layout.box()
            column = box.column()

            if self.invalid:
                column.label(text="This object is not a valid DECALmachine Decal!", icon_value=get_icon("error"))

            elif self.legacy:
                column.label(text="This is a Legacy Decal, and needs to be updated. Use the 'Update Decals & Trim Sheets' panel to do so.", icon_value=get_icon("info"))

            elif self.future:
                column.label(text="This is a Future Decal created in a newer version of DECALmachine or Blender, and can't be used in your current setup.", icon_value=get_icon("error"))



        box = layout.box()
        column = box.column()

        column.label(text="Basics")

        text, icon = (self.decal.name, "save") if self.decal else ("None", "error")
        column.label(text="Decal Object: %s" % (text), icon_value=get_icon(icon))

        text, icon = (self.decalmat.name, "save") if self.decalmat else ("None", "error")
        column.label(text="Decal Material: %s" % (text), icon_value=get_icon(icon))


        if self.decaltextures:
            text, icon = ("", "save") if self.hasrequiredtextures else ("missing required textures", "error")
            column.label(text="Decal Textures: %s" % (text), icon_value=get_icon(icon))
            for textype, img in sorted(self.decaltextures.items()):
                column.label(text="  • %s: %s" % (textype, img.name), icon="BLANK1")

        else:
            column.label(text="Decal Textures: None", icon_value=get_icon("error"))



        if all([self.decal, self.decalmat, self.decaltextures]):
            box = layout.box()

            column = box.column()
            column.label(text="Common Properties")

            if self.uuids and self.uuids_unique and self.uuids_complete:
                column.label(text="UUID: %s" %(self.uuids[0]), icon_value=get_icon("save"))
            else:
                row = column.row()
                row.label(text="UUID:", icon="BLANK1")
                row.label(text="present: %s" % (True if self.uuids else False), icon_value=get_icon("save") if self.uuids else get_icon("error"))
                row.label(text="unique: %s" % (self.uuids_unique), icon_value=get_icon("save") if self.uuids_unique else get_icon("error"))
                row.label(text="complete: %s" % (self.uuids_complete), icon_value=get_icon("save") if self.uuids_complete else get_icon("error"))

            if self.trimsheetuuids:
                if self.trimsheetuuids_unique and self.trimsheetuuids_complete:
                    column.label(text="trimsheet UUID: %s" %(self.trimsheetuuids[0]), icon_value=get_icon("save"))
                else:
                    row = column.row()
                    row.label(text="trimsheet UUID:", icon="BLANK1")
                    row.label(text="present: %s" % (True), icon_value=get_icon("save"))
                    row.label(text="unique: %s" % (self.trimsheetuuids_unique), icon_value=get_icon("save") if self.trimsheetuuids_unique else get_icon("error"))
                    row.label(text="complete: %s" % (self.trimsheetuuids_complete), icon_value=get_icon("save") if self.trimsheetuuids_complete else get_icon("error"))

            if self.versions and self.versions_unique and self.versions_complete:
                if self.legacy or self.future:
                    column.label(text="Version: %s, Expected: %s" %(self.versions[0], self.supported_version), icon_value=get_icon("error"))
                else:
                    column.label(text="Version: %s" %(self.versions[0]), icon_value=get_icon("save"))

            else:
                row = column.row()
                row.label(text="version:", icon="BLANK1")
                row.label(text="present: %s" % (True if self.versions else False), icon_value=get_icon("save") if self.versions else get_icon("error"))
                row.label(text="unique: %s" % (self.versions_unique), icon_value=get_icon("save") if self.versions_unique else get_icon("error"))
                row.label(text="complete: %s" % (self.versions_complete), icon_value=get_icon("save") if self.versions_complete else get_icon("error"))

            if self.decaltypes and self.decaltypes_unique and self.decaltypes_complete:
                column.label(text="decaltype: %s" %(self.decaltypes[0]), icon_value=get_icon("save"))
            else:
                row = column.row()
                row.label(text="decaltype:", icon="BLANK1")
                row.label(text="present: %s" % (True if self.decaltypes else False), icon_value=get_icon("save") if self.decaltypes else get_icon("error"))
                row.label(text="unique: %s" % (self.decaltypes_unique), icon_value=get_icon("save") if self.decaltypes_unique else get_icon("error"))
                row.label(text="complete: %s" % (self.decaltypes_complete), icon_value=get_icon("save") if self.decaltypes_complete else get_icon("error"))

            if self.decallibraries and self.decallibraries_unique and self.decallibraries_complete:
                column.label(text="decallibrary: %s" %(self.decallibraries[0]), icon_value=get_icon("save"))
            else:
                row = column.row()
                row.label(text="decallibrary:", icon="BLANK1")
                row.label(text="present: %s" % (True if self.decallibraries else False), icon_value=get_icon("save") if self.decallibraries else get_icon("error"))
                row.label(text="unique: %s" % (self.decallibraries_unique), icon_value=get_icon("save") if self.decallibraries_unique else get_icon("error"))
                row.label(text="complete: %s" % (self.decallibraries_complete), icon_value=get_icon("save") if self.decallibraries_complete else get_icon("error"))


            if self.decalnames and self.decalnames_unique and self.decalnames_complete:
                column.label(text="decalname: %s" %(self.decalnames[0]), icon_value=get_icon("save"))
            else:
                row = column.row()
                row.label(text="decalname:", icon="BLANK1")
                row.label(text="present: %s" % (True if self.decalnames else False), icon_value=get_icon("save") if self.decalnames else get_icon("error"))
                row.label(text="unique: %s" % (self.decalnames_unique), icon_value=get_icon("save") if self.decalnames_unique else get_icon("error"))
                row.label(text="complete: %s" % (self.decalnames_complete), icon_value=get_icon("save") if self.decalnames_complete else get_icon("error"))


            if self.decalmatnames and self.decalmatnames_unique and self.decalmatnames_complete:
                column.label(text="decalmatname: %s" %(self.decalmatnames[0]), icon_value=get_icon("save"))
            else:
                row = column.row()
                row.label(text="decalmatname:", icon="BLANK1")
                row.label(text="present: %s" % (True if self.decalmatnames else False), icon_value=get_icon("save") if self.decalmatnames else get_icon("error"))
                row.label(text="unique: %s" % (self.decalmatnames_unique), icon_value=get_icon("save") if self.decalmatnames_unique else get_icon("error"))
                row.label(text="complete: %s" % (self.decalmatnames_complete), icon_value=get_icon("save") if self.decalmatnames_complete else get_icon("error"))


            if self.creators and self.creators_unique and self.creators_complete:
                column.label(text="creator: %s" %(self.creators[0]), icon_value=get_icon("save"))
            else:
                row = column.row()
                row.label(text="creator:", icon="BLANK1")
                row.label(text="present: %s" % (True if self.creators else False), icon_value=get_icon("save") if self.creators else get_icon("info"))
                row.label(text="unique: %s" % (self.creators_unique), icon_value=get_icon("save") if self.creators_unique else get_icon("info"))
                row.label(text="complete: %s" % (self.creators_complete), icon_value=get_icon("save") if self.creators_complete else get_icon("info"))



        if self.decal and self.decalmat:
            split = layout.split(factor=0.4)
        else:
            split = layout

        if self.decal:
            box = split.box()

            column = box.column()
            column.label(text="Object Properties")

            column.label(text="  • isbackup: %s" % (self.decal.DM.isbackup))
            backup = self.decal.DM.decalbackup
            column.label(text="  • decalbackup: %s" % (backup.name if backup else backup))

            column.label(text="  • isprojected: %s" % (self.decal.DM.isprojected))
            if self.decal.DM.isprojected:
                projectedon = self.decal.DM.projectedon
                column.label(text="    • projectedon: %s" % (projectedon.name if projectedon else projectedon))

            column.label(text="  • issliced: %s" % (self.decal.DM.issliced))
            if self.decal.DM.issliced:
                slicedon = self.decal.DM.slicedon
                column.label(text="    • slicedon: %s" % (slicedon.name if slicedon else slicedon))

            column.label(text=f"  • istrimdecal: {self.decal.DM.istrimdecal}")
            column.label(text=f"  • forced UUID: {self.decal.DM.is_forced_uuid}")

        if self.decalmat:
            box = split.box()

            column = box.column()
            column.label(text="Material Properties")

            column.label(text="  • ismatched: %s" % (self.decalmat.DM.ismatched))
            if self.decalmat.DM.ismatched:
                matchedmaterialto = self.decalmat.DM.matchedmaterialto
                matchedmaterial2to = self.decalmat.DM.matchedmaterial2to
                matchedsubsetto = self.decalmat.DM.matchedsubsetto

                column.label(text="    • material: %s" % (matchedmaterialto.name if matchedmaterialto else matchedmaterialto))
                column.label(text="    • material2: %s" % (matchedmaterial2to.name if matchedmaterial2to else matchedmaterial2to))
                column.label(text="    • subset: %s" % (matchedsubsetto.name if matchedsubsetto else matchedsubsetto))

            column.label(text="  • isparallaxed: %s" % (self.decalmat.DM.isparallaxed))
            column.label(text="  • parallaxnodename: %s" % (self.decalmat.DM.parallaxnodename if self.decalmat.DM.parallaxnodename else "None"))

            if self.decalmat.DM.parallaxnodename:
                if self.pgroup and self.nameinsync:
                    text = "True"
                elif self.pgroup:
                    text = "True, but name differs"
                else:
                    text = "False"
                column.label(text="  • parallax group: %s" % (text))

                if self.pgroup:
                    column.label(text="    • height group texture: %s" % (True if self.heighttex else False))

            column.label(text="  • istrimdecalmat: %s" % (self.decalmat.DM.istrimdecalmat))



        if not self.legacy:
            box = layout.box()

            column = box.column()
            column.label(text="Actions")


            if self.decal and self.decalmat and self.decaltextures and not self.fixmissingtextures:
                row = column.row()
                row.prop(self, "generateuuid")

                if self.generateuuid and self.decal.DM.is_forced_uuid:
                    row.prop(self, "disableforceduuid")

                row = column.row()
                row.prop(self, "setdecalcreator")
                if self.setdecalcreator:
                    row.label(text="Creator: %s" % get_prefs().decalcreator)

    def invoke(self, context, event):
        active = context.active_object
        self.decal, self.decalmat, self.decaltextures = self.get_basics(active)
        self.isasset = False
        self.istemplate = False
        self.fixmissingtextures = False

        self.legacy = False
        self.future = False
        self.invalid = False
        self.supported_version = get_version_from_blender()

        if all([self.decal, self.decalmat, self.decaltextures]):
            self.uuids, self.trimsheetuuids, self.versions, self.decaltypes, self.decallibraries, self.decalnames, self.decalmatnames, self.creators, count = self.get_sync()

            print(20 * "-")
            print("PROPERTY UNIQUENESS")

            self.uuids_unique = len(set(self.uuids)) == 1
            self.trimsheetuuids_unique = len(set(self.trimsheetuuids)) == 1
            self.versions_unique = len(set(self.versions)) == 1
            self.decaltypes_unique = len(set(self.decaltypes)) == 1
            self.decallibraries_unique = len(set(self.decallibraries)) == 1
            self.decalnames_unique = len(set(self.decalnames)) == 1
            self.decalmatnames_unique = len(set(self.decalmatnames)) == 1
            self.creators_unique = len(set(self.creators)) == 1

            print(" • unique UUIDs:", self.uuids_unique)
            print(" • unique trimsheet UUIDs:", self.trimsheetuuids_unique)
            print(" • unique versions:", self.versions_unique)
            print(" • unique decaltypes:", self.decaltypes_unique)
            print(" • unique decallibraries:", self.decallibraries_unique)
            print(" • unique decalnames:", self.decalnames_unique)
            print(" • unique decalmatnames:", self.decalmatnames_unique)
            print(" • unique creators:", self.creators_unique)


            print(20 * "-")
            print("PROPERTY SYNCHRONIZATION")

            self.uuids_complete = len(self.uuids) == count
            self.trimsheetuuids_complete = len(self.trimsheetuuids) == count
            self.versions_complete = len(self.versions) == count
            self.decaltypes_complete = len(self.decaltypes) == count
            self.decallibraries_complete = len(self.decallibraries) == count
            self.decalnames_complete = len(self.decalnames) == count
            self.decalmatnames_complete = len(self.decalmatnames) == count
            self.creators_complete = len(self.creators) == count

            print(" • complete UUIDs:", self.uuids_complete)
            print(" • complete trimsheet UUIDs:", self.trimsheetuuids_complete)
            print(" • complete versions:", self.versions_complete)
            print(" • complete decaltypes:", self.decaltypes_complete)
            print(" • complete decallibraries:", self.decallibraries_complete)
            print(" • complete decalnames:", self.decalnames_complete)
            print(" • complete decalmaterialnames:", self.decalmatnames_complete)
            print(" • complete decalcreators:", self.creators_complete)

            if self.decalmat.DM.version and get_version_as_float(self.decalmat.DM.version) < get_version_as_float(self.supported_version):
                self.legacy = True

            elif self.decalmat.DM.version and get_version_as_float(self.decalmat.DM.version) > get_version_as_float(self.supported_version):
                self.future = True


            self.generateuuid = False

            self.setdecaltype = False
            self.decaltype = self.decal.DM.decaltype

            self.setdecallibrary = False
            self.setdecalname = False
            self.setdecalmatname = False

            currentblend = bpy.data.filepath
            if get_prefs().assetspath in currentblend:
                self.isasset = True

                decalpath = os.path.dirname(currentblend)
                basename = os.path.basename(decalpath)
                library = os.path.basename(os.path.dirname(decalpath))
                decalmatname = "%s_%s" % (library, basename)
                decalname = decalmatname

                self.decallibrary = library
                self.decalname = decalname
                self.decalmatname = decalmatname

            elif any(t in currentblend for t in ['Templates_2.93.blend', 'Templates_3.0.blend']):
                self.isasset = True
                self.istemplate = True

                basename = self.decaltype
                library = "TEMPLATE"
                decalmatname = "%s_%s" % (library, basename)
                decalname = decalmatname

                self.decallibrary = library
                self.decalname = decalname
                self.decalmatname = decalmatname

            else:
                self.decallibrary = self.decal.DM.decallibrary if self.decal.DM.decallibrary else self.decallibraries[0] if self.decallibraries else ""
                self.decalname = self.decal.DM.decalname if self.decal.DM.decalname else self.decalnames[0] if self.decalnames else ""
                self.decalmatname = self.decal.DM.decalmatname if self.decal.DM.decalmatname else self.decalmatnames[0] if self.decalmatnames else ""

            self.setdecalcreator = False

        else:
            self.invalid = True

        width = 650 if any([self.legacy, self.future]) else 500 if self.decal and self.decalmat else 300

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=width)

    def execute(self, context):


        if self.decal and self.decalmat and self.decaltextures:
            if self.istemplate:
                uuid = ""
            else:
                uuid = str(uuid4())

            if self.generateuuid and self.isasset and not self.istemplate:
                currentblend = bpy.data.filepath

                decalpath = os.path.dirname(currentblend)
                uuidpath = os.path.join(decalpath, "uuid")

                with open(uuidpath, "w") as f:
                    f.write(uuid)

            if self.generateuuid and self.disableforceduuid:
                self.decal.DM.is_forced_uuid = False

            for component in [self.decal] + [self.decalmat] + list(self.decaltextures.values()):

                if self.generateuuid:
                    component.DM.uuid = uuid

                if self.setdecalcreator:
                    component.DM.creator = "" if self.istemplate else get_prefs().decalcreator


        return {'FINISHED'}

    def get_sync(self):
        uuids = []
        trimsheetuuids = []
        versions = []
        decaltypes = []
        decallibraries = []
        decalnames = []
        decalmatnames = []
        creators = []


        if self.decal.DM.uuid:
            uuids.append(self.decal.DM.uuid)

        if self.decal.DM.trimsheetuuid:
            trimsheetuuids.append(self.decal.DM.trimsheetuuid)

        if self.decal.DM.version:
            versions.append(self.decal.DM.version)

        if self.decal.DM.decaltype:
            decaltypes.append(self.decal.DM.decaltype)

        if self.decal.DM.decallibrary:
            decallibraries.append(self.decal.DM.decallibrary)

        if self.decal.DM.decalname:
            decalnames.append(self.decal.DM.decalname)

        if self.decal.DM.decalmatname:
            decalmatnames.append(self.decal.DM.decalmatname)

        if self.decal.DM.creator:
            creators.append(self.decal.DM.creator)



        if self.decalmat.DM.uuid:
            uuids.append(self.decalmat.DM.uuid)

        if self.decalmat.DM.trimsheetuuid:
            trimsheetuuids.append(self.decalmat.DM.trimsheetuuid)

        if self.decalmat.DM.version:
            versions.append(self.decalmat.DM.version)

        if self.decalmat.DM.decaltype:
            decaltypes.append(self.decalmat.DM.decaltype)

        if self.decalmat.DM.decallibrary:
            decallibraries.append(self.decalmat.DM.decallibrary)

        if self.decalmat.DM.decalname:
            decalnames.append(self.decalmat.DM.decalname)

        if self.decalmat.DM.decalmatname:
            decalmatnames.append(self.decalmat.DM.decalmatname)

        if self.decalmat.DM.creator:
            creators.append(self.decalmat.DM.creator)


        count = 2
        for img in self.decaltextures.values():
            count += 1

            if img.DM.uuid:
                uuids.append(img.DM.uuid)

            if img.DM.trimsheetuuid:
                trimsheetuuids.append(img.DM.trimsheetuuid)

            if img.DM.version:
                versions.append(img.DM.version)

            if img.DM.decaltype != "NONE":
                decaltypes.append(img.DM.decaltype)

            if img.DM.decallibrary:
                decallibraries.append(img.DM.decallibrary)

            if img.DM.decalname:
                decalnames.append(img.DM.decalname)

            if img.DM.decalmatname:
                decalmatnames.append(img.DM.decalmatname)

            if img.DM.creator:
                creators.append(img.DM.creator)

        return uuids, trimsheetuuids, versions, decaltypes, decallibraries, decalnames, decalmatnames, creators, count

    def get_basics(self, active):
        decal = active if active.DM.isdecal else None
        decalmat = get_decalmat(active)
        decaltextures = get_decal_textures(decalmat) if decalmat else None

        print(20 * "-")
        print("DECAL BASICS")

        print(" • decal object:", decal)
        print(" • decal material:", decalmat)
        print(" • decal textures:", decaltextures)

        if decal:
            print(20 * "-")
            print("OBJECT PROPERTIES")

            print(" • isbackup:", decal.DM.isbackup)
            print(" • decalbackup:", decal.DM.decalbackup)

            print(" • isprojected:", decal.DM.isprojected)
            if decal.DM.isprojected:
                print("  • projectedon:", decal.DM.projectedon)

            print(" • issliced:", decal.DM.issliced)
            if decal.DM.issliced:
                print("  • slidedon:", decal.DM.slicedon)

            print(" • issliced:", decal.DM.issliced)
            print(" • istrimdecal:", decal.DM.istrimdecal)
            print(" • is_forced_uuid:", decal.DM.is_forced_uuid)

        if decalmat:
            print(20 * "-")
            print("MATERIAL PROPERTIES")

            if decaltextures:
                print(" • decaltype:", decalmat.DM.decaltype)
                self.hasrequiredtextures = self.has_required_textures(decalmat.DM.decaltype, decaltextures)
                print("  • has all required textures:", self.hasrequiredtextures)

            print(" • ismatched:", decalmat.DM.ismatched)
            if decalmat.DM.ismatched:
                print("  • matchedmaterialto:", decalmat.DM.matchedmaterialto)
                print("  • matchedmaterial2to:", decalmat.DM.matchedmaterial2to)
                print("  • matchedsubsetto:", decalmat.DM.matchedsubsetto)

            print(" • isparallaxed:", decalmat.DM.isparallaxed)
            print(" • parallaxnodename:", decalmat.DM.parallaxnodename)

            if decalmat.DM.parallaxnodename:
                self.pgroup, self.nameinsync = self.has_prallax_group(decalmat)

                if self.pgroup and self.nameinsync:
                    print("  • parallax group:", True)
                elif self.pgroup:
                    print("  • parallax group:", True, ", but name differs")
                else:
                    print("  • parallax group:", False)

                if self.pgroup:
                    self.heighttex = self.has_functional_height_group(self.pgroup)
                    print("    • height group texture:", True if self.heighttex else False)

            print(" • istrimdecalmat:", decalmat.DM.istrimdecalmat)

        return decal, decalmat, decaltextures

    def has_functional_height_group(self, pgroup):
        hgroup = get_heightgroup_from_parallaxgroup(pgroup)

        if hgroup:
            for node in hgroup.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    return node.image

    def has_prallax_group(self, decalmat):
        pgroup = get_parallaxgroup_from_decalmat(decalmat)

        if pgroup:
            if pgroup.name == decalmat.DM.parallaxnodename:
                return pgroup, True
            else:
                return pgroup, False
        else:
            return False, False

    def has_required_textures(self, decaltype, decaltextures):
        aocurvheight = "AO_CURV_HEIGHT" in decaltextures
        normal = "NORMAL" in decaltextures
        masks = "MASKS" in decaltextures
        color = "COLOR" in decaltextures
        emission = "EMISSION" in decaltextures

        pattern = (aocurvheight, normal, masks, color, emission)

        requiredtextures = False

        if decaltype in ["SIMPLE", "SUBSET", "PANEL"]:
            if pattern == (True, True, True, False, True):
                requiredtextures = True

        elif decaltype == "INFO":
            if pattern == (False, False, True, True, True):
                requiredtextures = True

        return requiredtextures


class ClearProps(bpy.types.Operator):
    bl_idname = "machin3.clear_decal_props"
    bl_label = "MACHIN3: clear_decal_props"
    bl_description = "Clear Decal Properties, turning a Decal into a regular object"
    bl_options = {'REGISTER', 'UNDO'}

    clear_modifiers: BoolProperty(name="Clear Modifiers", default=True)
    clear_materials: BoolProperty(name="Clear Materials", default=True)

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        row = column.row(align=True)
        row.label(text="Clear")

        row.prop(self, "clear_modifiers", text="Modifiers", toggle=True)
        row.prop(self, "clear_materials", text="Materials", toggle=True)

    @classmethod
    def poll(cls, context):
        return [obj for obj in context.selected_objects if obj.type == 'MESH']

    def execute(self, context):
        decals = [obj for obj in context.selected_objects if obj.DM.isdecal]

        if decals:
            for decal in decals:

                if self.clear_modifiers:
                    decal.modifiers.clear()

                if self.clear_materials:
                    decal.data.materials.clear()

                clear_decalobj_props(decal)

                unlock(decal)

                if decal.parent:
                    unparent(decal)

        else:
            popup_message("No decals among selected objects", title="Illegal Selection")


        return {'FINISHED'}


class RestoreUserKeymapItems(bpy.types.Operator):
    bl_idname = "machin3.restore_decal_machine_user_keymap_items"
    bl_label = "MACHIN3: Restore DECALmachine Keymaps"
    bl_description = "Restore DECALmachine keymaps, removed by the user"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        for name, keylist in keysdict.items():
            for item in keylist:
                print()

                keymap = item.get("keymap")
                space_type = item.get("space_type", "EMPTY")

                km = kc.keymaps.get(keymap, None)

                if not km:
                    km = kc.keymaps.new(name=keymap, space_type=space_type)

                idname = item.get("idname")

                kmi = km.keymap_items.get(idname)

                if kmi:
                    print("INFO: keymap item is already set", idname)
                    print("      type:", kmi.type)
                    print("      value:", kmi.value)
                    print("      shift:", kmi.shift, "ctrl:", kmi.ctrl, "alt:", kmi.alt)

                if not kmi:
                    type = item.get("type")
                    value = item.get("value")

                    shift = item.get("shift", False)
                    ctrl = item.get("ctrl", False)
                    alt = item.get("alt", False)

                    print("WARNING: recreating keymap item", idname)
                    print("         type:", type)
                    print("         value:", value)
                    print("         shift:", shift, "ctrl:", ctrl, "alt:", alt)

                    kmi = km.keymap_items.new(idname, type, value, shift=shift, ctrl=ctrl, alt=alt)

                    if kmi:
                        properties = item.get("properties")

                        if properties:
                            for name, value in properties:
                                setattr(kmi.properties, name, value)

        return {'FINISHED'}
