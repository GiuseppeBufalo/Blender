'''
Copyright (C) 2015 Pistiwique, Pitiwazou
 
Created by Pistiwique, Pitiwazou
 
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
 
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
 
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import os
import bpy
import bpy.utils.previews
 
epm_icon_collections = {}
epm_icons_loaded = False
 
def load_icons():
    global epm_icon_collections
    global epm_icons_loaded
 
    if epm_icons_loaded: return epm_icon_collections["main"]
 
    custom_icons = bpy.utils.previews.new()
 
    icons_dir = os.path.join(os.path.dirname(__file__))

    custom_icons.load("icon_speedretopo", os.path.join(icons_dir, "speedretopo.png"), 'IMAGE')
    custom_icons.load("icon_align_to_x", os.path.join(icons_dir, "align_to_x.png"), 'IMAGE')
    custom_icons.load("icon_bsurface", os.path.join(icons_dir, "bsurface.png"), 'IMAGE')
    custom_icons.load("icon_gstretch", os.path.join(icons_dir, "gstretch.png"), 'IMAGE')
    custom_icons.load("icon_relax", os.path.join(icons_dir, "relax.png"), 'IMAGE')
    custom_icons.load("icon_space", os.path.join(icons_dir, "space.png"), 'IMAGE')
    custom_icons.load("icon_bridge", os.path.join(icons_dir, "bridge.png"), 'IMAGE')
    custom_icons.load("icon_continue", os.path.join(icons_dir, "continue.png"), 'IMAGE')
    custom_icons.load("icon_valid", os.path.join(icons_dir, "valid.png"), 'IMAGE')
    custom_icons.load("icon_update", os.path.join(icons_dir, "update.png"), 'IMAGE')
    custom_icons.load("icon_delete", os.path.join(icons_dir, "delete.png"), 'IMAGE')
    custom_icons.load("icon_gridfill", os.path.join(icons_dir, "gridfill.png"), 'IMAGE')
    custom_icons.load("icon_recalculate_normals_outside", os.path.join(icons_dir, "recalculate_normals_outside.png"), 'IMAGE')
    custom_icons.load("icon_recalculate_normals_inside", os.path.join(icons_dir, "recalculate_normals_inside.png"), 'IMAGE')
    custom_icons.load("icon_flip_normals", os.path.join(icons_dir, "flip_normals.png"), 'IMAGE')
    custom_icons.load("icon_clipping", os.path.join(icons_dir, "clipping.png"), 'IMAGE')
    custom_icons.load("icon_optimal_display", os.path.join(icons_dir, "optimal_display.png"), 'IMAGE')
    custom_icons.load("icon_color", os.path.join(icons_dir, "color.png"), 'IMAGE')
    custom_icons.load("icon_polybuild", os.path.join(icons_dir, "polybuild.png"), 'IMAGE')
    custom_icons.load("icon_vertex", os.path.join(icons_dir, "vertex.png"), 'IMAGE')
    custom_icons.load("icon_face", os.path.join(icons_dir, "face.png"), 'IMAGE')
    custom_icons.load("icon_curve", os.path.join(icons_dir, "curve.png"), 'IMAGE')
    custom_icons.load("icon_retopomt", os.path.join(icons_dir, "retopomt.png"), 'IMAGE')
    custom_icons.load("icon_decimate", os.path.join(icons_dir, "decimate.png"), 'IMAGE')
    custom_icons.load("icon_error", os.path.join(icons_dir, "error.png"), 'IMAGE')
    custom_icons.load("icon_quadriflow", os.path.join(icons_dir, "quadriflow.png"), 'IMAGE')

    custom_icons.load("icon_market", os.path.join(icons_dir, "market.png"), 'IMAGE')
    custom_icons.load("icon_artstation", os.path.join(icons_dir, "artstation.png"), 'IMAGE')
    custom_icons.load("icon_gumroad", os.path.join(icons_dir, "gumroad.png"), 'IMAGE')
    custom_icons.load("icon_youtube", os.path.join(icons_dir, "youtube.png"), 'IMAGE')
    custom_icons.load("icon_tutocom", os.path.join(icons_dir, "tutocom.png"), 'IMAGE')
    custom_icons.load("icon_discord", os.path.join(icons_dir, "discord.png"), 'IMAGE')
    custom_icons.load("icon_twitter", os.path.join(icons_dir, "twitter.png"), 'IMAGE')
    custom_icons.load("icon_web", os.path.join(icons_dir, "web.png"), 'IMAGE')
    custom_icons.load("icon_patreon", os.path.join(icons_dir, "patreon.png"), 'IMAGE')
    custom_icons.load("icon_facebook", os.path.join(icons_dir, "facebook.png"), 'IMAGE')
    custom_icons.load("icon_tipeee", os.path.join(icons_dir, "tipeee.png"), 'IMAGE')

    custom_icons.load("icon_fluent", os.path.join(icons_dir, "fluent.png"), 'IMAGE')

    epm_icon_collections["main"] = custom_icons
    epm_icons_loaded = True
 
    return epm_icon_collections["main"]
 
def speedretopo_clear_icons():
    global epm_icons_loaded
    for icon in epm_icon_collections.values():
        bpy.utils.previews.remove(icon)
    epm_icon_collections.clear()
    epm_icons_loaded = False
