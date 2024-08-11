import bpy

from bpy.types import Panel


from .main import calculate_num_chunks


# ----- PARENT CLASSES, don't register
class CSDF_PT_VIEW_3D:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CSDF"


# ----- 3D VIEWPORT PANELS

class CSDF_PT_MESHING(Panel, CSDF_PT_VIEW_3D):
    bl_label = "Meshing"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    def draw(self, context):

        scene = context.scene
        CSDF_meshingprops = scene.csdf_meshingprops

        layout = self.layout
        box = layout.box()

        row = box.row()

        if not context.scene.objects.get("CSDF_Meshing_Bounds"):
            row.scale_y = 2
        row.operator('csdf.addbounds', text="Add Bounds")

        if context.scene.objects.get("CSDF_Meshing_Bounds"):

            box.separator()

            box2 = box.box()

            row = box2.row()
            row.label(text="Bounds Properties")

            if scene.objects.get("CSDF_Meshing_Corner01"):
                obj = scene.objects["CSDF_Meshing_Corner01"]
                
                col = box2.column()
                row = col.row(align=True)
                row.prop(obj, "location", text="Corner 01")

            if scene.objects.get("CSDF_Meshing_Corner02"):
                obj = scene.objects["CSDF_Meshing_Corner02"]
                
                col = box2.column()
                row = col.row(align=True)
                row.prop(obj, "location", text="Corner 02")

            box2.separator()

            row = box2.row()
            row.prop(CSDF_meshingprops, "triangle_density")


        box.separator()

        mgl_error = False
        try:  
            import moderngl
        except:
            mgl_error = True

        bounds_deleted = False
        if not (context.scene.objects.get("CSDF_Meshing_Bounds") and context.scene.objects.get("CSDF_Meshing_Corner01") and context.scene.objects.get("CSDF_Meshing_Corner02")) :
            bounds_deleted = True

        row = box.row()
        row.alert = mgl_error
        row.scale_y = 2
        if bounds_deleted:
            row.alert = True
        row.operator('mesh.csdf_sdftomesh')
        
        if mgl_error:
            row = box.row()
            row.alert = True
            row.label(text="ModernGL not found,")
            row = box.row()
            row.alert = True
            row.label(text="install via Addon Preferences!")




        if bounds_deleted:
            row = box.row()
            row.alert = True
            row.label(text="Missing Bounds, can't convert SDF to mesh")
        else:
            row = box.row()

            bounds_01 = scene.objects["CSDF_Meshing_Corner01"].location
            bounds_02 = scene.objects["CSDF_Meshing_Corner02"].location

            num_chunks_XYZ = calculate_num_chunks(CSDF_meshingprops, bounds_01, bounds_02)
            num_chunks = num_chunks_XYZ[0] * num_chunks_XYZ[1] * num_chunks_XYZ[2]
            chunk_xyz_str = "(" + str(num_chunks_XYZ[0]) + " x " + str(num_chunks_XYZ[1]) + " x " + str(num_chunks_XYZ[2]) + ")"
            row.label(text="Total Voxels: " + str(num_chunks) + " Million " + chunk_xyz_str)

            row = box.row()
            row.label(text="Estimated Conversion Time: " + str(num_chunks/2) + " seconds")


        box.separator()

        row = box.row()
        row.label(text="Last Meshing info:")

        row = box.row()
        row.label(text="Number of Voxels: " + str(CSDF_meshingprops.last_chunk_count) + " Million")
        row = box.row()
        row.label(text="Time to Mesh: " + str( round(CSDF_meshingprops.last_chunk_time, 3) ) + " seconds")

        box.separator()
        box.separator()

        row = box.row()
        row.scale_y = 2
        row.operator(operator="csdf.cleanmesh")
        row = box.row()
        row.label(text="After cleanup, Remesh Density and Smoothing")
        row = box.row()
        row.label(text="can be adjusted in the modifiers panel")
