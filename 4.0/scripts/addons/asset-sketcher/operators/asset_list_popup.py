import bpy

class ASSET_SKETCHER_OT_AssetListPopup(bpy.types.Operator):
    bl_idname = "asset_sketcher.asset_list_popup"
    bl_label = "AssetList Popup"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        wm = context.window_manager
        col = self.layout.column()
        col.label(text="Asset List")
        col.prop(wm.asset_sketcher, "categories_enum", text="")
        col.template_list("ASSET_SKETCHER_UL_ListAssetItem", "dummy", wm.asset_sketcher, "display_asset_list",
                          wm.asset_sketcher, "display_asset_list_index", rows=5)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def execute(self, context):
        print("test")
        return{"FINISHED"}