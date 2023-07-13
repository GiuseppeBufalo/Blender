
#####################################################################################################
#
#       .o.             .o8        .o8       ooooooooo.
#      .888.           "888       "888       `888   `Y88.
#     .8"888.      .oooo888   .oooo888        888   .d88'  .oooo.o oooo    ooo
#    .8' `888.    d88' `888  d88' `888        888ooo88P'  d88(  "8  `88.  .8'
#   .88ooo8888.   888   888  888   888        888         `"Y88b.    `88..8'
#  .8'     `888.  888   888  888   888        888         o.  )88b    `888'
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o888o        8""888P'     .8'
#                                                                  .o..P'
#                                                                  `Y8P'
#####################################################################################################

import bpy, os, time, random
from mathutils import Vector

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. utils.import_utils import import_selected_assets
from .. utils.path_utils import json_to_dict
from .. utils.event_utils import get_mouse_context

from .. manual import brushes

from . import presetting

from . instances import find_compatible_instances
from . emitter import find_compatible_surfaces

from .. ui.ui_creation import find_preset_name

from .. widgets.infobox import SC5InfoBox, generic_infobox_setup
from .. utils.draw_utils import add_font, clear_all_fonts


"""
Important info:

-ScatterDensity/ScatterPreset/ScatterManual/ScatterBiomes operators use their own scat_scene.operators settings
 see in ops_settings.py: 
    - scat_ops.create_operators
    - scat_ops.add_psy_preset
    - scat_ops.add_psy_density
    - scat_ops.add_psy_manual
    - scat_ops.add_psy_modal
    - scat_ops.load_biome

-ScatterDensity & ScatterBiomes are derrivate of ScatterPreset operator

-Structure Graph: 

          ┌──────────────────┐
          │ add_psy_virgin() │
          └─┬─────┬───────┬──┘
            │     │       │
            │     │       │ ┌──────────────┐-> security features
┌───────────▼──┐  │       └─►add_psy_preset│-> complete visibility & display
│add_psy_simple│  │         └─┬────────────┘-> special mask assignation
└──────────────┘  │           │             
     ┌────────────▼─┐         │ ┌───────────────┐
     │add_psy_manual│         ├─►add_psy_density│
     └───▲──────────┘         │ └───────────────┘
         !                    │
         !                    │ ┌─────────────────┐
         !                    ├─►add_biome_layer()│
         !                    │ └─┬───────────────┘
         !  ┌─────────────┐   │   │
         !  │add_psy_modal◄───┘   │ ┌─────────┐
         !  └───▲─────────┘       ├─►add_biome│ for scripts
         !      !                 │ └─────────┘
         !      !                 │
     ┌---┴------┴--------┐        │ ┌──────────┐
     |  define_add_psy   |        └─►load_biome│ for ux/ui
     └-------------------┘          └──────────┘
                                  

"""


# oooooooooooo               .
# `888'     `8             .o8
#  888          .ooooo.  .o888oo
#  888oooo8    d88' `"Y8   888
#  888    "    888         888
#  888         888   .o8   888 .
# o888o        `Y8bod8P'   "888"

#REMARK: we could use some class inheritence instead of functions in there


def estimate_future_instance_count(
    surfaces=[],
    d=None,
    preset_density=None,
    preset_keyword="",
    refresh_square_area=True,
    ctxt_operator="" #add_psy_preset, add_psy_density ect..
    ):
    """estimate a future particle count of a scatter-system before it's created by looking at preset and emitting surface(s)
    
    parameters: either pass settings_dict `d` or pass `preset_density`&`preset_keyword` """

    # Note that this estimation calculation is also done in  ui_creation.draw_scattering(self,layout) for preset GUI prupose...
    # some on creation options can affect final particle count, however not all can be taken into consideration. this is an appromaximative forecast

    scat_scene   = bpy.context.scene.scatter5
    scat_ops     = scat_scene.operators
    scat_op_ctxt = getattr(scat_ops,ctxt_operator)
    scat_op_crea = scat_ops.create_operators

    #creation settings we'll take into consideration 
    f_ = ctxt_f_settings(ctxt_operator=ctxt_operator,)
    count = 0

    if (f_["f_visibility_hide_viewport"]):
        return 0

    if (f_["f_visibility_cam_allow"]):
        return 0

    if (f_["f_mask_action_method"]=="paint"):
        return 0

    #if passed a preset, then we have to fill preset_density & preset_keyword
    if (d is not None):
        preset_density = d["estimated_density"] if ("estimated_density" in d) else 0
        preset_keyword = ""
        if ("s_distribution_space" in d):
            preset_keyword += " "+d["s_distribution_space"]
        if ("s_distribution_method" in d):
            preset_keyword += " "+d["s_distribution_method"]

    if (preset_keyword==""): #Should not be possible
        return -1

    if ("manual_all" in preset_keyword):
        return 0

    if ("random_stable" in preset_keyword):
        return 0

    if ("verts" in preset_keyword):
        return sum( len(s.data.vertices) for s in surfaces )

    if ("faces" in preset_keyword):
        return sum( len(s.data.polygons) for s in surfaces )

    if ("edges" in preset_keyword):
        return sum( len(s.data.edges) for s in surfaces )

    #most common, other distribution modes are exotic
    if ( ("random" in preset_keyword) or ("clumping" in preset_keyword) ):

        #estimate surface area
        square_area = 0
        for s in surfaces:
            surface_area = s.scatter5.estimate_square_area() if refresh_square_area else s.scatter5.estimated_square_area
            if ("global" in preset_keyword):
                surface_area *= sum(s.scale)/3
            square_area += surface_area
            continue

        #estimate selection square area if selection
        if (f_["f_visibility_facepreview_allow"]): 
            square_area = sum(s.scatter5.s_visibility_facepreview_area for s in surfaces)

        #Instance-Count
        count = int(square_area*preset_density)

        #viewport % reduction
        if (f_["f_visibility_view_allow"]):
            count = (count/100)*(100-f_["f_visibility_view_percentage"])

    #estimate count if visibility method engaged
    if (f_["f_visibility_maxload_allow"]):
        if (count>f_["f_visibility_maxload_treshold"]):
            if (f_["f_visibility_maxload_cull_method"]=="maxload_shutdown"):
                return 0
            elif (f_["f_visibility_maxload_cull_method"]=="maxload_limit"):
                return f_["f_visibility_maxload_treshold"]

    return count


def utils_find_args(context, pop_msg=True, emitter_name="", surfaces_names="", instances_names="", selection_mode="viewport", psy_name="default", psy_color=(1,1,1), psy_color_random=False,):
    """utility function to define emitter, surfaces, instances, psy name&color quickly"""

    scat_scene = context.scene.scatter5

    #Get Emitter

    emitter = bpy.data.objects.get(emitter_name)
    if (emitter is None):
        emitter = scat_scene.emitter
    if (emitter is None):
        
        if (pop_msg):
            msg = translate("\nNo emitter found.\n")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
        
        print("utils_find_args: Error, no emitter found")
        return {'FINISHED'}

    #Get Surfaces (from given names passed)

    l = [ bpy.data.objects[n] for n in surfaces_names.split("_!#!_") if n in context.scene.objects ]
    surfaces = list(find_compatible_surfaces(l))
    #no surfaces found? 
    if (len(surfaces)==0):
        
        if (pop_msg):
            msg = translate("\nNo valid surface(s) found.\nPlease Define your Surfaces.\n")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
        
        print("utils_find_args: Error, no surfaces found")
        return {'FINISHED'}

    #Get Instances (either find selection in asset browser or selection)

    if (selection_mode=="browser"):
        l = import_selected_assets(link=(scat_scene.objects_import_method=="LINK"),)
    elif (selection_mode=="viewport"):
        if (instances_names==""):
              l = [ o for o in bpy.context.selected_objects if (o.type=="MESH") ]
        else: l = [ bpy.data.objects[n] for n in instances_names.split("_!#!_") if n in bpy.data.objects ] #pass object or not?
    instances = list(find_compatible_instances(l, emitter=emitter,))
    #no instances found?
    if (len(instances)==0):
        
        if (pop_msg):

            if (selection_mode=="viewport"):
                msg = translate("\nNo valid object(s) found in selection.\n\nPlease select the object(s) you want to Scatter in the viewport.\n")
            
            elif (selection_mode=="browser"):
                if (bpy.context.window):
                    browsers_found = [a for w in bpy.context.window_manager.windows for a in w.screen.areas if (a.ui_type=="ASSETS")]
                    msg = translate("\nWe haven't found an asset-browser editor open.\n\nThis selection-method works with the blender asset-browser.\n")
                    if (len(browsers_found)==1):
                        msg = translate("\nNo Asset(s) selected in the asset-browser.\n")
                    elif (len(browsers_found)>1):
                        msg = translate("\nNo Asset(s) selected in the asset-browser.\n\nIt looks like many browser(s) are opened? We picked the first one.\n")
                else:
                    print("utils_find_args: Warning, no support for this operator in blender headless, it relies on window selection")
            
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)

        print("utils_find_args: Error, no instances found")
        return {'FINISHED'}

    #Set Color & name 

    #Give default name is name is empty
    if (psy_name in [""," ","  ","   ","    "]):
        psy_name = "No Name"
    #support for automatic name finding
    if (psy_name=="*AUTO*"):
        psy_name = find_preset_name(instances) #auto color is done at ui level
    #random color
    if (psy_color_random):
        psy_color = [random.uniform(0, 1),random.uniform(0, 1),random.uniform(0, 1),]

    return psy_name, psy_color, emitter, surfaces, instances



def ctxt_f_settings(scope_ref={}, ctxt_operator=""):
    """define future settings depending on ass_psy_preset | add_psy_density | load_biome ect...
    because settings supports vary depending on operators"""

    scat_scene   = bpy.context.scene.scatter5
    scat_ops     = scat_scene.operators
    scat_op_ctxt = getattr(scat_ops,ctxt_operator)
    scat_op_crea = scat_ops.create_operators

    d = {}

    #quick scatter or manual scatter do not support hide or hide %

    if (ctxt_operator not in ("add_psy_modal","add_psy_manual")):
        d["f_visibility_hide_viewport"] = scat_op_crea.f_visibility_hide_viewport
        d["f_visibility_view_allow"] = scat_op_crea.f_visibility_view_allow
        d["f_visibility_view_percentage"] = scat_op_crea.f_visibility_view_percentage
    else: 
        d["f_visibility_hide_viewport"] = False
        d["f_visibility_view_allow"] = False
        d["f_visibility_view_percentage"] = 0

    #manual scatter do not support any visibility settings

    if (ctxt_operator not in ("add_psy_manual")):
        d["f_visibility_facepreview_allow"] = scat_op_crea.f_visibility_facepreview_allow

        d["f_visibility_cam_allow"] = scat_op_crea.f_visibility_cam_allow
        d["f_visibility_camclip_allow"] = scat_op_crea.f_visibility_camclip_allow
        d["f_visibility_camclip_cam_boost_xy"] = scat_op_crea.f_visibility_camclip_cam_boost_xy
        d["f_visibility_camdist_allow"] = scat_op_crea.f_visibility_camdist_allow
        d["f_visibility_camdist_min"] = scat_op_crea.f_visibility_camdist_min
        d["f_visibility_camdist_max"] = scat_op_crea.f_visibility_camdist_max

        d["f_visibility_maxload_allow"] = scat_op_crea.f_visibility_maxload_allow
        d["f_visibility_maxload_cull_method"] = scat_op_crea.f_visibility_maxload_cull_method
        d["f_visibility_maxload_treshold"] = scat_op_crea.f_visibility_maxload_treshold
    else: 
        d["f_visibility_facepreview_allow"] = False

        d["f_visibility_cam_allow"] = False
        d["f_visibility_camclip_allow"] = False
        d["f_visibility_camclip_cam_boost_xy"] = 0
        d["f_visibility_camdist_allow"] = False
        d["f_visibility_camdist_min"] = 0
        d["f_visibility_camdist_max"] = 0

        d["f_visibility_maxload_allow"] = False
        d["f_visibility_maxload_cull_method"] = 0
        d["f_visibility_maxload_treshold"] = 0

    #biomes ignore display settings, they use their own encoded display in .biome format

    if (ctxt_operator not in ("load_biome")):
        d["f_display_allow"] = scat_op_crea.f_display_allow
        d["f_display_method"] = scat_op_crea.f_display_method
        d["f_display_custom_placeholder_ptr"] = scat_op_crea.f_display_custom_placeholder_ptr
    else: 
        d["f_display_allow"] = False
        d["f_display_method"] = None
        d["f_display_custom_placeholder_ptr"] = None

    d["f_display_bounding_box"] = scat_op_crea.f_display_bounding_box

    #operators that do not support special masks will automatically ignore the following

    d["f_mask_action_method"] = getattr( scat_op_ctxt, "f_mask_action_method", "none",)
    d["f_mask_action_type"] = getattr( scat_op_ctxt, "f_mask_action_type", None,)
    d["f_mask_assign_vg"] = getattr( scat_op_ctxt, "f_mask_assign_vg", None,)
    d["f_mask_assign_bitmap"] = getattr( scat_op_ctxt, "f_mask_assign_bitmap", None,)
    d["f_mask_assign_curve_area"] = getattr( scat_op_ctxt, "f_mask_assign_curve_area", None,)
    d["f_mask_assign_reverse"] = getattr( scat_op_ctxt, "f_mask_assign_reverse", None,)
    d["f_mask_paint_vg"] = getattr( scat_op_ctxt, "f_mask_paint_vg", None,)
    d["f_mask_paint_bitmap"] = getattr( scat_op_ctxt, "f_mask_paint_bitmap", None,)
    d["f_mask_paint_curve_area"] = getattr( scat_op_ctxt, "f_mask_paint_curve_area", None,)

    #security settings, quick scatter & manual do not need them

    if (ctxt_operator not in ("add_psy_modal","add_psy_manual")):
        d["f_sec_count_allow"] = scat_op_crea.f_sec_count_allow
    else:
        d["f_sec_count_allow"] = False

    d["f_sec_count"] = scat_op_crea.f_sec_count
    d["f_sec_verts_allow"] = scat_op_crea.f_sec_verts_allow
    d["f_sec_verts"] = scat_op_crea.f_sec_verts

    #load new variable in scope 
    scope_ref.update(d)
    return d


def ctxt_f_action(context, p=None, d={}, surfaces=None, instances=None, pop_msg=True, ctxt_operator="",):
    """depending on ctxt_f tweak scatter-system"""

    #load f_settings in current scope
    f_ = ctxt_f_settings(ctxt_operator=ctxt_operator,)

    #Visibility Settings 

    if (f_["f_visibility_facepreview_allow"]): #Face Preview
        p.s_visibility_facepreview_allow = True

    if (f_["f_visibility_view_allow"]): #Viewport % Optimization
        p.s_visibility_view_allow = True
        p.s_visibility_view_percentage = f_["f_visibility_view_percentage"]

    if (f_["f_visibility_cam_allow"]): #Camera Optimization
        p.s_visibility_cam_allow = True

        p.s_visibility_camclip_allow = f_["f_visibility_camclip_allow"]
        if (f_["f_visibility_camclip_allow"]):
            p.s_visibility_camclip_cam_boost_xy = [f_["f_visibility_camclip_cam_boost_xy"]]*2
        
        p.s_visibility_camdist_allow = f_["f_visibility_camdist_allow"]
        if (f_["f_visibility_camdist_allow"]):
            p.s_visibility_camdist_min = f_["f_visibility_camdist_min"]
            p.s_visibility_camdist_max = f_["f_visibility_camdist_max"]

    if (f_["f_visibility_maxload_allow"]): #Maximal Load
        p.s_visibility_maxload_allow = True 
        p.s_visibility_maxload_cull_method = f_["f_visibility_maxload_cull_method"]
        p.s_visibility_maxload_treshold = f_["f_visibility_maxload_treshold"]

     #Display Settings

    if (f_["f_display_allow"]):
        p.s_display_allow = True
        if (f_["f_display_method"]!="none"):
            p.s_display_method = f_["f_display_method"]
            if (f_["f_display_method"]=="placeholder_custom"):
                p.s_display_custom_placeholder_ptr = f_["f_display_custom_placeholder_ptr"]

    if (f_["f_display_bounding_box"]): #BoundingBox Display of instances
        for o in instances:
            o.display_type="BOUNDS"

    #Special Actions

    if (f_["f_mask_action_method"]!="none"):

        #biome have a their own implementation for direct-paint, we just assign them
        
        if ( (ctxt_operator=="load_biome") and (f_["f_mask_action_method"]=="paint") ):
            f_["f_mask_action_method"] = "assign"
            f_["f_mask_assign_vg"] = f_["f_mask_paint_vg"]
            f_["f_mask_assign_bitmap"] = f_["f_mask_paint_bitmap"]
            f_["f_mask_assign_curve_area"] = f_["f_mask_paint_curve_area"]
            f_["f_mask_assign_reverse"] = f_["f_mask_assign_reverse"] = f_["f_mask_assign_reverse"] = True

        #direct paint a mask?

        if (f_["f_mask_action_method"]=="paint"):

            if (f_["f_mask_action_type"]=="vg"):
                
                #find name not taken, across all surfaces
                i = 1
                vg_name =  "DirectPaint"
                while vg_name in [v.name for o in surfaces for v in o.vertex_groups]:
                    vg_name = f"DirectPaint.{i:03}"
                    i += 1
                for s in surfaces:
                    s.vertex_groups.new(name=vg_name)
                p.s_mask_vg_allow = True
                p.s_mask_vg_ptr = vg_name
                p.s_mask_vg_revert = True
                bpy.ops.scatter5.vg_quick_paint(mode="vg", group_name=vg_name, use_surfaces=True,)

            elif (f_["f_mask_action_type"]=="bitmap"):

                img = bpy.data.images.new("ImageMask", 1000, 1000,)
                p.s_mask_bitmap_allow = True
                p.s_mask_bitmap_ptr = img.name
                p.s_mask_bitmap_revert = True
                bpy.ops.scatter5.image_utils(option="paint", paint_color=(1,1,1), img_name=img.name,)

            elif (f_["f_mask_action_type"]=="curve"):

                bez = bpy.data.curves.new("BezierArea","CURVE")
                bez.dimensions = '3D'
                cur = bpy.data.objects.new(bez.name,bez)
                cur.location = context.scene.cursor.location
                context.scene.collection.objects.link(cur)
                p.s_mask_curve_allow = True
                p.s_mask_curve_ptr = cur
                p.s_mask_curve_revert = True
                
                #bezier area drawing has special context requisite

                for window in context.window_manager.windows:
                    screen = window.screen
                    for area in screen.areas:
                        if (area.type == 'VIEW_3D'):
                            # NOTE: use first found.. but because this is non modal operator call i have no event and therefore i have no access to mouse location so i can't compare with region coordinates and dimensions.. so i need to use what i got.
                            region = None
                            for r in area.regions:
                                if (r.type == 'WINDOW'):
                                    region = r
                                    break
                            if (region is not None):
                                override = {'window':window, 'screen':screen, 'area':area, 'region':region, }
                                # NOTE: override context AND use invoke at the same time! third param is use undo, operator adds its own undo state, so this is not needed (i hope?)
                                bpy.ops.scatter5.draw_bezier_area(override, 'INVOKE_DEFAULT', False, edit_existing=cur.name, )
                                break

         #or just assign mask?

        elif (f_["f_mask_action_method"]=="assign"):

            if (f_["f_mask_action_type"]=="vg"):
                p.s_mask_vg_allow = True
                p.s_mask_vg_ptr = f_["f_mask_assign_vg"]
                p.s_mask_vg_revert = f_["f_mask_assign_reverse"]

            elif (f_["f_mask_action_type"]=="bitmap"):
                p.s_mask_bitmap_allow = True
                p.s_mask_bitmap_ptr = f_["f_mask_assign_bitmap"]
                p.s_mask_bitmap_revert = f_["f_mask_assign_reverse"]

            elif (f_["f_mask_action_type"]=="curve"):
                p.s_mask_curve_allow = True
                p.s_mask_curve_ptr = f_["f_mask_assign_curve_area"]
                p.s_mask_curve_revert = f_["f_mask_assign_reverse"]


    #Unhiding the system is always done at the end 
    #for optimization purpose & security 

    #by default, always visible
    is_visible = True

    #will pop security msg?
    pop_msg_scatter = False
    pop_msg_poly = False
    max_poly = 0

    #except if creation settings is overriding
    if (f_["f_visibility_hide_viewport"]):
        is_visible = False

    #Security Threshold Estimated Particle Count
    if (f_["f_sec_count_allow"]):

        if (d!={}):
            count = estimate_future_instance_count(
                surfaces=surfaces, 
                d=d, 
                refresh_square_area=True,
                ctxt_operator=ctxt_operator,
                )
        else:
            count = estimate_future_instance_count(
                surfaces=surfaces,
                preset_density=p.s_distribution_density,
                preset_keyword=p.s_distribution_method,
                refresh_square_area=True,
                ctxt_operator=ctxt_operator,
                )

        if (count>f_["f_sec_count"]):

            is_visible = False
            pop_msg_scatter = True

    #Security Threshold Instance Polycount
    if (f_["f_sec_verts_allow"]):

        too_high_poly = [o for o in instances if ( (o.type=="MESH") and (o.display_type!="BOUNDS") and (len(o.data.vertices)>=f_["f_sec_verts"]) ) ]
        if (len(too_high_poly)!=0):
            pop_msg_poly = True
            for o in too_high_poly:
                o.display_type = "BOUNDS"
                continue

    #finally, shall we show the system in viewport?
    if (is_visible):
        p.hide_viewport = False

    #Pop security message with additional options?
    if ((pop_msg) and (pop_msg_poly or pop_msg_scatter)):
        bpy.ops.scatter5.popup_security('INVOKE_DEFAULT', scatter=pop_msg_scatter, poly=pop_msg_poly, emitter=p.id_data.name, psy_name_00=p.name,)

    return None

#################################################################################################################################
#
#   .oooooo.                                    .    o8o                               .oooooo.
#  d8P'  `Y8b                                 .o8    `"'                              d8P'  `Y8b
# 888          oooo d8b  .ooooo.   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.        888      888 oo.ooooo.   .oooo.o
# 888          `888""8P d88' `88b `P  )88b    888   `888  d88' `88b `888P"Y88b       888      888  888' `88b d88(  "8
# 888           888     888ooo888  .oP"888    888    888  888   888  888   888       888      888  888   888 `"Y88b.
# `88b    ooo   888     888    .o d8(  888    888 .  888  888   888  888   888       `88b    d88'  888   888 o.  )88b
#  `Y8bood8P'  d888b    `Y8bod8P' `Y888""8o   "888" o888o `Y8bod8P' o888o o888o       `Y8bood8P'   888bod8P' 8""888P'
#                                                                                                  888
#                                                                                                 o888o
#################################################################################################################################


#  .oooooo..o  o8o                               oooo                  .oooooo..o                         .       .
# d8P'    `Y8  `"'                               `888                 d8P'    `Y8                       .o8     .o8
# Y88bo.      oooo  ooo. .oo.  .oo.   oo.ooooo.   888   .ooooo.       Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  `"Y8888o.  `888  `888P"Y88bP"Y88b   888' `88b  888  d88' `88b       `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
#      `"Y88b  888   888   888   888   888   888  888  888ooo888           `"Y88b 888        .oP"888    888     888   888ooo888  888
# oo     .d8P  888   888   888   888   888   888  888  888    .o      oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
# 8""88888P'  o888o o888o o888o o888o  888bod8P' o888o `Y8bod8P'      8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b
#                                      888
#                                     o888o


class SCATTER5_OT_add_psy_simple(bpy.types.Operator):

    bl_idname      = "scatter5.add_psy_simple"
    bl_label       = translate("Add a default Scatter-System")
    bl_description = translate("This operator will add a simple Scatter-system with default settings on the selected surface(s). By default there will be no instances in your instancing collection, so we'll display the scatter as single points.")
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) 

    psy_name : bpy.props.StringProperty(default="Default", options={"SKIP_SAVE",},)
    psy_color : bpy.props.FloatVectorProperty(default=(1,1,1), options={"SKIP_SAVE",},)
    psy_color_random : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    
    def invoke(self, context, event):

        #Get Emitter
        self.emitter = bpy.data.objects.get(self.emitter_name)
        if (self.emitter is None):
            self.emitter = context.scene.scatter5.emitter

        #Correct if no name or empty name
        if (self.psy_name in [""," ","  ","   ","    "]): #meh
            self.psy_name = "No Name"

        #Get Color 
        self.psy_color = [random.uniform(0, 1),random.uniform(0, 1),random.uniform(0, 1),] if self.psy_color_random else self.psy_color

        #Alt workflow
        if (event.alt):

            #Get Surfaces
            if (self.surfaces_names):
                  self.surfaces = [ bpy.data.objects[n] for n in self.surfaces_names.split("_!#!_") if n in bpy.data.objects ]
            else: self.surfaces = []
            self.instances = []

        #Standard behavior
        else: 
            #Get instances
            if (self.instances_names):
                  obj_list = [ bpy.data.objects[n] for n in self.instances_names.split("_!#!_") if n in bpy.data.objects ]
            else: obj_list = []
            self.instances = list(find_compatible_instances(obj_list, emitter=self.emitter,))
            self.surfaces = []

        return self.execute(context) 

    def execute(self, context):

        emitter = self.emitter
        if (emitter is None):
            return {'FINISHED'}

        #ignore any properties update behavior, such as update delay or hotkeys
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):

            #create virgin psy
            p = emitter.scatter5.add_psy_virgin(
                psy_name=self.psy_name,
                psy_color=self.psy_color,
                deselect_all=True,
                instances=self.instances,
                surfaces=self.surfaces,
                )

            #display as point?
            if (len(self.instances)==0):
                p.s_display_allow = True
                p.s_display_method = "point"

            p.s_distribution_density = 0.222
            p.s_distribution_is_random_seed = True
            p.hide_viewport = False

        return {'FINISHED'}


# ooooooooo.                                             .         .oooooo..o                         .       .
# `888   `Y88.                                         .o8        d8P'    `Y8                       .o8     .o8
#  888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo      Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888         `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
#  888          888     888ooo888 `"Y88b.  888ooo888   888             `"Y88b 888        .oP"888    888     888   888ooo888  888
#  888          888     888    .o o.  )88b 888    .o   888 .      oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
# o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"      8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b


#Example

# bpy.ops.scatter5.add_psy_preset(
#     psy_name="New Psy Test",
#     psy_color = (1,1,1),
#     psy_color_random= False,
#     emitter_name="Plane",
#     selection_mode="viewport",
#     instances_names="Instance Cube_!#!_Suzanne_!#!_Cube",
#     json_path="C:/Users/Dude/Desktop/testing.json",
#     )


class SCATTER5_OT_add_psy_preset(bpy.types.Operator):
    """main scattering operator for user in 'Creation>Scatter' if running this from script, note that there are a few globals parameters that could have an influence over this operation, such as the security features"""

    #this operator parameters are automatically configuired in the ui_creation interface

    bl_idname      = "scatter5.add_psy_preset"
    bl_label       = translate("Add a Scatter-System from Chosen Preset")
    bl_description = translate("Scatter the selected item with the active preset settings on the chosen emitter target object.")
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    selection_mode : bpy.props.StringProperty(default="viewport", options={"SKIP_SAVE",},) #"browser"/"viewport"
    
    psy_name : bpy.props.StringProperty(default="NewPsy", options={"SKIP_SAVE",},) #use "*AUTO*" to automatically find name and color
    psy_color : bpy.props.FloatVectorProperty(default=(1,1,1), options={"SKIP_SAVE",},)
    psy_color_random : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    json_path : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #string = json preset path, if not will use active preset
    settings_override : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #set settings via text format "prop_api:value_override,next_prop:next_override"

    ctxt_operator : bpy.props.StringProperty(default="add_psy_preset", options={"SKIP_SAVE",},) #define settings that will influence creation behavior

    pop_msg : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)

    def execute(self, context):

        scat_scene   = context.scene.scatter5
        scat_ops     = scat_scene.operators
        scat_op_crea = scat_ops.create_operators

        r = utils_find_args(context,
            pop_msg=self.pop_msg,
            emitter_name=self.emitter_name,
            surfaces_names=self.surfaces_names,
            instances_names=self.instances_names,
            selection_mode=self.selection_mode,
            psy_name=self.psy_name,
            psy_color=self.psy_color,
            psy_color_random=self.psy_color_random,
            )

        if (r=={'FINISHED'}):
            return {'FINISHED'}

        self.psy_name, self.psy_color, emitter, surfaces, instances = r

        #ignore any properties update behavior, such as update delay or hotkeys
        with scat_scene.factory_update_pause(event=True,delay=True,sync=True):

            #create virgin psy
            p = emitter.scatter5.add_psy_virgin(
                psy_name=self.psy_name,
                psy_color=self.psy_color,
                deselect_all=True,
                instances=instances,
                surfaces=surfaces,
                )

            #load json preset to settings
            d = {}

            #user don't want to apply any preset ? if so use default ""
            if (self.json_path==""):
                pass

            #if preset not exists, inform user
            elif (not os.path.exists(self.json_path)):
                if (self.pop_msg):
                    bpy.ops.scatter5.popup_menu(msgs=translate("Broken preset path detected")+f"\n {self.json_path}", title=translate("Warning"),icon="ERROR",)

            #paste preset to settings
            else:
                d = json_to_dict(
                    path=os.path.dirname(self.json_path),
                    file_name=os.path.basename(self.json_path),
                    )
                presetting.dict_to_settings( d, p,) #default "s_filter" argument, should be fit for basic preset usage, aka no s_surface,s_mask,s_visibility,s_display

                #refresh ecosystem dependencies?
                for ps in emitter.scatter5.particle_systems:
                    if (ps!=p):
                        if (ps.s_ecosystem_affinity_allow):
                            for i in (1,2,3):
                                if (getattr(ps,f"s_ecosystem_affinity_{i:02}_ptr")==p.name):
                                    setattr(ps,f"s_ecosystem_affinity_{i:02}_ptr",p.name)
                        if (ps.s_ecosystem_repulsion_allow):
                            for i in (1,2,3):
                                if (getattr(ps,f"s_ecosystem_repulsion_{i:02}_ptr")==p.name):
                                    setattr(ps,f"s_ecosystem_repulsion_{i:02}_ptr",p.name)

            #Settings override via text?
            if (self.settings_override!=""):
                for prop_value in self.settings_override.split(","):
                    prop,value = prop_value.split(":")
                    if (hasattr(p,prop)):
                        setattr(p,prop,eval(value))

            #now need to evaluate f_display/f_visibility/f_mask & f_security settings on this psy
            ctxt_f_action(context, 
                p=p,
                d=d,
                surfaces=surfaces,
                instances=instances,
                pop_msg=self.pop_msg,
                ctxt_operator=self.ctxt_operator,
                )

        return {'FINISHED'}


# oooooooooo.                                   o8o      .                     .oooooo..o                         .       .
# `888'   `Y8b                                  `"'    .o8                    d8P'    `Y8                       .o8     .o8
#  888      888  .ooooo.  ooo. .oo.    .oooo.o oooo  .o888oo oooo    ooo      Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  888      888 d88' `88b `888P"Y88b  d88(  "8 `888    888    `88.  .8'        `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
#  888      888 888ooo888  888   888  `"Y88b.   888    888     `88..8'             `"Y88b 888        .oP"888    888     888   888ooo888  888
#  888     d88' 888    .o  888   888  o.  )88b  888    888 .    `888'         oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
# o888bood8P'   `Y8bod8P' o888o o888o 8""888P' o888o   "888"     .8'          8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b
#                                                            .o..P'
#                                                            `Y8P'

class SCATTER5_OT_add_psy_density(bpy.types.Operator):
    """running add_psy_preset w/o using presets and overriding with own density & default settings"""

    bl_idname      = "scatter5.add_psy_density"
    bl_label       = translate("Add a Scatter-System with given density")
    bl_description = translate("Scatter the selected item with the given particle density value")
    bl_options     = {'INTERNAL','UNDO'}
    
    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    selection_mode : bpy.props.StringProperty(default="viewport", options={"SKIP_SAVE",},) #"browser"/"viewport"

    psy_name : bpy.props.StringProperty(default="DensityScatter")
    psy_color : bpy.props.FloatVectorProperty(default=(0.220, 0.215, 0.200), options={"SKIP_SAVE",},)
    psy_color_random : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    density_value : bpy.props.FloatProperty(default=10.0, options={"SKIP_SAVE",},)
    density_scale : bpy.props.StringProperty(default="m", options={"SKIP_SAVE",},)

    pop_msg : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)

    def execute(self, context):

        #adjust density depending on scale
        if   (self.density_scale=="cm"): self.density_value*=10_000
        elif (self.density_scale=="ha"): self.density_value*=0.0001
        elif (self.density_scale=="km"): self.density_value*=0.000001

        #override settings, instead of dumping a .preset text file, there's the option to feed a string containing props instruction, directly like this
        d = f"s_distribution_density:{self.density_value},s_distribution_is_random_seed:True,s_rot_align_z_allow:True,s_rot_align_y_allow:True,s_rot_align_y_method:'meth_align_y_random'"

        bpy.ops.scatter5.add_psy_preset(
            emitter_name=self.emitter_name,
            surfaces_names=self.surfaces_names,
            selection_mode=self.selection_mode,
            instances_names=self.instances_names,
            psy_name=self.psy_name,
            psy_color=self.psy_color,
            psy_color_random=self.psy_color_random,
            ctxt_operator="add_psy_density", #using the f_visibility/f_display/f_mask ect.. of this ctxt_operator
            settings_override=d, #dont use  json path, use settings override instead
            pop_msg=self.pop_msg,
            )

        return {'FINISHED'}



# ooo        ooooo                                             oooo        .oooooo..o                         .       .
# `88.       .888'                                             `888       d8P'    `Y8                       .o8     .o8
#  888b     d'888   .oooo.   ooo. .oo.   oooo  oooo   .oooo.    888       Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  8 Y88. .P  888  `P  )88b  `888P"Y88b  `888  `888  `P  )88b   888        `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
#  8  `888'   888   .oP"888   888   888   888   888   .oP"888   888            `"Y88b 888        .oP"888    888     888   888ooo888  888
#  8    Y     888  d8(  888   888   888   888   888  d8(  888   888       oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
# o8o        o888o `Y888""8o o888o o888o  `V88V"V8P' `Y888""8o o888o      8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b


add_psy_manual_context_override = None 

class SCATTER5_OT_add_psy_manual(bpy.types.Operator):

    bl_idname      = "scatter5.add_psy_manual"
    bl_label       = translate("Add a manual-distribution Scatter-System")
    bl_description = translate("Add a Scatter-System and directly enter manual distribution mode")
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    selection_mode : bpy.props.StringProperty(default="viewport", options={"SKIP_SAVE",},)
    
    psy_name : bpy.props.StringProperty(default="ManualScatter", options={"SKIP_SAVE",},)
    psy_color : bpy.props.FloatVectorProperty(default=(0.495, 0.484, 0.449), options={"SKIP_SAVE",},)
    psy_color_random : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    
    pop_msg : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)

    def execute(self, context):

        scat_scene   = context.scene.scatter5
        scat_ops     = scat_scene.operators
        scat_op_crea = scat_ops.create_operators

        r = utils_find_args(context,
            pop_msg=self.pop_msg,
            emitter_name=self.emitter_name,
            surfaces_names=self.surfaces_names,
            instances_names=self.instances_names,
            selection_mode=self.selection_mode,
            psy_name=self.psy_name,
            psy_color=self.psy_color,
            psy_color_random=self.psy_color_random,
            )

        if (r=={'FINISHED'}):
            return {'FINISHED'}

        self.psy_name, self.psy_color, emitter, surfaces, instances = r

        #create virgin psy & set to manual distribution

        p = emitter.scatter5.add_psy_virgin(
            psy_name=self.psy_name,
            psy_color=self.psy_color,
            deselect_all=True,
            instances=instances,
            surfaces=surfaces,
            )

        p.s_distribution_method = "manual_all"
        p.s_rot_random_allow = scat_scene.operators.add_psy_manual.f_rot_random_allow
        p.s_scale_random_allow = scat_scene.operators.add_psy_manual.f_scale_random_allow

        #now need to evaluate f_display,f_sec ect..

        ctxt_f_action(context, 
            p=p,
            surfaces=surfaces,
            instances=instances,
            pop_msg=self.pop_msg,
            ctxt_operator="add_psy_manual",
            )

        #force unhide psy
        p.hide_viewport = False

        #override in case if user is calling this operator `from scatter5.define_add_psy`
        global add_psy_manual_context_override
        if (add_psy_manual_context_override is not None):
            exec(f"bpy.ops.scatter5.manual_enter(add_psy_manual_context_override,'INVOKE_DEFAULT',)")
            add_psy_manual_context_override = None 
        else: 
            exec(f"bpy.ops.scatter5.manual_enter('INVOKE_DEFAULT')")

        return {'FINISHED'}

#   .oooooo.                   o8o            oooo              .oooooo..o                         .       .
#  d8P'  `Y8b                  `"'            `888             d8P'    `Y8                       .o8     .o8
# 888      888    oooo  oooo  oooo   .ooooo.   888  oooo       Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
# 888      888    `888  `888  `888  d88' `"Y8  888 .8P'         `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
# 888      888     888   888   888  888        888888.              `"Y88b 888        .oP"888    888     888   888ooo888  888
# `88b    d88b     888   888   888  888   .o8  888 `88b.       oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
#  `Y8bood8P'Ybd'  `V88V"V8P' o888o `Y8bod8P' o888o o888o      8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b


class SCATTER5_OT_define_add_psy(bpy.types.Operator):
    """define dynamic selection for surfaces or instances, 
    here only used for the add_psy_modal operator"""

    bl_idname      = "scatter5.define_add_psy"
    bl_label       = translate("Quick Scatter")
    bl_description = translate("Quick Scatter")

    operator_context : bpy.props.StringProperty(default="", options={"SKIP_SAVE","HIDDEN"},)
    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE","HIDDEN"},)

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    @classmethod
    def poll(cls,context,):
        if (context.mode!="OBJECT"):
            return False
        if (context.area.type not in ("VIEW_3D","FILE_BROWSER")):
            return False
        if (context.scene.scatter5.emitter is None):
            return False
        return True

    def invoke(self, context, event):

        self.areatype = context.area.type
        self.areaicon = "VIEW3D" if (self.areatype=="VIEW_3D") else "ASSET_MANAGER"
        self.areamode = "viewport" if (self.areatype=="VIEW_3D") else "browser"

        if (self.operator_context!=""):
            self.execute(context)
            return {'FINISHED'}

        #Draw Menu

        def draw(self, context):

            layout = self.layout
            pie = layout.menu_pie()

            #left
            op = pie.operator("scatter5.define_add_psy", text=translate("Manual Scatter"), icon="BRUSHES_ALL",)
            op.operator_context = "manual"
            op.description = translate("Directly enter manual mode with the selected objects or assets as your future instances")
            
            #right
            op = pie.operator("scatter5.define_add_psy", text="..."+translate("Vgroup Mask"), icon="TEMP",)
            op.operator_context = "vg"
            op.description = translate("Directly scatter and enter vertex group paint mode with the selected objects or assets as your future instances")
                
            #low
            
            col = pie.box().column()
            col.scale_x = 1.2
            
            scat_scene = bpy.context.scene.scatter5
            scat_ops = scat_scene.operators
            scat_op_crea = scat_ops.create_operators

            if (len(scat_op_crea.f_surfaces)!=0):
                lis = col.box().column(align=True)
                lis.scale_y = 0.85
                
                for i,o in enumerate(scat_op_crea.get_f_surfaces()): 
                    if (o.name!=""):
                        lisr = lis.row()
                        lisr.label(text=o.name)

            op = col.operator("scatter5.define_add_psy", text = translate("Redefine Surfaces"), icon="RESTRICT_SELECT_OFF",)
            op.operator_context = "surfdefine"
            op.description = translate("Redefine your future Surfaces")

            #top
            op = pie.operator("scatter5.define_add_psy", text = "..."+translate("Image Mask"), icon="TEMP",)
            op.operator_context = "bitmap"
            op.description = translate("Directly scatter and enter bitmap painting mode with the selected objects or assets as your future instances")
            
            #top left
            op = pie.operator("scatter5.define_add_psy", text = translate("Modal Scatter"), icon="TEMP",)
            op.operator_context = "standard"
            op.description = translate("Directly scatter with the selected objects or assets as your future instances")
            
            #top right
            op = pie.operator("scatter5.define_add_psy", text = "..."+translate("Bezier-Area Mask"), icon="TEMP",)
            op.operator_context = "curve"
            op.description = translate("Directly scatter and enter bezier area drawing mode with the selected objects or assets as your future instances")
            
            #low left
            pie.separator()
                
            #low right
            pie.separator()

            return None 

        bpy.context.window_manager.popup_menu_pie(event, draw, title=translate("Quick Scatter"), icon=self.areaicon,)

        return {'FINISHED'}

    def execute(self,context,):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        scat_ops = scat_scene.operators
        scat_op_crea = scat_ops.create_operators

        if (self.operator_context == "surfdefine"):

            scat_op_crea.f_surface_method = "collection"
            scat_op_crea.f_surfaces.clear()
            scat_op_crea.add_selection()

        #Operator Conditions

        elif (self.operator_context in ["vg","bitmap","standard","curve","manual"]):

            #Get Surfaces from operator settings

            l = scat_op_crea.get_f_surfaces()
            surfaces = list(find_compatible_surfaces(l))

            #no surfaces found? 
            if (len(surfaces)==0):
                
                msg = translate("\nNo valid surface(s) found.\nPlease Define your Surfaces.\n")
                bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
                
                print("utils_find_args: Error, no surfaces found")
                return {'FINISHED'}

            #Get Instances (either find selection in asset browser or selection)

            if (self.areamode=="browser"):
                l = import_selected_assets(link=(scat_scene.objects_import_method=="LINK"),)
            elif (self.areamode=="viewport"):
                l = [ o for o in bpy.context.selected_objects if (o.type=="MESH") ]
            instances = list(find_compatible_instances(l, emitter=emitter,))
            
            #no instances found?
            if (len(instances)==0):
            
                if (self.areamode=="viewport"):
                    msg = translate("\nNo valid object(s) found in selection.\n\nPlease select the object(s) you want to Scatter in the viewport.\n")
                
                elif (self.areamode=="browser"):
                    if (bpy.context.window):
                        browsers_found = [a for w in bpy.context.window_manager.windows for a in w.screen.areas if (a.ui_type=="ASSETS")]
                        msg = translate("\nWe haven't found an asset-browser editor open.\n\nThis selection-method works with the blender asset-browser.\n")
                        if (len(browsers_found)==1):
                            msg = translate("\nNo Asset(s) selected in the asset-browser.\n")
                        elif (len(browsers_found)>1):
                            msg = translate("\nNo Asset(s) selected in the asset-browser.\n\nIt looks like many browser(s) are opened? We picked the first one.\n")
                    else:
                        print("utils_find_args: Warning, no support for this operator in blender headless, it relies on window selection")
                
                bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
                return {'FINISHED'}
                
            #Launch operators

            if (self.operator_context in ["vg","bitmap","standard","curve",]):

                bpy.ops.scatter5.add_psy_modal('INVOKE_DEFAULT',
                    emitter_name=emitter.name,
                    surfaces_names="_!#!_".join(o.name for o in surfaces),
                    instances_names="_!#!_".join(o.name for o in instances),
                    default_startup=self.operator_context.replace("standard",""),
                    )

            elif (self.operator_context=="manual"):

                #Need context override..

                kwargs = {
                    "emitter_name":emitter.name,
                    "surfaces_names":"_!#!_".join(o.name for o in surfaces),
                    "instances_names":"_!#!_".join(o.name for o in instances),
                    "psy_color_random":True,
                    "selection_mode":self.areamode,
                    "pop_msg":False,
                    }

                #need to support manual from asset browser context

                if (self.areatype=="FILE_BROWSER"):

                    for window in bpy.context.window_manager.windows:
                        screen = window.screen
                        for area in screen.areas:
                            if(area.type == 'VIEW_3D'):
                                region = None
                                for r in area.regions:
                                    if(r.type == 'WINDOW'):
                                        region = r
                                        break
                                if region is not None:
                                    override = {'window': window, 'screen': screen, 'area': area, 'region': region, }
                                    global add_psy_manual_context_override 
                                    add_psy_manual_context_override = override
                                    bpy.ops.scatter5.add_psy_manual(override,('EXEC_DEFAULT'),**kwargs)
                                    break

                else:
                    bpy.ops.scatter5.add_psy_manual(('EXEC_DEFAULT'),**kwargs)

        return {'FINISHED'}




# class SCATTER5_OT_define_add_psy(bpy.types.Operator):
#     """define dynamic selection for surfaces or instances, 
#     here only used for the add_psy_modal operator"""

#     #PROBLEM: this operator does not support finding assets from other bpy.screens very annoying
#     #context is very limited while in modal, not cool, no way to update it.. i tried a trick, get_mouse_context() but did not work
#     #i have absolutely no idea how to do this, because windows can overlap the comparing mouse with area dimensions trick won't work...

#     bl_idname      = "scatter5.define_add_psy"
#     bl_label       = translate("Define Scatter")
#     bl_description = translate("Define Scatter")

#     emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE","HIDDEN"},)
#     instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE","HIDDEN"},)
#     surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE","HIDDEN"},)

#     is_running = False

#     @classmethod
#     def poll(cls, context,):
#         return (context.mode=="OBJECT") and\
#                (context.area.type in ("VIEW_3D","FILE_BROWSER")) and\
#                (not cls.is_running) and\
#                (not SCATTER5_OT_add_psy_modal.is_running)
    
#     class InfoBox_define_add_psy(SC5InfoBox):
#         pass

#     def __init__(self):
#         self.press_I = self.press_V = self.press_L = self.press_M = False
        
#         self.delay_set = {} #delay between shortcuts, for more flexible shortcut detection

#         if (self.emitter_name==""):
#             self.emitter_name = bpy.context.scene.scatter5.emitter.name
#         return None

#     def set_surfaces(self, context, event, sel=[],):
#         self.surfaces_names = "_!#!_".join(o.name for o in sel)
#         self.define_ctxt()
#         return None

#     def set_instances(self, context, event, sel=[],):
#         #asset browser
#         if (self.is_in_region(context, event)):
#             sel = import_selected_assets(link=(bpy.context.scene.scatter5.objects_import_method=="LINK"),)
#             if (len(sel)==0):
#                 return None
#         self.instances_names = "_!#!_".join(o.name for o in sel)
#         self.define_ctxt()
#         return None

#     def define_ctxt(self,):

#         from . instances import find_compatible_instances
#         from . emitter import find_compatible_surfaces

#         if (self.surfaces_names==""):
#             self.ctxt = "surfaces"
#             self.ctxt_title = translate("Surfaces(s)")
#             self.filterfct = find_compatible_surfaces
#             self.ctxt_set = self.set_surfaces
#             return None 

#         if (self.instances_names==""):
#             self.ctxt = "instances"
#             self.ctxt_title = translate("Instance(s)")
#             self.filterfct = find_compatible_instances
#             self.ctxt_set = self.set_instances
#             return None 

#         return None

#     def is_in_region(self, context, event, region_match="FILE_BROWSER"):
#         """TODO this function do not work properly when user is in other window, often the case for asset browser windows..."""

#         def in_area(mouse_x, mouse_y, area,):
#             x = area.x
#             y = area.y
#             w = area.width
#             h = area.height
#             if (mouse_x > x and mouse_x < x + w):
#                 if (mouse_y > y and mouse_y < y + h):
#                     return True
#             return False
            
#         for a in context.screen.areas:
#             if (a.type==region_match):
#                 if in_area(event.mouse_x, event.mouse_y, a,):
#                     return True
        
#         return False

#     def draw_ctxt_box(self, context, i=0, is_browser=False,):

#         if (self.InfoBox_define_add_psy._initialized):
#             self.InfoBox_define_add_psy.deinit()

#         title = f'{translate("Select the future")} {self.ctxt_title}'
#         subtitle = f'{i} {self.ctxt_title} {translate("Found")}'
#         lines = [
#             "• "+translate("Press 'ENTER' to Confirm"),
#             "───────────────────────────────────────────",
#             "• "+translate("Press 'ESC' to Cancel"),
#             ]

#         #special indication if final surfaces indication
#         if (self.ctxt=="instances"):
#             lines = [
#                 "• "+translate("Press 'ENTER' to Finalize"),
#                 "• "+translate("Press 'V+ENTER' for Vgroup Painting"),
#                 "• "+translate("Press 'L+ENTER' for Lasso Painting"),
#                 "• "+translate("Press 'I+ENTER' for Image Painting"),
#                 "• "+translate("Press 'M+ENTER' for Manual Mode"),
#                 "───────────────────────────────────────────",
#                 "• "+translate("Press 'ESC' to Cancel"),
#                 ]

#         #special subtitle if instances method and cursot in assetbrowser
#         if (is_browser and self.ctxt=="instances"):
#             subtitle = translate("Selecting Items in the Asset-Browser")

#         #add infobox on screen
#         t = generic_infobox_setup(title,subtitle,lines,)

#         self.InfoBox_define_add_psy.init(t)

#         return None 

#     def invoke(self, context, event):

#         #the purpose of this operator is to fill these fieald, if not filled, just skip
#         if ( (self.instances_names!="") and (self.surfaces_names!="") ):
#             self.confirm(context,event)
#             return {'FINISHED'}

#         #define default context
#         self.define_ctxt()

#         #start modal
#         context.window_manager.modal_handler_add(self)

#         cls = type(self)
#         cls.is_running = True 

#         return {'RUNNING_MODAL'}

#     def modal(self, context, event):

#         sel = list(self.filterfct(context.selected_objects))

#         self.draw_ctxt_box(context,
#             i=len(sel),
#             is_browser=self.is_in_region(context, event, region_match="FILE_BROWSER"),
#             )

#         if (event.type=='ESC'):
#             self.quit(context)
#             return {'FINISHED'}

#         #fill args with selections

#         if ( (event.type=='RET') and (event.value=="RELEASE") ): #avoid users keep pressing enter & too quick of a selection
#             self.ctxt_set(context, event, sel=sel,)

#         #are we done ? 

#         if ( (self.instances_names!="") and (self.surfaces_names!="") ):
#             self.confirm(context,event)
#             self.quit(context)
#             return {'FINISHED'}

#         #delay shortcut, otherwise key combination is too strict
#         if (len(self.delay_set)):
#             for k,v in self.delay_set.items():
#                 if (v>20):
#                     setattr(self,k,False)
#                     del self.delay_set[k]
#                 else:
#                     self.delay_set[k] +=1

#         #define shorcuts 
#         if (event.type=='I'):
#             if (event.value=="PRESS"):
#                 self.press_I = True
#             elif (event.value!="PRESS"):
#                 self.delay_set["press_I"] = 1 #add delay
#             return {'RUNNING_MODAL'}

#         elif (event.type=='V'):
#             if (event.value=="PRESS"):
#                 self.press_V = True
#             elif (event.value!="PRESS"):
#                 self.delay_set["press_V"] = 1 #add delay
#             return {'RUNNING_MODAL'}

#         elif (event.type=='L'):
#             if (event.value=="PRESS"):
#                 self.press_L = True
#             elif (event.value!="PRESS"):
#                 self.delay_set["press_L"] = 1 #add delay
#             return {'RUNNING_MODAL'}

#         elif (event.type=='M'):
#             if (event.value=="PRESS"):
#                 self.press_M = True
#             elif (event.value!="PRESS"):
#                 self.delay_set["press_M"] = 1 #add delay
#             return {'RUNNING_MODAL'}

#         return {'PASS_THROUGH'}

#     def quit(self, context):

#         if (self.InfoBox_define_add_psy._initialized):
#             self.InfoBox_define_add_psy.deinit()

#         cls = type(self)
#         cls.is_running = False 

#         return None 

#     def confirm(self, context, event):
        
#         if (self.press_M):

#             bpy.ops.scatter5.add_psy_manual('INVOKE_DEFAULT',
#                 emitter_name=self.emitter_name,
#                 surfaces_names=self.surfaces_names,
#                 instances_names=self.instances_names,
#                 )

#             return None 

#         bpy.ops.scatter5.add_psy_modal('INVOKE_DEFAULT',
#             emitter_name=self.emitter_name,
#             surfaces_names=self.surfaces_names,
#             instances_names=self.instances_names,
#             default_startup="vg" if self.press_V else "curve" if self.press_L else "bitmap" if self.press_I else "",
#             )

#         return None 



quickscatter_keymaps = []

def register_quickscatter_shortcuts():
    
    if (bpy.app.background):
        return None
    
    #add hotkey
    wm  = bpy.context.window_manager
    kc  = wm.keyconfigs.addon
    km  = kc.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
    kmi = km.keymap_items.new("scatter5.define_add_psy", 'W', 'PRESS', shift=True, alt=True, ctrl=True,)

    quickscatter_keymaps.append(kmi)

    return None

def unregister_quickscatter_shortcuts():

    if (bpy.app.background):
        return None

    #remove hotkey
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps["Window"]
    for kmi in quickscatter_keymaps:
        km.keymap_items.remove(kmi)
    quickscatter_keymaps.clear()

    return None



class SCATTER5_OT_add_psy_modal(bpy.types.Operator):

    bl_idname      = "scatter5.add_psy_modal"
    bl_label       = translate("Quickly scatter the selected object(s), then change few settings directly in modal mode.")
    bl_description = translate("Quickly scatter the selected object(s), then change few settings directly in modal mode.")
    
    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) 
    default_startup : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #"vg"|"bitmap"|"curve"

    p = None
    is_running = False
    recursive_launch = False

    def __init__(self):
        self.is_density_D = self.is_scale_S = self.is_brightness_B = self.is_transforms_T = False
        return None 

    class InfoBox_add_psy_modal(SC5InfoBox):
        pass

    def invoke(self, context, event):
        cls = type(self)

        scat_scene = context.scene.scatter5
        scat_op = scat_scene.operators.add_psy_modal

        #Get Emitter

        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter
        if (emitter is None):
            raise Exception("add_psy_modal: Need an emitter object")

        #if user is relaunching, ,then we quit old loop, and start another loop soon

        """
        if (cls.is_running==True):

            cls.recursive_launch = True
            default_startup = str(self.default_startup)

            def launch_new_modal():
                nonlocal default_startup
                bpy.ops.scatter5.add_psy_modal(('INVOKE_DEFAULT'),default_startup=default_startup)
                #BUG here, when using draw_bezier_area, will lose the context 
                return None 

            bpy.app.timers.register(launch_new_modal, first_interval=0.1)
            return {'FINISHED'}
        """

        #set settings, normally these are in interface, here they are handled by the operator directly

        if (self.default_startup):
            scat_op.f_mask_action_method = "paint"
            scat_op.f_mask_action_type = self.default_startup
        else:
            scat_op.f_mask_action_method = "none"

        #override settings, instead of dumping a .preset text file

        density_value = scat_op.f_distribution_density
        override_dict_str = f"s_distribution_density:{density_value},s_distribution_is_random_seed:True,s_scale_default_allow:True,s_rot_align_z_allow:True,s_rot_align_y_allow:True,s_rot_align_y_method:'meth_align_y_random'"

        bpy.ops.scatter5.add_psy_preset(
            emitter_name=emitter.name,
            surfaces_names=self.surfaces_names,
            instances_names=self.instances_names,
            psy_name="QScatter",
            psy_color_random=True,
            settings_override=override_dict_str,
            ctxt_operator="add_psy_modal",
            pop_msg=True,
            )

        #save name for later
        self.p = emitter.scatter5.get_psy_active()

        #ignore any properties update behavior, such as update delay or hotkeys
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):

            # #add default vertex group
            # if (not self.p.s_mask_vg_allow):

            #     #TODO SURFACE
            #     vg = emitter.vertex_groups.new()
            #     vg.name = "Vgroup"
            #     self.p.s_mask_vg_allow = True
            #     self.p.s_mask_vg_ptr = vg.name

            #add default texture
            self.texture_node = self.p.get_scatter_mod().node_group.nodes["s_pattern1"].node_tree.nodes["texture"]
            self.texture_node.node_tree = self.texture_node.node_tree.copy()
            self.texture_node.node_tree.scatter5.texture.user_name = "QuickSatterTexture"
            self.texture_node.node_tree.scatter5.texture.mapping_random_allow = True 
            self.texture_node.node_tree.nodes["random_loc_switch"].mute = True

        #add infobox on screen
        t = generic_infobox_setup(translate("Quick Scatter Mode"),
                                  translate("Quickly adjust the settings with shortcuts below."),
                                  ["• "+translate("Press 'D+MOUSEWHEEL' to Adjust Density"),
                                   "• "+translate("Press 'S+MOUSEWHEEL' to Adjust Default Scale"),
                                   "• "+translate("Press 'R' to Randomize Seeds"),
                                   "• "+translate("Press 'P' to Toggle Pattern Slot 1"),
                                   "• "+translate("Press 'T+MOUSEWHEEL' to Adjust Pattern Transform Scale"),
                                   "• "+translate("Press 'B+MOUSEWHEEL' to Adjust Pattern Brightness"),
                                   "──────────────────────────────────────────────────────────",
                                   "• "+translate("Press 'SHIFT+MOUSEWHEEL' to Adjust With Precision"),
                                   "• "+translate("Press 'ESC' to Cancel"),
                                   "• "+translate("Press 'ENTER' to Confirm"),
                                   ],)
        self.InfoBox_add_psy_modal.init(t)

        #set global scatter5 mode
        context.window_manager.scatter5.mode = "PSY_MODAL"
        cls.is_running = True

        #start modal
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        cls = type(self)

        clear_all_fonts()

        #confirm event

        if ( (event.type=='RET') or cls.recursive_launch ):
            self.confirm(context)
            return {'FINISHED'}

        #cancel event

        if ( (event.type=='ESC') or (context.window_manager.scatter5.mode != "PSY_MODAL") ):
            self.cancel(context)
            return {'CANCELLED'}

        #shortcut detection?

        if (event.type=='D'):
            if (event.value=="PRESS"):
                self.is_density_D = True
            elif (event.value!="PRESS"):
                self.is_density_D = False

        elif (event.type=='S'):
            if (event.value=="PRESS"):
                self.is_scale_S = True
            elif (event.value!="PRESS"):
                self.is_scale_S = False

        elif (event.type=='R'):
            if (event.value!="PRESS"): #wait for release
                self.p.s_distribution_is_random_seed = True
                self.p.s_rot_align_y_is_random_seed = True
                if (self.p.s_pattern1_allow):
                    self.texture_node.node_tree.scatter5.texture.mapping_random_is_random_seed = True
            return {'RUNNING_MODAL'}

        elif (event.type=='P'):
            if (event.value!="PRESS"): #wait for release
                self.p.s_pattern1_allow = not self.p.s_pattern1_allow
            return {'RUNNING_MODAL'}

        elif ( (self.p.s_pattern1_allow) and (event.type=='B') ):
            if (event.value=="PRESS"):
                self.is_brightness_B = True
            elif (event.value!="PRESS"):
                self.is_brightness_B = False

        elif ( (self.p.s_pattern1_allow) and (event.type=='T') ):
            if (event.value=="PRESS"):
                self.is_transforms_T = True
            elif (event.value!="PRESS"):
                self.is_transforms_T = False

        #shortcut action

        if self.is_density_D:
            if (event.type=='WHEELUPMOUSE'):
                self.p.s_distribution_density += 0.1 if event.shift else 1
            elif (event.type=='WHEELDOWNMOUSE'):
                self.p.s_distribution_density -= 0.1 if event.shift else 1
            add_font(text=translate("Instances/m²")+f": {self.p.s_distribution_density:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}

        elif self.is_scale_S:
            if not self.p.s_scale_default_allow:
                self.p.s_scale_default_allow=True
            if (event.type=='WHEELUPMOUSE'):
                self.p.s_scale_default_value += Vector([0.01]*3) if event.shift else Vector([0.1]*3)
            elif (event.type=='WHEELDOWNMOUSE'):
                self.p.s_scale_default_value -= Vector([0.01]*3) if event.shift else Vector([0.1]*3)
            add_font(text=translate("Default Scale")+f": {self.p.s_scale_default_value[2]:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}

        if self.is_brightness_B:
            if (event.type=='WHEELUPMOUSE'):
                self.texture_node.node_tree.scatter5.texture.intensity += 0.01 if event.shift else 0.1
            elif (event.type=='WHEELDOWNMOUSE'):
                self.texture_node.node_tree.scatter5.texture.intensity -= 0.01 if event.shift else 0.1
            add_font(text=translate("Pattern Brightness")+f": {self.texture_node.node_tree.scatter5.texture.intensity:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}

        elif self.is_transforms_T:
            if (event.type=='WHEELUPMOUSE'):
                self.texture_node.node_tree.scatter5.texture.scale -= 0.01 if event.shift else 0.1
            elif (event.type=='WHEELDOWNMOUSE'):
                self.texture_node.node_tree.scatter5.texture.scale += 0.01 if event.shift else 0.1
            add_font(text=translate("Pattern Scale")+f": {self.texture_node.node_tree.scatter5.texture.scale:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def cancel(self, context):

        self.p.remove_psy()

        #what if created a curve area ?

        self.exit(context)
        return None

    def confirm(self, context):

        bpy.ops.ed.undo_push(message=translate("Quick Scatter Confirm"))

        self.exit(context)
        return None

    def exit(self, context):
        cls = type(self)

        #quit mode, if was in paint vg/texture
        if (context.mode!="OBJECT"):
            bpy.ops.object.mode_set(mode="OBJECT")

        context.window_manager.scatter5.mode = ""

        #reset modal
        cls.is_running = False
        cls.recursive_launch = False

        #clear indications
        self.InfoBox_add_psy_modal.deinit()

        return None


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_add_psy_simple,
    SCATTER5_OT_add_psy_density,
    SCATTER5_OT_add_psy_preset,
    SCATTER5_OT_add_psy_manual,

    SCATTER5_OT_define_add_psy,
    SCATTER5_OT_add_psy_modal,

    )

#if __name__ == "__main__":
#    register()