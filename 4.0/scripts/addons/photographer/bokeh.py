import bpy, os
from .ui.library import enum_previews_from_directory_items
from .functions import copy_collections, show_message

# photographer_dir = os.path.dirname(os.path.realpath(__file__))
# default_opt_vignetting_tex = photographer_dir + r"\textures\optical_vignetting\OV_Round_01.png"
# default_bokeh_tex = photographer_dir + r"\textures\bokeh\Round_01.png"

# Global Variables
bokeh_clip_start = 0.002


def enum_previews_opt_vignetting(self, context):
    return enum_previews_from_directory_items(self, context,'opt_vignetting')

def enum_previews_bokeh(self, context):
    return enum_previews_from_directory_items(self, context,'bokeh')

def update_opt_vignetting(self,context):
    cam_name = [o.name for o in bpy.data.objects if o.type == 'CAMERA' and o.data is self.id_data][0]
    afc = False
    ae = False
    if self.opt_vignetting:
        # Endless refreshing viewport workaround: disabling auto exposure and AF-C first
        if self.af_continuous_enabled:
            afc = True
            self.af_continuous_enabled = False
        if self.exposure_mode == 'AUTO':
            ae = True
            self.exposure_mode = 'EV'

        bpy.ops.photographer.optvignetting_add(camera = cam_name)
        update_opt_vignetting_tex(self,context)

        # Endless refreshing viewport workaround
        if afc:
            self.af_continuous_enabled = True
        if ae:
            self.exposure_mode = 'AUTO'
    else:
        bpy.ops.photographer.optvignetting_delete(camera = cam_name)

def update_opt_vignetting_tex(self,context):
    if self.opt_vignetting:
        cam_obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is self.id_data][0]
        for c in cam_obj.children:
            if c.get("is_opt_vignetting", False):
                slot = c.material_slots[0]
                mat = slot.material
                if mat.use_nodes:
                    if context.scene.render.engine == 'LUXCORE':
                        nodes = mat.luxcore.node_tree.nodes
                        for node in nodes:
                            if node.bl_idname == 'LuxCoreNodeTexImagemap':
                                if node.get("is_opt_vignetting_tex", False):
                                    if self.opt_vignetting_tex != 'empty':
                                        node.image = bpy.data.images.load(self.opt_vignetting_tex, check_existing=True)
                    else:
                        nodes = mat.node_tree.nodes
                        for node in nodes:
                            if type(node) is bpy.types.ShaderNodeTexImage:
                                if node.get("is_opt_vignetting_tex", False):
                                    if self.opt_vignetting_tex != 'empty':
                                        node.image = bpy.data.images.load(self.opt_vignetting_tex, check_existing=True)
                                        colorspaces = ['Non-Color', 'Generic Data']
                                        for cs in colorspaces:
                                            try:
                                                node.image.colorspace_settings.name = cs
                                            except:
                                                pass

def update_bokeh(self,context):
    cam_name = [o.name for o in bpy.data.objects if o.type == 'CAMERA' and o.data is self.id_data][0]
    cam = self.id_data
    afc = False
    ae = False

    if self.bokeh:
        # Endless refreshing viewport workaround: disabling auto exposure and AF-C first
        if self.af_continuous_enabled:
            afc = True
            self.af_continuous_enabled = False
        if self.exposure_mode == 'AUTO':
            ae = True
            self.exposure_mode = 'EV'
        
        if context.scene.render.engine == 'LUXCORE':
            if not cam.luxcore.bokeh.non_uniform:
                cam.luxcore.bokeh.non_uniform = True
            if cam.luxcore.bokeh.distribution != 'CUSTOM':
                cam.luxcore.bokeh.distribution = 'CUSTOM'
        else:
            bpy.ops.photographer.bokeh_add(camera = cam_name)
        update_bokeh_tex(self,context)

        # Endless refreshing viewport workaround
        if afc:
            self.af_continuous_enabled = True
        if ae:
            self.exposure_mode = 'AUTO'
    else:
        bpy.ops.photographer.bokeh_delete(camera = cam_name)

def update_bokeh_tex(self,context):
    if self.bokeh:
        if context.scene.render.engine == 'LUXCORE':
            cam = self.id_data
            image = bpy.data.images.load(self.bokeh_tex, check_existing=True)
            cam.luxcore.bokeh.image = image
        else:
            cam_obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is self.id_data][0]
            for c in cam_obj.children:
                if c.get("is_bokeh_plane", False):
                    slot = c.material_slots[0]
                    mat = slot.material
                    if mat.use_nodes:
                        nodes = mat.node_tree.nodes
                        for node in nodes:
                            if type(node) is bpy.types.ShaderNodeTexImage:
                                if node.get("is_bokeh_tex", False):
                                    if self.bokeh_tex != 'empty':
                                        node.image = bpy.data.images.load(self.bokeh_tex, check_existing=True)
                                        colorspaces = ['sRGB', 'sRGB 2.2']
                                        for cs in colorspaces:
                                            try:
                                                node.image.colorspace_settings.name = cs
                                            except:
                                                pass

def update_bokeh_size(self,context):
    if context.scene.camera:
        cam = context.scene.camera.data
        settings = cam.photographer
        if settings.bokeh:
            cam_obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is cam][0]
            for c in cam_obj.children:
                if c.get("is_bokeh_plane", False):
                    unit_scale = context.scene.unit_settings.scale_length
                    c.scale[0] = c.scale[1] = c.scale[2] = 0.2 / unit_scale

def upgrade_bokeh_material(self,mat, cam):
    if mat and mat.use_nodes == True:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        try:
            mapping=[n for n in nodes if n.bl_idname=='ShaderNodeMapping'][0]
            scale=[n for n in nodes if n.name=='Size'][0]
            loc = mapping.inputs['Location']
            sc = mapping.inputs['Scale']
            link_loc = [l for l in links if l.to_node == mapping and l.to_socket == loc]
            div = link_loc[0].from_node
            link_sc = [l for l in links if l.to_node == mapping and l.to_socket == loc]
            sc = link_sc[0].from_node

        except:
            show_message("Rename the Camera and re-enable Bokeh Texture to create new material.",
                        "The material has been modified and couldn't be updated.",
                        'ERROR')

        else:
            if div.bl_idname != 'ShaderNodeCombineXYZ' or sc.bl_idname != 'ShaderNodeCombineXYZ':
                # Move nodes before the Mapping node
                for node in nodes:
                    if node.location[0] < mapping.location[0]:
                        node.location[0] -= 200

                mul = nodes.new('ShaderNodeMath')
                mul.location = (mapping.location[0]-800,mapping.location[1]+100)
                mul.operation = 'MULTIPLY'
                mul.inputs[0].default_value = 1

                sub = nodes.new('ShaderNodeMath')
                sub.location = (mapping.location[0]-600,mapping.location[1]+100)
                sub.operation = 'SUBTRACT'
                sub.inputs[0].default_value = 1

                div_x = nodes.new('ShaderNodeMath')
                div_x.location = (mapping.location[0]-400,mapping.location[1]+100)
                div_x.operation = 'DIVIDE'
                div_x.inputs[1].default_value = 2

                comb_loc = nodes.new('ShaderNodeCombineXYZ')
                comb_loc.location = (mapping.location[0]-200,mapping.location[1])

                comb_scale = nodes.new('ShaderNodeCombineXYZ')
                comb_scale.location = (mapping.location[0]-200,mapping.location[1]-200)

                # Connect them
                links.new(scale.outputs[0], comb_scale.inputs[1])
                links.new(scale.outputs[0], mul.inputs[0])
                links.new(mul.outputs[0], sub.inputs[1])
                links.new(mul.outputs[0], comb_scale.inputs[0])
                links.new(sub.outputs[0], div_x.inputs[0])
                links.new(div_x.outputs[0], comb_loc.inputs[0])
                links.new(div.outputs[0], comb_loc.inputs[1])

                links.new(comb_loc.outputs[0], mapping.inputs['Location'])
                links.new(comb_scale.outputs[0], mapping.inputs['Scale'])

                # Add Anamorphic ratio driver to Multiply
                d = mul.inputs[1].driver_add('default_value').driver
                var = d.variables.new()
                var.name = 'anamorphic_ratio'
                target = var.targets[0]
                target.id_type = 'CAMERA'
                target.id = cam
                target.data_path = 'dof.aperture_ratio'
                d.expression = "anamorphic_ratio"

def luxcore_opt_vignetting_mat(mat,cam,obj):
    # mat = bpy.data.materials.new(name="Material")
    #
    # mat.roughness = 1
    # mat.blend_method = 'CLIP'
    # mat.shadow_method = 'NONE'
    node_tree = mat.luxcore.node_tree
    if node_tree:
        nodes.clear()
        links.clear()
    else:
        node_tree = bpy.data.node_groups.new(name=mat.name, type="luxcore_material_nodes")
        node_tree.use_fake_user = True
        mat.luxcore.node_tree = node_tree
    # # Flag the object for update, needed in viewport render
    # obj.update_tag()

    nodes = node_tree.nodes
    links = node_tree.links

    # Create an output for the new nodes
    mapping = nodes.new("LuxCoreNodeTexMapping2D")
    mapping.location = (-300,0)
    mapping.center_map = True
    mapping.uniform_scale = 8.0

    # Create an output for the new nodes
    img = nodes.new("LuxCoreNodeTexImagemap")
    img.location = (-100,0)
    img.gamma = 1.0
    img.wrap = 'clamp'
    img["is_opt_vignetting_tex"] = True
    img.name = 'Optical Vignetting Mask'

    # Create an output for the new nodes
    inv = nodes.new("LuxCoreNodeTexInvert")
    inv.location = (200,0)

    # Create an output for the new nodes
    matte = nodes.new("LuxCoreNodeMatMatte")
    matte.inputs[0].default_value = (0.0,0.0,0.0)
    matte.location = (400,0)

    # Create an output for the new nodes
    output = nodes.new("LuxCoreNodeMatOutput")
    output.location = (600,0)

    # Connect them
    links.new(mapping.outputs[0], img.inputs[0])
    links.new(img.outputs[0], inv.inputs[0])
    links.new(inv.outputs[0], matte.inputs['Opacity'])
    links.new(matte.outputs[0], output.inputs[0])

    # Texture Rotation
    d = mapping.driver_add('rotation').driver

    var = d.variables.new()
    var.name = 'ov_rotation'
    target = var.targets[0]
    target.id_type = 'CAMERA'
    target.id = cam
    target.data_path = 'photographer.ov_rotation'

    d.expression = "ov_rotation"

    # Flag the object for update, needed in viewport render
    obj.update_tag()
    return {"FINISHED"}

class PHOTOGRAPHER_OT_Bokeh_Add(bpy.types.Operator):
    bl_idname = "photographer.bokeh_add"
    bl_label = "Enable Bokeh Texture"
    bl_description = "Adds Bokeh plane and material"
    bl_options = {'REGISTER', 'UNDO'}

    camera: bpy.props.StringProperty()

    def execute(self,context):
        cam_obj = bpy.data.objects[self.camera]
        cam = cam_obj.data

        #Store the current object selection
        current_sel = context.selected_objects
        active_obj = context.view_layer.objects.active

        # Remove Camera scaling that would break the drivers
        if cam_obj.scale != [1,1,1]:
            cam_obj.scale = [1,1,1]
        cam_obj.lock_scale = [True,True,True]

        # Switch to object mode to create plane
        if bpy.context.scene.collection.all_objects:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

        # Create Plane and name it (will become a box with a Solidify)
        bpy.ops.mesh.primitive_plane_add()
        bokeh_plane = context.view_layer.objects.active
        bokeh_plane.name = cam_obj.name + "_Bokeh_Plane"

        # Assign collections from camera
        copy_collections(cam_obj,bokeh_plane)

        unit_scale = context.scene.unit_settings.scale_length
        bokeh_plane.scale[0] = bokeh_plane.scale[1] = bokeh_plane.scale[2] = 0.2 / unit_scale
        # bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        bokeh_plane["is_bokeh_plane"] = True
        bokeh_plane.display_type = 'WIRE'

        if context.scene.render.engine == 'CYCLES':
            if bpy.app.version >= (3,0,0):
                bokeh_plane.visible_diffuse = False
                bokeh_plane.visible_glossy = False
                bokeh_plane.visible_transmission = False
                bokeh_plane.visible_volume_scatter = False
                bokeh_plane.visible_shadow = False
            else:
                bokeh_plane.cycles_visibility.diffuse = False
                bokeh_plane.cycles_visibility.glossy = False
                bokeh_plane.cycles_visibility.transmission = False
                bokeh_plane.cycles_visibility.scatter = False
                bokeh_plane.cycles_visibility.shadow = False

        # Parent to Camera using No Inverse
        # (could not find command to parent with no_inverse, using operator instead)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[cam_obj.name].select_set(True)
        bpy.data.objects[bokeh_plane.name].select_set(True)
        context.view_layer.objects.active = bpy.data.objects[cam_obj.name]
        bpy.ops.object.parent_no_inverse_set()

        clip_start = bokeh_clip_start / context.scene.unit_settings.scale_length
        # Move plane as close to the focal plane as possible
        offset = 0.0005 / context.scene.unit_settings.scale_length
        bokeh_plane.location[2] = -(clip_start + offset)
        # Make sure the cam clip is lower than the plane position
        if cam.clip_start > clip_start:
            cam.clip_start = clip_start

        # Lock Bokeh Plane transform for user
        bokeh_plane.lock_location = bokeh_plane.lock_rotation = bokeh_plane.lock_scale = [True, True, True]
        bokeh_plane.hide_select = True

        # Get material
        mat_name = bokeh_plane.name + "_Mat"
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name=mat_name)

            mat.roughness = 1
            mat.blend_method = 'BLEND'
            mat.shadow_method = 'NONE'

            # Enable 'Use nodes':
            mat.use_nodes = True

            if mat.node_tree:
                mat.node_tree.links.clear()
                mat.node_tree.nodes.clear()

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            img = nodes.new('ShaderNodeTexImage')
            img["is_bokeh_tex"] = True
            img.location = (200,0)
            img.extension = 'EXTEND'
            img.name = 'Bokeh Texture'

            # Scale value
            scale = nodes.new('ShaderNodeValue')
            scale.location = (-1000,-100)
            scale.outputs[0].default_value = 7 # Default Scale Value
            scale.name = 'Size'

            # Mapping
            mapping = nodes.new('ShaderNodeMapping')
            mapping.location = (-200,0)

            rotate = nodes.new('ShaderNodeVectorRotate')
            rotate.location = (0,0)
            rotate.inputs[1].default_value[0] = 0.5
            rotate.inputs[1].default_value[1] = 0.5

            coord = nodes.new('ShaderNodeTexCoord')
            coord.location = (-400,400)

            div = nodes.new('ShaderNodeMath')
            div.location = (-400,-100)
            div.operation = 'DIVIDE'
            div.inputs[1].default_value = 2

            sub = nodes.new('ShaderNodeMath')
            sub.location = (-600,-100)
            sub.operation = 'SUBTRACT'
            sub.inputs[0].default_value = 1

            # Connect them
            links.new(scale.outputs[0], sub.inputs[1])
            links.new(sub.outputs[0], div.inputs[0])
            links.new(div.outputs[0], mapping.inputs['Location'])
            links.new(scale.outputs[0], mapping.inputs['Scale'])
            links.new(coord.outputs['UV'], mapping.inputs['Vector'])
            links.new(mapping.outputs[0], rotate.inputs[0])
            links.new(rotate.outputs[0], img.inputs[0])

            # Brightness
            br = nodes.new('ShaderNodeValue')
            br.location = (500,200)
            br.name = "Brightness"

            # Multiply
            mul = nodes.new('ShaderNodeMixRGB')
            mul.location = (600,0)
            mul.blend_type = 'MULTIPLY'
            mul.inputs[0].default_value = 1

            # Add Cycles transparent shader
            transp = nodes.new('ShaderNodeBsdfTransparent')
            transp.location = (800,0)

            # Add Cycles output node
            output = nodes.new('ShaderNodeOutputMaterial')
            output.location = (1000,0)
            output.target = 'ALL'

            # Connect them
            links.new(img.outputs[0], mul.inputs[1])
            links.new(br.outputs[0], mul.inputs[2])
            links.new(mul.outputs[0], transp.inputs[0])
            links.new(transp.outputs[0], output.inputs['Surface'])

            # Add Eevee transparent shader
            transp_eevee = nodes.new('ShaderNodeBsdfTransparent')
            transp_eevee.location = (800,200)

            # Add Eevee output node
            output_eevee = nodes.new('ShaderNodeOutputMaterial')
            output_eevee.location = (1000,200)
            output_eevee.target = 'EEVEE'

            # Connect them
            links.new(transp_eevee.outputs[0], output_eevee.inputs['Surface'])

            d = scale.outputs[0].driver_add('default_value').driver

            var = d.variables.new()
            var.name = 'sw'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'sensor_width'

            var = d.variables.new()
            var.name = 'focal'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'lens'

            var = d.variables.new()
            var.name = 'aperture'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'dof.aperture_fstop'

            # var = d.variables.new()
            # var.name = 'unit_scale'
            # target = var.targets[0]
            # target.id_type = 'SCENE'
            # target.id = context.scene
            # target.data_path = 'unit_settings.scale_length'

            d.expression = "22 * (sw/2) / focal * aperture / " + str(unit_scale)
            # 22 sets the default size according to the plane size

            # Texture Rotation
            d = rotate.inputs[3].driver_add('default_value').driver

            var = d.variables.new()
            var.name = 'bokeh_rotation'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'photographer.bokeh_rotation'

            d.expression = "bokeh_rotation"

            # Brightness
            d = br.outputs[0].driver_add('default_value').driver

            var = d.variables.new()
            var.name = 'bokeh_brightness'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'photographer.bokeh_brightness'

            d.expression = "bokeh_brightness"

            # # Contrast
            # d = bc.inputs[2].driver_add('default_value').driver
            #
            # var = d.variables.new()
            # var.name = 'bokeh_contrast'
            # target = var.targets[0]
            # target.id_type = 'CAMERA'
            # target.id = cam
            # target.data_path = 'photographer.bokeh_contrast'
            #
            # d.expression = "bokeh_contrast"

        # Add new features to old materials
        upgrade_bokeh_material(self,mat,cam)

        # Assign it to object
        if bokeh_plane.data.materials:
            # Assign to 1st material slot
            bokeh_plane.data.materials[0] = mat
        else:
            # Append if no slots
            bokeh_plane.data.materials.append(mat)

        #Restore the previous selection
        bpy.ops.object.select_all(action='DESELECT')
        if current_sel:
            for o in current_sel:
                bpy.data.objects[o.name].select_set(True)
        if active_obj:
            context.view_layer.objects.active = active_obj

        return {'FINISHED'}

class PHOTOGRAPHER_OT_Bokeh_Delete(bpy.types.Operator):
    bl_idname = "photographer.bokeh_delete"
    bl_label = "Disable Bokeh Texture"
    bl_description = "Deletes Bokeh Plane mesh"
    bl_options = {'REGISTER', 'UNDO'}

    camera: bpy.props.StringProperty()

    def execute(self,context):
        obj = bpy.data.objects
        cam_obj = obj[self.camera]
        cam = cam_obj.data

        # Disable Camera Limits
        cam.show_limits = False

        for c in cam_obj.children:
            # Checking to see if this object has the custom flag written to it- it will default to False in the event that the key does not exist
            if c.get("is_bokeh_plane", False):
                if isinstance(c.data, bpy.types.Mesh):
                    # remove the mesh data first, while the object still exists
                    bpy.data.meshes.remove(c.data)
                    try:
                        bpy.data.objects.remove(c)
                    except ReferenceError:
                        # ignore a ReferenceError exception when the StructRNA is removed
                        pass

        return {'FINISHED'}

class PHOTOGRAPHER_OT_OptVignetting_Add(bpy.types.Operator):
    bl_idname = "photographer.optvignetting_add"
    bl_label = "Enable Optical Vignetting"
    bl_description = "Adds Optical Vignetting cube and material"
    bl_options = {'REGISTER', 'UNDO'}

    camera: bpy.props.StringProperty()

    def execute(self,context):
        cam_obj = bpy.data.objects[self.camera]
        cam = cam_obj.data

        #Store the current object selection
        current_sel = context.selected_objects
        active_obj = context.view_layer.objects.active

        # Remove Camera scaling that would break the drivers
        if cam_obj.scale != [1,1,1]:
            cam_obj.scale = [1,1,1]
        cam_obj.lock_scale = [True,True,True]

        # Switch to object mode to create plane
        if bpy.context.scene.collection.all_objects:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

        # Create Plane and name it (will become a box with a Solidify)
        bpy.ops.mesh.primitive_plane_add()
        ov_box = context.view_layer.objects.active
        ov_box.name = cam_obj.name + "_Optical_Vignetting"

        ov_box.scale[0] = ov_box.scale[1] = ov_box.scale[2] = 0.1

        # Assign collections from camera
        copy_collections(cam_obj,ov_box)


        ov_box["is_opt_vignetting"] = True
        # Commented 'WIRE', need to be visible for EEEVEE
        # ov_box.display_type = 'WIRE'

        if context.scene.render.engine == 'CYCLES':
            if bpy.app.version >= (3,0,0):
                ov_box.visible_diffuse = False
                ov_box.visible_glossy = False
                ov_box.visible_transmission = False
                ov_box.visible_volume_scatter = False
                ov_box.visible_shadow = False
            else:
                ov_box.cycles_visibility.diffuse = False
                ov_box.cycles_visibility.glossy = False
                ov_box.cycles_visibility.transmission = False
                ov_box.cycles_visibility.scatter = False
                ov_box.cycles_visibility.shadow = False

        # Parent to Camera using No Inverse
        # (could not find command to parent with no_inverse, using operator instead)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[cam_obj.name].select_set(True)
        bpy.data.objects[ov_box.name].select_set(True)
        context.view_layer.objects.active = bpy.data.objects[cam_obj.name]
        bpy.ops.object.parent_no_inverse_set()

        # Move plane in front of the camera
        ov_box.location[2] = -0.03
        # Make sure the cam clip is lower than the plane position
        clip_start = bokeh_clip_start / context.scene.unit_settings.scale_length
        if cam.clip_start > clip_start:
            cam.clip_start = clip_start

        mod = ov_box.modifiers.get("Opt_Vignetting_Box_Solidify")
        if mod is None:
            mod = ov_box.modifiers.new("Opt_Vignetting_Box_Solidify", 'SOLIDIFY')
        mod.thickness = -1

        # Lock OV Box transform for user
        ov_box.lock_location = ov_box.lock_rotation = ov_box.lock_scale = [True, True, True]
        ov_box.hide_select = True

        # Get material
        mat_name = ov_box.name + "_Mat"
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name=mat_name)
            mat.roughness = 1
            mat.blend_method = 'CLIP'
            mat.shadow_method = 'NONE'

            # Enable 'Use nodes':
            mat.use_nodes = True

            if context.scene.render.engine == 'LUXCORE':
                luxcore_opt_vignetting_mat(mat,cam,ov_box)

            # Still do Cycles/EEVEE material even if using LuxCore
            if mat.node_tree:
                mat.node_tree.links.clear()
                mat.node_tree.nodes.clear()

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Add Cycles transparent shader
            img = nodes.new('ShaderNodeTexImage')
            img["is_opt_vignetting_tex"] = True
            img.location = (0,0)
            img.extension = 'EXTEND'
            img.name = 'Optical Vignetting Mask'

            # Mapping
            mapping = nodes.new('ShaderNodeMapping')
            mapping.location = (-400,0)

            rotate = nodes.new('ShaderNodeVectorRotate')
            rotate.location = (-200,0)
            rotate.inputs[1].default_value[0] = 0.5
            rotate.inputs[1].default_value[1] = 0.5

            coord = nodes.new('ShaderNodeTexCoord')
            coord.location = (-600,200)

            div = nodes.new('ShaderNodeMath')
            div.location = (-600,-100)
            div.operation = 'DIVIDE'
            div.inputs[1].default_value = 2

            sub = nodes.new('ShaderNodeMath')
            sub.location = (-800,-100)
            sub.operation = 'SUBTRACT'
            sub.inputs[0].default_value = 1

            scale = nodes.new('ShaderNodeValue')
            scale.location = (-1000,-100)
            scale.outputs[0].default_value = 8
            scale.name = 'Scale'

            # Connect them
            links.new(scale.outputs[0], sub.inputs[1])
            links.new(sub.outputs[0], div.inputs[0])
            links.new(div.outputs[0], mapping.inputs['Location'])
            links.new(scale.outputs[0], mapping.inputs['Scale'])
            links.new(coord.outputs['UV'], mapping.inputs['Vector'])
            links.new(mapping.outputs[0], rotate.inputs[0])
            links.new(rotate.outputs[0], img.inputs[0])

            # Add Cycles transparent shader
            transp = nodes.new('ShaderNodeBsdfTransparent')
            transp.location = (600,0)

            # Add Cycles output node
            output = nodes.new('ShaderNodeOutputMaterial')
            output.location = (800,0)
            output.target = 'ALL'

            # Connect them
            links.new(img.outputs[0], transp.inputs[0])
            links.new(transp.outputs[0], output.inputs['Surface'])

            if bpy.app.version < (2,93,0):
                # Add Eevee transparent shader
                transp_eevee = nodes.new('ShaderNodeBsdfTransparent')
                transp_eevee.location = (600,200)

                # Add Eevee output node
                output_eevee = nodes.new('ShaderNodeOutputMaterial')
                output_eevee.location = (800,200)
                output_eevee.target = 'EEVEE'

                # Connect them
                links.new(transp_eevee.outputs[0], output_eevee.inputs['Surface'])

            # Texture Rotation
            d = rotate.inputs[3].driver_add('default_value').driver

            var = d.variables.new()
            var.name = 'ov_rotation'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'photographer.ov_rotation'

            d.expression = "ov_rotation"

        # Location of Plane based on Focal Length
        loc_z = "pow(fl*0.001,2)*25"

        # Plane location Y for lens_shift
        d = ov_box.driver_add('location',1).driver
        var = d.variables.new()
        var.name = 'lens_shift'
        target = var.targets[0]
        target.id_type = 'CAMERA'
        target.id = cam
        target.data_path = 'shift_y'

        var = d.variables.new()
        var.name = 'fl'
        target = var.targets[0]
        target.id_type = 'CAMERA'
        target.id = cam
        target.data_path = 'lens'

        d.expression = "tan(atan(lens_shift/(fl/36)))*"+loc_z

        # Increasing Box distance with focal length to maintain occlusion
        d = ov_box.driver_add('location',2).driver

        var = d.variables.new()
        var.name = 'fl'
        target = var.targets[0]
        target.id_type = 'CAMERA'
        target.id = cam
        target.data_path = 'lens'

        # var = d.variables.new()
        # var.name = 'unit_scale'
        # target = var.targets[0]
        # target.id_type = 'SCENE'
        # target.id = context.scene
        # target.data_path = 'unit_settings.scale_length'

        unit_scale = str(context.scene.unit_settings.scale_length)
        d.expression = "-" + loc_z + "/ " + unit_scale
        # *25 was found empiracally to maintain occlusion.

        # Bokeh Texture size
        fcurve_driver = ov_box.driver_add('scale')
        drivers = [f.driver for f in fcurve_driver]

        for d in drivers:
            var = d.variables.new()
            var.name = 'fl'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'lens'

            var = d.variables.new()
            var.name = 'sw'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'sensor_width'

            var = d.variables.new()
            var.name = 'ov_scale'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'photographer.ov_scale'

            var = d.variables.new()
            var.name = 'aperture'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = cam
            target.data_path = 'dof.aperture_fstop'

            # var = d.variables.new()
            # var.name = 'unit_scale'
            # target = var.targets[0]
            # target.id_type = 'SCENE'
            # target.id = context.scene
            # target.data_path = 'unit_settings.scale_length'

            # 25 is the Scale value used in the Shader.This is to make the hole smaller at the center of the face.
            drivers[0].expression = '(' + loc_z + '* (sw/2) / fl)/(ov_scale+0.1)*8/' + unit_scale
            drivers[1].expression = '(' + loc_z + '* (sw/2) / fl)/(ov_scale+0.1)*8/' + unit_scale
            drivers[2].expression = '(' + loc_z + '* (sw/2) / fl)/(ov_scale+0.1)*8/' + unit_scale
            # + 0.1 and * 8 to make the 0 to 1 slider sensical.

        # Assign it to object
        if ov_box.data.materials:
            # Assign to 1st material slot
            ov_box.data.materials[0] = mat
        else:
            # Append if no slots
            ov_box.data.materials.append(mat)

        # Make sure it's transparent in viewport for EEVEE
        mat.diffuse_color[3] = 0.0

        # Remove EEVEE Shader if version supports new DoF
        if bpy.app.version >= (2,93,0):
            nodes = mat.node_tree.nodes
            for n in nodes:
                if n.bl_idname=='ShaderNodeOutputMaterial' and n.target=='EEVEE':
                    nodes.remove(n)

        #Restore the previous selection
        bpy.ops.object.select_all(action='DESELECT')
        if current_sel:
            for o in current_sel:
                bpy.data.objects[o.name].select_set(True)
        if active_obj:
            context.view_layer.objects.active = active_obj

        return {'FINISHED'}

class PHOTOGRAPHER_OT_OptVignetting_Delete(bpy.types.Operator):
    bl_idname = "photographer.optvignetting_delete"
    bl_label = "Disable Optical Vignetting"
    bl_description = "Delete Optical Vignetting object"
    bl_options = {'REGISTER', 'UNDO'}

    camera: bpy.props.StringProperty()

    def execute(self,context):
        obj = bpy.data.objects
        cam_obj = obj[self.camera]
        cam = cam_obj.data

        # Disable Camera Limits
        cam.show_limits = False

        for c in cam_obj.children:
            # Checking to see if this object has the custom flag written to it- it will default to False in the event that the key does not exist
            if c.get("is_opt_vignetting", False):
                if isinstance(c.data, bpy.types.Mesh):
                    # remove the mesh data first, while the object still exists
                    bpy.data.meshes.remove(c.data)
                    try:
                        bpy.data.objects.remove(c)
                    except ReferenceError:
                        # ignore a ReferenceError exception when the StructRNA is removed
                        pass

        return {'FINISHED'}
