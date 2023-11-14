import bpy, os, subprocess, addon_utils
from bpy_extras.io_utils import ImportHelper
from .constants import addon_name
from .functions import has_keyframe, traverse_tree, list_collections, keyframe_node_param
from sys import platform as _platform
from bpy.props import  PointerProperty
from .operators.exposure import get_exposure_node
from .operators.light_material import (
    light_tex_controls_grp_name,
    gobo_mapping_name,
    gobo_mapping_area_name,
    gobo_tangent_name,
    gobo_mult_scale_name,
    gobo_mult_scale_y_name,
    falloff_name,
)

fp_token_items = [
    ('$blend','Blend File','Replaces with Blend file name',0),
    ('$scene','Scene','Replaces with Scene name',1),
    ('$world','World','Replaces with World name',2),
    ('$camera','Camera','Replaces with Active Camera name',3),
    ('$denoise','Denoise','Adds Denoised if enabled',4),
    ('$samples','Min Samples','Adds Max Samples if enabled',5),
    ('$noisethreshold','Noise Threshold','Adds Noise Threshold if enabled',6),
]

def turbo_render_enabled(context):
    # Adding support for Turbo Tools render operators
    is_tt_enabled,is_tt_loaded = addon_utils.check('Turbo Tools')
    if is_tt_loaded:
        if context.scene.Turbo_Render:
            print ("Photographer Render Queue: Turbo Render enabled, using add-on render commands")
            return True

def get_fo_nodes(scene,fo_nodes, file_outputs):
    if scene.node_tree:
        nodes = scene.node_tree.nodes
        outputs = [n for n in nodes if n.bl_idname == 'CompositorNodeOutputFile']
        for n in outputs:
            fo_nodes.append(n)
            for file in n.file_slots:
                file_outputs.append((file,file.path))
    return fo_nodes, file_outputs

def overwrite_fo_nodes_output(scene,fo_nodes,shot,fpath,prefix):
    for n in fo_nodes:
        base_path = fpath
        if not fpath.endswith('/'):
            base_path = fpath.split(prefix)[0]
        n.base_path = base_path
        if scene.renderqueue.use_folder:
            n.base_path += shot + '/'
        print ("File output overriden with: " + n.base_path)

def bump_render_slot(context):
    scene = context.scene
    # Bump Render Slot
    if scene.renderqueue.incremental_slot and scene.renderqueue.frame_mode == 'STILL':
        if [i for i in bpy.data.images if i.name=='Render Result']:
            render_result = bpy.data.images['Render Result']
            if render_result.has_data:
                slot = render_result.render_slots.active_index
                slot += 1
                slot %= 8
                render_result.render_slots.active_index = slot

def get_cameras(context,mode):
    scene = context.scene

    collections = list_collections(context)
    colls = []
    for coll in collections:
        lc = [lc for lc in traverse_tree(context.view_layer.layer_collection)
        if lc.name == coll.name and not lc.exclude]
        # print (lc)
        if lc:
            colls.append(coll)

    cameras = []
    for coll in colls:
            cams=[cam for cam in coll.objects if cam.type=='CAMERA' and not coll.hide_render]
            for c in cams:
                cameras.append(c)

    if mode == 'ACTIVE':
        shots = [ o.name+'' for o in cameras if o == scene.camera]
    elif mode == 'SELECTED':
        shots = [ o.name+'' for o in cameras if o.select_get()]
    else:
        shots = [ o.name+'' for o in cameras if o.data.photographer.renderable == True ]
    return shots

def set_renderfilepath(context,shot,filepath,increment):

    scene = context.scene

    for token in fp_token_items:
        if token[0] in filepath:
            if token[0] == '$blend':
                if bpy.context.blend_data.is_saved:
                    blend_name = bpy.path.basename(bpy.context.blend_data.filepath).replace(".blend","")
                    filepath = filepath.replace(token[0],blend_name)
                else:
                    filepath = filepath.replace(token[0],"untitled")
            if token[0] == '$scene' and context.scene:
                filepath = filepath.replace(token[0],context.scene.name)
            if token[0] == '$world' and context.scene.world:
                filepath = filepath.replace(token[0],context.scene.world.name)
            if token[0] == '$camera' and context.scene.camera:
                filepath = filepath.replace(token[0],context.scene.camera.name)
            if token[0] == '$denoise' and context.scene.render.engine == 'CYCLES':
                if context.scene.cycles.use_denoising:
                    filepath = filepath.replace(token[0],'denoised')
            if token[0] == '$samples' and context.scene.render.engine == 'CYCLES':
                filepath = filepath.replace(token[0],str(context.scene.cycles.samples))
            if token[0] == '$noisethreshold' and context.scene.render.engine == 'CYCLES':
                if context.scene.cycles.use_adaptive_sampling:
                    filepath = filepath.replace(token[0], str(round(context.scene.cycles.adaptive_threshold,3)))                
            # if token[0] == '$viewlayer':
                # filepath = filepath.replace(token[0],context.view_layer.name)
    
    # Replace Spaces with Underscores
    # filepath = filepath.replace(' ', '_')

    fpath = filepath.replace(os.path.sep, '/')
    numbers = "001"

    # Check if Path is relative
    if fpath[:2] == "//":
        lpath = bpy.path.abspath(fpath)
    else:
        lpath = fpath

    # If path doesn't end with /, take the last name as a prefix
    if not lpath == '//' and lpath.endswith('/'):
        prefix = lpath.rpartition('/')[-1]
        if prefix:
            lpath = lpath.split(prefix)[0]
    else:
        prefix = ''

    # Filename
    fname = prefix + shot

    # If using Folder structure
    if scene.renderqueue.use_folder:
        # Add folder with camera name
        lpath += shot + '/'
        # Use Prefix as file name
        fname = prefix

        # Use Camera name to avoid file with no name
        if fname == '':
            if scene.renderqueue.frame_mode == 'STILL':
                if not scene.renderqueue.incremental:
                    fname = shot
            if scene.renderqueue.frame_mode == 'ANIM':
                fname = shot

    if lpath=="":
        lpath="//"

    rpath = lpath + fname

    if scene.renderqueue.frame_mode == 'ANIM' or scene.renderqueue.background_render:
        rpath += "_"
        scene.render.filepath = rpath
    else:
        rpath += scene.render.file_extension
        scene.render.filepath = rpath

        if increment:
            if fname and not fname.endswith('_'):
                fname += "_"
            # Add _001 to the first incremental render
            scene.render.filepath = lpath + fname + numbers + scene.render.file_extension

            # Reset counter
            counter = 0
            while os.path.exists(scene.render.filepath):
                counter += 1
                numbers = str(counter).zfill(3)
                scene.render.filepath = lpath + fname + numbers + scene.render.file_extension
            rpath = scene.render.filepath

    return (fpath, lpath, fname, numbers, prefix)

def render_buttons(self,context,parent_ui):
    layout = parent_ui
    scene = context.scene
    render = scene.render

    drone_cam = 'DroneCamera'

    active_cam = get_cameras(context,'ACTIVE')
    renderable_cams = get_cameras(context,'')
    selected_cams = get_cameras(context,'SELECTED')

    if not context.preferences.addons[addon_name].preferences.show_compact_ui:
        layout.prop(render, "engine", text='')

    col = layout.column(align=True)
    if active_cam and scene.camera == bpy.data.objects.get(drone_cam):
        col.operator("render.renderqueue",text="Render Drone Camera").mode='ACTIVE'
    else:
        rc_label = " (" + str(len(renderable_cams)) + ")"
        sc_label = " (" + str(len(selected_cams)) + ")"

        col = layout.column(align=True)
        row = col.row(align=True)
        rdr_icn = 'RENDER_ANIMATION' if context.scene.renderqueue.frame_mode == 'ANIM' else 'RENDER_STILL'
        row.operator("render.renderqueue",
                text= 'Render Active Only' if active_cam else 'No Scene Camera',
                icon = rdr_icn).mode='ACTIVE'

        row2 = col.row(align=True)
        row2.operator("render.renderqueue",
                    text= "Render All Enabled" + rc_label,
                    icon='RENDERLAYERS').mode='RENDERABLE'
        row3 = col.row(align=True)
        row3.operator("render.renderqueue",
                    text="Render Selected" + sc_label,
                    icon='RESTRICT_SELECT_OFF').mode='SELECTED'

        if not active_cam:
            row.enabled = False
        if not renderable_cams: # and scene.camera != bpy.data.objects.get(drone_cam):
            row2.enabled = False
        if not selected_cams:
            row3.enabled = False

    col.separator()
    row = col.row(align=True)
    row.prop(scene.renderqueue,'frame_mode', expand=True)
    if scene.renderqueue.frame_mode == 'ANIM':
        row = col.row(align=True)
        row.prop(scene,'frame_start', text = 'Start')
        row.prop(scene,'frame_end', text = 'End')
        # row = col.row(align=True)
        # row.prop(scene,'frame_step', text = 'Step')
        # row.prop(scene.render,'fps')
    else:
        col.prop(scene,'frame_current')

class PHOTOGRAPHER_OT_RenderQueue(bpy.types.Operator):
    """ Render through Render Queue """
    bl_idname = "render.renderqueue"
    bl_label = "Render Queue"

    _timer = None
    shots = None
    stop = None
    rendering = None
    path = "//"
    fpath = "//"
    fo_nodes = []
    file_outputs = []

    mode : bpy.props.EnumProperty(
        name = "Render Queue Mode",
        items = [('ACTIVE','Active',''),('SELECTED','Selected',''),('RENDERABLE','Renderable','')],
        default = 'ACTIVE',
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Do you want to render animations")
        col.label(text="for all renderable cameras?")
        col.label(text="Press ESC to cancel the render at anytime.")

    def pre(self, dummy, thrd = None):
        self.rendering = True

    def post(self, dummy, thrd = None):
        scene = bpy.context.scene
        if scene.renderqueue.frame_mode == 'ANIM':
            if scene.frame_current == scene.frame_end:
                self.shots.pop(0)
                self.rendering = False
                for file in self.file_outputs:
                    file[0].path = file[1]
                bpy.data.scenes.get(scene.name).render.filepath = self.fpath
        else:
            self.shots.pop(0)
            self.rendering = False
            for file in self.file_outputs:
                file[0].path = file[1]
            bpy.data.scenes.get(scene.name).render.filepath = self.fpath
            if self.shots:
                bump_render_slot(bpy.context)

    def cancelled(self, dummy, thrd = None):
        scene = bpy.context.scene
        self.stop = True
        for file in self.file_outputs:
            file[0].path = file[1]
        bpy.data.scenes.get(scene.name).render.filepath = self.fpath

    def execute(self, context):
        self.stop = False
        self.rendering = False
        scene = bpy.context.scene
        wm = bpy.context.window_manager

        self.fo_nodes, self.file_outputs = get_fo_nodes(scene,self.fo_nodes,self.file_outputs)

        self.fpath = scene.render.filepath
        self.shots = get_cameras(context,mode=self.mode)

        if not self.shots:
            self.report({"ERROR"}, "No cameras to render")
            return {"CANCELLED"}

        if bpy.context.scene.render.filepath is None or len(bpy.context.scene.render.filepath)<1:
            self.report({"ERROR"}, 'Output path not defined. Please, define the output path on the render settings panel')
            return {"CANCELLED"}

        animation_formats = [ 'FFMPEG', 'AVI_JPEG', 'AVI_RAW', 'FRAMESERVER' ]
        if bpy.context.scene.render.image_settings.file_format in animation_formats:
            self.report({"ERROR"}, 'Video output formats (AVI, FFMPEG) are not supported. Please use Image file formats instead.')
            return {"CANCELLED"}

        # Background rendering
        if scene.renderqueue.background_render:
            bpy.ops.render.renderqueue_export(
                mode=self.mode,
                increment=scene.renderqueue.incremental,
                )
            if _platform == "darwin":
                subprocess.call(['chmod', '+x', scene.renderqueue.bat_file])
                subprocess.call(['open', '-a', 'Terminal.app', scene.renderqueue.bat_file])
            elif _platform == "linux" or _platform == "linux2":
                subprocess.call(['chmod', '+x', scene.renderqueue.bat_file])

                console_apps = ['konsole','xfce4-terminal', 'mate-terminal','gnome-terminal', 'xterm']
                console = None
                for c in console_apps:
                    # print (subprocess.call(['which', c]))
                    if subprocess.call(['which', c]) == 0:
                        console = c
                        break
                if console is not None:
                    subprocess.call(['chmod', '+x', scene.renderqueue.bat_file])
                    if console == 'gnome-terminal':
                        subprocess.call([console, '--', scene.renderqueue.bat_file])
                    if console == 'mate-terminal':
                        subprocess.call([console, '--command=', scene.renderqueue.bat_file])
                    if console in {'konsole', 'xfce4-terminal', 'xterm'}:
                        subprocess.call([console, '-e', scene.renderqueue.bat_file])
                else:
                    self.report({'ERROR'},'Could not find the Terminal app for this distro.'
                        'Please reach out to request support.')
                    return {'CANCELLED'}

            elif _platform == "win32" or _platform == "win64":
                subprocess.Popen(scene.renderqueue.bat_file, creationflags = subprocess.CREATE_NEW_CONSOLE)
            return {"FINISHED"}

        else:
            bump_render_slot(context)
            bpy.app.handlers.render_pre.append(self.pre)
            bpy.app.handlers.render_post.append(self.post)
            bpy.app.handlers.render_cancel.append(self.cancelled)

            self._timer = bpy.context.window_manager.event_timer_add(0.5, window=bpy.context.window)
            bpy.context.window_manager.modal_handler_add(self)
            
            return {"RUNNING_MODAL"}

    def modal(self, context, event):
        scene = bpy.context.scene
        if event.type == 'TIMER':
            if True in (not self.shots, self.stop is True):
                bpy.app.handlers.render_pre.remove(self.pre)
                bpy.app.handlers.render_post.remove(self.post)
                bpy.app.handlers.render_cancel.remove(self.cancelled)
                bpy.context.window_manager.event_timer_remove(self._timer)                
                return {"FINISHED"}
            
            if self.rendering is False:
                bpy.ops.photographer.look_through(camera = self.shots[0])

                fpath,lpath,fname,numbers,prefix = set_renderfilepath(context,self.shots[0],self.fpath,scene.renderqueue.incremental)

                # Create rendering folder if it doesn't exist
                if not os.path.exists(lpath) and lpath not in {'\\\\','//'}:
                    try:
                        os.makedirs(lpath)
                    except:
                        self.report({'ERROR'}, "Invalid path, the render has been cancelled.")
                        bpy.data.scenes.get(scene.name).render.filepath = self.fpath
                        bpy.app.handlers.render_pre.remove(self.pre)
                        bpy.app.handlers.render_post.remove(self.post)
                        bpy.app.handlers.render_cancel.remove(self.cancelled)
                        bpy.context.window_manager.event_timer_remove(self._timer)    
                        return {"CANCELLED"}

                # File Output nodes support
                # Set File Output base paths to the same Render output path
                if scene.renderqueue.overwrite_file_nodes:
                    overwrite_fo_nodes_output(scene,self.fo_nodes,self.shots[0],fpath,prefix)

                # Rename File Outputs names to match Render output file name
                for file in self.file_outputs:
                    if scene.renderqueue.incremental:
                        file[0].path = fname + numbers + '_' + file[1]
                    else:
                        file[0].path = fname + '_' + file[1]

                if scene.renderqueue.frame_mode == 'ANIM':
                    if turbo_render_enabled(context):
                        bpy.ops.threedi.render_animation()
                    else:
                        bpy.ops.render.render("INVOKE_DEFAULT", animation=True, write_still=True)
                else:
                    if turbo_render_enabled(context):
                        bpy.ops.threedi.render_still(write_still=True)
                    else:
                        bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)

        return {"PASS_THROUGH"}

    def invoke(self, context, event):

        # Check if RenderQueue functions are appended to handlers to determine if it is currently rendering
        if 'PHOTOGRAPHER_OT_RenderQueue' in str(bpy.app.handlers.render_pre):
            self.report({'WARNING'}, "Already rendering, press ESC to cancel the current render.")
            return {'CANCELLED'}
        else:
            if context.scene.renderqueue.frame_mode == 'ANIM' and self.mode =='RENDERABLE':
                return context.window_manager.invoke_props_dialog(self)
            else:
                return self.execute(context)


class PHOTOGRAPHER_OT_RenderQueueButton(bpy.types.Operator):
    bl_idname = "render.renderqueue_button"
    bl_label = "Render Active Camera"
    bl_description = ("Shift-Click to render all enabled cameras.\n"
                    "Ctrl-Click to render all selected cameras")

    def invoke(self, context, event):
        if event.shift:
            mode = 'RENDERABLE'
        elif event.ctrl:
            mode = 'SELECTED'
        else:
            mode = 'ACTIVE'
        
        return bpy.ops.render.renderqueue("INVOKE_DEFAULT",mode=mode)

class PHOTOGRAPHER_OT_BakeProperties(bpy.types.Operator):
    bl_idname = "render.bake_properties"
    bl_label = "Bake Animated properties"
    bl_description = ("Animated Photographer properties are baked into Blender"
                    " properties, to support render farm rendering where machines"
                    " do not have Photographer installed")
    bl_options = {'UNDO'}

    def execute(self,context):

        scene = context.scene
        stored_current = scene.frame_current
        scene.frame_set(frame=scene.frame_start)
        # Animatable Photographer Properties
        # Cameras
        cam_props = ['ev', 'exposure_compensation', 'shutter_speed',
        'shutter_speed_preset', 'shutter_angle', 'shutter_angle_preset',
        'aperture', 'aperture_preset','iso', 'iso_preset', 'focal',
        'fisheye_focal', 'lens_shift'] #,'color_temperature', 'tint']
        anim_cam = [p for p in cam_props if has_keyframe(scene.camera.data,"photographer." + p)]

        pl_props = ['light_type', 'color', 'light_temperature',
        'irradiance', 'illuminance', 'intensity', 'light_exposure', 'power',
        'advanced_power', 'efficacy', 'lumen', 'candela', 'spot_size', 'spread',
        'shape', 'size', 'size_y', 'azimuth', 'elevation', 'gobo_opacity', 'ies_opacity',
        'gobo_scale','gobo_scale_y','gobo_offset_x','gobo_offset_y','light_falloff_smooth']
        light_props = ['type'] # Color and Energy cannot use keyframe_insert
        lights = [l.data for l in context.view_layer.objects if l.type=='LIGHT']
        anim_lights = []
        for l in lights:
            for p in pl_props:
                # print('PL Property: ' + p)
                if has_keyframe(l,"photographer." + p):
                    if l not in anim_lights:
                        anim_lights.append(l)
        # print('Animated lights: ' + str(anim_lights))
        while scene.frame_current <= scene.frame_end:
            bpy.ops.photographer.applyphotographersettings()
            if anim_cam:
                if scene.render.engine == 'CYCLES':
                    scene.render.keyframe_insert(data_path="motion_blur_shutter")
                elif scene.render.engine == 'BLENDER_EEVEE':
                    scene.eevee.keyframe_insert(data_path="motion_blur_shutter")
                if scene.photographer.comp_exposure:
                    exp = get_exposure_node(self,context)
                    if exp:
                        exp.inputs['Exposure'].keyframe_insert(data_path="default_value")
                else:
                    scene.view_settings.keyframe_insert(data_path="exposure")
                scene.camera.data.keyframe_insert(data_path="lens")
                scene.camera.data.keyframe_insert(data_path="shift_x")
                scene.camera.data.keyframe_insert(data_path="shift_y")
                # scene.view_settings.curve_mapping.keyframe_insert(data_path="white_level")

            for l in anim_lights:
                # Baking Photographer Color and Power to work around issue if baking Color and Energy
                # Since properties are linked with the get function,
                # keyframe_insert is not getting the right value
                l.keyframe_insert(data_path="photographer.color")                
                l.keyframe_insert(data_path="photographer.power")

                # Keyframe Light Material nodes
                params = {(gobo_tangent_name,0),
                          (gobo_mult_scale_name, 0),
                          (gobo_mult_scale_y_name,0),
                          (gobo_mapping_area_name,1),
                          (gobo_mapping_area_name,3),
                          (gobo_mapping_name,1),
                          (gobo_mapping_name,3),
                          (light_tex_controls_grp_name,2),
                          (light_tex_controls_grp_name,5),
                          (falloff_name,1),
                          }
                for n, i in params:
                    keyframe_node_param(l,n,i)

                for p in light_props:
                    l.keyframe_insert(data_path=p)
                if l.type == 'SUN':
                    l.id_data.keyframe_insert(data_path="rotation_euler")
                if l.type == 'SPOT':
                    l.keyframe_insert(data_path="spot_size")
                if l.type == 'AREA':
                    l.keyframe_insert(data_path="shape")
                    l.keyframe_insert(data_path="size")
                    l.keyframe_insert(data_path="size_y")

            scene.frame_set(frame=scene.frame_current+1)

        # Copy F-Curves from Photographer Color and Energy to Color and Energy
        for l in anim_lights:
            for fc in l.animation_data.action.fcurves:
                if fc.data_path == "photographer.color":
                    fc.data_path = "color"
                if fc.data_path == "photographer.power":
                    fc.data_path = "energy"

        scene.frame_current = stored_current

        return {'FINISHED'}

class PHOTOGRAPHER_OT_RenderQueueExport(bpy.types.Operator, ImportHelper):
    bl_idname = "render.renderqueue_export"
    bl_label = "Export Render files"
    bl_description = ("Bakes Photographer animations and exports each "
                    "renderable camera to a blend file "
                    "that can be rendered on machines that don't have the "
                    "addon installed. \n"
                    "NOTE: Animated White Balance CANNOT be baked and requires "
                    "the addon for rendering")

    mode : bpy.props.EnumProperty(
        name = "Cameras",
        items = [('ACTIVE','Active',''),('SELECTED','Selected',''),('RENDERABLE','Renderable','')],
        default = 'RENDERABLE',
        description = "Choose which cameras will be exported"
    )
    increment : bpy.props.BoolProperty(
        name = "Increment",
        description = ("Increment Output Image filename if it already exists for the "
        "Command line render. Note that this increment only happens once "
        "at Export. Reusing the same Command Line won't add any increment"),
        default = False,
    )
    bake_anim : bpy.props.BoolProperty(
        name = "Bake Animations",
        description = ("Animated Photographer properties are baked into Blender"
                        " properties, to support render farm rendering where machines"
                        " do not have Photographer installed"),
        default = True,
    )
    export = False

    def execute(self, context):
        scene = context.scene
        # Store render output filepath
        path = scene.render.filepath
        opath = ''

        # No self.filepath = Background rendering
        if self.filepath:
            self.export = True
            # Undo is unreliable, so saving the mainfile and reverting it at the end
            if self.bake_anim:
                if bpy.data.is_saved:
                    bpy.ops.wm.save_as_mainfile()
                else:
                    self.report({'ERROR'}, 'Export failed. Please save your scene first.')
                    return {'CANCELLED'}

        # Get camera names
        shots = get_cameras(context,mode=self.mode)
        if not shots:
            self.report({'ERROR'}, 'Found no camera to export. Choose which cameras to export in the File browser Options panel that opens.')
            return {'CANCELLED'}

        # Fix incorrect slashes like // for relative path instead of \\
        opath = scene.render.filepath = scene.render.filepath.replace(os.path.sep, '/')

        # Retrieve Absolute path
        if opath[:2] == "//":
            opath = bpy.path.abspath(opath)
        else:
            # Real path to support paths without disk letter, like /tmp/
            opath = os.path.realpath(opath)

        # Retrieve directory without prefix
        if not scene.render.filepath.endswith('/'):
            opath = os.path.dirname(opath)

        # # Restore last slash that got lost with Real path
        opath = os.path.join(opath, '')

        # No self.filepath = Background rendering
        if not self.export:
            # Render files folder
            rpath = os.path.join(opath, 'renderfiles')

            fname = bpy.path.basename(bpy.context.blend_data.filepath)
            # Set path and name of the rendered blend file
            self.filepath = os.path.join(rpath, fname)

            # Join will add backslashes on Windows,let's unify them again
            self.filepath.replace(os.path.sep, '/')
            opath.replace(os.path.sep, '/')

            # Create render files folder if it doesn't exist
            if not os.path.exists(rpath):
                try:
                    os.makedirs(rpath)
                except:
                    self.report({'ERROR'}, "Invalid path, the render has been cancelled.")
                    return {"CANCELLED"}

        # Extension based on OS
        if os.name == 'posix':
            ext = '.sh'
        else:
            ext = '.bat'
        # Store Bat file path as string for subprocess
        scene.renderqueue.bat_file = self.filepath + ext

        # Create bat file for Windows
        try:
            bat = open(scene.renderqueue.bat_file,'w+')
            bat.write('#!/bin/bash \n')
        except RuntimeError:
            self.report({'ERROR'},"Incorrect file path, could not export files required"
                        " for Background rendering")
            return {'CANCELLED'}

        for cam in shots:
            # Prepare the Scene before saving it
            bpy.ops.photographer.look_through(camera = cam)

            fpath,lpath,fname,numbers,prefix = set_renderfilepath(context,cam,scene.render.filepath,self.increment)

            if scene.renderqueue.overwrite_file_nodes:
                fo_nodes = []
                file_outputs = []
                fo_nodes,file_outputs = get_fo_nodes(scene,fo_nodes,file_outputs)
                overwrite_fo_nodes_output(scene,fo_nodes,cam,fpath,prefix)

            # Set Blend file name for each camera
            if self.filepath.endswith('.blend'):
                fpath = os.path.splitext(self.filepath)[0] + "_" + cam + ".blend"
            else:
                fpath = self.filepath + "_" + cam + ".blend"

            if self.export and self.bake_anim:
                bpy.ops.render.bake_properties()

            # Save Blend file
            bpy.ops.wm.save_as_mainfile(copy=True, filepath=fpath)

            # Restore render output filepath that was set by set_renderfilepath
            scene.render.filepath = path

            # Create command line rendering file
            bat.write('\"' + bpy.app.binary_path + '\"' + ' -b ' + '\"' + fpath + '\"')
            if scene.renderqueue.frame_mode == 'ANIM':
                if turbo_render_enabled(context):
                    bat.write(' --python-expr "import bpy; bpy.ops.threedi.render_animation()"')
                else:
                    bat.write(' -a')
            else:
                if turbo_render_enabled(context):
                    bat.write(' --python-expr "import bpy; bpy.ops.threedi.render_still()"')
                bat.write(' -f ' + str(scene.frame_current))
            bat.write(' \n')

        # Open Explorer where rendered images were saved
        if _platform == "darwin":
            bat.write('open ' + '\"' + opath  + '\" \n')
            bat.write('read -p "Press Enter to close the Terminal..."')
        elif _platform == "linux" or _platform == "linux2":
            bat.write('xdg-open ' + '\"' + opath  + '\" \n')
            bat.write('read -p "Press Enter to close the Terminal..."')
        elif _platform == "win32" or _platform == "win64":
            bat.write('start \"Render Output\" ' + '\"' + opath  + '\" \n')
            bat.write('pause')
        bat.close()

        # Open Explorer where render files were exported
        if self.export:
            if _platform == "darwin":
                os.system("open " + os.path.dirname(self.filepath))
            elif _platform == "linux" or _platform == "linux2":
                os.system("xdg-open " + os.path.dirname(self.filepath))
            elif _platform == "win32" or _platform == "win64":
                os.startfile(os.path.dirname(self.filepath))

            if self.bake_anim:
                # Reverting to main file, before bake
                bpy.ops.wm.revert_mainfile()

        return {'FINISHED'}

class PHOTOGRAPHER_PT_ViewPanel_RenderQueue(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Render Q"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    def draw_header_preset(self, context):
        layout = self.layout
        row = layout.row(align=False)
        row.alignment = 'RIGHT'
        row.scale_x = 0.81
        render = context.scene.render
        if context.preferences.addons[addon_name].preferences.show_compact_ui:
            row.prop(render, "engine", text='')

        sub = layout.row(align=False)
        rdr_icn = 'RENDER_ANIMATION' if context.scene.renderqueue.frame_mode == 'ANIM' else 'RENDER_STILL'
        sub.operator("render.renderqueue_button",text="", icon=rdr_icn, emboss=False)
        sub.scale_x = 1.6

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        render = scene.render

        render_buttons(self,context,layout)

        col = layout.column(align=True)
        col.prop(render, "filepath", text="")

        split = col.split(factor=0.72)
        row = split.row(align=True)
        row.prop(scene.renderqueue, "fp_token", text='')
        tk = row.operator("render.renderqueue_token_add", icon='ADD', text='')
        tk.slash=False
        tk.underscore=False
        row = split.row(align=True)
        us = row.operator("render.renderqueue_token_add", text='_')
        us.slash=False
        us.underscore=True
        sl = row.operator("render.renderqueue_token_add", text='\\')
        sl.slash=True
        sl.underscore=False

        row = col.row(align=True)
        split = row.split(factor = 0.4)
        split.label(text="Incremental:")
        split.prop(scene.renderqueue, "incremental", text="Save")
        split.prop(scene.renderqueue, "incremental_slot", text="Slot")
        if scene.renderqueue.frame_mode == 'ANIM':
            split.enabled = False
        col.prop(scene.renderqueue, "use_folder")
        col.prop(scene.renderqueue, "overwrite_file_nodes")
        col.prop(scene.renderqueue, "background_render")
        col.separator()
        col.operator("render.renderqueue_export", icon='EXPORT')


class PHOTOGRAPHER_PT_ImageEditor_RenderQueue(PHOTOGRAPHER_PT_ViewPanel_RenderQueue):
    bl_space_type = 'IMAGE_EDITOR'

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        return bpy.context.preferences.addons[addon_name].preferences.show_image_panels

class PHOTOGRAPHER_PT_NodeEditor_RenderQueue(PHOTOGRAPHER_PT_ViewPanel_RenderQueue):
    bl_space_type = 'NODE_EDITOR'

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        snode = context.space_data
        return bpy.context.preferences.addons[addon_name].preferences.show_image_panels and snode.tree_type == 'CompositorNodeTree'

class PHOTOGRAPHER_OT_FilePathTokenAdd(bpy.types.Operator):
    bl_idname = "render.renderqueue_token_add"
    bl_label = "Add Token"
    bl_description = ("Adds token to filepath, which will be replaced with corresponding value")
    bl_options = {'UNDO'}

    slash : bpy.props.BoolProperty(default=False)
    underscore : bpy.props.BoolProperty(default=False)

    def execute(self,context):
        scene = context.scene
        if self.slash:
            scene.render.filepath += '\\'
        elif self.underscore:
            scene.render.filepath += '_'
        else:
            scene.render.filepath += scene.renderqueue.fp_token
        # scene = context.scene.name
        # viewlayer = context.view_layer.name
        # camera = context.scene.camera.name
        # world = context.scene.world.name
        # print(scene, viewlayer, camera, world)
        return {'FINISHED'}

class RenderQueueSettings(bpy.types.PropertyGroup):
    incremental : bpy.props.BoolProperty(
        name = "Increment Save",
        description = "Saves each render as a new image file with incremented suffix number",
        options = {'HIDDEN'},
        default = True,
    )
    incremental_slot : bpy.props.BoolProperty(
        name = "Increment Slot",
        description = "Stores new render automatically in the next Render Slot (limited to 8)",
        options = {'HIDDEN'},
        default = True,
    )
    use_folder : bpy.props.BoolProperty(
        name = "Use Folder structure",
        description = "Each Camera will save files in its own folder",
        options = {'HIDDEN'},
        default = False,
    )
    overwrite_file_nodes : bpy.props.BoolProperty(
        name = "Overwrite File Output nodes path",
        description = "Assign the Render Path above to all File Output nodes in Compositing. \n"
        "Will keep all the rendered files in the same location",
        options = {'HIDDEN'},
        default = False,
    )
    frame_mode : bpy.props.EnumProperty(
        name = "Render Mode",
        description = "Render still frame or animation",
        items=[('STILL','Still','Render current frame','RENDER_STILL',0),
        ('ANIM', 'Animation', 'Render Animation according to frame range','RENDER_ANIMATION',1)],
        options = {'HIDDEN'},
        default = 'STILL',
    )
    background_render : bpy.props.BoolProperty(
        name = "Background Render",
        description = "Will start the Render in the background using command line rendering",
        options = {'HIDDEN'},
        default = False,
    )
    bat_file : bpy.props.StringProperty()
    fp_token : bpy.props.EnumProperty(
        name = "File Path Tokens",
        description = "Available tokens to add to render output file path",
        items=fp_token_items,
        options = {'HIDDEN'},
        default = '$camera',
    )


def menu_func(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("render.renderqueue", text='Render Enabled Cameras',icon='RENDERLAYERS').mode='RENDERABLE'
    layout.operator("render.renderqueue", text='Render Selected Cameras',icon='RESTRICT_SELECT_OFF').mode='SELECTED'

classes = (
    PHOTOGRAPHER_OT_RenderQueue,
    PHOTOGRAPHER_OT_RenderQueueButton,
    PHOTOGRAPHER_OT_RenderQueueExport,
    PHOTOGRAPHER_OT_BakeProperties,
    PHOTOGRAPHER_PT_ImageEditor_RenderQueue,
    PHOTOGRAPHER_PT_NodeEditor_RenderQueue,
    PHOTOGRAPHER_OT_FilePathTokenAdd,
)

def register():
    from bpy.utils import register_class
    register_class(RenderQueueSettings)
    bpy.types.Scene.renderqueue = PointerProperty(type=RenderQueueSettings)
    for cls in classes:
        register_class(cls)
    bpy.types.TOPBAR_MT_render.append(menu_func)

def unregister():
    from bpy.utils import unregister_class
    bpy.types.TOPBAR_MT_render.remove(menu_func)
    for cls in classes:
        unregister_class(cls)
    unregister_class(RenderQueueSettings)
    del bpy.types.Scene.renderqueue
