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
import blf
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
import functools


_handles = {}


class BGLMessageBox:
    def __init__(self, context, message):
        self.message = message

        self.handle = bpy.types.SpaceView3D.draw_handler_add(
                   self.draw_text_callback, (context,),
                   'WINDOW', 'POST_PIXEL')

    def draw_text_callback(self, context):
        font_id = 0

        area_width = context.area.width
        area_height = context.area.height

        i_font_size = 20

        blf.size(0, i_font_size, 72)
        text_width, text_height = blf.dimensions(0, self.message)

        i_width = int(text_width + text_width * 0.1)
        i_height = int(text_height * 4)

        i_x = (area_width * 0.1)
        i_y = int(area_height / 2 - i_height / 2)

        indices = ((0, 1, 2), (0, 2, 3))

        y_screen_flip = area_height - i_y

        # bottom left, top left, top right, bottom right
        vertices = (
                    (i_x, y_screen_flip),
                    (i_x, y_screen_flip - i_height),
                    (i_x + i_width, y_screen_flip - i_height),
                    (i_x + i_width, y_screen_flip))

        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

        shader.bind()
        shader.uniform_float("color", (0.0, 0.0, 0.0, 0.75))

        bgl.glEnable(bgl.GL_BLEND)
        batch.draw(shader)

        # draw some text
        blf.position(font_id, int(i_x + text_width * 0.05), int(y_screen_flip - text_height * 2.25), 0)
        blf.color(font_id, 1.0, 0.0, 0.0, 1)
        blf.draw(font_id, self.message)

        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

    def remove_handle(self):
        if self.handle:
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
            self.handle = None


def redraw_regions():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    region.tag_redraw()


def _enqueue_hide(id, free=False):
    global _handles
    if id in _handles:
        _handles[id].remove_handle()
        if free:
            del _handles[id]

        redraw_regions()

    return None


def show_overlay_messagebox(id, message, timeout=3.0):
    global _handles
    if id not in _handles:
        _handles[id] = BGLMessageBox(bpy.context, message)
        bpy.app.timers.register(functools.partial(_enqueue_hide, id, free=True), first_interval=timeout)


def cleanup_overlay_handles():
    global _handles
    for h in _handles:
        _enqueue_hide(h, free=False)
    _handles = {}
