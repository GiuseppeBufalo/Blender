
######################################################################################
#
# oooooooooooo           oooo  oooo             .o88o.  .o88o.      ooooooooo.
# `888'     `8           `888  `888             888 `"  888 `"      `888   `Y88.
#  888          .oooo.    888   888   .ooooo.  o888oo  o888oo        888   .d88'  .ooooo.  ooo. .oo.  .oo.    .oooo.   oo.ooooo.
#  888oooo8    `P  )88b   888   888  d88' `88b  888     888          888ooo88P'  d88' `88b `888P"Y88bP"Y88b  `P  )88b   888' `88b
#  888    "     .oP"888   888   888  888   888  888     888          888`88b.    888ooo888  888   888   888   .oP"888   888   888
#  888         d8(  888   888   888  888   888  888     888          888  `88b.  888    .o  888   888   888  d8(  888   888   888
# o888o        `Y888""8o o888o o888o `Y8bod8P' o888o   o888o        o888o  o888o `Y8bod8P' o888o o888o o888o `Y888""8o  888bod8P'
#                                                                                                                       888
#                                                                                                                      o888o
######################################################################################

# This module will handle map curve data
# map curve data supported so far are map curve in vgedit modifiers AND map curve in geometry nodes.
# meaning that this module is an universal Scatter5 map curve data manager.

#in order to work with such data we first need to identify them correctly :
# - source_api : mod api str for modifiers, or nodes. Note that modifiers needs a refresh... 
# - mapping_api : curve api str == .mapping.curves[0]

import bpy
import re
import random
import functools

from mathutils import Vector

from .. resources.icons import cust_icon
from .. resources.translate import translate

from .. import utils 

from .. ui import ui_templates

#how about creating our own matrix type? overkill?

# oooooooooooo               .
# `888'     `8             .o8
#  888          .ooooo.  .o888oo
#  888oooo8    d88' `"Y8   888
#  888    "    888         888
#  888         888   .o8   888 .
# o888o        `Y8bod8P'   "888"


def matrix_parsing(matrix):
    """convert stringified matrix back to tuple"""
        
    if (type(matrix) is not str):
        return [[],] 

    r = []

    #find inside of first element
    vec = matrix
    par = ("[]()")
    if (vec[0] in par):
        vec = vec[1:]
    if (vec[-1] in par):
        vec = vec[:-1]
    elif (vec[-2] in par):
        vec = vec[:-2]

    #find all points, either brackets or parenthesis
    fin = re.findall(r'\[.*?\]', vec)
    if (len(fin)==0):
        fin = re.findall(r'\(.*?\)', vec)
    vec = fin

    #remove all brackets or parenthesis or spaces
    vec = [p.replace("[","").replace("]","").replace("(","").replace(")","").replace(" ","") for p in vec]

    #for each points, convert type back
    for p in vec:
        rp = []
        for e in p.split(","):
            if e:
                if ('"' in e): #either string== handle type
                    rp.append(e.replace('"',''))
                elif ("'" in e):
                    rp.append(e.replace("'",""))
                else: #or else must be float 
                    rp.append(float(e))
        r.append(rp)
        continue

    return r

def get_matrix(curve, handle=False, string=False,):
    """get points coord matrix from mod"""

    matrix=[]

    for p in curve.points:
        x,y = p.location.x, p.location.y

        #handle support, only "VECTOR" or "AUTO"
        if (handle):
            h = "VECTOR" if (p.handle_type=="VECTOR") else "AUTO"
            matrix.append([x,y,h])
            continue
        
        matrix.append([x,y])
        continue

    if (string):
        matrix = str(matrix)

    return matrix

def set_matrix(curve,matrix,):
    """create graph from given location matrix
    note that clear points may be needed first"""   

    if (not matrix):
        return None

    #supports stringified matrix type
    if (type(matrix) is str):
        matrix = matrix_parsing(matrix)

    #clear all points 
    clear_points(curve)

    #add required points
    while (len(curve.points)<len(matrix)):
        curve.points.new(0,0)

    #assign points locations & handle
    for i,vec in enumerate(matrix):
        x,y,*h = vec
        curve.points[i].location = (x,y)
        curve.points[i].handle_type = h[0] if (h) else "AUTO"
        continue

    return None

def clear_points(curve):
    """clear all points of this curve (2 pts need to be left)"""

    #gather points to be deleted
    points = curve.points

    #remove everything but two pts
    while (len(curve.points)>2):
        points.remove(points[1])

    #reset to pts to original positon
    points[0].location = (0,0)
    points[1].location = (1,1)

    return None

def get_matrix_sum(curve):
    """get a sum number, aka a way to identify a matrix"""
    return sum( p.location.x+p.location.y for p in curve.points )

def matrix_eq(*curves):
    """check if the given matrix are equal"""
    return ( len( set( get_matrix_sum(c) for c in curves ) )==1 )

def move_graph_back_to_origin(curve):
    """move graph abscissa back to origin"""

    first_point = curve.points[0].location.x 

    if (first_point==0):
        return None

    step = 0-first_point

    for p in curve.points:
        p.select = False
        p.location.x = p.location.x + step

    return None 

def move_whole_graph(curve, direction="RIGHT",step=0.03, frame_coherence=False,):
    """move graph abscissa left/right by given step value, anchor point with first point"""

    for p in curve.points:
        p.select = False
    
    if (frame_coherence):

        #back to origin
        move_graph_back_to_origin(curve)
        #move depending on frame 
        frame_current = bpy.context.scene.frame_current
        delta = step*frame_current
        for p in curve.points:
            p.location.x = p.location.x - delta

    else:

        if (direction=="LEFT"):
            step = -step
        for p in curve.points:
            p.location.x = p.location.x + step

    return None

def mapping_upd_trigger(source_api, mapping_api):
    """changing points of a graph won't trigger an update, we need to send one manually somehow.."""

    #either refresh a modifier
    if (".nodes[" not in source_api):
        m = eval(source_api)
        m.falloff_type = "CURVE"
        m.show_viewport = not m.show_viewport
        m.show_viewport = not m.show_viewport
    #or a node ? 
    else:
        n = eval(source_api)
        n.mute = not n.mute
        n.mute = not n.mute
    
    #refresh graph drawing 
    mapping = eval(mapping_api)
    if (mapping is not None): 
        mapping.update()

    return None


#  ooooooooo.                                             .
#  `888   `Y88.                                         .o8
#   888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo
#   888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888
#   888          888     888ooo888 `"Y88b.  888ooo888   888
#   888          888     888    .o o.  )88b 888    .o   888 .
#  o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"
# 
# 

MAP_LINEAR  = [[0.0,0.0, "VECTOR"], [1.0,1.0, "VECTOR"]]
MAP_SMOOTH  = [[0.0,0.0, "AUTO"], [0.25,0.06, "AUTO"], [0.75,0.94, "AUTO"], [1.0,1.0, "AUTO"]]
MAP_SHARP   = [[0.0,0.0, "AUTO"], [0.25,0.06, "AUTO"], [0.75,0.50, "AUTO"], [1.0,1.0, "AUTO"]]
MAP_SPHERE  = [[0.0,0.0, "AUTO"], [0.14,0.50, "AUTO"], [0.50,0.90, "AUTO"], [1.0,1.0, "AUTO"]]
MAP_CENTRAL = [[0.0,0.0, "AUTO"], [0.75,1.00, "AUTO"], [1.00,0.00, "AUTO"]]

def apply_matrix_preset(curve, preset, arg=None):
    """update modifier edit curve with custom preset matrix, note that it"""

    #first clean up points 
    clear_points(curve)

    #set up a standard preset ?

    if (preset.startswith("MAP_")):

        exec(f'global {preset} ; set_matrix(curve, {preset})')

    #or use a parametric preset ? 

    elif (preset=="PARA_RANDOM"):

        def get_random_matrix(ran):
            """ create rando graph"""

            matrix = []
            for _ in range(0,ran):
                x = round(random.uniform(0,1),3)
                y = round(random.uniform(0,1),3)
                matrix.append([x,y,"AUTO"])

            return matrix

        set_matrix(curve, get_random_matrix(arg))

    elif (preset=="PARA_SINUS"):

        def get_sinus_matrix(division):
            """create sinus graph"""

            steps_length = 1.0/division
            matrix  = []
            _ys = [0.5, 1, 0.5, 0,]* (division*4)
            _x  = 0

            parts = (division*4)+1

            for i in range(parts):
                y = _ys[i]
                x = _x

                if not (i not in [0,parts-1] and y==0.5):
                    matrix.append([x,y,"AUTO"])

                _x += steps_length/4
                continue

            #start/end always 0/1
            matrix[0][1] = 0
            matrix[-1][1] = 1

            return matrix

        set_matrix(curve, get_sinus_matrix(arg))

    elif (preset=="PARA_STRATAS"):

        def get_strata_matrix(steps):
            """create stratas (Linear Discretization)"""
            seg_x = 1.0/steps
            seg_y = 1.0/(steps-1)
            move    = 0.00001
            matrix  = []

            for i in range(steps):

                _x = seg_x*i
                _y = seg_y*(i-1)
                if (_y<0 or _x<0):
                    continue
                matrix.append([_x,_y,"VECTOR"])

                _x = (seg_x+move)*i  
                _y = seg_y*i
                if (_y<0 or _x<0):
                    continue
                matrix.append([_x,_y,"VECTOR"])

            return matrix

        set_matrix(curve, get_strata_matrix(arg))

        for p in curve.points:
            p.handle_type = 'VECTOR'

    elif (preset=="PARA_MAX_FALLOFF"):

        def get_max_falloff_matrix(perc, falloff,):
            """graph from percentage/falloff"""

            def bool_round(x):
                if (not 1>x>0):
                    if (x>1):
                        x=1
                    elif (x<0):
                        x=0
                return x

            matrix = [[bool_round(perc/100 - falloff),0.0,"VECTOR"],[bool_round(perc/100 + falloff),1.0,"VECTOR"]]

            return matrix

        set_matrix(curve, get_max_falloff_matrix(arg[0],arg[1]))

    elif (preset=="PARA_MIN_MAX"):

        def get_min_max_matrix(v1, v2,):
            """graph from min max value"""

            minv = None 

            #re-evaluate min and max as user may be dummy 
            if (v1>=v2):
                maxv,minv = v1/100,v2/100
            elif (v1<=v2):
                maxv,minv = v2/100,v1/100

            if (minv==0):
                max1,max2 = maxv-0.001,maxv+0.001
                matrix = [[max1,0],[max2,1]]
            else:
                max1,max2 = maxv-0.001,maxv+0.001
                min1,min2 = minv-0.001,minv+0.001
                matrix = [[max1,0],[max2,1],[min1,1],[min2,0]]

            return matrix

        set_matrix(curve, get_min_max_matrix(arg[0],arg[1]))

    #deselect all points 

    for p in curve.points:
        p.select = False

    return None

def preset_update(self, context,):
    """update functions for any preset enum or props"""

    source_api = self.source_api
    mapping_api = self.mapping_api
    preset = self.preset
        
    #choose potential parametric arg
    arg = None
    if (preset=="PARA_RANDOM"):
        arg = self.random
    elif (preset=="PARA_SINUS"):
        arg = self.sinus
    elif (preset=="PARA_STRATAS"):
        arg = self.stratas
    elif (preset=="PARA_MAX_FALLOFF"):
        arg = [self.val, self.fal]
    elif (preset=="PARA_MIN_MAX"):
        arg = [self.min, self.max]

    curve = eval(f"{mapping_api}.curves[0]")
    apply_matrix_preset(curve, preset, arg=arg)
    mapping_upd_trigger(source_api, mapping_api)

    return None 


# oooooooooo.    o8o            oooo
# `888'   `Y8b   `"'            `888
#  888      888 oooo   .oooo.    888   .ooooo.   .oooooooo
#  888      888 `888  `P  )88b   888  d88' `88b 888' `88b
#  888      888  888   .oP"888   888  888   888 888   888
#  888     d88'  888  d8(  888   888  888   888 `88bod8P'
# o888bood8P'   o888o `Y888""8o o888o `Y8bod8P' `8oooooo.
#                                               d"     YD
#                                               "Y88888P'

"""
ABOUT 
`psy.foo_fallremap_data` do not pass in our `update_factory` update function processing..
in fact a `fall_remap` data is only but a getter/setter directly interacting with the nodetree

we are forced to implement ALT & SYNC behavior from the dialog interface operator, 
meaning that user will be fooled, but interaction from api will not work properly...

perhaps we'll be able to introduce a real `CurveMapping` property? 
https://devtalk.blender.org/t/python-api-support-for-curveprofile-curvemapping-and-colorramp/25666/3
"""

class SCATTER5_OT_graph_dialog(bpy.types.Operator):
    """this operator is compatible for fallremap graph coming from scatter systems or vg edit
    https://blender.stackexchange.com/questions/274785/how-to-create-a-modal-state-dialog-box-operator/274786#274786"""

    bl_idname  = "scatter5.graph_dialog"
    bl_label   = translate("Falloff Graph")
    bl_options = {'REGISTER', 'INTERNAL'}

    #Dialog Properties 

    source_api : bpy.props.StringProperty()
    mapping_api : bpy.props.StringProperty()

    mask_name : bpy.props.StringProperty(default="", description="facultative arg only for vg-edit", options={"SKIP_SAVE",},) 
    psy_name : bpy.props.StringProperty(default="", description="facultative arg only for psy-fallremap", options={"SKIP_SAVE",},) 

    def __init__(self):
        """compose additional instance properties from these given above"""

        #evaluate source data
        self._source = eval(self.source_api)
        self._curve = eval(f"{self.mapping_api}.curves[0]")
        self._points = self._curve.points

        #is scatter-system or vg-edit use context?
        self._psy_context = (".nodes[" in self.source_api)

        if (self._psy_context):
            #find the name api of the feature we are working with
            self._propname = self.source_api.split("node_group.nodes['")[1].split("']")[0]
            #find the _fallremap_data propname
            self._propname_fall = self._propname + "_fallremap_data"

        return None

    #find if dialog is currently active?
    
    dialog_state = False

    def get_dialog_state(self)->bool:
        cls = type(self)
        return cls.dialog_state
        
    def set_dialog_state(self, value:bool,)->None:
        cls = type(self)
        cls.dialog_state = value
        return None

    instance_type : bpy.props.StringProperty(default="UNDEFINED", description="private, don't touch me", options={'SKIP_SAVE',},)

    def invoke(self,context,event,):
        """decide if we'll invoke modal or dialog"""

        #launch both modal & dialog instance of this operator simultaneously
        if (self.instance_type=="UNDEFINED"):

            #transfer operator arguments
            kwargs = {
                "source_api":self.source_api,
                "mapping_api":self.mapping_api,
                "mask_name":self.mask_name,
                "psy_name":self.psy_name,
                } 
            bpy.ops.scatter5.graph_dialog('INVOKE_DEFAULT', instance_type="DIALOG", **kwargs,)
            bpy.ops.scatter5.graph_dialog('INVOKE_DEFAULT', instance_type="MODAL", **kwargs,)
            return {'FINISHED'}

        #launch a dialog instance?
        if (self.instance_type=="DIALOG"):
            self.set_dialog_state(True)
            return context.window_manager.invoke_popup(self)

        #launch a modal instance?
        if (self.instance_type=="MODAL"):
            self.modal_start(context)
            context.window_manager.modal_handler_add(self)  
            return {'RUNNING_MODAL'}

        return {'FINISHED'}

    def __del__(self):
        """called when the operator has finished"""
        try:
            if (self.instance_type=="DIALOG"):
                self.set_dialog_state(False)
        except:
            pass
        return None

    def graph_has_updated(self):
        """yes all of this for tracking an update trigger on bpy.types.CurveMapping...
        unfortunately we cannot msgbus subscribe to bpy.types.CurveMapPoint ect.."""

        new_matrix_sum = get_matrix_sum(self._curve)

        if (not hasattr(self,"_old_matrix_sum")):
            self._old_matrix_sum = []

        if (new_matrix_sum!=self._old_matrix_sum):
            self._old_matrix_sum = new_matrix_sum
            return True

        return False

    def graph_callback(self,context,event):

        scat_scene = context.scene.scatter5
        psy = scat_scene.get_psy_by_name(self.psy_name)
        matrix_str = get_matrix(self._curve, handle=True, string=True,)

        #synchronization implementation for fallremap graph
        if (scat_scene.factory_synchronization_allow):
            from .. scattering.update_factory import update_sync
            update_sync(psy, self._propname_fall, matrix_str,)

        #alt support implementation for fallremap graph
        if ( (scat_scene.factory_alt_allow) and (event is not None) and (event.alt) ):
            from .. scattering.update_factory import update_alt
            update_alt(psy, self._propname_fall, matrix_str,)

        return None 

    def modal(self,context,event,):
        """for modal instance"""

        #modal state only active while dialog instance is! 
        if (self.get_dialog_state()==False):
            self.modal_quit(context)
            return {'FINISHED'}

        #ignore user dropping the alt key 
        if ( (event.type=='LEFT_ALT') and (event.value=='RELEASE') ): 
            return {'PASS_THROUGH'}

        #update if graph change detected & user stopped pressing MOUSE ? 
        if (event.value=='RELEASE'):
            if (self.graph_has_updated()==True):
                self.graph_callback(context,event,)
                return {'PASS_THROUGH'}

        return {'PASS_THROUGH'}

    def modal_start(self,context,):

        #set vg active option?
        if (not self._psy_context and self.mask_name):
            utils.vg_utils.set_vg_active_by_name(context.scene.scatter5.emitter, self.mask_name)

        return None

    def modal_quit(self,context,):

        #send update signal anyway when quitting, mostly for ensuring synchronization
        self.graph_callback(context,None,)

        return None

    #Preset Properties for drawing code

    preset : bpy.props.EnumProperty(
        name = translate("Apply a preset to the graph"), 
        default = "MAP_LINEAR",
        items = ( ( "MAP_LINEAR"       ,"", translate("Linear")                , "LINCURVE", 0, ),
                  ( "MAP_SMOOTH"       ,"", translate("Smooth")                , "SMOOTHCURVE", 1, ),
                  ( "MAP_SHARP"        ,"", translate("Sharp")                 , "SHARPCURVE", 2, ),
                  ( "MAP_SPHERE"       ,"", translate("Sphere")                , "SPHERECURVE", 3, ),
                  ( "MAP_CENTRAL"      ,"", translate("Central")               , "IPO_BACK", 4, ),
                  ( "PARA_RANDOM"      ,"", translate("Random (Parametric)")   , "RNDCURVE", 5, ),
                  ( "PARA_SINUS"       ,"", translate("Sinus (Parametric)")    , "FORCE_HARMONIC", 6, ),
                  ( "PARA_STRATAS"     ,"", translate("Quantize (Parametric)") , "IPO_CONSTANT", 7, ),
                  ( "PARA_MAX_FALLOFF" ,"", translate("Falloff (Parametric)")  , "IPO_LINEAR", 8, ),
                  ( "PARA_MIN_MAX"     ,"", translate("Min-Max (Parametric)")  , "NOCURVE", 9, ),
                ),
            update=preset_update,
        )
    random : bpy.props.IntProperty(
        name=translate("Points"),
        default=10, 
        min=2, 
        soft_max=50, 
        max=300,
        update=preset_update,
        )
    sinus : bpy.props.IntProperty(
        name=translate("Cycles"),
        default=2,
        min=1,
        soft_max=20,
        max=100,
        update=preset_update,
        )
    stratas : bpy.props.IntProperty(
        name=translate("Steps"),
        default=7, 
        min=2, 
        soft_max=20, 
        max=100,
        update=preset_update,
        )
    min : bpy.props.FloatProperty(
        name=translate("Min Value"),
        default=0,
        min=0,
        max=100,
        subtype='PERCENTAGE',
        update=preset_update,
        ) 
    max : bpy.props.FloatProperty(
        name=translate("Max Value"),
        default=50,
        min=0,
        max=100,
        subtype='PERCENTAGE',
        update=preset_update,
        )
    val : bpy.props.FloatProperty(
        name=translate("Max Value"),
        default=50,
        min=-20,
        max=120,
        subtype='PERCENTAGE',
        update=preset_update,
        )
    fal : bpy.props.FloatProperty(
        name=translate("Falloff"),
        default=0.05,
        min=-0.50,
        max=0.50,      
        update=preset_update,              
        )
    op_move : bpy.props.FloatProperty(
        name=translate("Move Step"),
        default=0.03,
        min=0,
        soft_max=1,
        )
    op_size : bpy.props.FloatProperty(
        name=translate("Size Factor"),
        default=1.1,
        min=0,
        soft_max=10,
        )

    def draw(self, context):

        layout = self.layout
        
        scat_scene = context.scene.scatter5
        emitter = scat_scene.emitter 

        box, is_open = ui_templates.box_panel(self, layout,         
            prop_str = "ui_dialog_graph", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_dialog_graph");BOOL_VALUE(1)
            icon = "FCURVE", 
            name = translate("Falloff Graph"), 
            pref_panel = "SCATTER5_PT_graph_subpanel",
            popover_argument = self,
            )
        if is_open:

                #draw main graph template, depending if is from map curve modifier or geometry float remap node 
                if (self._psy_context):
                      box.template_curve_mapping(self._source, "mapping")
                else: box.template_curve_mapping(self._source, "map_curve")

                #Set Up Preset

                col = box.column(align=True)
                
                lbl = col.row()
                lbl.label(text=translate("Graph Presets")+":")

                row = col.row(align=True)
                row.scale_x = 2.0
                row.prop(self,"preset", expand=True, icon_only=True)

                if (self.preset=="PARA_RANDOM"):
                    col.separator()
                    coll = col.row(align=True)
                    coll.prop(self,"random")

                elif (self.preset=="PARA_SINUS"):
                    col.separator()
                    col.prop(self,"sinus")

                elif (self.preset=="PARA_STRATAS"):
                    col.separator()
                    col.prop(self,"stratas")

                elif (self.preset=="PARA_MAX_FALLOFF"):
                    col.separator()
                    coll = col.column(align=True)
                    coll.scale_y = 0.9
                    coll.prop(self,"val")
                    coll.prop(self,"fal")

                elif (self.preset=="PARA_MIN_MAX"):
                    col.separator()
                    coll = col.column(align=True)
                    coll.scale_y = 0.9
                    coll.prop(self,"min")
                    coll.prop(self,"max")

                #Widgets 

                col = box.column(align=True)
                
                lbl = col.row()
                lbl.label(text=translate("Graph Widgets")+":")

                row = col.row(align=True)
                row.scale_x = 1.3
                
                op = row.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_MOVE_LEFT"))
                op.description = translate("move the graph on the x axis by step value on chosen direction")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "move_left"    
                op.op_move = self.op_move  
                #   
                op = row.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_MOVE_RIGHT"))
                op.description = translate("move the graph on the x axis by step value on chosen direction")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "move_right"    
                op.op_move = self.op_move  
                
                op = row.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_SIZE_UP"))
                op.description = translate("resize the graph with given factor")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "x_upsize"    
                op.op_size = self.op_size  
                #
                op = row.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_SIZE_DOWN"))
                op.description = translate("resize the graph with given factor")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "x_downsize"    
                op.op_size = self.op_size  

                op = row.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_REVERSE_X"))
                op.description = translate("reverse the graph on given axis")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "x_reverse"    
                #
                op = row.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_REVERSE_Y"))
                op.description = translate("reverse the graph on given axis")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "y_reverse"    

                op = row.operator("scatter5.graph_operations",text="",icon="MOD_MIRROR")
                op.description = translate("everything that is on the left of the axis X=0.5 will be mirrored on the other side")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "x_symetry"    

                op = row.operator("scatter5.graph_operations",text="",icon="COMMUNITY")
                op.description = translate("Will make a copy of the graph and put it right behind itself on +x axis")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "conga"   

                op = row.operator("scatter5.graph_operations",text="",icon="HANDLE_VECTOR")
                op.description = translate("Set all handle to vector")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "handle_vector"    
                #
                op = row.operator("scatter5.graph_operations",text="",icon="HANDLE_ALIGNED")
                op.description = translate("Set all handle to bezier")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "handle_bezier"    

                #Graph Info

                col = box.column(align=True)
                
                lbl = col.row()
                lbl.label(text=translate("Number of Points")+f": {len(self._points)}",)
        
        return None

    def execute(self, context,):
        """mandatory function called when user press on 'ok' """

        return {'FINISHED'}


#   .oooooo.                                         88 ooooooooo.                          .
#  d8P'  `Y8b                                       .8' `888   `Y88.                      .o8
# 888           .ooooo.  oo.ooooo.  oooo    ooo    .8'   888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.
# 888          d88' `88b  888' `88b  `88.  .8'    .8'    888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b
# 888          888   888  888   888   `88..8'    .8'     888          .oP"888  `"Y88b.    888   888ooo888
# `88b    ooo  888   888  888   888    `888'    .8'      888         d8(  888  o.  )88b   888 . 888    .o
#  `Y8bood8P'  `Y8bod8P'  888bod8P'     .8'     88      o888o        `Y888""8o 8""888P'   "888" `Y8bod8P'
#                         888       .o..P'
#                        o888o      `Y8P'


BufferGraphPreset = None

class SCATTER5_OT_graph_copy_preset(bpy.types.Operator):

    bl_idname = "scatter5.graph_copy_preset"
    bl_label = translate("Copy/Paste Buffer")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    copy : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    paste : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    apply_selected : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    source_api : bpy.props.StringProperty()
    mapping_api : bpy.props.StringProperty()

    def execute(self, context):

        global BufferGraphPreset

        curve = eval(f"{self.mapping_api}.curves[0]")

        if (self.copy):

            BufferGraphPreset = get_matrix(curve)

            return {'FINISHED'}

        if (self.paste):

            if (BufferGraphPreset is None):
                return {'FINISHED'}

            clear_points(curve)
            set_matrix(curve, BufferGraphPreset)
            for p in curve.points:
                p.select = False
            mapping_upd_trigger(self.source_api, self.mapping_api,)

            return {'FINISHED'}

        if (self.apply_selected):

            emitter = bpy.context.scene.scatter5.emitter
            psy_active = emitter.scatter5.get_psy_active()
            psys_sel = [p for p in emitter.scatter5.get_psys_selected() if (p is not psy_active) ]

            #find prop from node api
            prop_name = self.source_api.split("node_group.nodes['")[1].split("']")[0]

            matrix = getattr(psy_active,f"{prop_name}_fallremap_data") #..._fallremap_data == getter/setter property
            for p in psys_sel:
                setattr(p,f"{prop_name}_fallremap_data",matrix)

            return {'FINISHED'}

        return {'FINISHED'}

#   .oooooo.                                  oooo             oooooo   oooooo     oooo  o8o        .o8                           .
#  d8P'  `Y8b                                 `888              `888.    `888.     .8'   `"'       "888                         .o8
# 888           oooo d8b  .oooo.   oo.ooooo.   888 .oo.          `888.   .8888.   .8'   oooo   .oooo888   .oooooooo  .ooooo.  .o888oo  .oooo.o
# 888           `888""8P `P  )88b   888' `88b  888P"Y88b          `888  .8'`888. .8'    `888  d88' `888  888' `88b  d88' `88b   888   d88(  "8
# 888     ooooo  888      .oP"888   888   888  888   888           `888.8'  `888.8'      888  888   888  888   888  888ooo888   888   `"Y88b.
# `88.    .88'   888     d8(  888   888   888  888   888            `888'    `888'       888  888   888  `88bod8P'  888    .o   888 . o.  )88b
#  `Y8bood8P'   d888b    `Y888""8o  888bod8P' o888o o888o            `8'      `8'       o888o `Y8bod88P" `8oooooo.  `Y8bod8P'   "888" 8""888P'
#                                   888                                                                  d"     YD
#                                  o888o                                                                 "Y88888P'


class SCATTER5_OT_graph_operations(bpy.types.Operator):

    bl_idname = "scatter5.graph_operations"
    bl_label = translate("Graph Operations")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO_GROUPED'}

    source_api : bpy.props.StringProperty()
    mapping_api : bpy.props.StringProperty()

    preset : bpy.props.StringProperty()
    description : bpy.props.StringProperty()

    op_move : bpy.props.FloatProperty()
    op_size : bpy.props.FloatProperty()

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):

        curve = eval(f"{self.mapping_api}.curves[0]")

        for p in curve.points:
            p.select = False

        #operations:
        
        if (self.preset=="move_left"):
            move_whole_graph(curve, direction="LEFT", step=self.op_move)

        elif (self.preset=="move_right"):
            move_whole_graph(curve, direction="RIGHT", step=self.op_move)

        elif (self.preset=="x_reverse"):
            for p in curve.points:
                p.location.x = 1-p.location.x

        elif (self.preset=="y_reverse"):
            for p in curve.points:
                p.location.y = 1-p.location.y

        elif (self.preset=="x_upsize"):
            for p in curve.points:
                p.location.x = p.location.x*self.op_size

        elif (self.preset=="x_downsize"):
            for p in curve.points:
                p.location.x = p.location.x/self.op_size

        elif (self.preset=="handle_bezier"):
            for p in curve.points:
                p.handle_type = 'AUTO'

        elif (self.preset=="handle_vector"):
            for p in curve.points:
                p.handle_type = 'VECTOR'

        elif (self.preset=="conga"):
            mA = get_matrix(curve)
            mA_length = abs(mA[-1][0]-mA[0][0])
            mB = [[ m[0] + mA_length ,m[1] ] for m in mA]
            mC = mA + mB
            #avoid doubles
            matrix = []
            for p in mC:
                if p not in matrix:
                    matrix.append(p)
            set_matrix(curve, matrix)

        elif (self.preset=="x_symetry"):
            matrix = get_matrix(curve)
            half=[]
            for x,y in matrix:
                if x<0.5:
                    half.append([x,y])
            new=[]
            new+=half
            for x,y in half:
                _x = 1-x
                new.append([_x,y])
            clear_points(curve)
            set_matrix(curve, new)

        #update
        for p in curve.points:
            p.select = False
        mapping_upd_trigger(self.source_api, self.mapping_api)

        return {'FINISHED'}


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'


classes = (
    
    SCATTER5_OT_graph_copy_preset,
    SCATTER5_OT_graph_operations,
    SCATTER5_OT_graph_dialog,
    
    )


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    return 

def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    return 


#if __name__ == "__main__":
#    register()