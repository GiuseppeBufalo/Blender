import bpy
from typing import Tuple, Union
from mathutils import Matrix, Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_origin_3d, region_2d_to_vector_3d

def get_shading_type(context):
    return context.space_data.shading.type

def set_xray(context):
    x = (context.scene.M3.pass_through, context.scene.M3.show_edit_mesh_wire)
    shading = context.space_data.shading

    shading.show_xray = True if any(x) else False

    if context.scene.M3.show_edit_mesh_wire:
        shading.xray_alpha = 0.1

    elif context.scene.M3.pass_through:
        shading.xray_alpha = 1 if context.active_object and context.active_object.type == "MESH" else 0.5

def reset_xray(context):
    shading = context.space_data.shading

    shading.show_xray = False
    shading.xray_alpha = 0.5

def update_local_view(space_data, states):
    if space_data.local_view:
        for obj, local in states:
            if obj:
                obj.local_view_set(space_data, local)

def reset_viewport(context, disable_toolbar=False):
    for screen in context.workspace.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        r3d = space.region_3d

                        r3d.view_distance = 10
                        r3d.view_matrix = Matrix(((1, 0, 0, 0),
                                                  (0, 0.2, 1, -1),
                                                  (0, -1, 0.2, -10),
                                                  (0, 0, 0, 1)))

                        if disable_toolbar:
                            space.show_region_toolbar = False

def sync_light_visibility(scene):

    for view_layer in scene.view_layers:
        lights = [obj for obj in view_layer.objects if obj.type == 'LIGHT']

        for light in lights:
            hidden = light.hide_get(view_layer=view_layer)

            if light.hide_render != hidden:
                light.hide_render = hidden

def get_loc_2d(context, loc):
    loc_2d = location_3d_to_region_2d(context.region, context.region_data, loc)
    return loc_2d if loc_2d else Vector((-1000, -1000))

def get_view_origin_and_dir(context, coord=None) -> Tuple[Vector, Vector]:
    if not coord:
        coord = Vector((context.region.width / 2, context.region.height / 2))

    view_origin = region_2d_to_origin_3d(context.region, context.region_data, coord)
    view_dir = region_2d_to_vector_3d(context.region, context.region_data, coord)

    return view_origin, view_dir

def is_on_viewlayer(obj):
    return obj.name in bpy.context.view_layer.objects

def ensure_visibility(context, obj: Union[bpy.types.Object, list[bpy.types.Object]], view_layer=True, local_view=True, unhide=True, unhide_viewport=True, select=False):
    view = context.space_data

    objects = obj if type(obj) in [list, set] else [obj]

    if view_layer:
        for obj in objects:
            if not is_on_viewlayer(obj):
                context.scene.collection.objects.link(obj)
                obj.select_set(False)  # it's automatically selected when being linked, but if we actually want this, we'll do it intentionally

    if local_view:
        if view.local_view:
            for obj in objects:
                obj.local_view_set(view, True)

    if unhide:
        for obj in objects:
            if not obj.visible_get():
                obj.hide_set(False)

    if unhide_viewport:
        for obj in objects:
            if obj.hide_viewport:
                obj.hide_viewport = False

    if select:
        for obj in objects:
            obj.select_set(True)

def get_location_2d(context, co3d, default=(0, 0), debug=False):
    if default == 'OFF_SCREEN':
        default = Vector((-1000, -1000))
    co2d = Vector(round(i) for i in location_3d_to_region_2d(context.region, context.region_data, co3d, default=default))
    if debug:
        print(tuple(co3d), "is", tuple(co2d))

    return co2d

def get_view_bbox(context, bbox, margin=0, border_gap=0, debug=False):
    from . ui import get_scale

    scale = get_scale(context)
    gap = border_gap * scale

    coords = []

    for co in bbox:
        coords.append(get_location_2d(context, co, default=Vector((context.region.width / 2, context.region.height / 2))))
    xmin = round(min(context.region.width - gap, max(gap, min(coords, key=lambda x: x[0])[0] - margin)))
    xmax = round(min(context.region.width - gap, max(gap, max(coords, key=lambda x: x[0])[0] + margin)))

    ymin = round(min(context.region.height - gap, max(gap, min(coords, key=lambda x: x[1])[1] - margin)))
    ymax = round(min(context.region.height - gap, max(gap, max(coords, key=lambda x: x[1])[1] + margin)))

    bbox = [Vector((xmin, ymin)), Vector((xmax, ymin)), Vector((xmax, ymax)), Vector((xmin, ymax))]

    if debug:
        print(bbox)

        from . draw import draw_line

        line_coords = [co.resized(3) for co in bbox + [bbox[0]]]
        draw_line(line_coords, screen=True, modal=False)

    return bbox
