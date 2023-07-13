import bpy
from ... utils.registration import get_prefs
from ... utils.system import save_json, printd
from ... utils.library import validate_presets



class DecalLibraryVisibility(bpy.types.Operator):
    bl_idname = "machin3.decal_library_visibility"
    bl_label = "MACHIN3: Decal Library Visibility"
    bl_description = "Adjust Decal and Trimsheet Library Visibility"
    bl_options = {'INTERNAL'}

    def draw(self, context):
        layout = self.layout
        p = get_prefs()

        column = layout.column()
        column.label(text="Toggle Decal and Trimsheet Library Visibility")

        column.template_list("MACHIN3_UL_simple_decal_libs", "", p, "decallibsCOL", p, "decallibsIDX", rows=max(len(p.decallibsCOL), 6))


        if not context.preferences.use_preferences_save and context.preferences.is_dirty:
            column.operator_context = "EXEC_DEFAULT"
            column.operator("wm.save_userpref", text="Save Prefrences")



        col = column.column(align=True)
        col.operator_context = "INVOKE_DEFAULT"
        col.scale_y = 0.8

        preset_count = 10
        preset_width = 5

        for i in range(int(preset_count / preset_width)):
            row = col.row(align=True)

            for j in range(preset_width):
                preset = str(i * 5 + j + 1)
                row.operator("machin3.decal_library_visibility_preset", text=preset).name = preset

    def execute(self, context):
        validate_presets(debug=False)
        return context.window_manager.invoke_popup(self, width=250)
