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
from ZenUV.utils.hops_integration import show_uv_in_3dview
from ZenUV.ui.labels import ZuvLabels
from bpy.props import BoolProperty
from ZenUV.utils.generic import (
    check_selection_mode,
    collect_selected_objects_data,
    restore_selection,
    fit_uv_view,
    resort_by_type_mesh_in_edit_mode_and_sel
)
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.ui.pie import ZsPieFactory
from ZenUV.ops.pack_exclusion import PackExcludedFactory


class GenericPackerManager:

    def __init__(self, context, addon_prefs) -> None:
        self.context = context
        self.addon_prefs = addon_prefs
        self.packer_parsed_props = {"generic": "generic"}
        self.packer_name = None
        self.stored_props = None
        self.packer_props_pointer = None
        self.show_transfer = False
        self.raise_popup = False

    def pack(self):
        return False

    def get_engine_version(self):
        return False

    # PROTECTED
    # this method must be overrided in all derived classes !!!
    def _engine_is_present(self):
        return False

    def _store_packer_props(self):
        self.stored_props = dict()
        for attr in self.packer_parsed_props.keys():
            try:
                self.stored_props.update({attr: getattr(self.packer_props_pointer, attr)})
            except Exception:
                self.stored_props = None

    def _restore_packer_props(self):
        for attr in self.packer_parsed_props.keys():
            try:
                setattr(self.packer_props_pointer, attr, self.stored_props[attr])
            except Exception:
                return False
        if self.show_transfer:
            print(f"\nRestored Packer Props: {self.stored_props}\n")
        return True

    def _is_attribute_real(self, attrib):
        if isinstance(attrib, str):
            if getattr(self.addon_prefs, attrib, "NOT_PASSED") == "NOT_PASSED":
                return False
            return True
        return False

    def _trans_props_zen_to_packer(self):
        for packer_attr, zuv_attr in self.packer_parsed_props.items():
            try:
                if self._is_attribute_real(zuv_attr):
                    if self.show_transfer:
                        print(f"attr type: {type(zuv_attr)}.\t{self.packer_name}: {packer_attr} -> {getattr(self.packer_props_pointer, packer_attr)}, Zen UV: {zuv_attr} -> {getattr(self.addon_prefs, zuv_attr, False)}")
                    setattr(self.packer_props_pointer, packer_attr, getattr(self.addon_prefs, zuv_attr))

                else:
                    if self.show_transfer:
                        print(f"attr type: {type(zuv_attr)}.\t{self.packer_name}: {packer_attr} -> {getattr(self.packer_props_pointer, packer_attr)}, Zen UV: {zuv_attr} -> {self.packer_parsed_props[packer_attr]}")
                    setattr(self.packer_props_pointer, packer_attr, zuv_attr)

            except Exception:
                if self.show_transfer:
                    print(f"\nError in: {packer_attr}. Value: {getattr(self.packer_props_pointer, packer_attr)}")
                    print(f"\t\t{self.packer_name}: {packer_attr}, Zen UV: {zuv_attr}: {getattr(self.addon_prefs, zuv_attr, 'UNDEFINED')}, Type: {type(zuv_attr)}\n")


class UVPackerManager(GenericPackerManager):

    def __init__(self, context, addon_prefs) -> None:
        GenericPackerManager.__init__(self, context, addon_prefs)
        self.packer_parsed_props = {
            "uvp_width": "TD_TextureSizeX",
            "uvp_height": "TD_TextureSizeY",
            "uvp_rescale": "averageBeforePack",
            "uvp_prerotate": "rotateOnPack",
            "uvp_rotate": None,
            "uvp_padding": None
        }
        self.packer_name = "UV-Packer"
        self.show_transfer = False

    def _engine_is_present(self):
        if hasattr(bpy.types, bpy.ops.uvpackeroperator.packbtn.idname()):
            if hasattr(self.context.scene, "UVPackerProps") and hasattr(self.context.scene.UVPackerProps, "uvp_padding"):
                if self.show_transfer:
                    print("Engine present. Props Pointer created.")
                self.packer_props_pointer = self.context.scene.UVPackerProps
                return True
        return False

    def pack(self):

        if not self._engine_is_present():
            self.raise_popup = True
            return False, f"Nothing is produced. Seems like {self.packer_name} is not installed on your system."

        self._store_packer_props()

        # Setting additional Packer Properties
        self.packer_parsed_props["uvp_rotate"] = self.context.scene.UVPackerProps.uvp_rotate
        if not self.addon_prefs.rotateOnPack:
            self.packer_parsed_props["uvp_rotate"] = "0"
        self.packer_parsed_props["uvp_padding"] = self.context.scene.zen_uv.pack_uv_packer_margin

        self._trans_props_zen_to_packer()

        if bpy.ops.uvpackeroperator.packbtn.poll():
            bpy.ops.uvpackeroperator.packbtn('INVOKE_DEFAULT')
        else:
            self._restore_packer_props()
            return False, f"For some reason, {self.packer_name} cannot be launched. Check out its performance separately from Zen UV."

        restored = self._restore_packer_props()

        if not restored:
            return False, f"The properties of the {self.packer_name} are not restored."

        return True, "Finished"


class UVPMmanager(GenericPackerManager):

    def __init__(self, context, addon_prefs) -> None:
        GenericPackerManager.__init__(self, context, addon_prefs)
        self.uvp_2_parsed_props = {
            "margin": "margin",
            "rot_enable": "rotateOnPack",
            "lock_overlapping_mode": "lock_overlapping_mode",
            "fixed_scale": "packFixedScale",
            "heuristic_enable": False,
            "normalize_islands": "averageBeforePack",
            "pack_to_others": False,
            "use_blender_tile_grid": False
        }

        self.uvp_3_parsed_props = {
            "margin": "margin",
            "rotation_enable": "rotateOnPack",
            "lock_overlapping_enable": "lock_overlapping_enable",
            "lock_overlapping_mode": "lock_overlapping_mode",
            "fixed_scale": "packFixedScale",
            "heuristic_enable": False,
            "normalize_islands": "averageBeforePack",
            # "pack_to_others": False,
            "use_blender_tile_grid": False
        }
        self.uvpm_version = None
        self.packer_name = "UV Packmaster"
        self.show_transfer = False
        self.disable_overlay = False

    def get_engine_version(self):
        if hasattr(self.context.scene, "uvp2_props"):
            self.packer_parsed_props = self.uvp_2_parsed_props
            self.packer_props_pointer = self.context.scene.uvp2_props
            self.uvpm_version = 2
            return self.uvpm_version

        elif hasattr(self.context.scene, "uvpm3_props"):
            self.packer_parsed_props = self.uvp_3_parsed_props
            self.packer_props_pointer = self.context.scene.uvpm3_props
            self.uvpm_version = 3
            return self.uvpm_version

        else:
            return None

    def transfer_attrs_to_uvpm(self):
        self._trans_props_zen_to_packer()

    def pack(self):

        ZsPieFactory.mark_pie_cancelled()

        if not self.get_engine_version():
            self.raise_popup = True
            return False, self.rise_message("engine_not_present")

        print(f"Zen UV: UVPMmanager: Pack Engine UV Packmaster {self.uvpm_version} detected.")

        if not self.packer_props_pointer:
            return False, self.rise_message("props_error")

        self._store_packer_props()

        if not self.stored_props:
            return False, self.rise_message("props_not_found")

        self._trans_props_zen_to_packer()

        if self.uvpm_version == 2 and bpy.ops.uvpackmaster2.uv_pack.poll():
            if self.disable_overlay:
                bpy.ops.uvpackmaster2.uv_pack()
            else:
                bpy.ops.uvpackmaster2.uv_pack("INVOKE_DEFAULT")

        elif self.uvpm_version == 3 and bpy.ops.uvpackmaster3.pack.poll():
            if self.disable_overlay:
                bpy.ops.uvpackmaster3.pack(mode_id=self.context.scene.zen_uv.uvp3_packing_method, pack_to_others=False)
            else:
                bpy.ops.uvpackmaster3.pack("INVOKE_DEFAULT", mode_id=self.context.scene.zen_uv.uvp3_packing_method, pack_to_others=False)

        else:
            self._restore_packer_props()
            return False, self.rise_message("poll_failed")

        restored = self._restore_packer_props()
        if not restored:
            return False, self.rise_message("restore_props_error")

        return True, self.rise_message("finished")

    def rise_message(self, err_type):
        messages = {
            "detected_engine": f"Zen UV: UVPMmanager: Pack Engine UV Packmaster {self.uvpm_version} detected.",
            "props_error": "Some Properties of UV Packmaster cannot be found. Update UV Packmaster to the latest version.",
            "restore_props_error": "Property restoring error.",
            "engine_not_present": "Nothing is produced. Seems like UV Packmaster is not installed on your system.",
            "props_not_found": "Not found properties of UVPackmaster",
            "finished": "Finished.",
            "err_finished": "Finished with Errors.",
            "poll_failed": "For some reason, UVPackmaster cannot be launched. Check out its performance separately from Zen UV.",
        }
        if err_type in messages.keys():
            out_message = f"Zen UV: {messages[err_type]}"
            if self.show_transfer:
                print(out_message)
        else:
            out_message = "Zen UV: UVPMmanager: Message is not classified."
            if self.show_transfer:
                print(out_message)

        return out_message


class ZUV_OT_Pack(bpy.types.Operator):
    bl_idname = "uv.zenuv_pack"
    bl_label = ZuvLabels.PACK_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.PACK_DESC

    display_uv: BoolProperty(
        name="Display UV",
        default=False,
        options={'HIDDEN'}
    )
    disable_overlay: BoolProperty(
        name="Disable Overlay",
        default=False,
        options={'HIDDEN'}
    )

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()

        addon_prefs = get_prefs()
        selection_mode = False
        current_engine = addon_prefs.packEngine

        bms = collect_selected_objects_data(context)
        work_mode = check_selection_mode(context)

        for obj in bms:
            if not selection_mode and bms[obj]['pre_selected_faces'] or bms[obj]['pre_selected_edges']:
                selection_mode = True

        blender_sync_mode = context.scene.tool_settings.use_uv_select_sync
        context.scene.tool_settings.use_uv_select_sync = True

        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}
        PEF = PackExcludedFactory()
        PEF.hide_by_facemap(context, objs)

        if current_engine == "UVP":
            print("Zen UV - Pack: UV Packmaster Engine activated.")
            bpy.ops.mesh.select_all(action='SELECT')
            packer = UVPMmanager(context, addon_prefs)
            packer.disable_overlay = self.disable_overlay
            result, message = packer.pack()
            raise_popup = packer.raise_popup
            bpy.ops.mesh.select_all(action='DESELECT')

        elif current_engine == "BLDR":
            print("Zen UV - Pack: Blender Engine activated.")
            bpy.ops.mesh.select_all(action='SELECT')
            result, message = self.blen_start(addon_prefs)
            bpy.ops.mesh.select_all(action='DESELECT')

        elif current_engine == "UVPACKER":
            print("Zen UV - Pack: UV-Packer Engine activated.")
            packer = UVPackerManager(context, addon_prefs)
            result, message = packer.pack()
            raise_popup = packer.raise_popup

        else:
            result = False
            message = "Zen UV: There is no selected Engine for packing."

        if not result:
            PEF.unhide_by_stored(context)
            PEF.restore_selection(context)
            self.report({'WARNING'}, message)
            if raise_popup:
                if current_engine == "UVP":
                    bpy.ops.wm.call_menu(name="ZUV_MT_ZenPack_Uvp_Popup")
                if current_engine == "UVPACKER":
                    bpy.ops.wm.call_menu(name="ZUV_MT_ZenPack_Uvpacker_Popup")
            return {'CANCELLED'}

        print(message)

        context.scene.tool_settings.use_uv_select_sync = blender_sync_mode

        if selection_mode:
            for obj in bms:
                restore_selection(
                    work_mode,
                    bms[obj]['pre_selected_faces_index'],
                    bms[obj]['pre_selected_edges_index'],
                    verts=bms[obj]['pre_selected_verts_index'],
                    indexes=True,
                    bm=bms[obj]["data"]
                )
                bms[obj]["data"].select_flush_mode()

        PEF.unhide_by_stored(context)
        PEF.restore_selection(context)

        fit_uv_view(context, mode="all")

        if self.display_uv:
            # Display UV Widget from HOPS addon
            show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=False)

        return {'FINISHED'}

    def blen_start(self, addon_prefs):
        if addon_prefs.averageBeforePack:
            bpy.ops.uv.average_islands_scale()
        try:
            corrected_margin = addon_prefs.margin * 2.95
            # print(f"Margin: {corrected_margin}% = {addon_prefs.margin_px} px")
            # self.report({'INFO'}, f"Margin: {corrected_margin}")
            bpy.ops.uv.pack_islands(rotate=addon_prefs.rotateOnPack, margin=corrected_margin)
        except Exception:
            _message = "Zen UV: Potential Crash in Blender Pack process. \
                Try to clean up geometry."
            return False, _message
        return True, "Zen UV: Pack Finished"


class ZUV_OT_SyncZenUvToUVP(bpy.types.Operator):
    bl_idname = "uv.zenuv_sync_to_uvp"
    bl_label = ZuvLabels.OT_SYNC_TO_UVP_LABEL
    bl_description = ZuvLabels.OT_SYNC_TO_UVP_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        addon_prefs = get_prefs()
        current_engine = addon_prefs.packEngine

        if current_engine == "UVP":
            print("Zen UV: UV Packmaster Engine detected")
            packer = UVPMmanager(context, addon_prefs)
            if not packer.get_engine_version():
                return {'CANCELLED'}
            packer.transfer_attrs_to_uvpm()
        else:
            bpy.ops.wm.call_menu(name="ZUV_MT_ZenPack_Uvp_Popup")
            return {'CANCELLED'}
        return {'FINISHED'}


pack_classes = (
    ZUV_OT_Pack,
    ZUV_OT_SyncZenUvToUVP,
)


if __name__ == '__main__':
    pass
