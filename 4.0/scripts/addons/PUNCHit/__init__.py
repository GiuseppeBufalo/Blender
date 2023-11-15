bl_info = {
    "name": "PUNCHit",
    "author": "MACHIN3",
    "version": (1, 2, 0),
    "blender": (3, 6, 0),
    "location": "",
    "description": "Manifold Extrude that works.",
    "warning": "",
    "doc_url": "https://machin3.io/PUNCHit/docs",
    "category": "Mesh"}


import bpy
from . utils.registration import get_core, get_ops, get_prefs
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



    if get_prefs().registration_debug:
        print("Registered %s %s" % (bl_info["name"], ".".join([str(i) for i in bl_info['version']])))


def unregister():
    global classes, keymaps, icons

    debug = get_prefs().registration_debug



    unregister_classes(classes)
    unregister_keymaps(keymaps)

    bpy.types.VIEW3D_MT_edit_mesh_extrude.remove(extrude_menu)



    unregister_icons(icons)

    if debug:
        print("Unregistered %s %s" % (bl_info["name"], ".".join([str(i) for i in bl_info['version']])))
