
#   .oooooo.                                         ooo        ooooo
#  d8P'  `Y8b                                        `88.       .888'
# 888      888 oo.ooooo.   .ooooo.  ooo. .oo.         888b     d'888   .oooo.   ooo. .oo.    .oooo.    .oooooooo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888P"Y88b        8 Y88. .P  888  `P  )88b  `888P"Y88b  `P  )88b  888' `88b  d88' `88b `888""8P
# 888      888  888   888 888ooo888  888   888        8  `888'   888   .oP"888   888   888   .oP"888  888   888  888ooo888  888
# `88b    d88'  888   888 888    .o  888   888        8    Y     888  d8(  888   888   888  d8(  888  `88bod8P'  888    .o  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' o888o o888o      o8o        o888o `Y888""8o o888o o888o `Y888""8o `8oooooo.  `Y8bod8P' d888b
#               888                                                                                   d"     YD
#              o888o                                                                                  "Y88888P'


import bpy
import platform, os
import ctypes


class SCATTER5_OT_open_editor(bpy.types.Operator):

    bl_idname      = "scatter5.open_editor"
    bl_label       = ""
    bl_description = ""

    editor_type : bpy.props.StringProperty(default="", options={"SKIP_SAVE"},)
    instructions : bpy.props.StringProperty(default="", options={"SKIP_SAVE"},)
    description : bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    @staticmethod
    def set_window(size=(100,100),):
        
        if (platform.system()=="Windows"):

            SWP_NOMOVE = 0x0002

            ctypes.windll.user32.SetWindowPos(
                ctypes.windll.user32.GetActiveWindow(), 
                0,
                0,
                0,
                size[0],
                size[1],
                SWP_NOMOVE,
                )

        return None

    def execute(self, context):

        w = bpy.context.window
        wm = bpy.context.window_manager
        scat_win = wm.scatter5
        addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
        win_dimension = w.width, w.height

        #check if we need to create a new window? perhaps already an editor is open
        for w in wm.windows:
            for a in w.screen.areas: 
                if (a.ui_type==self.editor_type):
                    #define convenience variables for exec
                    window, area, screen= w,a,w.screen
                    exec(self.instructions)
                    return {'FINISHED'}

        #dupplicate area on top left corner!
        area_candidates = {a.y:a for a in w.screen.areas if (a.x==0)}
        area_candidates = dict(sorted(area_candidates.items())) #sort by lower .y values first! 
        area_found = list(area_candidates.values())[-1] #take the bigger value to get top editor

        #dupplicate area to window
        override = {"area":area_found}
        bpy.ops.screen.area_dupli(override,'INVOKE_DEFAULT')

        #define convenience variables for exec
        window = wm.windows[-1] #not sure this is reliable enough..
        screen = window.screen
        area = screen.areas[0]
        area.ui_type = self.editor_type

        #change window size, for now only window OS is supported
        window_size = ( int(win_dimension[0]/4), int(win_dimension[1]) )
        self.set_window(size=window_size,)

        exec(self.instructions)

        return {'FINISHED'}



classes = (

    SCATTER5_OT_open_editor,    

    )