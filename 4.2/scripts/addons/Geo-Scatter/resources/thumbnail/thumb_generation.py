

import bpy
import os, sys, traceback, shlex, subprocess, time, datetime

#WARNING
#Dorian, you had the very bad idea of mixing plugin module with script in here
#This meant that for example you cannot use the translate module, as it will create errors 
#This is very bad and it should be corrected, Dorian if you are reading this, correct this asap thank you very much
#Cheers,
#Old self


# ooooooooooooo oooo                                       .o8             .oooooo.                                                           .    o8o
# 8'   888   `8 `888                                      "888            d8P'  `Y8b                                                        .o8    `"'
#      888       888 .oo.   oooo  oooo  ooo. .oo.  .oo.    888oooo.      888            .ooooo.  ooo. .oo.    .ooooo.  oooo d8b  .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.
#      888       888P"Y88b  `888  `888  `888P"Y88bP"Y88b   d88' `88b     888           d88' `88b `888P"Y88b  d88' `88b `888""8P `P  )88b    888   `888  d88' `88b `888P"Y88b
#      888       888   888   888   888   888   888   888   888   888     888     ooooo 888ooo888  888   888  888ooo888  888      .oP"888    888    888  888   888  888   888
#      888       888   888   888   888   888   888   888   888   888     `88.    .88'  888    .o  888   888  888    .o  888     d8(  888    888 .  888  888   888  888   888
#     o888o     o888o o888o  `V88V"V8P' o888o o888o o888o  `Y8bod8P'      `Y8bood8P'   `Y8bod8P' o888o o888o `Y8bod8P' d888b    `Y888""8o   "888" o888o `Y8bod8P' o888o o888o


class SCATTER5_OT_generate_thumbnail(bpy.types.Operator): #This is the same generator for preset and biomes. ui and argument are different tho. 

    bl_idname  = "scatter5.generate_thumbnail"
    bl_label   = "Generate Thumbnail"
    bl_description = "Render a preview of this biome/preset for this item in background"

    render_output : bpy.props.StringProperty()
    json_path : bpy.props.StringProperty()

    def invoke(self, context, event):

        #should always be INVOKE_DEFAULT context

        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        from ...ui import ui_templates
        from .. translate import translate

        layout = self.layout
        
        scat_scene = bpy.context.scene.scatter5
        scat_op    = bpy.context.scene.scatter5.operators.generate_thumbnail

        box, is_open = ui_templates.box_panel(self, layout,         
            prop_str = "ui_dialog_biomethumb", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_dialog_biomethumb");BOOL_VALUE(1)
            icon = "RESTRICT_RENDER_OFF", 
            name = translate("Generate Thumbnail"),
            )
        if is_open:

            col = box.column()

            if (self.json_path.endswith(".biome")):
                

                path = col.row()
                path.enabled = not scat_op.thumbcrea_use_current_blend_path
                path.alert = not os.path.exists(scat_op.thumbcrea_custom_blend_path) 
                path.prop(scat_op,"thumbcrea_custom_blend_path")
                
                col.prop(scat_op,"thumbcrea_custom_blend_emitter")

                col.separator(factor=0.5)
                
                col.prop(scat_op,"thumbcrea_use_current_blend_path")
                col.prop(scat_op,"thumbcrea_auto_reload_all")
                col.prop(scat_op,"thumbcrea_render_iconless")

                if (scat_op.thumbcrea_render_iconless):
                    txt = col.column()
                    txt.active = False 
                    txt.label(text=translate("Open the console to see progress & estimation."),icon="CONSOLE",)

            if (self.json_path.endswith(".preset")):

                col.prop(scat_op,"thumbcrea_camera_type")
                col.separator(factor=0.2)
                col.prop(scat_op,"thumbcrea_placeholder_type")
                col.prop(scat_op,"thumbcrea_placeholder_color")
                col.prop(scat_op,"thumbcrea_placeholder_scale")

            ui_templates.separator_box_in(box)

        return None 

    def back_ground_render(self, render_output="", camera_name="", json_path="", emitter_name="", placeholder_type="none", color="none", scale="none", scene_blend="" ):

        from .. import directories

        com = f'{shlex.quote(bpy.app.binary_path)} -b --python {shlex.quote(__file__)} -- {shlex.quote(render_output)} "{camera_name}" {shlex.quote(json_path)} "{emitter_name}" "{placeholder_type}" "{color}" "{scale}" {shlex.quote(scene_blend)}'
        print("")
        print("Background Task Initialized: ", com)
        
        args = shlex.split(com)

        # NOTE: silence ouput, it will be in p.stdout and p.stderr
        p = subprocess.run(args, capture_output=True, )
        
        if (p.returncode!=0):
            # something failed, print error
            print("exit code:", p.returncode, )
            print(p.stderr.decode("utf-8"))
            return None

        print("")
        print("Background Task Finished.")

        return None

    def execute(self, context):

        from ... utils.path_utils import get_subpaths
        from .. import directories

        if (not os.path.exists(self.json_path)):
            raise Exception("File do not exists")
            return {'FINISHED'}

        scat_scene = bpy.context.scene.scatter5
        scat_op    = scat_scene.operators.generate_thumbnail

        emitter_name = None
        scene_blend = None

        if (self.json_path.endswith(".biome")):
            emitter_name = scat_op.thumbcrea_custom_blend_emitter
            scene_blend = scat_op.thumbcrea_custom_blend_path
            
            if (scat_op.thumbcrea_use_current_blend_path):
                scene_blend = bpy.data.filepath

        elif (self.json_path.endswith(".preset")):
            emitter_name = "emitter_far" if (scat_op.thumbcrea_camera_type=="cam_forest") else "emitter_close"
            scene_blend = os.path.join(directories.addon_thumbnail, "thumb_scene.blend")

        if (not emitter_name):
            raise Exception("Please Fill emitter name information.")
            return {'FINISHED'}

        if (not scene_blend):
            raise Exception("Please Fill blender path information.")
            return {'FINISHED'}

        #batch render all iconless .biome files ?

        if (self.json_path.endswith(".biome") and scat_op.thumbcrea_render_iconless):

            formt = ".jpg"
            to_render = { p:p.replace(".biome",formt) for p in get_subpaths(directories.lib_biomes) if ( p.endswith(".biome") and not os.path.exists(p.replace(".biome",formt)) ) }
            total_steps = len(to_render.keys())

            if (total_steps==0):
                print("Seem like every .biomes files have .jpg icons already?")
                return {'FINISHED'}

            estimation = None
            start_time = time.time()
            
            for i,(pbiome,picon) in enumerate(to_render.items()):
                
                elapsed = datetime.timedelta(seconds=time.time()-start_time)
                msg =  f" (step: {i+1}/{total_steps})"
                #start time estimation if not first run
                if (i!=0):
                    estimation = (elapsed/i)*total_steps #get average of icon rendertime
                    msg += f" (elapsed: {elapsed} s)"
                    msg += f" (remaining: {estimation-elapsed} s)"
                else:
                    msg += " Estimation Available Soon..."

                print("")
                print(f">>>>>> SCATTER5_RENDERING_ICONS >>>>>> {msg}")

                self.back_ground_render(
                    render_output=picon, 
                    json_path=pbiome, 
                    emitter_name=emitter_name, 
                    scene_blend=scene_blend,
                    )

                continue 

        #fine single render then

        else:
            self.back_ground_render(
                render_output=self.render_output,
                camera_name=scat_op.thumbcrea_camera_type, #Used only if .preset
                json_path=self.json_path,
                emitter_name=emitter_name,
                placeholder_type=scat_op.thumbcrea_placeholder_type, #Used only if .preset
                color=str(tuple(scat_op.thumbcrea_placeholder_color)), #Used only if .preset
                scale=str(tuple(scat_op.thumbcrea_placeholder_scale)), #Used only if .preset
                scene_blend=scene_blend,
                )

        #Reload whole gallery of item
        if (self.json_path.endswith(".preset")):
            bpy.ops.scatter5.reload_preset_gallery()

        elif (self.json_path.endswith(".biome")):
            if (scat_op.thumbcrea_auto_reload_all):
                bpy.ops.scatter5.reload_biome_library()

        return {'FINISHED'}


classes = (

    SCATTER5_OT_generate_thumbnail,

    )


#   .oooooo.                                            oooo                .oooooo..o                     o8o                 .
#  d8P'  `Y8b                                           `888               d8P'    `Y8                     `"'               .o8
# 888           .ooooo.  ooo. .oo.    .oooo.o  .ooooo.   888   .ooooo.     Y88bo.       .ooooo.  oooo d8b oooo  oo.ooooo.  .o888oo
# 888          d88' `88b `888P"Y88b  d88(  "8 d88' `88b  888  d88' `88b     `"Y8888o.  d88' `"Y8 `888""8P `888   888' `88b   888
# 888          888   888  888   888  `"Y88b.  888   888  888  888ooo888         `"Y88b 888        888      888   888   888   888
# `88b    ooo  888   888  888   888  o.  )88b 888   888  888  888    .o    oo     .d8P 888   .o8  888      888   888   888   888 .
#  `Y8bood8P'  `Y8bod8P' o888o o888o 8""888P' `Y8bod8P' o888o `Y8bod8P'    8""88888P'  `Y8bod8P' d888b    o888o  888bod8P'   "888"
#                                                                                                                888
#                                                                                                               o888o

if __name__ == "__main__":

    print("...executing script thumb_generation.py as script")

    argv = sys.argv
    if('--' not in argv):
        print("Error, We did not detect arguments?")
        sys.exit(1)
    
    # blender itself will ignore all arguments after -- and those can be passed here
    argv = argv[argv.index("--") + 1:]

    render_output    = os.path.abspath(argv[0])
    camera_name      = argv[1]
    json_path        = os.path.abspath(argv[2])
    emitter_name     = argv[3]
    placeholder_type = argv[4]
    color            = argv[5]
    scale            = argv[6]
    scene_blend      = argv[7]

    try:

        #open scene file
        if (not os.path.exists(scene_blend)):
            raise Exception(f"Error, Could't find the given scene '{scene_blend}'")

        bpy.ops.wm.open_mainfile(filepath=scene_blend,)

        #define scat_scene and disable security features
        #they might hide our future scatter-system if left checked
        scat_scene = bpy.context.scene.scatter5
        scat_scene.sec_verts_allow = False
        scat_scene.sec_count_allow = False

        #get emitter by name 
        if (emitter_name!=""):
            scat_scene.emitter = bpy.data.objects.get(emitter_name)
        emitter = scat_scene.emitter
        if (emitter is None): 
            raise Exception(f"Error, Emitter not found")

        #handle preset thumbnail generation 
        #from thumb_scene.blend only 
        if (json_path.endswith(".preset")):
                
                hld = bpy.data.objects[placeholder_type]

                #change placeholder color?
                if (color!="none"):
                    color = eval(color)+(1.0, ) #convert from string tuple back to tuple
                    hld.material_slots[0].material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = color

                #eevee for presets 
                bpy.context.scene.render.engine = 'BLENDER_EEVEE'
                
                #scatter operator
                bpy.ops.scatter5.add_psy_preset(
                    emitter_name=emitter_name,
                    surfaces_names=emitter_name,
                    instances_names=placeholder_type,
                    selection_mode="viewport",
                    psy_name="Thumbnail",
                    psy_color=(1,1,1),
                    json_path=json_path,
                    pop_msg=False,
                    )

                #change placeholder scale? == adjust scale posteriori 
                if (scale!="none"):
                    scale = eval(scale) #convert from string tuple back to tuple
                    p = emitter.scatter5.particle_systems[0]
                    p.s_scale_default_allow = True
                    p.s_scale_default_value[0] *= scale[0]
                    p.s_scale_default_value[1] *= scale[1]
                    p.s_scale_default_value[2] *= scale[2]

                # custom cam in blend? choose so,  note that this is onlygot (if using default scene)
                getty_cam = bpy.data.objects.get(camera_name)
                if (getty_cam is not None):
                    bpy.context.scene.camera = getty_cam

        #or if biome, import biome
        elif (json_path.endswith(".biome")):
            bpy.ops.scatter5.add_biome(
                emitter_name=emitter_name,
                surfaces_names=emitter_name,
                json_path=json_path,
                )

        #do the render 
        bpy.context.scene.render.filepath = render_output
        bpy.ops.render.render(animation=False, write_still=True, )

    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
    
    # NOTE: cleanup moved here so it can be used as non-blocking call
    if (os.path.exists(library_blend)):
        os.remove(library_blend)
    
    sys.exit(0)
