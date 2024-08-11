from random import uniform
import bpy

import os.path

from bgl import *

from mathutils import Vector, Matrix

from .mesh import Mesh

from .shaders.fallbacks import FallbackShader
from .shaders.user import UserShader

from .sdf.main import SDF_ROOT
from .sdf.shader import SDF_Shader

from .meshtriangle.shader import MeshTriangleShader


from ..util.math import objects_sphere_bounds
from ..util.object import get_csdf_prims
from ConjureSDF.get_path import get_addon_location

from math import ceil



class CSDFRenderEngine(bpy.types.RenderEngine):
    bl_idname = "CSDF_renderer"
    bl_label = "Conjure Vision"
    bl_use_preview = False

    # Enable an OpenGL context for the engine (2.91+ only)
    bl_use_gpu_context = True

    # Apply Blender's compositing on render results.
    # This enables the "Color Management" section of the scene settings
    bl_use_postprocess = True

    def __init__(self):
        """Called when a new render engine instance is created.
        Note that multiple instances can exist @ once, e.g. a viewport and final render
        """
        self.meshes = dict()

        self.light_direction = (0, 0, 1, 0)
        self.light_color = (1, 1, 1, 1)

        self.fallback_shader = FallbackShader()
        self.user_shader = UserShader()

        self.sdf_shader = None
        if bpy.context.scene.objects.get("CSDF Root"):
            self.sdf_shader = SDF_Shader(bpy.context.evaluated_depsgraph_get())
            self.sdf_root = SDF_ROOT("test")

        self.meshtriangle_shader = MeshTriangleShader()

        # TODO : set a default from the context.preferences.studio_lights
        
        
        # get path to addon
        addon_relative_path = r"addon\resources\matcaps\clay_brown.exr"
        addon_path = get_addon_location()

        # get path to shader source files
        matcap_file = os.path.join(addon_path, addon_relative_path)

        bpy.data.images.load(filepath=matcap_file, check_existing=False)
        self.matcap = bpy.data.images["clay_brown.exr"]
        

    def __del__(self):
        """Clean up render engine data, e.g. stopping running render threads"""
        pass

    def render(self, depsgraph):
        """Handle final render (F12) and material preview window renders"""
        # If you want to support material preview windows you will
        # also need to set `bl_use_preview = True`
        pass

    def view_update(self, context, depsgraph):
        """Called when a scene or 3D viewport changes"""

        shading = context.scene.display.shading
        matcap_path = shading.selected_studio_light.path
        matcap_name = os.path.basename(matcap_path)

        # TODO : cleanup previous matcap
        # TODO : make current matcap texture a fake user? Or find way to load image data in without bpy.data.images.load
        if matcap_path:
            bpy.data.images.load(filepath=matcap_path, check_existing=False)
            self.matcap = bpy.data.images[matcap_name]

        self.check_shaders(context, depsgraph)

        region = context.region
        view3d = context.space_data
        scene = depsgraph.scene

        self.updated_meshes = dict()
        self.updated_geometries = []

        # Check for any updated mesh geometry to rebuild GPU buffers
        for update in depsgraph.updates:
            name = update.id.name
            if type(update.id) == bpy.types.Object:
                if update.is_updated_geometry and name in self.meshes:
                    self.updated_geometries.append(name)

        # Aggregate everything visible in the scene that we care about
        for obj in scene.objects:
            if not obj.visible_get():
                continue

            if obj.csdfData.is_csdf_prim:
                    continue

            if obj.type == 'MESH':
                if obj.display_type in ('SOLID', 'TEXTURED'):
                    self.update_mesh(obj, depsgraph)
            elif obj.type == 'LIGHT' and obj.data.type == 'SUN':
                self.update_light(obj)

        self.meshes = self.updated_meshes

    def update_mesh(self, obj, depsgraph):
        """Update mesh data for next render"""

        # Get/create the mesh instance and determine if we need
        # to reupload geometry to the GPU for this mesh
        rebuild_geometry = obj.name in self.updated_geometries
        if obj.name not in self.meshes:
            mesh = Mesh(obj.name)
            rebuild_geometry = True
        else:
            mesh = self.meshes[obj.name]

        mesh.update(obj)

        # If modified - prep the mesh to be copied to the GPU next draw
        if rebuild_geometry:
            mesh.rebuild(obj.evaluated_get(depsgraph))

        self.updated_meshes[obj.name] = mesh

    def update_light(self, obj):
        """Update main (sun) light data for the next render"""
        light_type = obj.data.type

        direction = obj.matrix_world.to_quaternion() @ Vector((0, 0, 1))
        color = obj.data.color
        intensity = obj.data.csdf.intensity

        self.light_direction = (direction[0], direction[1], direction[2], 0)
        self.light_color = (color[0], color[1], color[2], intensity)

    def check_shaders(self, context, depsgraph):
        """Check if we should reload the shader sources"""
        settings = context.scene.csdf

        # Check for source file changes or other setting changes
        try:
            # for regular meshes
            self.meshtriangle_shader.update_settings(settings)
            settings.last_shader_error = self.meshtriangle_shader.last_error

            self.sdf_shader.update_settings(settings, depsgraph)
            settings.last_shader_error = self.sdf_shader.last_error

        except Exception as e:
            settings.last_shader_error = str(e)


    def send_primitive_buffer(self, sdf_objs):

        num_sdf_objs = len(sdf_objs)

        primitive_data = compose_primitive_data(sdf_objs)

        uniform_data = Buffer(GL_FLOAT, num_sdf_objs*28, primitive_data)

        PrimitiveBlock = Buffer(GL_INT, 1)
        glGenBuffers(1, PrimitiveBlock)
        
        glBindBuffer(GL_UNIFORM_BUFFER, PrimitiveBlock[0])
        glBufferData(GL_UNIFORM_BUFFER, num_sdf_objs*112, None, GL_STATIC_DRAW)
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

        glBindBufferBase(GL_UNIFORM_BUFFER, 0, PrimitiveBlock[0])

        glBindBuffer(GL_UNIFORM_BUFFER, PrimitiveBlock[0])

        glBufferSubData(GL_UNIFORM_BUFFER, 0, num_sdf_objs*112, uniform_data)
        glBindBuffer(GL_UNIFORM_BUFFER, 0)


    def draw_SDF(self, context, scene, region, region3d, settings, root, sdf_objs):

        # glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)

        # glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
        # changed to GL_SRC_ALPHA to allow for discarding of pixels in fs
        glBlendFunc(GL_ONE, GL_SRC_ALPHA)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        self.bind_display_space_shader(scene)

        shader = self.sdf_shader
        
        if not shader.bind():
            shader = self.fallback_shader
            shader.bind()


        if len(sdf_objs)>0:
            self.send_primitive_buffer(sdf_objs)


        if len(sdf_objs) >= 1:
            bounds_c, bounds_r = objects_sphere_bounds(sdf_objs)
        else:
            bounds_c = Vector((0,0,0))
            bounds_r = 1

        if len(sdf_objs) == 1:
            bounds_c = sdf_objs[0].location
            bounds_r = bounds_r*2

        shader.set_vec3("u_bounds_pos", bounds_c)
        shader.set_float("u_bounds_radius", bounds_r)

        if root.csdfData.mirror_smooth:
            shader.set_float("mirror_smoothing_strength", root.csdfData.mirror_smooth_strength)

        shader.set_tex("matcap", self.matcap)
        shader.set_vec2("u_resolution", [region.width, region.height])
        shader.set_vec4("steps_dist_surface_scale", [settings.max_steps, settings.max_distance, settings.min_surface_distance, settings.marching_scale])

        # https://blender.stackexchange.com/questions/22963/viewport-position-and-direction
        shader.set_mat4("u_viewMatrix", region3d.view_matrix)
        # shader.set_vec3("u_cameraPosition", region3d.view_matrix.inverted().translation)

        pv = region3d.window_matrix @ region3d.view_matrix
        pv = Matrix(pv).inverted().transposed()

        projm = region3d.view_matrix @ region3d.window_matrix
        projm = Matrix(projm).inverted()

        shader.set_mat4("inverse_perspectiveMatrix", pv)
        shader.set_mat4("ProjectionMatrix", region3d.perspective_matrix)


        # depth calculation
        # from https://iquilezles.org/articles/raypolys/
        near = context.space_data.clip_start
        far = context.space_data.clip_end

        a = (far+near)/(far-near)
        b = (2.0*far*near)/(far-near)

        shader.set_float("depth_a", a)
        shader.set_float("depth_b", b)

        # also used in orthographic
        viewQuat = region3d.view_matrix.inverted().to_quaternion()

        # used to correct depth
        forward = Vector((0,0,-1))
        forward.rotate(viewQuat)
        shader.set_vec3("camForward", forward )


        shader.set_int("orthoview", 0)
        # if camera is in orthographic mode
        if region3d.view_perspective == 'ORTHO':
            shader.set_int("orthoview", 1)

            # based on https://twitter.com/IY0YI 's Ernst Renderer
            orthoscale = region3d.view_distance*3.0*(16/50)*(50/context.area.spaces.active.lens)
            shader.set_float("orthoScale",  orthoscale)
            # shader.set_float("orthoDist", region3d.view_distance)

            shader.set_vec3("viewpos", region3d.view_matrix.inverted().translation)

            # do the math here instead of in the shader, seems to be more correct for some reason
            up = Vector((0,1,0))
            up.rotate(viewQuat)

            shader.set_vec3("camUp", up )
            shader.set_vec3("camForward", forward )
        
        # glEnable(GL_DEPTH_TEST)

        # Clear background with the user's clear color
        clear_color = scene.csdf.clear_color
        glClearColor(clear_color[0], clear_color[1], clear_color[2], 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if len(sdf_objs)>0:
            self.sdf_root.draw(shader)

        shader.unbind()
        self.unbind_display_space_shader()

        # glDisable(GL_BLEND)


    def draw_meshtriangle(self, context, scene, region3d):

        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_TEXTURE_2D)

        self.bind_display_space_shader(scene)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        # for regular geometry
        shader = self.meshtriangle_shader
        shader.bind()



        shader.set_tex("matcap", self.matcap)

        # Set up MVP matrices
        shader.set_mat4("u_viewMatrix", region3d.view_matrix)
        shader.set_mat4("ViewMatrix", region3d.view_matrix.transposed())
        shader.set_mat4("ProjectionMatrix", region3d.window_matrix.transposed())
        shader.set_mat4("CameraMatrix", region3d.view_matrix.inverted().transposed())

        # Upload current lighting information
        shader.set_vec4("_MainLightDirection", (0,0,1, 0))

        for mesh in self.meshes.values():
            mv = region3d.view_matrix @ mesh.model_matrix
            mvp = region3d.window_matrix @ mv

            # Set per-mesh uniforms
            shader.set_mat4("ModelMatrix", mesh.model_matrix.transposed())
            shader.set_mat4("ModelViewMatrix", mv.transposed())
            shader.set_mat4("ModelViewProjectionMatrix", mvp.transposed())

            # Draw the mesh itself
            mesh.draw(shader)

        shader.unbind()
        self.unbind_display_space_shader()

        glDisable(GL_BLEND)



    def view_draw(self, context, depsgraph):
        """Called whenever Blender redraws the 3D viewport.
        In 2.91+ this is also where you can safely interact
        with the GL context for this RenderEngine.
        """

        scene = depsgraph.scene
        region = context.region
        region3d = context.region_data
        settings = scene.csdf

        root = scene.objects.get("CSDF Root")

        if root:
            sdf_objs = get_csdf_prims(scene)
            # includes root object
            if len (sdf_objs) > 1:
                # happens when rendering was turned on before a root or prims were present
                if not self.sdf_shader:
                    self.__init__()

                self.draw_SDF(context, scene, region, region3d, settings, root, sdf_objs)

        # FOR REGULAR MESHES
        self.draw_meshtriangle(context, scene, region3d)




def compose_primitive_data(sdf_objs):
    primitive_data = []

    for obj in sdf_objs:
        
        csdfData = obj.csdfData

        ob = obj
        obj_world_mat = Matrix()
        while ob.parent:
            obj_world_mat = ob.matrix_local @ obj_world_mat
            ob = ob.parent
        obj_world_mat = ob.matrix_local @ obj_world_mat
        loc, rot, _ = obj_world_mat.decompose()

        # location
        primitive_data += loc[:]
        # op strength
        primitive_data.append(csdfData.operation_strength)

        # dimension
        primitive_data += obj.scale[:]
        # radius
        primitive_data.append(csdfData.rounding)

        # trans/rot matrix
        trans_rot_mat = Matrix.LocRotScale(loc, rot, None)
        for row in trans_rot_mat:
            primitive_data += row[:]

        # additional parameters
        # if csdfData.primitive_type in ('CapCone', 'rCapCone'):
        #     primitive_data.append(csdfData.parm01)
        # else:
        #     primitive_data += [0.0]

        primitive_data.append(csdfData.solidify_strength)
        primitive_data += [0.0, 0.0, 0.0]

    return primitive_data
