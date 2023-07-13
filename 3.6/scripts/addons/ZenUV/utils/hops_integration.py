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
import bmesh
from ZenUV.utils.generic import (
    get_mesh_data,
    ensure_facemap,
    set_face_int_tag,
    remove_facemap,
    HOPS_SHOW_UV_FACEMAP_NAME,
)
import ZenUV.utils.get_uv_islands as island_util
from ZenUV.ui.labels import ZuvLabels


def draw_hops_popup(self, context):
    layout = self.layout
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    layout.label(text="It looks like HOps addon")
    layout.label(text="is not installed on your system.")
    layout.operator("wm.url_open",
                    text="Buy HOps addon",
                    icon="HELP").url = "https://gumroad.com/l/hardops"
    layout.separator()
    layout.label(text="To disable the notification ")
    layout.label(text="turn off option:")
    layout.prop(addon_prefs, "hops_uv_activate")


def show_hops_widget(context, use_selected_meshes, use_selected_faces, use_tagged_faces):
    for obj in context.objects_in_mode:
        me, bm = get_mesh_data(obj)
        bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        hops_show_uv_facemap = ensure_facemap(bm, HOPS_SHOW_UV_FACEMAP_NAME)
        int_tag = 1
        islands_for_process = island_util.get_island(context, bm, uv_layer)
        if not islands_for_process:
            islands_for_process = island_util.get_islands(context, bm)
            int_tag = 0
        set_face_int_tag(islands_for_process, hops_show_uv_facemap, int_tag=int_tag)
        bmesh.update_edit_mesh(me, loop_triangles=False)
    try:
        bpy.ops.hops.draw_uv_launcher(
            use_selected_meshes=use_selected_meshes,
            use_selected_faces=use_selected_faces,
            use_tagged_faces=use_tagged_faces,
            show_all_and_highlight_sel=True
        )
    except Exception:
        print("Zen UV: Hard Ops have no such attributes.")
        print("        Perhaps the Hard Ops version does not meet the requirements.")
        print("        The ability to display a UV widget is supported since Hard Ops 00987.")

    bpy.ops.object.mode_set(mode='EDIT')

    # Remove Facemap for display
    for obj in context.objects_in_mode:
        me, bm = get_mesh_data(obj)
        bm.faces.ensure_lookup_table()
        remove_facemap(bm, HOPS_SHOW_UV_FACEMAP_NAME)
        bmesh.update_edit_mesh(me, loop_triangles=False)


def show_uv_in_3dview(context, use_selected_meshes, use_selected_faces, use_tagged_faces):
    """
    Shows UV map in View 3D using HOPS module ops.hops.draw_uv_launcher
    Conditions: Image Editon not in areas and ops.hops.draw_uv_launcher is
    activated.
    """
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    if addon_prefs.hops_uv_activate:
        if not hasattr(bpy.types, bpy.ops.hops.draw_uv_launcher.idname()):
            context.window_manager.popup_menu(draw_hops_popup, title="Zen UV", icon='INFO')
        else:
            uv_editor_opened = 'IMAGE_EDITOR' in [area.type for area in context.screen.areas]
            show_widget_always = addon_prefs.hops_uv_context
            if show_widget_always:
                show_hops_widget(context, use_selected_meshes, use_selected_faces, use_tagged_faces)
            else:
                if not uv_editor_opened:
                    show_hops_widget(context, use_selected_meshes, use_selected_faces, use_tagged_faces)
