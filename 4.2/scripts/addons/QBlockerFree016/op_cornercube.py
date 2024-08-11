from .op_mesh import MeshCreateOperator
from .qobjects.qcornercube import QCornercube
from .draw_module import draw_callback_cube


# box create op new
class CornerCubeCreateOperator(MeshCreateOperator):
    bl_idname = "object.cornercube_create"
    bl_label = "Corner Cube Create Operator"

    drawcallback = draw_callback_cube
    objectType = 1

    # create Qobject tpye
    def CreateQobject(self):
        self.qObject = QCornercube(self)
