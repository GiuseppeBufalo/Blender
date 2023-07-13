

import bpy
import os
import json
import time
import pathlib

from .. utils.extra_utils import dprint

from .. resources.translate import translate
from .. resources import directories

from .. import utils
from .. utils.str_utils import legal, word_wrap
from .. utils.path_utils import dict_to_json, json_to_dict

from .. ui import ui_templates
from . presetting import settings_to_dict
from . add_psy import estimate_future_instance_count


#TODO:
#Import behavior is very complex, since we need to support 3 ways of storing instances, 
#either all centralized, or automatically saved with BASENAME.instances.blend, or all individually displatched per instances.
#we need to find back the paths in our library or externally defined paths
#cherry on top we always try to batch import all of them in the beginning of the process with scatter5.load_biome()
#this kind of support is very difficult to organize, we need a cleanup here, clarify functions. but. quite hard


# oooooooooooo               .
# `888'     `8             .o8
#  888          .ooooo.  .o888oo  .oooo.o
#  888oooo8    d88' `"Y8   888   d88(  "8
#  888    "    888         888   `"Y88b.
#  888         888   .o8   888 . o.  )88b
# o888o        `Y8bod8P'   "888" 8""888P'


def add_biome_layer( #add a new biome_layer, WARNING, will assume all instances or display objects are all presents in this blend!
    emitter_name="", #if left none, will find active
    instances_names=[], #list of future instances, object names that we'll import from given blend path
    surfaces_names=[], #surfaces upon which we will scatter
    json_path="", #.preset file path we'll use to define the settings of this scatter-layer
    psy_name="",
    psy_color=(1,1,1),
    display_settings={}, #display settings we extract from the .biome json file
    ):
    
    scat_scene = bpy.context.scene.scatter5
    scat_op    = scat_scene.operators.load_biome
    
    #assert files found? 
    if (not os.path.exists(json_path)):
        raise Exception(f"Preset path ''{json_path}'' Not found!")

    #Get Emitter 
    emitter = bpy.data.objects.get(emitter_name)
    if (emitter is None):
        emitter = scat_scene.emitter
    if (emitter is None):
        raise Exception("add_biome_layer: no emitter found")

    #assert no instance?
    if ( (instances_names==[None]) or (len(instances_names)==0) ):
        raise Exception("add_biome_layer: no instances found")
    #assert no surfaces?
    if ( (surfaces_names==[None]) or (len(surfaces_names)==0) ):
        raise Exception("add_biome_layer: no surfaces found")

    #carreful,display_settings can be None if get() function failed when gathering information from .biome file dict
    if (display_settings is None):
        display_settings = {}

    #check if we have all the required objects in the scene?
    should_be_imported = instances_names.copy()
    #we will also need to import potential placeholder objects if biomes are using custom placeholders
    if ("s_display_custom_placeholder_ptr" in display_settings.keys()):
        should_be_imported.append(display_settings["s_display_custom_placeholder_ptr"])
    for name in should_be_imported:
        if (name not in bpy.data.objects):
            raise Exception(f"add_biome_layer: '{name}' object couldn't be found")

    #pause get_event() operator, is constantly called otherwise
    with scat_scene.factory_update_pause(event=True):

        #do the scattering
        bpy.ops.scatter5.add_psy_preset(
            emitter_name=emitter.name,
            surfaces_names="_!#!_".join(surfaces_names),
            instances_names="_!#!_".join(instances_names),
            psy_name=psy_name,
            psy_color=psy_color,
            json_path=json_path,
            ctxt_operator="load_biome",
            pop_msg=False, #messages are handled by biome operator directly
            )

        p = emitter.scatter5.particle_systems[-1]

        #after creation, assign display settings, if encoded properly

        if ("s_display_method" in display_settings.keys()):

            if ("s_display_method" in display_settings.keys()):
                p.s_display_method =  display_settings["s_display_method"]

            if ("s_display_placeholder_type" in display_settings.keys()):
                p.s_display_placeholder_type = display_settings["s_display_placeholder_type"]
            if ("s_display_custom_placeholder_ptr" in display_settings.keys()):
                p.s_display_custom_placeholder_ptr = bpy.data.objects.get(display_settings["s_display_custom_placeholder_ptr"])
            if ("s_display_placeholder_scale" in display_settings.keys()):
                p.s_display_placeholder_scale = display_settings["s_display_placeholder_scale"]

            if ("s_display_point_radius" in display_settings.keys()):
                p.s_display_point_radius = display_settings["s_display_point_radius"]
            if ("s_display_cloud_radius" in display_settings.keys()):
                p.s_display_cloud_radius = display_settings["s_display_cloud_radius"]
            if ("s_display_cloud_density" in display_settings.keys()):
                p.s_display_cloud_density = display_settings["s_display_cloud_density"]

            if ("s_display_camdist_allow" in display_settings.keys()):
                p.s_display_camdist_allow = display_settings["s_display_camdist_allow"]
            if ("s_display_camdist_distance" in display_settings.keys()):
                p.s_display_camdist_distance = display_settings["s_display_camdist_distance"]

            if ("s_display_viewport_method" in display_settings.keys()):
                p.s_display_viewport_method = display_settings["s_display_viewport_method"]

        #enable biome display by default? 

        p.s_display_allow = scat_op.f_display_biome_allow

    return p


def get_instances_names_list(d,):
    """get instance list information from json dict"""

    #perhaps biome format encoded just a single name as instance? not sure why we support this. 
    if (type(d["instances"]) is str):
        return list(d["instances"])

    #or instances is iterable
    if (type(d["instances"]) in (list,tuple)):

        #if elements are tuple, then we have an INSTANCES_DEFINED blend case, ignore blend name
        if (type(d["instances"][0]) in (list,tuple)):
            return [e[0] for e in d["instances"]]

        #else classic instances names list 
        if (type(d["instances"][0]) is str):
            return d["instances"]

    raise Exception(f"Instance type not recognized: {d['instances']}")
    return None


def search_biome_file(
    file_name="",
    biome_path="",
    is_blend=False,
    raise_exception=False,
    pop_msg=False,
    ):
    """search for the full path of given basename in the scatter library & environment paths"""

    full_path = ""
    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    #benchmark debug
    dprint(f"search_biome_file({file_name})->start")

    if ( (is_blend) and (not file_name.endswith(".blend")) ):
        file_name = f"{file_name}.blend"

    #using basename shortcut? 
    if ("BASENAME" in file_name):
        file_name = file_name.replace("BASENAME", os.path.basename(biome_path).replace(".biome","") ,)
    
        #if using the basename system, then there is a strong probability of finding path directly here 
        probable_path = os.path.join(os.path.dirname(biome_path),file_name)
        if (os.path.exists(probable_path)):
            full_path = probable_path

    if (full_path==""):

        path_ext = "."+file_name.split(".")[-1]
        search_first = os.path.dirname(biome_path)
         
        search_others = []
        if (addon_prefs.blend_environment_path_asset_browser_allow):
            search_others += [os.path.realpath(l.path) for l in bpy.context.preferences.filepaths.asset_libraries]
        if (addon_prefs.blend_environment_path_allow):
            search_others += [p.blend_folder for p in addon_prefs.blend_environment_paths]

        #search everywhere for file
        full_path = utils.path_utils.search_for_path(
            keyword=file_name,
            search_folder=directories.lib_library,
            search_first=search_first,
            search_others=search_others,
            file_type=path_ext,
            )

    #benchmark debug
    dprint("search_biome_file->end")

    #couldn't find the file?
    if (not os.path.exists(full_path)):
            
        txtmsg = f"{translate('We did not find')}\n'{file_name}'\n{translate('in your scatter library')}.\n{translate('did you installed the library correctly?')}\n\n{translate('Perhaps you need to define new environment paths leading to this .blend file in the plugin preferences.')}\n"
        if (raise_exception):
            raise Exception(txtmsg)
        
        if (pop_msg):
            bpy.ops.scatter5.popup_dialog(
                'INVOKE_DEFAULT',
                msg=txtmsg,
                header_title=translate("Missing File"),
                header_icon="LIBRARY_DATA_BROKEN",
                )
        return None

    return full_path


def import_biome_objs(
    biome_dict={},
    biome_path="",
    raise_exception=False,
    pop_msg=False,
    ):
    """batch import all related objects of a biome preset file"""

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    scat_scene  = bpy.context.scene.scatter5
    scat_op     = scat_scene.operators.load_biome

    to_import = {} #key=blend_name, value=[obj_names]
    display_objs = []

    #gather obj & their blend name per layers

    for key, value in biome_dict.items():
        
        #only interested by 
        if (not key.isdigit()):
            continue

        blend_name = value["asset_file"]

        #blend individually precised per objs? (this was added much later)
        if (blend_name=="INSTANCES_DEFINED"):

            for ins,ins_bname in value["instances"]:

                d = to_import.get(ins_bname)
                if (d is None):
                    d = to_import[ins_bname] = []

                if (ins not in d):
                    d.append(ins)

        #or blend defined per scatter-layer?
        else:

            d = to_import.get(blend_name)
            if (d is None):
                d = to_import[blend_name] = []

            for ins in get_instances_names_list(value):
                if (ins not in d):
                    d.append(ins)

        #need to support custom placeholder obj need to import them too
        if ("display" in value):

            dptr = value["display"].get("s_display_custom_placeholder_ptr")
            if (dptr is not None):

                if (dptr not in display_objs):
                    display_objs.append(dptr)

        continue

    #support the use of the shortcut BASENAME for referencing the blend name

    for blend_name in to_import.copy().keys():
        
        if ("BASENAME" in blend_name):
            biome_basename = os.path.basename(biome_path).replace(".biome","")
            new_key = blend_name.replace("BASENAME", biome_basename,)
            to_import[new_key] = to_import.pop(blend_name)
        
        continue

    #add support for custom placeholder obj

    if (len(display_objs)!=0):
        
        for key, value in to_import.copy().items():
            to_import[key] += display_objs
            
            continue

    #import if needed, to do so, find path from blend_name

    for blend_name, obj_names in to_import.items():

        if (any(name not in bpy.data.objects for name in obj_names)):

            path_found = search_biome_file(
                file_name=blend_name,
                biome_path=biome_path,
                is_blend=True,
                raise_exception=raise_exception,
                pop_msg=pop_msg,
                )

            if (path_found is None):
                return "RAISE_ERROR"

            utils.import_utils.import_objects(
                blend_path=path_found,
                object_names=obj_names,
                link=(scat_scene.objects_import_method=="LINK"),
                )

        continue

    #warning if everything was imported correctly

    for obj_names in to_import.values():
        for name in obj_names:
            if (name not in bpy.data.objects):
                print(f"S5 WARNING: couldn't import '{name}'")

            continue

    return obj_names


#       .o.             .o8        .o8       oooooooooo.   o8o
#      .888.           "888       "888       `888'   `Y8b  `"'
#     .8"888.      .oooo888   .oooo888        888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo.
#    .8' `888.    d88' `888  d88' `888        888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b
#   .88ooo8888.   888   888  888   888        888    `88b  888  888   888  888   888   888  888ooo888
#  .8'     `888.  888   888  888   888        888    .88P  888  888   888  888   888   888  888    .o
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'


class SCATTER5_OT_add_biome(bpy.types.Operator): 
    """add a new biome file to given emitter object, prefer to use this operator when scripting, scatter5.load_biome() is for GUI
    direct paint option is not supported by this operator""" 

    bl_idname      = "scatter5.add_biome"
    bl_label       = translate("Add Biome")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    json_path : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    def execute(self, context):

        #found files? 
        if (not os.path.exists(self.json_path)):
            raise Exception(f"Biome path ''{self.json_path}'' Not found!")
            return {'FINISHED'}

        scat_scene   = bpy.context.scene.scatter5
        scat_op      = scat_scene.operators.load_biome
        scat_op_crea = scat_scene.operators.create_operators
        addon_prefs  = bpy.context.preferences.addons["Geo-Scatter"].preferences

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter
        if (emitter is None):
            raise Exception("No Emitter found")
            return {'FINISHED'}

        #Get Surfaces (will find f_surfaces if nothing passed)
        if (self.surfaces_names==""):
              surfaces_names = [s.name for s in scat_op_crea.get_f_surfaces()]
        else: surfaces_names = self.surfaces_names.split("_!#!_")
        surfaces = [bpy.data.objects.get(s) for s in surfaces_names if (s in bpy.data.objects)]
        if (len(surfaces)==0):
            raise Exception("No Surfaces found")
            return {'FINISHED'}

        #Read json info 
        json_path, json_filename = os.path.split(self.json_path)
        d = json_to_dict( path=json_path, file_name=json_filename)

        #import all objects this biome file might need
        import_biome_objs(
            biome_dict=d,
            biome_path=self.json_path,
            raise_exception=True,
            )

        #add biomes layers one by one
        for i, (key, value) in enumerate(d.items()):

            #ignore info dict
            if (key=="info"):
                continue 
                    
            #if is digit, that mean we got a biome layer dict
            if (key.isdigit()):
                
                json_preset_path = search_biome_file(
                    file_name=value["preset"],
                    biome_path=self.json_path,
                    raise_exception=True,
                    )

                add_biome_layer(
                    emitter_name=emitter.name,
                    surfaces_names=surfaces_names,
                    instances_names=get_instances_names_list(value),
                    json_path=json_preset_path,
                    psy_name=value["name"],
                    psy_color=value["color"],
                    display_settings=value.get("display"),
                    )
                continue

            #apply material option? 
            if (key.startswith("material")):

                #get blend path
                material_blend_path = search_biome_file(
                    file_name=value["material_file"],
                    is_blend=True,
                    biome_path=self.json_path,
                    raise_exception=True,
                    )

                #import material & import 
                mats = utils.import_utils.import_materials(
                    material_blend_path,
                    [value["material_name"]],
                    link=(scat_scene.objects_import_method=="LINK"),
                    )

                mat = bpy.data.materials.get(mats[0])
                if (mat is not None): 
                    if (emitter.data.materials):
                          emitter.data.materials[0] = mat
                    else: emitter.data.materials.append(mat)

                continue

            if (key.startswith("script")):
                continue #support later maybe

            continue 

        return {'FINISHED'}


# ooooo                                  .o8      oooooooooo.   o8o
# `888'                                 "888      `888'   `Y8b  `"'
#  888          .ooooo.   .oooo.    .oooo888       888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo.
#  888         d88' `88b `P  )88b  d88' `888       888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b
#  888         888   888  .oP"888  888   888       888    `88b  888  888   888  888   888   888  888ooo888
#  888       o 888   888 d8(  888  888   888       888    .88P  888  888   888  888   888   888  888    .o
# o888ooooood8 `Y8bod8P' `Y888""8o `Y8bod88P"     o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'
#                                                

class SCATTER5_OT_load_biome(bpy.types.Operator): 
    """same as 'add_biome()', with added layer of complexity of progress bar system""" 

    bl_idname      = "scatter5.load_biome"
    bl_label       = translate("Load Biome")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    json_path : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #=.biome path -> Mandatory arg
    single_layer : bpy.props.IntProperty(default=-1, options={"SKIP_SAVE",},) #optional load single layer, set -1 to ignore 

    @classmethod
    def description(cls, context, properties):

        scat_scene   = bpy.context.scene.scatter5
        scat_op_crea = scat_scene.operators.create_operators

        square_area = 0
        for s in scat_op_crea.get_f_surfaces():
            square_area += s.scatter5.estimated_square_area
            continue

        e = bpy.context.window_manager.scatter5.library[properties.json_path]
        description = '\n \u2022 '.join([ 
            translate("Information about this .biome file:"),
            f'{translate("Layers")} : {e.layercount}',
            f'{translate("Estimated Density")} : {round(e.estimated_density,2):,} Ins/m²',
            f'{translate("Estimated Count")} : {int(e.estimated_density*square_area):,} P',
            f'{translate("Author")} : {e.author}',
            f'{translate("Website")} : {e.website}',
            f'{translate("Keywords")} : {e.keywords}',
            f'{translate("Description")} : {e.description}',
            ])

        return description

    def __init__(self):

        self.Operations = {}
        self.step = 0
        self.timer = None
        self.done = False
        self.max_step = None
        self.timer_count = 0

        self.loaded_psys = []

        return None 

    def add_import_instruction(self, d,):
        """import dependencies objects from biome files, done at once for optimization purpose"""

        scat_scene   = bpy.context.scene.scatter5
        scat_op      = scat_scene.operators.load_biome
        addon_prefs  = bpy.context.preferences.addons["Geo-Scatter"].preferences
             
        #store import function in instruction stack

        def instruction():
            """import_instruction"""

            #import all objects this biome file might need
            r_value = import_biome_objs(
                biome_dict=d,
                biome_path=self.json_path,
                pop_msg=True,
                )
            if (r_value=="RAISE_ERROR"):
                return "RAISE_ERROR"

            return r_value

        self.Operations["Import"] = instruction

        return None 

    def add_addlayer_instructions(self, d, emitter, surfaces, surfaces_names,):
        """add all addlayer to instructions stack, can also be material"""

        addon_prefs  = bpy.context.preferences.addons["Geo-Scatter"].preferences

        max_count   = -1
        total_count = 0
        layer_count = 1

        for i, (key, dval) in enumerate(d.items()):

            #ignore info dict
            if (key=="info"):
                continue 

            #single layer option?
            if ( (self.single_layer!=-1) and (i!=self.single_layer) ):
                continue

            #biome layer dict
            if (key.isdigit()):

                #get layer preset path
                json_preset_path = search_biome_file(
                    file_name=dval["preset"],
                    biome_path=self.json_path,
                    pop_msg=True,
                    )
                if (not json_preset_path):
                    return {'FINISHED'}

                #store particle count information for message
                count = estimate_future_instance_count(
                    surfaces=surfaces,
                    d=json_to_dict(path=os.path.dirname(json_preset_path),file_name=os.path.basename(json_preset_path),),
                    refresh_square_area=(i==1), #always refresh at least once
                    ctxt_operator="load_biome",
                    )

                total_count += count
                if (max_count<count):
                    max_count=count

                #store function in dict 

                def generate_instruction(dval, json_preset_path,):
                    def instruction():
                        """addlayer_instructions"""
                        
                        p = add_biome_layer(
                            emitter_name=emitter.name,
                            surfaces_names=surfaces_names,
                            instances_names=get_instances_names_list(dval),
                            json_path=json_preset_path,
                            psy_name=dval["name"],
                            psy_color=dval["color"],
                            display_settings=dval.get("display"),
                            )

                        #save layer
                        self.loaded_psys.append(p.name)
                        return None
                    return instruction

                self.Operations[f"Layer {int(layer_count)}"] = generate_instruction(dval, json_preset_path,)
                
                layer_count += 1

                continue 

            #apply material option? 

            if (key.startswith("material")):

                #get blend path
                material_blend_path = search_biome_file(
                    file_name=dval["material_file"],
                    is_blend=True,
                    biome_path=self.json_path,
                    pop_msg=True,
                    )
                if (not material_blend_path):
                    return {'FINISHED'}

                def instruction():
                    #import material & apply dialog 
                    utils.import_utils.import_materials(
                        material_blend_path,
                        [dval["material_name"]],
                        link=(scat_scene.objects_import_method=="LINK"),
                        )
                    bpy.ops.scatter5.material_confirm(
                        ('INVOKE_DEFAULT') if dval["confirm"] else ('EXEC_DEFAULT'),
                        obj_name=emitter.name,
                        material_name=dval["material_name"],
                        )
                    return None
                
                self.Operations["Material"] = instruction
                
                continue

            #if script, execute script
            if (key.startswith("script")):
                continue #later maybe

            continue

        return max_count, total_count 

    def add_quickpaint_instruction(self, action_type, mask_name,):
        """special instruction for direct mask painting option"""

        def instruction():
            """quickpaint_instruction"""

            if (action_type=="vg"):
                bpy.ops.scatter5.vg_quick_paint(mode="vg", group_name=mask_name, use_surfaces=True,)

            elif (action_type=="bitmap"):
                bpy.ops.scatter5.image_utils(option="paint", paint_color=(1,1,1), img_name=mask_name,)

            elif (action_type=="curve"):
                for window in bpy.context.window_manager.windows:
                    screen = window.screen
                    for area in screen.areas:
                        if (area.type == 'VIEW_3D'):
                            region = None
                            for r in area.regions:
                                if (r.type == 'WINDOW'):
                                    region = r
                                    break
                            if (region is not None):
                                override = {'window': window, 'screen': screen, 'area': area, 'region': region, }
                                # NOTE: override context AND use invoke at the same time! third param is use undo, operator adds its own undo state, so this is not needed (i hope?)
                                bpy.ops.scatter5.draw_bezier_area(override, 'INVOKE_DEFAULT', False, edit_existing=mask_name, )
                                break
            
            return None 

        self.Operations["Start Painting"] = instruction

        return None 

    def add_security_instruction(self, max_count, total_count,):

        def instruction():
            """security_instruction"""

            #gather list of psys we generated
            emitter = bpy.context.scene.scatter5.emitter
            kwargs = {f"psy_name_{i:02}":pname for i,pname in enumerate(self.loaded_psys)}

            #check if the scatter has heavy poly obj
            poly = False
            if (bpy.context.scene.scatter5.operators.create_operators.f_sec_verts_allow==True):
                for p in emitter.scatter5.particle_systems:
                    if (p.name in self.loaded_psys):
                        for o in p.get_instances_obj():
                            if (o.display_type=="BOUNDS"):
                                poly = True
                                break

            #call the dialog box popup
            bpy.ops.scatter5.popup_security('INVOKE_DEFAULT', scatter=True, poly=poly, total_scatter=total_count, emitter=emitter.name, **kwargs,)
            return None

        self.Operations["Pop Message"] = instruction

        return None 

    def invoke(self, context, event):

        # Not likely to happend 
        if (not os.path.exists(self.json_path)):
            raise Exception("Json path don't exists?")
        
        scat_scene   = bpy.context.scene.scatter5
        scat_op      = scat_scene.operators.load_biome
        scat_op_crea = scat_scene.operators.create_operators
        addon_prefs  = bpy.context.preferences.addons["Geo-Scatter"].preferences

        ######### Prepare Step Separation 

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name) #POTENTIAL BUG, load seem to only support context emitter
        if (emitter is None):
            emitter = scat_scene.emitter
        if (emitter is None):
            raise Exception("No Emitter found")
            return {'FINISHED'}

        #Get Surfaces (will find f_surfaces if nothing passed)
        if (self.surfaces_names==""):
              surfaces_names = [s.name for s in scat_op_crea.get_f_surfaces()]
        else: surfaces_names = self.surfaces_names.split("_!#!_")
        surfaces = [bpy.data.objects.get(s) for s in surfaces_names if (s in bpy.data.objects)]
        if (len(surfaces)==0):
            raise Exception("No Surfaces found")
            return {'FINISHED'}

        #Read json info 
        json_path, json_filename = os.path.split(self.json_path)
        d = json_to_dict(path=json_path, file_name=json_filename)

        #prepare for direct-paint

        action_type = None 
        if (scat_op.f_mask_action_method=="paint"):
            action_type = scat_op.f_mask_action_type

            if (action_type=="vg"):
                #find name not taken, across all surfaces
                i = 1
                vg_name = "DirectPaint"
                while vg_name in [v.name for o in surfaces for v in o.vertex_groups]:
                    vg_name = f"DirectPaint.{i:03}"
                    i += 1
                for s in surfaces:
                    s.vertex_groups.new(name=vg_name)
                scat_op.f_mask_paint_vg = vg_name #assignation will be done in add_psy_preset()
                mask_name = vg_name

            elif (action_type=="bitmap"):
                img = bpy.data.images.new("ImageMask", 1000, 1000,)
                scat_op.f_mask_paint_bitmap = img.name #assignation will be done in add_psy_preset()
                mask_name = img.name

            elif (action_type=="curve"):
                bez = bpy.data.curves.new("BezierArea","CURVE")
                cur = bpy.data.objects.new(bez.name,bez)
                cur.location = bpy.context.scene.cursor.location
                bpy.context.scene.collection.objects.link(cur)
                scat_op.f_mask_paint_curve_area = cur #assignation will be done in add_psy_preset()
                mask_name = cur.name

        #fill our instruction stack, self.Operation with instructions
        #https://blender.stackexchange.com/questions/3219/how-to-show-to-the-user-a-progression-in-a-script/231693#231693

        #import all objects dependencies instructions
        r = self.add_import_instruction(d)
        if (r=={'FINISHED'}):
            return {'FINISHED'}

        #scatter layers & assign materials instructions
        r = self.add_addlayer_instructions(d, emitter, surfaces, surfaces_names,)
        if (r=={'FINISHED'}):
            return {'FINISHED'}
        max_count, total_count = r

        #direct paint instructions 
        if (action_type is not None):
            self.add_quickpaint_instruction(action_type, mask_name,)

        #Security check confirm?
        if ((scat_op_crea.f_sec_count_allow) and (total_count>scat_op_crea.f_sec_count)):
            self.add_security_instruction(max_count, total_count,)

        #define context for progress bar interface
        scat_scene.operators.load_biome.progress_context = self.json_path

        #define maximal instructions step achievable for this biome
        self.max_step = len(self.Operations.keys())

        #maunch modal
        context.window_manager.modal_handler_add(self)
        
        #add timer to control running jobs activities 
        self.timer = context.window_manager.event_timer_add(0.01, window=context.window)

        return {'RUNNING_MODAL'}

    def update_progress(self,context):

        #update progess bar & label
        scat_op_ctxt = context.scene.scatter5.operators.load_biome
        scat_op_ctxt.progress_bar = ((self.step+1)/(self.max_step+1))*100
        scat_op_ctxt.progress_label = list(self.Operations.keys())[self.step] if (self.step<len(self.Operations.keys())) else translate("Done!")

        context.area.tag_redraw()

        return None 

    def modal(self, context, event):

        try:
            self.update_progress(context)

            #by running a timer at the same time of our modal operator and catching timer event
            #we are guaranteed that update is done correctly in the interface, as timer event cannot occur when interface is frozen
            if (event.type!="TIMER"):
                return {'RUNNING_MODAL'}
                
            #but wee need a little time off between timers to ensure that blender have time to breath
            #then are sure that interface has been drawn and unfrozen for user 
            self.timer_count +=1
            if (self.timer_count!=10):
                return {'RUNNING_MODAL'}
            self.timer_count=0

            #if we are done, then make blender freeze a little so user can see final progress state
            #and very important, run restore function
            if (self.done):
                time.sleep(0.05)
                self.restore(context)
                return {'FINISHED'}
        
            if (self.step<self.max_step):

                #run instruction function!
                instruction = list(self.Operations.values())[self.step]
                r_value = instruction()

                #problem occured during the instruction?
                if (r_value=="RAISE_ERROR"):
                    self.restore(context)
                    return {'FINISHED'}

                #iterate over step, if last step, signal it
                self.step += 1
                if (self.step==self.max_step):
                    self.done=True

                return {'RUNNING_MODAL'}

            return {'RUNNING_MODAL'}

        except Exception as e:
            self.restore(context)
            raise Exception(e)

        return {'FINISHED'}
 
    def restore(self, context):

        scat_op_ctxt = bpy.context.scene.scatter5.operators.load_biome
        scat_op_ctxt.progress_bar = 0
        scat_op_ctxt.progress_label = ""
        scat_op_ctxt.progress_context = ""

        context.area.tag_redraw()

        context.window_manager.event_timer_remove(self.timer)

        #CLEANUP: perhaps do everything in aftermath? No need to be in operation stack, right?

        #in the case of bounding box secutity feature, we have no way of telling in advance if the object imported will be high poly
        #with the current security instance count we try to predict it. in order to pop the message, we can observe aftermath of load
        #if count seccurity feature, will be supported anyway!

        if ("Pop Message" not in self.Operations):

            #gather list of psys we generated
            emitter = bpy.context.scene.scatter5.emitter
            kwargs = {f"psy_name_{i:02}":pname for i,pname in enumerate(self.loaded_psys)}

            #check if the scatter has heavy poly obj
            poly = False
            if (bpy.context.scene.scatter5.operators.create_operators.f_sec_verts_allow==True):
                for p in emitter.scatter5.particle_systems:
                    if (p.name in self.loaded_psys):
                        for o in p.get_instances_obj():
                            if (o.display_type=="BOUNDS"):
                                poly = True
                                break

            #call the dialog box popup
            if poly:
                bpy.ops.scatter5.popup_security('INVOKE_DEFAULT', scatter=False, poly=True, emitter=emitter.name, **kwargs,)

        return None 


class SCATTER5_OT_material_confirm(bpy.types.Operator):

    bl_idname = "scatter5.material_confirm"
    bl_label = translate("Would you want to apply a  new Material ?")
    bl_options = {'REGISTER', 'INTERNAL'}

    obj_name : bpy.props.StringProperty()
    material_name : bpy.props.StringProperty()

    def execute(self, context):

        emitter = bpy.data.objects.get(self.obj_name)
        mat = bpy.data.materials.get(self.material_name)

        if (not emitter or not mat):
            return {'FINISHED'}    

        if emitter.data.materials:
              emitter.data.materials[0] = mat
        else: emitter.data.materials.append(mat)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=translate("There's a material associated with this ecosystem."))



#  .oooooo..o                                      oooooooooo.   o8o                                       
# d8P'    `Y8                                      `888'   `Y8b  `"'                                       
# Y88bo.       .oooo.   oooo    ooo  .ooooo.        888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo. 
#  `"Y8888o.  `P  )88b   `88.  .8'  d88' `88b       888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b
#      `"Y88b  .oP"888    `88..8'   888ooo888       888    `88b  888  888   888  888   888   888  888ooo888
# oo     .d8P d8(  888     `888'    888    .o       888    .88P  888  888   888  888   888   888  888    .o
# 8""88888P'  `Y888""8o     `8'     `Y8bod8P'      o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'
#                                                                                                          


class SCATTER5_OT_save_biome_to_disk_dialog(bpy.types.Operator):

    bl_idname      = "scatter5.save_biome_to_disk_dialog"
    bl_label       = translate("Biome Export")
    bl_description = translate("Export the selected scatter-system(s) as .biome files in your hard drive")
    bl_options     = {'REGISTER', 'INTERNAL'}

    #redefine settings, used for biome overwrite option
    redefine_biocrea_settings : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    biocrea_biome_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    biocrea_creation_directory : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    biocrea_file_keywords : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    biocrea_file_author : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    biocrea_file_website : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    biocrea_file_description : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter is not None)

    def invoke(self, context, event):
        
        scat_scene = bpy.context.scene.scatter5
        scat_op = scat_scene.operators.save_biome_to_disk_dialog

        if (len(scat_scene.emitter.scatter5.get_psys_selected())==0):
            bpy.ops.scatter5.popup_menu(title=translate("Biome Creation Failed"), msgs=translate("No Scatter-System(s) Selected"), icon="ERROR",)
            return {'FINISHED'}

        #redefine GUI steps
        scat_op.biocrea_creation_steps=0
            
        #override settings? used bu biomes overwrite option
        if (self.redefine_biocrea_settings):
            scat_op.biocrea_biome_name = self.biocrea_biome_name
            scat_op.biocrea_creation_directory = self.biocrea_creation_directory
            scat_op.biocrea_file_keywords = self.biocrea_file_keywords
            scat_op.biocrea_file_author = self.biocrea_file_author
            scat_op.biocrea_file_website = self.biocrea_file_website
            scat_op.biocrea_file_description = self.biocrea_file_description

        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw_steps(self, layout, steps=None, smin=0,smax=2):

        lrow = layout.row()
        lrow1 = lrow.row()
        lrow2 = lrow.row()
        lrow3 = lrow.row()
        skip_prev = lrow2.row(align=True)
        
        op = skip_prev.row(align=True)
        op.enabled = (steps!=smin)
        op.operator("scatter5.exec_line",text="",icon="REW",).api = "scat_ops.save_biome_to_disk_dialog.biocrea_creation_steps -=1"
        
        if (steps==smax):
            txt = skip_prev.row(align=True)
            txt.operator("scatter5.dummy",text=translate("Done!"),)
        else:
            txt = skip_prev.row(align=True)
            txt.operator("scatter5.exec_line",text=translate("Next Step"),).api = "scat_ops.save_biome_to_disk_dialog.biocrea_creation_steps +=1"
           
        op = skip_prev.row(align=True)
        op.enabled = (steps!=smax)
        op.operator("scatter5.exec_line",text="",icon="FF",).api = "scat_ops.save_biome_to_disk_dialog.biocrea_creation_steps +=1"
            
        layout.separator(factor=0.44)

        return 

    def draw(self, context):
        layout  = self.layout

        scat_scene = bpy.context.scene.scatter5
        scat_op    = scat_scene.operators.save_biome_to_disk_dialog
        emitter    = scat_scene.emitter
        psys       = emitter.scatter5.get_psys_selected()

        bcol = layout.column(align=True)
        box, is_open = ui_templates.box_panel(self, bcol, 
            prop_str = "ui_dialog_presetsave", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_dialog_presetsave";UI_BOOL_VAL:"1"
            icon = "FILE_NEW", 
            name = translate("Export Selected as Biome"),
            )
        if is_open:

            sep = box.row()
            s1 = sep.separator(factor=0.2)
            s2 = sep.column()
            s3 = sep.separator(factor=0.2)

            s2.separator()

            steps = scat_op.biocrea_creation_steps 
            BASENAME = legal(scat_op.biocrea_biome_name.lower().replace(" ","_"))
            BLENDNAME = f"{BASENAME}.instances"

            #draw step 1/3

            if (steps==0):

                word_wrap(layout=s2, alignment="LEFT", max_char=55, string=translate("A Biome is a text file that bridge presets with assets.\nComplete these steps to create your biome.\nPlease select the layer(s) you will export first!"),)

                s2.separator(factor=0.5)

                exp = s2.column(align=True)
                exp.label(text=translate("Biome Name")+":")
                exp.prop(scat_op,"biocrea_biome_name",text="")

                s2.separator(factor=0.5)

                exp = s2.column(align=True)
                exp.label(text=translate("Export Directory")+":")
                exp.prop(scat_op,"biocrea_creation_directory",text="")

                txt = s2.column()
                txt.scale_y = 0.8
                txt.active = False
                txt.separator(factor=1.5)
                txt.label(text="the scatter Biome Library is by default located in:")
                txt.operator("scatter5.open_directory", text=f"'{directories.lib_biomes}", emboss=False,).folder = directories.lib_biomes
                txt.label(text="You are free to create subfolders within this location.")

                s2.separator(factor=2.5)
                self.draw_steps(s2, steps=steps,)

            #draw step 2/3

            elif (steps==1):

                s2.prop(scat_op,"biocrea_use_biome_display",)

                s2.prop(scat_op,"biocrea_external_blend_allow",)
                if (scat_op.biocrea_external_blend_allow):

                    nr = s2.row()
                    nr1 = nr.row()
                    nr1.separator(factor=2)
                    nr2 = nr.row()
                    prp = nr2.column(align=True)

                    txt = prp.column(align=True)
                    txt.active = False
                    txt.label(text=translate("Storage Method")+":")
                    prp.prop(scat_op, "biocrea_storage_type", text="")
                    prp.separator(factor=1)

                    if (scat_op.biocrea_storage_type=="individual"):
                        txt = prp.column(align=True)
                        txt.active = False
                        txt.scale_y = 0.9
                        word_wrap(layout=txt, alignment="LEFT", max_char=45, string=translate("Please only scatter linked objects, that way we'll find back the original .blend used!"),)

                    elif (scat_op.biocrea_storage_type=="centralized"):
                        txt = prp.column(align=True)
                        txt.active = False
                        txt.scale_y = 0.8
                        txt.label(text=translate("What's the name of the centralized .blend?"))
                        prp.prop(scat_op,"biocrea_centralized_blend",text="")

                else:
                    txt = s2.column(align=True)
                    txt.active = False
                    txt.scale_y = 0.9
                    txt.separator(factor=1)
                    word_wrap(layout=txt, alignment="LEFT", max_char=50, string=translate("With this option we cannot export objects containing linked meshes/ materials/ images or textures!"),)

                s2.separator()

                txt = s2.column(align=True)
                txt.scale_y = 0.8
                txt.label(text=translate("Geo-Scatter will create the Following Files :"))
                one_exists = False
                
                #biome file

                rtxt = txt.row()
                rtxt.active = False
                if ( os.path.exists(os.path.join(scat_op.biocrea_creation_directory,f"{BASENAME}.biome")) ):
                    rtxt.alert = True
                    one_exists = True 
                rtxt.label(text=f" - ''{BASENAME}.biome''")
                
                #blend file

                if (not scat_op.biocrea_external_blend_allow):
                    rtxt = txt.row()
                    rtxt.active = False
                    if ( os.path.exists(os.path.join(scat_op.biocrea_creation_directory,f"{BLENDNAME}.blend")) ):
                        rtxt.alert = True
                        one_exists = True 
                    rtxt.label(text=f" - ''{BLENDNAME}.blend''")

                for i,p in enumerate(psys):
                    PRESETNAME = f"{BASENAME}.layer{i:02}"
                    rtxt = txt.row()
                    rtxt.active = False
                    if ( os.path.exists(os.path.join(scat_op.biocrea_creation_directory,f"{PRESETNAME}.preset")) ):
                        rtxt.alert = True
                        one_exists = True 
                    rtxt.label(text=f" - ''{PRESETNAME}.preset''")

                s2.separator()

                overw = s2.row()
                overw.alert = one_exists
                overw.prop(scat_op,"biocrea_overwrite",)

                s2.separator()

                txt = s2.column(align=True)
                txt.scale_y = 0.8
                if (scat_op.biocrea_external_blend_allow):
                    if (scat_op.biocrea_storage_type=="individual"):
                        txt.label(text=translate("These assets need to be linked:"),)
                    elif (scat_op.biocrea_storage_type=="centralized"):
                        txt.label(text=translate("These Assets needs to be in")+f" '{scat_op.biocrea_centralized_blend}' :",)
                else: 
                    txt.label(text=translate("These Assets will be exported in new .blend :"),)

                to_export = set( o for p in psys for o in p.get_instances_obj() )                
                if (len(to_export)):
                    for o in to_export:
                        rtxt = txt.row()
                        rtxt.active = False
                        rtxt.label(text=f" - ''{o.name}''")
                else:
                    rtxt = txt.row()
                    rtxt.alert = True
                    rtxt.active = False
                    rtxt.label(text="  "+translate("No Instances Found!"),)

                s2.separator(factor=2.5)
                self.draw_steps(s2, steps=steps,)

            #draw step 3/3

            elif (steps==2):

                txt = s2.column(align=True)
                txt.active = False
                txt.scale_y = 0.8
                txt.label(text=translate("Preset Generation Options :"))
                s2.separator(factor=0.5)

                s2.prop(scat_op, "biocrea_use_random_seed",)
                s2.prop(scat_op, "biocrea_texture_is_unique",)
                s2.prop(scat_op, "biocrea_texture_random_loc",)

                s2.separator(factor=2)

                txt = s2.column(align=True)
                txt.active = False
                txt.scale_y = 0.8
                txt.label(text=translate("Biome Informations :"))
                s2.separator(factor=0.5)

                s2.prop(scat_op,"biocrea_file_author")
                s2.prop(scat_op,"biocrea_file_website")
                s2.prop(scat_op,"biocrea_file_description")
                s2.prop(scat_op,"biocrea_file_keywords")

                s2opt = s2.row()
                s2optlbl = s2opt.row()
                s2optlbl.scale_x = 0.54
                s2optlbl.label(text=" ")
                s2opt.prop(scat_op,"biocrea_keyword_from_instances")

                s2.separator(factor=1)
                word_wrap(layout=s2, alignment="LEFT", max_char=50, string=translate("Note that icons can be generated in the biome context menu."))

                s2.separator(factor=1)
                s2.prop(scat_op,"biocrea_auto_reload_all")

                s2.separator(factor=2.5)
                self.draw_steps(s2, steps=steps,)

            ui_templates.separator_box_in(box)

        return 


    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        scat_op    = scat_scene.operators.save_biome_to_disk_dialog
        emitter    = scat_scene.emitter
        psys       = emitter.scatter5.get_psys_selected()
        
        #create biome directory if non existing
        if (not os.path.exists(scat_op.biocrea_creation_directory)):
            pathlib.Path(scat_op.biocrea_creation_directory).mkdir(parents=True, exist_ok=True)

        #get .biome file general info
        biome_dict = {}
        biome_dict["info"] = {}
        biome_dict["info"]["name"] = scat_op.biocrea_biome_name
        biome_dict["info"]["type"] = "Biome"
        biome_dict["info"]["keywords"] = scat_op.biocrea_file_keywords
        biome_dict["info"]["author"] = scat_op.biocrea_file_author
        biome_dict["info"]["website"] = scat_op.biocrea_file_website
        biome_dict["info"]["description"] = scat_op.biocrea_file_description
        biome_dict["info"]["layercount"] = 0
        biome_dict["info"]["estimated_density"] = 0

        to_export = []
        BASENAME = legal(scat_op.biocrea_biome_name.lower().replace(" ","_"))
        BLENDNAME = f"{BASENAME}.instances" #noted as "BASENAME.instances" within the text file -> no .blend extension 
        
        #for all psys 
        for i,p in enumerate(psys): 

            #get file name
            PRESETNAME = f"{BASENAME}.layer{i:02}" #noted as "BASENAME.layer00.preset" within the text file

            #gather instances
            psy_instance = p.get_instances_obj()
            if (len(psy_instance)==0):
                bpy.ops.scatter5.popup_menu(
                    msgs=translate("This scatter-system do not have any instances : ")+f"'{p.name}'",
                    title=translate("Biome Creation Failed"),
                    icon="ERROR",
                    )
                return {'FINISHED'}

            #& add them to general list if need export
            if (not scat_op.biocrea_external_blend_allow):
                to_export += psy_instance

            #fill .biome file information
            ii = f"{i:02}"
            biome_dict[ii] = {}
            biome_dict[ii]["name"] = p.name
            biome_dict[ii]["color"] = tuple(p.s_color)[:3]
            biome_dict[ii]["preset"] = f"BASENAME.layer{i:02}.preset"

            #fill blend file name information
            if (scat_op.biocrea_external_blend_allow):

                #find back the blend names from linked objects?
                if (scat_op.biocrea_storage_type=="individual"):

                    #user might do bs here, need to be foolproof
                    for o in psy_instance:
                        if (o.data.library is None):
                            bpy.ops.scatter5.popup_menu(
                                msgs=translate("You chose a biome export behavior that rely on linked objects. The following object is not linked: ")+f"'{o.name}'",
                                title=translate("Biome Creation Failed"),
                                icon="ERROR",
                                )
                            return {'FINISHED'}

                    #if all .blend reference are the same, then we just need to encode a single blend
                    if (len(set(o.data.library.name for o in psy_instance))==1):
                        biome_dict[ii]["asset_file"] = psy_instance[0].data.library.name.replace(".blend","")
                        biome_dict[ii]["instances"] = [o.name for o in psy_instance]

                    #otherwise we need to encode the name of the .blend per instances
                    else:
                        biome_dict[ii]["asset_file"] = "INSTANCES_DEFINED"
                        biome_dict[ii]["instances"] = [(o.name,o.data.library.name.replace(".blend","")) for o in psy_instance]
                
                #objects from a single centralized blend?
                elif (scat_op.biocrea_storage_type=="centralized"):
                    biome_dict[ii]["asset_file"] = scat_op.biocrea_centralized_blend.replace(".blend","")
                    biome_dict[ii]["instances"] = [o.name for o in psy_instance]
            
            #will export below
            else: 
                biome_dict[ii]["asset_file"] = f"BASENAME.instances"
                biome_dict[ii]["instances"] = [o.name for o in psy_instance]

            #encode display placeholder? 
            if (scat_op.biocrea_use_biome_display):

                biome_dict[ii]["display"] = {}
                biome_dict[ii]["display"]["s_display_method"] = p.s_display_method

                biome_dict[ii]["display"]["s_display_placeholder_type"] = p.s_display_placeholder_type
                biome_dict[ii]["display"]["s_display_placeholder_scale"] = tuple(p.s_display_placeholder_scale)

                biome_dict[ii]["display"]["s_display_point_radius"] = p.s_display_point_radius
                biome_dict[ii]["display"]["s_display_cloud_radius"] = p.s_display_cloud_radius
                biome_dict[ii]["display"]["s_display_cloud_density"] = p.s_display_cloud_density

                biome_dict[ii]["display"]["s_display_camdist_allow"] = p.s_display_camdist_allow
                biome_dict[ii]["display"]["s_display_camdist_distance"] = p.s_display_camdist_distance

                biome_dict[ii]["display"]["s_display_viewport_method"] = p.s_display_viewport_method

                #need to also export model for special custom
                if (p.s_display_method=="placeholder_custom"):
                    #only exports if custom assigned
                    if (p.s_display_custom_placeholder_ptr is not None):
                        biome_dict[ii]["display"]["s_display_custom_placeholder_ptr"] = p.s_display_custom_placeholder_ptr.name
                        #if need to export, also export custom placeholder objects
                        if (not scat_op.biocrea_external_blend_allow):
                            to_export.append(p.s_display_custom_placeholder_ptr)

            ######## WRITE PRESETS

            #export psy settings as new .preset 
            d = settings_to_dict(p,
                use_random_seed=scat_op.biocrea_use_random_seed,
                texture_is_unique=scat_op.biocrea_texture_is_unique,
                texture_random_loc=scat_op.biocrea_texture_random_loc,
                ) 

            d["name"] = f""
            d["s_color"] = [0,0,0]

            #write psy settings a .preset file
            if ( os.path.exists( os.path.join(scat_op.biocrea_creation_directory, f"{PRESETNAME}.preset")) and (not scat_op.biocrea_overwrite) ):
                bpy.ops.scatter5.popup_menu(msgs=translate("File already exists!\nOverwriting not allowed."),title=translate("Preset Creation Skipped"),icon="ERROR")
                continue 

            dict_to_json(d, path=scat_op.biocrea_creation_directory, file_name=PRESETNAME, extension=".preset",)

            #add to density information
            biome_dict["info"]["layercount"] +=1
            biome_dict["info"]["estimated_density"] += d["estimated_density"]

            ######## AUTOMATIC KEYWORD? 

            if (scat_op.biocrea_keyword_from_instances):

                #automatice keywords from instances names?
                names = [ o.name for o in psy_instance ]
                #remove repetitive digits
                name_removedigit = lambda name: ''.join([s for s in name if not s.isdigit()])
                names = [ name_removedigit(name) for name in names ]
                #remove underscores
                names = [ name.replace("_"," ") for name in names ]
                #split points
                name_split = lambda name: name.split(".")[0] if ("." in name) else name
                names = [ name_split(name) for name in names ]
                #get old kw 
                current_kw = biome_dict["info"]["keywords"].split(",")
                #merge lists
                new_kw = set( name.title() for name in list(current_kw+names) )
                #potentially remove empty kw
                new_kw = [name for name in new_kw if name]
                #reassign
                biome_dict["info"]["keywords"] = ",".join(new_kw)

            continue

        ######## WRITE BLEND

        if (not scat_op.biocrea_external_blend_allow):

            #get .blend file path
            biome_blend_path = os.path.join( scat_op.biocrea_creation_directory, f"{BLENDNAME}.blend",)

            #exists?
            if ( os.path.exists( biome_blend_path) and (not scat_op.biocrea_overwrite) ):
                bpy.ops.scatter5.popup_menu(msgs=translate("File already exists!\nOverwriting not allowed."),title=translate("Biome Creation Skipped"),icon="ERROR")
                return {'FINISHED'} 

            to_export = list(set(to_export)) #remove double! not sure if list needed tho, perhaps we can keep it as a set.
            utils.import_utils.export_objects( biome_blend_path, to_export,)

        ######## WRITE BIOMES

        #get .biome file path
        biome_json_path = os.path.join( scat_op.biocrea_creation_directory, f"{BASENAME}.biome",)
        
        #exists?
        if ( os.path.exists( biome_json_path) and (not scat_op.biocrea_overwrite) ):
            bpy.ops.scatter5.popup_menu(msgs=translate("File already exists!\nOverwriting not allowed."),title=translate("Biome Creation Skipped"),icon="ERROR")
            return {'FINISHED'} 
        
        #write json file
        with open(biome_json_path, 'w') as f:
            json.dump(biome_dict, f, indent=4)

        #reload library
        if (scat_op.biocrea_auto_reload_all):
            bpy.ops.scatter5.reload_biome_library()

        return {'FINISHED'}


# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo.   ooo. .oo.  .oo.    .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88b  `P  )88b  `888P"Y88bP"Y88b  d88' `88b
#  888`88b.    888ooo888  888   888   .oP"888   888   888   888  888ooo888
#  888  `88b.  888    .o  888   888  d8(  888   888   888   888  888    .o
# o888o  o888o `Y8bod8P' o888o o888o `Y888""8o o888o o888o o888o `Y8bod8P'



class SCATTER5_OT_rename_biome(bpy.types.Operator): 
    """rename a biome json/files""" 

    bl_idname      = "scatter5.rename_biome"
    bl_label       = "Rename Operator" 
    bl_description = translate("Rename this .biome name and file(s)")
    bl_options     = {'INTERNAL','UNDO'}

    path : bpy.props.StringProperty()
    old_name : bpy.props.StringProperty()
    new_name : bpy.props.StringProperty(default="New Name")
    replace_files_names : bpy.props.BoolProperty(default=True)

    def invoke(self, context, event):
        
        if (not os.path.exists(self.path)):
            raise Exception(f"Biome path ''{self.path}'' Not found!")   

        return bpy.context.window_manager.invoke_props_dialog(self)

    def get_linked_files(self):
        """return a list of all paths that scatter5 believe are linked with the given biome"""
            
        old_paths = []
        new_paths = []

        old_basename = os.path.basename(self.path).replace(".biome","")
        new_basename = self.new_name.replace(" ","_").lower()
        
        folder = os.path.dirname(self.path)

        for f in os.listdir(folder):
            if (f.startswith(old_basename+".")):

                old_p = os.path.join(folder,f)
                old_paths.append(old_p)

                new_p_basename = f.replace(old_basename+".",new_basename+".")
                new_p = os.path.join(folder,new_p_basename)
                new_paths.append(new_p)

        return old_paths,new_paths

    def draw(self, context):
        layout  = self.layout

        box, is_open = ui_templates.box_panel(self, layout, 
            prop_str = "ui_dialog_presetsave", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_dialog_presetsave";UI_BOOL_VAL:"1"
            icon = "FONT_DATA", 
            name = translate("Rename Biome"),
            )
        if is_open:

            prop = box.column(align=True)
            prop.label(text=translate("Old Name")+":")
            nm = prop.row()
            nm.enabled = False
            nm.prop(self,"old_name",text="",)

            prop = box.column(align=True)
            prop.label(text=translate("New Name")+":")
            prop.prop(self,"new_name",text="",)

            box.prop(self,"replace_files_names",text=translate("Also Replace Files Names"))

            lbl = box.column(align=True)
            lbl.scale_y = 0.8
            lbl.active = False
            lbl.label(text=" "+translate("Geo-Scatter will do the following operations:"))
            lbl.label(text="     \u2022 "+translate("Change the name information from:"))
            lbl.label(text=f"           '{os.path.basename(self.path)}'")

            if (self.replace_files_names):
                for p in self.get_linked_files()[0]:
                    lbl.label(text=f"     \u2022 "+translate("Replace a file name."))
                    lbl.label(text=f"           '{os.path.basename(p)}'")

            lbl.separator()

        layout.separator()
        return 

    def execute(self, context):

        if (self.old_name.lower()==self.new_name.lower()) or (self.new_name==""):
            bpy.ops.scatter5.popup_menu(msgs=translate("Please choose a correct name"),title=translate("Renaming not possible"),icon="ERROR")
            return {'FINISHED'}      

        if (self.replace_files_names):
            old_paths,new_paths = self.get_linked_files()
            
            for p in new_paths:
                if (os.path.exists(p,)):
                    bpy.ops.scatter5.popup_menu(msgs=translate("There's already files with the following basename.")+f"\n {self.new_name.replace(' ','_').lower()}",title=translate("Renaming not possible"),icon="ERROR")
                    return {'FINISHED'}

        #Replace Biome Name 

        with open(self.path) as f:
            d = json.load(f)

        d["info"]["name"]=self.new_name.title()

        with open(self.path, 'w') as f:
            json.dump(d, f, indent=4)

        #change element name for live feedback

        bpy.context.window_manager.scatter5.library[self.path].user_name = self.new_name.title()

        #Replace File Names

        if (self.replace_files_names):
            bpy.context.window_manager.scatter5.library[self.path].name = new_paths[0]
            for p,n in zip(old_paths,new_paths):
                os.rename(p,n)

        return {'FINISHED'}


class SCATTER5_OT_refresh_biome_estimated_density(bpy.types.Operator): 
    """rename a biome json/files""" 

    bl_idname      = "scatter5.refresh_biome_estimated_density"
    bl_label       = "Rename Operator" 
    bl_description = translate("")
    bl_options     = {'INTERNAL','UNDO'}

    path : bpy.props.StringProperty()

    def execute(self, context):

        if (not os.path.exists(self.path)):
            print("'",self.path,"'")
            raise Exception("refresh_biome_estimated_density() self.path Do Not Exist")

        with open(self.path) as f:
            biome_dict = json.load(f)

        assert "info" in biome_dict
        assert "estimated_density" in biome_dict["info"]

        #reset density
        biome_dict["info"]["estimated_density"] = 0

        for i, (key, value) in enumerate(biome_dict.items()):

            if (key.isdigit()):

                json_preset_path = search_biome_file(
                    file_name=value["preset"],
                    biome_path=self.path,
                    raise_exception=True,
                    )

                with open(json_preset_path) as f:
                    d = json.load(f)
                    assert "estimated_density" in d
                    biome_dict["info"]["estimated_density"] += d["estimated_density"]

        with open(self.path, 'w') as f:
            json.dump(biome_dict, f, indent=4,)

        return {'FINISHED'}


classes = (
    
    SCATTER5_OT_add_biome,
    SCATTER5_OT_load_biome,

    SCATTER5_OT_material_confirm,
    SCATTER5_OT_save_biome_to_disk_dialog,
    SCATTER5_OT_rename_biome,
    SCATTER5_OT_refresh_biome_estimated_density,

    )