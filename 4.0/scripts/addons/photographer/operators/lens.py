import bpy, blf, os, math
from ..functions import raycast, show_message
from .autofocus import list_focus_planes
from ..rigs.build_rigs import get_camera_rig
from ..constants import photographer_folder
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane
from ..properties.post_effects import light_effects_grp_name, get_comp_group_node, LE_VERSION

def draw_callback_px(self,context):
    font_id = 0
    x_offset = context.region.width / 2 - 75
    # 75 = text horizontal dimension / 2
    y_offset = 35
    cam = context.scene.camera.data

    text = "Focal Length: " + str(round(cam.photographer.focal)) + " mm"
    # find text dimensions
    blf.position(font_id, x_offset, y_offset ,0)
    blf.size(font_id, 28, 72)
    blf.color(font_id, 1.0,0.7,0.02,1.0)
    blf.draw(font_id,text)

class PHOTOGRAPHER_OT_DollyZoom(bpy.types.Operator):
    bl_idname = "photographer.dollyzoom"
    bl_label = "Dolly Zoom"
    bl_description = ("Dolly Zoom: Focal length adjustment, compensated by a Camera translation in depth. \n"
    "Click on an object's surface and move the mouse horizontally. Hold shift for smaller increment")
    bl_options = {'REGISTER', 'UNDO'}

    # Camera location has to be stored as property to work properly
    stored_cam_loc: bpy.props.FloatVectorProperty()
    # stored_aim_loc: bpy.props.FloatVectorProperty()
    stored_focus_distance: bpy.props.FloatProperty()

    def modal(self, context, event):
        # Allow navigation for Blender and Maya shortcuts
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} or event.alt and event.type == 'LEFTMOUSE' or event.alt and event.type == 'RIGHTMOUSE':
            return {'PASS_THROUGH'}

        cam_obj = context.scene.camera
        cam = cam_obj.data
        settings = cam.photographer

        # Enter Dolly zoom
        if event.type == 'LEFTMOUSE' and context.space_data.type == 'VIEW_3D':
            if event.value == 'PRESS':
                # Store Mouse position of the leftmouse click
                self.pos = (event.mouse_region_x, event.mouse_region_y)

                # Raycast to find distance to object
                result, location, object, normal = raycast(context, event, False, False, cam_obj)

                if result:
                    cam_dir = cam_obj.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
                    self.dist = abs(distance_point_to_plane(cam_obj.matrix_world.translation, location, cam_dir))
                    self.focal_length = settings.focal
                    self.focus_distance = cam.dof.focus_distance
                    if self.rig_obj:
                        self.cam_loc = self.rig_obj.matrix_world.translation
                    else:
                        self.cam_loc = cam_obj.matrix_world.translation
                    self.left_press = True
                else:
                    if self.cursor_set:
                        context.window.cursor_modal_restore()
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    self.report({'WARNING'}, "Raycast failed. Is the targeted object a mesh? Are you looking through the scene camera in this 3D view?")
                    return {'CANCELLED'}

        if self.left_press:
            if event.type == 'MOUSEMOVE' and self.pos:
                # Mouse Sensitivity
                if event.shift:
                    fac = 50
                else:
                    fac = 8
                focal_offset = (event.mouse_region_x - self.pos[0])/fac
                if settings.focal + focal_offset >= 4:
                    settings.focal += focal_offset
                    self.pos = (event.mouse_region_x, event.mouse_region_y)
                    offset_dist = focal_offset*0.1*(self.dist/(self.focal_length*0.1))
                    offset_vec = Vector((0.0, 0.0, offset_dist ))
                    
                    rotation_matrix = cam_obj.matrix_world.to_3x3()
                    rotation_matrix.invert()
                    if self.rig_obj:
                        self.rig_obj.matrix_world.translation = self.cam_loc + offset_vec @ rotation_matrix
                        # if self.aim_bone:
                        #      self.aim_bone.location -= offset_vec @ rotation_matrix
                    else:
                        cam_obj.matrix_world.translation = self.cam_loc + offset_vec @ rotation_matrix
                    cam.dof.focus_distance += offset_dist

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if not event.type == 'MOUSEMOVE':
                self.left_press = False
                if self.cursor_set:
                    context.window.cursor_modal_restore()
                # Restore Focus Planes visibility
                for o in self.fp:
                    o.hide_viewport = False
                # for o in self.dof_objects:
                #     o.hide_viewport = False

                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'FINISHED'}

        # Cancel Modal with RightClick and ESC
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.focal_length:
                settings.focal = self.focal_length
            if self.focus_distance:
                cam.dof.focus_distance = self.focus_distance


            if self.rig_obj:
                self.rig_obj.location = self.stored_cam_loc
                # if self.aim_bone:
                #     self.aim_bone.location = self.stored_aim_loc
            else:
                context.scene.camera.location = self.stored_cam_loc

            # Restore Focus Planes visibility
            for o in self.fp:
                o.hide_viewport = False
            # for o in self.dof_objects:
            #     o.hide_viewport = False

            if self.cursor_set:
                context.window.cursor_modal_restore()

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            cam_obj = context.scene.camera
            self.left_press = False
            self.pos = None
            self.cursor_set = True
            self.dist = None
            self.focal_length = None
            self.focus_distance = None
            self.cam_loc = None
            self.rig_obj = None
            self.aim_bone = None
            if cam_obj.get("is_rigged", False):
                self.rig_obj = get_camera_rig(cam_obj)
                if self.rig_obj:
                    self.stored_cam_loc = self.rig_obj.location
                    # aim_bone = self.rig_obj.pose.bones.get("Aim")
                    # if aim_bone:
                    #     self.aim_bone = aim_bone
                    #     self.stored_aim_loc = aim_bone.location
            else:
                self.stored_cam_loc = context.scene.camera.location
            self.stored_focus_distance = context.scene.camera.data.dof.focus_distance

            # Hide all Focus Planes
            self.fp = list_focus_planes()
            # self.dof_objects = list_dof_objects()

            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            context.window.cursor_modal_set('EYEDROPPER')
            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

# SET EV KEY BUTTON
class PHOTOGRAPHER_OT_DollyZoom_Set_Key(bpy.types.Operator):
    """Set key on Focal Length, Focus Distance and Camera location"""
    bl_idname = "photographer.dollyzoom_set_key"
    bl_label = "Set Dolly Zoom Key"

    def execute(self, context):
        cam_obj = context.scene.camera
        cam = cam_obj.data
        current_frame = context.scene.frame_current
        if cam_obj.get("is_rigged", False):
            rig_obj = get_camera_rig(cam_obj)
            if rig_obj:
                rig_obj.keyframe_insert(data_path='location', frame=(current_frame))
        else:
            cam_obj.keyframe_insert(data_path='location', frame=(current_frame))

        cam.photographer.keyframe_insert(data_path='focal', frame=(current_frame))
        cam.dof.keyframe_insert(data_path='focus_distance', frame=(current_frame))

        return{'FINISHED'}


class PHOTOGRAPHER_OT_AutoLensShift(bpy.types.Operator):
    bl_idname = "photographer.auto_lens_shift"
    bl_label = "Automatic Lens Shift"
    bl_description = "Calculates Lens Shift from current Camera rotation to make vertical lines parallel"
    bl_options = {'REGISTER', 'UNDO'}

    camera: bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.camera)
        if obj is not None:
            if obj.type != 'CAMERA':
                return{'CANCELLED'}

            camera = obj.data
            photographer = camera.photographer

            old_rot = obj.rotation_euler.x
            old_vert_shift = photographer.lens_shift
            old_atan = math.atan(photographer.lens_shift/(camera.lens/36))
            rot = old_rot + old_atan

            if rot == 0:
                self.report({'ERROR'}, "Impossible to calculate Lens Shift, the Camera has no vertical rotation")
                return{'CANCELLED'}
            else:
                shift = -(camera.lens/36)/math.tan(rot)
                if shift > 20 or shift < -20:
                    self.report({'ERROR'}, "Camera vertical rotation is too extreme, reduce angle to calculate Lens Shift")
                    return{'CANCELLED'}
                photographer.lens_shift = shift
                if rot < 0:
                    obj.rotation_euler.x = math.radians(-90)
                else:
                    obj.rotation_euler.x = math.radians(90)

                if round(math.degrees(obj.rotation_euler.y)%360) != 0:
                    show_message("Consider removing any rotation Y for the Auto Lens Shift to work as expected.",
                    "Vertical lines will be parallel but not straight because the camera rotation Y is not 0.",
                                )
                return{'FINISHED'}    
            
class PHOTOGRAPHER_OT_LensEffects_Add(bpy.types.Operator):
    bl_idname = "photographer.post_effects_add"
    bl_label = "Enable Lens Effects"
    bl_description = "Adds Lens Effects node in Compositing. Requires 3.5 for Viewport realtime compositing"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene = context.scene
        nodes = scene.node_tree.nodes
        links = scene.node_tree.links

        le_grp = composite = viewer = None

        dir = os.path.join(photographer_folder,"blends/node_groups.blend/NodeTree/")
        # Normalize slashes for Windows // linux
        dir = os.path.normpath(dir)

        le_grps = [g for g in bpy.data.node_groups if g.name == light_effects_grp_name]
        if le_grps:
            for g in le_grps:
                if g.get('version',0) == LE_VERSION:
                    le_grp = le_grps[0]
        
        if not le_grp:
            # Append Node Group
            bpy.ops.wm.append(filename=light_effects_grp_name, directory=dir)
            le_grp = [g for g in bpy.data.node_groups if g.name == light_effects_grp_name][0]
            le_grp['version'] = LE_VERSION

        location_right_x = -1000
        for node in nodes:
            if type(node) is bpy.types.CompositorNodeComposite:
                composite = node
            if type(node) is bpy.types.CompositorNodeViewer:
                viewer = node
            if node.location[0] >= location_right_x:
                location_right_x = node.location[0]
        if not composite:
            composite = nodes.new('CompositorNodeComposite')
            composite.location = (location_right_x + 300,0)
        if not viewer:
            viewer = nodes.new('CompositorNodeViewer')
            viewer.location = (location_right_x + 300,-120)

        # Get node groups
        post_effects = get_comp_group_node(context,light_effects_grp_name)

        if not post_effects:
            post_effects = nodes.new('CompositorNodeGroup')
            post_effects.node_tree = le_grp
            post_effects.node_tree.use_fake_user = True
            post_effects.name = light_effects_grp_name
            post_effects.location = composite.location
            composite.location[0] += 200
            viewer.location[0] += 200

            inc_comp = inc_comp_socket = None
            link_comp = [l for l in links if l.to_node == composite and l.to_socket.name == 'Image']
            if link_comp:
                inc_comp = link_comp[0].from_node
                inc_comp_socket = link_comp[0].from_socket.name

            if inc_comp and inc_comp != le_grp:
                links.new(inc_comp.outputs[inc_comp_socket], post_effects.inputs[0])
            links.new(post_effects.outputs[0], composite.inputs[0])
            links.new(post_effects.outputs[0], viewer.inputs[0])
            
        return {'FINISHED'}