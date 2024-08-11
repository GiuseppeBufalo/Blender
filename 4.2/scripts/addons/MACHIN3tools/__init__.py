bl_info = {
    "name": "MACHIN3tools",
    "author": "MACHIN3, TitusLVR",
    "version": (1, 10, 1),
    "blender": (3, 6, 0),
    "location": "Everywhere",
    "revision": "5b8dc3488f6e6417e5c0fe30775a0e34aa12e5e3",
    "description": "Streamlining Blender 3.6+.",
    "warning": "",
    "doc_url": "https://machin3.io/MACHIN3tools/docs",
    "category": "3D View"}

def reload_modules(name):
    import os
    import importlib

    dbg = False

    from . import registration, items, colors

    for module in [registration, items, colors]:
        importlib.reload(module)

    utils_modules = sorted([name[:-3] for name in os.listdir(os.path.join(__path__[0], "utils")) if name.endswith('.py')])

    for module in utils_modules:
        impline = f"from . utils import {module}"

        if dbg:
            print(f"reloading {name}.utils.{module}")

        exec(impline)
        importlib.reload(eval(module))

    from . import handlers
    
    if dbg:
        print("reloading", handlers.__name__)

    importlib.reload(handlers)

    modules = []

    for label in registration.classes:
        entries = registration.classes[label]
        for entry in entries:
            path = entry[0].split('.')
            module = path.pop(-1)

            if (path, module) not in modules:
                modules.append((path, module))

    for path, module in modules:
        if path:
            impline = f"from . {'.'.join(path)} import {module}"
        else:
            impline = f"from . import {module}"

        if dbg:
            print(f"reloading {name}.{'.'.join(path)}.{module}")

        exec(impline)
        importlib.reload(eval(module))

if 'bpy' in locals():
    reload_modules(bl_info['name'])

import bpy
from bpy.props import PointerProperty, BoolProperty, EnumProperty
from . properties import M3SceneProperties, M3ObjectProperties, M3CollectionProperties
from . utils.registration import get_core, get_prefs, get_tools, get_pie_menus
from . utils.registration import register_classes, unregister_classes, register_keymaps, unregister_keymaps, register_icons, unregister_icons, register_msgbus, unregister_msgbus
from . utils.system import verify_update, install_update
from . ui.menus import asset_browser_bookmark_buttons, asset_browser_metadata, object_context_menu, mesh_context_menu, add_object_buttons, material_pick_button, outliner_group_toggles, extrude_menu, group_origin_adjustment_toggle, render_menu, render_buttons, asset_browser_update_thumbnail
from . handlers import load_post, undo_pre, depsgraph_update_post, render_start, render_end

def register():
    global classes, keymaps, icons, owner

    core_classes = register_classes(get_core())

    bpy.types.Scene.M3 = PointerProperty(type=M3SceneProperties)
    bpy.types.Object.M3 = PointerProperty(type=M3ObjectProperties)
    bpy.types.Collection.M3 = PointerProperty(type=M3CollectionProperties)

    bpy.types.WindowManager.M3_screen_cast = BoolProperty()
    bpy.types.WindowManager.M3_asset_catalogs = EnumProperty(items=[])

    tool_classlists, tool_keylists, tool_count = get_tools()
    pie_classlists, pie_keylists, pie_count = get_pie_menus()

    classes = register_classes(tool_classlists + pie_classlists) + core_classes
    keymaps = register_keymaps(tool_keylists + pie_keylists)

    bpy.types.VIEW3D_MT_object_context_menu.prepend(object_context_menu)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(mesh_context_menu)

    bpy.types.VIEW3D_MT_edit_mesh_extrude.append(extrude_menu)
    bpy.types.VIEW3D_MT_mesh_add.prepend(add_object_buttons)
    bpy.types.VIEW3D_MT_editor_menus.append(material_pick_button)

    bpy.types.OUTLINER_HT_header.prepend(outliner_group_toggles)

    bpy.types.ASSETBROWSER_MT_editor_menus.append(asset_browser_bookmark_buttons)
    bpy.types.ASSETBROWSER_PT_metadata.prepend(asset_browser_metadata)
    bpy.types.ASSETBROWSER_PT_metadata_preview.append(asset_browser_update_thumbnail)

    bpy.types.VIEW3D_PT_tools_object_options_transform.append(group_origin_adjustment_toggle)

    bpy.types.TOPBAR_MT_render.append(render_menu)
    bpy.types.DATA_PT_context_light.prepend(render_buttons)

    icons = register_icons()

    owner = object()
    register_msgbus(owner)

    bpy.app.handlers.load_post.append(load_post)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post)

    bpy.app.handlers.render_init.append(render_start)
    bpy.app.handlers.render_cancel.append(render_end)
    bpy.app.handlers.render_complete.append(render_end)

    bpy.app.handlers.undo_pre.append(undo_pre)

    if get_prefs().registration_debug:
        print(f"Registered {bl_info['name']} {'.'.join([str(i) for i in bl_info['version']])} with {tool_count} {'tool' if tool_count == 1 else 'tools'}, {pie_count} pie {'menu' if pie_count == 1 else 'menus'}")

    verify_update()

def unregister():
    global classes, keymaps, icons, owner

    debug = get_prefs().registration_debug

    bpy.app.handlers.load_post.remove(load_post)

    from . handlers import axesHUD, focusHUD, surfaceslideHUD, screencastHUD

    if axesHUD and "RNA_HANDLE_REMOVED" not in str(axesHUD):
        bpy.types.SpaceView3D.draw_handler_remove(axesHUD, 'WINDOW')

    if focusHUD and "RNA_HANDLE_REMOVED" not in str(focusHUD):
        bpy.types.SpaceView3D.draw_handler_remove(focusHUD, 'WINDOW')

    if surfaceslideHUD and "RNA_HANDLE_REMOVED" not in str(surfaceslideHUD):
        bpy.types.SpaceView3D.draw_handler_remove(surfaceslideHUD, 'WINDOW')

    if screencastHUD and "RNA_HANDLE_REMOVED" not in str(screencastHUD):
        bpy.types.SpaceView3D.draw_handler_remove(screencastHUD, 'WINDOW')

    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post)

    bpy.app.handlers.render_init.remove(render_start)
    bpy.app.handlers.render_cancel.remove(render_end)
    bpy.app.handlers.render_complete.remove(render_end)

    bpy.app.handlers.undo_pre.remove(undo_pre)

    unregister_msgbus(owner)

    bpy.types.VIEW3D_MT_object_context_menu.remove(object_context_menu)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(mesh_context_menu)

    bpy.types.VIEW3D_MT_edit_mesh_extrude.remove(extrude_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_buttons)
    bpy.types.VIEW3D_MT_editor_menus.remove(material_pick_button)

    bpy.types.OUTLINER_HT_header.remove(outliner_group_toggles)

    bpy.types.ASSETBROWSER_MT_editor_menus.remove(asset_browser_bookmark_buttons)
    bpy.types.ASSETBROWSER_PT_metadata.remove(asset_browser_metadata)
    bpy.types.ASSETBROWSER_PT_metadata_preview.remove(asset_browser_update_thumbnail)

    bpy.types.VIEW3D_PT_tools_object_options_transform.remove(group_origin_adjustment_toggle)

    bpy.types.TOPBAR_MT_render.remove(render_menu)
    bpy.types.DATA_PT_context_light.remove(render_buttons)

    unregister_keymaps(keymaps)
    unregister_classes(classes)

    del bpy.types.Scene.M3
    del bpy.types.Object.M3
    del bpy.types.Collection.M3

    del bpy.types.WindowManager.M3_screen_cast
    del bpy.types.WindowManager.M3_asset_catalogs

    unregister_icons(icons)

    if debug:
        print(f"Unregistered {bl_info['name']} {'.'.join([str(i) for i in bl_info['version']])}.")

    install_update()
