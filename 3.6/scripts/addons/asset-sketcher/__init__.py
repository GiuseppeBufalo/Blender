bl_info = {
    "name": "Asset Sketcher 2",
    "author": "Andreas Esau",
    "version": (2, 0, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Addon Description",
    "warning": "",
    "wiki_url": "",
    "category": "Ndee Tools",
}


import bpy
from . operators.asset_item_handling import *
from . operators.physics_calculation import *
from . operators.import_asset_lib import *
from . operators.sketch_operator import *
from . operators.generate_asset_previews import *
from . operators.pie_menu import *
from . operators.asset_list_popup import *
from . properties import *
from . ui import *


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def set_asset_preview(self, context):
        if not self.enable_asset_preview:
            context.window_manager.asset_sketcher.asset_preview = False
            bpy.data.scenes[0].asset_sketcher.asset_preview = False

    enable_asset_preview: bpy.props.BoolProperty(
        name="Enable Asset Preview",
        description="Enable Asset Preview for sketching. This feature is sort of unstable with Undoing brushstrokes.",
        default=True,
        update=set_asset_preview
    )

    paint_mode_shortcut: bpy.props.EnumProperty(name="PaintMode Pie Menu", default="M", description="Opens the Paint Mode Pie menu", items=(("A","A","A"),("B","B","B"),("C","C","C"),("D","D","D"),("E","E","E"),
                                                                                                                                            ("F","F","F"),("G","G","G"),("H","H","H"),("I","I","I"),("J","J","J"),
                                                                                                                                            ("K","K","K"),("L","L","L"),("M","M","M"),("N","N","N"),("O","O","O"),
                                                                                                                                            ("P","P","P"),("Q","Q","Q"),("R","R","R"),("S","S","S"),("T","T","T"),
                                                                                                                                            ("U","U","U"),("V","V","V"),("W","W","W"),("X","X","X"),("Y","Y","Y"),
                                                                                                                                            ("Z","Z","Z"),("ZERO","ZERO","ZERO"),("ONE","ONE","ONE"),("TWO","TWO","TWO"),
                                                                                                                                            ("THREE","THREE","THREE"),("FOUR","FOUR","FOUR"),("FIVE","FIVE","FIVE"),
                                                                                                                                            ("SIX","SIX","SIX"),("SEVEN","SEVEN","SEVEN"),("EIGHT","EIGHT","EIGHT"),
                                                                                                                                            ("NINE","NINE","NINE")))
    asset_list_shortcut: bpy.props.EnumProperty(name="AssetList Menu", default="A", description="Opens the Asset List", items=(("A","A","A"),("B","B","B"),("C","C","C"),("D","D","D"),("E","E","E"),
                                                                                                                               ("F","F","F"),("G","G","G"),("H","H","H"),("I","I","I"),("J","J","J"),
                                                                                                                               ("K","K","K"),("L","L","L"),("M","M","M"),("N","N","N"),("O","O","O"),
                                                                                                                               ("P","P","P"),("Q","Q","Q"),("R","R","R"),("S","S","S"),("T","T","T"),
                                                                                                                               ("U","U","U"),("V","V","V"),("W","W","W"),("X","X","X"),("Y","Y","Y"),
                                                                                                                               ("Z","Z","Z"),("ZERO","ZERO","ZERO"),("ONE","ONE","ONE"),("TWO","TWO","TWO"),
                                                                                                                               ("THREE","THREE","THREE"),("FOUR","FOUR","FOUR"),("FIVE","FIVE","FIVE"),
                                                                                                                               ("SIX","SIX","SIX"),("SEVEN","SEVEN","SEVEN"),("EIGHT","EIGHT","EIGHT"),
                                                                                                                               ("NINE","NINE","NINE")))

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "enable_asset_preview")
        row.label(icon="ERROR")
        col = layout.column()
        col.label(text="Shortcuts:")
        col.prop(self, "paint_mode_shortcut")
        col.prop(self, "asset_list_shortcut")

classes = (
    AddonPreferences,

    # properties.py
    ASSET_SKETCHER_ItemObjects,
    ASSET_SKETCHER_AssetCategories,
    ASSET_SKETCHER_CanvasList,
    ASSET_SKETCHER_AssetList,
    ASSET_SKETCHER_MergeObjectAvailableObjects,
    ASSET_SKETCHER_AssetSketcherProperties,

    # ui.py
    ASSET_SKETCHER_OT_NewMergeObject,
    ASSET_SKETCHER_OT_MergeObjects,
    ASSET_SKETCHER_PT_AssetSketcherUI,
    ASSET_SKETCHER_UL_ListCanvasItem,
    ASSET_SKETCHER_UL_ListAssetItem,

    # asset_item_handling.py
    ASSET_SKETCHER_OT_AddCanvasItem,
    ASSET_SKETCHER_OT_RemoveCanvasItem,
    ASSET_SKETCHER_OT_AddAssetToCategory,
    ASSET_SKETCHER_OT_RemoveAssetToCategory,
    ASSET_SKETCHER_OT_AddAssetCategory,
    ASSET_SKETCHER_OT_RemoveAssetCategory,
    ASSET_SKETCHER_OT_AddAssetItem,
    ASSET_SKETCHER_OT_RemoveAssetItem,
    ASSET_SKETCHER_OT_SelectObjects,

    # physics_calculation.py
    ASSET_SKETCHER_OT_CalcPhysics,
    ASSET_SKETCHER_OT_AddActivePhysics,
    ASSET_SKETCHER_OT_ApplyPhysics,

    # import_asset_lib.py
    ASSET_SKETCHER_OT_ImportAssetLib,

    # sketch_operator.py
    ASSET_SKETCHER_OT_SketchAssets,

    # generate_asset_preview.py
    ASSET_SKETCHER_OT_GenerateAssetPreview,

    # pie_menu.py
    ASSET_SKETCHER_MT_menu,
    ASSET_SKETCHER_OT_SetSketchMode,

    #asset_list_popup.py
    ASSET_SKETCHER_OT_AssetListPopup
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    register_properties()
    register_icons()

    bpy.app.handlers.load_post.append(load_asset_list)
    bpy.app.handlers.save_pre.append(save_asset_list)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    unregister_properties()
    unregister_icons()

    bpy.app.handlers.load_post.remove(load_asset_list)
    bpy.app.handlers.save_pre.remove(save_asset_list)

if __name__ == "__main__":
    register()


@persistent
def save_asset_list(dummy):
    context = bpy.context
    save_load_asset_list(context, mode="SAVE")


@persistent
def load_asset_list(dummy):
    context = bpy.context
    save_load_asset_list(context, mode="LOAD")
