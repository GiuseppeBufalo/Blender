import bpy
from bpy.utils import register_class, unregister_class
from QuickTexture import operators
from bpy.props import (
    FloatProperty,
    IntProperty,
    FloatVectorProperty,
    EnumProperty,
    StringProperty,
    BoolProperty
)

bl_info = {
    "name": "QuickTexture 2024",
    "author": "Jama Jurabaev and ALKSNDR",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "See Sidebar ('N' Panel) for Hotkeys",
    "description": "Sketching in 3D for Concept Artists",
    "wiki_url": "http://www.alksndr.com/quicktools",
    "tracker_url": "http://www.alksndr.com/quicktools",
    "category": "Mesh",
}

class quickTexturePrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    viewport_drawing_border: FloatProperty(
        name="Viewport Drawing Border",
        description="Control the amount of acceptable drawing area in the viewport",
        default=0.001,
        min=0.001,
        max=200,
    )
    col_primary: FloatVectorProperty(
        name="Primary Color",
        subtype="COLOR",
        description="Primary Color",
        size=4,
        default=(1.0, 1.0, 1.0, 1.0),
    )
    col_secondary: FloatVectorProperty(
        name="Secondary Color",
        subtype="COLOR",
        description="Secondary Color",
        size=4,
        default=(0.1, 0.9, 0.9, 1.0),
    )
    col_tertiary: FloatVectorProperty(
        name="Tertiary Color",
        subtype="COLOR",
        description="Tertiary Color",
        size=4,
        default=(0.8, 0.8, 0.8, 1.0),
    )
    text_size: IntProperty(
        name="Text Size", description="Text Size", default=15, min=6, max=20
    )
    mouse_mult: FloatProperty(
        name="Mouse Speed Multiplier",
        description="Mouse Speed Multiplier",
        default=1,
        min=0.1,
        max=10,
    )
    diffuse: StringProperty(
        name="Diffuse", 
        description="Diffuse", 
        default='diffuse diff albedo color col basecolor basecol'
    )
    roughness: StringProperty(
        name="Roughness", 
        description="Roughness", 
        default='roughness rough glossiness gloss spec specular'
    )
    normal: StringProperty(
        name="Normal", 
        description="Normal", 
        default='normal norm nor nrm nmap'
    )
    opacity: StringProperty(
        name="Opacity", 
        description="Opacity", 
        default='opacity opac alpha transparency'
    )
    ao: StringProperty(
        name="AO", 
        description="AO", 
        default='ao ambient ambientocclusion ambient_occlusion occlusion'
    )
    displacement: StringProperty(
        name="Displacement", 
        description="Displacement", 
        default='displacement disp dis height heightmap'
    )
    metal: StringProperty(
        name="Metal", 
        description="Metal", 
        default='metal metalness metallic'
    )
    
    uv_mode: EnumProperty(
        items = [
            ('UV','UV','','',0), 
            ('Triplanar','Triplanar','','',1),
            ('View','View','','',2),
            ('Procedural Box','Procedural Box','','',3),
        ],
        name = "UV Mode",
        default = 'Procedural Box')

    res: IntProperty(
        name="Decal Resolution",
        description="Decal Resolution",
        default=1,
        min=0,
        max=10,
    )
    offset: FloatProperty(
        name="Decal Offset",
        description="Decal Offset",
        default=0.01,
        min=0.0001,
        max=10,
    )
    paintover_res: IntProperty(
        name="Paintover Resolution",
        description="Paintover Resolution",
        default=4,
        min=1,
        max=10,
    )
    paintover_offset: FloatProperty(
        name="Paintover Offset",
        description="Paintover Offset",
        default=0.003,
        min=0.0001,
        max=10,
    )
    path: StringProperty(
        name="Image Editor Path", 
        description="Full Path to your Image Editor .EXE", 
        default=''
    )
    paintover: IntProperty(
        name="Paintover Resolution",
        description="Paintover Resolution is a Multiplier on your current Viewport Size",
        default=2,
        min=1,
        max=4,
    )
    overscan: FloatProperty(
        name="Paintover Overscan",
        description="Adjust this value if your object is not being entirely covered by the Paintover",
        default=1.1,
        min=1,
        max=2,
    )
    multilayer: BoolProperty(name="Multilayer", description="Create Multilayer QuickTexture with automatic Dirt and Edges Masks", default=False)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text="Close QuickTexture while editing preferences")
        row = box.row()
        row.label(text="To customize QuickTexture hotkeys, visit the Keymap section of Blender preferences and search for QuickTexture.")
        row = box.row()
        row.label(text="Reload the scene for changes to take effect in the UI.")
        row = box.row()
        row.label(text="Check the documentation for more information ALKSNDR.COM/QUICKTOOLS")
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text="Global")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "text_size")
        row.prop(bpy.context.preferences.addons[__name__].preferences, "mouse_mult")
        row.prop(bpy.context.preferences.addons[__name__].preferences, "viewport_drawing_border")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "col_primary")
        row.prop(bpy.context.preferences.addons[__name__].preferences, "col_secondary")
        row.prop(bpy.context.preferences.addons[__name__].preferences, "col_tertiary")

        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "path")

        box = layout.box()
        row = box.row()
        row.label(text="Startup")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "uv_mode")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "multilayer")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "res")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "offset")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "paintover")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "paintover_res")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "paintover_offset")
        box = layout.box()
        row = box.row()
        row.label(text="Maps")
        row = box.row()
        row.label(text="QuickTexture places texture maps in the proper slots by looking for these keywords in the file name. Separate keywords by spaces.")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "diffuse")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "roughness")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "normal")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "opacity")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "ao")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "displacement")
        row = box.row()
        row.prop(bpy.context.preferences.addons[__name__].preferences, "metal")

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
            "label": "QuickTexture Decal",
            "keymap": "Object Mode",
            "idname": "object.quicktexturedecal",
            "type": "D",
            "ctrl": True,
            "alt": False,
            "shift": True,
            "value": "PRESS",
        },
        {
            "label": "QuickTexture Paintover",
            "keymap": "Object Mode",
            "idname": "object.quicktexturepaintover",
            "type": "D",
            "ctrl": False,
            "alt": True,
            "shift": True,
            "value": "PRESS",
        },
    ]
}

def get_keys():
    keylists = []
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
    operators.MyPropertiesQT,
    operators.QT_PT_panel,
    operators.quickTexture,
    operators.quickTextureDecal,
    operators.quickTexturePaintover,
    operators.QT_OT_material_qt,
    operators.QT_OT_boxlayer_qt,
    operators.QT_OT_viewlayer_qt,
    operators.QT_OT_triplanar_qt,
    operators.QT_OT_texturemask_qt,
    operators.QT_OT_edgesmask_qt,
    operators.QT_OT_dirtmask_qt,
    operators.QT_OT_heightmask_qt,
    operators.QT_OT_depthmask_qt,
    operators.QT_OT_randomizeperobject_qt,
    operators.QT_OT_replacemaps_qt,
    operators.QT_OT_normalmask_qt,
    operators.QT_OT_variationmask_qt,
    operators.QT_OT_vertexmask_qt,
    operators.QT_OT_smudge_qt,
    operators.QT_OT_detiling_qt,
    operators.QT_OT_copymats,
    operators.QT_OT_resetmaterial,
    operators.QT_OT_makeunique,
    operators.QT_OT_decal_qt,
    operators.QT_OT_paintover_qt,
    operators.QT_OT_apply_paintover_qt,
    operators.QT_MT_Quick_Menu_Pie,
    operators.QT_OT_Quick_Menu_Pie_call,
    operators.BakeFileSelector,
    operators.bakeTextures,
    operators.previewTextures,
    operators.bakePreviewTextures,
    operators.quicktexture_uv,
    operators.quicktexture_view,
    operators.quicktexture_box,
    operators.quicktexture_triplanar,
    operators.photomodelingplane,
    operators.photomodelingbox,
    operators.photomodelingapply,
)

def register():
    global keymaps
    keys = get_keys()
    keymaps = register_keymaps(keys)

    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.my_toolqt = bpy.props.PointerProperty(type=operators.MyPropertiesQT)
    bpy.context.window_manager.my_toolqt.uv_mode = bpy.context.preferences.addons[__package__].preferences.uv_mode
    bpy.context.window_manager.my_toolqt.multilayer = bpy.context.preferences.addons[__package__].preferences.multilayer
    bpy.context.window_manager.my_toolqt.res = bpy.context.preferences.addons[__package__].preferences.res
    bpy.context.window_manager.my_toolqt.offset = bpy.context.preferences.addons[__package__].preferences.offset
    bpy.context.window_manager.my_toolqt.paintover = bpy.context.preferences.addons[__package__].preferences.paintover
    bpy.context.window_manager.my_toolqt.paintover_res = bpy.context.preferences.addons[__package__].preferences.paintover_res
    bpy.context.window_manager.my_toolqt.paintover_offset = bpy.context.preferences.addons[__package__].preferences.paintover_offset
    bpy.context.window_manager.my_toolqt.overscan = bpy.context.preferences.addons[__package__].preferences.overscan
    if not bpy.context.preferences.filepaths.image_editor or bpy.context.preferences.addons[__package__].preferences.path:
        bpy.context.preferences.filepaths.image_editor = bpy.context.preferences.addons[__package__].preferences.path

def unregister():
    global keymaps
    for km, kmi in keymaps:
        km.keymap_items.remove(kmi)

    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.WindowManager.my_toolqt
