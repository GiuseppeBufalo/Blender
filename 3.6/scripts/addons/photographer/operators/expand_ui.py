import bpy

# Used for Camera Collections and Light Collections
class PHOTOGRAPHER_OT_CollectionExpand(bpy.types.Operator):
    bl_idname = "photographer.collection_expand"
    bl_label = "Expand Collection"
    bl_description = "Shift-Click to expand all Collections"

    collection: bpy.props.StringProperty()
    expand_all: bpy.props.BoolProperty(default=False)
    # To expand collections independently in Camera List and Lightmixer
    cam_list: bpy.props.BoolProperty(default=False)
    
    def execute(self, context):
        coll = bpy.data.collections[self.collection]
        if self.cam_list:
            bpy.types.Collection.cl_expand= bpy.props.BoolProperty(default=True)
            coll.cl_expand = not coll.cl_expand
        else:
            bpy.types.Collection.expand = bpy.props.BoolProperty(default=True)
            coll.expand = not coll.expand
        
        if self.expand_all:
            colls=([c for c in bpy.data.collections if c!=coll])
            for c in colls:
                if self.cam_list:
                    c.cl_expand = coll.cl_expand
                else:
                    c.expand = coll.expand
        # Reset Cam List
        self.cam_list=False
        
        return {'FINISHED'}
        
    def invoke(self, context, event):
        self.expand_all = event.shift
        return self.execute(context)
        
# LightMixer Light settings Expand
class LIGHTMIXER_OT_ShowMore(bpy.types.Operator):
    bl_idname = "lightmixer.show_more"
    bl_label = "Show more settings"
    bl_description = "Shift-Click to expand options for all lights or materials"

    light: bpy.props.StringProperty()
    mat: bpy.props.StringProperty()
    expand_all: bpy.props.BoolProperty(default=False)
    
    def execute(self, context):
        if self.light:
            light_obj = bpy.data.objects[self.light]
            lightmixer = light_obj.lightmixer
            lightmixer.show_more = not lightmixer.show_more
            if self.expand_all:
                coll = context.scene.collection.all_objects
                lights=([obj for obj in coll if obj.type=='LIGHT' and obj!=light_obj])
                for light in lights:
                    light.lightmixer.show_more = lightmixer.show_more
            
        elif self.mat:
            mat = bpy.data.materials[self.mat]
            lightmixer = mat.lightmixer
            lightmixer.show_more = not lightmixer.show_more
            if self.expand_all:
                materials = [mat for mat in bpy.data.materials if mat.get('is_emissive', False)]
                for m in materials:
                    m.lightmixer.show_more = lightmixer.show_more
        
        # Clear properties
        self.light = ''
        self.mat = ''
        return {'FINISHED'}        
        
    def invoke(self, context, event):
        self.expand_all = event.shift
        return self.execute(context)    
               