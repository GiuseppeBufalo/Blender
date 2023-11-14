import bpy
import os
from ... utils.system import abspath, splitpath, relpath, makedir, load_json
from ... utils.registration import get_prefs


class PackImages(bpy.types.Operator):
    bl_idname = "machin3.pack_decal_textures"
    bl_label = "MACHIN3: Pack Decal Textures"
    bl_description = "Pack Decal and Trim Sheet Textures into blend file"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        textures = sorted([(img, img.users) for img in bpy.data.images if (img.DM.isdecaltex or img.DM.istrimsheettex or img.DM.istrimdecaltex) and not img.packed_file], key=lambda i: i[0].filepath)

        for img, users in textures:
            if users:
                path = abspath(img.filepath)

                if os.path.exists(path):
                    img.filepath = path
                    print("INFO: packing", img.name)
                    img.pack()

                else:
                    print("WARNING: Image path doesn't exist for image %s, skipping: %s" % (img.name, path))

            else:
                print("INFO: removing 0 users image", img.name)
                bpy.data.images.remove(img)

        return {'FINISHED'}


class UnpackImages(bpy.types.Operator):
    bl_idname = "machin3.unpack_decal_textures"
    bl_label = "MACHIN3: Unpack Decal Textures"
    bl_description = "Unpack Decal and Trim Sheet Textures\nALT: Force unpacking to local path"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        assetspath = get_prefs().assetspath

        textures = sorted([img for img in bpy.data.images if (img.DM.isdecaltex or img.DM.istrimsheettex or img.DM.istrimdecaltex) and img.packed_file], key=lambda i: i.filepath)

        force_local = event.alt

        for img in textures:
            path = abspath(img.filepath)
            folderpath = os.path.dirname(path)

            if img.DM.istrimsheettex:
                datapath = os.path.join(folderpath, 'data.json')

                if os.path.exists(datapath):
                    sheetdata = load_json(datapath)
                    uuid = sheetdata.get('uuid')
                else:
                    uuid = None

            elif img.DM.isdecaltex or img.DM.istrimdecaltex:
                uuidpath = os.path.join(folderpath, 'uuid')

                if os.path.exists(uuidpath):
                    with open(uuidpath) as f:
                        uuid = f.read()
                else:
                    uuid = None

            split = splitpath(path)

            if img.DM.istrimsheettex:
                fixedpath = os.path.join(assetspath, 'Trims', *split[-2:])

            elif img.DM.istrimdecaltex:
                fixedpath = os.path.join(assetspath, 'Trims', *split[-3:])

            elif img.DM.isdecaltex:
                fixedpath = os.path.join(assetspath, 'Decals', *split[-3:])

            fixedfolderpath = os.path.dirname(fixedpath)

            if img.DM.istrimsheettex:
                fixeddatapath = os.path.join(folderpath, 'data.json')

                if os.path.exists(fixeddatapath):
                    fixedsheetdata = load_json(fixeddatapath)
                    fixeduuid = fixedsheetdata.get('uuid')
                else:
                    fixeduuid = None

            elif img.DM.isdecaltex or img.DM.istrimdecaltex:
                fixeduuidpath = os.path.join(fixedfolderpath, 'uuid')

                if os.path.exists(fixeduuidpath):
                    with open(fixeduuidpath) as f:
                        fixeduuid = f.read()
                else:
                    fixeduuid = None

            if not force_local and (os.path.exists(path) and uuid):
                print("INFO: unpacking to original path:", path)
                img.filepath = path
                img.unpack(method='REMOVE')

            elif not force_local and fixedpath != path and (os.path.exists(fixedpath) and fixeduuid):
                print("INFO: unpacking to fixed path:", fixedpath)
                img.filepath = fixedpath
                img.unpack(method='REMOVE')

            else:

                if img.DM.istrimsheettex:
                    trimsheetname = img.DM.trimsheetname
                    localpath = os.path.join(os.path.dirname(bpy.data.filepath), 'textures', 'Trims', trimsheetname, os.path.basename(path))

                elif img.DM.isdecaltex:
                    decalname = img.DM.decalname.replace(img.DM.decallibrary + '_', '')
                    localpath = os.path.join(os.path.dirname(bpy.data.filepath), 'textures', 'Trims' if img.DM.istrimdecaltex else 'Decals', img.DM.decallibrary, decalname, os.path.basename(path))

                print("INFO: unpacking to local path:", relpath(localpath))

                makedir(os.path.dirname(localpath))

                img.filepath_raw = relpath(localpath)
                img.save()

                img.unpack(method='REMOVE')

        return {'FINISHED'}
