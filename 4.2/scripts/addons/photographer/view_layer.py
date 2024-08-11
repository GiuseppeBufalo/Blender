import bpy
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel
from .constants import addon_name

def update_cam_view_layer(cam,context):
    # Apply Camera Active View Layer
    if context.scene.view_layers.get(cam.photographer.active_view_layer,False):
        if context.view_layer != context.scene.view_layers[cam.photographer.active_view_layer]:
            context.window.view_layer = context.scene.view_layers[cam.photographer.active_view_layer]

    render_view_layers = []

    # Populate Collection property of Cameras with View Layers
    for cvl in cam.view_layers:
        render_view_layers.append(cvl.name)
        if cvl.name not in context.scene.view_layers:
            cam.view_layers.remove(cam.view_layers.find(cvl.name))

    # If View Layer is present in the Collection property, set Use with .render property.
    for vl in context.scene.view_layers:
        if vl.name in render_view_layers:
            vl.use = cam.view_layers[vl.name].render
        else:
            # Else add to the Collection Property and retrieve .render from current Use value.
            cam.view_layers.add().name = vl.name
            cam.view_layers[vl.name].render = vl.use 

def draw_view_layer_item(self, context, layout, item, use_scene_camera):

    # Make sure your code supports all 3 layout types
    if self.layout_type in {'DEFAULT', 'COMPACT'}:
        row = layout.row(align=True)
        icn = 'HIDE_OFF' if context.window.view_layer == context.scene.view_layers[item.name] else 'HIDE_ON'
        set = row.operator("photographer.set_view_layer",text="", icon=icn)
        set.view_layer = item.name
        set.use_scene_camera = use_scene_camera
        row.prop(item,"name",text="")

        if use_scene_camera:
            cam = context.scene.camera.data
        else:
            cam = context.camera
    cam_view_layers = cam.view_layers

    icn = 'RESTRICT_RENDER_OFF'
    for vl in cam_view_layers:
        if item.name == vl.name and vl.render == False:
            icn = 'RESTRICT_RENDER_ON'                        
    render_op = row.operator("photographer.render_view_layer",text="", icon=icn)
    render_op.view_layer=item.name
    render_op.use_scene_camera = use_scene_camera

def draw_view_layer_panel(context,layout,cam,use_scene_camera):
    if use_scene_camera:
        uilist = "PHOTOGRAPHER_UL_ViewPanel_ViewLayerList"
    else:
        uilist = "PHOTOGRAPHER_UL_ViewLayerList"
    scene = context.scene

    box = layout.box()
    row = box.row()
    row.template_list(uilist, "View Layer List", scene,
                    "view_layers", scene.photographer, "active_view_layer_index")
    col = row.column(align=True)
    col.operator("photographer.view_layer_copy",text="", icon='DUPLICATE').use_scene_camera=use_scene_camera
    row = col.row()
    row.operator("photographer.view_layer_remove",text="", icon='X').use_scene_camera=use_scene_camera
    vl = [vl for vl in context.scene.view_layers]
    if len(vl)<2:
        row.enabled = False

    # Image format warning to make sure Incremental Save works  
    vlr = [vl for vl in cam.view_layers if vl.render]
    if len(vl) >=2:
        if scene.render.image_settings.file_format != "OPEN_EXR_MULTILAYER" and scene.use_nodes==False:
            col = layout.column(align=True)
            col.label(text="Use File Output node or EXR Multilayer", icon='INFO')
            col.label(text="       to save each View layers.")

    layout.prop(scene.render,"use_single_layer", text="Render Single Layer (Viewport Only)")

class ViewLayerItem(PropertyGroup):
    """Group of properties representing an item in the list."""

    # Properties added to View Layers in the UI List to set them Renderable
    name: StringProperty()
    render: BoolProperty(default=True)

class PHOTOGRAPHER_UL_ViewPanel_ViewLayerList(UIList):
    """View Layer List for View Panel"""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index):

        # Using Scene Camera
        draw_view_layer_item(self, context, layout, item, True)

class PHOTOGRAPHER_UL_ViewLayerList(UIList):
    """View Layer List for Camera Properties panel"""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index):
    
        # Using Camera data
        draw_view_layer_item(self, context, layout, item, False)


class PHOTOGRAPHER_OT_SetViewLayer(Operator):
    """Set active View Layer"""
    bl_idname = "photographer.set_view_layer"
    bl_label = "Set active View Layer"

    view_layer : StringProperty()
    use_scene_camera : BoolProperty(default=False)

    def execute(self, context):
        scene = context.scene
        if context.view_layer != scene.view_layers[self.view_layer]:
            context.window.view_layer = scene.view_layers[self.view_layer]

        if self.use_scene_camera:
            cam = scene.camera.data
        else:
            cam = context.camera
        cam.photographer.active_view_layer = self.view_layer

        return{'FINISHED'}

class PHOTOGRAPHER_OT_RenderViewLayer(Operator):
    """Make View Layer renderable"""
    bl_idname = "photographer.render_view_layer"
    bl_label = "Render View Layer"

    view_layer : StringProperty()
    use_scene_camera: BoolProperty(default=False)

    def execute(self, context):
        if self.use_scene_camera:
            cam = context.scene.camera.data
        else:
            cam = context.camera

        update_cam_view_layer(cam,context)

        cvl = cam.view_layers[self.view_layer]
        cvl.render = not cvl.render
        context.scene.view_layers[self.view_layer].use = cvl.render

        return{'FINISHED'}

class PHOTOGRAPHER_OT_CopyViewLayer(Operator):
    """Copy current View Layer"""
    bl_idname = "photographer.view_layer_copy"
    bl_label = "Copy View Layer"

    use_scene_camera : BoolProperty(default=False)

    def execute(self, context):
        if self.use_scene_camera:
            cam = context.scene.camera.data
        else:
            cam = context.camera
        bpy.ops.scene.view_layer_add(type='COPY')
        cam.photographer.active_view_layer = context.view_layer.name

        return{'FINISHED'}

class PHOTOGRAPHER_OT_RemoveViewLayer(Operator):
    """Remove Active View Layer"""
    bl_idname = "photographer.view_layer_remove"
    bl_label = "Remove View Layer"

    use_scene_camera : BoolProperty(default=False)

    def execute(self, context):
        if self.use_scene_camera:
            cam = context.scene.camera.data
        else:
            cam = context.camera
        bpy.ops.scene.view_layer_remove()
        cam.photographer.active_view_layer = context.view_layer.name

        if not self.use_scene_camera:
            cam_obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is cam.id_data][0]
            context.view_layer.objects.active = cam_obj

        return{'FINISHED'}

class PHOTOGRAPHER_PT_ViewPanel_ViewLayer(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = 'View Layers'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 9

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA'

    def draw_header(self, context):
        settings = context.scene.camera.data.photographer    
        self.layout.prop(settings, "view_layer_enabled", text="")    

    def draw_header_preset(self, context):
        if context.preferences.addons[addon_name].preferences.show_compact_ui:
            layout = self.layout
            settings = context.scene.camera.data.photographer 
            row = layout.row(align=True)
            row.enabled = settings.view_layer_enabled
            row.prop(settings,"active_view_layer",text="")
            row.separator()

    def draw(self, context):
        layout = self.layout        
        cam = context.scene.camera.data
        settings = cam.photographer
        layout.enabled = settings.view_layer_enabled

        draw_view_layer_panel(context,layout,cam,use_scene_camera=True)


class PHOTOGRAPHER_PT_ViewLayer(Panel):
    bl_label = 'View Layers'
    bl_parent_id = 'PHOTOGRAPHER_PT_Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw_header(self, context):
        settings = context.camera.photographer
        self.layout.prop(settings, "view_layer_enabled", text="")

    def draw_header_preset(self, context):
        layout = self.layout
        settings = context.camera.photographer
        row = layout.row(align=True)
        row.enabled = settings.view_layer_enabled
        row.prop(settings,"active_view_layer",text="")
        row.separator()

    def draw(self, context):
        layout = self.layout
        cam = context.camera
        layout.enabled = cam.photographer.view_layer_enabled

        draw_view_layer_panel(context,layout,cam,use_scene_camera=False)


def register():

    bpy.utils.register_class(ViewLayerItem)
    bpy.utils.register_class(PHOTOGRAPHER_UL_ViewLayerList)
    bpy.utils.register_class(PHOTOGRAPHER_UL_ViewPanel_ViewLayerList)
    bpy.utils.register_class(PHOTOGRAPHER_OT_SetViewLayer)
    bpy.utils.register_class(PHOTOGRAPHER_OT_RenderViewLayer)
    # View Panel is registered in panel_classes
    # bpy.utils.register_class(PHOTOGRAPHER_PT_ViewPanel_ViewLayer)  
    bpy.utils.register_class(PHOTOGRAPHER_PT_ViewLayer)
    bpy.utils.register_class(PHOTOGRAPHER_OT_CopyViewLayer)
    bpy.utils.register_class(PHOTOGRAPHER_OT_RemoveViewLayer)

    bpy.types.Camera.view_layers = CollectionProperty(type = ViewLayerItem)

def unregister():

    del bpy.types.Camera.view_layers

    bpy.utils.unregister_class(ViewLayerItem)
    bpy.utils.unregister_class(PHOTOGRAPHER_UL_ViewPanel_ViewLayerList)
    bpy.utils.unregister_class(PHOTOGRAPHER_UL_ViewLayerList)
    bpy.utils.unregister_class(PHOTOGRAPHER_OT_SetViewLayer)
    bpy.utils.unregister_class(PHOTOGRAPHER_OT_RenderViewLayer)
    bpy.utils.unregister_class(PHOTOGRAPHER_PT_ViewLayer)
    # View Panel is registered in panel_classes
    #bpy.utils.unregister_class(PHOTOGRAPHER_PT_ViewPanel_ViewLayer)
    bpy.utils.unregister_class(PHOTOGRAPHER_OT_CopyViewLayer)
    bpy.utils.unregister_class(PHOTOGRAPHER_OT_RemoveViewLayer)
