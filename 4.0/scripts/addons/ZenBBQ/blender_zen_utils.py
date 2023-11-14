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

# Copyright 2021, Alex Zhornyak

""" Zen Blender Utils """
import bpy

import ctypes
import platform
import re

from enum import IntEnum

from .vlog import Log

_ATTR_DEPSGRAPH_UPDATE_LOCK = 'zen_sets_depsgraph_update_lock'
_ATTR_DEPSGRAPH_UPDATE_ONE_LOCK = 'zen_sets_depsgraph_update_one_lock'
_ATTR_LAY_COL_UPDATE_ONE_LOCK = 'zen_sets_lay_col_update_one_lock'
_ATTR_NOTIFY_EDIT_LOCK = 'zen_sets_notify_edit_lock'
_ATTR_SCENE_GROUP_INDEX_LOCK = 'zen_sets_index_lock'
_ATTR_LOOKUP_BUILD_LOCK = 'zen_sets_lookup_build_lock'


_ATTR_OBJ_COLOR_STATE = 'zen_sets_object_color_state'


class ZenLocks:
    @staticmethod
    def is_depsgraph_update_locked():
        return (_ATTR_DEPSGRAPH_UPDATE_LOCK in bpy.app.driver_namespace.keys()) \
                and bpy.app.driver_namespace[_ATTR_DEPSGRAPH_UPDATE_LOCK]

    @staticmethod
    def lock_depsgraph_update():
        bpy.app.driver_namespace[_ATTR_DEPSGRAPH_UPDATE_LOCK] = True

    @staticmethod
    def unlock_depsgraph_update():
        bpy.app.driver_namespace[_ATTR_DEPSGRAPH_UPDATE_LOCK] = False

    @staticmethod
    def is_depsgraph_update_one_locked():
        return (_ATTR_DEPSGRAPH_UPDATE_ONE_LOCK in bpy.app.driver_namespace.keys()) \
                and bpy.app.driver_namespace[_ATTR_DEPSGRAPH_UPDATE_ONE_LOCK]

    @staticmethod
    def lock_depsgraph_update_one():
        bpy.app.driver_namespace[_ATTR_DEPSGRAPH_UPDATE_ONE_LOCK] = True

    @staticmethod
    def unlock_depsgraph_update_one():
        bpy.app.driver_namespace[_ATTR_DEPSGRAPH_UPDATE_ONE_LOCK] = False

    @staticmethod
    def is_lay_col_update_one_locked():
        return (_ATTR_LAY_COL_UPDATE_ONE_LOCK in bpy.app.driver_namespace.keys()) \
                and bpy.app.driver_namespace[_ATTR_LAY_COL_UPDATE_ONE_LOCK]

    @staticmethod
    def lock_lay_col_update_one():
        bpy.app.driver_namespace[_ATTR_LAY_COL_UPDATE_ONE_LOCK] = True

    @staticmethod
    def unlock_lay_col_update_one():
        bpy.app.driver_namespace[_ATTR_LAY_COL_UPDATE_ONE_LOCK] = False

    @staticmethod
    def is_notify_edit_locked():
        return (_ATTR_NOTIFY_EDIT_LOCK in bpy.app.driver_namespace.keys()) \
                and bpy.app.driver_namespace[_ATTR_NOTIFY_EDIT_LOCK]

    @staticmethod
    def lock_notify_edit():
        bpy.app.driver_namespace[_ATTR_NOTIFY_EDIT_LOCK] = True

    @staticmethod
    def unlock_notify_edit():
        bpy.app.driver_namespace[_ATTR_NOTIFY_EDIT_LOCK] = False

    @staticmethod
    def is_lookup_build_locked():
        return (_ATTR_LOOKUP_BUILD_LOCK in bpy.app.driver_namespace.keys()) \
                and bpy.app.driver_namespace[_ATTR_LOOKUP_BUILD_LOCK]

    @staticmethod
    def lock_lookup_build():
        bpy.app.driver_namespace[_ATTR_LOOKUP_BUILD_LOCK] = True

    @staticmethod
    def unlock_lookup_build():
        bpy.app.driver_namespace[_ATTR_LOOKUP_BUILD_LOCK] = False

    @staticmethod
    def is_group_index_locked(id_group):
        return ((_ATTR_SCENE_GROUP_INDEX_LOCK + id_group) in bpy.app.driver_namespace.keys()) \
                and bpy.app.driver_namespace[_ATTR_SCENE_GROUP_INDEX_LOCK + id_group]

    @staticmethod
    def lock_group_index(id_group):
        bpy.app.driver_namespace[_ATTR_SCENE_GROUP_INDEX_LOCK + id_group] = True

    @staticmethod
    def unlock_group_index(id_group):
        bpy.app.driver_namespace[_ATTR_SCENE_GROUP_INDEX_LOCK + id_group] = False


class ZenStates:
    @staticmethod
    def set_obj_color_state():
        bpy.app.driver_namespace[_ATTR_OBJ_COLOR_STATE] = True

    @staticmethod
    def unset_obj_color_state():
        bpy.app.driver_namespace[_ATTR_OBJ_COLOR_STATE] = False

    @staticmethod
    def is_obj_color_state():
        return (_ATTR_OBJ_COLOR_STATE in bpy.app.driver_namespace.keys()) \
                and bpy.app.driver_namespace[_ATTR_OBJ_COLOR_STATE]


class ZsViewLayerStoredType(IntEnum):
    HideSelect = 0,
    HideViewport = 1,
    HideGet = 2,
    SelectGet = 3,
    WasEditable = 4


def save_viewlayer_layers_state(parent_layer, layers_state):
    for child_layer in parent_layer.children:
        layers_state[child_layer.name] = (child_layer.exclude, child_layer.hide_viewport)
        save_viewlayer_layers_state(child_layer, layers_state)


def show_all_viewlayers(parent_layer):
    for child_layer in parent_layer.children:
        child_layer.exclude = False
        child_layer.hide_viewport = False
        show_all_viewlayers(child_layer)


def restore_viewlayer_layers(parent_layer, layers_state):
    for child_layer in parent_layer.children:
        if child_layer.name in layers_state:
            is_excluded, is_viewport_hidden = layers_state[child_layer.name]
            if child_layer.exclude != is_excluded:
                child_layer.exclude = is_excluded
            if child_layer.hide_viewport != is_viewport_hidden:
                child_layer.hide_viewport = is_viewport_hidden
        restore_viewlayer_layers(child_layer, layers_state)


def save_viewlayer_objects_state():
    view_layer = bpy.context.view_layer
    act_obj_name = view_layer.objects.active.name if view_layer.objects.active else ''
    were_objects = {obj.name: (obj.hide_select,
                               obj.hide_viewport,
                               obj.hide_get(),
                               obj.select_get(),
                               obj.data.is_editmode if obj.type == 'MESH' else (act_obj_name == obj.name))
                    for obj in view_layer.objects}
    return (were_objects, act_obj_name)


def restore_viewlayer_objects(were_objects):
    obj_list = bpy.context.view_layer.objects
    for obj_name, obj_data in were_objects.items():
        obj = obj_list.get(obj_name)
        if obj:
            if obj.hide_get() != obj_data[ZsViewLayerStoredType.HideGet]:
                obj.hide_set(obj_data[ZsViewLayerStoredType.HideGet])

            if obj.hide_select != obj_data[ZsViewLayerStoredType.HideSelect]:
                obj.hide_select = obj_data[ZsViewLayerStoredType.HideSelect]
            if obj.hide_viewport != obj_data[ZsViewLayerStoredType.HideViewport]:
                obj.hide_viewport = obj_data[ZsViewLayerStoredType.HideViewport]

            if obj.select_get() != obj_data[ZsViewLayerStoredType.SelectGet]:
                obj.select_set(obj_data[ZsViewLayerStoredType.SelectGet])
        else:
            Log.error('Can not restore:', obj_name)


def ensure_object_in_viewlayer(obj, parent_layer):
    for child_layer in parent_layer.children:
        if obj.name in child_layer.collection.objects:
            child_layer.exclude = False
            child_layer.hide_viewport = False

        ensure_object_in_viewlayer(obj, child_layer)


def unhide_and_select_all_viewlayer_objects(act_obj_name):
    view_layer = bpy.context.view_layer
    for obj in view_layer.objects:
        if obj.type == 'MESH':
            obj.hide_viewport = False
            obj.hide_select = False
            obj.hide_set(False)
            obj.select_set(True)
        if obj.name == act_obj_name:
            view_layer.objects.active = obj


def prepare_stored_objects_for_edit(were_objects, act_obj_name):
    view_layer = bpy.context.view_layer
    for obj in view_layer.objects:
        if obj.name in were_objects:
            was_in_edit_mode = were_objects[obj.name][ZsViewLayerStoredType.WasEditable]
            if was_in_edit_mode:
                try:
                    obj.hide_viewport = False
                    obj.hide_select = False
                    obj.hide_set(False)
                    obj.select_set(True)
                except Exception:
                    pass
            else:
                try:
                    obj.hide_viewport = were_objects[obj.name][ZsViewLayerStoredType.HideViewport]
                    obj.hide_select = were_objects[obj.name][ZsViewLayerStoredType.HideSelect]
                    obj.hide_set(were_objects[obj.name][ZsViewLayerStoredType.HideGet])
                    obj.select_set(False)
                except Exception:
                    pass

        if obj.name == act_obj_name:
            view_layer.objects.active = obj


class ZenModeSwitcher:
    def __init__(self, mode='OBJECT'):
        self.were_objects, self.act_obj_name = save_viewlayer_objects_state()
        ctx_mode = bpy.context.mode
        if ctx_mode == 'OBJECT':
            self.was_mode = 'OBJECT'
        else:
            self.was_mode = 'EDIT'
        if mode != self.was_mode:
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode=mode)

    def return_to_edit_mode(self):
        prepare_stored_objects_for_edit(self.were_objects, self.act_obj_name)
        bpy.ops.object.mode_set(mode='EDIT')
        restore_viewlayer_objects(self.were_objects)

    def return_to_mode(self):
        if self.was_mode == 'EDIT':
            prepare_stored_objects_for_edit(self.were_objects, self.act_obj_name)
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode=self.was_mode)
        restore_viewlayer_objects(self.were_objects)


def fix_undo_push_edit_mode(msg):
    try:
        ZenLocks.lock_depsgraph_update()

        active_object = bpy.context.view_layer.objects.active
        if active_object and active_object.mode == "EDIT":
            try:
                ZenLocks.lock_notify_edit()
                mode_switcher = ZenModeSwitcher()

                bpy.ops.mesh.primitive_cube_add(enter_editmode=False)
                bpy.ops.object.delete(use_global=True, confirm=False)

                bpy.ops.object.select_all(action='DESELECT')

                mode_switcher.return_to_edit_mode()
            except Exception as e:
                Log.error('FIX_UNDO:', e)

        bpy.ops.ed.undo_push(message=msg)
    finally:
        ZenLocks.unlock_depsgraph_update()
    pass


def view_selected_in_center():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            ctx = bpy.context.copy()
            ctx['area'] = area
            ctx['region'] = area.regions[-1]
            bpy.ops.view3d.view_selected(ctx)


def update_view3d_in_all_screens():
    context = bpy.context

    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def is_property_modified(obj_prop):
    for prop in obj_prop.bl_rna.properties:
        if hasattr(prop, "default"):
            is_array = getattr(prop, "is_array", False)
            if is_array:
                default_array = [p for p in prop.default_array]
                current_value = [p for p in getattr(obj_prop, prop.identifier)]
                if default_array != current_value:
                    return True
            else:
                current = getattr(obj_prop, prop.identifier)
                if current != prop.default:
                    return True
    return False


def reset_property_modified(obj_prop):
    for prop in obj_prop.bl_rna.properties:
        if hasattr(prop, "default"):
            is_array = getattr(prop, "is_array", False)
            if is_array:
                cur_array = getattr(obj_prop, prop.identifier)

                default_values = [(i, p) for i, p in enumerate(prop.default_array)]
                current_values = [(i, p) for i, p in enumerate(cur_array)]
                if default_values != current_values:
                    if len(default_values) == len(current_values):
                        for i, p in default_values:
                            cur_array[i] = p
            else:
                current = getattr(obj_prop, prop.identifier)
                if current != prop.default:
                    setattr(obj_prop, prop.identifier, prop.default)


def get_operator_attr(op_name, attr_name, default=None):
    wm = bpy.context.window_manager
    op_last = wm.operator_properties_last(op_name)
    if op_last:
        return getattr(op_last, attr_name)
    return default


def set_operator_attr(op_name, attr_name, value):
    wm = bpy.context.window_manager
    op_last = wm.operator_properties_last(op_name)
    if op_last:
        setattr(op_last, attr_name, value)


def ireplace(text, find, repl):
    return re.sub('(?i)' + re.escape(find), lambda m: repl, text)


def win_emulate_escape():
    try:
        if platform.system() == 'Windows':
            VK_ESCAPE = 0x1B
            ctypes.windll.user32.keybd_event(VK_ESCAPE)
    except Exception as e:
        Log.error('Can not emulate ESC!', e)


def dump_context_objects(context):
    def _dump_object(idx, p_obj, s_category):
        Log.debug('\tCategory:', s_category, '[', idx, ']:', p_obj.name)

    categories = (
        'visible_objects',
        'selectable_objects',
        'selected_objects',
        'editable_objects',
        'selected_editable_objects',
        'selected_editable_objects',
        'selected_editable_objects_unique_data'
    )

    for s_cat in categories:
        Log.debug('===========> Category:', s_cat, '<=============')
        for i, obj in enumerate(getattr(context, s_cat, [])):
            _dump_object(i, obj, s_cat)


class ZsDrawConstans:
    DEFAULT_VERT_ACTIVE_ALPHA = 60
    DEFAULT_VERT_INACTIVE_ALPHA = 40
    DEFAULT_VERT_ACTIVE_POINT_SIZE = 10
    DEFAULT_VERT_INACTIVE_POINT_SIZE = 6

    DEFAULT_EDGE_ACTIVE_ALPHA = 60
    DEFAULT_EDGE_INACTIVE_ALPHA = 40
    DEFAULT_EDGE_ACTIVE_LINE_WIDTH = 3
    DEFAULT_EDGE_INACTIVE_LINE_WIDTH = 2

    DEFAULT_FACE_ACTIVE_ALPHA = 60
    DEFAULT_FACE_INACTIVE_ALPHA = 20

    DEFAULT_OBJECT_ACTIVE_ALPHA = 40
    DEFAULT_OBJECT_INACTIVE_ALPHA = 20
    DEFAULT_OBJECT_COLLECTION_BOUNDBOX_WIDTH = 2
    DEFAULT_OBJECT_COLLECTION_LABEL_SIZE = 12


class ZsUiConstants:
    ZSTS_PANEL_CATEGORY = "Zen BBQ"
    ZSTS_REGION_TYPE = "UI"
    ZSTS_CONTEXT = "mesh_edit"
    ZSTS_SPACE_TYPE = "VIEW_3D"
