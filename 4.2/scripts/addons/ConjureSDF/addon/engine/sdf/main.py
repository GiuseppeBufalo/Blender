import threading

from bgl import *

from ..shaders.main import BaseShader

class SDF_ROOT:
    """Minimal representation needed to render a mesh"""
    def __init__(self, name):
        self.name = name
        self.lock = threading.Lock()
        self.VAO = None
        self.VBO = None
        self.EBO = None

        self.is_dirty = True
        self.indices_size = 0

    def rebuild(self, obj):
        """Not sure yet what to do here"""

        with self.lock:

            # Let the render thread know it can copy new buffer data to the GPU
            self.is_dirty = True


    def rebuild_vbos(self, shader: BaseShader):

       if not self.VAO:
            VAO = Buffer(GL_INT, 1)
            glGenVertexArrays(1, VAO)
            self.VAO = VAO[0]

       self.is_dirty = True

    def draw(self, shader: BaseShader):
        if self.is_dirty:
            with self.lock:
                self.rebuild_vbos(shader)
                self.is_dirty = False

        glBindVertexArray(self.VAO)

        glDrawArrays(GL_TRIANGLES, 0, 6)

        glBindVertexArray(0)
