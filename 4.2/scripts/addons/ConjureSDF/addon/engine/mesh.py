import threading

from bgl import *

from .settings import GL_PATCHES

from .shaders.main import BaseShader

class Mesh:
    """Minimal representation needed to render a mesh"""
    def __init__(self, name):
        self.name = name
        self.lock = threading.Lock()
        self.VAO = None
        self.VBO = None
        self.EBO = None

        self.is_dirty = False
        self.indices_size = 0

    def rebuild(self, eval_obj):
        """Copy evaluated mesh data into buffers for updating the VBOs on the render thread"""

        with self.lock:
            # We use the evaluated mesh after all modifies are applied.
            # This is a temporary mesh that we can't safely hold a reference
            # to within the render thread - so we copy from it here and now.
            mesh = eval_obj.to_mesh()

            # Refresh triangles on the mesh
            # TODO: Is this necessary with the eval mesh?
            mesh.calc_loop_triangles()
            mesh.calc_normals_split()

            self._cvertices = []
            self._cnormals = []
            self._cindices = []

            # TODO : possibly can be optimized using foreach_get
            # could probably do something like:
            # self._vertices = [0]*len(mesh.vertices) * 3
            # mesh.vertices.foreach_get('co', self._vertices)
            
            for idx, loop_triangle in enumerate(mesh.loop_triangles):
                self._cvertices += mesh.vertices[loop_triangle.vertices[0]].co[:]
                self._cvertices += mesh.vertices[loop_triangle.vertices[1]].co[:]
                self._cvertices += mesh.vertices[loop_triangle.vertices[2]].co[:]

                self._cnormals += loop_triangle.split_normals[0][:]
                self._cnormals += loop_triangle.split_normals[1][:]
                self._cnormals += loop_triangle.split_normals[2][:]

                self._cindices.append(idx*3)
                self._cindices.append(idx*3+1)
                self._cindices.append(idx*3+2)


            # Fast copy vertex data / triangle indices from the mesh into buffers
            # Reference: https://blog.michelanders.nl/2016/02/copying-vertices-to-numpy-arrays-in_4.html
            self.vertices = Buffer(GL_FLOAT, len(self._cvertices), self._cvertices)
            self.normals = Buffer(GL_FLOAT, len(self._cnormals), self._cnormals)
            self.indices = Buffer(GL_INT, len(self._cindices), self._cindices)

            eval_obj.to_mesh_clear()

            # Let the render thread know it can copy new buffer data to the GPU
            self.is_dirty = True

    def rebuild_vbos(self, shader: BaseShader):
        """Upload new vertex buffer data to the GPU
        This method needs to be called within the render thread
        to safely access the RenderEngine's current GL context
        Args:
            shader (BaseShader): Shader to set attribute positions in
        """

        # Make sure our VAO/VBOs are ready
        if not self.VAO:
            VAO = Buffer(GL_INT, 1)
            glGenVertexArrays(1, VAO)
            self.VAO = VAO[0]

        if not self.VBO:
            VBO = Buffer(GL_INT, 2)
            glGenBuffers(2, VBO)
            self.VBO = VBO

        if not self.EBO:
            EBO = Buffer(GL_INT, 1)
            glGenBuffers(1, EBO)
            self.EBO = EBO[0]

        # Bind the VAO so we can upload new buffers
        glBindVertexArray(self.VAO)

        # TODO: Use glBufferSubData to avoid recreating the store with glBufferData.
        # This would require tracking previous buffer size as well to determine if
        # we need to rebuild a new one during resizes.

        # Copy verts
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO[0])
        glBufferData(GL_ARRAY_BUFFER, len(self.vertices) * 4, self.vertices, GL_DYNAMIC_DRAW) # GL_STATIC_DRAW - for inactive mesh
        shader.set_vertex_attribute('Position', 0)

        # Copy normals
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO[1])
        glBufferData(GL_ARRAY_BUFFER, len(self.normals) * 4, self.normals, GL_DYNAMIC_DRAW)
        shader.set_vertex_attribute('Normal', 0)

        # TODO: set_vertex_attribute calls don't really make sense here - because we're
        # not rebuilding a mesh on a shader reload - so those attributes are never bound
        # on the new program?

        # TODO: Tangent, Binormal, Color, Texcoord0-7
        # TODO: Probably don't do per-mesh VAO. See: https://stackoverflow.com/a/18487155

        # Copy indices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(self.indices) * 4, self.indices, GL_DYNAMIC_DRAW)

        # Cleanup, just so bad code elsewhere doesn't also write to this VAO
        glBindVertexArray(0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        self.indices_size = len(self.indices)

    def update(self, obj):
        """Update transformation info for this mesh"""
        self.model_matrix = obj.matrix_world

    def draw(self, shader: BaseShader):
        if self.is_dirty:
            with self.lock:
                self.rebuild_vbos(shader)
                self.is_dirty = False

        # print('draw VAO={} valid={}, VBO[0]={} valid={}, VBO[1]={} valid={}, EBO={} valid={}'.format(
        #     self.VAO,
        #     glIsBuffer(self.VAO),
        #     self.VBO[0],
        #     glIsBuffer(self.VBO[0]),
        #     self.VBO[1],
        #     glIsBuffer(self.VBO[1]),
        #     self.EBO,
        #     glIsBuffer(self.EBO),
        # ))

        glBindVertexArray(self.VAO)

        # If the shader includes a tessellation stage, we need to draw in patch mode
        if shader.has_tessellation:
            # glPatchParameteri(GL_PATCH_VERTICES, 3)
            # Not supported in bgi - but defaults to 3.
            glDrawElements(GL_PATCHES, self.indices_size, GL_UNSIGNED_INT, 0)
        else:
            glDrawElements(GL_TRIANGLES, self.indices_size, GL_UNSIGNED_INT, 0)

        glBindVertexArray(0)
