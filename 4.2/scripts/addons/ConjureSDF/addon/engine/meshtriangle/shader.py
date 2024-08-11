from bgl import *

import os.path


from ..shaders.main import BaseShader

from ..settings import GL_TESS_EVALUATION_SHADER, GL_TESS_CONTROL_SHADER
from ConjureSDF.get_path import get_path


class MeshTriangleShader(BaseShader):
    """Shader for rendering regular blender meshes"""

    def __init__(self):
        super().__init__()

        vs_shader, fs_shader = self.get_shader_source()

        self.sources[GL_VERTEX_SHADER] = vs_shader
        self.sources[GL_FRAGMENT_SHADER] = fs_shader

    def get_shader_source(self):
        # get path to addon
        addon_relative_path = os.path.join('addon', 'engine', 'meshtriangle', 'source')

        addon_path = get_path()

        # get path to shader source files
        src_folder = os.path.join(addon_path, addon_relative_path)

        template_src_files = (
        "meshtriangle.vs.glsl",
        "matcap.fs.glsl",
        )

        sources = []

        for template in template_src_files:
            src_file = os.path.join(src_folder, template)
            with open(src_file) as f:
                sources.append(f.read())

        return sources[0], sources[1]
