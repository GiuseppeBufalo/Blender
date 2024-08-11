import bpy

from .add_prims import CSDF_MT_AddMenu, draw_CSDF_addMenu, CSDF_PT_AddMenu
from .engine.viewport_shading import CSDF_PT_shading_lighting, CSDF_PT_overlays

from .viewport.modifier_stack import (CSDF_PT_OUTLINER, CSDF_PT_PRIMITIVE,
                                      
                                      subscribe_selection_state, unsubscribe_selection_state,
                                      
                                      CSDF_OT_EXPAND_OUTLINER_ITEM,
                                      CSDF_Scene_Node_Childindex,
                                      CSDF_Scene_Node, CSDF_OutlinerUI_Item, CSDF_UL_OUTLINER, 
                                      selectModifier_Item,
                                      )

classes = (
    CSDF_PT_OUTLINER, CSDF_PT_PRIMITIVE,

    CSDF_OT_EXPAND_OUTLINER_ITEM,
    CSDF_Scene_Node_Childindex,
    CSDF_Scene_Node, CSDF_OutlinerUI_Item, CSDF_UL_OUTLINER,

    CSDF_MT_AddMenu, CSDF_PT_AddMenu,
    CSDF_PT_shading_lighting, CSDF_PT_overlays,
)



def register_menus():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.CSDF_SceneNodes = bpy.props.CollectionProperty(type=CSDF_Scene_Node)
    bpy.types.Scene.CSDF_OutlinerTree = bpy.props.CollectionProperty(type=CSDF_OutlinerUI_Item)
    bpy.types.Scene.CSDF_OutlinerTree_index = bpy.props.IntProperty(update=selectModifier_Item)

    bpy.types.VIEW3D_MT_add.prepend(draw_CSDF_addMenu)

    subscribe_selection_state()


def unregister_menus():

    bpy.types.VIEW3D_MT_add.remove(draw_CSDF_addMenu)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.CSDF_SceneNodes
    del bpy.types.Scene.CSDF_OutlinerTree
    del bpy.types.Scene.CSDF_OutlinerTree_index

    unsubscribe_selection_state()
