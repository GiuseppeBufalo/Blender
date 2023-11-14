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

""" Attempts to make something with Blender WindowManager progress """
import bpy


_ATTR_PROGRESS_LOCK = 'zen_sets_progress_lock'


def _is_progress_locked():
    return (
        _ATTR_PROGRESS_LOCK in bpy.app.driver_namespace.keys()) \
        and bpy.app.driver_namespace[_ATTR_PROGRESS_LOCK]


def start_progress(context, min=0, max=100, high_priority=False):
    if high_priority:
        bpy.app.driver_namespace[_ATTR_PROGRESS_LOCK] = True
    else:
        if _is_progress_locked():
            return

    context.window_manager.progress_begin(min, max)


def update_progress(context, val, high_priority=False):
    if high_priority is False and _is_progress_locked():
        return
    else:
        context.window_manager.progress_update(val)


def end_progress(context, high_priority=False):
    if high_priority:
        bpy.app.driver_namespace[_ATTR_PROGRESS_LOCK] = False
    else:
        if _is_progress_locked():
            return

    context.window_manager.progress_end()
