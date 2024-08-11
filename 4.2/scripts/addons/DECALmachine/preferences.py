import bpy
import os
import platform
from bpy.props import CollectionProperty, IntProperty, StringProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty
from time import time
from . properties import DecalLibsCollection, AtlasesCollection
from . utils.assets import declutter_assetspath, get_assets_dict, move_assets, get_ambiguous_libs, get_invalid_libs, get_corrupt_libs, verify_assetspath
from . utils.registration import get_path, get_name, reload_decal_libraries, get_addon, get_version_filename_from_blender
from . utils.ui import get_icon, popup_message, draw_keymap_items, draw_pil_warning, draw_version_warning
from . utils.draw import draw_split_row
from . utils.system import makedir, abspath, get_PIL_image_module_path, normpath, remove_folder, get_bl_info_from_file, get_update_files
from . utils.assets import reload_all_assets
from . utils.library import get_lib, get_short_library_path, import_library, get_atlas, import_atlas
from . items import prefs_tab_items, prefs_asset_loader_tab_items, prefs_newlibmode_items, prefs_decalmode_items
from . import bl_info

meshmachine = None
machin3tools = None
punchit = None
curvemachine = None
hypercursor = None

thankyou_time = None

class DECALmachinePreferences(bpy.types.AddonPreferences):
    path = get_path()
    bl_idname = get_name()

    def update_update_path(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.update_path:
            if os.path.exists(self.update_path):
                filename = os.path.basename(self.update_path)

                if filename.endswith('.zip'):
                    split = filename.split('_')

                    if len(split) == 2:
                        addon_name, tail = split

                        if addon_name == bl_info['name']:
                            split = tail.split('.')

                            if len(split) >= 3:
                                dst = os.path.join(self.path, '_update')

                                from zipfile import ZipFile

                                with ZipFile(self.update_path, mode="r") as z:
                                    print(f"INFO: extracting {addon_name} update to {dst}")
                                    z.extractall(path=dst)

                                blinfo = get_bl_info_from_file(os.path.join(dst, addon_name, '__init__.py'))

                                if blinfo:
                                    self.update_msg = f"{blinfo['name']} {'.'.join(str(v) for v in blinfo['version'])} is ready to be installed."

                                else:
                                    remove_folder(dst)

            self.avoid_update = True
            self.update_path = ''

    update_path: StringProperty(name="Update File Path", subtype="FILE_PATH", update=update_update_path)
    update_msg: StringProperty(name="Update Message")
    update_keep_assets: BoolProperty(name="Keep Assets", description="Keep the currently installed assets folder, in your current DECCALmachine installation!\n\nHIGHLY RECOMMENDED if you have created custom Decals, and have your assetspath still in the DECALmachine addon folder, instead of somewhere outside",default=True)

    registration_debug: BoolProperty(name="Addon Terminal Registration Output", default=True)

    def update_assetspath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        old_path = abspath(self.oldpath)
        new_path = makedir(abspath(self.assetspath)) + os.sep

        self.oldpath = new_path

        self.avoid_update = True
        self.assetspath = new_path

        if self.move_assets:
            move_assets(old_path, new_path)

        if normpath(old_path) != normpath(new_path): 
            verify_assetspath()

            decluttered = declutter_assetspath(force=False)

            reload_all_assets()

            if decluttered:
                msg = ["There were files/folders in your new assets location, in places where they shouldn't have been.",
                       "They have been moved to a dedicated Clutter folder now."]

                for old_path, new_path in decluttered:
                    msg.append(f"  {'📁' if os.path.isdir(new_path) else '📄'} {get_short_library_path(old_path, assets_root=False)}") 

                popup_message(msg)
                             
    def update_importdecallibpath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.importdecallibpath.strip():
            path = abspath(self.importdecallibpath)

            if path and os.path.exists(path):
                msg = import_library(path)

            else:
                msg = "Path does not exist: %s" % (path)

            if msg:
                popup_message(msg, title="Decal Library could not be imported")

        self.avoid_update = True
        self.importdecallibpath = ""

    def update_newdecallibraryname(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        assetspath = self.assetspath
        name = self.newdecallibraryname.strip()

        if name:
            if os.path.exists(os.path.join(assetspath, 'Decals', name)):
                popup_message("This library exists already, choose another name!", title="Failed to add library", icon="ERROR")
            else:
                libpath = makedir(os.path.join(assetspath, 'Decals', name))

                print(" • Created decal library folder '%s'" % (libpath))

                with open(os.path.join(libpath, get_version_filename_from_blender()), "w") as f:
                    f.write("")

                self.avoid_update = True
                self.newdecallibraryname = ""

                get_assets_dict(force=True)
                reload_decal_libraries()

    def update_importatlaspath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.importatlaspath.strip():
            path = abspath(self.importatlaspath)

            if path and os.path.exists(path):
                msg = import_atlas(path)

            else:
                msg = "Path does not exist: %s" % (path)

            if msg:
                popup_message(msg, title="Atlas could not be imported")

        self.avoid_update = True
        self.importatlaspath = ""

    defaultpath = os.path.join(path, 'assets' + os.sep)
    assetspath: StringProperty(name="DECALmachine assets:\nDecal Libraries, Trim Sheet Libraries, Decal Atlases as well as\ntemporary locations for Decal/Trim Sheet/Atlas Creation and Export", subtype='DIR_PATH', default=defaultpath, update=update_assetspath)
    oldpath: StringProperty(name="Old Path", subtype='DIR_PATH', default=defaultpath)
    move_assets: BoolProperty(name="Move Assets, when changing assetspath", description="Move assets from current location to new location, when changing assetspath", default=True)
    decallibsCOL: CollectionProperty(type=DecalLibsCollection)
    decallibsIDX: IntProperty(name="Registered Decal or Trim Sheet")

    atlasesCOL: CollectionProperty(type=AtlasesCollection)
    atlasesIDX: IntProperty(name="Registered Atlas")

    newlibmode: EnumProperty(name="New Library Mode", items=prefs_newlibmode_items, default="EMPTY")
    importdecallibpath: StringProperty(name="Import Path", description="Choose a Folder or .zip File to load a Library from", subtype='FILE_PATH', default="", update=update_importdecallibpath)
    newdecallibraryname: StringProperty(name="New Library Name", description="Enter a name to create a new empty Decal Library", update=update_newdecallibraryname)

    importatlaspath: StringProperty(name="Import Atlas", description="Choose a Folder or .zip File to load a Atlas from", subtype='FILE_PATH', default="", update=update_importatlaspath)
    reversedecalsorting: BoolProperty(name="Reverse Decal Sorting (requires library reload or Blender restart)", description="Sort Decals Newest First", default=False)
    libraryrows: IntProperty(name="Rows of libraries in the Pie Menu", default=2, min=1)
    libraryoffset: IntProperty(name="Offset libraries to the right or left side of the Pie Menu", default=0)
    libraryscale: IntProperty(name="Size of Decal Library Icons", default=4, min=1, max=20)
    decalsinlibraryscale: IntProperty(name="Size of Icons in Decal Libraries", default=4, min=1, max=20)
    showdecalcount: BoolProperty(description="Show Decal Count next to Library Name", default=False)
    showdecalnames: BoolProperty(description="Show Decal Names in Decal Libraries", default=False)
    showdecalbuttonname: BoolProperty(description="Show Decal Name on Insert Button", default=False)
    reversetrimsorting: BoolProperty(name="Reverse Trim Sorting (requires library reload or Blender restart)", description="Sort Trims Newest First", default=False)
    trimlibraryrows: IntProperty(name="Rows of libraries in the Pie Menu", default=1, min=1)
    trimlibraryoffset: IntProperty(name="Offset libraries to the right or left side of the Pie Menu", default=0)
    trimlibraryscale: IntProperty(name="Size of Decal Library Icons", default=4, min=1, max=20)
    trimsinlibraryscale: IntProperty(name="Size of Icons in Trimsheet Libraries", default=4, min=1, max=20)
    showtrimcount: BoolProperty(description="Show Trim Count next to Library Name", default=False)
    showtrimnames: BoolProperty(description="Show Trim Names in Trimsheet Libraries", default=False)
    showtrimbuttonname: BoolProperty(description="Show Trim Name on Insert Button", default=False)
    decalcreator: StringProperty(name="Decal Creator", description="Setting this property, will mark Decals created by you with your own details", default="MACHIN3 - machin3.io, @machin3io")
    use_decal_float_normals: BoolProperty(name="Use Decal Float Normals", description="Use 16-bit vs 8-bit Normal Maps, when creating Decals", default=False)

    show_join_in_pie: BoolProperty(description="Show Join and Split in Pie Menu\nThey can otherwise always be found in the Tools section of the main DECALmachine Panel in the 3D Views Sidebar", default=False)
    adjust_use_alt_height: BoolProperty(description="Require ALT Key when adjusting Decal Height", default=False)
    modal_hud_hints: BoolProperty(description="Show Hints", default=True)
    modal_hud_scale: FloatProperty(name="HUD Scale", default=1, min=0.5, max=10)
    modal_hud_color: FloatVectorProperty(name="HUD Font Color", subtype='COLOR', default=[1, 1, 1], size=3, min=0, max=1)
    modal_hud_timeout: FloatProperty(name="HUD timeout", description="Global Timeout Modulation (not exposed or used in DECALmachine yet)", default=1, min=0.1)

    show_sidebar_panel: BoolProperty(name="Show Sidebar Panel", default=True)
    show_legacy_assets_in_blend_warnings: BoolProperty(name="Show warnings when loading .blend files containing legacy assets", default=True)

    def update_trim_uv_layer(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.trim_uv_layer == self.second_uv_layer:
            self.avoid_update = True

            if self.second_uv_layer - 1 >= 0:
                self.second_uv_layer -= 1
            else:
                self.second_uv_layer += 1

    def update_second_uv_layer(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.second_uv_layer == self.trim_uv_layer:
            self.avoid_update = True

            if self.trim_uv_layer - 1 >= 0:
                self.trim_uv_layer -= 1
            else:
                self.trim_uv_layer += 1

    trim_uv_layer: IntProperty(name="UV Layer used for Trim Detail", default=0, min=0, update=update_trim_uv_layer)
    second_uv_layer: IntProperty(name="Secondary UV Layer used by Box Unwrap", default=1, min=0, update=update_second_uv_layer)

    update_available: BoolProperty(name="Update is available", default=False)

    def update_show_update(self, context):
        if self.show_update:
            get_update_files(force=True)

    tabs: EnumProperty(name="Tabs", items=prefs_tab_items, default="GENERAL")
    asset_loader_tabs: EnumProperty(name="Asset Loader Tabs", items=prefs_asset_loader_tab_items, default="DECALS")
    show_update: BoolProperty(default=False, update=update_show_update)
    def update_decalmode(self, context):
        if self.decalremovemode is True:
            self.decalmode = "REMOVE"
        else:
            self.decalmode = "INSERT"

    decalmode: EnumProperty(name="Decal Mode", items=prefs_decalmode_items, default="INSERT")
    decalremovemode: BoolProperty(name="Decal Removal Mode", description="Toggle Decal Removal Mode\nThis allows for permanent removal of specific Decals from the Hard Drive", default=False, update=update_decalmode)
    pil: BoolProperty(name="PIL", default=False)
    pilrestart: BoolProperty(name="PIL restart", default=False)
    showpildetails: BoolProperty(name="Show PIL details", default=False)
    show_future: BoolProperty(name="Show/Hide Next-Gen Info", default=True)
    show_collision: BoolProperty(name="Show/Hide Collision Info", default=True)
    show_decluttered: BoolProperty(name="Show/Hide Decluttered Info", default=True)
    show_quarantined: BoolProperty(name="Show/Hide Quarantiend Info", default=True)
    show_skipped: BoolProperty(name="Show/Hide Skipped Info", default=True)
    avoid_update: BoolProperty(default=False)

    def draw(self, context):
        layout=self.layout

        draw_version_warning(layout, (3, 6, 0))

        self.draw_thank_you(layout)

        self.draw_update(layout)

        self.draw_support(layout)

        column = layout.column()

        row = column.row()
        row.prop(self, "tabs", expand=True)

        box = column.box()

        if self.tabs == "GENERAL":
            self.draw_general_tab(box)

        elif self.tabs == "CREATEEXPORT":
            self.draw_create_export_tab(box)

        elif self.tabs == "ABOUT":
            self.draw_about_tab(box)

    def draw_thank_you(self, layout):
        global thankyou_time

        message = [f"Thank you for purchasing {bl_info['name']}!",
                   "",
                   "Your support allows me to keep developing this addon and future ones, keeps updates free for everyone, and most importantly enables me to provide for my family.",
                   f"If you haven't purchased {bl_info['name']}, please consider doing so."]

        if thankyou_time is None:
            thankypou_path = os.path.join(get_path(), 'thank_you')

            if not os.path.exists(thankypou_path):
                thankyou_time = time()
                msg = message + ['', str(thankyou_time)]

                with open(thankypou_path, mode='w') as f:
                    f.write('\n'.join(m for m in msg))

            else:
                with open(thankypou_path) as f:
                    lines = [l[:-1] for l in f.readlines()]

                try:
                    thankyou_time = float(lines[-1])

                except:
                    os.unlink(thankypou_path)

        if thankyou_time:
            draw_message = False
            message_lifetime = 5

            if isinstance(thankyou_time, float):
                deltatime = (time() - thankyou_time) / 60
                draw_message = deltatime < message_lifetime

            else:
                draw_message = True
                deltatime = 'X'

            if draw_message:

                b = layout.box()
                b.label(text="Thank You!", icon='INFO')

                col = b.column()

                for i in range(2):
                    col.separator()

                for line in message:
                    if line:
                        col.label(text=line)
                    else:
                        col.separator()

                for i in range(3):
                    col.separator()

                col.label(text=f"This message will self-destruct in {message_lifetime - deltatime:.1f} minutes.", icon='SORTTIME')

                for i in range(3):
                    col.separator()

                col.label(text=f"If you have purchased {bl_info['name']} and find this nag-screen annoying, I appologize.")
                col.label(text=f"If you haven't purchased {bl_info['name']} and find this nag-screen annoying, go fuck yourself.")

    def draw_update(self, layout):
        column = layout.column(align=True)

        row = column.row()
        row.scale_y = 1.25
        row.prop(self, 'show_update', text="Install DECALmachine Update", icon='TRIA_DOWN' if self.show_update else 'TRIA_RIGHT')

        if self.show_update:
            update_files = get_update_files()

            box = layout.box()
            box.separator()

            if self.update_msg:
                row = box.row()
                row.scale_y = 1.5

                split = row.split(factor=0.35, align=True)
                split.label(text=self.update_msg, icon_value=get_icon('refresh_green'))

                s = split.split(factor=0.33, align=True)
                s.operator('machin3.remove_decalmachine_update', text='Remove Update', icon='CANCEL')

                ss = s.split(factor=0.33, align=True)
                ss.prop(self, 'update_keep_assets', text='Keep Assets', icon='MONKEY', toggle=True)
                ss.operator('wm.quit_blender', text='Quit Blender + Install Update', icon='FILE_REFRESH')

            else:
                b = box.box()
                col = b.column(align=True)

                row = col.row()
                row.alignment = 'LEFT'

                if update_files:
                    row.label(text="Found the following Updates in your home and/or Downloads folder: ")
                    row.operator('machin3.rescan_decalmachine_updates', text="Re-Scan", icon='FILE_REFRESH')

                    col.separator()

                    for path, tail, _ in update_files:
                        row = col.row()
                        row.alignment = 'LEFT'

                        r = row.row()
                        r.active = False

                        r.alignment = 'LEFT'
                        r.label(text="found")

                        op = row.operator('machin3.use_decalmachine_update', text=f"DECALmachine {tail}")
                        op.path = path
                        op.tail = tail

                        r = row.row()
                        r.active = False
                        r.alignment = 'LEFT'
                        r.label(text=path)

                else:
                    row.label(text="No Update was found. Neither in your Home directory, nor in your Downloads folder.")
                    row.operator('machin3.rescan_decalmachine_updates', text="Re-Scan", icon='FILE_REFRESH')

                row = box.row()

                split = row.split(factor=0.4, align=True)
                split.prop(self, 'update_path', text='')

                text = "Select DECALmachine_x.x.x.zip file"

                if update_files:
                    if len(update_files) > 1:
                        text += " or pick one from above"

                    else:
                        text += " or pick the one above"

                split.label(text=text)

            box.separator()

    def draw_support(self, layout):
        column = layout.column(align=True)
        column.separator()

        box = layout.box()
        box.label(text="Support")

        column = box.column()
        row = column.row()
        row.scale_y = 1.5
        row.operator('machin3.get_decalmachine_support', text='Get Support', icon='GREASEPENCIL')

    def draw_general_tab(self, layout):
        split = layout.split()

        b = split.box()

        b.label(text="Assets")

        self.draw_assets_path(b)

        self.draw_decal_libraries(b)

        self.draw_asset_loaders(b)

        b = split.box()
        b.label(text="Settings")

        self.draw_keymaps(b)

        self.draw_addon(b)

        self.draw_UI(b)

        self.draw_UVs(b)

    def draw_create_export_tab(self, layout):
        split = layout.split()

        b = split.box()
        b.label(text="Create")

        self.draw_pil(b)

        self.draw_decal_creation(b)

        b = split.box()
        b.label(text="Export")

        self.draw_decal_export(b)

    def draw_about_tab(self, layout):
        split = layout.split()

        b = split.box()
        b.label(text="MACHIN3")

        self.draw_machin3(b)

        b = split.box()
        b.label(text="Get More Decals")
        self.draw_decal_resources(b)

    def draw_addon(self, layout):
        box = layout.box()
        box.label(text="Addon")

        column = box.column()

        draw_split_row(self, column, 'registration_debug', label='Print Addon Registration Output in System Console')

    def draw_assets_path(self, layout):
        box = layout.box()
        col = box.column()

        split = col.split(factor=0.2, align=True)
        split.label(text="Location")

        row = split.row(align=True)
        row.prop(self, "assetspath", text='')
        row.operator("machin3.reset_decalmachine_assets_location", text="", icon="LOOP_BACK")

        draw_split_row(self, col, 'move_assets', label='Move Assets to new location, when changing assetspath')

        if normpath(self.assetspath) == normpath(self.defaultpath):
            b = box.box()

            col = b.column()
            col.label(text="I highly recommend you change this path!", icon='INFO')
            col.label(text="Otherwise your Assets will remain in the DECALmachine folder,", icon='BLANK1')
            col.label(text="and you risk loosing any Decals/Trim Sheets/Atlases you have", icon='BLANK1')
            col.label(text="created yourself, when uninstalling or updating DECALmachine", icon='BLANK1')

        assets_dict = get_assets_dict(force=False)

        obsolete = assets_dict['OBSOLETE']
        legacy = assets_dict['LEGACY']
        future = assets_dict['FUTURE']

        ambiguous = get_ambiguous_libs()
        invalid = get_invalid_libs()
        corrupt = get_corrupt_libs()

        clutter = assets_dict['CLUTTER']
        decluttered = assets_dict['DECLUTTERED']

        collided = assets_dict['COLLIDED']
        quarantined = assets_dict['QUARANTINED']
        skipped = assets_dict['SKIPPED']

        deferred = False
        if any([obsolete, legacy, future, ambiguous, invalid, corrupt]):
            b = box.box()
            b.label(text="Failed Asset Registration")

            if legacy or ambiguous:
                bb = b.box()
                bb.label(text="Update-able Asset Libraries")

                col = bb.column(align=True)

                has_both_types = legacy and ambiguous
                has_multiple = (len(legacy) + len(ambiguous) > 1) or has_both_types

                updateable_verb = 'are' if has_multiple else 'is a' if legacy else 'is an'
                updateable_type = 'Legacy and Ambiguous' if has_both_types else 'Legacy' if legacy else 'Ambiguous'
                updateable_action = 'updated and fixed' if has_both_types else 'updated' if legacy else 'fixed'

                updateable_action_button = 'Update and Fix' if has_both_types else 'Update' if legacy else 'Fix'
                updateable_object_button = 'Them All' if has_multiple else 'It'

                decalspath = os.path.join(self.assetspath, 'Decals')
                trimspath = os.path.join(self.assetspath, 'Trims')

                asset_type = 'Decal and Trim Sheet' if all(any(path.startswith(type_path) for path in legacy + ambiguous) for type_path in [decalspath, trimspath]) else 'Decal' if all(path.startswith(decalspath) for path in legacy + ambiguous) else 'Trim Sheet'

                text = f"There {updateable_verb} {updateable_type} {asset_type} {'libraries' if has_multiple else 'library'} in your current Assets Location, that can be {updateable_action}!"
                optext = f"{updateable_action_button} {updateable_object_button}!"

                col.label(text=text, icon='INFO')

                draw_pil_warning(col, needed="for library update")

                row = col.row()
                row.scale_y = 2
                row.operator("machin3.batch_update_decal_libraries", text=optext, icon_value=get_icon('refresh'))

            if future:
                bb = b.box()

                row = bb.row(align=True)
                row.label(text="Next-Gen Asset Libraries", icon='ERROR')
                row.scale_x = 1.25

                row.prop(self, 'show_future', text='', icon='TRIA_DOWN' if self.show_future else 'TRIA_LEFT')

                if self.show_future:
                    col = bb.column(align=True)
                    col.label(text="The following Folders in your Assets Location are Libraries created in or updated for a newer DECALmachine or Blender version.")
                    col.label(text="They can't be actively used in this version of DECALmachine or Blender, and they can't be downgraded either.")
                    col.label(text="They should still display fine in any existing .blend files, that use a previous version of them however.")
                    col.separator()

                    for path in future:
                        col.label(text=f"  📁 {get_short_library_path(path, assets_root=False)}")

            if any([obsolete, invalid, corrupt]):
                deferred = True
                bb = b.box()

                column = bb.split(factor=0.7, align=True)

                col = column.column(align=True)
                col.label(text=f"Some Libraries in your assets location could not be registered, and require", icon_value=get_icon('error'))
                col.label(text="further investigation. The best way to do this is is by first moving them into")
                col.label(text="Quarantine, followed by checking the log files, generated in that process.")

                row = column.row()
                row.scale_y = 3
                row.operator('machin3.quarantine_asset_lib', text='Quarantine', icon_value=get_icon('radiation'))

                column = bb.column(align=True)
                column.label(text="The following reasons caused these libraries to fail registration:")

                if obsolete:
                    column.label(text="  •  Obsolete Libraries! These are libraries, that predate decal versioning, and can't be updated (by you).")
                                         
                if set(invalid) - set(obsolete):
                    column.label(text="  •  Invalid Libraries! These are libraries without an indicator file.")

                if set(corrupt) - set(obsolete) - set(ambiguous) - set(invalid):
                    column.label(text="  •  Corrupt Libraries! These are libraries containing empty or non-Decal folders.")

                column = bb.split(factor=0.7, align=True)
                column.scale_y = 1.5
                column.label(text="For more info and on what and why please see the documentation.")
                column.operator("wm.url_open", text="Documentation", icon='URL').url = "https://machin3.io/DECALmachine/docs/preferences/#failed-asset-registration"

        if clutter:
            deferred = True
            b = box.box()
            b.label(text="Clutter")

            column = b.split(factor=0.7, align=True)

            col = column.column(align=True)
            col.label(text="The following files/folders in your Assets Location shouldn't be there. It's clutter.")

            row = column.row()
            row.scale_y = 1.5
            row.operator('machin3.declutter_assetspath', text='Declutter', icon_value=get_icon('clutter'))

            col.separator()

            for path in clutter:
                col.label(text=f"  {'📁' if os.path.isdir(path) else '📄'} {get_short_library_path(path, assets_root=False)}") 

        if collided:
            deferred = True
            b = box.box()

            row = b.row(align=True)
            row.label(text="Collided Asset Libraries", icon='ERROR')
            row.scale_x = 1.25

            if self.show_collision:
                row.operator('machin3.open_folder', text='', icon='FILE_FOLDER').path = self.assetspath

            row.prop(self, 'show_collision', text='', icon='TRIA_DOWN' if self.show_collision else 'TRIA_LEFT')

            if self.show_collision:
                col = b.column(align=True)

                col.label(text="Some previous libraries have been moved out of the way, when changing the assets location, with the 'Move Assets' option enabled.")
                col.label(text="This was done to avoid overwriting existing folders in the target location, thereby potentially creating ambiguous libraries.")
                col.separator()
                col.label(text="Investigate the following libraries, to see if they are still required, otherwise remove them. Usually they are just DM's Example Assets")
                col.separator()

                for path in collided:
                    col.label(text=f"  📁 {get_short_library_path(path, assets_root=False)}")

        if decluttered:
            deferred = True
            b = box.box()

            row = b.row(align=True)
            row.label(text="Decluttered Files/Folders", icon='ERROR')
            row.scale_x = 1.25

            if self.show_decluttered:
                row.operator('machin3.open_folder', text='', icon='FILE_FOLDER').path = os.path.join(self.assetspath, 'Clutter')

            row.prop(self, 'show_decluttered', text='', icon='TRIA_DOWN' if self.show_decluttered else 'TRIA_LEFT')

            if self.show_decluttered:

                col = b.column(align=True)
                col.label(text="In a previous Asset Path Operation a number of misplaced files/folders have been detected in your assets location.")
                col.label(text="They have been collected in the Clutter folder now. Most likely these are old decal libraries, that ended up in the root assets path, rather")
                col.label(text="than the Decals sub-folder. Investigate if they are still needed, and if not remove them.")
                col.label(text="You can try moving them into the Decals sub-folder, and optionally update them. But watch out for duplicates.")

                col.separator()

                for path in decluttered:
                    col.label(text=f"  {'📁' if os.path.isdir(path) else '📄'} {get_short_library_path(path, assets_root=False)}") 

        if quarantined:
            deferred = True
            b = box.box()

            row = b.row(align=True)
            row.label(text="Quarantined Asset Libraries", icon='ERROR')
            row.scale_x = 1.25

            if self.show_quarantined:
                row.operator('machin3.open_folder', text='', icon='FILE_FOLDER').path = self.assetspath

            row.prop(self, 'show_quarantined', text='', icon='TRIA_DOWN' if self.show_quarantined else 'TRIA_LEFT')

            if self.show_quarantined:
                col = b.column(align=True)
                col.label(text="The following Libraries couldn't be registered or updated, and have been quarantined for further investigation.")
                col.label(text="Each one contains a log.txt file with information on why these libraries were quarantined.")
                col.separator()

                for path in quarantined:
                    col.label(text=f"  📁 {get_short_library_path(path, assets_root=False)}")

        if skipped:
            deferred = True
            b = box.box()

            row = b.row(align=True)
            row.label(text="Skipped Asset Libraries", icon='ERROR')
            row.scale_x = 1.25

            if self.show_skipped:
                row.operator('machin3.open_folder', text='', icon='FILE_FOLDER').path = self.assetspath

            row.prop(self, 'show_skipped', text='', icon='TRIA_DOWN' if self.show_skipped else 'TRIA_LEFT')

            if self.show_skipped:
                col = b.column(align=True)
                col.label(text="Some Decals or potentially entire Libraries couldn't previously be updated and have been moved out of the Decals or Trims folders.")
                col.label(text="The specific reasons for this have been logged per-Decal, and can be found in the log.txt file in each library folder.")
                col.separator()

                for path in skipped:
                    col.label(text=f"  📁 {get_short_library_path(path, assets_root=False)}")

        if deferred:
            b = box.box()
            b.label(text="Customer Support", icon='GREASEPENCIL')

            column = b.column(align=True)

            column.label(text="If you need assistance with any of the above, feel free to reach out to decal@machin3.io")
            column.label(text="But when you do, make sure to use the GetSupport tool accordingly.")

            column.separator()

            row = column.row(align=True)
            row.scale_y = 2

            row.operator("wm.url_open", text="How to get Support?", icon='WORLD').url = "https://machin3.io/DECALmachine/docs/faq/#get-support"
            row.operator('machin3.get_decalmachine_support', text='Get Support tool', icon='GREASEPENCIL')

    def draw_decal_libraries(self, layout):
        box = layout.box()
        box.label(text="Registered Decal + Trim Libraries")

        column = box.column()
        row = column.row()

        col = row.column(align=True)
        col.template_list("MACHIN3_UL_decal_libs", "", self, "decallibsCOL", self, "decallibsIDX", rows=max(len(self.decallibsCOL), 6))

        col = row.column(align=True)
        col.operator("machin3.move_decal_or_trim_library", text="", icon="TRIA_UP").direction = "UP"
        col.operator("machin3.move_decal_or_trim_library", text="", icon="TRIA_DOWN").direction = "DOWN"
        col.separator()
        col.operator("machin3.rename_decal_or_trim_library", text="", icon="OUTLINER_DATA_FONT")
        col.separator()
        col.operator("machin3.clear_decal_and_trim_libraries", text="", icon="LOOP_BACK")
        col.operator("machin3.reload_decal_and_trim_libraries", text="", icon_value=get_icon("refresh"))

        _, _, active = get_lib()
        icon = "cancel" if active and not active.islocked else "cancel_grey"
        col.operator("machin3.remove_decal_or_trim_library", text="", icon_value=get_icon(icon))

        column = box.column()

        row = column.row()
        row.prop(self, "newlibmode", expand=True)

        if self.newlibmode == 'IMPORT':
            row.label(text="Library from Folder or .zip")
            row.prop(self, "importdecallibpath", text="")
        else:
            row.label(text="Library named")
            row.prop(self, "newdecallibraryname", text="")

    def draw_asset_loaders(self, layout):
        box = layout.box()
        box.label(text="Asset Loaders")

        row = box.row()
        row.prop(self, "asset_loader_tabs", expand=True)

        column = box.column(align=True)

        if self.asset_loader_tabs == 'DECALS':
            draw_split_row(self, column, 'libraryrows', label='Rows of Decal Libraries in the Pie Menu')
            draw_split_row(self, column, 'libraryoffset', label='Offset Decal Libraries to right or left side in the Pie Menu')
            draw_split_row(self, column, 'libraryscale', label='Size of Decal Library Icons')
            draw_split_row(self, column, 'decalsinlibraryscale', label='Size of Icons in Decal Libraries')
            draw_split_row(self, column, 'reversedecalsorting', label='Sort Decals Newest First', info='requires library reload or Blender restart', factor=0.202)
            draw_split_row(self, column, 'showdecalcount', label='Show Decal Count next to Library Name')
            draw_split_row(self, column, 'showdecalnames', label='Show Decal Names in Decal Libraries')
            draw_split_row(self, column, 'showdecalbuttonname', label='Show Decal Name on Insert Buttons')

        elif self.asset_loader_tabs == 'TRIMS':
            draw_split_row(self, column, 'trimlibraryrows', label='Rows of Trim Libraries in the Pie Menu')
            draw_split_row(self, column, 'trimlibraryoffset', label='Offset Trim Libraries to right or left side in the Pie Menu')
            draw_split_row(self, column, 'trimlibraryscale', label='Size of Trim Library Icons')
            draw_split_row(self, column, 'trimsinlibraryscale', label='Size of Icons in Trim Libraries')
            draw_split_row(self, column, 'reversetrimsorting', label='Sort Trims Newest First', info='requires library reload or Blender restart', factor=0.202)
            draw_split_row(self, column, 'showtrimcount', label='Show Trim Count next to Library Name')
            draw_split_row(self, column, 'showtrimnames', label='Show Trim Names in Decal Libraries')
            draw_split_row(self, column, 'showtrimbuttonname', label='Show Trim Name on Insert Buttons')

    def draw_keymaps(self, layout):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        from . registration import keys as keysdict

        box = layout.box()
        box.label(text="Keymaps")

        column = box.column()

        drawn = []
        for name, keylist in keysdict.items():
            drawn.extend(draw_keymap_items(kc, name, keylist, column))

        if not all(drawn):
            row = box.row()
            row.scale_y = 1.5
            row.operator('machin3.restore_decal_machine_user_keymap_items', text="Restore Keymaps")

    def draw_UI(self, layout):
        box = layout.box()
        box.label(text="UI")

        column = box.column(align=True)

        draw_split_row(self, column, 'show_join_in_pie', label='Show Join and Split tools in Pie Menu')
        draw_split_row(self, column, 'adjust_use_alt_height', label='Require ALT key when adjusting decal height', info='Helpful to prevent accidental height changes', factor=0.202)

        box.label(text="HUDs")

        column = box.column()

        row = draw_split_row(self, column, 'modal_hud_hints', label='Show Hints', factor=0.6)
        draw_split_row(self, row, 'modal_hud_scale', label='HUD Scale', factor=0.6)
        draw_split_row(self, row, 'modal_hud_color', label='Color', expand=False, factor=0.6)

        box.label(text="View 3D")

        column = box.column(align=True)

        draw_split_row(self, column, 'show_sidebar_panel', label='Show Sidebar panel')
        draw_split_row(self, column, 'show_legacy_assets_in_blend_warnings', label="Show fading warnings when loading .blend files containing legacy assets")

    def draw_UVs(self, layout):
        box = layout.box()
        box.label(text="UVs")

        column = box.column(align=True)

        row = draw_split_row(self, column, 'trim_uv_layer', label='UV Layer used for Trim Detail', factor=0.4)
        draw_split_row(self, row, 'second_uv_layer', label='UV Layer used for Box Unwrap', factor=0.4)

    def draw_pil(self, layout):
        box = layout.box()
        column = box.column()
        column.scale_y = 1.2

        if self.pil:
            row = column.row()
            row.label(text="PIL is installed.", icon_value=get_icon("save"))

            icon = 'TRIA_DOWN' if self.showpildetails else 'TRIA_LEFT'
            row.prop(self, "showpildetails", text="", icon=icon)

            if self.showpildetails:
                path = get_PIL_image_module_path()
                if path:
                    column.label(text=path, icon='MONKEY')

                row = column.row()
                row.operator("machin3.purge_pil", text="Purge PIL", icon_value=get_icon('cancel'))

        elif self.pilrestart:
            column.label(text="PIL has been installed. Please restart Blender now.", icon="INFO")

        else:
            row = column.split(factor=0.2)
            row.operator("machin3.install_pil", text="Install PIL", icon="PREFERENCES")
            col = row.column()
            col.label(text="PIL is needed for Decal and Trim Sheet Creation as wells as for Atlasing and Baking.")
            col.label(text="Internet connection required.", icon_value=get_icon('info'))

            column.separator()

            box = column.box()
            box.label(text="Alternative Installation Methods")

            col = box.column(align=True)
            col.label(text="If you've used the Install button above, but are not seeing a green checkmark,")
            col.label(text="even after a Blender restart, you can try the following alternative installation methods.")

            if platform.system() == "Windows":
                b = col.box()
                r = b.row()
                r.label(text="Windows users, purge PIL now.")
                r.operator("machin3.purge_pil", text="Purge PIL", icon_value=get_icon('cancel'))

            elif platform.system() == "Darwin" and "AppTranslocation" in bpy.app.binary_path:
                b = col.box()
                b.label(text="Warning", icon_value=get_icon("error"))
                c = b.column()

                c.label(text="Blender is not properly installed, AppTranslocation is enabled.")
                c.label(text="Please refer to Blender's 'Installing on macOS' instructions.")
                c.label(text="Note that, for dragging of files and folders, you need to hold down the command key.")

                r = c.row()
                r.operator("wm.url_open", text="Installing on macOS").url = "https://docs.blender.org/manual/en/dev/getting_started/installing/macos.html"
                r.operator("wm.url_open", text="additional Information").url = "https://machin3.io/DECALmachine/docs/installation/#macos"

            col.label(text="Make sure to either run Blender as Administrator or at least have write access to the Blender folder.")
            col.label(text="Restart Blender, if the green checkmark doesn't show, after pressing either button.")

            row = col.row()
            row.operator("machin3.install_pil_admin", text="Install PIL (Admin)", icon="PREFERENCES")
            row.operator("machin3.easy_install_pil_admin", text="Easy Install PIL (Admin)", icon="PREFERENCES")

    def draw_decal_creation(self, layout):
        box = layout.box()
        column = box.column()

        row = column.split(factor=0.25)
        row.label(text="Decal Creator")
        row.prop(self, "decalcreator", text="")

        row = column.split(factor=0.25)
        row.label()
        row.label(text="Change this, so Decals created by you, are tagged with your info!", icon="INFO")

        column.separator()

        row = column.split(factor=0.25)
        row.label(text="Float Normals")

        r = row.split(factor=0.25)
        r.prop(self, "use_decal_float_normals", text=str(self.use_decal_float_normals), toggle=True)

        row = column.split(factor=0.25)
        row.label()
        row.label(text="Largely untested, use at your own risk", icon="INFO")

        row = column.split(factor=0.25)
        row.label()
        row.label(text="Atlasing will work, but will create 8-bit normal Atlas map", icon="INFO")

    def draw_decal_export(self, layout):
        box = layout.box()
        box.label(text="Decal Atlases")

        _, _, active = get_atlas()

        if active and active.istrimsheet:
            _, libs, _ = get_lib()

            for idx, lib in enumerate(libs):
                if lib.name == active.name:
                    self.decallibsIDX = idx
                    break

        column = box.column()

        row = column.row()

        col = row.column(align=True)
        col.template_list("MACHIN3_UL_atlases", "", self, "atlasesCOL", self, "atlasesIDX", rows=max(len(self.atlasesCOL), 6))

        col = row.column(align=True)
        col.operator("machin3.move_atlas", text="", icon="TRIA_UP").direction = "UP"
        col.operator("machin3.move_atlas", text="", icon="TRIA_DOWN").direction = "DOWN"
        col.separator()

        if active and active.istrimsheet:
            col.operator("machin3.rename_decal_or_trim_library", text="", icon="OUTLINER_DATA_FONT")
        else:
            col.operator("machin3.rename_atlas", text="", icon="OUTLINER_DATA_FONT")

        col.separator()
        col.operator("machin3.reload_atlases", text="", icon_value=get_icon("refresh"))

        if active and active.istrimsheet:
            icon = "cancel" if lib and not lib.islocked else "cancel_grey"
            col.operator("machin3.remove_decal_or_trim_library", text="", icon_value=get_icon(icon))
        else:
            icon = "cancel" if active and not active.islocked else "cancel_grey"
            col.operator("machin3.remove_atlas", text="", icon_value=get_icon(icon))

        row = column.row()
        row.label(text="Import Existing Atlas from Folder or .zip")
        row.prop(self, "importatlaspath", text="")

    def draw_machin3(self, layout):
        global meshmachine, machin3tools, punchit, curvemachine, hypercursor

        if meshmachine is None:
            meshmachine = get_addon('MESHmachine')[0]

        if machin3tools is None:
            machin3tools = get_addon('MACHIN3tools')[0]

        if punchit is None:
            punchit = get_addon('PUNCHit')[0]

        if curvemachine is None:
            curvemachine = get_addon('CURVEmachine')[0]

        if hypercursor is None:
            hypercursor = get_addon('HyperCursor')[0]

        installed = get_icon('save')
        missing = get_icon('cancel_grey')

        box = layout.box()
        box.label(text="My other Blender Addons")
        column = box.column(align=True)

        row = column.split(factor=0.3, align=True)
        row.scale_y = 1.2
        row.label(text="MESHmachine", icon_value=installed if meshmachine else missing)
        r = row.split(factor=0.2, align=True)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://mesh.machin3.io"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/a/164689011/Gwgt"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://www.blendermarket.com/products/MESHmachine?ref=1051"

        row = column.split(factor=0.3, align=True)
        row.scale_y = 1.2
        row.label(text="MACHIN3tools", icon_value=installed if machin3tools else missing)
        r = row.split(factor=0.2, align=True)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://machin3.io"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/a/164689011/IjsAf"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://www.blendermarket.com/products/MACHIN3tools?ref=1051"

        row = column.split(factor=0.3, align=True)
        row.scale_y = 1.2
        row.label(text="PUNCHit", icon_value=installed if punchit else missing)
        r = row.split(factor=0.2, align=True)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://punch.machin3.io/"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/a/164689011/irase"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://www.blendermarket.com/products/PUNCHit?ref=1051"

        row = column.split(factor=0.3, align=True)
        row.scale_y = 1.2
        row.label(text="CURVEmachine", icon_value=installed if curvemachine else missing)
        r = row.split(factor=0.2, align=True)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://curve.machin3.io/"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/a/164689011/okwtf"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://www.blendermarket.com/products/CURVEmachine?ref=1051"

        row = column.split(factor=0.3, align=True)
        row.scale_y = 1.2
        row.label(text="HyperCursor", icon_value=installed if hypercursor else missing)
        row.operator("wm.url_open", text="Youtube Playlist, Pre-Release available on Patreon", icon='URL').url = "https://www.youtube.com/playlist?list=PLcEiZ9GDvSdWs1w4ZrkbMvCT2R4F3O9yD"

        box = layout.box()
        box.label(text="Documentation")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Docs", icon='INFO').url = "https://machin3.io/DECALmachine/docs"
        row.operator("wm.url_open", text="Youtube", icon_value=get_icon('youtube')).url = "https://www.youtube.com/playlist?list=PLcEiZ9GDvSdWiU2BPQp99HglGGg1OGiHs"
        row.operator("wm.url_open", text="FAQ", icon='QUESTION').url = "https://machin3.io/DECALmachine/docs/faq"
        row.operator("machin3.get_decalmachine_support", text="Get Support", icon='GREASEPENCIL')

        box = layout.box()
        box.label(text="Discussion")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Blender Artists", icon_value=get_icon('blenderartists')).url = "https://blenderartists.org/t/decalmachine/688181"

        box = layout.box()
        box.label(text="Follow my work")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator("wm.url_open", text="MACHINƎ.io", icon='WORLD').url = "https://machin3.io"
        row.operator("wm.url_open", text="Twitter", icon_value=get_icon('twitter')).url = "https://twitter.com/machin3io"
        row.operator("wm.url_open", text="Artstation", icon_value=get_icon('artstation')).url = "https://artstation.com/machin3"
        row.operator("wm.url_open", text="Patreon", icon_value=get_icon('patreon')).url = "https://patreon.com/machin3"

    def draw_decal_resources(self, layout):
        column = layout.column()

        row = column.row()
        row.scale_y = 16
        row.operator("wm.url_open", text="Get More Decals", icon='URL').url = "https://machin3.io/DECALmachine/docs/decal_resources"
