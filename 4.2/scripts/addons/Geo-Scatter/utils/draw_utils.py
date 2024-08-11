
#Bunch of function /operators related to drawing 

import bpy 

from . str_utils import word_wrap

from .. resources.icons import cust_icon
from .. resources.translate import translate



#   .oooooo.                                oooooooooo.
#  d8P'  `Y8b                               `888'   `Y8b
# 888           oo.ooooo.  oooo  oooo        888      888 oooo d8b  .oooo.   oooo oooo    ooo
# 888            888' `88b `888  `888        888      888 `888""8P `P  )88b   `88. `88.  .8'
# 888     ooooo  888   888  888   888        888      888  888      .oP"888    `88..]88..8'
# `88.    .88'   888   888  888   888        888     d88'  888     d8(  888     `888'`888'
#  `Y8bood8P'    888bod8P'  `V88V"V8P'      o888bood8P'   d888b    `Y888""8o     `8'  `8'
#                888
#               o888o

import bpy, blf #, bgl, gpu
#from gpu_extras.batch import batch_for_shader



#Keep track of all font added here 
AllFonts = { 
    #example: { "font_id":0, "handler":None, "region_type":""}
}


def add_font(text="Hello World", size=[50,72], position=[2,180], color=[1,1,1,0.1], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],}):

    global AllFonts

    Id = str(len(AllFonts.keys())+1)
    AllFonts[Id]= {"font_id":0, "handler":None,}

    def draw(self, context):
        font_id = AllFonts[Id]["font_id"]
    
        #Define X
        if ("LEFT" in origin):
            pos_x = position[0]
        elif ("RIGHT" in origin):
            pos_x = bpy.context.region.width - position[0]

        #Define Y
        if ("BOTTOM" in origin):
            pos_y = position[1]
        elif ("TOP" in origin):
            pos_y = bpy.context.region.height - position[1]


        blf.position(font_id, pos_x, pos_y, 0)

        blf.color(font_id, color[0], color[1], color[2], color[3])
        
        if(bpy.app.version < (4, 0, 0)):
            blf.size(font_id, size[0], size[1])
        else:
            # 4.0, `dpi` argument is removed
            blf.size(font_id, size[0])

        if (shadow is not None):
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, shadow["blur"], shadow["color"][0], shadow["color"][1], shadow["color"][2], shadow["color"][3])
            blf.shadow_offset(font_id, shadow["offset"][0], shadow["offset"][1])

        blf.draw(font_id, text)

        return 

    # #try to Load custom font?
    # import os
    # font_path = bpy.path.abspath('//Zeyada.ttf')
    # if os.path.exists(font_path):
    #       AllFonts["font_id"] = blf.load(font_path)
    # else: AllFonts["font_id"] = 0

    #add font handler 
    draw_handler = bpy.types.SpaceView3D.draw_handler_add( draw, (None, None), 'WINDOW', 'POST_PIXEL')
    AllFonts[Id]["handler"] = draw_handler

    return draw_handler


# # fct if dynamic font update needed?
# def blf_update_font(key, text="Hello World", size=[50,72], position=[2,180,0], color=[1,1,1,0.3]):
#    #search in dict for key and remove then add new handler?
#    return 


def clear_all_fonts():

    global AllFonts
    for key,font in AllFonts.items():
        bpy.types.SpaceView3D.draw_handler_remove(font["handler"], "WINDOW")
    AllFonts.clear()

    return 



# def add_gradient(px_height=75,alpha_start=0.85):

#     def get_shader(line_height):

#         vertices = (
#             (0, line_height), (bpy.context.region.width*100, line_height),
#             (0, line_height+1), (bpy.context.region.width*100, line_height+1)
#             )
#         indices = ((0, 1, 2), (2, 1, 3))

#         shader = gpu.shader.from_builtin('UNIFORM_COLOR')
#         batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
#         return shader, batch

#     def draw():

#         bgl.glEnable(bgl.GL_BLEND)

#         alpha_division = alpha_start/px_height
#         for i in range(1,px_height):
#             alpha_value = alpha_division*(px_height-i)
#             if alpha_value<0:
#                 break
#             shader,batch = get_shader(i)
#             shader.bind()
#             shader.uniform_float("color", (0, 0, 0, alpha_value))
#             batch.draw(shader)

#         bgl.glDisable(bgl.GL_BLEND)

#         return 

#     draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')
#     return draw_handler



# def add_image(image_data=None, path="",position=[20,20], origin="BOTTOM LEFT", height_px=100):
    
#     if image_data is not None: 
#         image = image_data

#     elif path != "":
#         from . import_utils import import_image
#         image = import_image(path, hide=True, use_fake_user=True)
#         if image is None:
#             return None 
#     else:
#         return None

#     #Define X
#     if "LEFT" in origin:
#         pos_x = position[0]
#     elif "RIGHT" in origin:
#         pos_x = bpy.context.region.width - position[0]
#     #Define Y
#     if "BOTTOM" in origin:
#         pos_y = position[1]
#     elif "TOP" in origin:
#         pos_y = bpy.context.region.height - position[1]

#     img_y = height_px
#     img_x = height_px * (image.size[0]/image.size[1])

#     shader = gpu.shader.from_builtin('IMAGE')
#     batch = batch_for_shader(
#         shader, 'TRI_FAN',
#         {
#             "pos": ((pos_x, pos_y), (pos_x+img_x, pos_y), (pos_x+img_x, pos_y+img_y), (pos_x, pos_y+img_y)),
#             "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
#         },
#     )

#     if image.gl_load():
#         raise Exception()

#     def draw():
        
#         bgl.glEnable(bgl.GL_BLEND)
#         bgl.glActiveTexture(bgl.GL_TEXTURE0)
#         bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

#         shader.bind()
#         shader.uniform_int("image", 0)
#         batch.draw(shader)


#     draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')
#     return draw_handler


#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b  .oooo.o
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P d88(  "8
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888     `"Y88b.
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888     o.  )88b
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b    8""888P'
#               888
#              o888o



class SCATTER5_OT_popup_menu(bpy.types.Operator):
    """popup_menu""" #bpy.ops.scatter5.popup_menu(msgs="",title="",icon="")

    bl_idname      = "scatter5.popup_menu"
    bl_label       = ""
    bl_description = ""

    msgs  : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    title : bpy.props.StringProperty(default="Error", options={"SKIP_SAVE",},)
    icon  : bpy.props.StringProperty(default="ERROR", options={"SKIP_SAVE",},)

    def execute(self, context):

        msgs = self.msgs 

        def draw(self, context):
            
            nonlocal msgs
            word_wrap( string=msgs, layout=self.layout, max_char=40, alignment=None)

            return  None

        bpy.context.window_manager.popup_menu(draw, title=self.title, icon=self.icon)

        return {'FINISHED'}


class SCATTER5_OT_scroll_to_top(bpy.types.Operator):
    """scroll view2d to top using scroll_up() operator multiple times in a row"""

    bl_idname      = "scatter5.scroll_to_top"
    bl_label       = ""
    bl_description = ""

    def execute(self, context):

        for i in range(10_000):
            bpy.ops.view2d.scroll_up(deltax=0, deltay=10_000, page=False)

        return {'FINISHED'}


class SCATTER5_OT_tag_redraw(bpy.types.Operator):
    """tag redraw all context window area"""

    bl_idname      = "scatter5.tag_redraw"
    bl_label       = ""
    bl_description = ""

    def execute(self, context):

        for window in context.window_manager.windows:
               for area in window.screen.areas:
                   area.tag_redraw()

        return {'FINISHED'}


class SCATTER5_OT_popup_dialog(bpy.types.Operator):
    """Will invoke a dialog box -> need to run in ("INVOKE_DEFAULT")"""

    bl_idname = "scatter5.popup_dialog"
    bl_label = translate("Information")+":"
    bl_description = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    msg : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    website : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    header_title : bpy.props.StringProperty(default=translate("Information")+":", options={"SKIP_SAVE",},)
    header_icon : bpy.props.StringProperty(default="HELP", options={"SKIP_SAVE",},)
    no_confirm : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self) if (self.no_confirm) else context.window_manager.invoke_props_dialog(self)

    @classmethod
    def description(cls, context, properties): 
        return properties.description
        
    def draw(self, context):

        from .. ui import ui_templates

        layout = self.layout

        box, is_open = ui_templates.box_panel(self, layout,         
            prop_str= "ui_dialog_popup", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_dialog_popup");BOOL_VALUE(1)
            icon= self.header_icon,
            name= self.header_title,
            )
        if is_open:

            text=box.column()
            text.scale_y = 0.90

            for line in self.msg.split("\n"):

                #special alert line ? currently used by warning dialog

                if (line.startswith("###ALERT###")):
                    
                    row = text.row()
                    row.alert = True
                    row.alignment = "CENTER"
                    row.label(text=line.replace("###ALERT###",""),)

                #special link button line ? currently unused 

                elif ("_#LINK#_" in line):

                    label,link = line.split("_#LINK#_")
                    row = text.column()
                    row.alignment = "CENTER"
                    row.operator("wm.url_open", emboss=True, text=label, icon="URL").url = link

                else:

                    for l in word_wrap( string=line, layout=None,  max_char=50,).split("\n"):
                        lbl = text.row()
                        lbl.alignment = "CENTER"
                        lbl.label(text=l)

        return None

    def execute(self, context):
        
        if (self.website!=""):
            bpy.ops.wm.url_open(url=self.website)

        return {'FINISHED'}




classes = (

    SCATTER5_OT_popup_menu,
    SCATTER5_OT_scroll_to_top,
    SCATTER5_OT_tag_redraw,
    SCATTER5_OT_popup_dialog,

    )