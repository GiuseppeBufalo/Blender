#
#     This file is part of NodePreview.
#     Copyright (C) 2021 Simon Wendsche
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy
from bpy.types import AddonPreferences
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, EnumProperty, BoolProperty
from bpy.utils import register_class, unregister_class

from os.path import basename, dirname


addon_name = basename(dirname(__file__))
THUMB_CHANNEL_COUNT = 4
SUPPORTED_NODE_TREE = "ShaderNodeTree"
addon_keymaps = []

bl_info = {
    "name": "Node Preview",
    "author": "Simon Wendsche (B.Y.O.B.)",
    "version": (1, 8),
    "blender": (2, 80, 0),
    "category": "Node",
    "location": "Shader Node Editor",
    "description": "Displays rendered thumbnails above shader nodes",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}


class UnsupportedNodeException(Exception):
    pass


def is_group_node(node):
    return hasattr(node, "node_tree") and (isinstance(node.node_tree, bpy.types.ShaderNodeTree) or node.node_tree is None)


def force_node_editor_draw():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "NODE_EDITOR":
                for region in area.regions:
                    if region.type == "WINDOW":
                        region.tag_redraw()


def needs_linking(image):
    return bool(image.packed_file) or image.source == "GENERATED"


class BACKGROUND_PATTERNS:
    CHECKER = "CHECKER"
    WHITE = "WHITE"


BG_COLOR_DESC = ("Visible when parts of a shader are transparent. Note that very dark or saturated background "
                 "colors can produce misleading results for thumbnails of colored transparent shaders")


class NodePreviewAddonPreferences(AddonPreferences):
    # Must be the addon directory name
    # (by default "NodePreview", but a user/dev might change the folder name)
    bl_idname = addon_name

    previews_enabled_by_default: BoolProperty(name="Previews Visible by Default", default=True,
                                              description="Choose wether the thumbnails should be visible by default or not. "
                                                          "If disabled, thumbnails are only shown after selecting nodes and "
                                                          "pressing Ctrl+Shift+P to make them visible")

    thumb_scale: FloatProperty(name="Thumbnail Scale", default=50, min=1, max=100,
                               subtype="PERCENTAGE")

    thumb_resolution: IntProperty(name="Thumbnail Resolution", default=150, min=50, soft_max=300, max=500,
                                  description="Higher resolutions preserve fine detail in textures better, but lead to slower updates")

    background_pattern_items = [
        (BACKGROUND_PATTERNS.CHECKER, "Checkerboard Pattern", "", 0),
        (BACKGROUND_PATTERNS.WHITE, "Solid Color", "", 1),
    ]
    background_pattern: EnumProperty(name="Background", items=background_pattern_items, default="CHECKER",
                                     description="The background pattern is visible when parts of a shader are transparent/transmissive")

    background_color_1: FloatVectorProperty(name="Background Color", default=(0.994, 0.994, 0.994), min=0, max=1, subtype="COLOR",
                                            description=BG_COLOR_DESC)
    background_color_2: FloatVectorProperty(name="Background Color", default=(0.8086, 0.8086, 0.8086), min=0, max=1, subtype="COLOR",
                                            description=BG_COLOR_DESC)

    show_help: BoolProperty(name="Show Help Messages", default=True,
                            description="Show the following help messages:\n"
                                        "- Procedural texture scale can be ignored with Ctrl+Shift+I (shown if texture scale is so large\n"
                                        "  that the texture is no longer recognizable, or if texture scale is driven by another texture")

    need_blender_restart = False
    def update_enable_debug_output(self, context):
        NodePreviewAddonPreferences.need_blender_restart = True

    enable_debug_output: BoolProperty(name="Enable Debug Output", default=False,
                                      update=update_enable_debug_output,
                                      description="Print debug information to the system console")

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "previews_enabled_by_default")

        row = layout.row()
        row.prop(self, "thumb_scale")
        row.prop(self, "thumb_resolution")

        row = layout.row()
        row.label(text="Background:")
        row.prop(self, "background_pattern", expand=True)

        using_checker_pattern = self.background_pattern == BACKGROUND_PATTERNS.CHECKER
        row = layout.row()
        row.label(text="")
        if using_checker_pattern:
            row.label(text="")
        row.prop(self, "background_color_1", text=("Color 1" if using_checker_pattern else "Color"))
        if using_checker_pattern:
            row.prop(self, "background_color_2", text="Color 2")

        layout.prop(self, "show_help")
        layout.prop(self, "enable_debug_output")
        if NodePreviewAddonPreferences.need_blender_restart:
            layout.label(text="Please restart Blender for the change to take effect", icon="ERROR")

        col = layout.column(align=True)
        col.label(text="Shortcuts:", icon="INFO")
        col.label(text="Ctrl+Shift+P: Toggle thumbnail visibility on selected nodes")
        col.label(text="Ctrl+Shift+i: Toggle wether to ignore the Scale socket on selected procedural texture nodes")


def poll_node_tree(context):
    space = context.space_data
    # Path contains a chain of nested node trees, the last one is the currently active one
    if not space.path:
        return False
    node_tree = space.path[-1].node_tree
    return space.type == "NODE_EDITOR" and node_tree and space.tree_type == SUPPORTED_NODE_TREE


class NODEPREVIEW_OT_toggle_preview(bpy.types.Operator):
    bl_idname = "nodepreview.toggle_preview"
    bl_label = "Toggle Node Previews"
    bl_description = "On selected nodes: Toggle visibility of the node preview thumbnail on/off"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_node_tree(context)

    def invoke(self, context, event):
        space = context.space_data
        node_tree = space.path[-1].node_tree
        preferences = context.preferences.addons[addon_name].preferences

        selection = [node for node in node_tree.nodes if node.select and hasattr(node, "node_preview")]
        # If at least one node has the preview enabled, this operator should switch them all off.
        # Only when all selected nodes have the preview disabled, switch them on.
        initial_state = any((node.node_preview.is_enabled(preferences) for node in selection))

        for node in selection:
            node.node_preview.enabled = not initial_state

        force_node_editor_draw()
        return {"FINISHED"}


class NODEPREVIEW_OT_toggle_ignore_scale(bpy.types.Operator):
    bl_idname = "nodepreview.toggle_ignore_scale"
    bl_label = "Toggle Ignore Scale"
    bl_description = ("On selected nodes: Toggle wether to ignore procedural texture scale when rendering the node preview "
                      "(useful on procedural textures like Musgrave, Voronoi, Noise etc.)")
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_node_tree(context)

    def invoke(self, context, event):
        space = context.space_data
        node_tree = space.path[-1].node_tree

        for node in node_tree.nodes:
            if node.select:
                node.node_preview.ignore_scale = not node.node_preview.ignore_scale

        force_node_editor_draw()
        return {"FINISHED"}


class NodePreviewNodeProps(bpy.types.PropertyGroup):
    def update_enabled(self, context):
        self.enabled_modified = True

    enabled: BoolProperty(default=True, update=update_enabled)
    enabled_modified: BoolProperty(default=False)
    ignore_scale: BoolProperty(default=False)

    def is_enabled(self, addon_preferences):
        if self.enabled_modified:
            return self.enabled
        else:
            return addon_preferences.previews_enabled_by_default

    force_update_counter: IntProperty(default=0, min=0)

    def force_update(self):
        try:
            self.force_update_counter += 1
        except ValueError:
            # Overflow
            self.force_update_counter = 0

    @classmethod
    def register(cls):
        bpy.types.Node.node_preview = bpy.props.PointerProperty(name="Node Preview Settings", type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Node.node_preview


class NodePreviewTreeProps(bpy.types.PropertyGroup):
    enabled: BoolProperty(name="Show Previews", default=True,
                          description="Show thumbnails above the nodes in this node tree")

    @classmethod
    def register(cls):
        bpy.types.NodeTree.node_preview = bpy.props.PointerProperty(name="Node Preview Settings", type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.NodeTree.node_preview


class NodePreviewPanel:
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Node Preview"

    @classmethod
    def poll(cls, context):
        return poll_node_tree(context)


class NODEPREVIEW_PT_node_tree_settings(bpy.types.Panel, NodePreviewPanel):
    bl_label = "Node Tree Settings"

    def draw(self, context):
        layout = self.layout
        node_tree = context.space_data.path[-1].node_tree
        layout.prop(node_tree.node_preview, "enabled")


class NODEPREVIEW_PT_node_tools(bpy.types.Panel, NodePreviewPanel):
    bl_label = "Selected Nodes"

    def draw(self, context):
        layout = self.layout
        layout.operator("nodepreview.toggle_preview")


classes = (
    NodePreviewNodeProps,
    NodePreviewTreeProps,
    NODEPREVIEW_OT_toggle_preview,
    NODEPREVIEW_OT_toggle_ignore_scale,
    NODEPREVIEW_PT_node_tree_settings,
    NODEPREVIEW_PT_node_tools,
)


def register():
    register_class(NodePreviewAddonPreferences)

    if bpy.app.background:
        from . import background
    else:
        from .display import display_register
        display_register()

        for cls in classes:
            register_class(cls)

        # Register keymap
        wm = bpy.context.window_manager
        keymap = wm.keyconfigs.addon.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")

        keymap_item = keymap.keymap_items.new(NODEPREVIEW_OT_toggle_ignore_scale.bl_idname, "I", "PRESS", ctrl=True, shift=True)
        addon_keymaps.append((keymap, keymap_item))
        keymap_item = keymap.keymap_items.new(NODEPREVIEW_OT_toggle_preview.bl_idname, "P", "PRESS", ctrl=True, shift=True)
        addon_keymaps.append((keymap, keymap_item))


def unregister():
    unregister_class(NodePreviewAddonPreferences)

    if not bpy.app.background:
        from .display import display_unregister
        display_unregister()

        for cls in reversed(classes):
            unregister_class(cls)

        # Unregister keymaps
        for keymap, keymap_item in addon_keymaps:
            keymap.keymap_items.remove(keymap_item)
        addon_keymaps.clear()
