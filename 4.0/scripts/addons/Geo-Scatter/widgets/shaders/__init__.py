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

# (c) 2022 Jakub Uhlik

import os

shader_registry = {
    # NOTE: used in .widgets.widgets.ToolOverlay (obsolete, use grid overlay)
    'UI_OVERLAY': {'v': "ui_overlay.vert", 'f': "ui_overlay.frag", },
    # NOTE: used in .widgets.grid.SC5GridOverlay (obsolete as well, use `CHECKERBOARD` if need to be, it can scale with ui_scale)
    'GRID_OVERLAY': {'v': "grid_overlay.vert", 'f': "grid_overlay.frag", },
    'CHECKERBOARD': {'v': "checkerboard.vert", 'f': "checkerboard.frag", },
}
SHADER_DIRECTORY = os.path.dirname(__file__)


def load_shader_code(name):
    if(name not in shader_registry.keys()):
        raise TypeError("Unknown shader requested..")
    d = shader_registry[name]
    vf = d['v']
    ff = d['f']
    gf = None
    if('g' in d.keys()):
        gf = d['g']
    with open(os.path.join(SHADER_DIRECTORY, vf), mode='r', encoding='utf-8') as f:
        vs = f.read()
    with open(os.path.join(SHADER_DIRECTORY, ff), mode='r', encoding='utf-8') as f:
        fs = f.read()
    gs = None
    if(gf is not None):
        with open(os.path.join(SHADER_DIRECTORY, gf), mode='r', encoding='utf-8') as f:
            gs = f.read()
    return vs, fs, gs


classes = ()
