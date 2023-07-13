#pylint: disable=import-error, relative-beyond-top-level
import bpy
from . SMR_CALLBACK import SMR_callback
from . SMR_ADDMAIN import add_smr_base
from . SMR_ADDPART import define_mat_scale, add_subsetup, add_wear, normals_connect
from . influence_functions import add_influence

def preset_update (self, context):
    settings = bpy.context.scene.SMR
    if settings.creation_presets == 'Custom':
        return

    if settings.creation_presets == 'Brand New':
        du = False
        sm = True
        sc = True
        cw = False

        sm_str = .6
        sm_rand = False
        sm_bcm = 0
        bcm_col = 1,1,1,1
        bcm_rand = False

        sc_str = .03
        sc_rand = False

    elif settings.creation_presets == 'Dusty':
        du = True
        sm = False
        sc = False
        cw = False

        du_str = 4
        du_side = .1
        du_col = 1,1,1,1


    elif settings.creation_presets == 'Well Used':
        du = True
        sm = True
        sc = True
        cw = True

        du_str = .3
        du_side = .02
        du_col = 1,1,1,1

        sm_str = .7
        sm_rand = False
        sm_bcm = .2
        bcm_col = .1,.1,.1,1
        bcm_rand = True

        sc_str = .03
        sc_rand = True

        cw_col = .3,.3,.3,1
        cw_mult = 1

    elif settings.creation_presets == 'Very Old':   
        du = True
        sm = True
        sc = True
        cw = True

        du_str = 5
        du_side = .2
        du_col = .5,.5,.5,1

        sm_str = .8
        sm_rand = False
        sm_bcm = .2
        bcm_col = 0,0,0,1
        bcm_rand = True

        sc_str = .03
        sc_rand = True

        cw_col = .1,.1,.1,1
        cw_mult = 2


    settings.custom_exception = True
    ###########

    settings.auto_dust = du
    if du:
        settings.auto_dust_strength = du_str
        settings.auto_dust_side = du_side
        settings.auto_dust_color = du_col

    settings.auto_smudge = sm
    if sm:
        settings.auto_smudge_strength = sm_str
        settings.auto_smudge_random = sm_rand
        settings.auto_smudge_bcm = sm_bcm
        settings.auto_smudge_bcm_color = bcm_col
        settings.auto_smudge_bcm_random = bcm_rand

    settings.auto_scratch = sc
    if sc:
        settings.auto_scratch_strength = sc_str
        settings.auto_scratch_random = sc_rand

    settings.auto_cwear = cw
    if cw:
        settings.auto_cwear_color = cw_col
        settings.auto_cwear_mult = cw_mult

    #############
    settings.custom_exception = False

def set_custom (self, context):
    if bpy.context.scene.SMR.custom_exception:
        return
    bpy.context.scene.SMR.creation_presets = 'Custom'


class SMR_OT_AUTOMATIC(bpy.types.Operator):
    bl_idname = "smr.automatic"
    bl_label = "auto"
    bl_description = "auto"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):            
        if bpy.context.active_object.mode != 'OBJECT':
            self.report({'WARNING'}, 'You are not in object mode')
            return {'FINISHED'}
            
        old_active = context.active_object
        for obj in context.selected_objects:
            context.view_layer.objects.active = obj
            try:
                if 'SMR' in obj.active_material.node_tree.nodes:
                    continue
            except:
                continue

            SMR_callback(self)
            completed = add_smr_base(self, 'Normal')
            if not completed:
                continue
                
            settings = context.scene.SMR
            
            scale = define_mat_scale(context.active_object)

            if settings.auto_dust:
                add_subsetup('Dust')
                settings.dust_multiplier = settings.auto_dust_strength
                settings.dust_side = settings.auto_dust_side
                settings.dust_color = settings.auto_dust_color
                settings.dust_scale = scale
                settings.dust_genscale = scale


            if settings.auto_smudge:
                add_subsetup('Smudge')
                settings.smudge_falloff = settings.auto_smudge_strength
                settings.smudge_roughness = settings.auto_smudge_strength
                settings.smudge_bcm_intensity = settings.auto_smudge_bcm
                settings.smudge_bcm_color = settings.auto_smudge_bcm_color
                settings.smudge_scale = scale
                if settings.auto_smudge_bcm_random:
                    add_influence('SmBCM')
                    settings.smr_ui_categ = 'Smudge'
                    settings.inf2_black = 70
                    settings.inf2_white = 0 
                    settings.inf1_mult =  .5
                    settings.inf2_inf = .9
                    settings.inf2_val4 = 2

            if settings.auto_cwear:
                add_wear('Cavity')
                settings.wearmode_bake = 'Live'
                settings.cavity_color = settings.auto_cwear_color
                settings.smr_ui_categ = 'Wear'
                settings.inf1_mult = settings.auto_cwear_mult
                settings.wearmode_bake = 'Live'
            
            if settings.auto_scratch:
                add_subsetup('Scratch')
                normals_connect(self, 'scratch')
                settings.scratch_intensity = settings.auto_scratch_strength
                settings.scratch_scale = scale * 2
                if settings.auto_scratch_random:
                    add_influence('ScIntensity')
                    settings.smr_ui_categ = 'Scratch'
                    settings.inf1_black = 100
                    settings.inf1_white = 70 
                    settings.inf1_mult =  .15
                    settings.inf1_inf = .7
                    settings.inf1_val4 = 2                
        context.view_layer.objects.active = old_active
        return {'FINISHED'}        