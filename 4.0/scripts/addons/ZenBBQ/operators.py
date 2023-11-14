# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2022, Dmitry Aleksandrovich Maslov (ABTOMAT)

import bmesh
import bpy

import addon_utils

from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty

from . import globals as ZBBQ_Globals
from .blender_zen_utils import ZenLocks
from .vlog import Log

from .consts import ZBBQ_Consts
from .labels import ZBBQ_Labels

from .commonFunc import ZBBQ_CommonFunc, ZBBQ_MaterialFunc
from .units import ZBBQ_UnitSystems, ZBBQ_Units, ZBBQ_UnitsForEnumPropertySceneUnitSystem, ZBBQ_UnitsForEnumPropertyUnitSystemForCurrentPresetGroup
from .sceneConfig import ZBBQ_PreviewRenderConfigIsNotTouched, ZBBQ_PreviewRenderPresetsSet, ZBBQ_SceneConfigFunc

from timeit import default_timer as timer
from .draw_sets import (
    ZBBQ_EdgeLayerManager,
    remove_draw_handler,
    is_draw_handler_enabled,
    check_update_cache,
    _do_add_draw_handler,
    _do_remove_draw_handler
)


class ZBBQ_OT_ActiveObjectGetReady(Operator):  # Deprecated, debug use only!

    bl_idname = "object.zen_bbq_active_object_get_ready"
    bl_label = ZBBQ_Labels.ZBBQ_OT_ActiveObjectGetReady_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_ActiveObjectGetReady_Desc
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        ZBBQ_CommonFunc.Report(self, ZBBQ_Labels.ZBBQ_OT_ActiveObjectGetReady_Report)
        ZBBQ_CommonFunc.ObjectGetReadyForBevel(context.active_object)

        return {"FINISHED"}


class ZBBQ_OT_ShaderNodeNormalAdd(Operator):  # Deprecated. For debug purposes only.

    # For debug purposes only.
    # Adding bevel node is performed automatically when needed

    bl_idname = "object.zen_bbq_shader_node_normal_add"
    bl_label = ZBBQ_Labels.ZBBQ_OT_ShaderNodeNormalAdd_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_ShaderNodeNormalAdd_Desc
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        ZBBQ_MaterialFunc.MaterialAddShaderNodeNormal(context.active_object.active_material)

        return {'FINISHED'}


class ZBBQ_OT_ShaderNodeNormalRemove(Operator):  # Deprecated. For debug purposes only.

    bl_idname = "object.zen_bbq_shader_node_normal_remove"
    bl_label = ZBBQ_Labels.ZBBQ_OT_ShaderNodeNormalRemove_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_ShaderNodeNormalRemove_Desc
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        ZBBQ_MaterialFunc.MaterialRemoveShaderNodeNormal(context.active_object.active_material)

        return {'FINISHED'}


class ZBBQ_OT_ShaderNodeNormalToggle(Operator):

    bl_idname = "object.zen_bbq_shader_node_normal_toggle"
    bl_label = ZBBQ_Labels.ZBBQ_OT_ShaderNodeNormalToggle_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_ShaderNodeNormalToggle_Desc
    bl_options = {'REGISTER', 'UNDO'}

    toggleMode: bpy.props.EnumProperty(
        items=[("AUTO", "Toggle", ""),
               ("ON", "On", ""),
               ("OFF", "Off", "")],
        default='AUTO')

    @classmethod
    def poll(cls, context):

        objects = []

        if context.mode == 'EDIT_MESH':
            objects = context.objects_in_mode
        elif context.mode == 'OBJECT':
            objects = context.selected_editable_objects

        if len(ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(objects, ZBBQ_Consts.shaderNodeTreeNormalName)['objectsToToggle']) == 0:
            return False

        # Button is disabled also if Preview Node is on

        toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode
        previewShaderNodeToggleModeAndObjects = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(objects, toggleNodeTreeName)

        return previewShaderNodeToggleModeAndObjects['toggleMode'] == 'ON'

    def execute(self, context):

        shaderNodeStatus = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(context.selected_editable_objects, ZBBQ_Consts.shaderNodeTreeNormalName)
        objectsToToggle = shaderNodeStatus['objectsToToggle']

        toggleMode = self.toggleMode
        if(self.toggleMode == 'AUTO'):
            toggleMode = shaderNodeStatus['toggleMode']

        ZBBQ_CommonFunc.Report(self, f"Toggling Material Bevel Node {toggleMode}, objects to toggle: {len(objectsToToggle)}")

        if toggleMode == 'ON':
            for obj in objectsToToggle:
                for mat in obj.data.materials:
                    ZBBQ_MaterialFunc.MaterialAddShaderNodeNormal(mat)
        else:
            for obj in objectsToToggle:
                for mat in obj.data.materials:
                    ZBBQ_MaterialFunc.MaterialRemoveShaderNodeNormal(mat)

        return {'CANCELLED'}


class ZBBQ_OT_SetBevelRadiusToSelection(Operator):

    bl_idname = "object.zen_bbq_set_radius_to_selection"
    bl_label = ZBBQ_Labels.ZBBQ_OT_SetBevelRadiusToSelection_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_SetBevelRadiusToSelection_Desc
    bl_options = {'REGISTER', 'UNDO'}

    radius: bpy.props.FloatProperty(name=ZBBQ_Labels.ZBBQ_OT_SetBevelRadiusToSelection_Prop_Radius_Name,
                                    description=ZBBQ_Labels.ZBBQ_OT_SetBevelRadiusToSelection_Prop_Radius_Desc,
                                    default=100, min=0, soft_max=500, subtype='FACTOR')
    units: EnumProperty(
            name=ZBBQ_Labels.ZBBQ_OT_SetBevelRadiusToSelection_Prop_Units_Name,
            description=ZBBQ_Labels.ZBBQ_OT_SetBevelRadiusToSelection_Prop_Units_Desc,
            items=lambda self, context: ZBBQ_UnitsForEnumPropertyUnitSystemForCurrentPresetGroup(),
    )

    @classmethod
    def poll(cls, context):

        if context.mode == 'EDIT_MESH':
            for obj in context.objects_in_mode:
                if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                    continue

                if obj.data.total_vert_sel > 0:
                    return True

            return False

        elif context.mode == 'OBJECT':
            return len(context.selected_editable_objects) > 0
        else:
            return False

    def execute(self, context):

        unitsInfo = ZBBQ_Units[self.units]
        radius = self.radius * unitsInfo.unitAndSceneScaleMultiplier()

        if context.mode == 'EDIT_MESH':
            prefs = ZBBQ_CommonFunc.GetPrefs()
            boundaryLoopOnlyMode = bpy.context.tool_settings.mesh_select_mode[2] and prefs.polygonBoundaryLoopOnly

            ZBBQ_CommonFunc.SetBevelRadiusToSelectedGeometry(context.objects_in_mode, radius, boundaryLoopOnlyMode)
            ZBBQ_CommonFunc.Report(self, f'Applying bevel radius {self.radius:2g} {unitsInfo.shortTitle} to the selected geometry!')
        else:
            ZBBQ_CommonFunc.SetBevelRadiusToObjects(context.selected_editable_objects, radius)
            ZBBQ_CommonFunc.Report(self, f'Applying bevel radius {self.radius:2g} {unitsInfo.shortTitle} to the selected objects!')

        if (ZBBQ_PreviewRenderConfigIsNotTouched()):
            ZBBQ_PreviewRenderPresetsSet(None, 2)

        ZBBQ_CommonFunc.ColoredEdgesEnableIfNeverUsed()

        return {"FINISHED"}


class ZBBQ_OT_SetZeroBevelRadiusToSelection(Operator):

    bl_idname = "object.zen_bbq_set_zero_radius_to_selection"
    bl_label = ZBBQ_Labels.ZBBQ_OT_SetZeroBevelRadiusToSelection_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_SetZeroBevelRadiusToSelection_Desc
    bl_options = {'REGISTER', 'UNDO'}

    forWholeObject = False

    @classmethod
    def poll(cls, context):

        if context.mode == 'EDIT_MESH':
            for obj in context.objects_in_mode:
                if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                    continue
                return True

            return False
        else:
            return False

    def execute(self, context):

        if self.forWholeObject:
            # If there is no selected vertices, we apply sero to whole mesh
            ZBBQ_CommonFunc.SetBevelRadiusToObjects(context.objects_in_mode, 0)
        else:
            prefs = ZBBQ_CommonFunc.GetPrefs()
            boundaryLoopOnlyMode = bpy.context.tool_settings.mesh_select_mode[2] and prefs.polygonBoundaryLoopOnly

            ZBBQ_CommonFunc.SetBevelRadiusToSelectedGeometry(context.objects_in_mode, 0, boundaryLoopOnlyMode)
            ZBBQ_CommonFunc.Report(self, 'Applying zero bevel radius to the selected geometry!')

        if (ZBBQ_PreviewRenderConfigIsNotTouched()):
            ZBBQ_PreviewRenderPresetsSet(None, 2)

        return {"CANCELLED"}

    def invoke(self, context, event):

        for obj in context.objects_in_mode:
            if obj.data.total_vert_sel > 0:
                return self.execute(context)

        self.forWholeObject = True
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text="This set zero bevel to the whole mesh, "+ZBBQ_CommonFunc.StrConfirmQuestion(self))


class ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts(Operator):
    bl_idname = "object.zen_bbq_smart_select_by_radius_of_selected_verts"
    bl_label = ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts_Desc
    bl_options = {'REGISTER', 'UNDO'}

    # thresholdPrecentage: bpy.props.FloatProperty(name=ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts_Prop_ThresholdPrecentage_Name,
    #                                              description=ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts_Prop_ThresholdPrecentage_Desc,
    #                                              default=10, min=0, max=300, subtype='FACTOR')

    @classmethod
    def poll(cls, context):

        if context.mode == 'EDIT_MESH':
            for obj in context.objects_in_mode:
                if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                    continue
                if obj.data.total_vert_sel > 0:
                    return True
            return False
        else:
            return False

    def execute(self, context):

        valuesToCheck = []

        for obj in context.objects_in_mode:

            if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                # Non-mesh objects are ignored
                continue

            if obj.data.total_vert_sel == 0:
                continue

            bm = bmesh.from_edit_mesh(obj.data)
            vertsSelected = [vert for vert in bm.verts if vert.select]

            if not ZBBQ_CommonFunc.ObjectHasDataLayer(obj):
                # We do not add Data Layer if there is none
                # Instead, we consider all vertices to have zero radius
                valuesToCheck.append(0)
                continue

            dataLayer = bm.verts.layers.float.get(ZBBQ_Consts.customDataLayerName)
            if dataLayer is None:
                dataLayer = bm.verts.layers.float.new(ZBBQ_Consts.customDataLayerName)

            for vert in vertsSelected:
                if not vert[dataLayer] in valuesToCheck:
                    valuesToCheck.append(vert[dataLayer])

        ZBBQ_CommonFunc.Report(self, f"Selecting geometry with Bevel Radius {valuesToCheck}")

        ZBBQ_CommonFunc.SmartSelectByRadiusValues(context.objects_in_mode, valuesToCheck, ZBBQ_CommonFunc.GetPrefs().smartSelectRadiusThreshold*0.01, True)

        ZBBQ_CommonFunc.ColoredEdgesEnableIfNeverUsed()

        return {"FINISHED"}

    def draw(self, context):
        self.layout.prop(ZBBQ_CommonFunc.GetPrefs(), 'smartSelectRadiusThreshold')


class ZBBQ_OT_SmartSelectByRadiusFromActivePreset(Operator):  # Deprecated
    bl_idname = "object.zen_bbq_smart_select_by_radius_from_active_preset"
    bl_label = ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Desc
    bl_options = {'REGISTER', 'UNDO'}

    # thresholdPrecentage: bpy.props.FloatProperty(name=ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Prop_ThresholdPrecentage_Name,
    #                                              description=ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Prop_ThresholdPrecentage_Desc,
    #                                              default=10, min=0, max=300, subtype='FACTOR')

    addToSelection: bpy.props.BoolProperty(
            name=ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Prop_AddToSelection_Name,
            description=ZBBQ_Labels.ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Prop_AddToSelection_Desc,
            default=False)

    @classmethod
    def poll(cls, context):

        if context.mode == 'EDIT_MESH':
            for obj in context.objects_in_mode:
                if ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                    return True

            return False

        else:

            return False

    def execute(self, context):
        bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()
        bp = bpg.bevelPresets[bpg.bevelPresetsIndex]

        ZBBQ_CommonFunc.SmartSelectByRadiusValues(context.objects_in_mode, [bp.radius*bp.unitAndSceneScaleMultiplier()], ZBBQ_CommonFunc.GetPrefs().smartSelectRadiusThreshold*0.01, self.addToSelection)

        ZBBQ_CommonFunc.ColoredEdgesEnableIfNeverUsed()

        return {"FINISHED"}

    def draw(self, context):
        self.layout.prop(ZBBQ_CommonFunc.GetPrefs(), 'smartSelectRadiusThreshold')
        self.layout.prop(self, 'addToSelection')


class ZBBQ_OT_PreviewShaderNodeToggle(Operator):
    bl_idname = "object.zen_bbq_preview_shader_node_toggle"
    bl_label = ZBBQ_Labels.ZBBQ_OT_PreviewShaderNodeToggle_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_PreviewShaderNodeToggle_Desc
    bl_options = {'REGISTER', 'UNDO'}

    toggleMode: bpy.props.EnumProperty(
        items=[("AUTO", "Toggle", ""),
               ("ON", "On", ""),
               ("OFF", "Off", "")],
        default='AUTO')

    @classmethod
    def poll(cls, context):

        objects = []

        if context.mode == 'EDIT_MESH':
            objects = context.objects_in_mode
        elif context.mode == 'OBJECT':
            objects = context.selected_editable_objects

        if len(objects) == 0:
            return False

        toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode
        return len(ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(objects, toggleNodeTreeName, 'OVERRIDE')['objectsToToggle']) > 0

    def execute(self, context):
        # ZBBQ_CommonFunc.Report(self, "Toggling Preview")

        toggleNodeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode
        toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode

        objects = []

        if context.mode == 'EDIT_MESH':
            objects = context.objects_in_mode
        elif context.mode == 'OBJECT':
            objects = context.selected_editable_objects

        previewShaderNodeStatus = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(objects, toggleNodeTreeName, 'OVERRIDE')

        objectsToToggle = previewShaderNodeStatus['objectsToToggle']

        toggleMode = self.toggleMode
        if(self.toggleMode == 'AUTO'):
            toggleMode = previewShaderNodeStatus['toggleMode']

        ZBBQ_CommonFunc.Report(self, f"Toggling Preview {toggleMode}, objects to toggle: {len(objectsToToggle)}")

        if toggleMode == 'ON':
            for obj in objectsToToggle:
                for mat in obj.data.materials:
                    ZBBQ_MaterialFunc.MaterialAddOverrideNode(mat, toggleNodeName, toggleNodeTreeName)
        else:
            for obj in objectsToToggle:
                for mat in obj.data.materials:
                    ZBBQ_MaterialFunc.MaterialRemoveOverrideNode(mat, toggleNodeTreeName)

        # return {"FINISHED"}
        return {"CANCELLED"}


class ZBBQ_OT_TestOpA(Operator):  # Test operator for debug purposes

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'MESH'

    bl_idname = "object.zen_bbq_test_op_a"
    bl_label = "Test Button A"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Test OP Plz ignore"

    def execute(self, context):
        ZBBQ_CommonFunc.Report(self, 'Test Button A!')

        # bpy.ops.mesh.select_mode(type="FACE")
        if bpy.context.tool_settings.mesh_select_mode[2]:  # Face mode is ON
            print("Face Mode is ON!")
        else:
            print("Face Mode is OFF!")

        # ZBBQ_SceneConfigFunc.OverlayConfigOverride()

        # ZBBQ_MaterialFunc.NodeTreeNormalSetSamples(32)
        # ZBBQ_MaterialFunc.NodeTreeNormalGetSamples()

        return {'FINISHED'}


class ZBBQ_OT_TestOpB(Operator):  # Test operator for debug purposes

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'MESH'

    bl_idname = "object.zen_bbq_test_op_b"
    bl_label = "Test Button B"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Test OP Plz ignore"

    def execute(self, context):
        ZBBQ_CommonFunc.Report(self, 'Test Button B!')

        ZBBQ_SceneConfigFunc.OverlayConfigRestore()

        # ZBBQ_MaterialFunc.NodeTreeNormalSetSamples(32)
        # ZBBQ_MaterialFunc.NodeTreeNormalGetSamples()

        return {'FINISHED'}


class ZBBQ_OT_FixSceneUnitSystem(Operator):
    bl_idname = "object.zen_bbq_fix_scene_unit_system"
    bl_label = ZBBQ_Labels.ZBBQ_OT_FixSceneUnitSystem_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_FixSceneUnitSystem_Desc
    bl_options = {'REGISTER', 'UNDO'}

    unitSystem = 'METRIC'

    def execute(self, context):

        print(type(bpy.context.scene.unit_settings.system))

        bpy.context.scene.unit_settings.system = self.unitSystem
        return {'CANCELLED'}

    def invoke(self, context, event):

        bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()
        if bpg:
            self.unitSystem = bpg.unitSystem
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        self.layout.label(text=ZBBQ_Labels.ZBBQ_OT_FixSceneUnitSystem_Confirm+ZBBQ_UnitSystems[self.unitSystem]+", "+ZBBQ_CommonFunc.StrConfirmQuestion(self))


class ZBBQ_OT_RenderPreviewToggle(Operator):
    bl_idname = "object.zen_bbq_render_preview_toggle"
    bl_label = ZBBQ_Labels.ZBBQ_OT_RenderPreviewToggle_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_RenderPreviewToggle_Desc
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        cyclesWasJustActivated = False

        if bpy.context.scene.render.engine != 'CYCLES':
            bpy.context.scene.render.engine = 'CYCLES'
            cyclesWasJustActivated = True
            ZBBQ_CommonFunc.Report(self, ZBBQ_Labels.ZBBQ_OT_RenderPreviewToggle_Report_Cycles)

        for space in context.area.spaces:
            if space.type == 'VIEW_3D':

                OpToggle = eval("bpy.ops."+ZBBQ_OT_PreviewShaderNodeToggle.bl_idname)

                if space.shading.type == "SOLID" or bpy.context.scene.cycles.preview_pause or cyclesWasJustActivated:
                    Log.debug('Switching shading to Rendered!')

                    space.shading.type = "RENDERED"

                    if bpy.context.scene.cycles.preview_pause:
                        bpy.context.scene.cycles.preview_pause = False
                        bpy.context.scene.update_tag()

                    if bpy.context.scene.ZBBQ_AutoPreviewShaderNodeToggle:
                        if OpToggle.poll():
                            OpToggle('INVOKE_DEFAULT', toggleMode='ON')

                    if (ZBBQ_PreviewRenderConfigIsNotTouched()):
                        ZBBQ_PreviewRenderPresetsSet(None, 2)
                else:
                    Log.debug('Switching shading to Solid!')

                    if bpy.context.scene.ZBBQ_AutoPreviewShaderNodeToggle:
                        if OpToggle.poll():
                            OpToggle('INVOKE_DEFAULT', toggleMode='OFF')

                    space.shading.type = "SOLID"

        # return {'FINISHED'}
        return {"CANCELLED"}

    def invoke(self, context, event):

        if bpy.context.scene.render.engine != 'CYCLES' and ZBBQ_CommonFunc.GetPrefs().cyclesActivatingConfirmation:
            return context.window_manager.invoke_props_dialog(self)

        return self.execute(context)

    def draw(self, context):
        if bpy.context.scene.render.engine != 'CYCLES':

            self.layout.label(text=ZBBQ_Labels.ZBBQ_OT_RenderPreviewToggle_Confirm_Cycles+ZBBQ_CommonFunc.StrConfirmQuestion(self))


class ZBBQ_OT_BakeNormalForSelection(Operator):
    bl_idname = "object.zen_bbq_bake_normal_to_selection"
    bl_label = ZBBQ_Labels.ZBBQ_OT_BakeNormalForSelection_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_BakeNormalForSelection_Desc
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):

        objects = []

        if context.mode == 'EDIT_MESH':
            objects = context.objects_in_mode
        elif context.mode == 'OBJECT':
            objects = context.selected_objects

        if len(objects) == 0:
            return False

        return True

    def execute(self, context):
        print('[Not implemented] Baking normal!!')
        return {'FINISHED'}

    def invoke(self, context, event):

        if bpy.context.scene.render.engine != 'CYCLES' and ZBBQ_CommonFunc.GetPrefs().cyclesActivatingConfirmation:
            return context.window_manager.invoke_props_dialog(self)

        return self.execute(context)

    def draw(self, context):
        if bpy.context.scene.render.engine != 'CYCLES':

            row = self.layout
            row.label(text=ZBBQ_Labels.ZBBQ_OT_RenderPreviewToggle_Confirm_Cycles+ZBBQ_CommonFunc.StrConfirmQuestion(self))


class ZBBQ_OT_PieMenuGeometryOptionsTop(Operator):
    bl_idname = "object.zen_bbq_pie_menu_geometry_options_top"
    bl_label = ZBBQ_Labels.ZBBQ_OT_PieMenuGeometryOptionsTop_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_PieMenuGeometryOptionsTop_Desc
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):  # Check if we have some verts selected
        if context.mode == 'EDIT_MESH':
            for obj in context.objects_in_mode:
                if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                    continue
                if obj.data.total_vert_sel > 0:
                    return True
            return False
        else:
            return False

    def invoke(self, context, event):

        modCtrl = getattr(event, 'ctrl', False)

        if not modCtrl:
            OpEval = eval("bpy.ops."+ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts.bl_idname)
            if OpEval.poll():
                OpEval('INVOKE_DEFAULT')
                # ZBBQ_CommonFunc.Report(self, result)
        else:
            OpEval = eval("bpy.ops."+ZBBQ_OT_SetZeroBevelRadiusToSelection.bl_idname)
            if OpEval.poll():
                OpEval('INVOKE_DEFAULT')

        return {'FINISHED'}


class ZBBQ_OT_PieMenuGeometryOptionsBottom(Operator):
    bl_idname = "object.zen_bbq_pie_menu_geometry_options_bottom"
    bl_label = ZBBQ_Labels.ZBBQ_OT_PieMenuGeometryOptionsBottom_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_PieMenuGeometryOptionsBottom_Desc
    bl_options = {'REGISTER', 'UNDO'}

    # cmd = "bpy.ops."+ZBBQ_OT_SwitchShadingMode.bl_idname+"('INVOKE_DEFAULT')"
    opName = ""

    def invoke(self, context, event):

        self.opName = ZBBQ_OT_RenderPreviewToggle.bl_idname

        # ctrlUsageAllowed = event.type == "LEFTMOUSE"  or event.type == "TWO" or event.type.startswith("NUMPAD_")

        if getattr(event, 'ctrl', False):
            # User was holding Ctrl while activating this operator
            # print(f'CTRL is used! Event Type: {event.type}')

            self.opName = ZBBQ_OT_DrawHighlight.bl_idname

        return self.execute(context)

    def execute(self, context):

        OpEval = eval("bpy.ops."+self.opName)

        if OpEval.poll():
            OpEval('INVOKE_DEFAULT')
        else:
            ZBBQ_CommonFunc.Report(self, text=ZBBQ_Labels.ZBBQ_OT_PieMenuGeometryOptionsBottom_Report_MeshEditOnly)

        return {'FINISHED'}

# Preferences and Cleanup


class ZBBQ_OT_MaterialsRepair(Operator):

    bl_idname = "global.zen_bbq_materials_repair"
    bl_label = ZBBQ_Labels.ZBBQ_OT_MaterialRepair_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_MaterialRepair_Desc
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode

        for mat in bpy.data.materials:
            if mat.name == ZBBQ_Consts.defaultMaterialName:
                # If there is Zen BBQ default material, we recreate it
                print('ZenBBQ Default Material — recreate it')
                ZBBQ_MaterialFunc.CreateDefaultMaterial(mat)
            else:
                # User's material.
                # print(mat.name)

                needToRecreateBevelShaderNode = len(ZBBQ_MaterialFunc.MaterialGetShaderNodeGroups(mat, ZBBQ_Consts.shaderNodeTreeNormalName, 'NOCHECK')) > 0

                ZBBQ_MaterialFunc.MaterialRemoveShaderNodeNormal(mat)  # Remove regular Bevel Nodes
                ZBBQ_MaterialFunc.MaterialRemoveOverrideNode(mat, toggleNodeTreeName)  # To-Do: Multiple options

                # Remove nodes that are not linked:
                ZBBQ_MaterialFunc.MaterialRemoveShaderNodeGroupsByNodeTreeName(mat, ZBBQ_Consts.shaderNodeTreeNormalName)
                ZBBQ_MaterialFunc.MaterialRemoveShaderNodeGroupsByNodeTreeName(mat, toggleNodeTreeName)

                # Re-create Bevel node
                if needToRecreateBevelShaderNode:
                    # print(f'{mat.name} — recreate Bevel Shader Node!')
                    ZBBQ_MaterialFunc.MaterialAddShaderNodeNormal(mat)

        return {'CANCELLED'}


class ZBBQ_OT_ObjectAddonCleanup(Operator):

    bl_idname = "object.zen_bbq_addon_cleanup"
    bl_label = ZBBQ_Labels.ZBBQ_OT_ObjectAddonCleanup_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_ObjectAddonCleanup_Desc
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):

        if context.mode == 'EDIT_MESH':
            return len(context.objects_in_mode) > 0
        elif context.mode == 'OBJECT':
            return len(context.selected_editable_objects) > 0

    def execute(self, context):

        objectsToReset = []
        if context.mode == 'EDIT_MESH':
            objectsToReset = context.objects_in_mode
        elif context.mode == 'OBJECT':
            objectsToReset = context.selected_editable_objects

        try:
            ZenLocks.lock_depsgraph_update()

            for obj in objectsToReset:
                ZBBQ_CommonFunc.ObjectCleanupFromForBevel(obj)

        finally:
            ZenLocks.unlock_depsgraph_update()
        pass

        ZBBQ_CommonFunc.Report(self, text=f"Successfully reset {len(objectsToReset)} object(s)!")

        return {"CANCELLED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        objectsToReset = []
        if context.mode == 'EDIT_MESH':
            objectsToReset = context.objects_in_mode
        elif context.mode == 'OBJECT':
            objectsToReset = context.selected_editable_objects

        self.layout.label(text=f"This will cleanup {len(objectsToReset)} object(s) from Zen BBQ, "+ZBBQ_CommonFunc.StrConfirmQuestion(self))


class ZBBQ_OT_GlobalAddonCleanup(Operator):

    bl_idname = "global.zen_bbq_addon_cleanup"
    bl_label = ZBBQ_Labels.ZBBQ_OT_GlobalAddonCleanup_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_GlobalAddonCleanup_Desc
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        ZBBQ_CommonFunc.GlobalCleanup()

        ZBBQ_CommonFunc.Report(self, text=ZBBQ_Labels.ZBBQ_OT_GlobalAddonCleanup_Report_Success)

        return {"CANCELLED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=ZBBQ_Labels.ZBBQ_OT_GlobalAddonCleanup_Confirm+ZBBQ_CommonFunc.StrConfirmQuestion(self))


class ZBBQ_OT_Keymaps(bpy.types.Operator):
    bl_idname = "global.zen_bbq_show_keymaps"
    bl_label = ZBBQ_Labels.ZBBQ_OT_Keymaps_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_Keymaps_Desc
    bl_options = {'INTERNAL'}

    def execute(self, context):

        addon_utils.modules_refresh()

        try:
            mod = addon_utils.addons_fake_modules.get(ZBBQ_Consts.addonId)
            info = addon_utils.module_bl_info(mod)
            info["show_expanded"] = True  # or False to Collapse
        except Exception as e:
            print(e)

        addon_prefs = ZBBQ_CommonFunc.GetPrefs()
        addon_prefs.tabs = 'KEYMAP'

        context.preferences.active_section = "ADDONS"
        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        bpy.data.window_managers['WinMan'].addon_search = ZBBQ_Consts.addonName

        return {'FINISHED'}


# Managing presets


class ZBBQ_OT_PresetsPresetGroupAdd(Operator):

    bl_idname = "zbv_ul_presets.preset_group_add"
    bl_label = ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupAdd_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupAdd_Desc

    title: StringProperty(
           name=ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupAdd_Prop_Title_Name,
           description=ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupAdd_Prop_Title_Desc,
           default="Untitled"
    )

    units: EnumProperty(
            name=ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupAdd_Prop_Units_Name,
            description=ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupAdd_Prop_Units_Desc,
            items=lambda self, context: ZBBQ_UnitsForEnumPropertySceneUnitSystem(),
    )

    def execute(self, context):
        pg = ZBBQ_CommonFunc.CreateBevelPresetGroup(self.title, self.units)
        ZBBQ_CommonFunc.Report(self, f'New Preset Group added: {pg.title}!')

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=200)


class ZBBQ_OT_PresetsPresetGroupRemove(Operator):

    bl_idname = "zbv_ul_presets.preset_group_remove"
    bl_label = ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupRemove_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupRemove_Desc

    @classmethod
    def poll(cls, context):
        return len(ZBBQ_CommonFunc.GetPrefs().bevelPresetGroups) > 1

    def execute(self, context):

        msg = ""

        prefs = ZBBQ_CommonFunc.GetPrefs()
        bpgIndex = int(prefs.bevelPresetGroupsDropdown)

        if(bpgIndex == len(prefs.bevelPresetGroups)):  # Scene Saved
            msg = f"Preset Group \"{ZBBQ_CommonFunc.GetActiveBevelPresetGroup().title}\" has been removed from scene data!"
            bpy.context.scene.ZBBQ_HasPresetsIncluded = False
            ZBBQ_Globals.displaySceneIncludedBevelPresets = False

            prefs.bevelPresetGroupsDropdown = "0"
        else:
            msg = f"Preset Group \"{ZBBQ_CommonFunc.GetActiveBevelPresetGroup().title}\" has been removed from your preferences!"
            prefs.bevelPresetGroups.remove(bpgIndex)

            if len(prefs.bevelPresetGroups) > 0:
                prefs.bevelPresetGroupsDropdown = str(min(
                    max(0, bpgIndex - 1),
                    len(prefs.bevelPresetGroups) - 1))

        ZBBQ_CommonFunc.Report(self, msg)

        return{'FINISHED'}

    def draw(self, context):

        msg = ""

        prefs = ZBBQ_CommonFunc.GetPrefs()
        bpgIndex = int(prefs.bevelPresetGroupsDropdown)

        if(bpgIndex == len(prefs.bevelPresetGroups)):  # Scene Saved
            msg = f"Remove \"{ZBBQ_CommonFunc.GetActiveBevelPresetGroup().title}\" from scene data, "+ZBBQ_CommonFunc.StrConfirmQuestion(self)
        else:
            msg = f"Remove \"{ZBBQ_CommonFunc.GetActiveBevelPresetGroup().title}\" from your preferences, "+ZBBQ_CommonFunc.StrConfirmQuestion(self)

        self.layout.label(text=msg)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ZBBQ_OT_PresetsPresetGroupImportFromScene(Operator):

    bl_idname = "zbv_ul_presets.preset_group_import_from_scene"
    bl_label = ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupImportFromScene_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupImportFromScene_Desc

    bpgToReplace = None

    @classmethod
    def poll(cls, context):
        return ZBBQ_Globals.displaySceneIncludedBevelPresets

    def draw(self, context):
        self.layout.label(text=f"Replace \"{self.bpgToReplace.title}\" preset group?")

    def execute(self, context):

        bpgScene = bpy.context.scene.ZBBQ_PresetsIncluded

        prefs = ZBBQ_CommonFunc.GetPrefs()
        if(self.bpgToReplace is None):
            self.bpgToReplace = prefs.bevelPresetGroups.add()

        self.bpgToReplace.title = bpgScene.title
        self.bpgToReplace.unitSystem = bpgScene.unitSystem
        self.bpgToReplace.bevelPresetsIndex = bpgScene.bevelPresetsIndex

        for i in range(len(self.bpgToReplace.bevelPresets)-1, -1, -1):
            self.bpgToReplace.bevelPresets.remove(i)

        for i in range(len(bpgScene.bevelPresets)):

            bpScene = bpgScene.bevelPresets[i]

            preset = self.bpgToReplace.bevelPresets.add()
            preset.unitSystem = bpScene.unitSystem
            preset.radius = bpScene.radius
            preset.units = bpScene.units
            preset.colorId = bpScene.colorId
            preset.color = bpScene.color

        ZBBQ_Globals.displaySceneIncludedBevelPresets = False
        prefs.bevelPresetGroupsDropdown = str([index for (index, item) in enumerate(prefs.bevelPresetGroups) if item == self.bpgToReplace][0])

        # To-Do: Open dopdown on correct indes

        return{'FINISHED'}

    def invoke(self, context, event):

        prefs = ZBBQ_CommonFunc.GetPrefs()
        for bpg in prefs.bevelPresetGroups:
            if bpg.title == bpy.context.scene.ZBBQ_PresetsIncluded.title:
                self.bpgToReplace = bpg
                return context.window_manager.invoke_props_dialog(self)

        return self.execute(context)


class ZBBQ_OT_PresetsPresetGroupOrderChange(Operator):

    bl_idname = "zbv_ul_presets.preset_group_order_change"
    bl_label = ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupOrderChange_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_PresetsPresetGroupOrderChange_Desc

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', "Move the selected preset group in order up"),
                                             ('DOWN', 'Down', "Move the selected preset group in order down"),))

    @classmethod
    def poll(cls, context):
        return len(ZBBQ_CommonFunc.GetPrefs().bevelPresetGroups) > 0

    def OrderChange(self):

        prefs = ZBBQ_CommonFunc.GetPrefs()
        bpgIndex = int(prefs.bevelPresetGroupsDropdown)

        if len(prefs.bevelPresetGroups) > 0:
            prefs.bevelPresetGroupsDropdown = str(max(
                0, min(bpgIndex + (-1 if self.direction == 'UP' else 1),
                       len(prefs.bevelPresetGroups) - 1)))

    def execute(self, context):

        prefs = ZBBQ_CommonFunc.GetPrefs()
        bpgIndex = int(prefs.bevelPresetGroupsDropdown)

        prefs.bevelPresetGroups.move(bpgIndex + (-1 if self.direction == 'UP' else 1), bpgIndex)

        self.OrderChange()

        return{'FINISHED'}


class ZBBQ_OT_PresetsPresetOrderChange(Operator):

    bl_idname = "zbv_ul_presets.preset_order_change"
    bl_label = ZBBQ_Labels.ZBBQ_OT_PresetsPresetOrderChange_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_PresetsPresetOrderChange_Desc

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', "Move the selected preset in order up"),
                                             ('DOWN', 'Down', "Move the selected preset in order down"),))

    @classmethod
    def poll(cls, context):
        return len(ZBBQ_CommonFunc.GetPrefs().bevelPresetGroups) > 0

    def execute(self, context):

        bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()
        bpg.bevelPresets.move(bpg.bevelPresetsIndex + (-1 if self.direction == 'UP' else 1), bpg.bevelPresetsIndex)

        if len(bpg.bevelPresets) > 0:
            bpg.bevelPresetsIndex = max(
                0, min(bpg.bevelPresetsIndex + (-1 if self.direction == 'UP' else 1),
                       len(bpg.bevelPresets) - 1))
        return{'FINISHED'}


class ZBBQ_OT_ResetPreferences(Operator):

    bl_idname = "global.zen_bbq_reset_preferences"
    bl_label = ZBBQ_Labels.ZBBQ_OT_ResetPreferences_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_ResetPreferences_Desc
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        ZBBQ_CommonFunc.BevelPresetGroupsResetToDefault()

        prefs = ZBBQ_CommonFunc.GetPrefs()
        prefs.smartSelectRadiusThreshold = ZBBQ_Consts.smartSelectRadiusThresholdDefault
        prefs.polygonBoundaryLoopOnly = False
        prefs.cyclesActivatingConfirmation = True

        if context.mode == 'EDIT_MESH':
            eval("bpy.ops."+ZBBQ_OT_DrawHighlight.bl_idname+"('INVOKE_DEFAULT', mode='OFF')")

        ZBBQ_CommonFunc.Report(self, text=ZBBQ_Labels.ZBBQ_OT_ResetPreferences_Report_Success)

        return {"CANCELLED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=ZBBQ_Labels.ZBBQ_OT_ResetPreferences_Confirm+ZBBQ_CommonFunc.StrConfirmQuestion(self))


class ZBBQ_OT_DrawHighlight(bpy.types.Operator):
    bl_idname = 'zbbq.draw_highlight'
    bl_label = ZBBQ_Labels.ZBBQ_OT_DrawHighlight_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_DrawHighlight_Desc
    bl_options = {'REGISTER'}

    mode: bpy.props.EnumProperty(
        items=[("NONE", "None", ""),
               ("ON", "On", ""),
               ("OFF", "Off", "")],
        default='NONE')

    @classmethod
    def poll(cls, context):
        if context.mode not in {'EDIT_MESH'}:
            return False

        return True

    def modal(self, context, event):
        p_cls_mgr = ZBBQ_EdgeLayerManager
        if p_cls_mgr:
            if is_draw_handler_enabled(p_cls_mgr):
                if hasattr(context, "area"):
                    if context.area is not None:
                        context.area.tag_redraw()
            return {'PASS_THROUGH'}
        else:
            return {'CANCELLED'}

    def cancel(self, context):
        p_cls_mgr = ZBBQ_EdgeLayerManager
        if p_cls_mgr:
            remove_draw_handler(p_cls_mgr, context)

    def invoke(self, context, event):
        if context.mode in {'EDIT_MESH'}:
            p_cls_mgr = ZBBQ_EdgeLayerManager
            if p_cls_mgr:
                b_modal = False
                if not is_draw_handler_enabled(p_cls_mgr):
                    if self.mode != 'OFF':
                        interval = timer()
                        for p_obj in context.objects_in_mode:
                            Log.debug('Checking cache:', p_obj.name)
                            interval_obj = timer()
                            check_update_cache(p_cls_mgr, p_obj)
                            Log.debug('Check cache completed:', p_obj.name, timer() - interval_obj)
                        _do_add_draw_handler(p_cls_mgr, context)

                        context.window_manager.modal_handler_add(self)
                        b_modal = True
                        elapsed = timer() - interval

                        ZBBQ_SceneConfigFunc.CbOnBBQOverlayOn()

                        bpy.context.scene.ZBBQ_ZenBBQOverlayShow = True  # Need to storee this for furter use on scene load/addon init
                        Log.debug('ZBBQ_OT_DrawHighlight - ON:', elapsed)
                else:
                    if self.mode != 'ON':
                        _do_remove_draw_handler(p_cls_mgr.id_group, context)

                        ZBBQ_SceneConfigFunc.CbOnBBQOverlayOff()

                        bpy.context.scene.ZBBQ_ZenBBQOverlayShow = False  # Need to storee this for furter use on scene load/addon init
                        Log.debug('ZBBQ_OT_DrawHighlight - OFF')

                return {'RUNNING_MODAL'} if b_modal else {'CANCELLED'}

        return {'CANCELLED'}

    @classmethod
    def InvokeManually(cls, mode):
        op = eval("bpy.ops."+cls.bl_idname)
        if op.poll():
            op('INVOKE_DEFAULT', mode=mode)


classes = (

    ZBBQ_OT_FixSceneUnitSystem,
    ZBBQ_OT_RenderPreviewToggle,
    ZBBQ_OT_BakeNormalForSelection,

    ZBBQ_OT_ActiveObjectGetReady,

    ZBBQ_OT_ShaderNodeNormalAdd,
    ZBBQ_OT_ShaderNodeNormalRemove,
    ZBBQ_OT_ShaderNodeNormalToggle,

    ZBBQ_OT_SetBevelRadiusToSelection,
    ZBBQ_OT_SetZeroBevelRadiusToSelection,
    ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts,

    ZBBQ_OT_PresetsPresetGroupAdd,
    ZBBQ_OT_PresetsPresetGroupRemove,
    ZBBQ_OT_PresetsPresetGroupImportFromScene,
    # ZBBQ_OT_PresetsPresetGroupOrderChange,
    ZBBQ_OT_PresetsPresetOrderChange,

    ZBBQ_OT_SmartSelectByRadiusFromActivePreset,

    ZBBQ_OT_PreviewShaderNodeToggle,

    ZBBQ_OT_TestOpA,
    ZBBQ_OT_TestOpB,

    ZBBQ_OT_DrawHighlight,

    ZBBQ_OT_PieMenuGeometryOptionsTop,
    ZBBQ_OT_PieMenuGeometryOptionsBottom,

    ZBBQ_OT_MaterialsRepair,
    ZBBQ_OT_ObjectAddonCleanup,
    ZBBQ_OT_GlobalAddonCleanup,
    ZBBQ_OT_Keymaps,
    ZBBQ_OT_ResetPreferences
)


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
