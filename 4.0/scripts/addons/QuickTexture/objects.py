import bpy
import math
import mathutils
import os
from bpy_extras import view3d_utils

def create_empty(empty_name, empty_type, rotate, context, only_once):
    bpy.ops.object.select_all(action="DESELECT")
    found = empty_name in bpy.data.objects
    if found == 0 or only_once == 0:
        obj = bpy.ops.object.empty_add(
            type=empty_type, location=(0, 0, 0), rotation=rotate
        )
        obj = context.object
        context.view_layer.objects.active = obj
        obj.name = empty_name
        bpy.ops.object.select_all(action="DESELECT")
        context.object.hide_viewport = True
        context.object.hide_render = True
        context.object.hide_select = True
        return obj
    else:
        obj = bpy.data.objects[empty_name]
        return obj

def empty(empty_name, empty_type, location, rotate, context, only_once):

    bpy.ops.object.select_all(action="DESELECT")
    found = empty_name in bpy.data.objects
    if found == 0 or only_once == 0:
        obj = bpy.ops.object.empty_add(
            type=empty_type, location=location, rotation=rotate
        )
        obj = context.object
        context.view_layer.objects.active = obj
        obj.name = empty_name
        context.object.hide_viewport = True
        context.object.hide_render = True
        context.object.hide_select = True
        bpy.ops.object.select_all(action="DESELECT")
        return obj
    else:
        obj = bpy.data.objects[empty_name]
        return obj

def add_empty(empty_name, empty_type, location, rotate, context):
    bpy.ops.object.select_all(action="DESELECT")
    obj = bpy.ops.object.empty_add(type=empty_type, location=location, rotation=rotate)
    obj = context.object
    context.view_layer.objects.active = obj
    obj.name = empty_name
    context.object.hide_viewport = True
    context.object.hide_render = True
    context.object.hide_select = True
    bpy.ops.object.select_all(action="DESELECT")
    return obj

def make_collection(name, context):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    else:
        new_collection = bpy.data.collections.new(name)
        context.scene.collection.children.link(new_collection)
        return new_collection

def add_to_collection(name, collection, context):
    if name not in collection.objects:
        ob_cm = bpy.data.objects[name]
        col2 = context.scene.collection.children[collection.name]
        for col in ob_cm.users_collection:
            col.objects.unlink(ob_cm)
        col2.objects.link(ob_cm)

def create_image_plane(self, context, name, img_spec):
    bpy.ops.mesh.primitive_plane_add("INVOKE_REGION_WIN")
    plane = context.active_object
    if plane.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    px, py = img_spec.size
    size = px / py
    width = 1 * size
    height = 1
    plane.dimensions = width, height, 0.0
    plane.data.name = plane.name = name
    plane.rotation_euler.x = math.pi / 2
    return plane

def create_decal(self, context, sel, img_spec):

    if len(sel) > 0:
        bpy.ops.mesh.primitive_plane_add("INVOKE_REGION_WIN", align="VIEW")
    else:
        bpy.ops.mesh.primitive_plane_add("INVOKE_REGION_WIN")

    # Create new mesh
    plane = context.active_object
    plane.name = 'QT_Decal'

    px, py = img_spec.size
    size = px / py

    width = 1 * size
    height = 1

    plane.dimensions = width, height, 0.0

    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=10)
    bpy.ops.object.editmode_toggle()

    if len(sel) > 0:
        col = sel[0].users_collection[0]
        add_to_collection(plane.name, col, context)

    bpy.ops.object.shade_smooth()
    return plane

def create_paintover(cam, depth):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_plane_add()
    bpy.ops.object.mode_set(mode="OBJECT")
    plane = bpy.context.active_object
    plane.name = "QT_Paintover"

    if "QuickTexture" in bpy.data.collections:
        collection = bpy.data.collections["QuickTexture"]
        bpy.data.collections["QuickTexture"].hide_viewport = False
        bpy.data.collections["QuickTexture"].hide_render = False
    else:
        collection = make_collection("QuickTexture", bpy.context)

    collections = bpy.context.view_layer.layer_collection.children
    for collection in collections:
        if collection.name == "QuickTexture":
            if collection.hide_viewport:
                collection.hide_viewport = False

    plane.parent = cam
    plane.location = (0, 0, -depth)
    cA = cam.data.angle
    cT = cam.data.type
    cOS = cam.data.ortho_scale
    r_x = bpy.context.scene.render.resolution_x
    r_y = bpy.context.scene.render.resolution_y
    p_x = bpy.context.scene.render.pixel_aspect_x
    p_y = bpy.context.scene.render.pixel_aspect_y

    scales = [0.0, 0.0]
    for i in range(2):
        if cT == 'PERSP':
            scale_exp = -depth * math.tan(cA / 2)
            aspect_ratio = (r_y * p_y) / (r_x * p_x) if i == 1 else (r_x * p_x) / (r_y * p_y)
            scale = scale_exp * aspect_ratio if aspect_ratio < 1 else scale_exp
        else:
            scale_exp = cOS / 2
            aspect_ratio = (r_y * p_y) / (r_x * p_x) if i == 1 else (r_x * p_x) / (r_y * p_y)
            scale = scale_exp * aspect_ratio if aspect_ratio < 1 else scale_exp
        scales[i] = scale

    scale_x = abs(scales[0])
    scale_y = abs(scales[1])

    plane.scale.x = scale_x * bpy.context.window_manager.my_toolqt.overscan
    plane.scale.y = scale_y * bpy.context.window_manager.my_toolqt.overscan

    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=10)
    bpy.ops.mesh.subdivide(number_cuts=3)
    bpy.ops.object.editmode_toggle()

    bpy.ops.object.shade_smooth()
    return plane