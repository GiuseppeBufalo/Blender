import bpy


def get_selected_active(ctx):
    """
    Gets true Object selection. As an empty selection can still have an active object
    """
    if not ctx.selected_objects:
        return None
    if ctx.active_object in ctx.selected_objects:
        return ctx.active_object
    


def get_active_and_selected(context) -> tuple[bpy.types.Object, list[bpy.types.Object]]:
    """
    Returns the active object, and the remaining selected objects

    active (object): active selected object
    selected_list (object): the selected objects, excluding the active object
    """

    # context.selected_objects does NOT return a list in the order that you selected them

    active = context.active_object

    selected_list = context.selected_objects
    if active.select_get() == True:
        selected_list.remove(active)
    else:
        active = None

    return active, selected_list



def get_csdf_prims(scene):

    csdf_scene_nodes = scene.CSDF_SceneNodes
    prims = [node.obj for node in csdf_scene_nodes if node.obj.csdfData.show_viewport]

    return prims
