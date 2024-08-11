
from bgl import *

from ..settings import GL_TESS_CONTROL_SHADER, GL_TESS_EVALUATION_SHADER

import numpy as np

class CompileError(Exception):
    pass

class LinkError(Exception):
    pass


class BaseShader:
    """Encapsulate shader compilation and configuration
    Attributes:
        program (int): Shader program ID or None if not loaded
        last_error (str): Last shader compilation error
        sources (dict): Dictionary mapping GL stage constant to shader source string
        needs_recompile (bool): Should the render thread try to recompile shader sources
    """

    # Supported GLSL stages
    STAGES = [
        GL_VERTEX_SHADER,
        GL_TESS_EVALUATION_SHADER,
        GL_TESS_CONTROL_SHADER,
        GL_GEOMETRY_SHADER,
        GL_FRAGMENT_SHADER
    ]

    def __init__(self):
        self.program = None
        self.last_error = ''
        self.sources = dict.fromkeys(self.STAGES, None)
        self.needs_recompile = True

        self.uniform_cache = {}

    def update_settings(self, settings):
        """Update current settings and check if a recompile is necessary.
        This method is called from the main thread. Do not perform any actual
        shader compilation here - instead flag it for a recompile on the
        render thread by setting `self.needs_recompile` to true.
        Args:
            settings (CSDFRendererSettings): Current settings to read
        """
        pass

    def recompile(self):
        """Recompile shaders from sources, setting `self.last_error` if anything goes wrong.
        This *MUST* be called from within the render thread to safely
        compile shaders within the RenderEngine's GL context.
        """

        self.uniform_cache = {}

        try:
            self.program = self.compile_program()
            self.last_error = ''
        except Exception as err:
            self.last_error = str(err)
            self.program = None

    @property
    def has_tessellation(self) -> bool:
        """Does this shader perform tessellation"""
        return self.sources[GL_TESS_CONTROL_SHADER] is not None and self.sources[GL_TESS_EVALUATION_SHADER] is not None

    def compile_stage(self, stage: int):
        """Compile a specific shader stage from `self.sources`
        Args:
            stage (int): GL stage (e.g. `GL_VERTEX_SHADER`)
        Returns:
            int|None: Compiled Shader ID or None if the stage does not have a source
        Raises:
            CompileError: If GL fails to compile the stage
        """
        if not self.sources[stage]: # Skip stage
            return None

        shader = glCreateShader(stage)
        glShaderSource(shader, self.sources[stage])
        glCompileShader(shader)

        #Check for compile errors
        shader_ok = Buffer(GL_INT, 1)
        glGetShaderiv(shader, GL_COMPILE_STATUS, shader_ok)

        if shader_ok[0] == True:
            return shader

        # If not okay, read the error from GL logs
        bufferSize = 1024
        length = Buffer(GL_INT, 1)
        infoLog = Buffer(GL_BYTE, [bufferSize])
        glGetShaderInfoLog(shader, bufferSize, length, infoLog)

        if stage == GL_VERTEX_SHADER:
            stage_name = 'Vertex'
        elif stage == GL_FRAGMENT_SHADER:
            stage_name = 'Fragment'
        elif stage == GL_TESS_CONTROL_SHADER:
            stage_name = 'Tessellation Control'
        elif stage == GL_TESS_EVALUATION_SHADER:
            stage_name = 'Tessellation Evaluation'
        elif stage == GL_GEOMETRY_SHADER:
            stage_name = 'Geometry'

        # Reconstruct byte data into a string
        err = ''.join(chr(infoLog[i]) for i in range(length[0]))
        raise CompileError(stage_name + ' Shader Error:\n' + err)

    def compile_program(self):
        """Create a GL shader program from current `self.sources`
        Returns:
            int: GL program ID
        Raises:
            CompileError: If one or more stages fail to compile
            LinkError: If the program fails to link stages
        """
        vs = self.compile_stage(GL_VERTEX_SHADER)
        fs = self.compile_stage(GL_FRAGMENT_SHADER)
        tcs = self.compile_stage(GL_TESS_CONTROL_SHADER)
        tes = self.compile_stage(GL_TESS_EVALUATION_SHADER)
        gs = self.compile_stage(GL_GEOMETRY_SHADER)

        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        if tcs: glAttachShader(program, tcs)
        if tes: glAttachShader(program, tes)
        if gs: glAttachShader(program, gs)

        glLinkProgram(program)

        # Cleanup shaders
        glDeleteShader(vs)
        glDeleteShader(fs)
        if tcs: glDeleteShader(tcs)
        if tes: glDeleteShader(tes)
        if gs: glDeleteShader(gs)

        # Check for link errors
        link_ok = Buffer(GL_INT, 1)
        glGetProgramiv(program, GL_LINK_STATUS, link_ok)

        # If not okay, read the error from GL logs and report
        if link_ok[0] != True:
            bufferSize = 1024
            length = Buffer(GL_INT, 1)
            infoLog = Buffer(GL_BYTE, [bufferSize])
            glGetProgramInfoLog(program, bufferSize, length, infoLog)

            err = ''.join(chr(infoLog[i]) for i in range(length[0]))
            raise LinkError(err)

        return program

    def bind(self) -> bool:
        """Bind the shader for use and check if a recompile is necessary.
        Returns:
            bool: False if the shader could not be bound (e.g. due to a failed recompile)
        """
        if self.needs_recompile:
            self.recompile()
            self.needs_recompile = False

        if not self.program:
            return False

        glUseProgram(self.program)
        return True

    def unbind(self):
        """Perform cleanup necessary for this shader"""
        pass


    def getUniformLocation(self, uniform_name):
        if self.uniform_cache.get(uniform_name):
            return self.uniform_cache[uniform_name]

        location = glGetUniformLocation(self.program, uniform_name)
        self.uniform_cache[uniform_name] = location
        return location

    def set_mat3(self, uniform: str, mat):
        location = self.getUniformLocation(uniform)
        if location < 0: return # Skip uniforms that were optimized out for being unused

        mat_buffer = np.reshape(mat, (9, )).tolist()
        mat_buffer = Buffer(GL_FLOAT, 9, mat_buffer)
        glUniformMatrix4fv(location, 1, GL_FALSE, mat_buffer)

    def set_mat4(self, uniform: str, mat):
        location = self.getUniformLocation(uniform)
        if location < 0: return # Skip uniforms that were optimized out for being unused

        mat_buffer = np.reshape(mat, (16, )).tolist()
        mat_buffer = Buffer(GL_FLOAT, 16, mat_buffer)
        glUniformMatrix4fv(location, 1, GL_FALSE, mat_buffer)

    def set_vec3_array(self, uniform: str, arr):
        location = self.getUniformLocation(uniform)
        if location < 0: return

        buffer = Buffer(GL_FLOAT, len(arr), arr)
        glUniform3fv(location, len(arr), buffer)

    def set_vec4_array(self, uniform: str, arr):
        location = self.getUniformLocation(uniform)
        if location < 0: return

        buffer = Buffer(GL_FLOAT, len(arr), arr)
        glUniform4fv(location, len(arr), buffer)

    def set_int(self, uniform: str, value: int):
        location = self.getUniformLocation(uniform)
        if location < 0: return

        glUniform1i(location, value)

    def set_float(self, uniform: str, value: float):
        location = self.getUniformLocation(uniform)
        if location < 0: return

        glUniform1f(location, value)

    def set_vec2(self, uniform: str, value):
        location = self.getUniformLocation(uniform)
        if location < 0: return

        glUniform2f(location, value[0], value[1])

    def set_vec3(self, uniform: str, value):
        location = self.getUniformLocation(uniform)
        if location < 0: return

        glUniform3f(location, value[0], value[1], value[2])

    def set_vec4(self, uniform: str, value):
        location = self.getUniformLocation(uniform)
        if location < 0: return

        glUniform4f(location, value[0], value[1], value[2], value[3])

    def set_vertex_attribute(self, name: str, stride: int):
        """Enable a vertex attrib array and set the pointer for GL_ARRAY_BUFFER reads"""
        location = glGetAttribLocation(self.program, name)
        glEnableVertexAttribArray(location)
        glVertexAttribPointer(location, 3, GL_FLOAT, GL_FALSE, stride, 0)


    def set_tex(self, uniform: str, image):
        location = self.getUniformLocation(uniform)
        if location < 0: return

        glEnable(GL_TEXTURE_2D)

        # matcap = Buffer(GL_BYTE, [32, 32])
        # glGenTextures(1, matcap)
        # glBindTexture(GL_TEXTURE_2D, matcap)
        # glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 32, 32, 0, GL_RGBA, GL_UNSIGNED_BYTE, matcap)

        image.gl_load()
        tex_id = image.bindcode
        glBindTexture(GL_TEXTURE_2D, tex_id)