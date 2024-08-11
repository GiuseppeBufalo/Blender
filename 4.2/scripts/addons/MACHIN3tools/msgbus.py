from . utils import registration as r
from . utils.group import update_group_name

def object_name_change(context):
    active = context.active_object#

    if active:

        if active.M3.is_group_empty and r.get_prefs().group_auto_name:
            update_group_name(active)

def group_color_change(context):
    active = context.active_object

    if active and active.M3.is_group_empty:
        objects = [obj for obj in active.children if obj.M3.is_group_object and not obj.M3.is_group_empty]

        for obj in objects:
            obj.color = active.color
