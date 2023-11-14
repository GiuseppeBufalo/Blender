
#####################################################################################################
# 
#       .o.             .o8        .o8       ooo        ooooo                    oooo
#      .888.           "888       "888       `88.       .888'                    `888
#     .8"888.      .oooo888   .oooo888        888b     d'888   .oooo.    .oooo.o  888  oooo
#    .8' `888.    d88' `888  d88' `888        8 Y88. .P  888  `P  )88b  d88(  "8  888 .8P'
#   .88ooo8888.   888   888  888   888        8  `888'   888   .oP"888  `"Y88b.   888888.
#  .8'     `888.  888   888  888   888        8    Y     888  d8(  888  o.  )88b  888 `88b.
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o8o        o888o `Y888""8o 8""888P' o888o o888o
# 
#####################################################################################################



import bpy

from . import mask_type 

from .. resources.icons import cust_icon
from .. resources.translate import translate



#####################################################################################################



class SCATTER5_OT_add_mask(bpy.types.Operator):
    """add a new mask + menu"""

    bl_idname      = "scatter5.add_mask"
    bl_label       = translate("New Vertex-Mask")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    type : bpy.props.StringProperty()
    description : bpy.props.StringProperty()
    draw : bpy.props.BoolProperty()

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):

        #Call add function from type mask module 
        exec(f"mask_type.{self.type}.add()")
        
        #update active list idx 
        emitter = bpy.context.scene.scatter5.emitter
        emitter.scatter5.mask_systems_idx = len(emitter.scatter5.mask_systems)-1
        
        return {'FINISHED'}


    def invoke(self, context, event):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        masks = emitter.scatter5.mask_systems

        if (self.draw==False):
            self.execute(context)
            return {'FINISHED'} 

        def draw(self, context):
            layout = self.layout

            col1 = layout.column()
            row = col1.row()

            #Painting 
            col = row.column()
            #
            col.label(text=translate("General") + 20*" ",icon='LAYER_USED')
            col.separator()
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Layer Paint") ,icon="BRUSH_DATA")
            ope.description = translate("Create a new 'painting layer'")
            ope.type = "layer_paint"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Merge (realtime)") ,icon_value=cust_icon("W_ARROW_MERGE"),)
            ope.description = translate("Merge Up to 15 vertex-group together using a geometry node modifier")
            ope.type = "vgroup_merge"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Split (realtime)") ,icon_value=cust_icon("W_ARROW_SPLIT"),)
            ope.description = translate("Split weight up to 5 different vertex-group with the help of a value-remapping graph")
            ope.type = "vgroup_split"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Vcol to Vg (realtime)") ,icon="FILTER")
            ope.description = translate("Convert a vertex-color to a vertex group using RGB channel or Greyscale Values")
            ope.type = "vcol_to_vgroup"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Texture-Data (realtime)") ,icon="TEXTURE")
            ope.description = translate("")
            ope.type = "texture_mask"        

            #Boolean 
            col=row.column()
            #
            col.label(text=translate("Object") + 20*" ",icon='LAYER_USED')
            col.separator()
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Bezier Path (realtime)") ,icon="CURVE_BEZCURVE")
            ope.description = translate("Create a VertexWeightProximity modifier set-up on a curve object")
            ope.type = "bezier_path"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Bezier Area") ,icon="CURVE_BEZCIRCLE")
            ope.description = translate("Project the inside area of a closed bezier-curve onto a vertex-group")
            ope.type = "bezier_area"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Dynamic Paint (realtime)") ,icon="MOD_DYNAMICPAINT")
            ope.description = translate("Create a dynamic-paint modifiers set-up that will mask areas of your terrain from collision/proximity with chosen mesh-objects")
            ope.type = "boolean"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Ecosystem") ,icon_value=cust_icon("W_ECOSYSTEM"))
            ope.description = translate("Generate a distance field around given scatter-system")
            ope.type = "particle_proximity"

            ## Geometry 
            #
            col=row.column()
            #
            col.label(text=translate("Geometry") + 20*" ",icon='LAYER_USED')
            col.separator()
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Elevation") ,icon_value=cust_icon("W_ALTITUDE"))
            ope.description = translate("Mask based on your terrain Elevation Information")
            ope.type = "height"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Slope") ,icon_value=cust_icon("W_SLOPE"))
            ope.description = translate("Mask based on your terrain Slope Information")
            ope.type = "slope"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Curvature") ,icon_value=cust_icon("W_CURVATURE"))
            ope.description = translate("Mask based on your terrain Curvature Information (concave and convex angles)")
            ope.type = "curvature"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Border") ,icon_value=cust_icon("W_BORDER"))
            ope.description = translate("Create weights around your emitter mesh boundary loop, useful for adding or removing points distributed near your emitter borders")
            ope.type = "border"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Aspect") ,icon_value=cust_icon("W_ASPECT"))
            ope.description = translate("Mask based on your terrain slopes orientations (called 'Aspect map' in GIS)")
            ope.type = "aspect"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Normal") ,icon="NORMALS_FACE")
            ope.description = translate("Use the normal information of your emitter's vertices to generate weight data")
            ope.type = "normal"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Position") ,icon="EMPTY_ARROWS")
            ope.description = translate("Use the position information of your emitter's vertices to generate weight data")
            ope.type = "position"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Watershed") ,icon="MATFLUID")
            ope.description = translate("Mask based on your terrain areas that are susceptible to hosting water-streams")
            ope.type = "watershed"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Mesh-Data") ,icon="MOD_DATA_TRANSFER")
            ope.description = translate("Use your emitter mesh data to generate weight (marked edges, marked faces, indices, material ID, ect..)")
            ope.type = "mesh_data"

            ## Scene
            #
            col=row.column()
            #
            col.label(text=translate("Scene") + 20*" ",icon='LAYER_USED')
            col.separator()
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Camera Ray") ,icon="CAMERA_DATA")
            ope.description = translate("Create a vertex-group mask that will mask out areas not visible to camera(s)")
            ope.type = "camera_visibility"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Ambient Occlusion") ,icon="RENDER_STILL")
            ope.description = translate("Bake Cycles ambient occlusion as weight data")
            ope.type = "ao"
            #
            add = col.row()
            ope = add.operator("scatter5.add_mask" ,text=translate("Lighting") ,icon="RENDER_STILL")
            ope.description = translate("Bake Cycles lighting as weight data")
            ope.type = "light"

            return

        bpy.context.window_manager.popup_menu(draw)

        self.draw = False
        return {'PASS_THROUGH'}



class SCATTER5_OT_assign_mask(bpy.types.Operator):

    bl_idname      = "scatter5.assign_mask"
    bl_label       = translate("Assign Mask")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    assign_vg : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    mask_idx : bpy.props.IntProperty()

    @classmethod
    def poll(cls, context, ):
        
        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        masks = emitter.scatter5.mask_systems

        if (len(masks)==0):
            return False

        if (len(emitter.scatter5.particle_systems)==0):
            return False

        return True

    def invoke(self, context, event):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        masks = emitter.scatter5.mask_systems
        m = masks[self.mask_idx]

        #find vg name to assign 

        #split and vcol convert have multiple ouptut, assignment possible
        if m.type in ["vgroup_split","vcol_to_vgroup",]:
            self.assign_vg = ""
        #merge modifier does have an output!
        elif (m.type=="vgroup_merge"):
            mod = emitter.modifiers.get(f"Scatter5 {m.name}")
            if mod is not None:
                self.assign_vg = mod["Output_5_attribute_name"]
        #else everything else have an output and it's standard
        else:
            self.assign_vg = m.name

        if (self.assign_vg==""):

            def draw(self, context):
                layout = self.layout

                layout.label(text=translate("Couldn't find any VertexGroup to assign."),)
                layout.label(text=translate("Perhaps your mask has multiple output?"),)

                return None

        else:

            assign_vg = self.assign_vg

            def draw(self, context):

                nonlocal assign_vg

                self.layout.label(text=translate("Quickly Assign")+f" '{assign_vg}' :", icon="GROUP_VERTEX",)
                self.layout.separator()

                for psy in emitter.scatter5.particle_systems:

                    op = self.layout.operator("scatter5.exec_line",text=psy.name, icon="PARTICLES",)
                    op.api = f"psy = bpy.data.objects['{emitter.name}'].scatter5.particle_systems['{psy.name}'] ; psy.s_mask_vg_allow = True ; psy.s_mask_vg_ptr = '{assign_vg}'"
                    op.description = translate("Assign VertexGroup to this scatter-system")

                return None

        bpy.context.window_manager.popup_menu(draw)

        return {'PASS_THROUGH'}



#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (

    SCATTER5_OT_add_mask,
    SCATTER5_OT_assign_mask,

    )


#if __name__ == "__main__":
#    register()