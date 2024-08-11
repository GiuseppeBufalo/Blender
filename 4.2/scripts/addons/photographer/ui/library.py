import bpy, os, bpy.utils.previews
from .. constants import (
    addon_name,
    photographer_folder,
    HDR_FORMATS,
    SDR_FORMATS,
    IES_FORMATS,
)
from ..functions import show_message
from subprocess import run
from time import sleep

preview_collections = {}
subfolders_enum = []

def subfolders_return(self,context):
    # print (subfolders_enum)
    return subfolders_enum


def scan_for_elements(path,type):
    if type in {'hdri', 'stmap'}:
        if path.lower().endswith(HDR_FORMATS):
            return (path, True)
        else:
            return None
    elif type == 'ies':
        if path.lower().endswith(IES_FORMATS):
            return (path, True)
        else:
            return None
    elif type in {'bokeh','gobo'}:
        if path.lower().endswith(SDR_FORMATS) or path.lower().endswith(HDR_FORMATS):
            return (path, True)
        else:
            return None
    else:
        if path.lower().endswith(SDR_FORMATS):
            return (path, True)
        else:
            return None


def gen_thumbnails(image_paths, enum_items, pcoll):
    empty_path = os.path.join(os.path.dirname(__file__), 'empty.png')
    needs_thumb_path = os.path.join(os.path.dirname(__file__), 'needs_thumb.png')
    # For each image in the directory, load the thumb
    # unless it has already been loaded
    for i, im in enumerate(sorted(image_paths)):
        filepath, prev = im
        name = os.path.splitext(os.path.basename(filepath))[0]
        name = name.replace('.', ' ').replace('_', ' ').lower().capitalize()
        if filepath in pcoll:
            enum_items.append((filepath, name,
                               "", pcoll[filepath].icon_id, i))
        else:
            if prev:
                imgpath = filepath
                if filepath.endswith(HDR_FORMATS):
                    png = os.path.splitext(filepath)[0]+'.png'
                    thumb = thumbnail_path(filepath)
                    if os.path.exists(thumb):
                        imgpath = thumb
                    else:
                        imgpath = png

                    if not os.path.exists(imgpath):
                        if os.stat(filepath).st_size <100000000:
                            imgpath = filepath
                        else:
                            imgpath = needs_thumb_path
                elif filepath.endswith(IES_FORMATS):
                    thumb = thumbnail_path(filepath)
                    if os.path.exists(thumb):
                        imgpath = thumb
                    if not os.path.exists(imgpath):
                        imgpath = needs_thumb_path
                        
                thumb = pcoll.load(filepath, imgpath, 'IMAGE')
            else:
                thumb = pcoll.load(filepath, empty_path, 'IMAGE')
            enum_items.append((filepath, name,
                               "", thumb.icon_id, i))
    return enum_items


def list_subfolders():
    prefs = bpy.context.preferences.addons[addon_name].preferences
    if prefs.hdri_lib_path:
        folder = bpy.path.abspath(prefs.hdri_lib_path)
        subfolders_enum.append(('.','- Base Folder -',''))
        subfolders = [ f.path for f in os.scandir(folder) if f.is_dir() ]
        for s in subfolders:
            files = [f for f in os.listdir(s) if os.path.isfile(os.path.join(s, f)) and f.endswith(HDR_FORMATS)]
            if files:
                folder_name = os.path.basename(s)
                subfolders_enum.append((folder_name, folder_name, ''))


def hdri_lib_path_update(self,context):
    subfolders_enum.clear()
    list_subfolders()
    # Refresh Thumbnails
    previews_unregister()
    previews_register()


def enum_previews_from_directory_items(self, context, type):
    pcoll = preview_collections["main"]
    prefs = context.preferences.addons[addon_name].preferences

    if type == 'bokeh':
        directory = bpy.path.abspath(prefs.bokeh_lib_path)
    elif type == 'opt_vignetting':
        directory = bpy.path.abspath(prefs.opt_vignetting_lib_path)
    elif type == 'gobo':
        directory = bpy.path.abspath(prefs.gobo_lib_path)
    elif type == 'ies':
        directory = bpy.path.abspath(prefs.ies_lib_path)
    elif type == 'stmap':
        directory = bpy.path.abspath(prefs.stmap_lib_path)
    elif type == 'film_grain':
        directory = bpy.path.abspath(prefs.film_grain_lib_path)
    elif type == 'hdri':
        directory = bpy.path.abspath(prefs.hdri_lib_path)
        category = context.scene.lightmixer.hdri_category
        if category != ('.', '-Base Folder-',''):
            directory = os.path.join(directory, category)

    empty_path = os.path.join(os.path.dirname(__file__), 'empty.png')
    enum_items = []

    if context is None:
        return enum_items
    # wm = context.window_manager
    if directory == pcoll.library_prev_dir:
        return pcoll.library_prevs

    if directory and os.path.exists(directory):
        image_paths = []
        for fn in os.listdir(directory):
            prev = scan_for_elements(os.path.join(directory, fn),type)
            if prev:
                image_paths.append(prev)

        enum_items = gen_thumbnails(image_paths, enum_items, pcoll)

    # Return validation
    if len(enum_items) == 0:
        if 'empty' in pcoll:
            enum_items.append(('empty', '',
                               "", pcoll['empty'].icon_id, 0))
        else:
            empty = pcoll.load('empty', empty_path, 'IMAGE')
            enum_items.append(('empty', '', '', empty.icon_id, 0))
    pcoll.library_prevs = enum_items
    pcoll.library_prev_dir = directory

    return pcoll.library_prevs

def thumbnail_path(hdri):
    path, file = os.path.split(hdri)
    thumbnail_path = os.path.join(path,"_thumbnails/")+os.path.splitext(file)[0]+".png"
    return thumbnail_path

# def thumbnail_path(image):
#     path, file = os.path.split(image)
#     thumbnail_folder = os.path.join(path,"_thumbnails")
#     thumbnail_path = os.path.join(thumbnail_folder,os.path.splitext(file)[0]+".png")
#     return thumbnail_path

class LIGHTMIXER_OT_hdri_thumb_gen(bpy.types.Operator):
    "Creates small PNG thumbnails next to your HDRI files"
    bl_idname = 'lightmixer.generate_hdri_thumbs'
    bl_label = 'Generate Missing Thumbnails'
    bl_options = {'INTERNAL'}

    size_limit = 100

    include_small_hdris: bpy.props.BoolProperty(
        name="Include all HDRIs for faster menus",
        description=("Disable to only generate thumbnails "
                    "for HDRIs larger than " + str(size_limit) + "MB"),
        default=True
    )

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.label(text="Will create small PNGs next to the HDRIs, if missing.")
        col.label(text="This may take a few minutes.")

        col.separator()
        col = layout.column(align=True)
        col.prop(self, 'include_small_hdris')

    def generate_thumb(self, hdri):
        thumb = thumbnail_path(hdri)
        cmd = [bpy.app.binary_path]
        cmd.append("--background")
        cmd.append("--factory-startup")
        cmd.append("--python")
        cmd.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "thumbnail_resize.py"))
        cmd.append('--')
        cmd.append(hdri)
        cmd.append('200')
        cmd.append(thumb)
        run(cmd)

    def execute(self, context):
        prefs = context.preferences.addons[addon_name].preferences
        lib_path = prefs.hdri_lib_path

        hdris = []
        thumbnails = []
        small_hdris = []

        # List HDRIs in Library folder
        for root, dirs, files in os.walk(lib_path):
            for f in files:
                if f.endswith(HDR_FORMATS):
                    hdris.append(os.path.join(root, f))

        # Remove HDRIs that already have a PNG thumbnail
        for h in hdris:
            png = os.path.splitext(h)[0]+'.png'
            if os.path.exists(png):
                thumbnails.append(h)

            thumb = thumbnail_path(h)
            if os.path.exists(thumb):
                thumbnails.append(h)
        hdris = set(hdris) - set(thumbnails)

        # Remove HDRIs under 100 MB to only fix Missing Previews
        if not self.include_small_hdris:
            for h in hdris:
                if os.stat(h).st_size <100000000:
                    small_hdris.append(h)
            hdris = set(hdris) - set(small_hdris)

        # print (hdris)

        if not hdris:
            show_message("No missing thumbnails, the HDRI menu should be faster!")
            return {'FINISHED'}

        # Refresh Thumbnails
        previews_unregister()
        previews_register()

        threaded = True  # Set to False for debugging

        errors = []
        if threaded:
            from concurrent.futures import ThreadPoolExecutor
            executor = ThreadPoolExecutor(max_workers=8)
            threads = []
            for i, h in enumerate(hdris):
                t = executor.submit(self.generate_thumb, h)
                threads.append(t)

            while (any(t._state != "FINISHED" for t in threads)):
                num_finished = 0
                for tt in threads:
                    if tt._state == "FINISHED":
                        num_finished += 1
                        if tt.result() is not None:
                            errors.append(tt.result())
                sleep(2)
        else:
            for num_finished, h in enumerate(hdris):
                self.generate_thumb(h)

        if errors:
            for e in errors:
                print(e)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class LIGHTMIXER_OT_ies_thumb_gen(bpy.types.Operator):
    "Creates small PNG thumbnails next to your IES profiles"
    bl_idname = 'lightmixer.generate_ies_thumbs'
    bl_label = 'Generate IES profiles Thumbnails'
    bl_options = {'INTERNAL'}

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.label(text="Will create PNG thumbnails to preview IES profiles.")
        col.label(text="This may take a few minutes.")

    def generate_thumb(self, ies):
        thumb = thumbnail_path(ies)
        cmd = [bpy.app.binary_path]
        blends_folder = os.path.join(photographer_folder,"blends")
        cmd.append(os.path.join(blends_folder,"ies_thumbnail.blend"))
        cmd.append("--background")
        cmd.append("--python")
        cmd.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ies_thumbnail.py"))
        cmd.append('--')
        cmd.append(ies)
        cmd.append('200')
        cmd.append(thumb)
        print(cmd)
        run(cmd)

    def execute(self, context):
        prefs = context.preferences.addons[addon_name].preferences
        lib_path = prefs.ies_lib_path

        ies_profiles = []
        thumbnails = []

        # List IES in Library folder
        for root, dirs, files in os.walk(lib_path):
            for f in files:
                if f.endswith(IES_FORMATS):
                    ies_profiles.append(os.path.join(root, f))

        # Remove IES that already have a PNG thumbnail
        for ies in ies_profiles:
            png = os.path.splitext(ies)[0]+'.png'
            if os.path.exists(png):
                thumbnails.append(ies)

            thumb = thumbnail_path(ies)
            if os.path.exists(thumb):
                thumbnails.append(ies)
        ies_profiles = set(ies_profiles) - set(thumbnails)

        if not ies_profiles:
            show_message("No missing thumbnails")
            return {'FINISHED'}

        # Refresh Thumbnails
        previews_unregister()
        previews_register()

        threaded = True  # Set to False for debugging

        errors = []
        if threaded:
            from concurrent.futures import ThreadPoolExecutor
            executor = ThreadPoolExecutor(max_workers=8)
            threads = []
            for i, ies in enumerate(ies_profiles):
                t = executor.submit(self.generate_thumb, ies)
                threads.append(t)

            while (any(t._state != "FINISHED" for t in threads)):
                num_finished = 0
                for tt in threads:
                    if tt._state == "FINISHED":
                        num_finished += 1
                        if tt.result() is not None:
                            errors.append(tt.result())
                sleep(2)
        else:
            for num_finished, ies in enumerate(ies_profiles):
                self.generate_thumb(ies)

        if errors:
            for e in errors:
                print(e)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

classes = (
    LIGHTMIXER_OT_hdri_thumb_gen,
    LIGHTMIXER_OT_ies_thumb_gen,
)

def previews_register():
    pcoll = bpy.utils.previews.new()
    pcoll.library_prev_dir = ""
    pcoll.library_prevs = ""

    preview_collections["main"] = pcoll

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    previews_register()
    list_subfolders()

def previews_unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

def unregister():
    previews_unregister()
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
