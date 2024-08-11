import bpy

from bgl import *

from bpy.types import Scene, Object, Collection

import os

from ..shaders.main import BaseShader
from ..settings import GL_TESS_EVALUATION_SHADER, GL_TESS_CONTROL_SHADER

from .fallback import SDF_VERTEX_SHADER, SDF_FRAGMENT_SHADER

from .builder import generate_scene, build_shaders
from ...util.object import get_csdf_prims

class SDF_Shader(BaseShader):
    """Shader compiled from the user's GLSL source files"""
    def __init__(self, depsgraph):
        super().__init__()

        self.stage_filenames = dict()
        self.compile = True

        scene = generate_scene(depsgraph)

        self.SDF_VERTEX_SHADER, self.SDF_FRAGMENT_SHADER = build_shaders(scene)

        self.sdf_prim_count = len(get_csdf_prims(bpy.context.scene))

    def update_settings(self, settings, depsgraph):
        """Update current settings and check if a recompile is necessary
        Raises:
            FileNotFoundError: If the vertex or fragment shader are missing
        Args:
            settings (CSDFRendererSettings): Current settings to read
        """
        # if not os.path.isfile(settings.vert_filename):
        #     raise FileNotFoundError('Missing required vertex shader')

        # if not os.path.isfile(settings.frag_filename):
        #     raise FileNotFoundError('Missing required fragment shader')

        # TODO : Only need vertex and fragment shaders normally, but commenting out the rest causes compilation failure/errors?
        self.stage_filenames = {
            GL_VERTEX_SHADER:           self.SDF_VERTEX_SHADER,
            GL_TESS_CONTROL_SHADER:     settings.tesc_filename,
            GL_TESS_EVALUATION_SHADER:  settings.tese_filename,
            GL_GEOMETRY_SHADER:         settings.geom_filename,
            GL_FRAGMENT_SHADER:         self.SDF_FRAGMENT_SHADER
        }

        # get the number of sdf primitives in the scene. If one has been added or removed, recompile
        for update in depsgraph.updates:

            # fixes undo not triggering a shader recompilation
            # TODO : this also triggers when making a new collection, moving an object around, etc.
            # see if possible to narrow this down more
            if type(update.id) == Collection:
                self.compile = True

            if type(update.id) == Scene or Object:

                curr_sdf_prim_count = len(get_csdf_prims(bpy.context.scene))

                if curr_sdf_prim_count != self.sdf_prim_count:
                    self.sdf_prim_count = curr_sdf_prim_count
                    self.compile = True
                    
                    # TODO : breaking here might cause issues if multiple objects are added in one go (for example, by duplicating existing primitives)
                    # break

        if settings.force_reload or self.compile:
            
            settings.force_reload = False
            self.compile = False

            # TODO : this might break the code elsewhere, keep an eye on selection issues
            settings.block_index_callback = False
            # settings.block_selection_handler = False

            scene = generate_scene(depsgraph)

            self.SDF_VERTEX_SHADER, self.SDF_FRAGMENT_SHADER = build_shaders(scene)

            self.stage_filenames[GL_FRAGMENT_SHADER] = self.SDF_FRAGMENT_SHADER

            self.load_source_files()
            self.needs_recompile = True

            

    def load_source_files(self):
        """Read source files into their respective stage buffers for recompilation"""
        self.stage = [f for f in self.stage_filenames]


        for stage in self.STAGES:
            if self.stage_filenames[stage]:

                if not os.path.isfile(self.stage_filenames[stage]):
                    subshader = self.stage_filenames[stage]
                    self.sources[stage] = subshader
                else:
                    with open(self.stage_filenames[stage]) as f:
                        self.sources[stage] = f.read()
            else:
                self.sources[stage] = None

