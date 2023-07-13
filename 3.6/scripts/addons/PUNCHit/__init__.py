bl_info = {
    "name": "PUNCHit",
    "author": "MACHIN3",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "",
    "description": "Manifold Extrude that works.",
    "warning": "",
    "doc_url": "https://machin3.io/PUNCHit/docs",
    "category": "Mesh"}


import bpy
from . utils.registration import get_core, get_ops
from . utils.registration import register_classes, unregister_classes, register_keymaps, unregister_keymaps, register_icons, unregister_icons
from . ui.menus import extrude_menu


def register():
    global classes, keymaps, icons


    core_classlists = get_core()



    ops_classlists, ops_keylists = get_ops()

    classes = register_classes(core_classlists + ops_classlists)



    keymaps = register_keymaps(ops_keylists)



    bpy.types.VIEW3D_MT_edit_mesh_extrude.append(extrude_menu)



    icons = register_icons()



    print("Registered %s %s" % (bl_info["name"], ".".join([str(i) for i in bl_info['version']])))


def unregister():
    global classes, keymaps, icons



    unregister_classes(classes)
    unregister_keymaps(keymaps)

    bpy.types.VIEW3D_MT_edit_mesh_extrude.remove(extrude_menu)



    unregister_icons(icons)

    print("Unregistered %s %s" % (bl_info["name"], ".".join([str(i) for i in bl_info['version']])))
