bl_info = {
    "name": "QuickTexture 2024",
    "author": "Jama Jurabaev and ALKSNDR",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "location": "See Sidebar ('N' Panel) for Hotkeys",
    "description": "Sketching in 3D for Concept Artists",
    "wiki_url": "http://www.alksndr.com/quicktools",
    "tracker_url": "http://www.alksndr.com/quicktools",
    "category": "Mesh",
}

import bpy
from bpy.utils import register_class, unregister_class
import addon_utils
from .operators import (
    MyPropertiesQT,
    QT_PT_panel,
    quickTexture,
    quickDecal,
    draw_quickTexture,
    QT_OT_material_qt,
    QT_OT_boxlayer_qt,
    QT_OT_texturemask_qt,
    QT_OT_heightmask_qt,
    QT_OT_depthmask_qt,
    QT_OT_viewlayer_qt,
    QT_OT_vertexmask_qt,
    QT_OT_cavitymask_qt,
    QT_OT_aomask_qt,
    QT_OT_replacemaps_qt,
    QT_OT_smudge_qt,
    QT_OT_replacealpha_qt,
    QT_OT_normalmask_qt,
    QT_OT_copymats,
    QT_OT_makeunique,
    QT_OT_decal_qt,
    VIEW3D_MT_QT_PIE1,
    VIEW3D_MT_QT_PIE,
    VIEW3D_OT_PIE_QT_PIE_call,
    BakeFileSelector,
    bakeTextures,
    previewTextures,
    bakePreviewTextures,
    quicktexture_uv,
    quicktexture_view,
    quicktexture_box,
    photomodelingplane,
    photomodelingbox,
    photomodelingapply,
)
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    FloatVectorProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup
import rna_keymap_ui
import addon_utils


class quickTexturePrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    window_buffer: FloatProperty(
        name="Window Buffer Size",
        description="Window Buffer Size",
        default=0.001,
        min=0.001,
        max=20,
    )

    col_primary: FloatVectorProperty(
        name="Primary Color",
        subtype="COLOR",
        description="Primary Color",
        size=4,
        default=(1.0, 1.0, 1.0, 1.0),
    )

    col_accent: FloatVectorProperty(
        name="Accent Color",
        subtype="COLOR",
        description="Accent Color",
        size=4,
        default=(0.1, 0.9, 0.9, 1.0),
    )

    text_size: IntProperty(
        name="Text Size", description="Text Size", default=15, min=6, max=20
    )

    alt_nav: BoolProperty(
        name="Alt Navigation", description="Alt Navigation", default=0
    )

    mouse_mult: FloatProperty(
        name="Mouse Speed Multiplier",
        description="Mouse Speed Multiplier",
        default=1,
        min=0.1,
        max=10,
    )

    def draw(self, context):
        layout = self.layout
        wm = bpy.context.window_manager

        # settings
        box = layout.box()
        row = box.row()
        row.label(text="Settings:")

        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "window_buffer")
        row.prop(bpy.context.preferences.addons[__name__].preferences, "text_size")
        row.prop(bpy.context.preferences.addons[__name__].preferences, "mouse_mult")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "col_primary")
        row.prop(bpy.context.preferences.addons[__name__].preferences, "col_accent")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "alt_nav")


keys = {
    "MENU": [
        {
            "label": "QuickTexture",
            "keymap": "Object Mode",
            "idname": "object.quicktexture",
            "type": "T",
            "ctrl": True,
            "alt": False,
            "shift": False,
            "value": "PRESS",
        },
        {
            "label": "QuickTexture",
            "keymap": "Mesh",
            "idname": "object.quicktexture",
            "type": "T",
            "ctrl": True,
            "alt": False,
            "shift": False,
            "value": "PRESS",
        },
        {
            "label": "QuickDecal",
            "keymap": "Object Mode",
            "idname": "object.quickdecal",
            "type": "D",
            "ctrl": True,
            "alt": False,
            "shift": True,
            "value": "PRESS",
        },
    ]
}


def get_keys():
    keylists = []

    success = addon_utils.check('QuickDeform')
    if not success[0]:
        pie = {
            "label": "QuickTexture Pie",
            "keymap": "Object Mode",
            "idname": "object.quicktexturepie",
            "type": "Q",
            "ctrl": False,
            "alt": True,
            "shift": False,
            "value": "PRESS",
        }
        keys["MENU"].append(pie)

    keylists.append(keys["MENU"])

    return keylists


def register_keymaps(keylists):
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    keymaps = []

    for keylist in keylists:
        for item in keylist:
            keymap = item.get("keymap")
            space_type = item.get("space_type", "EMPTY")

            if keymap:
                km = kc.keymaps.new(name=keymap, space_type=space_type)

                if km:
                    idname = item.get("idname")
                    type = item.get("type")
                    value = item.get("value")

                    shift = item.get("shift", False)
                    ctrl = item.get("ctrl", False)
                    alt = item.get("alt", False)

                    kmi = km.keymap_items.new(
                        idname, type, value, shift=shift, ctrl=ctrl, alt=alt
                    )

                    if kmi:
                        properties = item.get("properties")

                        if properties:
                            for name, value in properties:
                                setattr(kmi.properties, name, value)

                        keymaps.append((km, kmi))
    return keymaps


def unregister_keymaps(keymaps):
    for km, kmi in keymaps:
        km.keymap_items.remove(kmi)


classes = (
    quickTexturePrefs,
    MyPropertiesQT,
    QT_PT_panel,
    quickTexture,
    quickDecal,
    QT_OT_material_qt,
    QT_OT_boxlayer_qt,
    QT_OT_texturemask_qt,
    QT_OT_cavitymask_qt,
    QT_OT_aomask_qt,
    QT_OT_heightmask_qt,
    QT_OT_depthmask_qt,
    QT_OT_viewlayer_qt,
    QT_OT_replacemaps_qt,
    QT_OT_replacealpha_qt,
    QT_OT_normalmask_qt,
    QT_OT_vertexmask_qt,
    QT_OT_smudge_qt,
    QT_OT_copymats,
    QT_OT_makeunique,
    QT_OT_decal_qt,
    VIEW3D_MT_QT_PIE1,
    VIEW3D_MT_QT_PIE,
    VIEW3D_OT_PIE_QT_PIE_call,
    BakeFileSelector,
    bakeTextures,
    previewTextures,
    bakePreviewTextures,
    quicktexture_uv,
    quicktexture_view,
    quicktexture_box,
    photomodelingplane,
    photomodelingbox,
    photomodelingapply,
)


def register():
    global keymaps
    keys = get_keys()
    keymaps = register_keymaps(keys)

    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.my_toolqt = bpy.props.PointerProperty(type=MyPropertiesQT)


def unregister():
    global keymaps
    for km, kmi in keymaps:
        km.keymap_items.remove(kmi)

    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.WindowManager.my_toolqt
