
#bunch of function that i store here because i do not know where to store them 

import bpy 

from . event_utils import get_event
from .. resources.translate import translate


def dprint(string, depsgraph=False,):
    """debug print"""

    addon_prefs=bpy.context.preferences.addons["Geo-Scatter"].preferences 

    if ((not addon_prefs.debug_depsgraph) and depsgraph):
        return None
    if (addon_prefs.debug):
        print(string)

    return None

flagdic = {}
def timer(msg="", init=False):
    """timer decorator"""

    #get modules
    global flagdic, flagcount
    import time, datetime

    #launch timer
    if (init==True):
        print("TimerInit")
        flagdic = {}
        flagdic[0] = time.time()
    else: 
        i=1
        while i in flagdic:
            i+=1
        flagdic[i] = time.time()
        totdelay = datetime.timedelta(seconds=flagdic[i]-flagdic[0]).total_seconds()
        lasdelay = datetime.timedelta(seconds=flagdic[i]-flagdic[i-1]).total_seconds()

        print(f"Timer{i:02} ||| Total: {totdelay:.2f}s ||| FromLast: {lasdelay:.2f}s ||| '{msg}'")
    
    return None


def all_3d_viewports():
    """return generator of all 3d view space"""

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if (area.type=="VIEW_3D"):
                for space in area.spaces:
                    if (space.type=="VIEW_3D"):
                        yield space


def all_3d_viewports_shading_type():
    """return generator of all shading type str"""

    for space in all_3d_viewports():
        yield space.shading.type


def is_rendered_view():
    """check if is rendered view in a 3d view somewhere"""

    return 'RENDERED' in all_3d_viewports_shading_type()

#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_property_toggle(bpy.types.Operator):
    """useful for some cases where we don't want to register an undo when we toggle a bool property"""
    #DO NOT REGISTER TO UNDO ON THIS OPERATOR, GOAL IS TO IGNORE UNDO WHEN CHANGING A PROP

    bl_idname      = "scatter5.property_toggle"
    bl_label       = ""
    bl_description = ""    

    api : bpy.props.StringProperty()
    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):

        if (self.api==""):
            return {'FINISHED'}

        addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
        scat_ui     = bpy.context.window_manager.scatter5.ui
        scat_scene  = bpy.context.scene.scatter5
        emitter     = scat_scene.emitter 
        psy_active  = emitter.scatter5.get_psy_active() if emitter else None
            
        subset_prop = self.api.split('.')[-1]

        #toggle via exec, not sure it's possible to use get/set here
        exec(f'{self.api} = not {self.api}')

        return {'FINISHED'}


class SCATTER5_OT_dummy(bpy.types.Operator):
    """dummy place holder"""

    bl_idname      = "scatter5.dummy"
    bl_label       = ""
    bl_description = ""

    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):
        return {'FINISHED'}

        
class SCATTER5_OT_exec_line(bpy.types.Operator):
    """quickly execute simple line of code, witouth needing to create a new operator"""

    bl_idname      = "scatter5.exec_line"
    bl_label       = ""
    bl_description = ""

    api : bpy.props.StringProperty()
    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    undo : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):

        #useful namespace
        import random 
        C,D           = bpy.context, bpy.data
        addon_prefs   = bpy.context.preferences.addons["Geo-Scatter"].preferences
        scat_scene    = bpy.context.scene.scatter5
        scat_ops      = scat_scene.operators
        emitter       = scat_scene.emitter
        scat_win      = bpy.context.window_manager.scatter5
        psys          = emitter.scatter5.particle_systems if (emitter is not None) else []
        psys_sel      = emitter.scatter5. get_psys_selected() if (emitter is not None) else []
        psy_active    = emitter.scatter5.get_psy_active() if (emitter is not None) else None
        group_active  = emitter.scatter5.get_group_active() if (emitter is not None) else None

        #exec_line
        exec(self.api)

        #write undo?
        if (self.undo!=""):
            bpy.ops.ed.undo_push(message=self.undo, )

        return {'FINISHED'}


class SCATTER5_OT_set_solid_and_object_color(bpy.types.Operator):

    bl_idname      = "scatter5.set_solid_and_object_color"
    bl_label       = ""
    bl_description = translate("Set the context viewport shading type to solid/object to see the particle systems colors")

    mode : bpy.props.StringProperty() #"set"/"restore"
    
    restore_dict = {}

    def execute(self, context):

        space_data = bpy.context.space_data 
        spc_hash   = hash(space_data)
        shading    = space_data.shading

        if (self.mode=="set"):

            self.restore_dict[spc_hash] = {"type":shading.type, "color_type":shading.color_type}
            shading.type = 'SOLID'
            shading.color_type = 'OBJECT'

        elif ((self.mode=="restore") and (spc_hash in self.restore_dict)):

            shading.type = self.restore_dict[spc_hash]["type"]
            shading.color_type = self.restore_dict[spc_hash]["color_type"]
            del self.restore_dict[spc_hash]

        return {'FINISHED'}


class SCATTER5_OT_image_utils(bpy.types.Operator):
    """operator used to quickly create or paint images, with mutli-surface support, for the active psy or active group context or else
    due to the nature of the geoscatter multi-surface workflow, this tool will set up a painting mode on many objects simultaneously"""

    bl_idname  = "scatter5.image_utils"
    bl_label   = translate("Create a New Image")
    bl_options = {'REGISTER', 'INTERNAL'}

    img_name : bpy.props.StringProperty(name=translate("Image Name"), options={"SKIP_SAVE",},)    
    option : bpy.props.StringProperty() #enum in "open"/"new"/"paint"
    api : bpy.props.StringProperty()
    paint_color : bpy.props.FloatVectorProperty()
    uv_ptr : bpy.props.StringProperty(default="UVMap", options={"SKIP_SAVE",},)
    
    context_surfaces : bpy.props.StringProperty(default="*PSY_CONTEXT*", options={"SKIP_SAVE",},)

    #new dialog 
    res_x : bpy.props.IntProperty(default=1080, name=translate("resolution X"), options={"SKIP_SAVE",},)
    res_y : bpy.props.IntProperty(default=1080, name=translate("resolution Y"), options={"SKIP_SAVE",},)
    quitandopen : bpy.props.BoolProperty(default=False,name=translate("Open From Explorer"), options={"SKIP_SAVE",},)
    
    #open dialog
    filepath : bpy.props.StringProperty(subtype="DIR_PATH")

    def __init__(self):
        """store surfaces target"""
        
        #find surfaces automatically depending on group/psy interface context
        if (self.context_surfaces=="*PSY_CONTEXT*"):
            
            #get active psy, or group
            emitter = bpy.context.scene.scatter5.emitter
            itm = emitter.scatter5.get_psy_active()
            if (itm is None):
                itm = emitter.scatter5.get_group_active()
            
            #get their surfaces
            self.surfaces = itm.get_surfaces()
            
        #find surfaces simply using the active emitter
        elif (self.context_surfaces=="*EMITTER_CONTEXT*"):
            self.surfaces = [bpy.context.scene.scatter5.emitter]
            
        #custom surface context
        else: 
            self.surfaces = [ bpy.data.objects[sn] for sn in self.context_surfaces.split("_!#!_") ]
        
        return None 

    @classmethod
    def description(cls, context, properties): 

        if (properties.option=="paint"):
            return translate("Start Painting")

        if (properties.option=="open"):
            return translate("Load Image File from Explorer")

        if (properties.option=="new"):
            return translate("Create Image Data")

        return ""

    def invoke(self, context, event):

        if (self.option=="paint"):
            self.execute(context)
            return {'FINISHED'}

        if (self.option=="open"):
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}  

        if (self.option=="new"):
            self.img_name="ImageMask"
            return context.window_manager.invoke_props_dialog(self)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        
        layout.use_property_split = True
        layout.prop(self,"res_x")
        layout.prop(self,"res_x")
        layout.prop(self,"img_name")
        layout.prop(self,"quitandopen")     

        return None 

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter 
            
        if (self.option=="paint"):

            #get img
            img = bpy.data.images.get(self.img_name)
            if (img is None):
                return {'FINISHED'}
            
            #need to set an object as active
            o = bpy.context.object
            if (o not in self.surfaces):
                for o in self.surfaces:
                    if (self.uv_ptr in o.data.uv_layers):
                        bpy.context.view_layer.objects.active = o
                        break      
                    
            #sett all uvlayers active
            for o in self.surfaces:
                for l in o.data.uv_layers:
                    if (l.name==self.uv_ptr):
                        o.data.uv_layers.active = l
                        
            #enter mode and set up tools settings
            bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
            tool_sett = bpy.context.scene.tool_settings
            tool_sett.image_paint.mode = 'IMAGE'
            tool_sett.image_paint.canvas = img
            tool_sett.unified_paint_settings.color = self.paint_color
            
            return {'FINISHED'}

        if (self.quitandopen):
            bpy.ops.scatter5.image_utils(('INVOKE_DEFAULT'), option="open", img_name=self.img_name, api=self.api,)
            return {'FINISHED'}

        if (self.option=="open"):
            img = bpy.data.images.load(filepath=self.filepath)
            exec( f"{self.api}=img.name" )
            return {'FINISHED'}

        if (self.option=="new"):
            img = bpy.data.images.new(self.img_name, self.res_x, self.res_y,)
            exec( f"{self.api}=img.name" )
            return {'FINISHED'}

        return {'FINISHED'}


class SCATTER5_OT_make_asset_library(bpy.types.Operator):

    bl_idname      = "scatter5.make_asset_library"
    bl_label       = translate("Mark all objects of .blends in the chosen folder as assets")
    bl_description = translate("Mark all objects of .blends in the chosen folder as assets.\n\nNested folder are not supported. Please do not run this operator from a blend file located in the folder you want to process. Please use this operator carefully, the result cannot be undone. Do not use this operator from an unsaved blend file.`\n\nOpen the console window to see progress.")

    directory : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) 
    recursive : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    
    # TODO:
    #-ADD CONFIRM DIALOGBOX: 
    #   "This process will restart your blender session, are you sure that you want to continue" "OK"
    #    Overall confirm boxes are shit to implement if invoke is already being used, perhaps we'd need a ConfirmOperator generic class, that would be nice!
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):

        import os
        import platform
        import functools
        import numpy as np
        
        # some checks..
        if (not os.path.exists(self.directory)):
            # raise Exception("The path you gave us do not exists?")
            self.report({'ERROR'}, "The path you gave us do not exists?")
            return {'FINISHED'}
        
        if (not os.path.isdir(self.directory)):
            # raise Exception("The path you gave us is not a directory?")
            self.report({'ERROR'}, "The path you gave us is not a directory?")
            return {'FINISHED'}
        
        print("\nStarting the conversion:")
        
        def log(msg, indent=0, prefix='>', ):
            m = "{}{} {}".format("    " * indent, prefix, msg, )
            print(m)
        
        # collect paths to blends in directory
        def collect():
            paths = []
            for root, ds, fs in os.walk(self.directory):
                for f in fs:
                    if(f.endswith('.blend')):
                        p = os.path.join(self.directory, root, f)
                        paths.append(p)
                
                if(not self.recursive):
                    break
            
            return paths
        
        def activate_textures():
            include = ('diffuse', 'albedo', )
            
            def do_mat(mat, ):
                # AI grade if-tree!
                if(mat.use_nodes):
                    nt = mat.node_tree
                    if(nt is not None):
                        ns = nt.nodes
                        for n in ns:
                            n.select = False
                        for n in ns:
                            if(n.type == 'TEX_IMAGE'):
                                im = n.image
                                if(im is not None):
                                    p = im.filepath
                                    if(p != ""):
                                        a = bpy.path.abspath(p)
                                        h, t = os.path.split(a)
                                        s = t.lower()
                                        for i in include:
                                            if(i in s):
                                                n.select = True
                                                ns.active = n
                                                return
            
            for mat in bpy.data.materials:
                do_mat(mat)
        
        # periodical check if all previews are created
        def check(p, paths, assets, callback, ):
            if(bpy.app.is_job_running('RENDER_PREVIEW')):
                # NOTE: is something is rendering, skip to next timer run so i don't hit something out of main thread.. (well, i hope..)
                log('preview render job is running..', 1)
                return 1.0
            
            while assets:
                ok = False
                if(isinstance(assets[0], bpy.types.Object)):
                    if(assets[0].type in ('MESH', )):
                        ok = True
                if(not ok):
                    log('skipping: {}'.format(assets[0]))
                    assets.pop(0)
                
                preview = assets[0].preview
                if(preview is None):
                    assets[0].asset_generate_preview()
                    return 0.2
                
                a = np.zeros((preview.image_size[0] * preview.image_size[1]) * 4, dtype=np.float32, )
                preview.image_pixels_float.foreach_get(a)
                if(np.all((a == 0))):
                    assets[0].asset_generate_preview()
                    return 0.2
                else:
                    assets.pop(0)
            
            if(not dry_run):
                log('save: {}'.format(p), 1)
                bpy.ops.wm.save_as_mainfile(filepath=p, compress=True, )
            else:
                log('save: dry_run = True, skipping!', 1)
            
            callback(paths, )
            return None
        
        # run recursively on all blends
        def run(paths, ):
            if(not len(paths)):
                bpy.ops.wm.read_homefile()
                log('-' * 100)
                log('all done!')
                
                on_all_done()
                
                return
            
            log('-' * 100)
            
            p = paths.pop()
            log('open: {}'.format(p))
            
            bpy.ops.wm.open_mainfile(filepath=p, )
            
            activate_textures()
            
            assets = []
            for o in bpy.data.objects:
                o.asset_mark()
                o.preview_ensure()
                # o.asset_generate_preview()
                assets.append(o)
            
            log('assets: {}'.format(assets), 1)
            
            log('processing..', 1)
            bpy.app.timers.register(
                functools.partial(check, p, paths, assets, run, )
            )
        
        # callback when all is done
        def on_all_done():
            #add path if not loaded yet?
            if (os.path.realpath(directory) not in [os.path.realpath(l.path) for l in context.preferences.filepaths.asset_libraries]):
                print("It seems that you did not register this library in your file paths?")
                print("let us do this process for you")
                bpy.ops.preferences.asset_library_add(directory=directory, )
                # NOTE: save preferences after or on blender restart will be lost
                bpy.ops.wm.save_userpref()
            
            print("Conversion finished!")
            
            # read default scene
            bpy.ops.wm.read_homefile()
            
            def delayed_call():
                bpy.ops.scatter5.popup_dialog(
                    'INVOKE_DEFAULT',
                    msg=translate("All files have been processed.\nDirectory has been added to your Asset-Library paths.\n"),
                    header_title=translate("Conversion Done!"),
                    header_icon="CHECKMARK",
                )
            
            bpy.app.timers.register(delayed_call, first_interval=0.1, )
        
        dry_run = False
        paths = collect()
        # NOTE: at the time `run` finishes, self will no longer be available because operator ended just after `run` was called, keep that in local vars
        directory = self.directory
        
        log('-' * 100)
        log('paths:')
        for p in paths:
            log(p, 1)
        log('-' * 100)
        
        run(paths)
        
        # NOTE: nothing should be called after `run` because it will be executed before `run` finishes, use `on_all_done` callback to do some work after conversion
        
        return {'FINISHED'}


classes = (
        
    SCATTER5_OT_property_toggle,
    SCATTER5_OT_dummy,
    SCATTER5_OT_exec_line,

    SCATTER5_OT_set_solid_and_object_color,
    SCATTER5_OT_image_utils,
    
    SCATTER5_OT_make_asset_library,

    )