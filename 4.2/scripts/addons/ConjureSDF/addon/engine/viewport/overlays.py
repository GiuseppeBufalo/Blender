import bpy

from ...util.object import get_csdf_prims


def update_wire_display(self, value):
    wire_draw_enable = self.draw_wire
    
    display_options = ('TEXTURED', 'BOUNDS')
    new_display_type = display_options[int(wire_draw_enable)]

    root = bpy.context.scene.objects.get("CSDF Root")
    if not root:
        return
    
    csdf_scene_nodes = bpy.context.scene.CSDF_SceneNodes

    if not int(wire_draw_enable):
        for node in csdf_scene_nodes:
            node.obj.display_type = 'TEXTURED'

    root_node = csdf_scene_nodes[0]
    update_wire_displace_recursively(csdf_scene_nodes, root_node, new_display_type, False)



def update_wire_displace_recursively(csdf_scene_nodes, node, new_display_type, parent_is_wire):

    if node.obj.csdfData.operation_type in ('Diff', 'Inset', 'Inters') or parent_is_wire:
        node.obj.display_type = new_display_type

        parent_is_wire = True

    if node.childCount:
        child_nodes = [csdf_scene_nodes[childidx.idx] for childidx in node.childIndices]

        for child_node in child_nodes:
            update_wire_displace_recursively(csdf_scene_nodes, child_node, new_display_type, parent_is_wire)
