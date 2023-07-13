import bpy
from . registration import get_addon


def gp_add_to_edit_mode_group(context, obj):
    return


    grouppro, _, _, _ = get_addon("Group Pro")

    if grouppro and len(context.scene.storedGroupSettings):
        bpy.ops.object.add_to_grouppro()

        obj.select_set(True)
        context.view_layer.objects.active = obj


def gp_get_edit_group(context):
    last = len(context.scene.storedGroupSettings) - 1
    storage = context.scene.storedGroupSettings[last]
    return bpy.data.objects.get(storage.currentEmptyName)
