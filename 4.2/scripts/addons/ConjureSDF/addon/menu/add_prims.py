import bpy

from ..resources import iconloader

def draw_addprims(layout):
    op = layout.operator(operator="mesh.csdf_addroot", icon='EMPTY_AXIS', text='CSDF Root')

    layout.separator()

    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Box'), text='Cube SDF')
    op.prim = 'Box'
    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Sphere'), text='Sphere SDF')
    op.prim = 'Sphere'
    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Ellipsoid'), text='Ellipsoid SDF')
    op.prim = 'Ellipsoid'

    layout.separator()

    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Cylinder'), text='Cylinder SDF')
    op.prim = 'Cylinder'
    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_LongCylinder'), text='Elongated Cylinder SDF')
    op.prim = 'LongCylinder'

    layout.separator()

    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_CapCone'), text='Capped Cone SDF')
    op.prim = 'CapCone'
    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_BiCapsule'), text='BiCapsule SDF')
    op.prim = 'BiCapsule'
    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Capsule'), text='Capsule SDF')
    op.prim = 'Capsule'
    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Coin'), text='Coin SDF')
    op.prim = 'Coin'

    layout.separator()

    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Link'), text='Link SDF')
    op.prim = 'Link'
    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Torus'), text='Torus SDF')
    op.prim = 'Torus'
    op = layout.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_HexPrism'), text='Hexagon SDF')
    op.prim = 'HexPrism'


class CSDF_MT_AddMenu(bpy.types.Menu):
    bl_label = "CSDF Primitives"
    bl_idname = "OBJECT_MT_CSDF_Primitives_menu"

    def draw(self, context):
        layout = self.layout
        draw_addprims(layout)


def draw_CSDF_addMenu(self, context):
    layout = self.layout
    layout.menu(CSDF_MT_AddMenu.bl_idname)


class CSDF_PT_AddMenu(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_context = ".objectmode" 

    bl_label = "ConjureSDF"

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        layout.label(text="Add Primitives")

        draw_addprims(layout)
