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


import bpy
from bpy.props import BoolProperty
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.mark_utils import MarkStateManager
from ZenUV.utils.vlog import Log


def get_zen_unwrap_addon_prefs():
    """ Return Zen UV Properties obj """
    return bpy.context.preferences.addons[ZuvLabels.ADDON_NAME].preferences.op_zen_unwrap_props


def get_zen_unwrap_sc_prefs():
    """ Return Zen UV Properties obj """
    return bpy.context.preferences.addons[ZuvLabels.ADDON_NAME].preferences.op_zen_unwrap_props


class ZenUnwrapProps:

    def __init__(self, context) -> None:
        addon_level_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences.op_zen_unwrap_props
        global_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        scene_level_props = context.scene.zen_uv.op_zen_unwrap_sc_props

        # Scene level Properties
        self.Mark = scene_level_props.MarkUnwrapped
        self.ProcessingMode = scene_level_props.ProcessingMode
        self.Pack = scene_level_props.packAfUnwrap
        self.AveragedTd = scene_level_props.averaged_td

        self.fill_holes = scene_level_props.fill_holes
        self.correct_aspect = scene_level_props.correct_aspect

        # Global Zen UV Properties
        self.UnwrapMethod = global_prefs.UnwrapMethod
        self.PackMargin = global_prefs.margin
        self.KeepStacks = global_prefs.lock_overlapping_mode
        self.PackEngine = global_prefs.packEngine

        # Addon Level Prefs
        self.ActivateSyncUV = addon_level_prefs.autoActivateUVSync
        self.TagFinished = addon_level_prefs.autoTagFinished
        self.SortFinished = addon_level_prefs.unwrapAutoSorting


class ZuvMessage:

    def __init__(self, _type='INFO', message="Generic Message", state=False) -> None:
        self.Mtype = _type
        self.message = message
        self.state = state
        self.ret = {'PASS_THROUGH'}


class ZenUnwrapState:

    def __init__(self, context, objs) -> None:
        # objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        # self.objs = resort_objects(context, objs)
        self.result = ZuvMessage()
        self.PROPS = ZenUnwrapProps(context)

        self.sync_mode = True
        self.update_sync_mode(context)

        self.mSeam, self.mSharp = MarkStateManager(context).get_state()

        # Local Operator Variables
        self.objs_init_count = len(objs)
        self.objs_count = len(objs)

        self.selection_exist = True in [obj.sel_exist for obj in objs]

        self.seams_exist = True in [obj.seam_exist for obj in objs]
        self.bl_selection_mode = self._get_bl_selection_mode(context)
        self.bl_live_unwrap = context.scene.tool_settings.use_edge_path_live_unwrap

        self.operator_mode = "DEFAULT"
        self.one_by_one = False
        self.skip_warning = False

        # Operator Processing Mode (OPM)
        self.OPM = self._detect_opm(context)
        self.fit_view = 'all'
        self.finished_came_across = False

        if not objs:
            self.result = self.report('WARNING', "Zen UV: Select something.", False)

    def is_sorting_allowed(self):
        return not self.PROPS.ProcessingMode == 'SEL_ONLY' and self.PROPS.SortFinished and self.PROPS.PackEngine == "BLDR"

    def update_sync_mode(self, context):
        sync_uv = context.scene.tool_settings.use_uv_select_sync
        self.sync_mode = context.space_data.type == 'IMAGE_EDITOR' and sync_uv or context.space_data.type == 'VIEW_3D'

    def set_selected_only(self, context, state):
        scene_level_props = context.scene.zen_uv.op_zen_unwrap_sc_props
        scene_level_props.ProcessingMode = state
        self.PROPS.ProcessingMode = state

    def is_all_with_seams(self, objs):
        Log.debug("Seam Exist all objects -->", [obj.seam_exist for obj in objs])
        return False not in [obj.seam_exist for obj in objs]

    def is_all_ready_to_unwrap(self, objs):
        Log.debug("All Ready to Unwrap -->", False not in [obj.ready_to_unwrap for obj in objs])
        return False not in [obj.ready_to_unwrap for obj in objs]

    def update_seams_exist(self, objs):
        for obj in objs:
            obj.update_seam_exist()
        self.seams_exist = True in [obj.seam_exist for obj in objs]

    def show_state(self):
        Log.debug_header_short(" The State ")
        Log.debug(f"\nOPM --> {self.OPM}")
        Log.debug(f"\tSel Only --> {self.PROPS.ProcessingMode}")
        Log.debug_header_short(" The End ")

    def set_operator_mode(self, action):
        modes_set = {'DEFAULT', 'AUTO', "CONTINUE", "LIVE_UWRP"}
        if action in modes_set:
            self.operator_mode = action
        else:
            Log.debug(f"WARNING !!! Operator Mode incorrect. Not in {modes_set} Current Value is {action}\n" * 5)

    def set_opm(self, mode):
        if mode in {'ALL', 'SELECTION'}:
            self.OPM = mode

    def _detect_opm(self, context):
        if self.PROPS.ProcessingMode == "SEAM_SWITCH":
            scene_level_props = context.scene.zen_uv.op_zen_unwrap_sc_props
            scene_level_props.averaged_td = False
        if self.selection_exist and not self.PROPS.ProcessingMode == "SEAM_SWITCH":
            return 'SELECTION'
        else:
            return 'ALL'

    def _get_bl_selection_mode(self, context):
        if context.tool_settings.mesh_select_mode[:] == (False, True, False):
            return 'EDGE'
        elif context.tool_settings.mesh_select_mode[:] == (False, False, True):
            return 'FACE'
        return 'VERTEX'

    def report(self, _type='INFO', message="Generic Message", state=False):
        return ZuvMessage(_type, message, state)

    def is_pack_allowed(self):
        if self.PROPS.ProcessingMode == 'SEL_ONLY':
            return False
        if self.PROPS.Pack:
            return True
        else:
            return False

    def is_avg_td_allowed(self, td_inputs):
        return self.PROPS.AveragedTd and td_inputs.td > 1 and not self.is_pack_allowed()


class LiveUnwrapPropManager:

    show_errors = True

    state_attrs = {
        'mSeam': False,
        'mSharp': False,
        'OPM': 'ALL',
        'skip_warning': True,
        'test': "uuu"
    }
    props_attrs = {
        'Mark': False,
        'Pack': True,
        'fill_holes': True,
    }

    attrs_storage = {}

    @classmethod
    def store_props(cls, state: ZenUnwrapState) -> None:
        Log.debug_header(' Storing Attributes ')

        # cls._show_all_current_attrs(state, ' Before Storing ')

        cls._store_attrs(state, cls.state_attrs)
        cls._store_attrs(state.PROPS, cls.props_attrs)

    @classmethod
    def set_live_unwrap_preset(cls, state: ZenUnwrapState) -> None:
        Log.debug_header("Set Live Unwrap Preset")
        # cls._show_all_current_attrs(state, 'Before Set Live Unwrap Preset')

        cls._set_live_preset(state, cls.state_attrs)
        cls._set_live_preset(state.PROPS, cls.props_attrs)

        # cls._show_all_current_attrs(state, 'After Set Live Unwrap Preset')

    @classmethod
    def restore_props(cls, state: ZenUnwrapState) -> None:
        Log.debug_header("Restore Props")
        cls._restore_attrs(state, cls.state_attrs)
        cls._restore_attrs(state.PROPS, cls.props_attrs)

        # cls._show_all_current_attrs(state, 'After Restoring')

    @classmethod
    def _store_attrs(cls, _class: type, attr_container: dict) -> None:
        for attr in attr_container.keys():
            value = cls._is_attr_in_class(_class, attr)
            if value is not None:
                cls.attrs_storage.update({attr: value})

    @classmethod
    def _set_live_preset(cls, _class: type, attr_container: dict) -> None:
        for attr, value in attr_container.items():
            test_value = cls._is_attr_in_class(_class, attr)
            if test_value is not None:
                setattr(_class, attr, value)

    @classmethod
    def _restore_attrs(cls, _class: type, attr_container: dict) -> None:
        for attr in attr_container.keys():
            value = cls._is_attr_in_class(_class, attr)
            if value is not None:
                setattr(_class, attr, cls.attrs_storage[attr])

    @classmethod
    def _is_attr_in_class(cls, _class: type, attr: str) -> any:
        ''' Return attribute value or None if attribute is not exist '''
        value = getattr(_class, attr, None)
        if value is None:
            if cls.show_errors:
                Log.debug(f"ERROR --> Attribute ( {attr} ) not in class {cls._get_class_name(_class)}\t\t <-- ERROR\n")
            return None
        else:
            return value

    @classmethod
    def _get_class_name(cls, _class: type):
        return str(_class.__class__).split('.')[-1][:-2]

    @classmethod
    def _show_attrs(cls, attrs: dict) -> None:
        for key, value in attrs.items():
            Log.debug(f"{key}: {value}")

    @classmethod
    def _show_all_current_attrs(cls, state: ZenUnwrapState, header: str = '') -> None:
        Log.debug_header_short(header)
        cls._show_current(state, cls.state_attrs)
        cls._show_current(state.PROPS, cls.props_attrs)

    @classmethod
    def _show_current(cls, _class: type, attr_container: dict) -> None:
        Log.debug_header_short(f" {cls._get_class_name(_class)} ")
        for attr in attr_container.keys():
            value = cls._is_attr_in_class(_class, attr)
            if value is not None:
                Log.debug(f"{attr}: {value}")


class ZUV_ZenUnwrapOpAddonProps(bpy.types.PropertyGroup):

    autoActivateUVSync: bpy.props.BoolProperty(
        name=ZuvLabels.PREF_AUTO_ACTIVATE_UV_SYNC_LABEL,
        description=ZuvLabels.PREF_AUTO_ACTIVATE_UV_SYNC_DESC,
        default=True)

    autoTagFinished: BoolProperty(
        name=ZuvLabels.PREF_AUTO_TAG_FINISHED_LABEL,
        description=ZuvLabels.PREF_AUTO_TAG_FINISHED_DESC,
        default=False)

    unwrapAutoSorting: BoolProperty(
        name=ZuvLabels.PREF_ZEN_UNWRAP_SORT_ISLANDS_LABEL,
        description=ZuvLabels.PREF_ZEN_UNWRAP_SORT_ISLANDS_DESC,
        default=False)

    # UnwrapMethod: bpy.props.EnumProperty(
    #     items=[
    #         ("ANGLE_BASED",
    #             ZuvLabels.PREF_UNWRAP_METHOD_ANGLE_LABEL,
    #             ZuvLabels.PREF_UNWRAP_METHOD_ANGLE_DESC),
    #         ("CONFORMAL",
    #             ZuvLabels.PREF_UNWRAP_METHOD_CONFORMAL_LABEL,
    #             ZuvLabels.PREF_UNWRAP_METHOD_CONFORMAL_DESC)],
    #     default="CONFORMAL")


class ZUV_ZenUnwrapOpSceneProps(bpy.types.PropertyGroup):

    MarkUnwrapped: BoolProperty(
        name=ZuvLabels.PREF_AUTO_SEAMS_WITH_UNWRAP_LABEL,
        description=ZuvLabels.PREF_AUTO_SEAMS_WITH_UNWRAP_DESC,
        default=True)

    ProcessingMode: bpy.props.EnumProperty(
        name='Processing Mode',
        items=[
            ("SEL_ONLY", "Selected Only", "Processing selection only."),
            ("WHOLE_MESH", "Whole Mesh", "Processing whole mesh."),
            ("SEAM_SWITCH", "Seam Switch", "Switch Seam Mode"),
            ("URP_VERTICES", "Unfold Vertices", "Processing Selected vertices only")],
        default="WHOLE_MESH",
    )

    packAfUnwrap: BoolProperty(
        name=ZuvLabels.PREF_PACK_AF_UNWRAP_LABEL,
        description=ZuvLabels.PREF_PACK_AF_UNWRAP_DESC,
        default=True)

    averaged_td: BoolProperty(
        name=ZuvLabels.PREF_ZEN_UNWRAP_AVG_TD_LABEL,
        description=ZuvLabels.PREF_ZEN_UNWRAP_AVG_TD_DESC,
        default=True)

    fill_holes: BoolProperty(
        name=ZuvLabels.PREF_ZEN_UNWRAP_FILL_HOLES_LABEL,
        description=ZuvLabels.PREF_ZEN_UNWRAP_FILL_HOLES_DESC,
        default=True)

    correct_aspect: BoolProperty(
        name=ZuvLabels.PREF_ZEN_UNWRAP_CORR_ASPECT_LABEL,
        description=ZuvLabels.PREF_ZEN_UNWRAP_CORR_ASPECT_DESC,
        default=True)

    def _is_avg_td_allowed(self):
        if self.ProcessingMode == "SEL_ONLY":
            return True
        return not self.ProcessingMode == "SEAM_SWITCH" and not self.packAfUnwrap

    def draw_zen_unwrap(self, layout, context):
        scene_level_props = context.scene.zen_uv
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        # op_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences.op_zen_unwrap_props
        switch_seam_mode = self.ProcessingMode == "SEAM_SWITCH"
        if context.tool_settings.mesh_select_mode[:] == (False, True, False):
            s_mode = "Edge"
            ico = 'EDGESEL'
        elif context.tool_settings.mesh_select_mode[:] == (False, False, True):
            s_mode = "Face"
            ico = 'FACESEL'
        else:
            s_mode = "Vertex"
            ico = 'VERTEXSEL'

        box = layout.box()
        row = box.row()
        row.split(factor=0.7, align=False)
        row.label(text="Select Mode: ")
        row.label(text=s_mode, icon=ico)

        row = box.row()
        # row.enabled = not switch_seam_mode
        row.split(factor=0.7, align=False)
        row.label(text="Processing Mode: ")
        row.prop(self, "ProcessingMode", text="")

        row = box.row()
        row.split(factor=0.7, align=False)
        row.label(text=ZuvLabels.PANEL_UNWRAP_METHOD_LABEL)
        row.prop(addon_prefs, 'UnwrapMethod', text='')

        box = layout.box()
        box.enabled = not self.ProcessingMode == "URP_VERTICES"

        mark_box = box.box()
        s_mark_settings = 'Mark Settings'
        s_mark_settings += ' (Global Mode)' if addon_prefs.useGlobalMarkSettings else ' (Local Mode)'
        mark_box.label(text=s_mark_settings)

        row = mark_box.row(align=True)
        row_mark = row.row(align=True)
        row_mark.enabled = not switch_seam_mode
        row_mark.prop(self, "MarkUnwrapped", text="Mark")

        if not addon_prefs.useGlobalMarkSettings:
            row_seam = row.row(align=False)
            row_sharp = row.row(align=False)
            row_seam.prop(scene_level_props, 'op_markSeamEdges', text="Seams")
            row_seam.enabled = not switch_seam_mode and self.MarkUnwrapped
            row_sharp.prop(scene_level_props, 'op_markSharpEdges', text="Sharp")
            row_sharp.enabled = self.MarkUnwrapped or switch_seam_mode

        box.prop(self, "fill_holes")

        row = box.row(align=True)
        row.enabled = self._is_avg_td_allowed()
        row.prop(self, "averaged_td")

        row = box.row()
        row.enabled = not self.ProcessingMode == 'SEL_ONLY'
        row.prop(self, "packAfUnwrap")

        # if not addon_prefs.packEngine == "UVP":
        box.prop(addon_prefs.op_zen_unwrap_props, 'unwrapAutoSorting')


ZenUnwrapProperties = (
    ZUV_ZenUnwrapOpAddonProps,
    ZUV_ZenUnwrapOpSceneProps
)
