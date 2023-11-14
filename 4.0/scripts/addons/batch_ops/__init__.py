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

bl_info = {
    "name": "Batch Operations™",
    "author": "moth3r, dairin0d",
    "version": (0, 8, 1),
    "blender": (2, 80, 0),
    "location": "View3D > right-side panel > Batch tab",
    "description": "Batch operations - advanced outliner / manager for Blender 2.8",
    "warning": "",
    "wiki_url": "https://batchops.moth3r.com",
    "doc_url": "https://batchops.moth3r.com",
    "tracker_url": "https://www.moth3r.com/about/#contact",
    "category": "3D View",
}

# =========================================================================== #

import time
import inspect
import itertools
from collections import namedtuple
import re
import functools
import os
import subprocess
import platform
import traceback

import bpy
import bmesh
from mathutils import Vector, Matrix, Quaternion, Euler, Color

import importlib
import importlib.util

if "dairin0d" in locals(): importlib.reload(dairin0d)
exec(("" if importlib.util.find_spec("dairin0d") else "from . ")+"import dairin0d")

dairin0d.load(globals(), {
    "bpy_inspect": "BlRna, BpyProp, prop, BlEnums",
    "utils_blender": "BlUtil, UndoBlock, NodeTreeComparer, BpyPath, apply_modifiers, apply_constraints, get_idblock, obj_in_collection",
    "utils_ui": "BlUI, NestedLayout",
    "utils_addon": "AddonManager",
})

addon = AddonManager()

# =========================================================================== #

batch_classes = []

# TODO: get rid of simple_operator()?

def simple_operator(idname, label="", description="", options={'REGISTER'}, props=None, size=None, poll=None):
    if props is None: props = {}
    def wrapper(func):
        bl_kwargs = dict(bl_idname=idname, bl_label=label, bl_description=description, bl_options=options)
        if isinstance(func, type):
            bl_kwargs.update(func.__dict__)
            if hasattr(func, "__annotations__"): props.update(func.__annotations__)
            simple_op = type(func.__name__, (bpy.types.Operator,), bl_kwargs)
            simple_op.__annotations__ = props
        else:
            simple_op = type(func.__name__, (bpy.types.Operator,), bl_kwargs)
            simple_op.__annotations__ = props
            func_params = inspect.signature(func).parameters
            if len(func_params) == 2:
                simple_op.execute = (lambda self, context: {'CANCELLED'} if (func(self, context) is False) else {'FINISHED'})
                if size is not None:
                    width = (size if isinstance(size, (int, float)) else size[0])
                    simple_op.invoke = (lambda self, context, event: context.window_manager.invoke_props_dialog(self, width=int(width)))
            elif len(func_params) == 3:
                simple_op.invoke = (lambda self, context, event: {'CANCELLED'} if (func(self, context, event) is False) else {'FINISHED'})
        if poll:
            if hasattr(simple_op, "poll"):
                poll0 = simple_op.poll
                simple_op.poll = classmethod(lambda cls, context: poll0(context) and poll(cls, context))
            else:
                simple_op.poll = classmethod(poll)
        addon.Operator(simple_op)
        return simple_op
    return wrapper

@addon.handler(["depsgraph_update_post", "undo_post", "redo_post", "load_post"], persistent=True)
def on_change(scene):
    for batch_cls in batch_classes:
        batch_cls.dirty = True

# =========================================================================== #

@addon.context_menu('APPEND')
def context_menu_draw(self, context):
    btn_op = getattr(context, "button_operator", None)
    if btn_op is None: return
    btn_id = btn_op.rna_type.identifier
    for batch_cls in batch_classes:
        if batch_cls.context_btn_id == btn_id:
            if btn_op.idname not in batch_cls.selection:
                batch_cls.select_idname(context, btn_op.idname, 'ENSURE', restricted=True)
            self.layout.separator()
            batch_cls.context_btn_draw(self, context)
            return

@addon.ui_draw("VIEW3D_MT_object_context_menu", 'APPEND')
def object_context_menu_draw(self, context):
    addon_prefs = addon.preferences
    panels_prefs = get_screen_prefs(context, 'PANELS_PIE')
    self.layout.separator()
    self.layout.menu("VIEW3D_MT_batch_ops_prefs_object_context_local", text="Batch Categories")
    for batch_cls in batch_classes:
        if batch_cls.plural_up not in addon_prefs.categories: continue
        if batch_cls.plural_up not in panels_prefs.show_context_menu: continue
        self.layout.menu(f"VIEW3D_MT_{batch_cls.prefix}", text=f"Batch {batch_cls.plural}")

# =========================================================================== #

@addon.Preferences.Include
class BatchOpsPreferences:
    def update_refresh(self, context):
        for batch_cls in batch_classes:
            batch_cls.dirty = True
            batch_cls.refresh(context)
    
    prefs_tab: 'SETTINGS' | prop("Tab", "Which tab to show in addon preferences", items=[
        ('SETTINGS', "Settings", "Settings"),
        ('ABOUT', "About", "About"),
    ])
    
    @classmethod
    def get_enum_items(cls, name):
        return BpyProp.find(BatchOpsPreferences, name, unwrap=True).keywords["items"]
    
    categories: {'MATERIALS', 'MODIFIERS', 'COLLECTIONS'} | prop("Categories", "Allowed panel categories", items=[])
    def categories_items(self, context):
        return BatchOpsPreferences.get_enum_items("categories")
    def categories_get(self):
        return BlRna.enum_to_int(self, "categories")
    def categories_set(self, value):
        value = BlRna.enum_from_int(self, "categories", value)
        new_panels = value - self.categories
        self.show_panels |= new_panels
        self.show_context_menu |= new_panels
        ScreenProps.update_panels(new_panels)
        self.categories = value
        BlUI.tag_redraw()
    categories_wrapper: set() | prop("Categories", "Allowed panel categories", items=categories_items, get=categories_get, set=categories_set)
    
    def update_keymaps(self, context):
        unregister_keymaps()
        register_keymaps()
    pie_view3d: 'MATERIALS' | prop("Pie Menu", "Operations on", items=[])
    pie_view3d_key: 'Q' | prop("Pie Menu Key", "Default key for 3D View Pie Menu", items=[
        (item.identifier, item.name, item.description, item.icon, item.value)
        for item in bpy.types.KeyMapItem.bl_rna.properties["type"].enum_items
    ], update=update_keymaps)
    pie_view3d_mods: {'alt'} | prop("3D View Pie Menu Modifiers", "Default modifiers for 3D View Pie Menu", items=[
        ('any', "Any", "Any"),
        ('alt', "Alt", "Alt"),
        ('shift', "Shift", "Shift"),
        ('ctrl', "Ctrl", "Ctrl"),
        ('oskey', "OS key", "OS key"),
    ], update=update_keymaps)
    pie_icons_only: True | prop("Pie icons only", "Display pie category as a row of icons")
    
    panel_view3d_key: 'ACCENT_GRAVE' | prop("Panel Key", "Default key for 3D View Batch Panel (popup dialog)", items=[
        (item.identifier, item.name, item.description, item.icon, item.value)
        for item in bpy.types.KeyMapItem.bl_rna.properties["type"].enum_items
    ], update=update_keymaps)
    panel_view3d_mods: {'alt'} | prop("3D View Panel Modifiers", "Default modifiers for 3D View Batch Panel (popup dialog)", items=[
        ('any', "Any", "Any"),
        ('alt', "Alt", "Alt"),
        ('shift', "Shift", "Shift"),
        ('ctrl', "Ctrl", "Ctrl"),
        ('oskey', "OS key", "OS key"),
    ], update=update_keymaps)
    
    panel_view3d_width: 300.0 | prop("3D View Panel width", "Width of the 3D View Batch Panel", min=100)
    panel_view3d_ok: False | prop("3D View Panel OK button", "Display Ok button in the 3D View Batch Panel")
    
    show_panels: {'MATERIALS', 'MODIFIERS', 'COLLECTIONS'} | prop("Panels", "Which Batch Ops panels to show", items=[])
    
    show_context_menu: {'MATERIALS', 'MODIFIERS', 'COLLECTIONS'} | prop("Context Menu", "Which Batch Ops categories to show in the object context menu", items=[])
    
    use_batch_tab: True | prop("Use Batch tab", "Show BatchOps panels in a Batch tab in 3D view")
    
    always_toggle_selection: False | prop("Toggle selections", "Always toggle selections")
    
    sync_with_editors: True | prop("Sync editors", "Synchronize Properties and Node editors to the selected item")
    
    sync_selection: False | prop("Sync selection", "Synchronize object selection and Batch panels selection")
    
    icon_previews: 'CONTEXTUAL' | prop("Icon previews", "Icon previews mode", items=[
        ('OFF', "Off", "No icon previews"),
        ('SELECT', "Select", "Clicking on an icon preview selects the item"),
        ('OPS_MENU', "Menu", "Clicking on an icon preview opens the corresponding operations menu"),
        ('CONTEXTUAL', "Contextual", "Clicking on an icon preview executes category-specific actions"),
    ])
    
    contextual_single_selection: False | prop("Single selection", "Apply contextual operation only to the clicked slot")
    
    use_local_storage: {'PANELS_PIE', 'FILTERS', 'RENAME'} | prop("Store locally",
        "What settings to store locally (in .blend file's workspaces) instead of addon preferences", items=[
        ('PANELS_PIE', "Panels+Pie+Context menu", "Panel visibility, active pie menu category and context menu"),
        ('FILTERS', "Filters", "Filter mode and name filtering"),
        ('RENAME', "Quick rename", "Quick rename"),
    ])

    mute_on_isolate: set() | prop("Mute on Isolate",
        "Isolate will mute (hide other objects) instead of switching to Local View for the specified categories", items=[])
    
    hide_filter: False | prop("Hide filter", "Hide filter mode & name filtering from panels")
    
    hide_obj_global: False | prop("Hide objects globally", "Hide objects globally or only in active view layer")
    
    #double_click_mode: 'RENAME' | prop("Double click", "Action performed when double-clicking a slot", items=[
    #    ('RENAME', "Rename", "Rename"),
    #    ('SELECT', "Select All/None/Inverse", "Context-based (DClick on unselected: Inverse, on selected: All, if everything is selected: None)"), # Commented out: "DClick: All, Shift+DClick: None, Ctrl+DClick: Inverse"
    #])
    double_click_rename: True | prop("Double click rename", "Rename when double-clicking a slot")
    
    include_instances: True | prop("Include instances", "Treat instances as part of the instancing object", update=update_refresh)
    
    ignore_dot_names: True | prop("Ignore .names", "Ignore items which names start with dot", update=update_refresh)
    
    make_unique_fake_user: True | prop("Set Fake User", "When Unique/Duplicate operation leaves a datablock without users, set a Fake User", update=update_refresh)
    
    unhide_on_isolate: False | prop("Unhide on Isolate", "Automatically unhide objects targeted by the Isolate operation")
    
    ops_icon_style: 'THREE_DOTS' | prop("Operations icon style", "Style of the Operations menu icon in the panels", items=[
        ('NONE', "Hidden", "", 'BLANK1', 0),
        ('THREE_DOTS', "Dots", "", 'THREE_DOTS', 1),
        ('COLLAPSEMENU', "Lines", "", 'COLLAPSEMENU', 2),
        ('TRIA_DOWN', "Triangle", "", 'TRIA_DOWN', 3),
    ])
    ops_icon_align: True | prop("Operations icon align", "Align or separate the Operations icon")
    
    use_pie_menu: True | prop("ALt Pie", "Show Pie menu instead of regular menu when Alt+clicking on panel items")
    
    virtual_slot_mode: 'ALWAYS' | prop("Virtual slot", "Treat objects without material slots as having a virtual empty slot", items=[
        ('NEVER', "Never", "Disable for all objects"),
        ('ALWAYS', "Always", "Enable for all objects"),
        ('CONTEXTUAL', "Contextual", "Enable for objects that can have materials"),
    ])
    
    remove_slots: False | prop("Remove slots", "Material slots can be removed (otherwise, they may only be emptied)")
    
    apply_options: {'CONVERT_TO_MESH', 'MAKE_SINGLE_USER', 'REMOVE_DISABLED', 'APPLY_SHAPE_KEYS', 'VISIBLE_ONLY'} | prop(
        "Apply options", "Apply options", items=[
        ('CONVERT_TO_MESH', "Convert to mesh", "Convert to mesh"),
        ('MAKE_SINGLE_USER', "Make single user", "Make single user"),
        ('REMOVE_DISABLED', "Remove disabled", "Remove disabled"),
        ('DELETE_OPERANDS', "Delete operands", "Delete the remaining boolean operands"),
        ('APPLY_SHAPE_KEYS', "Apply shape keys", "Apply shape keys before applying the modifiers"),
        ('VISIBLE_ONLY', "Only visible", "Apply only the modifiers visible in the viewport"),
    ])
    
    modstack_naming: 'TYPE' | prop("Naming options", "What names to show for modifiers/constraints/effects", items=[
        ('TYPE', "Type", "Type"),
        ('NAME', "Name", "Name"),
        ('SMART_NAME', "Smart name", "Name without .000-like suffix"),
    ], update=update_refresh)
    
    panel_newmod_width: 300.0 | prop("New dialog width", "Width of the New dialog", min=100)
    panel_newmod_ok: True | prop("New dialog Ok button", "Display Ok button in the New dialog")
    
    child_collections: True | prop("Child collections", "Show child (non-root) collections", update=update_refresh)
    
    auto_rename_obj: set() | prop("Auto Rename", "Assign object name to...", items=[
        ('OBJECT_TO_DATA', "Object → Data", "Assign object name to object data"),
        ('OBJECT_TO_MATERIALS', "Object → Materials", "Assign object name to object materials"),
    ])
    
    auto_rename_data: set() | prop("Auto Rename", "Assign object data name to...", items=[
        ('DATA_TO_OBJECTS', "Data → Objects", "Assign object data name to objects"),
        ('DATA_TO_MATERIALS', "Data → Materials", "Assign object data name to materials"),
    ])
    
    auto_rename_coll: set() | prop("Auto Rename", "Assign collection name to...", items=[
        ('COLLECTION_TO_INSTANCES', "Collection → Instances", "Assign collection name to its instances"),
        ('COLLECTION_TO_OBJECTS', "Collection → Objects", "Assign collection name to objects"),
        ('COLLECTION_TO_DATA', "Collection → Data", "Assign collection name to object data"),
        ('COLLECTION_TO_MATERIALS', "Collection → Materials", "Assign collection name to object materials"),
    ])
    
    group_pro_filter: 'ALL' | prop("Group Pro filter", "Filter Group Pro collection", items=[
        ('ALL', "All", "Show all collections"),
        ('HIDE', "Hide GroupPro", "Hide GroupPro collections"),
        ('ONLY', "Only GroupPro", "Show only GroupPro collections"),
    ], update=update_refresh)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop_tabs_enum(self, "prefs_tab")
        if self.prefs_tab == 'ABOUT':
            self.draw_about(context)
        else:
            self.draw_settings(context)
    
    def draw_about(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.label(text="Official:")
        col.operator("wm.url_open", text="BATCH TOOLS™ 2 Store").url = "https://www.moth3r.com"
        col.operator("wm.url_open", text="Documentation").url = "https://batchops.moth3r.com"
        col = row.column()
        col.label(text="Recommended:")
        col.operator("wm.url_open", text="MasterXeon1001 addons").url = "https://gumroad.com/masterxeon1001"
        col.operator("wm.url_open", text="MACHIN3 tools").url = "https://machin3.io/"
    
    def draw_settings(self, context):
        layout = NestedLayout(self.layout)
        
        prefs = context.preferences
        
        row_main = layout.row()
        
        col = row_main.column(align=True)
        col.alignment = 'LEFT'
        col.label(text="Categories:")
        col.prop_enum_filtered(self, "categories_wrapper")
        
        col_main = row_main.column()
        
        col = col_main.box()
        col.label(text="General options:")
        
        subrow = col.split()
        subrow.label(text="Pie menu & panels:", icon='BLANK1')
        
        subrow.menu("VIEW3D_MT_batch_ops_prefs_panels_base")
        subrow2 = subrow.row(align=True)
        subrow2.menu("VIEW3D_MT_batch_ops_prefs_pie")
        subrow2.prop(self, "pie_icons_only", text="", icon='COLLAPSEMENU')
        
        subrow = col.row()
        subrow.label(text="3D view menu:", icon='BLANK1')
        subrow.menu("VIEW3D_MT_batch_ops_prefs_object_context")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Pie menu hotkey:", icon='BLANK1')
        subrow.prop(self, "pie_view3d_key", text="")
        subrow.prop_menu_enum(self, "pie_view3d_mods", text="Key Modifiers")
        
        subrow = col.row()
        subrow.label(text="Panel hotkey:", icon='BLANK1')
        subrow.prop(self, "panel_view3d_key", text="")
        subrow.prop_menu_enum(self, "panel_view3d_mods", text="Key Modifiers")
        
        subrow = col.row()
        subrow.label(text="Popup panel:", icon='BLANK1')
        subrow.prop(self, "panel_view3d_width", text="Width")
        subrow.prop(self, "panel_view3d_ok", text="OK button", toggle=True)
        
        subrow = col.row()
        subrow.label(text="'New' dialog:", icon='BLANK1')
        subrow.prop(self, "panel_newmod_width", text="Width")
        subrow.prop(self, "panel_newmod_ok", text="OK button", toggle=True)
        
        subrow = col.split()
        subrow.label(text="Operations menu:", icon='BLANK1')
        subrow.prop(self, "ops_icon_style", text="")
        subrow2 = subrow.row()
        subrow2.prop(self, "ops_icon_align", text="Align")
        subrow2.prop(self, "use_pie_menu", text="Alt Pie")
        
        subrow = col.row()
        subrow.label(text="Icon previews:", icon='BLANK1')
        subrow.prop(self, "icon_previews", text="")
        subrow2 = subrow.row()
        subrow2.active = (self.icon_previews == 'CONTEXTUAL')
        subrow2.prop(self, "contextual_single_selection", text="Single selection")
        
        subrow = col.row()
        subrow.label(text="Store locally:", icon='BLANK1')
        subrow.prop_menu_enum(self, "use_local_storage", text="...")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Mute on Isolate:", icon='BLANK1')
        subrow.prop_menu_enum(self, "mute_on_isolate", text="Categories...")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Hide filter:", icon='BLANK1')
        subrow.prop(self, "hide_filter", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Hide objects globally:", icon='BLANK1')
        subrow.prop(self, "hide_obj_global", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Double click rename:", icon='BLANK1')
        subrow.prop(self, "double_click_rename", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Toggle selections:", icon='BLANK1')
        subrow.prop(self, "always_toggle_selection", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Synchronize selection:", icon='BLANK1')
        subrow.prop(self, "sync_selection", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Synchronize editors:", icon='BLANK1')
        subrow.prop(self, "sync_with_editors", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Panels in Batch tab:", icon='BLANK1')
        subrow.prop(self, "use_batch_tab", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Include instances:", icon='BLANK1')
        subrow.prop(self, "include_instances", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Ignore .names:", icon='BLANK1')
        subrow.prop(self, "ignore_dot_names", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Set Fake User:", icon='BLANK1')
        subrow.prop(self, "make_unique_fake_user", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Unhide on Isolate:", icon='BLANK1')
        subrow.prop(self, "unhide_on_isolate", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        col_main.separator()
        
        col = col_main.box()
        col.label(text="Specific options:")
        
        subrow = col.row()
        subrow.label(text="Modifiers & such:", icon='BLANK1')
        subrow.prop_menu_enum(self, "modstack_naming", text="Naming options")
        subrow.prop_menu_enum(self, "apply_options", text="Apply options")
        
        subrow = col.row()
        subrow.label(text="Material slots:", icon='BLANK1')
        subrow.prop_menu_enum(self, "virtual_slot_mode", text="Virtual slot")
        subrow.prop(self, "remove_slots", text="Allow deletion")
        
        subrow = col.row()
        subrow.label(text="Child collections:", icon='BLANK1')
        subrow.prop(self, "child_collections", text=" ")
        subrow.label(text="") # dummy UI element to use up the remaining space
        
        subrow = col.row()
        subrow.label(text="Auto Rename:", icon='BLANK1')
        subrow.prop_menu_enum(self, "auto_rename_obj", text="Object → ...")
        subrow.prop_menu_enum(self, "auto_rename_data", text="Data → ...")
        subrow.prop_menu_enum(self, "auto_rename_coll", text="Collection → ...")
        
        if "GroupPro" in prefs.addons:
            subrow = col.row()
            subrow.label(text="Group Pro filter:", icon='BLANK1')
            subrow.prop(self, "group_pro_filter", text="")
            subrow.label(text="") # dummy UI element to use up the remaining space

# WARNING: bpy.context in depsgraph_update handlers is different
# from the current workspace's context, so we *have* to store
# BatchOps options globally (i.e. in WindowManager).
@addon.PropertyGroup
class BatchOpsProps:
    filter_icons = {'FILE':'FILE', 'SCENE':'SCENE_DATA', 'LAYER':'RENDERLAYERS', 'VISIBLE':'HIDE_OFF', 'SELECTION':'RESTRICT_SELECT_OFF'}
    
    filter_mode: 'FILE' | prop("Filter mode", "Filter mode", items=[
        ('FILE', "File", "Filter by file", 'FILE', 0),
        ('SCENE', "Scene", "Filter by current scene", 'SCENE_DATA', 1),
        ('LAYER', "Layer", "Filter by current layer", 'RENDERLAYERS', 2),
        ('VISIBLE', "Visible", "Filter by visibility", 'HIDE_OFF', 3),
        ('SELECTION', "Selection", "Filter by selection", 'RESTRICT_SELECT_OFF', 4),
    ])

@addon.Operator(idname="batch_ops.panel_view3d", label="Batch Ops™", description="Batch Ops™")
class BatchOpsPopupPanelView3D:
    SelfEmulator = namedtuple("self", ["layout"])
    
    @classmethod
    def poll(cls, context):
        addon_prefs = addon.preferences
        return len(addon_prefs.categories) > 0
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        addon_prefs = addon.preferences
        wm = context.window_manager
        width = min(addon_prefs.panel_view3d_width, context.window.width)
        if addon_prefs.panel_view3d_ok:
            return wm.invoke_props_dialog(self, width=int(width))
        else:
            return wm.invoke_popup(self, width=int(width))
    
    def draw(self, context):
        layout = self.layout
        addon_prefs = addon.preferences
        panels_prefs = get_screen_prefs(context, 'PANELS_PIE')
        
        if not addon_prefs.panel_view3d_ok:
            row = layout.row()
            row.alignment = 'LEFT'
            row.label(text="Batch Ops™")
        
        row = layout.row(align=True)
        for item in BatchOpsPreferences.get_enum_items("categories"):
            if item[0] not in addon_prefs.categories: continue
            row.prop_enum(panels_prefs, "show_panels", item[0])
        
        for batch_cls in batch_classes:
            if batch_cls.plural_up not in addon_prefs.categories: continue
            if batch_cls.plural_up not in panels_prefs.show_panels: continue
            box = layout.box()
            row = box.row()
            batch_cls.draw_panel_header(self.SelfEmulator(row), context)
            row.label(text=batch_cls.plural)
            batch_cls.draw_panel(self.SelfEmulator(box), context)

@addon.Menu(idname="VIEW3D_MT_batch_ops_pie_view3d", label="Batch Ops™", description="Batch Ops™")
class BatchOpsMenuPieView3D:
    @classmethod
    def poll(cls, context):
        addon_prefs = addon.preferences
        return len(addon_prefs.categories) > 0
    
    def draw(self, context):
        layout = self.layout
        
        addon_prefs = addon.preferences
        pie_prefs = get_screen_prefs(context, 'PANELS_PIE')
        
        if (pie_prefs.pie_view3d not in addon_prefs.categories) and addon_prefs.categories:
            pie_prefs.pie_view3d = next(iter(addon_prefs.categories))
        
        pie = layout.menu_pie()
        
        title = ""
        for batch_cls in batch_classes:
            if batch_cls.plural_up == pie_prefs.pie_view3d:
                batch_cls.draw_pie(context, pie)
                title = f"Batch {batch_cls.plural}"
                break
        
        if addon_prefs.pie_icons_only:
            row = pie.row(align=True)
            for item in BatchOpsPreferences.get_enum_items("categories"):
                if item[0] not in addon_prefs.categories: continue
                row.prop_enum(pie_prefs, "pie_view3d", item[0], text="")
        else:
            pie.menu("VIEW3D_MT_batch_ops_pie_categories", text=title)

@addon.Menu(idname="VIEW3D_MT_batch_ops_prefs_panels", label="Panels", description="Panels")
class BatchOpsPrefsPanelsMenu: # used in Batch panel config submenu
    def draw(self, context):
        layout = self.layout
        
        addon_prefs = addon.preferences
        panels_prefs = get_screen_prefs(context, 'PANELS_PIE')
        
        layout.prop(addon_prefs, "use_batch_tab")
        layout.separator()
        
        for item in BatchOpsPreferences.get_enum_items("categories"):
            if item[0] not in addon_prefs.categories: continue
            layout.prop_enum(panels_prefs, "show_panels", item[0])

@addon.Menu(idname="VIEW3D_MT_batch_ops_prefs_panels_base", label="Panels", description="Panels")
class BatchOpsPrefsPanelsBaseMenu: # used only in addon preferences
    def draw(self, context):
        layout = self.layout
        
        addon_prefs = addon.preferences
        
        for item in BatchOpsPreferences.get_enum_items("categories"):
            if item[0] not in addon_prefs.categories: continue
            layout.prop_enum(addon_prefs, "show_panels", item[0])

@addon.Menu(idname="VIEW3D_MT_batch_ops_prefs_pie", label="Pie", description="Pie")
class BatchOpsPrefsPieMenu: # used only in addon preferences
    def draw(self, context):
        layout = self.layout
        
        addon_prefs = addon.preferences
        
        for item in BatchOpsPreferences.get_enum_items("pie_view3d"):
            if item[0] not in addon_prefs.categories: continue
            layout.prop_enum(addon_prefs, "pie_view3d", item[0])

@addon.Menu(idname="VIEW3D_MT_batch_ops_prefs_object_context", label="Context menu", description="Context menu")
class BatchOpsPrefsObjectContextMenu: # used only in addon preferences
    def draw(self, context):
        layout = self.layout
        
        addon_prefs = addon.preferences
        
        for item in BatchOpsPreferences.get_enum_items("show_context_menu"):
            if item[0] not in addon_prefs.categories: continue
            layout.prop_enum(addon_prefs, "show_context_menu", item[0])

@addon.Menu(idname="VIEW3D_MT_batch_ops_prefs_object_context_local", label="Catergories", description="Batch ops categories")
class BatchOpsPrefsObjectContextMenuLocal: # used only in addon preferences
    def draw(self, context):
        layout = self.layout
        
        addon_prefs = addon.preferences
        panel_prefs = get_screen_prefs(context, 'PANELS_PIE')
        
        for item in BatchOpsPreferences.get_enum_items("show_context_menu"):
            if item[0] not in addon_prefs.categories: continue
            layout.prop_enum(panel_prefs, "show_context_menu", item[0])

@addon.Menu(idname="VIEW3D_MT_batch_ops_pie_categories", label="Categories", description="Categories")
class BatchOpsPieCategoriesMenu: # used in View3D pie
    def draw(self, context):
        layout = self.layout
        
        addon_prefs = addon.preferences
        pie_prefs = get_screen_prefs(context, 'PANELS_PIE')
        
        for item in BatchOpsPreferences.get_enum_items("categories"):
            if item[0] not in addon_prefs.categories: continue
            layout.prop_enum(pie_prefs, "pie_view3d", item[0])

obj_type_icons = {
    'MESH':'OUTLINER_OB_MESH',
    'CURVE':'OUTLINER_OB_CURVE',
    'SURFACE':'OUTLINER_OB_SURFACE',
    'META':'OUTLINER_OB_META',
    'FONT':'OUTLINER_OB_FONT',
    'ARMATURE':'OUTLINER_OB_ARMATURE',
    'LATTICE':'OUTLINER_OB_LATTICE',
    'EMPTY':'OUTLINER_OB_EMPTY',
    'GPENCIL':'OUTLINER_OB_GREASEPENCIL',
    'CAMERA':'OUTLINER_OB_CAMERA',
    'LIGHT':'OUTLINER_OB_LIGHT',
    'SPEAKER':'OUTLINER_OB_SPEAKER',
    'LIGHT_PROBE':'OUTLINER_OB_LIGHTPROBE',
    'POINTCLOUD':'OUTLINER_OB_POINTCLOUD',
    'VOLUME':'OUTLINER_OB_VOLUME',
    # These are not actual obj.type enums, but have their own outliner icons
    'GROUP':'OUTLINER_OB_GROUP_INSTANCE',
    'FORCE':'OUTLINER_OB_FORCE_FIELD',
    'IMAGE':'OUTLINER_OB_IMAGE',
}

obj_type_names = {
    'MESH':"Mesh",
    'CURVE':"Curve",
    'SURFACE':"Surface",
    'META':"Metaball",
    'FONT':"Text",
    'ARMATURE':"Armature",
    'LATTICE':"Lattice",
    'EMPTY':"Empty",
    'GPENCIL':"Grease Pencil",
    'CAMERA':"Camera",
    'LIGHT':"Light",
    'SPEAKER':"Speaker",
    'LIGHT_PROBE':"Light Probe",
    'POINTCLOUD':"Point Cloud",
    'VOLUME':"Volume",
    # These are not actual obj.type enums, but have their own outliner icons
    'GROUP':"Group Instance",
    'FORCE':"Force Field",
    'IMAGE':"Image",
}
def get_obj_type(obj):
    if not obj: return ''
    
    obj_type = obj.type
    
    if obj_type != 'EMPTY': return obj_type
    
    if obj.instance_type == 'COLLECTION':
        obj_type = 'GROUP'
    elif obj.empty_display_type == 'IMAGE':
        obj_type = 'IMAGE'
    elif obj.field.type != 'NONE':
        obj_type = 'FORCE'
    
    return obj_type

def get_obj_hide(context, obj):
    return not BlUtil.Object.visible_get(obj, context.view_layer)

def set_obj_hide(context, obj, value):
    if value:
        addon_prefs = addon.preferences
        if addon_prefs.hide_obj_global:
            if not obj.hide_viewport: obj.hide_viewport = True # can be slow in complex scenes?
        else:
            BlUtil.Object.hide_set(obj, True, context.view_layer)
    else:
        if obj.hide_viewport: obj.hide_viewport = False # can be slow in complex scenes?
        BlUtil.Object.hide_set(obj, False, context.view_layer)

def sync_name(idblock, filter, name=None, affect_main=True):
    if (not idblock) or idblock.library: return
    is_main = (name is None)
    if is_main:
        name = idblock.name
    elif affect_main:
        idblock.name = name
    
    if isinstance(idblock, bpy.types.Material):
        return
    elif isinstance(idblock, bpy.types.Collection):
        for obj in tuple(idblock.objects):
            sync_name(obj, filter, name, filter.get('OBJS'))
        if filter.get('INST'):
            for obj in tuple(idblock.users_dupli_group):
                sync_name(obj, {}, name)
    elif isinstance(idblock, bpy.types.Object):
        if filter.get('DATA'):
            sync_name(idblock.data, ({} if is_main else {'MATS':filter.get('MATS')}), name)
        if filter.get('MATS'):
            for ms in idblock.material_slots:
                sync_name(ms.material, None, name)
    else: # assumed to be object data
        if filter.get('OBJS'):
            for obj in tuple(bpy.data.objects):
                if (obj.data != idblock): continue
                sync_name(obj, {'MATS':filter.get('MATS')}, name)
        if filter.get('MATS') and hasattr(idblock, "materials"):
            for mat in idblock.materials:
                sync_name(mat, None, name)

@simple_operator("batch_ops.enable_selection_globally", "Enable Selection Globally", "Make all objects and collections selectable (Click: all, Ctrl: objects only, Shift: collections only)")
class BatchOpsEnableSelectionGlobally:
    objects: True | prop()
    collections: True | prop()
    
    def execute(self, context):
        with UndoBlock(f"Enable Selection Globally"):
            if self.objects:
                for obj in bpy.data.objects:
                    obj.hide_select = False
            
            if self.collections:
                for coll in bpy.data.collections:
                    coll.hide_select = False
        
        BlUI.tag_redraw()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.objects = (event.ctrl or (event.ctrl == event.shift))
        self.collections = (event.shift or (event.ctrl == event.shift))
        return self.execute(context)

@simple_operator("batch_ops.sync_obj_sel", "Batch → Objects", "Sync objects to selected (filtered across all enabled Batch Ops categories)")
class BatchOpsSyncObjectsToSelectionGlobal:
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        addon_prefs = addon.preferences
        panels_prefs = get_screen_prefs(context, 'PANELS_PIE')
        
        objs = None
        
        for batch_cls in batch_classes:
            if batch_cls.plural_up not in addon_prefs.categories: continue
            if batch_cls.plural_up not in panels_prefs.show_panels: continue
            
            if not batch_cls.selection: continue
            
            batch_objs = batch_cls.selected_objects(context, force_sync=True)
            
            if objs is None:
                objs = batch_objs
            else:
                objs.intersection_update(batch_objs)
        
        with UndoBlock("Select"):
            BlUtil.Object.select_activate(objs, 'SOLO', active='ANY', view_layer=context.view_layer)
        
        BlUI.tag_redraw()
        return {'FINISHED'}

class AnyIDNames:
    def __contains__(self, item):
        return True

# =========================================================================== #

@addon.Preset("rename_patterns.preset", sorting='MODIFY', popup='OPERATOR', title="")
class RenamePreset:
    @staticmethod
    def _find_batch_cls(context):
        if context:
            prefix = "$category="
            for name in dir(context):
                if not name.startswith(prefix): continue
                category = name[len(prefix):]
                for batch_cls in batch_classes:
                    if batch_cls.plural_up == category: return batch_cls
        return None
    
    def apply(self, context):
        batch_cls = self._find_batch_cls(context)
        if not batch_cls: return
        if not hasattr(batch_cls, "rename"): return
        rename_prefs_wm = get_screen_prefs(context, 'RENAME')
        setattr(rename_prefs_wm, f"{batch_cls.singular_low}_rename", self.id)
    
    class OpEditMixin:
        def execute(self, context):
            batch_cls = RenamePreset._find_batch_cls(context)
            if not batch_cls: return {'CANCELLED'}
            if not hasattr(batch_cls, "rename"): return {'CANCELLED'}
            rename_prefs_wm = get_screen_prefs(context, 'RENAME')
            pattern = getattr(rename_prefs_wm, f"{batch_cls.singular_low}_rename")
            RenamePreset.presets.add(RenamePreset(pattern))
            return {'FINISHED'}

# =========================================================================== #

def make_batch_ops(batch_cls, singular, plural=None):
    if not plural: plural = singular+"s"
    singular_low = singular.lower().replace(" ", "_")
    plural_low = plural.lower().replace(" ", "_")
    singular_up = singular.upper().replace(" ", "_")
    plural_up = plural.upper().replace(" ", "_")
    prefix = f"batch_ops_{plural_low}"
    
    batch_classes.append(batch_cls)
    
    batch_cls.singular = singular
    batch_cls.plural = plural
    batch_cls.singular_low = singular_low
    batch_cls.plural_low = plural_low
    batch_cls.singular_up = singular_up
    batch_cls.plural_up = plural_up
    batch_cls.prefix = prefix
    
    batch_cls.dirty = True
    batch_cls.idnames = []
    batch_cls.names = []
    batch_cls.users = []
    batch_cls.states = []
    batch_cls.obj_sel = []
    batch_cls.selection = []
    batch_cls.clipboard = []
    batch_cls.scene = None
    batch_cls.view_layer = None
    batch_cls.click_time = 0
    batch_cls.click_index = -1
    batch_cls.prev_sel = set()
    
    if hasattr(batch_cls, "initialize"):
        batch_cls.initialize()
    
    extras = {}
    if hasattr(batch_cls, "extra_operators"):
        extras = batch_cls.extra_operators()
    extras_select = extras.get("extras_select")
    extras_view = extras.get("extras_view")
    extras_main = extras.get("extras_main")
    main_overrides = extras.get("main_overrides", ())
    
    batch_poll = batch_cls.poller()
    
    def on_update_rename(self, context):
        if not hasattr(batch_cls, "rename"): return
        rename_prefs = get_screen_prefs(context, 'RENAME')
        pattern = getattr(rename_prefs, f"{singular_low}_rename")
        with UndoBlock(f"Rename {plural}"):
            batch_cls.pattern_rename(batch_cls.selected_idnames(context), pattern, context)
        BlUI.tag_redraw()
    
    def on_update_search(self, context):
        batch_cls.refresh(context)
    
    if not getattr(BatchOpsProps, "__annotations__"): BatchOpsProps.__annotations__ = {}
    BatchOpsProps.__annotations__[f"{singular_low}_rename_on"] = False | prop(description="Enable quick renaming", options={'HIDDEN'})
    BatchOpsProps.__annotations__[f"{singular_low}_rename"] = "{name}" | prop(description="Quick rename:\n"+RenamePattern.__doc__.strip(), options={'HIDDEN'}, update=on_update_rename)
    BatchOpsProps.__annotations__[f"{singular_low}_search_on"] = False | prop(description="Enable name filtering", options={'HIDDEN'}, update=on_update_search)
    BatchOpsProps.__annotations__[f"{singular_low}_search"] = "" | prop(description="Filter by name", options={'HIDDEN', 'TEXTEDIT_UPDATE'}, update=on_update_search)
    BatchOpsProps.__annotations__[f"{singular_low}_filter"] = BatchOpsProps.__annotations__[f"filter_mode"]
    
    # If the user wants to store stuff in addon preferences, not everything makes sense to do so
    BatchOpsPreferences.__annotations__[f"{singular_low}_rename_on"] = BatchOpsProps.__annotations__[f"{singular_low}_rename_on"]
    BatchOpsPreferences.__annotations__[f"{singular_low}_search_on"] = BatchOpsProps.__annotations__[f"{singular_low}_search_on"]
    BatchOpsPreferences.__annotations__[f"{singular_low}_filter"] = BatchOpsProps.__annotations__[f"{singular_low}_filter"]

    for prop_name in ("categories", "show_panels", "show_context_menu", "pie_view3d", "mute_on_isolate"):
        items = BatchOpsPreferences.get_enum_items(prop_name)
        items.append((plural_up, plural, plural, batch_cls.icon, 1 << len(items)))
    
    @simple_operator(f"{prefix}.panel_search_toggle", f"Toggle search/rename", f"Click: toggle name filtering; Ctrl+Click: toggle quick renaming", {'INTERNAL'})
    def BatchOp(self, context, event):
        if event.ctrl:
            rename_prefs = get_screen_prefs(context, 'RENAME', True)
            prop_name = f"{singular_low}_rename_on"
            setattr(rename_prefs, prop_name, not getattr(rename_prefs, prop_name))
        else:
            filters_prefs = get_screen_prefs(context, 'FILTERS', True)
            prop_name = f"{singular_low}_search_on"
            setattr(filters_prefs, prop_name, not getattr(filters_prefs, prop_name))
    
    @addon.Menu(idname=f"VIEW3D_MT_{prefix}_prefs", label="Options", description="Options")
    class BatchOpsPrefsMenu:
        def draw(self, context):
            layout = self.layout
            
            addon_prefs = addon.preferences
            
            layout.menu("VIEW3D_MT_batch_ops_prefs_panels")
            layout.prop(addon_prefs, "double_click_rename")
            layout.prop(addon_prefs, "always_toggle_selection")
            layout.prop(addon_prefs, "sync_selection")
            layout.prop(addon_prefs, "sync_with_editors")
            layout.prop(addon_prefs, "ignore_dot_names")
            layout.prop(addon_prefs, "include_instances")
            layout.prop(addon_prefs, "make_unique_fake_user")
            layout.prop(addon_prefs, "unhide_on_isolate")
            
            if hasattr(batch_cls, "draw_prefs"):
                layout.separator()
                batch_cls.draw_prefs(layout, context)
    
    class BatchOpsPanelBase(bpy.types.Panel):
        f"""Batch {plural}"""
        bl_label = f"{plural}"
        bl_idname = f"VIEW3D_PT_{prefix}"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        
        def draw_header(self, context):
            layout = self.layout
            
            row = layout.row(align=True)
            row.menu(f"VIEW3D_MT_{prefix}_prefs", text="", icon='PREFERENCES')
        
        def draw(self, context):
            layout = self.layout
            layout.context_pointer_set(f"$category={plural_up}", None)
            
            addon_prefs = addon.preferences
            
            filters_prefs_wm = get_screen_prefs(context, 'FILTERS')
            filters_prefs = get_screen_prefs(context, 'FILTERS', True)

            rename_prefs_wm = get_screen_prefs(context, 'RENAME')
            rename_prefs = get_screen_prefs(context, 'RENAME', True)
            
            is_rename_on = getattr(rename_prefs, f"{singular_low}_rename_on") and hasattr(batch_cls, "rename")
            is_search_on = getattr(filters_prefs, f"{singular_low}_search_on")
            
            show_ops = addon_prefs.ops_icon_style != 'NONE'
            show_filter = not addon_prefs.hide_filter
            if is_rename_on and show_filter:
                row = layout.row()
                row2 = row.row(align=True)
                RenamePreset.draw_popup(row2)
                row2.prop(rename_prefs_wm, f"{singular_low}_rename", text="")
                row2.prop(rename_prefs, f"{singular_low}_rename_on", text="", icon='OUTLINER_DATA_FONT', icon_only=True)
            elif show_ops or show_filter:
                row = layout.row()
                row1 = row.row(align=addon_prefs.ops_icon_align)
                if show_ops:
                    row1.menu(f"VIEW3D_MT_{prefix}", text=("" if show_filter else "Operations"), icon=addon_prefs.ops_icon_style)
                if show_filter:
                    row1.prop(filters_prefs, f"{singular_low}_filter", text="", icon_only=is_search_on)
                    row2 = row.row(align=True)
                    if is_search_on: row2.prop(filters_prefs_wm, f"{singular_low}_search", text="")
                    if hasattr(batch_cls, "rename"):
                        row2.operator(f"{prefix}.panel_search_toggle", text="", depress=is_search_on, icon='VIEWZOOM')
                    else:
                        row2.prop(filters_prefs, f"{singular_low}_search_on", text="", icon='VIEWZOOM', icon_only=True)
            
            batch_cls.refresh(context)
            
            sublayout = layout.column(align=True)
            selection_set = set(batch_cls.selection)
            for idname, name, users, state, obj_sel in zip(batch_cls.idnames, batch_cls.names, batch_cls.users, batch_cls.states, batch_cls.obj_sel):
                icon = ('DOT' if obj_sel else 'BLANK1')
                selected = idname in selection_set
                subrow = sublayout.row(align=True)
                op = subrow.operator(f"{prefix}.click", text=f"{name} ({users})", depress=selected, icon=icon, translate=False)
                op.idname = idname
                # Seems like we HAVE to set all operator properties, or the last assigned values will be used
                # (in this case, op.mode from previous row's icon preview operator). Report this as a bug?
                op.mode = ""
                
                if hasattr(batch_cls, "icon_data") and (addon_prefs.icon_previews != 'OFF'):
                    icon_data = batch_cls.icon_data(idname)
                    if icon_data is not None:
                        subrow2 = subrow.row(align=True)
                        if state is None:
                            subrow2.alert = True
                        elif isinstance(state, str):
                            subrow2.emboss = state
                        else:
                            subrow2.active = state
                        icon, icon_value = ((icon_data, 0) if isinstance(icon_data, str) else ('NONE', layout.icon(icon_data)))
                        if addon_prefs.icon_previews == 'CONTEXTUAL':
                            op = subrow2.operator(f"{prefix}.contextual_click", text="", depress=selected, icon=icon, icon_value=icon_value)
                            op.idname = idname
                        else:
                            op = subrow2.operator(f"{prefix}.click", text="", depress=selected, icon=icon, icon_value=icon_value)
                            op.idname = idname
                            op.mode = addon_prefs.icon_previews
    
    @addon.Panel
    class BatchOpsPanelView(BatchOpsPanelBase):
        bl_idname = BatchOpsPanelBase.bl_idname + "_view"
        bl_category = "View"
        
        @classmethod
        def poll(cls, context):
            addon_prefs = addon.preferences
            panels_prefs = get_screen_prefs(context, 'PANELS_PIE')
            if plural_up not in addon_prefs.categories: return False
            if plural_up not in panels_prefs.show_panels: return False
            return not addon_prefs.use_batch_tab
    
    @addon.Panel
    class BatchOpsPanelBatch(BatchOpsPanelBase):
        bl_idname = BatchOpsPanelBase.bl_idname + "_batch"
        bl_category = "Batch™"
        
        @classmethod
        def poll(cls, context):
            addon_prefs = addon.preferences
            panels_prefs = get_screen_prefs(context, 'PANELS_PIE')
            if plural_up not in addon_prefs.categories: return False
            if plural_up not in panels_prefs.show_panels: return False
            return addon_prefs.use_batch_tab
    
    def select_idname(context, idname, mode, restricted=False):
        addon_prefs = addon.preferences
        
        #if restricted and addon_prefs.sync_selection: return # it's probably better not to leave selection in un-synced state (?)
        
        prev_sel = set(batch_cls.selection)
        
        try:
            click_index = batch_cls.idnames.index(idname)
        except ValueError:
            click_index = -1
        i0, i1 = batch_cls.click_index, click_index
        batch_cls.click_index = click_index
        
        if mode == 'ENSURE':
            if idname not in batch_cls.selection:
                batch_cls.selection = [idname]
        else:
            if (mode == 'MULTI') and (i0 >= 0) and (i1 >= 0):
                if i0 != i1:
                    i_step = (1 if i0 < i1 else -1)
                    idnames = [batch_cls.idnames[i0+di*i_step] for di in range(abs(i1-i0)+1)]
                    state = not all(idname in batch_cls.selection for idname in idnames)
                    for idname in (idnames if state else idnames[:-1]):
                        if idname in batch_cls.selection:
                            if not state: batch_cls.selection.remove(idname)
                        else:
                            if state: batch_cls.selection.append(idname)
                    """
                    state = batch_cls.idnames[i0] in batch_cls.selection
                    di = (1 if i0 < i1 else -1)
                    for i in range(i0+di, i1+di, di):
                        idname = batch_cls.idnames[i]
                        if idname in batch_cls.selection:
                            if not state: batch_cls.selection.remove(idname)
                        else:
                            if state: batch_cls.selection.append(idname)
                    """
            else:
                if mode not in {'MULTI', 'INVERT', 'ADD', 'REMOVE'}:
                    prev_sel -= {idname}
                    batch_cls.selection.clear()
                
                if idname in batch_cls.selection:
                    if mode != 'ADD':
                        batch_cls.selection.remove(idname)
                else:
                    if mode != 'REMOVE':
                        batch_cls.selection.append(idname)
        
        # Note: cannot modify blend data in drawing/rendering callbacks,
        # and cannot sync with editors (writing to ID classes in this context is not allowed)
        if not restricted:
            if addon_prefs.sync_selection:
                curr_sel = set(batch_cls.selection)
                diff_sel_neg = prev_sel - curr_sel
                diff_sel_pos = curr_sel - prev_sel
                if diff_sel_neg or diff_sel_pos:
                    with UndoBlock("Select"):
                        if diff_sel_neg: batch_cls.sync_obj_sel_partial(context, diff_sel_neg, False)
                        if diff_sel_pos: batch_cls.sync_obj_sel_partial(context, diff_sel_pos, True)
                #batch_cls.sync_obj_sel(context)
            
            if addon_prefs.sync_with_editors and batch_cls.selection:
                for area in context.screen.areas:
                    batch_cls.sync_editor(context, area)
        
        BlUI.tag_redraw()
    
    def check_double_click(context, idname=None):
        double_click_time = context.preferences.inputs.mouse_double_click_time / 1000.0
        click_time = time.perf_counter()
        double_click = (click_time - batch_cls.click_time) < double_click_time
        batch_cls.click_time = click_time
        if idname is not None:
            try:
                click_index = batch_cls.idnames.index(idname)
            except ValueError:
                click_index = -1
            if batch_cls.click_index != click_index: return False
        return double_click
    
    @simple_operator(f"{prefix}.click", f"Select {singular}", f"Select {singular.lower()}", {'INTERNAL'}, props=dict(idname = "" | prop(), mode = "" | prop()))
    def BatchOp(self, context, event):
        addon_prefs = addon.preferences
        double_click = check_double_click(context, self.idname)
        
        #dclick_mode = addon_prefs.double_click_mode
        #dclick_rename = (dclick_mode == 'RENAME')
        #dclick_select = (dclick_mode == 'SELECT')
        
        dclick_rename = addon_prefs.double_click_rename
        dclick_select = not dclick_rename
        
        dclick_rename_force = (double_click and event.shift and event.ctrl)
        dclick_rename |= dclick_rename_force
        
        dclick_rename &= double_click
        dclick_select &= double_click
        
        if event.alt or (self.mode == 'OPS_MENU'):
            select_idname(context, self.idname, 'ENSURE')
            if addon_prefs.use_pie_menu:
                bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name=f"VIEW3D_MT_{prefix}_pie")
            else:
                bpy.ops.wm.call_menu('INVOKE_DEFAULT', name=f"VIEW3D_MT_{prefix}")
        elif dclick_rename and hasattr(batch_cls, "rename"):
            if dclick_rename_force:
                batch_cls.selection = list(batch_cls.prev_sel)
            select_idname(context, self.idname, 'ADD')
            getattr(bpy.ops, prefix).rename('INVOKE_DEFAULT')
        elif dclick_select:
            if addon_prefs.always_toggle_selection:
                # negate the result of the previous "invert" click
                select_idname(context, self.idname, 'INVERT')
                curr_sel = set(batch_cls.selection)
                is_all_selected = curr_sel.issuperset(batch_cls.idnames)
                is_none_selected = curr_sel.isdisjoint(batch_cls.idnames)
                if self.idname in curr_sel:
                    if is_all_selected:
                        batch_select('NONE', context)
                    else:
                        batch_select('ALL', context)
                else:
                    batch_select('INVERT', context)
            else:
                # negate the result of the previous "invert" click
                batch_cls.selection = list(batch_cls.prev_sel)
                curr_sel = batch_cls.prev_sel
                is_all_selected = curr_sel.issuperset(batch_cls.idnames)
                is_none_selected = curr_sel.isdisjoint(batch_cls.idnames)
                if self.idname in curr_sel:
                    if is_all_selected:
                        batch_select('NONE', context)
                    else:
                        batch_select('ALL', context)
                else:
                    batch_select('INVERT', context)
                """
                if event.ctrl:
                    # negate the result of the previous "invert" click
                    select_idname(context, self.idname, 'INVERT')
                    batch_select('INVERT', context)
                elif event.shift:
                    batch_select('NONE', context)
                else:
                    batch_select('ALL', context)
                """
        else:
            batch_cls.prev_sel = set(batch_cls.selection)
            
            mode = ''
            if len(batch_cls.selection) == 1:
                if batch_cls.selection[0] == self.idname:
                    mode = 'INVERT'
            if addon_prefs.always_toggle_selection: mode = 'INVERT'
            if event.ctrl: mode = 'INVERT'
            if event.shift: mode = 'MULTI'
            select_idname(context, self.idname, mode)
        
        self.idname = "" # clean up, just in case
        
        BlUI.tag_redraw()
    
    @simple_operator(f"{prefix}.contextual_click", f"Contextual Click - {singular}", batch_cls.contextual_ops["description"], {'INTERNAL'}, props=dict(idname = "" | prop()))
    def BatchOp(self, context, event):
        addon_prefs = addon.preferences
        single_selection = addon_prefs.contextual_single_selection
        
        double_click = check_double_click(context)
        clicks = (2 if double_click else 1)
        key = (clicks, event.alt, event.ctrl, event.shift)
        op_info = batch_cls.contextual_ops.get(key)
        if not op_info: return False
        
        op_name, kwargs = op_info
        ops_category = getattr(bpy.ops, prefix)
        op = getattr(ops_category, op_name)
        if not op.poll(): return False
        
        selection = batch_cls.selection
        if single_selection or (self.idname not in batch_cls.selection):
            batch_cls.selection = [self.idname]
        else:
            batch_cls.selection = [idname for idname in batch_cls.selection if idname != self.idname]
            batch_cls.selection.append(self.idname) # makesure it's "last selected"
        op(**kwargs)
        batch_cls.selection = selection
        
        BlUI.tag_redraw()
    
    def batch_select(mode, context):
        addon_prefs = addon.preferences
        
        if mode == 'AUTO': mode = ('ALL' if set(batch_cls.selection).symmetric_difference(batch_cls.idnames) else 'NONE')
        
        if mode == 'NONE':
            batch_cls.selection.clear()
            batch_cls.click_index = -1
        else:
            for idname in batch_cls.idnames:
                if idname not in batch_cls.selection:
                    batch_cls.selection.append(idname)
                elif mode == 'INVERT':
                    batch_cls.selection.remove(idname)
        
        if addon_prefs.sync_selection:
            batch_cls.sync_obj_sel(context)
        
        BlUI.tag_redraw()
    
    @simple_operator(f"{prefix}.select_all", f"Select All {plural}", f"Select all {plural.lower()}", poll=batch_poll)
    def BatchOp(self, context):
        batch_select('ALL', context)
    
    @simple_operator(f"{prefix}.select_none", f"Deselect All {plural}", f"Deselect all {plural.lower()}", poll=batch_poll)
    def BatchOp(self, context):
        batch_select('NONE', context)
    
    @simple_operator(f"{prefix}.select_invert", f"Invert {plural} Selection", f"Invert {plural.lower()} selection", poll=batch_poll)
    def BatchOp(self, context):
        batch_select('INVERT', context)
    
    @simple_operator(f"{prefix}.sync_obj_sel", f"{plural} → Objects", "Sync objects to selected", poll=batch_poll)
    def BatchOp(self, context):
        batch_cls.sync_obj_sel(context)
        BlUI.tag_redraw()
    
    @simple_operator(f"{prefix}.sync_sel_obj", f"Objects → {plural}", "Sync selected to objects", poll=batch_poll)
    def BatchOp(self, context):
        batch_cls.sync_sel_obj(context)
        BlUI.tag_redraw()
    
    @simple_operator(f"{prefix}.enable_selection", f"Enable {plural} Selection", f"Enable selection for objects which use the selected {plural.lower()}", poll=batch_poll)
    def BatchOp(self, context):
        with UndoBlock(f"Enable Selection by {plural}"):
            for obj in batch_cls.filter(context.scene.objects, batch_cls.selected_idnames(context), context=context):
                obj.hide_select = False
        BlUI.tag_redraw()
    
    @simple_operator(f"{prefix}.disable_selection", f"Disable {plural} Selection", f"Disable selection for objects which use the selected {plural.lower()}", poll=batch_poll)
    def BatchOp(self, context):
        with UndoBlock(f"Disable Selection by {plural}"):
            for obj in batch_cls.filter(context.scene.objects, batch_cls.selected_idnames(context), context=context):
                obj.hide_select = True
        BlUI.tag_redraw()
    
    @simple_operator(f"{prefix}.show", f"Show {plural}", f"Show objects which use the selected {plural.lower()} (Click: viewport, Ctrl+Click: rendering)", poll=batch_poll)
    class BatchOp:
        viewport: True | prop()
        render: False | prop()
        def execute(self, context):
            with UndoBlock(f"Show by {plural}"):
                for obj in batch_cls.filter(context.scene.objects, batch_cls.selected_idnames(context), context=context):
                    if self.viewport: set_obj_hide(context, obj, False)
                    if self.render: obj.hide_render = False
            BlUI.tag_redraw()
            return {'FINISHED'}
        def invoke(self, context, event):
            self.viewport = not event.ctrl
            self.render = event.ctrl
            return self.execute(context)
    
    @simple_operator(f"{prefix}.hide", f"Hide {plural}", f"Hide objects which use the selected {plural.lower()} (Click: viewport, Ctrl+Click: rendering)", poll=batch_poll)
    class BatchOp:
        viewport: True | prop()
        render: False | prop()
        def execute(self, context):
            with UndoBlock(f"Hide by {plural}"):
                for obj in batch_cls.filter(context.scene.objects, batch_cls.selected_idnames(context), context=context):
                    if self.viewport: set_obj_hide(context, obj, True)
                    if self.render: obj.hide_render = True
            BlUI.tag_redraw()
            return {'FINISHED'}
        def invoke(self, context, event):
            self.viewport = not event.ctrl
            self.render = event.ctrl
            return self.execute(context)
    
    @simple_operator(f"{prefix}.toggle_show", f"Toggle {plural} Visibility", f"Toggle object visibility for selected {plural.lower()}", poll=batch_poll)
    def BatchOp(self, context):
        objs = batch_cls.filter(context.scene.objects, batch_cls.selected_idnames(context), context=context)
        value = None
        for obj in objs:
            value = (True if value is None else value) and (not get_obj_hide(context, obj))
        if value is None: return False
        with UndoBlock(f"{'Hide' if value else 'Show'} {plural}"):
            for obj in objs:
                set_obj_hide(context, obj, value)
                obj.hide_render = value
        BlUI.tag_redraw()
    
    if ("isolate" not in main_overrides):
        @simple_operator(f"{prefix}.isolate", f"Isolate By {plural}", f"Isolate objects which use the selected {plural.lower()} (Click: toggle isolate, Shift+Click: force isolate)", poll=batch_poll)
        class BatchOp:
            toggle: True | prop()
            mode: 'PREFS' | prop("Mute/Local view", "Mute others or use local view", items=[
                ('PREFS', "Use Prefs", "Use the addon preferences setting"),
                ('LOCAL_VIEW', "Local view", "Use local view"),
                ('MUTE', "Mute others", "Mute others"),
            ])
            
            def execute(self, context):
                addon_prefs = addon.preferences
                if self.mode == 'PREFS':
                    mute = (plural_up in addon_prefs.mute_on_isolate)
                else:
                    mute = (self.mode == 'MUTE')
                
                if mute:
                    view_objs = batch_cls.filter(context.scene.objects, AnyIDNames(), context=context, visible_only=True)
                    objs = batch_cls.filter(context.scene.objects, batch_cls.selected_idnames(context), context=context, visible_only=False)
                    
                    with UndoBlock(f"Isolate by {plural}"):
                        if self.toggle and (view_objs == objs):
                            for obj in batch_cls.filter(context.scene.objects, AnyIDNames(), context=context):
                                set_obj_hide(context, obj, False)
                        else:
                            for obj in view_objs.difference(objs):
                                set_obj_hide(context, obj, True)
                            for obj in objs:
                                set_obj_hide(context, obj, False)
                else:
                    view_3d = context.space_data
                    if not hasattr(view_3d, "local_view"): return
                    
                    depsgraph = bpy.context.evaluated_depsgraph_get()
                    local_view = view_3d.local_view
                    
                    def is_in_local_view(obj):
                        obj_eval = obj.evaluated_get(depsgraph)
                        return obj.local_view_get(view_3d) or obj_eval.local_view_get(view_3d)
                    
                    view_objs = {obj for obj in context.scene.objects if is_in_local_view(obj)} if local_view else set()
                    if local_view: bpy.ops.view3d.localview() # exit from local view
                    
                    unhide = addon_prefs.unhide_on_isolate
                    objs = batch_cls.filter(context.scene.objects, batch_cls.selected_idnames(context), context=context, visible_only=(not unhide))
                    do_local_view = not (self.toggle and (view_objs == objs))
                    
                    if do_local_view or unhide:
                        with UndoBlock(f"Isolate by {plural}"):
                            if unhide:
                                for obj in objs:
                                    set_obj_hide(context, obj, False)
                            
                            if do_local_view:
                                if bpy.ops.object.mode_set.poll():
                                    bpy.ops.object.mode_set(mode='OBJECT')
                                
                                bpy.ops.object.select_all(action='DESELECT')
                                
                                for obj in objs:
                                    BlUtil.Object.select_set(obj, True)
                                
                                bpy.ops.view3d.localview()
                
                BlUI.tag_redraw()
                
                return {'FINISHED'}
            
            def invoke(self, context, event):
                self.toggle = not event.shift
                return self.execute(context)
    
    if ("collect" not in main_overrides):
        @simple_operator(f"{prefix}.collect", f"Collect {plural}", f"Make a 'BatchOps' collection from all objects which use the selected {plural.lower()}", poll=batch_poll)
        def BatchOp(self, context):
            with UndoBlock(f"Collect {plural}"):
                batchops_collection = bpy.data.collections.get("BatchOps")
                if batchops_collection is None: batchops_collection = bpy.data.collections.new("BatchOps")
                if batchops_collection.name not in context.scene.collection.children:
                    context.scene.collection.children.link(batchops_collection)
                for obj in tuple(batchops_collection.objects):
                    batchops_collection.objects.unlink(obj)
                for obj in batch_cls.filter(bpy.data.objects, batch_cls.selected_idnames(context), context=context):
                    batchops_collection.objects.link(obj)
            BlUI.tag_redraw()
    
    if getattr(batch_cls, "copy", None) and ("copy" not in main_overrides):
        @simple_operator(f"{prefix}.copy", f"Copy {plural}", f"Copy {plural.lower()} (active object → clipboard)", poll=batch_poll)
        def BatchOp(self, context):
            batch_cls.copy(context.active_object)
            self.report({'INFO'}, f"Copy {plural.lower()}")
    
    if getattr(batch_cls, "paste", None) and ("paste" not in main_overrides):
        @simple_operator(f"{prefix}.paste", f"Paste {plural}", f"Paste {plural.lower()} (clipboard → selected objects) (Click: override, Shift+Click: append)", poll=batch_poll)
        class BatchOp:
            overwrite: True | prop()
            def execute(self, context):
                with UndoBlock(f"Paste {plural}"):
                    objs = filter_objs(context.selected_objects, context=context, subobjs=True)
                    batch_cls.paste(objs, overwrite=self.overwrite)
                    self.report({'INFO'}, f"Paste {plural.lower()}")
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.overwrite = not event.shift
                return self.execute(context)
    
    if getattr(batch_cls, "rename", None) and ("rename" not in main_overrides):
        @simple_operator(f"{prefix}.rename", f"Rename {plural}", f"Click: rename selected {plural.lower()}, Alt+Click: sync object/data/material names for objects with selected {plural.lower()}", poll=batch_poll)
        class BatchOp:
            name: "" | prop()
            use_pattern: True | prop(description="Use patterns:\n"+RenamePattern.__doc__.strip())
            sync_names: False | prop(description="Sync object/data/material names")
            sync_names_src: 'OBJECT' | prop("From", "Name source", items=[
                ('OBJECT', "Object", "Take name from object data"),
                ('DATA', "Object data", "Take name from object"),
            ])
            sync_names_dst: set() | prop("To", "Renaming targets", items=[
                ('OBJS', "Object", "Rename objects"),
                ('DATA', "Object data", "Rename object data"),
                ('MATS', "Materials", "Rename materials"),
            ])
            def execute(self, context):
                with UndoBlock(f"Rename {plural}"):
                    if self.sync_names:
                        filter = {key:True for key in self.sync_names_dst}
                        for obj in batch_cls.selected_objects(context, force_sync=True):
                            if self.sync_names_src == 'OBJECT':
                                sync_name(obj, filter)
                            else:
                                sync_name(obj.data, filter)
                    else:
                        if self.use_pattern:
                            batch_cls.pattern_rename(batch_cls.selected_idnames(context), self.name, context)
                        else:
                            batch_cls.rename(batch_cls.selected_idnames(context), self.name)
                self.sync_names = False # reset, just in case
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.sync_names = event.alt
                if not self.sync_names:
                    selected_idnames = set(batch_cls.selected_idnames(context))
                    if self.use_pattern:
                        if len(selected_idnames) == 1:
                            idname = next(iter(selected_idnames), "")
                            self.name = batch_cls.base_name(idname, "{name}")
                        else:
                            self.name = "{name}"
                    else:
                        best_name = None
                        for idname, name in zip(batch_cls.idnames, batch_cls.names):
                            if idname not in selected_idnames: continue
                            name = batch_cls.base_name(idname)
                            if (best_name is None) or (len(name) < len(best_name)):
                                best_name = name
                        self.name = best_name or ""
                return context.window_manager.invoke_props_dialog(self)
            def draw(self, context):
                if self.sync_names:
                    row = self.layout.row(align=True)
                    row.prop(self, "sync_names_src", text="From:")
                    row = self.layout.row(align=True)
                    row.label(text="To:")
                    if self.sync_names_src == 'OBJECT':
                        row.prop_enum(self, "sync_names_dst", 'DATA')
                    else:
                        row.prop_enum(self, "sync_names_dst", 'OBJS')
                    row.prop_enum(self, "sync_names_dst", 'MATS')
                else:
                    row = self.layout.row(align=True)
                    row.prop(self, "name", text="")
                    row2 = row.row(align=True)
                    row2.alignment = 'RIGHT'
                    row2.prop(self, "use_pattern", text="", icon='CONSOLE', toggle=True)
    
    if getattr(batch_cls, "add_new", None) and ("add_new" not in main_overrides):
        @simple_operator(f"{prefix}.add_new", f"New {singular}", f"Add a new {singular.lower()} to selected objects", poll=batch_poll)
        class BatchOp:
            if hasattr(batch_cls, "enum_items"):
                idname: '' | prop(items=batch_cls.enum_items) # empty string will be replaced by the first item
            else:
                idname: "" | prop()
            def execute(self, context):
                with UndoBlock(f"Add {singular}"):
                    batch_cls.add_new(batch_cls.selected_objects(context), self.idname)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                return context.window_manager.invoke_props_dialog(self)
            def draw(self, context):
                self.layout.prop(self, "idname", text="")
    
    if getattr(batch_cls, "make_unique", None) and ("make_unique" not in main_overrides):
        @simple_operator(f"{prefix}.make_unique", f"Make {plural} Unique/Duplicate", f"Make {plural.lower()} unique (Click: shared, Alt+Click: individual, Ctrl+Click: duplicate)", poll=batch_poll)
        class BatchOp:
            shared: True | prop()
            reuse: False | prop()
            def execute(self, context):
                with UndoBlock(f"Make {plural} Unique" if self.reuse else f"Duplicate {plural}"):
                    batch_cls.make_unique(batch_cls.selected_objects(context), batch_cls.selected_idnames(context), shared=self.shared, reuse=self.reuse)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.shared = not event.alt
                self.reuse = not event.ctrl
                return self.execute(context)
    
    if getattr(batch_cls, "assign", None) and ("assign" not in main_overrides):
        @simple_operator(f"{prefix}.assign", f"Assign {plural}", f"Assign {plural.lower()} to selected objects (Click: override, Shift+Click: append)", poll=batch_poll)
        class BatchOp:
            overwrite: True | prop()
            def execute(self, context):
                with UndoBlock(f"Assign {plural}"):
                    batch_cls.assign(batch_cls.selected_objects(context), batch_cls.selected_idnames(context), overwrite=self.overwrite)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.overwrite = not event.shift
                return self.execute(context)
    
    if getattr(batch_cls, "replace", None) and ("replace" not in main_overrides):
        @simple_operator(f"{prefix}.replace", f"Replace {plural}", f"Replace {plural.lower()} (Click: in selected objects, Ctrl+Click: globally, Alt+Click: with last selected)", poll=batch_poll)
        class BatchOp:
            idname: "" | prop()
            globally: False | prop()
            def execute(self, context):
                selected_idnames = batch_cls.selected_idnames(context)
                if len(selected_idnames) == 0: return {'CANCELLED'}
                with UndoBlock(f"Replace {plural}"):
                    objs = (bpy.data.objects if self.globally else batch_cls.selected_objects(context))
                    idname = self.idname
                    idnames = set(selected_idnames) - {idname}
                    batch_cls.replace(objs, idnames, idname)
                    if self.globally:
                        if hasattr(batch_cls, "remap"):
                            batch_cls.remap(idnames, idname)
                        batch_cls.delete(idnames)
                    self.idname = "" # a hack to force Blender to clear up the operator's property value (it seems that currently Blender 2.8 remembers operators' parameter values from their last call)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                if self.idname:
                    return self.execute(context)
                elif event.alt:
                    if len(batch_cls.selection) <= 1: return {'CANCELLED'}
                    self.globally = event.ctrl
                    self.idname = batch_cls.selection[-1]
                    return self.execute(context)
                else:
                    selected_idnames = batch_cls.selected_idnames(context)
                    if len(selected_idnames) == 0: return {'CANCELLED'}
                    globally = event.ctrl
                    def popup_draw(self, context):
                        layout = self.layout
                        layout.label(text=f"Replace {plural.lower()} with:", icon='AUTOMERGE_ON')
                        col = layout.column(align=True)
                        for idname, name in zip(batch_cls.idnames, batch_cls.names):
                            icon_data = batch_cls.icon_data(idname)
                            if icon_data is not None:
                                icon, icon_value = ((icon_data, 0) if isinstance(icon_data, str) else ('NONE', layout.icon(icon_data)))
                            else:
                                icon, icon_value = 'NONE', 0
                            op = col.operator(f"{prefix}.replace", text=name, icon=icon, icon_value=icon_value)
                            op.idname = idname
                            op.globally = globally
                    context.window_manager.popover(popup_draw)
                    return {'FINISHED'}
    
    if getattr(batch_cls, "replace", None) and ("remove" not in main_overrides):
        @simple_operator(f"{prefix}.remove", f"Remove {plural}", f"Remove {plural.lower()} from selected objects", poll=batch_poll)
        def BatchOp(self, context):
            with UndoBlock(f"Remove {plural}"):
                batch_cls.replace(batch_cls.selected_objects(context), batch_cls.selected_idnames(context), "")
            BlUI.tag_redraw()
    
    if getattr(batch_cls, "delete", None) and ("delete" not in main_overrides):
        @simple_operator(f"{prefix}.delete", f"Delete {plural}", f"Delete selected {plural.lower()}", poll=batch_poll)
        def BatchOp(self, context):
            with UndoBlock(f"Delete {plural}"):
                batch_cls.delete(batch_cls.selected_idnames(context))
            BlUI.tag_redraw()
    
    if getattr(batch_cls, "purge", None) and ("purge" not in main_overrides):
        @simple_operator(f"{prefix}.purge", f"Purge Unused {plural}", f"Purge unused {plural.lower()} (Click: with 0 users, Ctrl+Click: with 0 or fake users)", poll=batch_poll)
        class BatchOp:
            fake_users: False | prop()
            def execute(self, context):
                with UndoBlock(f"Purge unused {plural.lower()}"):
                    batch_cls.purge(self.fake_users)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.fake_users = event.ctrl
                return self.execute(context)
    
    if getattr(batch_cls, "merge_identical", None) and ("merge_identical" not in main_overrides):
        @simple_operator(f"{prefix}.merge_identical", f"Merge Identical {plural}", f"Merge identical {plural.lower()} (Click: among selected {plural.lower()}, Alt+Click: among {plural.lower()} of selected objects, Ctrl+Click: globally)", poll=batch_poll)
        class BatchOp:
            among_objects: False | prop()
            globally: False | prop()
            def execute(self, context):
                with UndoBlock(f"Merge identical {plural.lower()}"):
                    if self.globally:
                        idnames = None
                    elif self.among_objects:
                        idnames = set(item[0] for item in batch_cls.enumerate(batch_cls.selected_objects(context), context=context))
                    else:
                        idnames = batch_cls.selected_idnames(context)
                    batch_cls.merge_identical(idnames)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.among_objects = event.alt
                self.globally = event.ctrl
                return self.execute(context)
    
    @addon.Menu(idname=f"VIEW3D_MT_{prefix}_pie", label=f"Batch {plural}", description=f"Batch {plural}")
    class BatchOpsMenuPie:
        def draw(self, context):
            layout = self.layout
            pie = layout.menu_pie()
            self.draw_pie(context, pie)
        
        @staticmethod
        def draw_pie(context, pie):
            batch_cls.refresh(context)
            batch_cls_ops = set(dir(getattr(bpy.ops, prefix)))
            
            col = pie.column(align=True)
            col.operator(f"{prefix}.select_all", text="All", icon='RADIOBUT_ON')
            col.operator(f"{prefix}.select_none", text="None", icon='RADIOBUT_OFF')
            col.operator(f"{prefix}.select_invert", text="Inverse", icon='OVERLAY')
            col.separator()
            col.operator(f"{prefix}.sync_obj_sel", icon='EXPORT')
            col.operator(f"{prefix}.sync_sel_obj", icon='IMPORT')
            
            col = pie.column(align=True)
            col.operator(f"{prefix}.show", text="Show", icon='HIDE_OFF')
            col.operator(f"{prefix}.hide", text="Hide", icon='HIDE_ON')
            col.operator(f"{prefix}.isolate", text="Isolate", icon='SOLO_ON')
            col.separator()
            col.operator(f"{prefix}.enable_selection", text="Enable Selection", icon='RESTRICT_SELECT_OFF')
            col.operator(f"{prefix}.disable_selection", text="Disable Selection", icon='RESTRICT_SELECT_ON')
            if extras_view:
                col.separator()
                extras_view(col, context)
            if extras_select:
                col.separator()
                extras_select(col, context)
            
            #col = pie.column(align=True)
            row = pie.row()
            colL = row.box().column(align=True)
            col = row.column(align=True)
            colR = row.box().column(align=True)
            if "assign" in batch_cls_ops:
                col.operator(f"{prefix}.assign", text="Assign", icon='DECORATE_OVERRIDE')
            if "replace" in batch_cls_ops:
                col.operator(f"{prefix}.replace", text="Replace", icon='AUTOMERGE_ON')
            if "make_unique" in batch_cls_ops:
                col.operator(f"{prefix}.make_unique", text="Unique / Duplicate", icon='DUPLICATE')
            if "remove" in batch_cls_ops:
                col.operator(f"{prefix}.remove", text="Remove", icon='REMOVE')
            if "delete" in batch_cls_ops:
                col.operator(f"{prefix}.delete", text="Delete", icon='PANEL_CLOSE')
            if "add_new" in batch_cls_ops:
                col.operator(f"{prefix}.add_new", text="New", icon='ADD')
            if "merge_identical" in batch_cls_ops:
                col.operator(f"{prefix}.merge_identical", text="Merge Identical", icon='SORTBYEXT')
            
            if extras_main:
                col.separator()
                extras_main(col, context)
            
            #selected_idnames = batch_cls.selected_idnames(context)
            #cnt2 = (len(selected_idnames)+1) // 2
            #for idname in selected_idnames[:cnt2]:
            #    colL.label(text=idname)
            #for idname in selected_idnames[cnt2:]:
            #    colR.label(text=idname)
    
    @addon.Menu(idname=f"VIEW3D_MT_{prefix}_select", label="Select", description="Select")
    class BatchOpsMenuSelect:
        def draw(self, context):
            layout = self.layout
            layout.operator_context = 'INVOKE_DEFAULT'
            
            layout.operator(f"{prefix}.select_all", text="All", icon='RADIOBUT_ON')
            layout.operator(f"{prefix}.select_none", text="None", icon='RADIOBUT_OFF')
            layout.operator(f"{prefix}.select_invert", text="Inverse", icon='OVERLAY')
            layout.separator()
            layout.operator(f"batch_ops.sync_obj_sel", icon='EXPORT')
            layout.operator(f"{prefix}.sync_obj_sel", icon='EXPORT')
            layout.operator(f"{prefix}.sync_sel_obj", icon='IMPORT')
            layout.separator()
            layout.operator(f"{prefix}.enable_selection", text="Enable Selection", icon='RESTRICT_SELECT_OFF')
            layout.operator(f"{prefix}.disable_selection", text="Disable Selection", icon='RESTRICT_SELECT_ON')
            
            if extras_select:
                layout.separator()
                extras_select(layout, context)
    
    @addon.Menu(idname=f"VIEW3D_MT_{prefix}_show_hide", label="View", description="View")
    class BatchOpsMenuView:
        def draw(self, context):
            layout = self.layout
            layout.operator_context = 'INVOKE_DEFAULT'
            
            layout.operator(f"{prefix}.show", text="Show", icon='HIDE_OFF')
            layout.operator(f"{prefix}.hide", text="Hide", icon='HIDE_ON')
            layout.operator(f"{prefix}.isolate", text="Isolate", icon='SOLO_ON')
            
            if extras_view:
                layout.separator()
                extras_view(layout, context)
    
    @addon.Menu(idname=f"VIEW3D_MT_{prefix}", label="Operations", description="Operations")
    class BatchOpsMenu:
        def draw(self, context):
            layout = self.layout
            layout.operator_context = 'INVOKE_DEFAULT'
            
            batch_cls.refresh(context)
            batch_cls_ops = set(dir(getattr(bpy.ops, prefix)))
            
            # Note: hasattr() for bpy.ops categories always returns True
            layout.menu(f"VIEW3D_MT_{prefix}_select")
            layout.separator()
            layout.menu(f"VIEW3D_MT_{prefix}_show_hide")
            if "copy" in batch_cls_ops:
                layout.separator()
                layout.operator(f"{prefix}.copy", text="Copy", icon='COPYDOWN')
                layout.operator(f"{prefix}.paste", text="Paste", icon='PASTEDOWN')
            layout.separator()
            if "assign" in batch_cls_ops:
                layout.operator(f"{prefix}.assign", text="Assign", icon='DECORATE_OVERRIDE')
            if "replace" in batch_cls_ops:
                layout.operator(f"{prefix}.replace", text="Replace", icon='AUTOMERGE_ON')
            if "make_unique" in batch_cls_ops:
                layout.operator(f"{prefix}.make_unique", text="Unique / Duplicate", icon='DUPLICATE')
            if "remove" in batch_cls_ops:
                layout.operator(f"{prefix}.remove", text="Remove", icon='REMOVE')
            if "delete" in batch_cls_ops:
                layout.operator(f"{prefix}.delete", text="Delete", icon='PANEL_CLOSE')
            if "add_new" in batch_cls_ops:
                layout.operator(f"{prefix}.add_new", text="New", icon='ADD')
            layout.separator()
            if "rename" in batch_cls_ops:
                layout.operator(f"{prefix}.rename", text="Rename", icon='OUTLINER_DATA_FONT')
                layout.separator()
            if ("purge" in batch_cls_ops) or ("merge_identical" in batch_cls_ops):
                if "purge" in batch_cls_ops:
                    layout.operator(f"{prefix}.purge", text="Purge", icon='ORPHAN_DATA')
                if "merge_identical" in batch_cls_ops:
                    layout.operator(f"{prefix}.merge_identical", text="Merge Identical", icon='SORTBYEXT')
                layout.separator()
            layout.operator(f"{prefix}.collect", text="Collect", icon='GROUP')
            
            if extras_main:
                layout.separator()
                extras_main(layout, context)
    
    batch_cls.context_btn_id = f"{prefix.upper()}_OT_click"
    batch_cls.context_btn_draw = BatchOpsMenu.draw
    batch_cls.draw_pie = BatchOpsMenuPie.draw_pie
    batch_cls.draw_panel_header = BatchOpsPanelBase.draw_header
    batch_cls.draw_panel = BatchOpsPanelBase.draw
    batch_cls.select_idname = select_idname

# =========================================================================== #

class RenamePattern:
    """
{sort:<REVERSE><KEY>} - sorting key and order
    <REVERSE>: use minus sign (-) for reverse sort
    <KEY>: empty string or one of (name, obj, data, collection,
        p.x, p.y, p.z, s.x, s.y, s.z, d.x, d.y, d.z)
{id:<PADDING><START>:<STEP>} - index
    <PADDING>: any characters except minus (-), 0-9 and A-Z
    <START>: any number or english letter
    <STEP>: any non-zero number
{name} - name of the slot in the Batch panel
{scene} - name of the current scene
{obj}, {data}, {collection} - name of the matching object, its data or collection
Operations for name-like patterns (e.g. {name: <OP1>, <OP2>, ...}):
    Slice: <START>:<END>:<STEP> - extracts a substring
        See Python slicing notation for more details
    Find: <TARGET> - returns a matching substring
        Values in double quotes (") are treated as regular
        expressions, otherwise they are taken literally
    Replace: <TARGET>=<REPLACEMENT> - substring replacement
        Values are interpreted the same as in Find operation.
    """
    
    re_q1 = r"'(?:[^'])*'"
    re_q2 = r'"(?:[^"\\]|\\.)*"'
    re_tag = "(sort|id|name|scene|obj|data|collection)"
    re_arg = "(?:%s)|(?:%s)|(?:%s)" % (re_q1, re_q2, "[^'\"}]+")
    re_args = "((?:%s)*)" % re_arg
    re_main = "%s(?:(?: *:)%s)?(?:})" % (re_tag, re_args)
    re_nonzero = "-?[1-9][0-9]*"
    re_number = "-?[0-9]+"
    re_az = "[A-Za-z]+"
    
    re_main = re.compile(re_main)
    re_nonzero = re.compile(re_nonzero)
    re_number = re.compile(re_number)
    re_az = re.compile(re_az)
    re_arg = re.compile(re_arg)
    
    re_slice_part = "(/)? *(?:(?:\\*) *([0-9]+))? *((?:[+\\-]) *[0-9]+)"
    re_slice_full = "(?:(\\-)? *([^0-9:+\\-\\*/,]+)) *%s?" % re_slice_part
    re_slice_full = "(?:%s)|([+\\-]? *[0-9]+)" % re_slice_full
    
    re_slice_part = re.compile(re_slice_part)
    re_slice_full = re.compile(re_slice_full)
    
    def __init__(self, pattern):
        self.sort_key = ""
        self.sort_ascending = True
        self.parts = []
        self.tags = set()
        i0 = 0
        while True:
            i = pattern.find("{", i0)
            if i < 0:
                if i0 < len(pattern): self.parts.append(pattern[i0:])
                break
            else:
                if i0 < i: self.parts.append(pattern[i0:i])
                part, i0 = self.parse_subpattern(pattern, i+1)
                if part:
                    self.parts.append(part)
                elif i0 == i+1:
                    self.parts.append(pattern[i])
    
    def __call__(self, info):
        res = []
        for part in self.parts:
            if isinstance(part, str):
                res.append(part)
            else:
                res.append(part(info))
        return "".join(res)
    
    def parse_subpattern(self, pattern, i):
        match = self.re_main.match(pattern, i)
        if not match: return None, i
        tag, args = match.groups()
        self.tags.add(tag)
        if tag == "sort":
            self.parse_sort(args)
            return None, match.end()
        elif tag == "id":
            transform = self.parse_id(args)
        else:
            transform = self.parse_names(tag, args)
        return transform, match.end()
    
    def parse_sort(self, args):
        self.sort_key = (args.strip() if args else "")
        self.sort_ascending = True
        if self.sort_key.startswith("-"):
            self.sort_key = self.sort_key[1:].strip()
            self.sort_ascending = False
    
    def parse_id(self, args):
        argI, _, argD = (args.partition(":") if args else ("", "", ""))
        
        padding, id_start, id_increment = argI, "", 1
        
        converter = str
        
        match = self.re_number.search(argI)
        match_az = self.re_az.search(argI)
        if match or match_az:
            if match_az:
                match = match_az
                id_start = match.group()
                if id_start[0].islower():
                    converter = self.to_letters
                else:
                    converter = (lambda value: self.to_letters(value).upper())
                id_start = self.from_letters(id_start.lower())
            else:
                id_start = int(match.group())
            i = match.start()
            padding = argI[:i] + (argI[i-1]*(match.end()-i) if i > 0 else "")
        
        match = self.re_nonzero.match(argD.replace(" ", ""))
        if match:
            id_increment = int(match.group())
        
        def transform(info):
            id = info["id"] * id_increment
            if id_start != "":
                id += id_start
            elif id == 0:
                id = ""
            id = converter(id)
            return padding[:max(len(padding)-len(id), 0)] + id
        
        return transform
    
    @staticmethod
    def to_letters(value, chr_start="a", chr_end="z"):
        if value < 0: return ""
        ord_start = ord(chr_start)
        ord_size = ord(chr_end) - ord_start + 1
        result = ""
        while True:
            value, digit = divmod(value, ord_size)
            result = chr(ord_start + digit) + result
            if value <= 0: break
            value -= 1
        return result
    
    @staticmethod
    def from_letters(value, chr_start="a", chr_end="z"):
        ord_start = ord(chr_start)
        ord_size = ord(chr_end) - ord_start + 1
        result = 0
        for i, c in enumerate(reversed(value)):
            digit = ord(c) - ord_start
            if i > 0: digit += 1
            result += digit * (ord_size ** i)
        return result
    
    @staticmethod
    def try_int(s, default):
        if not s: return default
        try:
            return int(s.replace(" ", ""))
        except ValueError:
            return default
    
    def parse_slice_part(self, arg, slice_arg):
        match = self.re_slice_part.fullmatch(arg.strip())
        if match:
            slice_arg["endpos"] = bool(match.group(1))
            slice_arg["count"] = self.try_int(match.group(2), None)
            slice_arg["offset"] = self.try_int(match.group(3), None)
    
    def parse_slice_full(self, arg, slice_arg):
        match = self.re_slice_full.fullmatch(arg.strip())
        if match:
            slice_arg["reverse"] = bool(match.group(1))
            slice_arg["find"] = match.group(2)
            slice_arg["endpos"] = bool(match.group(3))
            slice_arg["count"] = self.try_int(match.group(4), None)
            slice_arg["offset"] = self.try_int(match.group(5) or match.group(5), None)
    
    def parse_slice_start(self, commands, slice_args):
        slice_start = {}
        if commands and (commands[-1][0] == "find"):
            slice_start["find"] = commands.pop()[1]
            if commands and (commands[-1][0] == "-"):
                slice_start["reverse"] = bool(commands.pop())
            self.parse_slice_part(slice_args[0], slice_start)
        else:
            self.parse_slice_full(slice_args[0], slice_start)
        return slice_start
    
    def parse_slice_end(self, commands, slice_args):
        slice_end = {}
        if slice_args[1] == "-":
            slice_end["reverse"] = True
        else:
            self.parse_slice_full(slice_args[1], slice_end)
        return slice_end
    
    def slice_arg_to_func(self, slice_arg):
        if not isinstance(slice_arg, tuple): return (lambda s: slice_arg)
        pattern, count, endpos, offset = slice_arg
        if count == 0: return (lambda s: None)
        def f_start(s):
            if count == 1:
                match = pattern.search(s)
                if not match: return None
            elif count > 0:
                matches = list(pattern.finditer(s))
                if not matches: return None
                if len(matches) < count: return len(s)
                match = matches[count-1]
            else:
                matches = list(pattern.finditer(s))
                if not matches: return None
                if len(matches) < -count: return 0
                match = matches[count]
            pos = (match.end() if endpos else match.start())
            return min(max(pos+offset, 0), len(s))
        return f_start
    
    def _map_collections(self):
        collection_map = {}
        gp_filter = group_pro_collection_filter()
        for i, collection in enumerate(bpy.data.collections):
            if gp_filter and not gp_filter(collection): continue
            for obj in collection.objects:
                collection_map[obj] = collection
        return collection_map
    
    def key_getter(self, tag):
        if tag == "name":
            def get_key(info):
                return info["name"]
        elif tag == "scene":
            def get_key(info):
                return info["context"].scene.name
        elif tag == "obj":
            def get_key(info):
                obj = info["obj"]
                return (obj.name if obj else "")
        elif tag == "data":
            def get_key(info):
                obj = info["obj"]
                if not obj: return ""
                data = obj.data
                return (data.name if data else "")
        elif tag == "collection":
            collection_map = self._map_collections()
            def get_key(info):
                obj = info["obj"]
                if not obj: return ""
                collection = collection_map.get(obj)
                return (collection.name if collection else "")
        elif tag in ("p.x", "p.y", "p.z"):
            axis = tag[-1]
            def get_key(info):
                obj = info["obj"]
                return (getattr(obj.location, axis) if obj else float("-inf"))
        elif tag in ("s.x", "s.y", "s.z"):
            axis = tag[-1]
            def get_key(info):
                obj = info["obj"]
                return (getattr(obj.scale, axis) if obj else float("-inf"))
        elif tag in ("d.x", "d.y", "d.z"):
            axis = tag[-1]
            def get_key(info):
                obj = info["obj"]
                return (getattr(obj.dimensions, axis) if obj else float("-inf"))
        else:
            get_key = None
        
        return get_key
    
    def parse_names(self, tag, args):
        get_name = self.key_getter(tag)
        
        commands = []
        if args:
            for match in self.re_arg.finditer(args):
                if args[match.start()] in "\"'":
                    expr = match.group()
                    expr = ((expr[1:-1],) if expr.startswith('"') else expr[1:-1])
                    if commands and (commands[-1][0] == "replace"):
                        commands[-1][2] = expr
                    elif commands and (commands[-1][0] == "slice"):
                        slice_info = commands[-1][1]
                        if "step" not in slice_info:
                            slice_info["end"]["find"] = expr
                    else:
                        commands.append(["find", expr])
                else:
                    for subarg_i, subarg in enumerate(match.group().split(",")):
                        if "=" in subarg:
                            src, _, dst = subarg.partition("=")
                            src, dst = src.strip(), dst.strip()
                            if not src:
                                if commands and (commands[-1][0] == "find"):
                                    src = commands.pop()[1]
                            commands.append(["replace", src, dst])
                        elif ":" in subarg:
                            slice_args = [slice_arg.strip() for slice_arg in subarg.split(":")]
                            if (subarg_i == 0) and (commands and (commands[-1][0] == "slice")):
                                slice_info = commands[-1][1]
                                if "step" not in slice_info:
                                    self.parse_slice_part(slice_args[0], slice_info["end"])
                                    slice_info["step"] = self.try_int(slice_args[1], None)
                            else:
                                slice_start = self.parse_slice_start(commands, slice_args)
                                slice_end = self.parse_slice_end(commands, slice_args)
                                slice_info = {"start": slice_start, "end": slice_end}
                                if len(slice_args) > 2:
                                    slice_info["step"] = self.try_int(slice_args[2], None)
                                commands.append(["slice", slice_info])
                        elif (subarg_i == 0) and (commands and (commands[-1][0] == "slice")):
                            slice_info = commands[-1][1]
                            if "step" not in slice_info:
                                self.parse_slice_part(subarg.strip(), slice_info["end"])
                        elif subarg.strip() == "-":
                            commands.append(["-"])
                        else:
                            commands.append([""]) # make sure commands aren't accidentally joined
            
            def arg_compile(arg):
                if isinstance(arg, str): return re.compile(re.escape(arg))
                try:
                    return re.compile(arg[0])
                except:
                    return None
            
            def arg_escape(arg):
                if isinstance(arg, str): return arg.replace('\\', r'\\')
                return arg[0]
            
            def arg_slice(arg):
                offset = arg.get("offset")
                find = arg.get("find")
                pattern = (arg_compile(find) if find else None)
                if not pattern: return offset
                endpos = bool(arg.get("endpos"))
                count = arg.get("count")
                if count is None: count = 1
                if arg.get("reverse"): count = -count
                return (pattern, count, endpos, offset or 0)
            
            for command in commands:
                if command[0] in ("find", "replace"):
                    command[1] = arg_compile(command[1])
                    if len(command) > 2: command[2] = arg_escape(command[2])
                elif command[0] == "slice":
                    slice_info = command[1]
                    arg_start = arg_slice(slice_info.get("start"))
                    arg_end = arg_slice(slice_info.get("end"))
                    arg_step = slice_info.get("step", 1)
                    command[1] = (arg_start, arg_end, arg_step)
        
        operations = []
        for command in commands:
            if command[0] == "slice":
                arg_start, arg_end, arg_step = command[1]
                arg_start = self.slice_arg_to_func(arg_start)
                arg_end = self.slice_arg_to_func(arg_end)
                def operation(f0, f1, d, s):
                    return s[f0(s):f1(s):d]
                operations.append(functools.partial(operation, arg_start, arg_end, arg_step))
            elif command[0] == "find":
                if command[1] is None: continue
                def operation(arg, s):
                    match = arg.search(s)
                    return (match.group() if match else "")
                operations.append(functools.partial(operation, command[1]))
            elif command[0] == "replace":
                if command[1] is None: continue
                def operation(arg, arg2, s):
                    return arg.sub(arg2, s)
                operations.append(functools.partial(operation, command[1], command[2]))
        
        def transform(info):
            name = get_name(info)
            for operation in operations:
                name = operation(name)
            return name
        
        return transform

class BatchOps:
    icon = 'NONE'
    
    contextual_ops = { # (clicks, alt, ctrl, shift)
        "description": "Click: select objects, Alt+Click: isolate, Alt+Ctrl+Click: delete",
        (1, False, False, False): ("sync_obj_sel", {}),
        (1, True, False, False): ("isolate", {}),
        (1, True, True, False): ("delete", {}),
    }
    
    @classmethod
    def poller(cls):
        def poll(op_cls, context):
            addon_prefs = addon.preferences
            return cls.plural_up in addon_prefs.categories
        return poll
    
    @classmethod
    def _map_idnames(cls, context, objs, visible_only=False):
        addon_prefs = addon.preferences
        filters_prefs_wm = get_screen_prefs(context, 'FILTERS')
        filters_prefs = get_screen_prefs(context, 'FILTERS', True)
        
        filter_name = ""
        if getattr(filters_prefs, f"{cls.singular_low}_search_on"):
            filter_name = getattr(filters_prefs_wm, f"{cls.singular_low}_search")
        filter_name = filter_name.lower()
        
        map_names = {}
        map_users = {}
        map_states = {}
        for idname, name, users, index, states in cls.enumerate(objs, context=context, visible_only=visible_only):
            if addon_prefs.ignore_dot_names and idname.startswith("."): continue
            if filter_name not in name.lower(): continue
            map_names[idname] = name
            map_users[idname] = map_users.get(idname, 0) + users
            states_set = map_states.get(idname)
            if states_set is None:
                states_set = set()
                map_states[idname] = states_set
            if states is not None: states_set.add(states)
        idnames = sorted(map_names.keys())
        
        return idnames, map_names, map_users, map_states
    
    @classmethod
    def refresh(cls, context):
        cls.dirty |= (context.scene != cls.scene)
        cls.dirty |= (context.view_layer != cls.view_layer)
        if not cls.dirty: return
        
        addon_prefs = addon.preferences
        filters_prefs = get_screen_prefs(context, 'FILTERS', True)
        
        visible_only = False
        filter_mode = getattr(filters_prefs, f"{cls.singular_low}_filter")
        if filter_mode == 'SCENE':
            objs = context.scene.objects
        elif filter_mode == 'LAYER':
            objs = context.view_layer.objects
        elif filter_mode == 'VISIBLE':
            objs = context.visible_objects
            visible_only = True
        elif filter_mode == 'SELECTION':
            objs = context.selected_objects
        else: # 'FILE'
            objs = None
        
        idnames, map_names, map_users, map_states = cls._map_idnames(context, objs, visible_only=visible_only)
        
        if filter_mode == 'SELECTION':
            obj_sel = set(idnames)
        else:
            obj_sel = set(item[0] for item in cls.enumerate(context.selected_objects, context=context))
        
        if addon_prefs.sync_selection:
            cls.sync_sel_refresh(context, obj_sel)
        elif idnames != cls.idnames:
            cls.selection = []
            cls.click_index = -1
        
        def eval_state(state):
            if len(state) > 1: return None
            state = next(iter(state), None)
            return (state != False)
        
        cls.idnames = idnames
        cls.names = [map_names[idname] for idname in idnames]
        cls.users = [map_users[idname] for idname in idnames]
        cls.states = [eval_state(map_states[idname]) for idname in idnames]
        cls.obj_sel = [(idname in obj_sel) for idname in idnames]
        cls.scene = context.scene
        cls.view_layer = context.view_layer
        cls.dirty = False
    
    @classmethod
    def idname_index(cls, idname):
        try:
            return cls.idnames.index(idname)
        except ValueError:
            return -1
    
    @classmethod
    def base_name(cls, id, default=None):
        # should be overridden by categories which display modified name
        if isinstance(id, str): id = cls.idname_index(id)
        if (id < 0) or (id >= len(cls.names)): return default
        return cls.names[id]
    
    @classmethod
    def pattern_rename(cls, idnames, pattern, context=None, **kwargs):
        if not hasattr(cls, "rename"): return
        
        if context is None: context = bpy.context
        
        rp = RenamePattern(pattern)
        current_info = dict(id=0, idname="", name="", obj=None, context=context)
        dummy_info = dict(id=0, idname="", name="", obj=None, context=context)
        
        needs_obj = not rp.tags.isdisjoint(["obj", "data", "collection"])
        needs_obj |= rp.sort_key in ["obj", "data", "collection",
            "p.x", "p.y", "p.z", "s.x", "s.y", "s.z", "d.x", "d.y", "d.z"]
        if needs_obj:
            obj_map = cls.map_objects()
        
        def setup_info(id, idname):
            try:
                i = cls.idnames.index(idname)
            except ValueError:
                return dummy_info
            current_info["id"] = id
            current_info["idname"] = idname
            current_info["name"] = cls.base_name(i)
            if needs_obj:
                mapped_objs = obj_map.get(idname)
                current_info["obj"] = (mapped_objs[0] if mapped_objs else None)
            return current_info
        
        get_key = rp.key_getter(rp.sort_key)
        if rp.sort_key == "name":
            idnames = sorted(idnames, reverse=(not rp.sort_ascending))
        elif get_key:
            idnames = sorted(idnames, reverse=(not rp.sort_ascending),
                key=(lambda idname: get_key(setup_info(0, idname))))
        elif not rp.sort_ascending:
            idnames = reversed(idnames)
        
        new_names = []
        for id, idname in enumerate(idnames):
            info = setup_info(id, idname)
            if not info["idname"]: continue
            new_names.append(rp(info))
        
        name_remap = cls.rename(idnames, new_names, **kwargs)
        
        click_index = ""
        if cls.click_index >= 0:
            click_index = cls.idnames[cls.click_index]
            click_index = name_remap.get(click_index, click_index)
            if not isinstance(click_index, str): click_index = click_index[0]
        
        selection = []
        for idname in cls.selection:
            new_idname = name_remap.get(idname)
            if isinstance(new_idname, str):
                selection.append(new_idname)
            elif new_idname: # can be None
                selection.extend(new_idname)
        
        cls.dirty = True # force refresh
        cls.refresh(context)
        cls.selection = selection
        try:
            cls.click_index = cls.idnames.index(click_index)
        except ValueError:
            pass
    
    @classmethod
    def map_objects(cls):
        result = {}
        objs = [None]
        for obj in bpy.data.objects:
            objs[0] = obj
            for idname, name, users, index, states in cls.enumerate(objs, raw=True):
                mapped = result.get(idname)
                if mapped is None:
                    mapped = []
                    result[idname] = mapped
                mapped.append(obj)
        return result
    
    @classmethod
    def _selected_objects(cls, context, force_sync=False):
        addon_prefs = addon.preferences
        if not force_sync:
            if context.selected_objects: return context.selected_objects
        scene_objs = context.scene.objects
        return [obj for obj in cls.filter(scene_objs, cls.selection, context=context) if not obj.hide_select]
    @classmethod
    def selected_objects(cls, context, force_sync=False):
        objs = cls._selected_objects(context, force_sync)
        return filter_objs(objs, context=context, subobjs=True)
    
    @classmethod
    def selected_idnames(cls, context, force_sync=False):
        addon_prefs = addon.preferences
        if not force_sync:
            if cls.selection: return cls.selection
        return cls._map_idnames(context, context.selected_objects)[0]
    
    @classmethod
    def sync_editor(cls, context, area):
        pass
    
    @classmethod
    def sync_sel_refresh(cls, context, obj_sel):
        cls.selection = sorted(obj_sel)
    
    @classmethod
    def sync_obj_sel_partial(cls, context, idnames, state):
        best_obj = None # just in case filter() results in an empty enumeration
        for obj in cls.filter(context.scene.objects, idnames, context=context):
            if not obj.hide_select:
                BlUtil.Object.select_set(obj, state)
                if state: best_obj = obj
        if best_obj: BlUtil.Object.active_set(obj, context.view_layer)
    
    @classmethod
    def sync_obj_sel(cls, context):
        with UndoBlock("Select"):
            objs = cls.selected_objects(context, force_sync=True)
            BlUtil.Object.select_activate(objs, 'SOLO', active='ANY', view_layer=context.view_layer)
    
    @classmethod
    def sync_sel_obj(cls, context):
        cls.selection = cls.selected_idnames(context, force_sync=True)

class ObjectFilter:
    def __init__(self, *callbacks, context=None, visible_only=False):
        if context is None: context = bpy.context
        self.callbacks = callbacks
        self.context = context
        self.visible_only = visible_only
        self.include_instances = addon.preferences.include_instances
        self.coll_child_maps = {}
        self.res_cache = {}
        self.main_child_map = self.map_children(context.scene.collection)
    
    def __call__(self, objs, subobjs=False):
        result = set()
        
        for obj in objs:
            obj_set = set()
            self.add_obj(obj_set, obj, self.main_child_map)
            if not subobjs:
                if self.test_objs(obj_set): result.add(obj)
            else:
                for subobj in obj_set:
                    if self.test_obj(subobj): result.add(subobj)
        
        return result
    
    def map_children(self, coll):
        child_map = self.coll_child_maps.get(coll)
        if child_map is None:
            child_map = {}
            for obj in coll.all_objects:
                parent = obj.parent
                children = child_map.get(parent)
                if children: children.append(obj)
                else: child_map[parent] = [obj]
            self.coll_child_maps[coll] = child_map
        return child_map
    
    def add_children_obj(self, obj_set, obj, child_map):
        for child in child_map.get(obj, ()):
            self.add_obj(obj_set, child, None)
            self.add_children_obj(obj_set, child, child_map)
    
    def add_children_coll(self, obj_set, coll):
        if not coll: return
        child_map = self.map_children(coll)
        obj_subset = set()
        for obj in coll.objects:
            self.add_obj(obj_subset, obj, child_map)
        obj_set.update(obj_subset)
        for child in coll.children:
            self.add_children_coll(obj_set, child)
    
    def add_obj(self, obj_set, obj, child_map):
        if self.visible_only and get_obj_hide(self.context, obj): return
        obj_set.add(obj)
        if self.include_instances:
            if obj.instance_type == 'COLLECTION':
                self.add_children_coll(obj_set, obj.instance_collection)
            elif obj.instance_type in ('VERTS', 'FACES'):
                if child_map: self.add_children_obj(obj_set, obj, child_map)
    
    def test_obj(self, obj):
        res = self.res_cache.get(obj)
        if res is None:
            res = all(callback(obj) for callback in self.callbacks)
            self.res_cache[obj] = res
        return res
    
    def test_objs(self, objs):
        return any(self.test_obj(obj) for obj in objs)

def filter_objs(objs, *callbacks, context=None, subobjs=False, visible_only=False):
    obj_filter = ObjectFilter(*callbacks, context=context, visible_only=visible_only)
    return obj_filter(objs, subobjs=subobjs)

# =========================================================================== #

# Regular modifiers
# Grease Pencil modifiers
# Constraints
# Bone Constraints
# Shader effects
class BatchOps_ModStack(BatchOps):
    separator = "\x1f"
    
    @classmethod
    def _remove_suffix(cls, name):
        i = name.rfind(".")
        if (i >= 0) and name[i+1:].isdecimal(): return name[:i]
        return name
    
    @classmethod
    def idname(cls, item):
        return cls.idname_and_name(item)[0]
    
    @classmethod
    def idname_and_name(cls, item):
        naming_mode = addon.preferences.modstack_naming
        if naming_mode == 'TYPE':
            return item.type, cls.dict_items[item.type][1]
        name = item.name
        if naming_mode == 'SMART_NAME':
            name = cls._remove_suffix(name)
        return f"{item.type}{cls.separator}{name}", name
    
    @classmethod
    def get_item_type(cls, idname):
        i = idname.find(cls.separator)
        return (idname if i < 0 else idname[:i])
    
    @classmethod
    def get_item_name(cls, idname):
        i = idname.find(cls.separator)
        return (cls.dict_items[idname][1] if i < 0 else idname[i+1:])
    
    @classmethod
    def icon_data(cls, idname):
        item = cls.dict_items.get(cls.get_item_type(idname))
        if not item: return None
        return item[-2]
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        if objs is None:
            objs = bpy.data.objects
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
        
        flags = cls.toggle_enabled_flags
        
        for obj in objs:
            for i, item in enumerate(cls.get_stack(obj)):
                state = (getattr(item, flags[0]) if BlUtil.Object.select_get(obj) else None)
                idname, name = cls.idname_and_name(item)
                yield (idname, name, 1, i, state)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            for item in cls.get_stack(obj):
                if cls.idname(item) in idnames: return True
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def copy(cls, obj):
        if not obj:
            cls.clipboard = []
        else:
            cls.clipboard = [BlRna.serialize(item) for item in cls.get_stack(obj)]
    
    @classmethod
    def paste(cls, objs, clipboard=None, overwrite=True):
        if clipboard is None: clipboard = cls.clipboard
        if clipboard is None: return
        for obj in objs:
            if overwrite: cls.stack_clear(obj)
            cls.stack_paste(obj, 'AFTER', *clipboard)
    
    @classmethod
    def add_new(cls, objs, type_name):
        type_name = cls.get_item_type(type_name) # just in case
        for obj in objs:
            cls.stack_paste(obj, 'AFTER', dict(name=cls.dict_items[type_name][1], type=type_name))
    
    @classmethod
    def assign(cls, objs, idnames, overwrite=True):
        clipboard = []
        for idname in idnames:
            if not idname:
                clipboard.append(None)
            else:
                clipboard.append(dict(name=cls.get_item_name(idname), type=cls.get_item_type(idname)))
        cls.paste(objs, clipboard, overwrite=overwrite)
    
    @classmethod
    def replace(cls, objs, idnames, idname):
        item_info = (dict(name=cls.get_item_name(idname), type=cls.get_item_type(idname)) if idname else None)
        for obj in objs:
            for i, item in enumerate(tuple(cls.get_stack(obj))):
                if cls.idname(item) not in idnames: continue
                cls.stack_paste(obj, item, item_info)
    
    @classmethod
    def delete(cls, idnames):
        cls.replace(bpy.data.objects, idnames, "")
    
    @classmethod
    def rename(cls, idnames, name):
        names = ([name]*len(idnames) if isinstance(name, str) else name)
        items_map = {}
        objs = cls.selected_objects(bpy.context)
        for obj in objs:
            for i, item in enumerate(tuple(cls.get_stack(obj))):
                idname = cls.idname(item)
                if idname not in idnames: continue
                item.name = names[idnames.index(idname)]
                items_map.setdefault(idname, []).append(item)
        return {idname: [cls.idname(item) for item in items] for idname, items in items_map.items()}
    
    @classmethod
    def sync_editor(cls, context, area):
        space = area.spaces.active
        if area.type == 'PROPERTIES':
            try:
                space.context = cls.area_space_context
            except TypeError:
                return
    
    @classmethod
    def stack_paste(cls, obj, where, *item_infos):
        replace_item = (None if (not where) or isinstance(where, str) else where)
        
        insert_index = -1
        if replace_item:
            insert_index = cls.stack_index(obj, replace_item)
            if insert_index < 0: return
            cls.stack_remove(obj, replace_item)
        elif where == 'BEFORE':
            insert_index = 0
        
        for item_info in item_infos:
            if not item_info: continue
            item = cls.stack_new(obj, item_info["name"], item_info["type"])
            if not item: continue
            BlRna.deserialize(item, item_info, ignore_default=True, suppress_errors=True)
            if insert_index >= 0:
                cls.stack_move(obj, item, insert_index)
                insert_index += 1
    
    @classmethod
    def stack_new(cls, obj, name, item_type):
        # Note: constraints.new() has a different signature. We have to
        # rely on exceptions since the inspect module doesn't work on it
        stack = cls.get_stack(obj)
        try:
            return stack.new(name, item_type)
        except TypeError:
            item = stack.new(item_type)
            item.name = name
            return item
    
    @classmethod
    def stack_index(cls, obj, item):
        stack = cls.get_stack(obj)
        if isinstance(item, str):
            name = item
            for i, item in enumerate(stack):
                if item.name == name: return i
        else:
            for i, item2 in enumerate(stack):
                if item2 == item: return i
        return -1
    
    @classmethod
    def stack_move(cls, obj, item, to_index):
        stack = cls.get_stack(obj)
        
        if isinstance(item, int):
            from_index = item
            name = stack[from_index].name
        else:
            name = (item if isinstance(item, str) else item.name)
            from_index = cls.stack_index(obj, name)
        
        if hasattr(stack, "move"):
            if from_index >= 0: stack.move(from_index, to_index)
            return
        
        layer_objs = bpy.context.view_layer.objects
        active_obj = layer_objs.active
        layer_objs.active = obj
        
        kwargs = cls.get_op_kwargs(name)
        move_to_index = cls.get_op_func("move_to_index")
        
        if move_to_index:
            kwargs["index"] = to_index
            move_to_index(**kwargs)
        elif to_index < from_index:
            move_up = cls.get_op_func("move_up")
            for _ in range(to_index, from_index):
                move_up(**kwargs)
        elif to_index > from_index:
            move_down = cls.get_op_func("move_down")
            for _ in range(from_index, to_index):
                move_down(**kwargs)
        
        layer_objs.active = active_obj
    
    @classmethod
    def stack_remove(cls, obj, item):
        stack = cls.get_stack(obj)
        stack.remove(item)
    
    @classmethod
    def stack_clear(cls, obj):
        stack = cls.get_stack(obj)
        stack.clear()
    
    @classmethod
    def get_op_idname(cls, op_name):
        op_parts = cls.stack_ops_info.get(op_name, None)
        if not op_parts: return None
        return ".".join(op_parts)
    
    @classmethod
    def get_op_func(cls, op_name):
        op_parts = cls.stack_ops_info.get(op_name, None)
        if not op_parts: return None
        category = getattr(bpy.ops, op_parts[0], None)
        if not category: return None
        return getattr(category, op_parts[1], None)
    
    @classmethod
    def get_op_kwargs(cls, name):
        # Defaults are only necessary for constraints (the "owner" argument)
        # and only for operators other than add (i.e. in the "constraints" category)
        kwargs = dict(cls.stack_ops_defaults)
        kwargs[cls.stack_ops_argname] = name
        return kwargs
    
    @classmethod
    def initialize(cls):
        if not hasattr(cls, "type_rna_prop"):
            cls.type_rna_prop = cls.get_op_func("add").get_rna_type().properties["type"]
        
        cls.enum_items = [(item.identifier, item.name, item.description, item.icon, item.value)
            for item in cls.type_rna_prop.enum_items]
        
        cls.dict_items = {item[0]:item for item in cls.enum_items}
    
    @classmethod
    def draw_prefs(cls, layout, context):
        addon_prefs = addon.preferences
        
        if hasattr(cls, "apply") and (cls.area_space_context == 'MODIFIER'):
            layout.prop_menu_enum(addon_prefs, "apply_options", text="Apply options")
        
        layout.prop_menu_enum(addon_prefs, "modstack_naming", text="Naming options")
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        def make_enable_disable(value):
            op_name = ("Enable" if value else "Disable")
            
            key_descriptions = []
            all_flags = []
            key_flags = {}
            
            for key_modifiers, option_name, option_flags in cls.enable_disable_options:
                key_modifiers = key_modifiers.split("+")
                keys = "+".join([key.capitalize() for key in key_modifiers if key] + ["Click"])
                key_descriptions.append(f"{keys}: {option_name}")
                
                is_alt = "alt" in key_modifiers
                is_ctrl = "ctrl" in key_modifiers
                is_shift = "shift" in key_modifiers
                key_flags[(is_alt, is_ctrl, is_shift)] = option_flags
                
                for flag in option_flags:
                    if flag not in all_flags:
                        all_flags.append(flag)
            
            description = f"{op_name} selected {cls.plural.lower()}"
            if len(key_descriptions) > 1: description += " (" + ", ".join(key_descriptions) + ")"
            
            @simple_operator(f"{cls.prefix}.{op_name.lower()}", f"{op_name} {cls.plural}", description, poll=batch_poll)
            class BatchOp:
                flags: set() | prop(items=[(flag, flag, flag) for flag in all_flags])
                
                def execute(self, context):
                    objs = cls.selected_objects(context)
                    idnames = cls.selected_idnames(context)
                    with UndoBlock(f"{op_name} {cls.plural}"):
                        for obj in objs:
                            for item in cls.get_stack(obj):
                                if cls.idname(item) not in idnames: continue
                                for flag in self.flags:
                                    setattr(item, flag, value)
                    BlUI.tag_redraw()
                    return {'FINISHED'}
                
                def invoke(self, context, event):
                    self.flags = key_flags.get((event.alt, event.ctrl, event.shift), None)
                    if not self.flags: return {'CANCELLED'}
                    return self.execute(context)
        
        make_enable_disable(True)
        make_enable_disable(False)
        
        def make_toggle_enabled():
            description = f"Toggle enabled state for selected {cls.plural.lower()}"
            
            @simple_operator(f"{cls.prefix}.toggle_enabled", f"Toggle {cls.plural} Enabled", description, poll=batch_poll)
            def BatchOp(self, context):
                objs = cls.selected_objects(context)
                idnames = cls.selected_idnames(context)
                value = None
                
                flags = cls.toggle_enabled_flags
                
                for obj in objs:
                    for item in cls.get_stack(obj):
                        if cls.idname(item) not in idnames: continue
                        value = (True if value is None else value) and getattr(item, flags[0])
                
                if value is None: return False
                
                with UndoBlock(f"{'Hide' if value else 'Show'} {cls.plural}"):
                    for obj in objs:
                        for item in cls.get_stack(obj):
                            if cls.idname(item) not in idnames: continue
                            for flag in flags:
                                setattr(item, flag, not value)
                
                BlUI.tag_redraw()
        
        make_toggle_enabled()
        
        def make_apply():
            apply_modes = getattr(cls, "apply_modes", None)
            
            if apply_modes and (len(apply_modes) > 1):
                modes_description = f"Click: {apply_modes[0][1]}, Alt+Click: {apply_modes[1][1]}"
            else:
                modes_description = "Click: on selection"
                apply_modes = [('APPLY', "Apply")]
            
            description = f"Apply selected {cls.plural.lower()} ({modes_description}, Ctrl+Click: on all objects in the active view layer)"
            
            @simple_operator(f"{cls.prefix}.apply", f"Apply {cls.plural}", description, poll=batch_poll)
            class BatchOp:
                mode: apply_modes[0][0] | prop(items=[(key, key, key) for key, name in apply_modes])
                globally: False | prop()
                
                @classmethod
                def poll(op_cls, context):
                    return cls.apply_poll(context)
                
                def execute(self, context):
                    addon_prefs = addon.preferences
                    options = set(addon_prefs.apply_options)
                    if self.globally: options.add('GLOBALLY')
                    
                    objs = (context.view_layer.objects if self.globally else cls.selected_objects(context))
                    objs = filter_objs(objs, context=context, subobjs=True)
                    
                    idnames = cls.selected_idnames(context)
                    
                    with UndoBlock(f"Apply {cls.plural}"):
                        cls.apply(objs, idnames, options=options, mode=self.mode)
                    
                    BlUI.tag_redraw()
                    
                    return {'FINISHED'}
                
                def invoke(self, context, event):
                    self.mode = (apply_modes[-1][0] if event.alt else apply_modes[0][0])
                    self.globally = event.ctrl
                    return self.execute(context)
        
        if hasattr(cls, "apply"):
            make_apply()
        
        main_overrides = set()
        
        @simple_operator(f"{cls.prefix}.add_new", f"Add {cls.plural}", f"Add {cls.plural.lower()} to selected objects", poll=batch_poll)
        class BatchOps_Add_New:
            prepend: False | prop(description=f"Add to the top or to the bottom of the {cls.singular.lower()} stack")
            
            active_obj = None
            objs = None
            obj = None
            use_global_undo = None
            
            def _make_MESH(self):
                data = bpy.data.meshes.new(".tmp-mesh")
                bm = bmesh.new()
                bmesh.ops.create_cube(bm, size=1.0) # just in case
                bm.to_mesh(data)
                bm.free()
                return data
            
            def _make_CURVE(self):
                data = bpy.data.curves.new(".tmp-curve", 'CURVE')
                spline = data.splines.new('BEZIER')
                spline.bezier_points.add(1)
                return data
            
            def _make_SURFACE(self):
                return self._make_CURVE()
            
            def _make_FONT(self):
                return self._make_CURVE()
            
            def _make_LATTICE(self):
                return bpy.data.lattices.new(".tmp-lattice")
            
            def _make_GPENCIL(self):
                return bpy.data.grease_pencils.new(".tmp-grease_pencil")
            
            def _make_ARMATURE(self):
                # Bones can be added/removed only via edit_bones,
                # but accessing them requires to be in EDIT mode.
                # To avoid a whole lot of extra object creation
                # and mode switching, here we utilize one of the
                # existing armatures.
                candidate_bones = None
                candidate_data = None
                for data in bpy.data.armatures:
                    data_bones = len(data.bones)
                    if data_bones == 0: continue
                    if (candidate_bones is None) or (data_bones < candidate_bones):
                        candidate_data = data
                        candidate_bones = data_bones
                if not candidate_data: return None
                data = candidate_data.copy()
                data.name = ".tmp-armature"
                data.bones.active = data.bones[0]
                data.bones[0].select = True
                return data
            
            def _remove_MESH(self, data):
                bpy.data.meshes.remove(data)
            
            def _remove_CURVE(self, data):
                bpy.data.curves.remove(data)
            
            def _remove_LATTICE(self, data):
                bpy.data.lattices.remove(data)
            
            def _remove_GPENCIL(self, data):
                bpy.data.grease_pencils.remove(data)
            
            def _remove_ARMATURE(self, data):
                bpy.data.armatures.remove(data)
            
            def add_tmp_obj(self, context, obj_type):
                data_maker = getattr(self, f"_make_{obj_type}", None)
                data = (data_maker() if data_maker else None)
                
                obj = bpy.data.objects.new(f".tmp-{obj_type}", data)
                # Note: we cannot hide the object, or the *_add()
                # operator will be inactive (greyed-out/unclickable)
                obj.scale = Vector((0, 0, 0))
                context.scene.collection.objects.link(obj)
                BlUtil.Object.active_set(obj, context.view_layer)
                BlUtil.Object.select_set(obj, True, context.view_layer)
                self.obj = obj
                
                self.prev_obj_mode = None
                if obj.type == 'ARMATURE':
                    self.prev_obj_mode = (self.active_obj.mode if self.active_obj else 'OBJECT')
                    bpy.ops.object.mode_set(mode='POSE')
            
            def del_tmp_obj(self):
                if not self.obj: return
                obj_type, data = self.obj.type, self.obj.data
                bpy.data.objects.remove(self.obj)
                data_remover = getattr(self, f"_remove_{obj_type}", None)
                if data_remover: data_remover(data)
                self.obj = None
            
            def execute(self, context):
                if not self.obj: return {'CANCELLED'}
                
                item_infos = [BlRna.serialize(item) for item in cls.get_stack(self.obj)]
                
                # restore the initial state before recording an Undo step
                self.cleanup(context)
                
                where = ('BEFORE' if self.prepend else 'AFTER')
                
                with UndoBlock(f"Add {cls.singular}"):
                    for obj in self.objs:
                        cls.stack_paste(obj, where, *item_infos)
                
                BlUI.tag_redraw()
                
                return {'FINISHED'}
            
            def cancel(self, context):
                self.cleanup(context)
            
            def cleanup(self, context):
                self.del_tmp_obj()
                
                BlUtil.Object.active_set(self.active_obj, context.view_layer)
                
                if self.prev_obj_mode and bpy.ops.object.mode_set.poll():
                    bpy.ops.object.mode_set(mode=self.prev_obj_mode)
                
                edit_preferences = bpy.context.preferences.edit
                edit_preferences.use_global_undo = self.use_global_undo
            
            def invoke(self, context, event):
                self.objs = cls.selected_objects(context)
                self.objs = filter_objs(self.objs, context=context, subobjs=True)
                
                obj_type = cls.get_common_obj_type(self.objs)
                if not obj_type: return {'CANCELLED'}
                
                edit_preferences = bpy.context.preferences.edit
                self.use_global_undo = edit_preferences.use_global_undo
                edit_preferences.use_global_undo = False
                
                self.active_obj = BlUtil.Object.active_get(context.view_layer)
                
                self.add_tmp_obj(context, obj_type)
                
                BlUI.tag_redraw() # make sure Properties editors are updated
                
                addon_prefs = addon.preferences
                wm = context.window_manager
                width = min(addon_prefs.panel_newmod_width, context.window.width)
                
                if addon_prefs.panel_newmod_ok:
                    return wm.invoke_props_dialog(self, width=int(width))
                else:
                    return wm.invoke_popup(self, width=int(width))
            
            def draw(self, context):
                layout = NestedLayout(self.layout)
                
                addon_prefs = addon.preferences
                
                def draw_op(layout, op_name, icon, item):
                    kwargs = cls.get_op_kwargs(item.name)
                    op = layout.operator(cls.get_op_idname(op_name), text="", icon=icon)
                    for key, value in kwargs.items(): setattr(op, key, value)
                
                if not addon_prefs.panel_newmod_ok:
                    layout.label(text=self.bl_label)
                
                with layout.row():
                    layout.prop(self, "prepend", text="", icon=('SORT_DESC' if self.prepend else 'SORT_ASC'))
                    layout.operator_menu_enum(cls.get_op_idname("add"), "type")
                
                # Since Blender 2.90, there are no layout.template_*(...) methods that
                # draw individual stack items. There are methods to draw all at once,
                # but they work *exclusively* in the PROPERTIES area/region's main UI.
                
                option_names = [name for name, predicate in cls.viaibility_draw_options
                    if (not predicate) or predicate(self.obj)]
                
                for item in cls.get_stack(self.obj):
                    with layout.box():
                        with layout.row(align=True):
                            # For show_expanded, Blender automatically shows the state-dependent icon
                            layout.prop(item, "show_expanded", text="", emboss=False)
                            layout.label(icon=cls.dict_items[item.type][3])
                            layout.prop(item, "name", text="")
                            
                            for option_name in option_names:
                                layout.prop(item, option_name, text="")
                            
                            draw_op(layout, "move_up", 'TRIA_UP', item)
                            draw_op(layout, "move_down", 'TRIA_DOWN', item)
                            draw_op(layout, "copy", 'DUPLICATE', item)
                            draw_op(layout, "remove", 'X', item)
                        
                        if not item.show_expanded: continue
                        
                        base_properties = item.bl_rna.base.properties
                        
                        for prop_name, bpy_prop in BlRna.properties(item):
                            if base_properties.find(prop_name) >= 0: continue
                            layout.prop(item, prop_name)
        
        main_overrides.add("add_new")
        
        def extras_view(layout, context):
            layout.operator(f"{cls.prefix}.enable", text="Enable", icon='CHECKBOX_HLT')
            layout.operator(f"{cls.prefix}.disable", text="Disable", icon='CHECKBOX_DEHLT')
        
        def extras_main(layout, context):
            if hasattr(cls, "apply"):
                layout.operator(f"{cls.prefix}.apply", text="Apply", icon='FILE_TICK')
        
        return {"extras_view":extras_view, "extras_main":extras_main, "main_overrides":main_overrides}

# =========================================================================== #

class BatchOps_Modifiers(BatchOps_ModStack):
    icon = 'MODIFIER_DATA'
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Shift+Click: enable/disable, Ctrl+Click: apply"
    contextual_ops[(1, False, False, True)] = ("toggle_enabled", {})
    contextual_ops[(1, False, True, False)] = ("apply", {"mode": 'DATA', "globally": False})
    
    area_space_context = 'MODIFIER'
    
    stack_ops_argname = "modifier"
    stack_ops_defaults = {}
    stack_ops_info = {
        "add": ("object", "modifier_add"),
        "move_up": ("object", "modifier_move_up"),
        "move_down": ("object", "modifier_move_down"),
        "move_to_index": ("object", "modifier_move_to_index"),
        "copy": ("object", "modifier_copy"),
        "remove": ("object", "modifier_remove"),
    }
    
    viaibility_draw_options = [
        ("use_apply_on_spline", (lambda obj: obj.type in ('CURVE', 'SURFACE', 'FONT'))),
        ("show_on_cage", (lambda obj: obj.type == 'MESH')),
        ("show_in_editmode", None),
        ("show_viewport", None),
        ("show_render", None),
    ]
    
    enable_disable_options = [
        ("", "viewport", {"show_viewport"}),
        ("ctrl", "rendering", {"show_render"}),
        ("shift", "edit mode", {"show_in_editmode"}),
        ("alt", "cage/spline", {"show_on_cage", "use_apply_on_spline"}),
    ]
    toggle_enabled_flags = ["show_viewport", "show_render"]
    
    apply_modes = [
        ('DATA', "to data"),
        ('SHAPE', "as shape"),
    ]
    
    @classmethod
    def get_stack(cls, obj):
        return obj.modifiers
    
    @classmethod
    def apply_poll(cls, context):
        # Modifiers cannot be applied in edit/sculpt/paint modes
        mode_info = BlEnums.mode_infos.get(context.mode)
        if not mode_info: return True
        return mode_info.type not in ('EDIT', 'SCULPT', 'PAINT')
    
    @classmethod
    def apply(cls, objs, idnames, options=(), mode='DATA'):
        validate_idname = (lambda item: cls.idname(item) in idnames)
        apply_modifiers(bpy.context, objs, validate_idname, options=options, apply_as=mode)
    
    @classmethod
    def get_common_obj_type(cls, objs):
        # MESH has all modifiers
        # CURVE, SURFACE, FONT have the same set of (fewer) modifiers
        # LATTICE has the fewest modifiers
        obj_types = {obj.type for obj in objs}
        for obj_type in ('MESH', 'SURFACE', 'CURVE', 'FONT', 'LATTICE'):
            if obj_type in obj_types: return obj_type
        return None

make_batch_ops(BatchOps_Modifiers, "Modifier")

# =========================================================================== #

class BatchOps_IDBlock(BatchOps):
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Shift+Click: show/hide"
    contextual_ops[(1, False, False, True)] = ("toggle_show", {})
    
    @classmethod
    def rename(cls, idnames, name):
        bpy_data = cls.get_bpy_data()
        
        if isinstance(name, str):
            idblocks = [(idname, get_idblock(bpy_data, idname), name) for idname in sorted(idnames)]
        else: # collection
            idblocks = [(idname, get_idblock(bpy_data, idname), _name) for idname, _name in zip(idnames, name)]
        
        idblock_map = {}
        
        for idname, idblock, name in idblocks:
            if (not idblock) or idblock.library: continue
            idblock.name = name
            idblock_map[idname] = idblock
        
        return {idname:idblock.name for idname, idblock in idblock_map.items()}
    
    @classmethod
    def remap(cls, idnames, idname):
        bpy_data = cls.get_bpy_data()
        new_id = get_idblock(bpy_data, idname)
        if not new_id: return # user_remap() argument cannot be None
        for idname0 in idnames:
            idblock = get_idblock(bpy_data, idname0)
            if idblock: idblock.user_remap(new_id)
    
    @classmethod
    def delete(cls, idnames):
        bpy_data = cls.get_bpy_data()
        for idname in idnames:
            idblock = get_idblock(bpy_data, idname)
            if idblock: bpy_data.remove(idblock)
    
    @classmethod
    def purge(cls, fake_users=False):
        bpy_data = cls.get_bpy_data()
        for idblock in tuple(bpy_data):
            users = idblock.users - (1 if (idblock.use_fake_user and fake_users) else 0)
            if users == 0: bpy_data.remove(idblock)
    
    @classmethod
    def merge_identical(cls, idnames):
        bpy_data = cls.get_bpy_data()
        merge_identical_idblocks(bpy_data, idnames)

def merge_identical_idblocks(bpy_data, idnames, compare=None, ignore=(), specials={}):
    idblocks = (bpy_data if idnames is None else [bpy_data[idname] for idname in idnames])
    unique = set(idblocks)
    identical = []
    
    if compare is None:
        ignore = set(ignore) | set(bpy.types.ID.bl_rna.properties.keys())
        compare = (lambda itemA, itemB: BlRna.compare(itemA, itemB, ignore=ignore, specials=specials))
    
    for idblock in idblocks:
        duplicates = None
        unique.discard(idblock)
        
        for idblock2 in unique:
            if not compare(idblock, idblock2): continue
            if duplicates is None: duplicates = {idblock}
            duplicates.add(idblock2)
        
        if duplicates is not None:
            identical.append(duplicates)
            unique.difference_update(duplicates)
    
    for duplicates in identical:
        # find best candidate for preservation
        best, best_users, best_len = None, 0, 0
        for idblock in duplicates:
            if idblock.users >= best_users:
                is_better = (idblock.users > best_users)
                is_better |= (best_len <= 0)
                is_better |= (len(idblock.name) < best_len)
                if is_better:
                    best, best_users, best_len = idblock, idblock.users, len(idblock.name)
        
        duplicates.discard(best)
        for idblock in duplicates:
            idblock.user_remap(best)
            bpy_data.remove(idblock)

# =========================================================================== #

class BatchOps_Materials(BatchOps_IDBlock):
    icon = 'MATERIAL'
    
    contextual_ops = dict(BatchOps_IDBlock.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Ctrl+Click: apply"
    contextual_ops[(1, False, True, False)] = ("apply", {})
    contextual_ops[(1, True, True, False)] = ("delete", {"remove_slots": False})
    
    @classmethod
    def set_material_slot(cls, ms, mat, objs):
        if not ms: return False
        obj_data = ms.id_data.data
        max_users = sum(int(obj.data == obj_data) for obj in objs)
        users = obj_data.users - (1 if obj_data.use_fake_user else 0)
        
        # In Blender 2.8 beta, there is no copy-on-write yet.
        # Assigning ms.link seems to work for linked objects,
        # but for ms.material an AttributeError is raised.
        try:
            if (users > max_users): ms.link = 'OBJECT'
            ms.material = mat
        except AttributeError:
            return False
        return True
    
    @classmethod
    def pop_material_slot(cls, obj, index=-1):
        if not hasattr(obj.data, "materials"): return False
        # In Blender 2.8 beta, there is no copy-on-write yet.
        # materials.pop() works, but is not reverted on undo (bug?)
        obj.data.materials.pop(index=index)
        return True
    
    @classmethod
    def add_material_slot(cls, obj, mat=None):
        if not hasattr(obj.data, "materials"): return None
        # In Blender 2.8 beta, there is no copy-on-write yet.
        # materials.append() works, but is not reverted on undo (bug?)
        obj.data.materials.append(mat)
        return obj.material_slots[len(obj.material_slots)-1]
    
    @classmethod
    def get_empty_slot(cls, obj, create=True):
        if not obj: return None
        for ms in obj.material_slots:
            if not ms.material: return ms
        return (cls.add_material_slot(obj) if create else None)
    
    @classmethod
    def iterate_slots(cls, obj, reverse=False):
        for i, ms in cls.enumerate_slots(obj, reverse):
            yield ms
    
    @classmethod
    def enumerate_slots(cls, obj, reverse=False):
        if len(obj.material_slots) == 0:
            virtual_slot_mode = addon.preferences.virtual_slot_mode
            use_virtual_slot = ((virtual_slot_mode == 'ALWAYS') or
                ((virtual_slot_mode == 'CONTEXTUAL') and hasattr(obj.data, "materials")))
            if use_virtual_slot: yield (0, None)
        elif reverse:
            for i in range(len(obj.material_slots)-1, -1, -1):
                yield (i, obj.material_slots[i])
        else:
            yield from enumerate(obj.material_slots)
    
    @classmethod
    def materials(cls, obj, empty=True):
        for ms in cls.iterate_slots(obj):
            if ms and ms.material:
                yield ms.material
            elif empty:
                yield None
    
    @classmethod
    def icon_data(cls, idname):
        if not idname: return cls.icon
        return get_idblock(bpy.data.materials, idname)
    
    @classmethod
    def get_bpy_data(cls):
        return bpy.data.materials
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        def count_empty_slots(objs):
            return sum(int(not mat) for obj in objs for mat in cls.materials(obj))
        
        if objs is None:
            empty_count = count_empty_slots(bpy.data.objects)
            if empty_count > 0: yield ("", "(No material)", empty_count, 0, None)
            
            for i, mat in enumerate(bpy.data.materials):
                yield (mat.name_full, mat.name_full, mat.users, i, None)
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
            
            empty_count = count_empty_slots(objs)
            if empty_count > 0: yield ("", "(No material)", empty_count, 0, None)
            
            for obj in objs:
                for i, mat in enumerate(cls.materials(obj, False)):
                    yield (mat.name_full, mat.name_full, 1, i+1, None)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            for mat in cls.materials(obj):
                mat_name = (mat.name_full if mat else "")
                if mat_name in idnames: return True
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def copy(cls, obj):
        if not obj:
            cls.clipboard = []
        else:
            cls.clipboard = [(mat.name_full if mat else "") for mat in cls.materials(obj)]
    
    @classmethod
    def paste(cls, objs, clipboard=None, overwrite=True, remove_slots=None):
        if remove_slots is None:
            addon_prefs = addon.preferences
            remove_slots = addon_prefs.remove_slots
        
        if clipboard is None: clipboard = cls.clipboard
        if clipboard is None: return
        mats = [get_idblock(bpy.data.materials, idname or "") for idname in clipboard]
        for obj in objs:
            if overwrite:
                for i in range(len(mats), len(obj.material_slots)):
                    if remove_slots:
                        if not cls.pop_material_slot(obj): break
                    else:
                        ms = obj.material_slots[i]
                        if not cls.set_material_slot(ms, None, objs): break
                
                for i in range(len(obj.material_slots), len(mats)):
                    if not cls.add_material_slot(obj): break
                
                if (overwrite == 'WRAP') and (len(mats) > 0):
                    for i in range(len(obj.material_slots)):
                        ms = obj.material_slots[i]
                        if not cls.set_material_slot(ms, mats[i % len(mats)], objs): break
                else:
                    for i in range(min(len(mats), len(obj.material_slots))):
                        ms = obj.material_slots[i]
                        if not cls.set_material_slot(ms, mats[i], objs): break
            else:
                for mat in mats:
                    ms = cls.get_empty_slot(obj)
                    if not cls.set_material_slot(ms, mat, objs): break
    
    @classmethod
    def add_new(cls, objs, name):
        mat = bpy.data.materials.new(name)
        for obj in objs:
            ms = cls.get_empty_slot(obj)
            cls.set_material_slot(ms, mat, objs)
        return mat
    
    @classmethod
    def make_unique(cls, objs, idnames, shared=True, reuse=True):
        addon_prefs = addon.preferences
        old_datablocks = set()
        
        max_users = {}
        for obj in objs:
            for mat in cls.materials(obj, False):
                idname = mat.name_full
                if not reuse:
                    max_users[idname] = -1
                elif not shared:
                    max_users[idname] = 1
                else:
                    max_users[idname] = max_users.get(idname, 0) + 1
        
        shared_mats = {}
        for obj in objs:
            for ms in obj.material_slots:
                mat = ms.material
                if not mat: continue
                
                idname = mat.name_full
                if idname not in idnames: continue
                
                unique_mat = shared_mats.get(idname)
                if not unique_mat:
                    users = mat.users - (1 if mat.use_fake_user else 0)
                    unique_mat = (mat.copy() if (users > max_users[idname]) else mat)
                    old_datablocks.add(mat)
                    if shared: shared_mats[idname] = unique_mat
                
                if not cls.set_material_slot(ms, unique_mat, objs): break
        
        if addon_prefs.make_unique_fake_user:
            for datablock in old_datablocks:
                if datablock.users == 0: datablock.use_fake_user = True
    
    @classmethod
    def assign(cls, objs, idnames, overwrite=True):
        cls.paste(objs, idnames, overwrite=overwrite)
    
    @classmethod
    def replace(cls, objs, idnames, idname, remove_slots=None):
        if remove_slots is None:
            addon_prefs = addon.preferences
            remove_slots = addon_prefs.remove_slots
        
        repl_mat = (get_idblock(bpy.data.materials, idname) if idname else None)
        for obj in objs:
            for i, ms in cls.enumerate_slots(obj, reverse=True):
                mat = (ms.material if ms else None)
                mat_name = (mat.name_full if mat else "")
                if mat_name not in idnames: continue
                if (not repl_mat) and remove_slots:
                    if not cls.pop_material_slot(obj, i): break
                else:
                    if not ms: ms = cls.add_material_slot(obj)
                    if not cls.set_material_slot(ms, repl_mat, objs): break
    
    @classmethod
    def merge_identical(cls, idnames):
        def compare_node_tree(rna_prop, valueA, valueB):
            return NodeTreeComparer.compare(valueA, valueB)
        merge_identical_idblocks(bpy.data.materials, idnames, specials={"node_tree":compare_node_tree})
    
    @classmethod
    def sync_editor(cls, context, area):
        obj = None
        space = area.spaces.active
        if area.type == 'PROPERTIES':
            try:
                space.context = 'MATERIAL' # not always valid (e.g. when acitve object does not support materials)
            except TypeError:
                return False
            obj = context.object
        elif area.type == 'NODE_EDITOR':
            obj = space.id_from # could be Object, World, LineStyle...
            if not isinstance(obj, bpy.types.Object): obj = context.object
        
        selected_idnames = cls.selected_idnames(context)
        if obj and selected_idnames:
            # Currently obj.material_slots.find() does not search by name_full
            for i, ms in enumerate(obj.material_slots):
                mat = ms.material
                if mat and (mat.name_full == selected_idnames[-1]):
                    obj.active_material_index = i
                    break
    
    @classmethod
    def _sync_edit_mesh(cls, context, callback):
        for obj in context.selected_objects:
            if obj.type != 'MESH': continue
            if obj.mode != 'EDIT': continue
            mat_names = {i:(ms.material.name_full if ms and ms.material else "") for i, ms in cls.enumerate_slots(obj)}
            bm = bmesh.from_edit_mesh(obj.data)
            if callback(bm, mat_names):
                bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    
    @classmethod
    def sync_sel_refresh(cls, context, obj_sel):
        if context.mode == 'EDIT_MESH':
            cls.sync_sel_obj(context)
        else:
            super(cls, cls).sync_sel_refresh(context, obj_sel)
    
    @classmethod
    def sync_obj_sel_partial(cls, context, idnames, state):
        if context.mode == 'EDIT_MESH':
            def callback(bm, mat_names):
                ids = {i for i, name in mat_names.items() if name in idnames}
                for face in bm.faces:
                    if face.material_index in ids: face.select = state
                return True
            cls._sync_edit_mesh(context, callback)
        else:
            super(cls, cls).sync_obj_sel_partial(context, idnames, state)
    
    @classmethod
    def sync_obj_sel(cls, context):
        if context.mode == 'EDIT_MESH':
            idnames = set(cls.selection)
            def callback(bm, mat_names):
                ids = {i for i, name in mat_names.items() if name in idnames}
                for face in bm.faces:
                    face.select = face.material_index in ids
                return True
            with UndoBlock("Select"):
                cls._sync_edit_mesh(context, callback)
        else:
            super(cls, cls).sync_obj_sel(context)
    
    @classmethod
    def sync_sel_obj(cls, context):
        if context.mode == 'EDIT_MESH':
            idnames = set()
            def callback(bm, mat_names):
                ids = {i for i, name in mat_names.items() if name in idnames}
                for face in bm.faces:
                    if not face.select: continue
                    idname = mat_names.get(face.material_index)
                    idnames.add(idname)
            cls._sync_edit_mesh(context, callback)
            cls.selection = sorted(idnames)
        else:
            super(cls, cls).sync_sel_obj(context)
    
    @classmethod
    def draw_prefs(cls, layout, context):
        addon_prefs = addon.preferences
        
        layout.prop_menu_enum(addon_prefs, "virtual_slot_mode", text="Virtual slot")
        layout.prop(addon_prefs, "remove_slots")
    
    @classmethod
    def extra_operators(cls):
        def ensure_mat_index(obj, mat, objs):
            for i, ms in enumerate(obj.material_slots):
                if ms.material == mat: return i
            ms = cls.get_empty_slot(obj)
            if not ms: return None
            if not cls.set_material_slot(ms, mat, objs): return None
            for i, ms in enumerate(obj.material_slots):
                if ms.material == mat: return i
            return None
        
        mat_obj_types = {'EDIT_MESH':'MESH', 'EDIT_SURFACE':'SURFACE', 'EDIT_CURVE':'CURVE', 'EDIT_TEXT':'FONT'}
        
        batch_poll = cls.poller()
        
        @simple_operator(f"{cls.prefix}.apply", f"Apply {cls.plural}", f"Apply last selected {cls.singular.lower()} to selected geometry (Edit mode)\n"+
            f"Assign (override) {cls.plural.lower()} in selected objects (non-Edit modes)", poll=batch_poll)
        class BatchOp:
            def execute(self, context):
                selected_idnames = cls.selected_idnames(context)
                if not selected_idnames: return False
                if context.mode not in mat_obj_types:
                    with UndoBlock(f"Assign {cls.plural}"):
                        cls.assign(cls.selected_objects(context), selected_idnames, overwrite='WRAP')
                else:
                    with UndoBlock(f"Apply {cls.singular}"):
                        mat = get_idblock(bpy.data.materials, selected_idnames[-1])
                        if not mat: return False
                        layer_objs = context.view_layer.objects
                        active_obj = layer_objs.active
                        obj_type = mat_obj_types[context.mode]
                        objs = {context.edit_object}.union(context.selected_editable_objects)
                        for obj in objs:
                            if obj.type != obj_type: continue
                            i = ensure_mat_index(obj, mat, objs)
                            if i is None: continue
                            obj.active_material_index = i
                            layer_objs.active = obj
                            bpy.ops.object.material_slot_assign()
                        layer_objs.active = active_obj
                BlUI.tag_redraw()
                return {'FINISHED'}
        
        main_overrides = set()
        
        @simple_operator(f"{cls.prefix}.remove", f"Remove {cls.plural}", f"Remove {cls.plural.lower()} from selected objects (Click: only materials, Shift+Click: remove slots too)", poll=batch_poll)
        class BatchOp:
            flip_remove_slots: False | prop()
            def execute(self, context):
                addon_prefs = addon.preferences
                remove_slots = addon_prefs.remove_slots
                if self.flip_remove_slots: remove_slots = not remove_slots
                with UndoBlock(f"Remove {cls.plural}"):
                    cls.replace(cls.selected_objects(context), cls.selected_idnames(context), "", remove_slots=remove_slots)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.flip_remove_slots = event.shift
                return self.execute(context)
        main_overrides.add("remove")
        
        @simple_operator(f"{cls.prefix}.delete", f"Delete {cls.plural}", f"Delete selected {cls.plural.lower()} (Click: only materials, Shift+Click: remove slots too)", poll=batch_poll)
        class BatchOp:
            remove_slots: False | prop()
            def execute(self, context):
                with UndoBlock(f"Delete {cls.plural}"):
                    selected_idnames = cls.selected_idnames(context)
                    if self.remove_slots: cls.replace(bpy.data.objects, selected_idnames, "", remove_slots=True)
                    cls.delete(selected_idnames)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.remove_slots = event.shift
                return self.execute(context)
        main_overrides.add("delete")
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.apply", text="Apply", icon='FILE_TICK')
        
        return {"extras_main":extras_main, "main_overrides":main_overrides}

make_batch_ops(BatchOps_Materials, "Material")

# =========================================================================== #

def group_pro_collection_filter():
    addon_prefs = addon.preferences
    
    if addon_prefs.group_pro_filter == 'ALL': return None
    
    gp_expect = (addon_prefs.group_pro_filter == 'ONLY')
    
    def gp_filter(collection):
        is_gp = any(v != 0 for v in getattr(collection, "BBoxVertsList", ()))
        is_gp |= getattr(collection, "created_with_gp", False)
        return (is_gp == gp_expect)
    
    return gp_filter

class BatchOps_Collections(BatchOps_IDBlock):
    icon = 'GROUP'
    
    contextual_ops = dict(BatchOps_IDBlock.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Ctrl+Click: assign"
    contextual_ops[(1, False, True, False)] = ("assign", {"overwrite": False})
    
    @classmethod
    def collection_link(cls, collection, obj):
        if not obj_in_collection(obj, collection, False):
            collection.objects.link(obj)
        return True
    
    @classmethod
    def collection_unlink(cls, collection, obj):
        if obj_in_collection(obj, collection, False):
            collection.objects.unlink(obj)
        return True
    
    @classmethod
    def collection_clear(cls, collection):
        for obj in tuple(collection.objects):
            collection.objects.unlink(obj)
    
    @classmethod
    def add_to_scene(cls, collection, scene=None):
        if scene is None: scene = bpy.context.scene
        if collection.name not in scene.collection.children:
            scene.collection.children.link(collection)
    
    @classmethod
    def remove_from_scene(cls, collection, scene=None):
        if scene is None: scene = bpy.context.scene
        if collection.name in scene.collection.children:
            scene.collection.children.unlink(collection)
    
    @classmethod
    def icon_data(cls, idname):
        return 'GROUP'
    
    @classmethod
    def get_bpy_data(cls):
        return bpy.data.collections
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        addon_prefs = addon.preferences
        
        child_collections = set()
        if not addon_prefs.child_collections:
            for collection in bpy.data.collections:
                child_collections.update(collection.children)
        
        gp_filter = group_pro_collection_filter()
        
        if objs is None:
            for i, collection in enumerate(bpy.data.collections):
                if collection in child_collections: continue
                if gp_filter and not gp_filter(collection): continue
                matches = set(collection.all_objects)
                yield (collection.name_full, collection.name_full, len(matches), i, None)
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
            for i, collection in enumerate(bpy.data.collections):
                if collection in child_collections: continue
                if gp_filter and not gp_filter(collection): continue
                matches = objs.intersection(collection.all_objects)
                if matches:
                    yield (collection.name_full, collection.name_full, len(matches), i, None)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        candidates = set()
        for collection in bpy.data.collections:
            if collection.name_full in idnames:
                candidates.update(collection.all_objects)
        
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            return obj in candidates
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def copy(cls, obj):
        cls.clipboard = []
        if not obj: return
        for collection in bpy.data.collections:
            if obj_in_collection(obj, collection, False):
                cls.clipboard.append(collection.name_full)
    
    @classmethod
    def paste(cls, objs, clipboard=None, overwrite=True):
        if clipboard is None: clipboard = cls.clipboard
        if clipboard is None: return
        
        objs = set(objs)
        objs_sel = {obj:BlUtil.Object.select_get(obj) for obj in objs}
        active_obj = BlUtil.Object.active_get()
        
        idnames = set(idname for idname in clipboard if idname)
        for collection in bpy.data.collections:
            if collection.name_full in idnames:
                for obj in objs.difference(collection.objects):
                    cls.collection_link(collection, obj)
            elif overwrite:
                for obj in objs.intersection(collection.objects):
                    cls.collection_unlink(collection, obj)
        
        for obj in objs:
            BlUtil.Object.select_set(obj, objs_sel[obj])
        BlUtil.Object.active_set(active_obj)
    
    @classmethod
    def add_new(cls, objs, name):
        collection = bpy.data.collections.new(name)
        cls.add_to_scene(collection)
        for obj in objs:
            cls.collection_link(collection, obj)
        return collection
    
    @classmethod
    def make_unique(cls, objs, idnames, shared=True, reuse=True):
        addon_prefs = addon.preferences
        old_datablocks = set()
        
        objs = set(objs)
        objs_sel = {obj:BlUtil.Object.select_get(obj) for obj in objs}
        active_obj = BlUtil.Object.active_get()
        
        idnames = set(idnames)
        for collection in bpy.data.collections:
            if collection.name_full not in idnames: continue
            common_objs = objs.intersection(collection.objects)
            if not common_objs: continue
            if shared:
                if (not reuse) or (len(common_objs) < len(collection.objects)):
                    old_datablocks.add(collection)
                    for obj in common_objs:
                        cls.collection_unlink(collection, obj)
                    new_collection = collection.copy()
                    cls.add_to_scene(new_collection)
                    cls.collection_clear(new_collection)
                    for obj in common_objs:
                        cls.collection_link(new_collection, obj)
            else:
                if (not reuse) or (len(collection.objects) > 1):
                    old_datablocks.add(collection)
                    for obj in common_objs:
                        cls.collection_unlink(collection, obj)
                    for obj in common_objs:
                        new_collection = collection.copy()
                        cls.add_to_scene(new_collection)
                        cls.collection_clear(new_collection)
                        cls.collection_link(new_collection, obj)
        
        for obj in objs:
            BlUtil.Object.select_set(obj, objs_sel[obj])
        BlUtil.Object.active_set(active_obj)
        
        if addon_prefs.make_unique_fake_user:
            for datablock in old_datablocks:
                if datablock.users == 0: datablock.use_fake_user = True
    
    @classmethod
    def assign(cls, objs, idnames, overwrite=True):
        cls.paste(objs, idnames, overwrite=overwrite)
    
    @classmethod
    def replace(cls, objs, idnames, idname):
        objs = set(objs)
        objs_sel = {obj:BlUtil.Object.select_get(obj) for obj in objs}
        active_obj = BlUtil.Object.active_get()
        
        new_collection = (get_idblock(bpy.data.collections, idname) if idname else None)
        idnames = set(idnames)
        for collection in bpy.data.collections:
            if collection.name_full not in idnames: continue
            common_objs = objs.intersection(collection.objects)
            for obj in common_objs:
                cls.collection_unlink(collection, obj)
                if new_collection:
                    cls.collection_link(new_collection, obj)
        
        for obj in objs:
            BlUtil.Object.select_set(obj, objs_sel[obj])
        BlUtil.Object.active_set(active_obj)
    
    @classmethod
    def purge(cls, fake_users=False):
        for collection in bpy.data.collections:
            if collection.objects or collection.children: continue
            bpy.data.collections.remove(collection)
    
    @classmethod
    def merge_identical(cls, idnames):
        def compare(collectionA, collectionB):
            if collectionA.instance_offset != collectionB.instance_offset: return False
            if set(collectionA.objects) != set(collectionB.objects): return False
            if set(collectionA.children) != set(collectionB.children): return False
            return True
        merge_identical_idblocks(bpy.data.collections, idnames, compare=compare)
    
    @classmethod
    def reparent(cls, idnames, idname, exclusive=False):
        dst_coll = get_idblock(bpy.data.collections, idname)
        if idname and (not dst_coll): return
        
        idnames = set(idnames) - {idname}
        child_colls = []
        for child_idname in idnames:
            child_coll = get_idblock(bpy.data.collections, child_idname)
            if child_coll: child_colls.append(child_coll)
        if not child_colls: return
        
        def clear(collection, idnames, recursive):
            for child_coll in tuple(collection.children):
                if child_coll.name_full in idnames:
                    collection.children.unlink(child_coll)
                elif recursive:
                    clear(child_coll, idnames, recursive)
        
        if exclusive:
            for collection in bpy.data.collections:
                clear(collection, idnames, False)
        
        if dst_coll:
            for child_coll in child_colls:
                clear(child_coll, [idname], True)
            for child_coll in child_colls:
                if child_coll.name not in dst_coll.children:
                    dst_coll.children.link(child_coll)
    
    @classmethod
    def rename(cls, idnames, name):
        name_map = super(BatchOps_Collections, cls).rename(idnames, name)
        addon_prefs = addon.preferences
        rename_inst = 'COLLECTION_TO_INSTANCES' in addon_prefs.auto_rename_coll
        rename_objs = 'COLLECTION_TO_OBJECTS' in addon_prefs.auto_rename_coll
        rename_data = 'COLLECTION_TO_DATA' in addon_prefs.auto_rename_coll
        rename_mats = 'COLLECTION_TO_MATERIALS' in addon_prefs.auto_rename_coll
        if rename_inst or rename_objs or rename_data or rename_mats:
            filter = {'INST':rename_inst, 'OBJS':rename_objs, 'DATA':rename_data, 'MATS':rename_mats}
            for idname in name_map.values():
                coll = get_idblock(bpy.data.collections, idname)
                if coll and (not coll.library):
                    sync_name(coll, filter)
        return name_map
    
    @classmethod
    def draw_prefs(cls, layout, context):
        prefs = context.preferences
        addon_prefs = addon.preferences
        
        layout.prop_menu_enum(addon_prefs, "auto_rename_coll", text="Auto Rename")
        
        layout.prop(addon_prefs, "child_collections")
        
        if "GroupPro" in prefs.addons:
            gp_mode = addon_prefs.group_pro_filter.capitalize()
            layout.prop_menu_enum(addon_prefs, "group_pro_filter", text=("GroupPro: %s" % gp_mode))
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        def set_collection_flags(idnames, flags, value):
            for idname in idnames:
                collection = get_idblock(bpy.data.collections, idname)
                if not collection: continue
                for flag in flags:
                    setattr(collection, flag, value)
        
        def set_layer_collection_flags(layer_coll, flags, value, idnames):
            coll = layer_coll.collection
            
            if coll.name_full in idnames:
                for flag in flags:
                    setattr(layer_coll, flag, value)
            
            for child in layer_coll.children:
                set_layer_collection_flags(child, flags, value, idnames)
        
        def make_enable_disable(value):
            op_name = ("Disable" if value else "Enable") # True: disable, False: enable in this context
            @simple_operator(f"{cls.prefix}.{op_name.lower()}", f"{op_name} {cls.plural}", f"{op_name} selected {cls.plural.lower()} (Click: exclude, Ctrl+Click: hide-viewport, Shift+Click: holdout, Alt+Click: indirect-only)", poll=batch_poll)
            class BatchOp:
                flags: set() | prop(items=[
                    ("exclude", "exclude", "exclude"),
                    ("hide_viewport", "hide_viewport", "hide_viewport"),
                    ("holdout", "holdout", "holdout"),
                    ("indirect_only", "indirect_only", "indirect_only"),
                ])
                def execute(self, context):
                    idnames = cls.selected_idnames(context)
                    with UndoBlock(f"{op_name} {cls.plural}"):
                        set_layer_collection_flags(context.layer_collection, self.flags, value, idnames)
                    BlUI.tag_redraw()
                    return {'FINISHED'}
                def invoke(self, context, event):
                    if event.ctrl: self.flags = {"hide_viewport"}
                    elif event.shift: self.flags = {"holdout"}
                    elif event.alt: self.flags = {"indirect_only"}
                    else: self.flags = {"exclude"}
                    return self.execute(context)
        
        def make_show_hide(value):
            op_kind = ("Hide" if value else "Show") # True: disable, False: enable in this context
            op_name = f"{op_kind} (Collections)" # True: disable, False: enable in this context
            op_idname = f"{op_kind.lower()}_collection" # show and hide are already in use
            @simple_operator(f"{cls.prefix}.{op_idname}", op_name, f"{op_kind} selected {cls.plural.lower()} (Click: viewport, Ctrl+Click: render)", poll=batch_poll)
            class BatchOp:
                flags: set() | prop(items=[
                    ("hide_viewport", "hide_viewport", "hide_viewport"),
                    ("hide_render", "hide_render", "hide_render"),
                ])
                def execute(self, context):
                    idnames = cls.selected_idnames(context)
                    with UndoBlock(f"{op_name} {cls.plural}"):
                        set_collection_flags(idnames, self.flags, value)
                    BlUI.tag_redraw()
                    return {'FINISHED'}
                def invoke(self, context, event):
                    if event.ctrl: self.flags = {"hide_render"}
                    else: self.flags = {"hide_viewport"}
                    return self.execute(context)
        
        def make_enable_disable_selection(value):
            op_kind = ("Disable" if value else "Enable")
            op_name = f"{op_kind} Selection (Collections)" # True: disable, False: enable in this context
            op_idname = f"{op_kind.lower()}_selection_collection" # enable_selection and disable_selection are already in use
            @simple_operator(f"{cls.prefix}.{op_idname}", op_name, f"{op_kind} selection for selected {cls.plural.lower()}", poll=batch_poll)
            class BatchOp:
                def execute(self, context):
                    idnames = cls.selected_idnames(context)
                    with UndoBlock(f"{op_name} {cls.plural}"):
                        set_collection_flags(idnames, ["hide_select"], value)
                    BlUI.tag_redraw()
                    return {'FINISHED'}
                def invoke(self, context, event):
                    return self.execute(context)
        
        make_enable_disable(True)
        make_enable_disable(False)
        
        make_show_hide(True)
        make_show_hide(False)
        
        make_enable_disable_selection(True)
        make_enable_disable_selection(False)
        
        @simple_operator(f"{cls.prefix}.instance", f"Instance {cls.plural}", f"Add {cls.plural.lower()} instances to the current scene", poll=batch_poll)
        def BatchOp(self, context):
            with UndoBlock(f"Instance {cls.plural}"):
                if bpy.ops.object.mode_set.poll():
                    bpy.ops.object.mode_set(mode='OBJECT')
                for idname in cls.selected_idnames(context):
                    bpy.ops.object.collection_instance_add(collection=idname)
            BlUI.tag_redraw()
        
        @simple_operator(f"{cls.prefix}.link", f"Link {cls.plural}", f"Link {cls.plural.lower()} to the current scene", poll=batch_poll)
        def BatchOp(self, context):
            with UndoBlock(f"Link {cls.plural}"):
                for idname in cls.selected_idnames(context):
                    collection = get_idblock(bpy.data.collections, idname)
                    if collection: cls.add_to_scene(collection)
            BlUI.tag_redraw()
        
        @simple_operator(f"{cls.prefix}.unlink", f"Unlink {cls.plural}", f"Unlink {cls.plural.lower()} from the current scene", poll=batch_poll)
        def BatchOp(self, context):
            with UndoBlock(f"Unlink {cls.plural}"):
                for idname in cls.selected_idnames(context):
                    collection = get_idblock(bpy.data.collections, idname)
                    if collection: cls.remove_from_scene(collection)
            BlUI.tag_redraw()
        
        @simple_operator(f"{cls.prefix}.reparent", f"Reparent {cls.plural}", f"Reparent {cls.plural.lower()} (Click: non-exclusive, Ctrl+Click: exclusive, Alt+Click: use last selected)", poll=batch_poll)
        class BatchOp:
            idname: "" | prop()
            exclusive: False | prop()
            def execute(self, context):
                selected_idnames = cls.selected_idnames(context)
                if len(selected_idnames) == 0: return {'CANCELLED'}
                with UndoBlock(f"Reparent {cls.plural}"):
                    idname = self.idname
                    idnames = set(selected_idnames) - {idname}
                    cls.reparent(idnames, idname, exclusive=self.exclusive)
                    self.idname = "" # a hack to force Blender to clear up the operator's property value
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                if self.idname:
                    return self.execute(context)
                elif event.alt:
                    if len(cls.selection) <= 1: return {'CANCELLED'}
                    self.idname = cls.selection[-1]
                    self.exclusive = event.ctrl
                    return self.execute(context)
                else:
                    selected_idnames = cls.selected_idnames(context)
                    if len(selected_idnames) == 0: return {'CANCELLED'}
                    exclusive = event.ctrl
                    def popup_draw(self, context):
                        layout = self.layout
                        layout.label(text=f"Reparent {cls.plural.lower()} to:", icon='FILE_PARENT')
                        col = layout.column(align=True)
                        op = col.operator(f"{cls.prefix}.reparent", text="(nothing)", icon='X')
                        op.idname = ""
                        op.exclusive = True
                        for idname, name in zip(cls.idnames, cls.names):
                            icon_data = cls.icon_data(idname)
                            if icon_data is not None:
                                icon, icon_value = ((icon_data, 0) if isinstance(icon_data, str) else ('NONE', layout.icon(icon_data)))
                            else:
                                icon, icon_value = 'NONE', 0
                            op = col.operator(f"{cls.prefix}.reparent", text=name, icon=icon, icon_value=icon_value)
                            op.idname = idname
                            op.exclusive = exclusive
                    context.window_manager.popover(popup_draw)
                    return {'FINISHED'}
        
        main_overrides = set()
        
        @simple_operator(f"{cls.prefix}.add_new", f"New {cls.plural}", f"Add a new {cls.plural.lower()}", poll=batch_poll)
        class BatchOp:
            idname: "" | prop()
            add_objs: True | prop(description="Add selected objects")
            add_colls: False | prop(description="Add selected collections")
            exclusive: False | prop(description="Reparent selected collections (exclusive)")
            def execute(self, context):
                with UndoBlock(f"Add {cls.singular}"):
                    objs = (cls.selected_objects(context) if self.add_objs else ())
                    new_coll = cls.add_new(objs, self.idname)
                    if self.add_colls:
                        cls.reparent(cls.selected_idnames(context), new_coll.name_full, exclusive=self.exclusive)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                return context.window_manager.invoke_props_dialog(self)
            def draw(self, context):
                layout = self.layout
                layout.prop(self, "idname", text="")
                row = layout.row()
                row1 = row.row(align=True)
                row1.prop(self, "add_objs", text="Objects", icon='OBJECT_DATAMODE')
                row2 = row.row(align=True)
                row2.prop(self, "add_colls", text="Collections", icon='GROUP')
                row3 = row2.row(align=True)
                row3.active = self.add_colls
                row3.prop(self, "exclusive", text="", icon='FILE_PARENT')
        
        main_overrides.add("add_new")
        
        def extras_select(layout, context):
            layout.operator(f"{cls.prefix}.enable_selection_collection", text="Enable Selection (Collections)", icon='RESTRICT_SELECT_OFF')
            layout.operator(f"{cls.prefix}.disable_selection_collection", text="Disable Selection (Collections)", icon='RESTRICT_SELECT_ON')
            layout.operator("batch_ops.enable_selection_globally", text="Enable Selection Globally", icon='RESTRICT_SELECT_OFF')
        
        def extras_view(layout, context):
            layout.operator(f"{cls.prefix}.show_collection", text="Show (Collections)", icon='RESTRICT_VIEW_OFF')
            layout.operator(f"{cls.prefix}.hide_collection", text="Hide (Collections)", icon='RESTRICT_VIEW_ON')
            layout.operator(f"{cls.prefix}.enable", text="Enable", icon='CHECKBOX_HLT')
            layout.operator(f"{cls.prefix}.disable", text="Disable", icon='CHECKBOX_DEHLT')
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.instance", text="Instance", icon='OUTLINER_OB_GROUP_INSTANCE')
            layout.operator(f"{cls.prefix}.link", text="Link", icon='LINKED')
            layout.operator(f"{cls.prefix}.unlink", text="Unlink", icon='UNLINKED')
            layout.operator(f"{cls.prefix}.reparent", text="Reparent", icon='FILE_PARENT')
        
        return {"extras_select":extras_select, "extras_view":extras_view, "extras_main":extras_main, "main_overrides":main_overrides}

make_batch_ops(BatchOps_Collections, "Collection")

# =========================================================================== #

class BatchOps_Textures(BatchOps_IDBlock):
    icon = 'TEXTURE'
    
    contextual_ops = dict(BatchOps_IDBlock.contextual_ops) # (clicks, alt, ctrl, shift)
    
    @classmethod
    def textures_meta(cls, obj):
        bpy_Texture = bpy.types.Texture
        
        for md in obj.modifiers:
            tex = getattr(md, "texture", None)
            if isinstance(tex, bpy_Texture): yield md, "texture", tex
            tex = getattr(md, "mask_texture", None)
            if isinstance(tex, bpy_Texture): yield md, "mask_texture", tex
            if hasattr(md, "flow_settings"):
                flow_settings = md.flow_settings
                tex = getattr(flow_settings, "noise_texture", None)
                if isinstance(tex, bpy_Texture): yield flow_settings, "noise_texture", tex
            elif hasattr(md, "canvas_settings"):
                canvas_surfaces = getattr(md.canvas_settings, "canvas_surfaces", None)
                tex = getattr(canvas_surfaces, "init_texture", None)
                if isinstance(tex, bpy_Texture): yield canvas_surfaces, "init_texture", tex
        
        if obj.field:
            field = obj.field
            tex = getattr(field, "texture", None)
            if isinstance(tex, bpy_Texture): yield field, "texture", tex
        
        for particle_system in obj.particle_systems:
            particle_settings = particle_system.settings
            if not particle_settings: continue # just in case
            tex = getattr(particle_settings, "active_texture", None)
            if isinstance(tex, bpy_Texture): yield particle_settings, "active_texture", tex
            if particle_settings.force_field_1:
                field = particle_settings.force_field_1
                tex = getattr(field, "texture", None)
                if isinstance(tex, bpy_Texture): yield field, "texture", tex
            if particle_settings.force_field_2:
                field = particle_settings.force_field_2
                tex = getattr(field, "texture", None)
                if isinstance(tex, bpy_Texture): yield field, "texture", tex
        
        for ms in obj.material_slots:
            mat = ms.material
            if not mat: continue
            if not mat.node_tree: continue
            for node in mat.node_tree.nodes:
                tex = getattr(ms, "texture", None)
                if isinstance(tex, bpy_Texture): yield ms, "texture", tex
    
    @classmethod
    def textures(cls, obj):
        for source, attr_name, tex in cls.textures_meta(obj):
            yield tex
    
    @classmethod
    def set_texture(cls, source, attr_id, tex):
        try:
            if isinstance(attr_id, str):
                setattr(source, attr_id, tex)
            else:
                source[attr_id] = tex
        except Exception:
            pass
    
    @classmethod
    def icon_data(cls, idname):
        if not idname: return cls.icon
        return get_idblock(bpy.data.textures, idname)
    
    @classmethod
    def get_bpy_data(cls):
        return bpy.data.textures
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        if objs is None:
            for i, tex in enumerate(bpy.data.textures):
                yield (tex.name_full, tex.name_full, tex.users, i, None)
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
            for obj in objs:
                for i, tex in enumerate(cls.textures(obj)):
                    yield (tex.name_full, tex.name_full, 1, i+1, None)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            for tex in cls.textures(obj):
                if tex.name_full in idnames: return True
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def replace(cls, objs, idnames, idname):
        repl_tex = (get_idblock(bpy.data.textures, idname) if idname else None)
        if (objs is None) and repl_tex:
            for tex in bpy.data.textures:
                if tex.name_full == idname: continue
                if tex.name_full not in idnames: continue
                tex.user_remap(repl_tex) # user_remap does not support None argument
        else:
            if objs is None: objs = bpy.data.objects
            for obj in objs:
                for source, attr_id, tex in tuple(cls.textures_meta(obj)):
                    cls.set_texture(source, attr_id, repl_tex)
    
    @classmethod
    def merge_identical(cls, idnames):
        def compare_node_tree(rna_prop, valueA, valueB):
            return NodeTreeComparer.compare(valueA, valueB)
        merge_identical_idblocks(bpy.data.textures, idnames, specials={"node_tree":compare_node_tree})
    
    @classmethod
    def make_unique(cls, objs, idnames, shared=True, reuse=True):
        addon_prefs = addon.preferences
        old_datablocks = set()
        
        max_users = {}
        for obj in objs:
            for tex in cls.textures(obj):
                idname = tex.name_full
                if not reuse:
                    max_users[idname] = -1
                elif not shared:
                    max_users[idname] = 1
                else:
                    max_users[idname] = max_users.get(idname, 0) + 1
        
        shared_texs = {}
        for obj in objs:
            for source, attr_id, tex in tuple(cls.textures_meta(obj)):
                idname = tex.name_full
                if idname not in idnames: continue
                
                unique_tex = shared_texs.get(idname)
                if not unique_tex:
                    users = tex.users - (1 if tex.use_fake_user else 0)
                    unique_tex = (tex.copy() if (users > max_users[idname]) else tex)
                    old_datablocks.add(tex)
                    if shared: shared_texs[idname] = unique_tex
                
                cls.set_texture(source, attr_id, unique_tex)
        
        if addon_prefs.make_unique_fake_user:
            for datablock in old_datablocks:
                if datablock.users == 0: datablock.use_fake_user = True
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        main_overrides = set()
        
        enum_items = [(item.identifier, item.name, item.description, item.icon, item.value)
            for item in bpy.types.Texture.bl_rna.properties["type"].enum_items]
        dict_items = {item[0]:item for item in enum_items}
        
        @simple_operator(f"{cls.prefix}.add_new", f"New {cls.singular}", f"Add a new {cls.singular.lower()}", poll=batch_poll)
        class BatchOp:
            idname: "" | prop()
            type: '' | prop(items=enum_items) # empty string -> first item
            def execute(self, context):
                with UndoBlock(f"Add {cls.singular}"):
                    bpy.data.textures.new(self.idname, type=self.type)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                return context.window_manager.invoke_props_dialog(self)
            def draw(self, context):
                layout = self.layout
                layout.prop(self, "idname", text="")
                layout.prop(self, "type", text="")
        
        main_overrides.add("add_new")
        
        return {"main_overrides":main_overrides}

make_batch_ops(BatchOps_Textures, "Texture")

# =========================================================================== #

class BatchOps_Images(BatchOps_IDBlock):
    icon = 'IMAGE_DATA'
    
    contextual_ops = dict(BatchOps_IDBlock.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Ctrl+Click: (un)pack, Double-Click: open file"
    contextual_ops[(1, False, True, False)] = ("toggle_pack", dict(show_menu=True))
    contextual_ops[(2, False, False, False)] = ("open_file", {})
    
    @classmethod
    def images_meta(cls, obj):
        bpy_Texture = bpy.types.Texture
        bpy_Image = bpy.types.Image
        
        if obj.type == 'CAMERA':
            for bkg_image in obj.data.background_images:
                img = getattr(bkg_image, "image", None)
                if isinstance(img, bpy_Image): yield bkg_image, "image", img
        
        for ms in obj.material_slots:
            mat = ms.material
            if not mat: continue
            
            for i, img in enumerate(mat.texture_paint_images):
                if not img: continue
                yield mat.texture_paint_images, i, img
            
            grease_pencil = mat.grease_pencil
            if grease_pencil:
                img = getattr(grease_pencil, "fill_image", None)
                if isinstance(img, bpy_Image): yield grease_pencil, "fill_image", img
                img = getattr(grease_pencil, "stroke_image", None)
                if isinstance(img, bpy_Image): yield grease_pencil, "stroke_image", img
            
            if mat.node_tree:
                for node in mat.node_tree.nodes:
                    tex = getattr(ms, "texture", None)
                    if isinstance(tex, bpy_Texture):
                        img = getattr(tex, "image", None)
                        if isinstance(img, bpy_Image): yield tex, "image", img
                    img = getattr(ms, "image", None)
                    if isinstance(img, bpy_Image): yield ms, "image", img
    
    @classmethod
    def images(cls, obj):
        for source, attr_name, img in cls.images_meta(obj):
            yield img
    
    @classmethod
    def set_image(cls, source, attr_id, img):
        try:
            if isinstance(attr_id, str):
                setattr(source, attr_id, img)
            else:
                source[attr_id] = img
        except Exception:
            pass
    
    @classmethod
    def get_icon_state(cls, img):
        if not img: return False
        if img.type != 'IMAGE': return False
        if img.source not in ('FILE', 'SEQUENCE', 'MOVIE'): return False
        if img.packed_files: return False
        if not img.filepath: return False
        return True
        #return os.path.isfile(img.filepath) # slows down significantly
    
    @classmethod
    def icon_data(cls, idname):
        if not idname: return cls.icon
        return get_idblock(bpy.data.images, idname)
    
    @classmethod
    def get_bpy_data(cls):
        return bpy.data.images
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        if objs is None:
            for i, img in enumerate(bpy.data.images):
                state = cls.get_icon_state(img)
                yield (img.name_full, img.name_full, img.users, i, state)
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
            for obj in objs:
                for i, img in enumerate(cls.images(obj)):
                    state = cls.get_icon_state(img)
                    yield (img.name_full, img.name_full, 1, i+1, state)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            for img in cls.images(obj):
                if img.name_full in idnames: return True
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def replace(cls, objs, idnames, idname):
        repl_img = (get_idblock(bpy.data.images, idname) if idname else None)
        if (objs is None) and repl_img:
            for img in bpy.data.images:
                if img.name_full == idname: continue
                if img.name_full not in idnames: continue
                img.user_remap(repl_img) # user_remap does not support None argument
        else:
            if objs is None: objs = bpy.data.objects
            for obj in objs:
                for source, attr_id, img in tuple(cls.images_meta(obj)):
                    cls.set_image(source, attr_id, repl_img)
    
    @classmethod
    def merge_identical(cls, idnames):
        merge_identical_idblocks(bpy.data.images, idnames, ignore={"bindcode"})
    
    @classmethod
    def make_unique(cls, objs, idnames, shared=True, reuse=True):
        addon_prefs = addon.preferences
        old_datablocks = set()
        
        max_users = {}
        for obj in objs:
            for img in cls.images(obj):
                idname = img.name_full
                if not reuse:
                    max_users[idname] = -1
                elif not shared:
                    max_users[idname] = 1
                else:
                    max_users[idname] = max_users.get(idname, 0) + 1
        
        shared_imgs = {}
        for obj in objs:
            for source, attr_id, img in tuple(cls.images_meta(obj)):
                idname = img.name_full
                if idname not in idnames: continue
                
                unique_img = shared_imgs.get(idname)
                if not unique_img:
                    users = img.users - (1 if img.use_fake_user else 0)
                    unique_img = (img.copy() if (users > max_users[idname]) else img)
                    old_datablocks.add(img)
                    if shared: shared_imgs[idname] = unique_img
                
                cls.set_image(source, attr_id, unique_img)
        
        if addon_prefs.make_unique_fake_user:
            for datablock in old_datablocks:
                if datablock.users == 0: datablock.use_fake_user = True
    
    @classmethod
    def sync_editor(cls, context, area):
        space = area.spaces.active
        if area.type == 'IMAGE_EDITOR':
            selected_idnames = cls.selected_idnames(context)
            if not selected_idnames: return
            # Currently Blender does not search by name_full
            for img in bpy.data.images:
                if img and (img.name_full == selected_idnames[-1]):
                    space.image = img
                    break
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        main_overrides = set()
        
        def is_image_packable(img):
            if not img: return False
            if img.type != 'IMAGE': return False
            if img.source not in ('FILE', 'SEQUENCE', 'MOVIE'): return False
            return True
        
        @simple_operator(f"{cls.prefix}.open_file", f"Open {cls.singular}", f"Open {cls.singular.lower()} file with the associated program", poll=batch_poll)
        class BatchOp:
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                if not idnames: return {'CANCELLED'}
                
                img = get_idblock(bpy.data.images, idnames[-1])
                if not img: return {'CANCELLED'}
                
                filepath = os.path.normpath(BpyPath.abspath(img.filepath))
                if not os.path.isfile(filepath):
                    #self.report({'WARNING'}, f"Image {img.name} is not a file!\n{filepath}")
                    return {'CANCELLED'}
                
                result = {'CANCELLED'}
                userprefs = bpy.context.preferences
                if userprefs.filepaths.image_editor:
                    try:
                        result = bpy.ops.image.external_edit(filepath=filepath)
                    except Exception:
                        pass
                
                if result == {'CANCELLED'}:
                    # https://stackoverflow.com/questions/434597/open-document-with-default-os-application-in-python-both-in-windows-and-mac-os
                    if platform.system() == 'Darwin': # macOS
                        subprocess.call(('open', filepath))
                    elif platform.system() == 'Windows': # Windows
                        os.startfile(filepath)
                    else: # linux variants
                        subprocess.call(('xdg-open', filepath))
                
                return {'FINISHED'}
        
        @simple_operator(f"{cls.prefix}.edit_properties", f"Edit {cls.singular} properties", f"Edit {cls.singular} properties", poll=batch_poll)
        class BatchOp:
            do_alpha_mode: False | prop("Apply")
            alpha_mode: BlRna.to_bpy_prop(bpy.types.Image, "alpha_mode")
            
            do_use_view_as_render: False | prop("Apply")
            use_view_as_render: BlRna.to_bpy_prop(bpy.types.Image, "use_view_as_render")
            
            do_colorspace_name: False | prop("Apply")
            colorspace_name: BlRna.to_bpy_prop(bpy.types.ColorManagedInputColorspaceSettings, "name")
            
            def initialize(self, context):
                idnames = cls.selected_idnames(context)
                if not idnames: return
                
                img = get_idblock(bpy.data.images, idnames[0])
                if not img: return
                
                self.alpha_mode = img.alpha_mode
                
                self.use_view_as_render = img.use_view_as_render
                
                colorspace = img.colorspace_settings
                try:
                    self.colorspace_name = colorspace.name
                except TypeError:
                    # Happens at least for the "Render Result" image
                    # (it has colorspace.name == "")
                    self.colorspace_name = "sRGB"
            
            def process(self, img):
                if self.do_alpha_mode:
                    img.alpha_mode = self.alpha_mode
                
                if self.do_use_view_as_render:
                    img.use_view_as_render = self.use_view_as_render
                
                if self.do_colorspace_name:
                    colorspace = img.colorspace_settings
                    colorspace.is_data = (self.colorspace_name == "Non-Color")
                    colorspace.name = self.colorspace_name
            
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                if not idnames: return {'CANCELLED'}
                
                for idname in idnames:
                    img = get_idblock(bpy.data.images, idname)
                    if img: self.process(img)
                
                BlUI.tag_redraw()
                
                return {'FINISHED'}
            
            def invoke(self, context, event):
                self.initialize(context)
                return context.window_manager.invoke_props_dialog(self)
            
            def draw(self, context):
                layout = self.layout
                self.draw_row(layout, "colorspace_name", "Color Space")
                self.draw_row(layout, "alpha_mode", "Alpha")
                self.draw_row(layout, "use_view_as_render", "View as Render")
            
            def draw_row(self, layout, name, label):
                do_name = "do_"+name
                row = layout.row()
                row.prop(self, do_name, text="")
                subrow = row.row()
                subrow.active = getattr(self, do_name)
                subrow.label(text=label)
                subrow.prop(self, name, text="")
        
        @simple_operator(f"{cls.prefix}.copy_paths", f"Copy {cls.singular} Path(s)", f"Copy {cls.singular} path(s) to system clipboard", poll=batch_poll)
        class BatchOp:
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                if not idnames: return {'CANCELLED'}
                
                paths = []
                for idname in idnames:
                    img = get_idblock(bpy.data.images, idname)
                    if not img: continue
                    if not img.filepath: continue
                    path = os.path.normpath(BpyPath.abspath(img.filepath))
                    paths.append(path)
                
                wm = context.window_manager
                wm.clipboard = os.linesep.join(paths)
                
                return {'FINISHED'}
        
        @simple_operator(f"{cls.prefix}.toggle_pack", f"(Un)pack {cls.singular}", f"(Un)pack {cls.singular}", poll=batch_poll)
        class BatchOp:
            show_menu: False | prop(options={'HIDDEN', 'SKIP_SAVE'})
            mode: 'PACK' | prop(items=[
                ('PACK', "Pack", ""),
                ('REMOVE', "Unpack (remove pack)", ""),
                ('USE_LOCAL', "Unpack (use local)", ""),
                ('WRITE_LOCAL', "Unpack (write local)", ""),
                ('USE_ORIGINAL', "Unpack (use original)", ""),
                ('WRITE_ORIGINAL', "Unpack (write original)", ""),
            ])
            
            def execute(self, context):
                if self.show_menu:
                    def draw(self, context):
                        self.layout.operator_enum(f"{cls.prefix}.toggle_pack", "mode")
                    context.window_manager.popup_menu(draw, title="(Un)pack", icon='PACKAGE')
                    return {'CANCELLED'}
                
                idnames = cls.selected_idnames(context)
                if not idnames: return {'CANCELLED'}
                
                for idname in idnames:
                    img = get_idblock(bpy.data.images, idname)
                    if not is_image_packable(img): continue
                    
                    try:
                        if self.mode == 'PACK':
                            img.pack()
                        else:
                            img.unpack(method=self.mode)
                    except Exception:
                        pass
                
                cls.refresh(context)
                BlUI.tag_redraw()
                
                return {'FINISHED'}
        
        @simple_operator(f"{cls.prefix}.reload", f"Reload {cls.singular}", f"Reload {cls.singular}", poll=batch_poll)
        class BatchOp:
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                if not idnames: return {'CANCELLED'}
                
                for idname in idnames:
                    img = get_idblock(bpy.data.images, idname)
                    if not is_image_packable(img): continue
                    path = os.path.normpath(BpyPath.abspath(img.filepath))
                    if not os.path.isfile(path): continue
                    
                    try:
                        img.reload()
                    except Exception:
                        pass
                
                cls.refresh(context)
                BlUI.tag_redraw()
                
                return {'FINISHED'}
        
        @simple_operator(f"{cls.prefix}.add_new", f"New Image(s)", f"Click: new image; Shift+Click: load image(s)", poll=batch_poll)
        class BatchOp:
            files: [bpy.types.OperatorFileListElement] | prop("File Path", "File path used for importing")
            directory: "" | prop()
            filter_image: True | prop(options={'HIDDEN', 'SKIP_SAVE'})
            filter_movie: True | prop(options={'HIDDEN', 'SKIP_SAVE'})
            filter_folder: True | prop(options={'HIDDEN', 'SKIP_SAVE'})
            
            is_file_browser: False | prop(options={'HIDDEN', 'SKIP_SAVE'})
            
            alpha_mode_rna = bpy.types.Image.bl_rna.properties["alpha_mode"]
            alpha_mode: alpha_mode_rna.default | prop(alpha_mode_rna.name, alpha_mode_rna.description,
                items=[(item.identifier, item.name, item.description) for item in alpha_mode_rna.enum_items])
            relative: True | prop("Relative Paths", "Use relative file paths")
            check_existing: False | prop("Use Existing", "Use existing data-block if this file is already loaded")
            
            idname: "" | prop(description="File path or image name")
            width: 1024 | prop("Width", "Image width", min=1)
            height: 1024 | prop("Height", "Image height", min=1)
            alpha: False | prop("Alpha", "Use alpha channel")
            float_buffer: False | prop("Float", "Create an image with floating point color")
            stereo3d: False | prop("Stereo", "Create left and right views")
            is_data: False | prop("Data", "Create image with non-color data color space")
            
            # Adapted from "Import Images As Planes" addon
            def postprocess(self, image):
                image.alpha_mode = self.alpha_mode
                
                if self.relative:
                    try:
                        image.filepath = BpyPath.relpath(image.filepath)
                    except ValueError:
                        pass
            
            def execute(self, context):
                if self.is_file_browser:
                    paths = [os.path.join(self.directory, item.name) for item in self.files]
                    with UndoBlock(f"Load {cls.plural}"):
                        for path in paths:
                            image = bpy.data.images.load(path, check_existing=self.check_existing)
                            self.postprocess(image)
                elif os.path.isfile(self.idname):
                    with UndoBlock(f"Load {cls.singular}"):
                        image = bpy.data.images.load(self.idname, check_existing=self.check_existing)
                        self.postprocess(image)
                else:
                    with UndoBlock(f"Add {cls.singular}"):
                        bpy.data.images.new(self.idname, self.width, self.height, alpha=self.alpha,
                            float_buffer=self.float_buffer, stereo3d=self.stereo3d, is_data=self.is_data)
                BlUI.tag_redraw()
                self.is_file_browser = False # reset, just in case
                return {'FINISHED'}
            
            def invoke(self, context, event):
                self.is_file_browser = event.shift
                if self.is_file_browser:
                    context.window_manager.fileselect_add(self)
                    return {'RUNNING_MODAL'}
                return context.window_manager.invoke_props_dialog(self)
            
            def draw(self, context):
                layout = self.layout
                
                if self.is_file_browser:
                    layout.prop(self, "relative")
                    layout.prop(self, "check_existing")
                    layout.prop(self, "alpha_mode")
                else:
                    layout.prop(self, "idname", text="")
                    if os.path.isfile(self.idname):
                        row = layout.row()
                        row.prop(self, "relative")
                        row.prop(self, "check_existing")
                        layout.prop(self, "alpha_mode")
                    else:
                        row = layout.row(align=True)
                        row.prop(self, "width")
                        row.prop(self, "height")
                        row = layout.row(align=True)
                        row.prop(self, "alpha", toggle=True)
                        row.prop(self, "float_buffer", toggle=True)
                        row.prop(self, "stereo3d", toggle=True)
                        row.prop(self, "is_data", toggle=True)
        
        main_overrides.add("add_new")
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.edit_properties", text="Edit Properties", icon='COPYDOWN')
            layout.operator(f"{cls.prefix}.copy_paths", text="Copy Path(s)", icon='PROPERTIES')
            layout.operator(f"{cls.prefix}.toggle_pack", text="(Un)pack", icon='PACKAGE').show_menu = True
            layout.operator(f"{cls.prefix}.reload", text="Reload", icon='FILE_REFRESH')
        
        return {"extras_main":extras_main, "main_overrides":main_overrides}

make_batch_ops(BatchOps_Images, "Image")

# =========================================================================== #

class BatchOps_ViewLayers(BatchOps):
    icon = 'SEQ_PREVIEW'
    icon_active = 'FILE_IMAGE'
    # RENDERLAYERS OUTPUT IMAGE_DATA OUTLINER_OB_IMAGE FILE_IMAGE IMAGE_RGB IMAGE_RGB_ALPHA SEQ_PREVIEW
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Shift+Click: enable/disable, Ctrl+Click: set active"
    contextual_ops[(1, False, False, True)] = ("toggle_enabled", {})
    contextual_ops[(1, False, True, False)] = ("set_active", {})
    
    separator = " ‣ "
    
    @classmethod
    def _remove_scene(cls, name):
        sep = cls.separator
        i = name.find(sep)
        if i < 0:
            sep = sep.strip()
            i = name.find(sep)
        return (name if i < 0 else name[i+len(sep):])
    
    @classmethod
    def base_name(cls, id, default=None):
        if isinstance(id, int):
            id = cls.idnames[id]
        elif id not in cls.idnames:
            return default
        return cls._remove_scene(id)
    
    @classmethod
    def idname(cls, scene, view_layer):
        return f"{scene.name_full}{cls.separator}{view_layer.name}"
    
    @classmethod
    def iter_scene(cls, scene):
        for view_layer in scene.view_layers:
            idname = cls.idname(scene, view_layer)
            yield scene, view_layer, idname
    
    @classmethod
    def iter_all(cls):
        for scene in bpy.data.scenes:
            yield from cls.iter_scene(scene)
    
    @classmethod
    def icon_data(cls, idname):
        context = bpy.context
        if cls.idname(context.scene, context.view_layer) == idname: return cls.icon_active
        return cls.icon
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        if objs is None:
            for i, (scene, view_layer, idname) in enumerate(cls.iter_all()):
                matches = set(view_layer.objects)
                yield (idname, idname, len(matches), i, None)
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
            for i, (scene, view_layer, idname) in enumerate(cls.iter_all()):
                matches = objs.intersection(view_layer.objects)
                if matches: yield (idname, idname, len(matches), i, None)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        candidates = set()
        for scene, view_layer, idname in cls.iter_all():
            if idname in idnames: candidates.update(view_layer.objects)
        
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            return obj in candidates
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def add_new(cls, objs, name):
        scene = bpy.context.scene
        view_layer = scene.view_layers.new(name)
        return view_layer
    
    @classmethod
    def rename(cls, idnames, name):
        layers_map = {idname:view_layer for scene, view_layer, idname in cls.iter_all() if idname in idnames}
        
        if isinstance(name, str):
            if cls.separator in name: name = cls._remove_scene(name)
            layers = [(idname, layers_map.get(idname), name) for idname in sorted(idnames)]
        else: # collection
            layers = [(idname, layers_map.get(idname),
                (cls._remove_scene(_name) if cls.separator in _name else _name))
                for idname, _name in zip(idnames, name)]
        
        layers_map_new = {}
        
        for idname, view_layer, name in layers:
            if not view_layer: continue
            view_layer.name = name
            layers_map_new[idname] = view_layer
        
        return {idname:view_layer.name for idname, view_layer in layers_map_new.items()}
    
    @classmethod
    def delete(cls, idnames):
        for scene, view_layer, idname in tuple(cls.iter_all()):
            if idname not in idnames: continue
            try:
                scene.view_layers.remove(view_layer)
            except RuntimeError:
                pass # this is the scene's only layer
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        def make_enable_disable(value):
            op_name = ("Enable" if value else "Disable")
            @simple_operator(f"{cls.prefix}.{op_name.lower()}", f"{op_name} {cls.plural}", f"{op_name} selected {cls.plural.lower()}", poll=batch_poll)
            def BatchOp(self, context):
                idnames = cls.selected_idnames(context)
                with UndoBlock(f"{op_name} {cls.plural}"):
                    for scene, view_layer, idname in cls.iter_all():
                        if idname not in idnames: continue
                        view_layer.use = value
                BlUI.tag_redraw()
        
        make_enable_disable(True)
        make_enable_disable(False)
        
        @simple_operator(f"{cls.prefix}.toggle_enabled", f"Toggle {cls.plural} Enabled", f"Toggle enabled state for selected {cls.plural.lower()}", poll=batch_poll)
        def BatchOp(self, context):
            idnames = cls.selected_idnames(context)
            value = None
            for scene, view_layer, idname in cls.iter_all():
                if idname not in idnames: continue
                value = (True if value is None else value) and view_layer.use
            if value is None: return False
            with UndoBlock(f"{'Hide' if value else 'Show'} {cls.plural}"):
                for scene, view_layer, idname in cls.iter_all():
                    if idname not in idnames: continue
                    view_layer.use = not value
            BlUI.tag_redraw()
        
        @simple_operator(f"{cls.prefix}.set_active", f"Set {cls.singular} Active", f"Activates the selected view layer (Click: current window, Shift+Click: all windows)", poll=batch_poll)
        class BatchOp:
            globally: False | prop()
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                active_idname = (idnames[-1] if idnames else None)
                if active_idname:
                    for scene, view_layer, idname in cls.iter_all():
                        if idname != active_idname: continue
                        windows = (context.window_manager.windows if self.globally else [context.window])
                        for window in windows:
                            window.scene = scene
                            window.view_layer = view_layer
                        BlUI.tag_redraw()
                        return {'FINISHED'}
                return {'CANCELLED'}
            def invoke(self, context, event):
                self.globally = event.shift
                return self.execute(context)
        
        def extras_view(layout, context):
            layout.operator(f"{cls.prefix}.enable", text="Enable", icon='CHECKBOX_HLT')
            layout.operator(f"{cls.prefix}.disable", text="Disable", icon='CHECKBOX_DEHLT')
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.set_active", text="Set Active", icon=cls.icon_active)
        
        return {"extras_view":extras_view, "extras_main":extras_main}

make_batch_ops(BatchOps_ViewLayers, "View Layer")

# =========================================================================== #

class BatchOps_ObjectTypes(BatchOps):
    icon = 'FILTER'
    
    @classmethod
    def icon_data(cls, idname):
        return obj_type_icons.get(idname, 'OBJECT_DATA')
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        if objs is None:
            for obj in bpy.data.objects:
                obj_type = get_obj_type(obj)
                type_name = obj_type_names.get(obj_type, obj_type)
                state = BlUtil.Object.visible_get(obj)
                yield (obj_type, type_name, obj.users, 1, state)
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
            for obj in objs:
                obj_type = get_obj_type(obj)
                type_name = obj_type_names.get(obj_type, obj_type)
                state = BlUtil.Object.visible_get(obj)
                yield (obj_type, type_name, 1, 1, state)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            return (get_obj_type(obj) in idnames)
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    merge_identical = None # doesn't really make sense for object types (and doesn't work anyway)

make_batch_ops(BatchOps_ObjectTypes, "Type")

# =========================================================================== #

class BatchOps_Object(BatchOps_IDBlock):
    icon = 'OBJECT_DATA'
    
    @classmethod
    def icon_data(cls, idname):
        obj = get_idblock(bpy.data.objects, idname)
        obj_type = get_obj_type(obj)
        return obj_type_icons.get(obj_type, 'OBJECT_DATA')
    
    @classmethod
    def get_bpy_data(cls):
        return bpy.data.objects
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        if objs is None:
            for obj in bpy.data.objects:
                state = BlUtil.Object.visible_get(obj)
                yield (obj.name_full, obj.name_full, obj.users, 1, state)
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
            for obj in objs:
                state = BlUtil.Object.visible_get(obj)
                yield (obj.name_full, obj.name_full, 1, 1, state)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            return obj.name_full in idnames
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def rename(cls, idnames, name):
        name_map = super(BatchOps_Object, cls).rename(idnames, name)
        addon_prefs = addon.preferences
        rename_data = 'OBJECT_TO_DATA' in addon_prefs.auto_rename_obj
        rename_mats = 'OBJECT_TO_MATERIALS' in addon_prefs.auto_rename_obj
        if rename_data or rename_mats:
            filter = {'DATA':rename_data, 'MATS':rename_mats}
            for idname in name_map.values():
                obj = get_idblock(bpy.data.objects, idname)
                if obj and (not obj.library):
                    sync_name(obj, filter)
        return name_map
    
    @classmethod
    def sync_editor(cls, context, area):
        space = area.spaces.active
        if area.type == 'PROPERTIES':
            try:
                space.context = 'OBJECT'
            except TypeError:
                return
    
    merge_identical = None # doesn't really make sense for objects (and doesn't work anyway)
    
    @classmethod
    def draw_prefs(cls, layout, context):
        addon_prefs = addon.preferences
        
        layout.prop_menu_enum(addon_prefs, "auto_rename_obj", text="Auto Rename")
    
    @classmethod
    def extra_operators(cls):
        @simple_operator(f"{cls.prefix}.clone", f"Clone {cls.plural}", f"Instantiate selected {cls.plural.lower()} at cursor (Click: duplicate data, Alt+Click: link data)")
        class BatchOp:
            link: False | prop()
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                if not idnames: return {'CANCELLED'}
                scene = context.scene
                view_layer = context.view_layer
                with UndoBlock(f"Clone {cls.plural}"):
                    BlUtil.Object.select_all('DESELECT')
                    obj = BlUtil.Object.active_get(view_layer)
                    for idname in idnames:
                        obj = get_idblock(bpy.data.objects, idname)
                        if not obj: continue # just in case
                        obj = obj.copy()
                        if not self.link: obj.data = obj.data.copy()
                        obj.location = scene.cursor.location.copy()
                        scene.collection.objects.link(obj)
                        BlUtil.Object.select_set(obj, True)
                    BlUtil.Object.active_set(obj, view_layer)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.link = event.alt
                return self.execute(context)
        
        @simple_operator(f"{cls.prefix}.link_to_scene", f"Link To Scene", f"Link selected {cls.plural.lower()} to the current scene")
        class BatchOp:
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                if not idnames: return {'CANCELLED'}
                collection = context.scene.collection
                with UndoBlock(f"Link {cls.plural} To Scene"):
                    for idname in idnames:
                        obj = get_idblock(bpy.data.objects, idname)
                        if not obj: continue # just in case
                        if obj_in_collection(obj, collection, True): continue
                        collection.objects.link(obj)
                BlUI.tag_redraw()
                return {'FINISHED'}
        
        def extras_select(layout, context):
            layout.operator("batch_ops.enable_selection_globally", text="Enable Selection Globally", icon='RESTRICT_SELECT_OFF')
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.clone", text="Clone", icon='DUPLICATE')
            layout.operator(f"{cls.prefix}.link_to_scene", text="Link To Scene", icon='LINKED')
        
        return {"extras_select":extras_select, "extras_main":extras_main}

make_batch_ops(BatchOps_Object, "Object", "Objects")

# =========================================================================== #

class BatchOps_ObjectData(BatchOps_IDBlock):
    contextual_ops = dict(BatchOps_IDBlock.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Ctrl+Click: assign"
    contextual_ops[(1, False, True, False)] = ("assign", {"overwrite": True})
    
    @classmethod
    def set_idblock(cls, obj, idblock):
        # In Blender 2.8 beta, there is no copy-on-write yet.
        # assigning data for linked objects works, but crashes on Undo
        if obj.library: return False
        obj.data = idblock
        return True
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        bpy_data = cls.get_bpy_data()
        if objs is None:
            for idblock in bpy_data:
                if not cls.validate(idblock): continue
                yield (idblock.name_full, idblock.name_full, idblock.users, 1, None)
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
            for obj in objs:
                if obj.type != cls.obj_type: continue
                idblock = obj.data
                yield (idblock.name_full, idblock.name_full, 1, 1, None)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            if obj.type != cls.obj_type: return False
            idblock = obj.data
            return idblock.name_full in idnames
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def copy(cls, obj):
        if obj and (obj.type == cls.obj_type):
            cls.clipboard = [obj.data.name_full]
        else:
            cls.clipboard = []
    
    @classmethod
    def paste(cls, objs, clipboard=None, overwrite=True):
        if clipboard is None: clipboard = cls.clipboard
        if clipboard is None: return
        bpy_data = cls.get_bpy_data()
        idblock = (get_idblock(bpy_data, clipboard[-1]) if clipboard else None)
        if not idblock: return
        if not cls.validate(idblock): return
        for obj in objs:
            if obj.type != cls.obj_type: continue
            cls.set_idblock(obj, idblock)
    
    @classmethod
    def make_unique(cls, objs, idnames, shared=True, reuse=True):
        addon_prefs = addon.preferences
        old_datablocks = set()
        
        max_users = {}
        for obj in objs:
            if obj.type != cls.obj_type: continue
            idblock = obj.data
            idname = idblock.name_full
            if not reuse:
                max_users[idname] = -1
            elif not shared:
                max_users[idname] = 1
            else:
                max_users[idname] = max_users.get(idname, 0) + 1
        
        shared_idblocks = {}
        for obj in objs:
            if obj.type != cls.obj_type: continue
            idblock = obj.data
            idname = idblock.name_full
            if idname not in idnames: continue
            
            unique_idblock = shared_idblocks.get(idname)
            if not unique_idblock:
                users = idblock.users - (1 if idblock.use_fake_user else 0)
                unique_idblock = (idblock.copy() if (users > max_users[idname]) else idblock)
                old_datablocks.add(idblock)
                if shared: shared_idblocks[idname] = unique_idblock
            
            cls.set_idblock(obj, unique_idblock)
        
        if addon_prefs.make_unique_fake_user:
            for datablock in old_datablocks:
                if datablock.users == 0: datablock.use_fake_user = True
    
    @classmethod
    def assign(cls, objs, idnames, overwrite=True):
        cls.paste(objs, idnames, overwrite=overwrite)
    
    @classmethod
    def replace(cls, objs, idnames, idname):
        bpy_data = cls.get_bpy_data()
        repl_idblock = (get_idblock(bpy_data, idname) if idname else None)
        if not repl_idblock: return
        if not cls.validate(repl_idblock): return
        for obj in objs:
            if obj.type != cls.obj_type: continue
            idblock = obj.data
            if idblock.name_full not in idnames: continue
            if obj.data != repl_idblock:
                cls.set_idblock(obj, idblock)
    
    @classmethod
    def rename(cls, idnames, name):
        # super(cls, cls) results in infinite recursion here
        # (since actual classes inherit from BatchOps_ObjectData)
        name_map = super(BatchOps_ObjectData, cls).rename(idnames, name)
        addon_prefs = addon.preferences
        rename_objs = 'DATA_TO_OBJECTS' in addon_prefs.auto_rename_data
        rename_mats = 'DATA_TO_MATERIALS' in addon_prefs.auto_rename_data
        if rename_objs or rename_mats:
            filter = {'OBJS':rename_objs, 'MATS':rename_mats}
            bpy_data = cls.get_bpy_data()
            for idname in name_map.values():
                data = get_idblock(bpy_data, idname)
                if data and (not data.library):
                    sync_name(data, filter)
        return name_map
    
    @classmethod
    def sync_editor(cls, context, area):
        space = area.spaces.active
        if area.type == 'PROPERTIES':
            try:
                space.context = 'DATA'
            except TypeError:
                return
    
    @classmethod
    def draw_prefs(cls, layout, context):
        addon_prefs = addon.preferences
        
        layout.prop_menu_enum(addon_prefs, "auto_rename_data", text="Auto Rename")

def make_batch_ops_objdata(obj_type, bpy_data_name, type_name, icon, singular, plural, mixin=None):
    if type_name:
        idblock_type = getattr(bpy.types, type_name)
        validate = classmethod(lambda cls, idblock: type(idblock) == idblock_type)
    else:
        validate = classmethod(lambda cls, idblock: True)
    get_bpy_data = classmethod(lambda cls: getattr(bpy.data, bpy_data_name))
    icon_data = classmethod(lambda cls, idname: icon)
    cls_dict = dict(obj_type=obj_type, get_bpy_data=get_bpy_data, validate=validate, icon_data=icon_data, icon=icon)
    if mixin: cls_dict.update(mixin.__dict__)
    batch_cls = type(f"BatchOps_{plural}", (BatchOps_ObjectData,), cls_dict)
    make_batch_ops(batch_cls, singular, plural)

def track_to_maker(cls):
    batch_poll = cls.poller()
    
    @simple_operator(f"{cls.prefix}.track_to", f"Track {cls.singular} To", f"Track selected {cls.plural.lower()} to the active object (Click: panel selection, Alt+Click: object selection, Ctrl+Click: track to a new empty)", poll=batch_poll)
    class BatchOp:
        use_obj_sel: False | prop()
        make_new_empty: False | prop()
        
        con_types = {'TRACK_TO', 'DAMPED_TRACK', 'LOCKED_TRACK'}
        @classmethod
        def get_constraint(cls, cam):
            for con in cam.constraints:
                if con.type in cls.con_types: return con
            con = cam.constraints.new('TRACK_TO')
            if cam.type in ('CAMERA', 'LIGHT'):
                con.track_axis = 'TRACK_NEGATIVE_Z'
                con.up_axis = 'UP_Y'
            return con
        
        def execute(self, context):
            if self.use_obj_sel:
                objs = set(context.selected_objects)
            else:
                idnames = set(cls.selected_idnames(context))
                objs = set(cls.filter(context.scene.objects, idnames, context=context))
                if not objs:
                    space = getattr(context, "space_data", None)
                    space_v3d = (space if space.type == 'VIEW_3D' else None)
                    scene = context.scene
                    if space_v3d and space_v3d.camera:
                        objs = {space_v3d.camera}
                    elif scene.camera:
                        objs = {scene.camera}
            
            if not objs: return {'CANCELLED'}
            
            active_obj = context.object
            if active_obj and (not BlUtil.Object.select_get(active_obj)): active_obj = None
            
            if self.make_new_empty:
                target = None
                if len(objs) <= 1: active_obj = None
            else:
                target = active_obj
            #if not (target or self.make_new_empty): return {'CANCELLED'}
            
            objs.discard(target)
            
            with UndoBlock(f"Track {cls.singular} To"):
                if not target:
                    target = bpy.data.objects.new(f"{cls.singular} Target", None)
                    context.scene.collection.objects.link(target)
                    if active_obj:
                        pos = active_obj.matrix_world.translation
                    else:
                        pos = context.scene.cursor.location
                    target.matrix_world.translation = Vector(pos)
                
                for obj in objs:
                    con = self.get_constraint(obj)
                    con.target = target
            
            BlUI.tag_redraw()
            return {'FINISHED'}
        
        def invoke(self, context, event):
            self.use_obj_sel = event.alt
            self.make_new_empty = event.ctrl
            return self.execute(context)

class CameraDataMixin:
    contextual_ops = dict(BatchOps_ObjectData.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Double-Click: set active"
    contextual_ops[(2, False, False, False)] = ("set_active", {"for_scene": True, "for_view3d": True})
    
    @classmethod
    def icon_data(cls, idname):
        cam = get_idblock(bpy.data.cameras, idname)
        if cam:
            active_cam = bpy.context.scene.camera
            if active_cam and (active_cam.data == cam):
                return 'VIEW_CAMERA'
        return 'CAMERA_DATA'
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        @simple_operator(f"{cls.prefix}.set_active", f"Set {cls.singular} Active", f"Set active the first camera that uses any of the selected camera data (Click: scene, Alt+Click: 3D view)\nSets marker in the timeline if automatic keyframe insertion is enabled", poll=batch_poll)
        class BatchOp:
            for_scene: True | prop()
            for_view3d: True | prop()
            
            @classmethod
            def get_marker(cls, scene, frame):
                for marker in scene.timeline_markers:
                    if marker.frame == frame: return marker
                return scene.timeline_markers.new("F_%s" % frame, frame=frame)
            
            def execute(self, context):
                space = getattr(context, "space_data", None)
                space_v3d = (space if space.type == 'VIEW_3D' else None)
                scene = context.scene
                
                idnames = cls.selected_idnames(context)
                active_idname = (idnames[-1] if idnames else None)
                idnames = set(idnames)
                best_lvl = 0
                best_obj = None
                for obj in cls.filter(scene.objects, idnames, context=context):
                    data_name = (obj.data.name_full if obj.data else None)
                    lvl = (1 | (int(obj.type == 'CAMERA') << 1) | (int(data_name in idnames) << 2) | (int(data_name == active_idname) << 3))
                    if lvl > best_lvl:
                        best_lvl = lvl
                        best_obj = obj
                
                with UndoBlock(f"Set {cls.singular} Active"):
                    if self.for_view3d and space_v3d: space_v3d.camera = best_obj
                    if self.for_scene: scene.camera = best_obj
                    
                    if scene.tool_settings.use_keyframe_insert_auto:
                        marker = self.get_marker(scene, scene.frame_current)
                        marker.camera = best_obj
                        
                BlUI.tag_redraw()
                return {'FINISHED'}
            
            def invoke(self, context, event):
                self.for_scene = not event.alt
                self.for_view3d = event.alt
                return self.execute(context)
        
        track_to_maker(cls)
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.set_active", text="Set Active", icon='OUTLINER_OB_CAMERA')
            layout.operator(f"{cls.prefix}.track_to", text="Track To", icon='PIVOT_CURSOR') # PIVOT_CURSOR, TRACKER, EMPTY_AXIS, PIVOT_BOUNDBOX, SHADING_BBOX
        
        return {"extras_main":extras_main}

class LightDataMixin:
    contextual_ops = dict(BatchOps_ObjectData.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Double-Click: Mute others"
    contextual_ops[(2, False, False, False)] = ("isolate", {"mode":'MUTE'})
    
    @classmethod
    def extra_operators(cls):
        track_to_maker(cls)
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.track_to", text="Track To", icon='PIVOT_CURSOR') # PIVOT_CURSOR, TRACKER, EMPTY_AXIS, PIVOT_BOUNDBOX, SHADING_BBOX
        
        return {"extras_main":extras_main}

# EMPTY has no data
make_batch_ops_objdata('ARMATURE', "armatures", "", 'ARMATURE_DATA', "Armature", "Armatures")
make_batch_ops_objdata('CAMERA', "cameras", "", 'CAMERA_DATA', "Camera", "Cameras", mixin=CameraDataMixin)
make_batch_ops_objdata('CURVE', "curves", "Curve", 'CURVE_DATA', "Curve", "Curves")
make_batch_ops_objdata('GPENCIL', "grease_pencils", "", 'GREASEPENCIL', "Grease Pencil", "Grease Pencils")
make_batch_ops_objdata('LATTICE', "lattices", "", 'LATTICE_DATA', "Lattice", "Lattices")
make_batch_ops_objdata('LIGHT', "lights", "", 'LIGHT', "Light", "Lights", mixin=LightDataMixin)
make_batch_ops_objdata('LIGHT_PROBE', "lightprobes", "", 'LIGHTPROBE_CUBEMAP', "Light Probe", "Light Probes")
make_batch_ops_objdata('MESH', "meshes", "", 'MESH_DATA', "Mesh", "Meshes")
make_batch_ops_objdata('META', "metaballs", "", 'META_DATA', "Metaball", "Metaballs")
make_batch_ops_objdata('SPEAKER', "speakers", "", 'SPEAKER', "Speaker", "Speakers")
make_batch_ops_objdata('SURFACE', "curves", "SurfaceCurve", 'SURFACE_DATA', "Surface", "Surfaces")
make_batch_ops_objdata('FONT', "curves", "TextCurve", 'FONT_DATA', "Text", "Texts")

# =========================================================================== #

def make_data_layer_rename(cls):
    batch_poll = cls.poller()
    
    @simple_operator(f"{cls.prefix}.rename", f"Rename {cls.plural}", f"Rename selected {cls.plural.lower()} (Click: in selected objects, Shift+Click: globally)", poll=batch_poll)
    class BatchOp:
        name: "" | prop()
        use_pattern: True | prop(description="Use patterns:\n"+RenamePattern.__doc__.strip())
        globally: False | prop()
        def execute(self, context):
            objs = (bpy.data.objects if self.globally else cls.selected_objects(bpy.context))
            with UndoBlock(f"Rename {cls.plural}"):
                if self.use_pattern:
                    cls.pattern_rename(cls.selected_idnames(context), self.name, context, objs=objs)
                else:
                    cls.rename(cls.selected_idnames(context), self.name, objs=objs)
            BlUI.tag_redraw()
            return {'FINISHED'}
        def invoke(self, context, event):
            self.globally = event.shift
            selected_idnames = set(cls.selected_idnames(context))
            if self.use_pattern:
                if len(selected_idnames) == 1:
                    idname = next(iter(selected_idnames), "")
                    self.name = cls.base_name(idname, "{name}")
                else:
                    self.name = "{name}"
            else:
                best_name = None
                for idname, name in zip(cls.idnames, cls.names):
                    if idname not in selected_idnames: continue
                    name = cls.base_name(idname)
                    if (best_name is None) or (len(name) < len(best_name)):
                        best_name = name
                self.name = best_name or ""
            return context.window_manager.invoke_props_dialog(self)
        def draw(self, context):
            row = self.layout.row(align=True)
            row.prop(self, "name", text="")
            row2 = row.row(align=True)
            row2.alignment = 'RIGHT'
            row2.prop(self, "use_pattern", text="", icon='CONSOLE', toggle=True)

def make_data_layer_remove(cls):
    batch_poll = cls.poller()
    
    @simple_operator(f"{cls.prefix}.remove", f"Remove {cls.plural}", f"Remove {cls.plural.lower()} from selected objects", poll=batch_poll)
    def BatchOp(self, context):
        with UndoBlock(f"Remove {cls.plural}"):
            cls._remove(cls.selected_objects(context), cls.selected_idnames(context))
        BlUI.tag_redraw()

class BatchOps_DataLayer(BatchOps):
    @classmethod
    def iter_in_obj(cls, obj):
        data_layers = cls.get_layers(obj) # can be None
        if data_layers: yield from data_layers
    
    @classmethod
    def icon_data(cls, idname):
        return cls.icon
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        if objs is None:
            objs = bpy.data.objects
        else:
            if not raw: objs = filter_objs(objs, *callbacks, context=context, subobjs=True, visible_only=visible_only)
        
        for obj in objs:
            for i, data_layer in enumerate(cls.iter_in_obj(obj)):
                yield (data_layer.name, data_layer.name, 1, i, None)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        def callback(obj):
            if isinstance(idnames, AnyIDNames): return True
            for data_layer in cls.iter_in_obj(obj):
                if data_layer.name in idnames: return True
        return filter_objs(objs, callback, *callbacks, context=context, visible_only=visible_only)
    
    @classmethod
    def copy(cls, obj):
        if not obj:
            cls.clipboard = []
        else:
            cls.clipboard = [data_layer.name for data_layer in cls.iter_in_obj(obj)]
    
    @classmethod
    def paste(cls, objs, clipboard=None, overwrite=True):
        if clipboard is None: clipboard = cls.clipboard
        if clipboard is None: return
        names = set(clipboard)
        
        for obj in objs:
            data_layers = cls.get_layers(obj) # can be None
            if data_layers is None: continue
            
            if overwrite:
                cls._remove_matches(data_layers, lambda data_layer: data_layer.name not in idnames)
            
            for info in clipboard:
                if not info: continue
                name = info
                if name in data_layers: continue
                data_layers.new(name=name)
            
            obj.update_tag(refresh={'OBJECT'})
    
    @classmethod
    def add_new(cls, objs, name):
        cls.paste(objs, [name], overwrite=False)
    
    @classmethod
    def assign(cls, objs, idnames, overwrite=True):
        clipboard = [idname for idname in idnames if idname]
        cls.paste(objs, clipboard, overwrite=overwrite)
    
    @classmethod
    def _remove(cls, objs, idnames):
        for obj in objs:
            data_layers = cls.get_layers(obj) # can be None
            if data_layers is None: continue
            
            cls._remove_matches(data_layers, lambda data_layer: data_layer.name in idnames)
            
            obj.update_tag(refresh={'OBJECT'})
    
    @classmethod
    def _remove_matches(cls, data_layers, predicate):
        # Since some Blender version, it has a weird bug - after removing
        # a data layer, other layers point to something completely different.
        # E.g. if a mesh had 2 UV layers ("UVMap", "UVMap.001"), then after
        # removing item 0, item 1 will point to "NGon Face-Vertex" instead.
        for i in range(len(data_layers) - 1, -1, -1):
            if predicate(data_layers[i]):
                data_layers.remove(data_layers[i])
    
    @classmethod
    def delete(cls, idnames):
        cls._remove(bpy.data.objects, idnames)
    
    @classmethod
    def rename(cls, idnames, name, objs=None):
        names = ([name]*len(idnames) if isinstance(name, str) else name)
        rename_map = {}
        if objs is None: objs = bpy.data.objects
        for obj in objs:
            for data_layer in cls.iter_in_obj(obj):
                idname = data_layer.name
                if idname not in idnames: continue
                data_layer.name = names[idnames.index(idname)]
                rename_map.setdefault(idname, []).append(data_layer)
        return {idname: [data_layer.name for data_layer in data_layers] for idname, data_layers in rename_map.items()}
    
    @classmethod
    def sync_editor(cls, context, area):
        space = area.spaces.active
        if area.type == 'PROPERTIES':
            try:
                space.context = 'DATA'
            except TypeError:
                return

class BatchOps_VertexGroups(BatchOps_DataLayer):
    icon = 'GROUP_VERTEX'
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Ctrl+Click: set active"
    contextual_ops[(1, False, True, False)] = ("set_active", {})
    
    @classmethod
    def get_layers(cls, obj):
        return obj.vertex_groups
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        main_overrides = set()
        
        make_data_layer_remove(cls)
        main_overrides.add("remove")
        
        make_data_layer_rename(cls)
        main_overrides.add("rename")
        
        @simple_operator(f"{cls.prefix}.set_active", f"Set {cls.singular} Active", f"Activates the selected {cls.singular.lower()}", poll=batch_poll)
        class BatchOp:
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                active_idname = (idnames[-1] if idnames else None)
                if not active_idname: return {'CANCELLED'}
                with UndoBlock(f"Set {cls.singular} Active"):
                    for obj in cls.filter(context.scene.objects, idnames, context=context):
                        for i, vertex_group in enumerate(obj.vertex_groups):
                            if vertex_group.name == active_idname:
                                obj.vertex_groups.active_index = i
                                break
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                return self.execute(context)
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.set_active", text="Set Active", icon='RESTRICT_RENDER_OFF')
        
        return {"extras_main":extras_main, "main_overrides":main_overrides}

make_batch_ops(BatchOps_VertexGroups, "Vertex Group")

# Shape keys (icon: SHAPEKEY_DATA) - not sure if batch operations on them make sense

class BatchOps_UVMaps(BatchOps_DataLayer):
    icon = 'GROUP_UVS'
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Ctrl+Click: set active"
    contextual_ops[(1, False, True, False)] = ("set_active", {})
    
    @classmethod
    def get_layers(cls, obj):
        return (obj.data.uv_layers if obj.type == 'MESH' else None)
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        main_overrides = set()
        
        make_data_layer_remove(cls)
        main_overrides.add("remove")
        
        make_data_layer_rename(cls)
        main_overrides.add("rename")
        
        @simple_operator(f"{cls.prefix}.set_active", f"Set {cls.singular} Active", f"Activates the selected {cls.singular.lower()} (Click: editing, Ctrl+Click: rendering, Alt+Click: cloning)", poll=batch_poll)
        class BatchOp:
            mode: 'EDITING' | prop(items=[
                ('EDITING', "Editing", "Editing"),
                ('RENDERING', "Rendering", "Rendering"),
                ('CLONING', "Cloning", "Cloning"),
            ])
            prop_names = {'EDITING':"active", 'RENDERING':"active_render", 'CLONING':"active_clone"}
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                active_idname = (idnames[-1] if idnames else None)
                if not active_idname: return {'CANCELLED'}
                with UndoBlock(f"Set {cls.singular} Active"):
                    for obj in cls.filter(context.scene.objects, idnames, context=context):
                        if obj.type != 'MESH': continue
                        uv_layer = obj.data.uv_layers.get(active_idname)
                        if not uv_layer: continue
                        setattr(uv_layer, self.prop_names[self.mode], True)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.mode = ('RENDERING' if event.ctrl else ('CLONING' if event.alt else 'EDITING'))
                return self.execute(context)
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.set_active", text="Set Active", icon='RESTRICT_RENDER_OFF')
        
        return {"extras_main":extras_main, "main_overrides":main_overrides}

make_batch_ops(BatchOps_UVMaps, "UV Map")

class BatchOps_VertexColors(BatchOps_DataLayer):
    icon = 'GROUP_VCOL'
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Ctrl+Click: set active"
    contextual_ops[(1, False, True, False)] = ("set_active", {})
    
    @classmethod
    def _get_layers(cls, mesh):
        # In Blender 3.2, color_attributes were introduced and vertex_colors were deprecated
        return (mesh.color_attributes if hasattr(mesh, "color_attributes") else mesh.vertex_colors)
    
    @classmethod
    def _set_active(cls, mesh, idname, mode):
        if hasattr(mesh, "color_attributes"):
            for i, attribute in enumerate(mesh.color_attributes):
                if attribute.name == idname:
                    prop_names = {'EDITING':"active_color_index", 'RENDERING':"render_color_index"}
                    setattr(mesh.color_attributes, prop_names[mode], i)
                    break
        else:
            color_layer = mesh.vertex_colors.get(idname)
            if not color_layer: return
            prop_names = {'EDITING':"active", 'RENDERING':"active_render"}
            setattr(color_layer, prop_names[mode], True)
    
    @classmethod
    def get_layers(cls, obj):
        return (cls._get_layers(obj.data) if obj.type == 'MESH' else None)
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        main_overrides = set()
        
        make_data_layer_remove(cls)
        main_overrides.add("remove")
        
        make_data_layer_rename(cls)
        main_overrides.add("rename")
        
        @simple_operator(f"{cls.prefix}.set_active", f"Set {cls.singular} Active", f"Activates the selected {cls.singular.lower()} (Click: editing, Ctrl+Click: rendering)", poll=batch_poll)
        class BatchOp:
            mode: 'EDITING' | prop(items=[
                ('EDITING', "Editing", "Editing"),
                ('RENDERING', "Rendering", "Rendering"),
            ])
            def execute(self, context):
                idnames = cls.selected_idnames(context)
                active_idname = (idnames[-1] if idnames else None)
                if not active_idname: return {'CANCELLED'}
                with UndoBlock(f"Set {cls.singular} Active"):
                    for obj in cls.filter(context.scene.objects, idnames, context=context):
                        if obj.type != 'MESH': continue
                        cls._set_active(obj.data, active_idname, self.mode)
                BlUI.tag_redraw()
                return {'FINISHED'}
            def invoke(self, context, event):
                self.mode = ('RENDERING' if event.ctrl else ('CLONING' if event.alt else 'EDITING'))
                return self.execute(context)
        
        def extras_main(layout, context):
            layout.operator(f"{cls.prefix}.set_active", text="Set Active", icon='RESTRICT_RENDER_OFF')
        
        return {"extras_main":extras_main, "main_overrides":main_overrides}

make_batch_ops(BatchOps_VertexColors, "Vertex Color")

# As of Blender 2.83, face maps API does not work
"""
class BatchOps_FaceMaps(BatchOps_DataLayer):
    icon = 'FACE_MAPS'
    
    # contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    # contextual_ops["description"] += ", Ctrl+Click: set active"
    # contextual_ops[(1, False, True, False)] = ("set_active", {})
    
    @classmethod
    def get_layers(cls, obj):
        return (obj.data.face_maps if obj.type == 'MESH' else None)
    
    @classmethod
    def extra_operators(cls):
        batch_poll = cls.poller()
        
        main_overrides = set()
        
        make_data_layer_remove(cls)
        main_overrides.add("remove")
        
        make_data_layer_rename(cls)
        main_overrides.add("rename")
        
        return {"main_overrides":main_overrides}

make_batch_ops(BatchOps_FaceMaps, "Face Map")
"""

# =========================================================================== #

class BatchOps_GreasePencilModifiers(BatchOps_ModStack):
    icon = 'MODIFIER_DATA'
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Shift+Click: enable/disable, Ctrl+Click: apply"
    contextual_ops[(1, False, False, True)] = ("toggle_enabled", {})
    contextual_ops[(1, False, True, False)] = ("apply", {"mode": 'DATA', "globally": False})
    
    area_space_context = 'MODIFIER'
    
    stack_ops_argname = "modifier"
    stack_ops_defaults = {}
    stack_ops_info = {
        "add": ("object", "gpencil_modifier_add"),
        "move_up": ("object", "gpencil_modifier_move_up"),
        "move_down": ("object", "gpencil_modifier_move_down"),
        "move_to_index": ("object", "gpencil_modifier_move_to_index"),
        "copy": ("object", "gpencil_modifier_copy"),
        "remove": ("object", "gpencil_modifier_remove"),
    }
    
    viaibility_draw_options = [
        ("show_in_editmode", None),
        ("show_viewport", None),
        ("show_render", None),
    ]
    
    enable_disable_options = [
        ("", "viewport", {"show_viewport"}),
        ("ctrl", "rendering", {"show_render"}),
    ]
    toggle_enabled_flags = ["show_viewport", "show_render"]
    
    apply_modes = [
        ('DATA', "to data"),
        ('SHAPE', "to a new shape"),
    ]
    
    @classmethod
    def get_stack(cls, obj):
        return obj.grease_pencil_modifiers
    
    @classmethod
    def apply_poll(cls, context):
        # Modifiers cannot be applied in edit/sculpt/paint modes
        mode_info = BlEnums.mode_infos.get(context.mode)
        if not mode_info: return True
        return mode_info.type not in ('EDIT', 'SCULPT', 'PAINT')
    
    @classmethod
    def apply(cls, objs, idnames, options=(), mode='DATA'):
        validate_idname = (lambda item: cls.idname(item) in idnames)
        apply_modifiers(bpy.context, objs, validate_idname, options=options, apply_as=mode, which='GPENCIL')
    
    @classmethod
    def get_common_obj_type(cls, objs):
        obj_types = {obj.type for obj in objs}
        return ('GPENCIL' if 'GPENCIL' in obj_types else None)

make_batch_ops(BatchOps_GreasePencilModifiers, "GPencil Modifier")

# =========================================================================== #

class BatchOps_ShaderEffects(BatchOps_ModStack):
    icon = 'SHADERFX'
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Shift+Click: enable/disable"
    contextual_ops[(1, False, False, True)] = ("toggle_enabled", {})
    
    area_space_context = 'SHADERFX'
    
    stack_ops_argname = "shaderfx"
    stack_ops_defaults = {}
    stack_ops_info = {
        "add": ("object", "shaderfx_add"),
        "move_up": ("object", "shaderfx_move_up"),
        "move_down": ("object", "shaderfx_move_down"),
        "move_to_index": ("object", "shaderfx_move_to_index"),
        "copy": ("object", "shaderfx_copy"),
        "remove": ("object", "shaderfx_remove"),
    }
    
    viaibility_draw_options = [
        ("show_in_editmode", None),
        ("show_viewport", None),
        ("show_render", None),
    ]
    
    enable_disable_options = [
        ("", "viewport", {"show_viewport"}),
        ("ctrl", "rendering", {"show_render"}),
    ]
    toggle_enabled_flags = ["show_viewport", "show_render"]
    
    @classmethod
    def get_stack(cls, obj):
        return obj.shader_effects
    
    @classmethod
    def get_common_obj_type(cls, objs):
        obj_types = {obj.type for obj in objs}
        return ('GPENCIL' if 'GPENCIL' in obj_types else None)

make_batch_ops(BatchOps_ShaderEffects, "Shader Effect")

# =========================================================================== #

class BatchOps_Constraints(BatchOps_ModStack):
    icon = 'CONSTRAINT'
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Shift+Click: enable/disable, Ctrl+Click: apply"
    contextual_ops[(1, False, False, True)] = ("toggle_enabled", {})
    contextual_ops[(1, False, True, False)] = ("apply", {"mode": 'DELETE', "globally": False})
    
    # Currently, object.constraint_add() operator has no properties for the "type" argument's enum items
    type_rna_prop = bpy.types.Constraint.bl_rna.properties["type"]
    
    area_space_context = 'CONSTRAINT'
    
    stack_ops_argname = "constraint"
    stack_ops_defaults = {"owner": 'OBJECT'}
    stack_ops_info = {
        "add": ("object", "constraint_add"),
        "move_up": ("constraint", "move_up"),
        "move_down": ("constraint", "move_down"),
        "move_to_index": ("constraint", "move_to_index"),
        "copy": ("constraint", "copy"),
        "remove": ("constraint", "delete"),
    }
    
    viaibility_draw_options = [
        ("enabled", None),
    ]
    
    enable_disable_options = [
        ("", "enabled", {"enabled"}),
    ]
    toggle_enabled_flags = ["enabled"]
    
    apply_modes = [
        ('DELETE', "then delete"),
        ('DISABLE', "then disable"),
    ]
    
    @classmethod
    def get_stack(cls, obj):
        return obj.constraints
    
    @classmethod
    def apply_poll(cls, context):
        return True
    
    @classmethod
    def apply(cls, objs, idnames, options=(), mode='DELETE'):
        validate_idname = (lambda item: cls.idname(item) in idnames)
        apply_constraints(bpy.context, objs, validate_idname, owner='OBJECT', mode=mode)
    
    @classmethod
    def get_common_obj_type(cls, objs):
        return 'EMPTY'

make_batch_ops(BatchOps_Constraints, "Constraint")

# =========================================================================== #

class BatchOps_BoneConstraints(BatchOps_ModStack):
    icon = 'CONSTRAINT_BONE'
    
    contextual_ops = dict(BatchOps.contextual_ops) # (clicks, alt, ctrl, shift)
    contextual_ops["description"] += ", Shift+Click: enable/disable, Ctrl+Click: apply"
    contextual_ops[(1, False, False, True)] = ("toggle_enabled", {})
    contextual_ops[(1, False, True, False)] = ("apply", {"mode": 'DELETE', "globally": False})
    
    # Currently, object.constraint_add() operator has no properties for the "type" argument's enum items
    type_rna_prop = bpy.types.Constraint.bl_rna.properties["type"]
    
    area_space_context = 'BONE_CONSTRAINT'
    
    stack_ops_argname = "constraint"
    stack_ops_defaults = {"owner": 'BONE'}
    stack_ops_info = {
        "add": ("pose", "constraint_add"),
        "move_up": ("constraint", "move_up"),
        "move_down": ("constraint", "move_down"),
        "move_to_index": ("constraint", "move_to_index"),
        "copy": ("constraint", "copy"),
        "remove": ("constraint", "delete"),
    }
    
    viaibility_draw_options = [
        ("enabled", None),
    ]
    
    enable_disable_options = [
        ("", "enabled", {"enabled"}),
    ]
    toggle_enabled_flags = ["enabled"]
    
    apply_modes = [
        ('DELETE', "then delete"),
        ('DISABLE', "then disable"),
    ]
    
    @classmethod
    def _iterate_bones(cls, obj):
        if (not obj) or (obj.type != 'ARMATURE'): return
        use_selected = (obj.mode == 'POSE')
        for pose_bone in obj.pose.bones:
            if use_selected and not pose_bone.bone.select: continue
            yield pose_bone
    
    @classmethod
    def _stack_paste(cls, pose_bone, where, item_infos):
        constraints = pose_bone.constraints
        
        def stack_index(item):
            for i, item2 in enumerate(constraints):
                if item2 == item: return i
            return -1
        
        replace_item = (None if (not where) or isinstance(where, str) else where)
        
        insert_index = -1
        replace_item_found = False
        
        if replace_item:
            insert_index = stack_index(replace_item)
            if insert_index < 0: return False
            replace_item_found = True
            constraints.remove(replace_item)
        elif where == 'BEFORE':
            insert_index = 0
        
        for item_info in item_infos:
            if not item_info: continue
            
            item = constraints.new(item_info["type"])
            if not item: continue
            
            BlRna.deserialize(item, item_info, ignore_default=True, suppress_errors=True)
            
            if (insert_index >= 0) and hasattr(constraints, "move"):
                constraints.move(stack_index(item), insert_index)
                insert_index += 1
        
        return replace_item_found
    
    @classmethod
    def get_stack(cls, obj):
        constraints = []
        for pose_bone in cls._iterate_bones(obj):
            constraints.extend(pose_bone.constraints)
        return constraints
    
    @classmethod
    def stack_paste(cls, obj, where, *item_infos):
        for pose_bone in cls._iterate_bones(obj):
            if cls._stack_paste(pose_bone, where, item_infos): break
    
    @classmethod
    def stack_clear(cls, obj):
        for pose_bone in cls._iterate_bones(obj):
            pose_bone.constraints.clear()
    
    @classmethod
    def apply_poll(cls, context):
        return context.mode != 'EDIT_ARMATURE'
    
    @classmethod
    def apply(cls, objs, idnames, options=(), mode='DELETE'):
        bones = ('ALL' if ('GLOBALLY' in options) or (bpy.context.mode != 'POSE') else 'SELECTED')
        validate_idname = (lambda item: cls.idname(item) in idnames)
        apply_constraints(bpy.context, objs, validate_idname, owner='BONE', mode=mode, bones=bones)
    
    @classmethod
    def get_common_obj_type(cls, objs):
        obj_types = {obj.type for obj in objs}
        return ('ARMATURE' if 'ARMATURE' in obj_types else None)

make_batch_ops(BatchOps_BoneConstraints, "Bone Constraint")

# =========================================================================== #

"""
Shader Editor:
* Object - materials, lights
* World - one per scene
* Line Style - per view layer, each can have multiple linesets
* shader node groups

Compositing:
* [Scene]
* compositor node groups

Texture Node Editor:
* World
* Brush
* Line Style
* texture node groups
"""

def make_batch_ops_node_editor(batch_cls, singular, plural=None, has_prefs=True, can_filter=True, tree_type=None):
    if not plural: plural = singular+"s"
    # WARNING: bl_idnames must not be too long, or Blender will truncate them
    prefix = (tree_type.lower()+"_" if tree_type else "node_editor_")
    singular_low = prefix + singular.lower().replace(" ", "_")
    plural_low = prefix + plural.lower().replace(" ", "_")
    singular_up = singular_low.upper()
    plural_up = plural_low.upper()
    prefix = f"batch_ops_{plural_low}"
    
    batch_classes.append(batch_cls)
    
    batch_cls.singular = singular
    batch_cls.plural = plural
    batch_cls.singular_low = singular_low
    batch_cls.plural_low = plural_low
    batch_cls.singular_up = singular_up
    batch_cls.plural_up = plural_up
    batch_cls.prefix = prefix
    
    batch_cls.dirty = True
    batch_cls.idnames = []
    batch_cls.names = []
    batch_cls.users = []
    batch_cls.states = []
    batch_cls.obj_sel = []
    batch_cls.selection = []
    batch_cls.clipboard = []
    batch_cls.scene = None
    batch_cls.view_layer = None
    batch_cls.click_time = 0
    batch_cls.click_index = -1
    
    batch_cls.context_btn_id = None
    
    def on_update_search(self, context):
        batch_cls.refresh(context)
    
    BatchOpsProps.__annotations__[f"{singular_low}_search_on"] = False | prop(description="Enable name filtering", options={'HIDDEN'}, update=on_update_search)
    BatchOpsProps.__annotations__[f"{singular_low}_search"] = "" | prop(description="Filter by name", options={'HIDDEN'}, update=on_update_search)
    BatchOpsProps.__annotations__[f"{singular_low}_filter"] = BatchOpsProps.__annotations__[f"filter_mode"]
    
    BatchOpsPreferences.__annotations__[f"{singular_low}_search_on"] = BatchOpsProps.__annotations__[f"{singular_low}_search_on"]
    BatchOpsPreferences.__annotations__[f"{singular_low}_filter"] = BatchOpsProps.__annotations__[f"{singular_low}_filter"]

    if has_prefs:
        @addon.Menu(idname=f"VIEW3D_MT_{prefix}_prefs", label="Options", description="Options")
        class BatchOpsPrefsMenu:
            def draw(self, context):
                layout = self.layout
                
                addon_prefs = addon.preferences
                
                layout.prop(addon_prefs, "ignore_dot_names")
                layout.prop(addon_prefs, "include_instances")
    
    class BatchOpsPanelBase(bpy.types.Panel):
        f"""Batch {plural}"""
        bl_label = f"{plural}"
        bl_idname = f"VIEW3D_PT_{prefix}"
        bl_space_type = 'NODE_EDITOR'
        bl_region_type = 'UI'
        
        def draw_header(self, context):
            if not has_prefs: return
            
            layout = self.layout
            
            row = layout.row(align=True)
            row.menu(f"VIEW3D_MT_{prefix}_prefs", text="", icon='PREFERENCES')
        
        def draw(self, context):
            layout = self.layout
            
            addon_prefs = addon.preferences
            
            filters_prefs_wm = get_screen_prefs(context, 'FILTERS')
            filters_prefs = get_screen_prefs(context, 'FILTERS', True)
            
            if can_filter and not addon_prefs.hide_filter:
                is_search_on = getattr(filters_prefs, f"{singular_low}_search_on")
                
                row = layout.row()
                row.prop(filters_prefs, f"{singular_low}_filter", text="", icon_only=is_search_on)
                row2 = row.row(align=True)
                if is_search_on: row2.prop(filters_prefs_wm, f"{singular_low}_search", text="")
                row2.prop(filters_prefs, f"{singular_low}_search_on", text="", icon='VIEWZOOM', icon_only=True)
            
            batch_cls.refresh(context)
            
            sublayout = layout.column(align=True)
            for idname, name, users in zip(batch_cls.idnames, batch_cls.names, batch_cls.users):
                icon_data = batch_cls.icon_data(idname)
                icon, icon_value = ((icon_data, 0) if isinstance(icon_data, str) else ('NONE', layout.icon(icon_data)))
                selected = batch_cls.is_active(context, idname)
                subrow = sublayout.row(align=True)
                op = subrow.operator(f"{prefix}.click", text=f"{name} ({users})", depress=selected, icon=icon, icon_value=icon_value)
                op.idname = idname
    
    @addon.Panel
    class BatchOpsPanelNode(BatchOpsPanelBase):
        bl_idname = BatchOpsPanelBase.bl_idname + "_node"
        bl_category = "Node"
        
        @classmethod
        def poll(cls, context):
            if (tree_type is not None) and (context.space_data.tree_type != tree_type): return False
            if hasattr(batch_cls, "poll") and not batch_cls.poll(context): return False
            addon_prefs = addon.preferences
            return not addon_prefs.use_batch_tab
    
    @addon.Panel
    class BatchOpsPanelBatch(BatchOpsPanelBase):
        bl_idname = BatchOpsPanelBase.bl_idname + "_batch"
        bl_category = "Batch™"
        
        @classmethod
        def poll(cls, context):
            if (tree_type is not None) and (context.space_data.tree_type != tree_type): return False
            if hasattr(batch_cls, "poll") and not batch_cls.poll(context): return False
            addon_prefs = addon.preferences
            return addon_prefs.use_batch_tab
    
    @simple_operator(f"{prefix}.click", f"Select {singular}", f"Select {singular.lower()}", {'INTERNAL'}, props=dict(idname = "" | prop()))
    def BatchOp(self, context, event):
        batch_cls.activate(context, self.idname)
        self.idname = "" # clean up, just in case
        BlUI.tag_redraw()

# =========================================================================== #

def get_tmp_obj(context, data_type, bpy_data_name, data=None, *args, **kwargs):
    name = ".batchops-tmp-"+bpy_data_name
    obj = context.scene.collection.all_objects.get(name)
    if data is None:
        if (not obj) or (obj.type != data_type) or obj.library:
            obj = bpy.data.objects.get(name)
            if (not obj) or (obj.type != data_type) or obj.library:
                bpy_data = getattr(bpy.data, bpy_data_name)
                data = bpy_data.get(name)
                if not data: data = bpy_data.new(name, *args, **kwargs)
                obj = bpy.data.objects.new(name, data)
                obj.name = name # make sure it has this name
            context.scene.collection.objects.link(obj)
    else:
        if (not obj) or (obj.type != data_type) or obj.library:
            obj = bpy.data.objects.get(name)
            if (not obj) or (obj.type != data_type) or obj.library:
                obj = bpy.data.objects.new(name, data)
                obj.name = name # make sure it has this name
            context.scene.collection.objects.link(obj)
        obj.data = data
    obj.hide_viewport = True
    obj.hide_render = True
    obj.hide_select = True
    #BlUtil.Object.select_set(obj, True, context.view_layer)
    BlUtil.Object.active_set(obj, context.view_layer)
    return obj

# =========================================================================== #

class BatchOps_NodeEditor_Materials(BatchOps_Materials):
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return (space.tree_type == 'ShaderNodeTree') and (space.shader_type == 'OBJECT')
    
    @classmethod
    def activate(cls, context, idname):
        space = context.space_data
        obj = space.id_from # could be Object, World, LineStyle...
        if cls.find_and_switch(context, obj, idname): return
        
        for obj in context.selected_objects:
            if cls.find_and_switch(context, obj, idname): return
        
        scene = context.scene
        scene_objs = scene.collection.all_objects
        for obj in scene_objs:
            if cls.find_and_switch(context, obj, idname): return
        
        obj = get_tmp_obj(context, 'MESH', "meshes")
        cls.paste([obj], [idname])
        cls.find_and_switch(context, obj, idname)
    
    @classmethod
    def find_and_switch(cls, context, obj, idname):
        layer_objs = context.view_layer.objects
        if isinstance(obj, bpy.types.Object):
            for i in range(len(obj.material_slots)):
                ms = obj.material_slots[i]
                mat = ms.material
                if mat and (mat.name_full == idname):
                    obj.active_material_index = i
                    layer_objs.active = obj
                    return True
        return False
    
    @classmethod
    def is_active(cls, context, idname):
        space = context.space_data
        obj = space.id_from # could be Object, World, LineStyle...
        if isinstance(obj, bpy.types.Object):
            i = obj.active_material_index
            if (i >= 0) and (i < len(obj.material_slots)):
                ms = obj.material_slots[i]
                mat = ms.material
                if mat and (mat.name_full == idname): return True
        return False

make_batch_ops_node_editor(BatchOps_NodeEditor_Materials, "Material", tree_type='ShaderNodeTree')

# =========================================================================== #

class BatchOps_NodeEditor_Lights(BatchOps_ObjectData):
    icon = 'LIGHT'
    obj_type = 'LIGHT'
    get_bpy_data = classmethod(lambda cls: bpy.data.lights)
    validate = classmethod(lambda cls, idblock: True)
    
    @classmethod
    def icon_data(cls, idname):
        light = get_idblock(bpy.data.lights, idname)
        return ('LIGHT_%s' % light.type if light else 'LIGHT')
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return (space.tree_type == 'ShaderNodeTree') and (space.shader_type == 'OBJECT')
    
    @classmethod
    def activate(cls, context, idname):
        space = context.space_data
        obj = space.id_from # could be Object, World, LineStyle...
        if cls.find_and_switch(context, obj, idname): return
        
        for obj in context.selected_objects:
            if cls.find_and_switch(context, obj, idname): return
        
        scene = context.scene
        scene_objs = scene.collection.all_objects
        for obj in scene_objs:
            if cls.find_and_switch(context, obj, idname): return
        
        data = get_idblock(bpy.data.lights, idname)
        obj = get_tmp_obj(context, 'LIGHT', "lights", data)
        cls.find_and_switch(context, obj, idname)
    
    @classmethod
    def find_and_switch(cls, context, obj, idname):
        layer_objs = context.view_layer.objects
        if isinstance(obj, bpy.types.Object):
            if (obj.type == 'LIGHT') and (obj.data.name_full == idname):
                layer_objs.active = obj
                return True
        return False
    
    @classmethod
    def is_active(cls, context, idname):
        space = context.space_data
        obj = space.id_from # could be Object, World, LineStyle...
        if isinstance(obj, bpy.types.Object):
            data = obj.data
            if data and (data.name_full == idname): return True
        return False

make_batch_ops_node_editor(BatchOps_NodeEditor_Lights, "Light", tree_type='ShaderNodeTree')

# =========================================================================== #

class BatchOps_NodeEditor_NodeGroups(BatchOps):
    icon = 'NODETREE'
    
    @classmethod
    def icon_data(cls, idname):
        return 'NODETREE'
    
    @classmethod
    def enumerate(cls, objs, callbacks=(), context=None, visible_only=False, raw=False):
        for node_group in bpy.data.node_groups:
            if node_group.type != cls.node_type: continue
            yield (node_group.name_full, node_group.name_full, 1, 1, None)
    
    @classmethod
    def filter(cls, objs, idnames, callbacks=(), context=None, visible_only=False):
        return []
    
    @classmethod
    def activate(cls, context, idname):
        is_active = cls.is_active(context, idname)
        space = context.space_data
        space.path.clear()
        if not is_active:
            space.path.append(bpy.data.node_groups[idname])
    
    @classmethod
    def is_active(cls, context, idname):
        space = context.space_data
        if not space.path: return False
        node_tree = space.path[-1].node_tree
        return getattr(node_tree, "name_full", "") == idname

class BatchOps_NodeEditor_NodeGroups_Shader(BatchOps_NodeEditor_NodeGroups):
    node_type = 'SHADER'

make_batch_ops_node_editor(BatchOps_NodeEditor_NodeGroups_Shader, "Node Group", tree_type='ShaderNodeTree', has_prefs=False, can_filter=False)

class BatchOps_NodeEditor_NodeGroups_Texture(BatchOps_NodeEditor_NodeGroups):
    node_type = 'TEXTURE'

make_batch_ops_node_editor(BatchOps_NodeEditor_NodeGroups_Texture, "Node Group", tree_type='TextureNodeTree', has_prefs=False, can_filter=False)

class BatchOps_NodeEditor_NodeGroups_Compositing(BatchOps_NodeEditor_NodeGroups):
    node_type = 'COMPOSITING'

make_batch_ops_node_editor(BatchOps_NodeEditor_NodeGroups_Compositing, "Node Group", tree_type='CompositorNodeTree', has_prefs=False, can_filter=False)

# =========================================================================== #

def copy_prop(prop):
    return BpyProp(prop)(copy=True)

@addon.PropertyGroup
class ScreenProps:
    show_panels_: copy_prop(BatchOpsPreferences.__annotations__["show_panels"])
    show_context_menu_: copy_prop(BatchOpsPreferences.__annotations__["show_context_menu"])
    pie_view3d_: copy_prop(BatchOpsPreferences.__annotations__["pie_view3d"])
    
    show_panels: copy_prop(BatchOpsPreferences.__annotations__["show_panels"])
    show_context_menu: copy_prop(BatchOpsPreferences.__annotations__["show_context_menu"])
    pie_view3d: copy_prop(BatchOpsPreferences.__annotations__["pie_view3d"])
    
    # Making selection local is harder, since a lot of logic
    # is written with the assumption that selection/idnames is global
    
    @classmethod
    def update_panels(cls, new_panels):
        for screen in bpy.data.screens:
            screen.batch_ops.show_panels |= new_panels
            screen.batch_ops.show_context_menu |= new_panels
    
    @classmethod
    def setup(cls):
        def init(self):
            if self.get("init"): return
            self["init"] = True
            self.show_panels_ = addon.preferences.show_panels
            self.show_context_menu_ = addon.preferences.show_context_menu
            self.pie_view3d_ = addon.preferences.pie_view3d
        
        def _get(self):
            if not self.get("init"): init(self)
            return BlRna.enum_to_int(self, "show_panels_")
        def _set(self, value):
            self.show_panels_ = BlRna.enum_from_int(self, "show_panels_", value)
        BpyProp(cls.__annotations__["show_panels"]).update(get=_get, set=_set)
        
        def _get(self):
            if not self.get("init"): init(self)
            return BlRna.enum_to_int(self, "show_context_menu_")
        def _set(self, value):
            self.show_context_menu_ = BlRna.enum_from_int(self, "show_context_menu_", value)
        BpyProp(cls.__annotations__["show_context_menu"]).update(get=_get, set=_set)
        
        def _get(self):
            if not self.get("init"): init(self)
            return BlRna.enum_to_int(self, "pie_view3d_")
        def _set(self, value):
            self.pie_view3d_ = BlRna.enum_from_int(self, "pie_view3d_", value)
        BpyProp(cls.__annotations__["pie_view3d"]).update(get=_get, set=_set)
        
        expr = re.compile(".+(_rename_on|_rename|_search_on|_search|_filter)")
        for name, prop in BatchOpsProps.__annotations__.items():
            if expr.fullmatch(name): cls.__annotations__[name] = prop

ScreenProps.setup()

def get_screen_prefs(context=None, tag=None, no_wm=False):
    if not context: context = bpy.context
    addon_prefs = addon.preferences
    if tag in addon_prefs.use_local_storage:
        return context.screen.batch_ops
    elif (tag == 'PANELS_PIE') or no_wm:
        return addon_prefs
    else:
        return context.window_manager.batch_ops

def register_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if not kc: return
    
    addon_prefs = addon.preferences
    
    #km = kc.keymaps.new(name="Object Mode")
    km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
    
    km_kwargs = {mod:True for mod in addon_prefs.pie_view3d_mods}
    kmi = km.keymap_items.new('wm.call_menu_pie', addon_prefs.pie_view3d_key, 'PRESS', **km_kwargs)
    kmi.properties.name = 'VIEW3D_MT_batch_ops_pie_view3d'
    
    km_kwargs = {mod:True for mod in addon_prefs.panel_view3d_mods}
    kmi = km.keymap_items.new('batch_ops.panel_view3d', addon_prefs.panel_view3d_key, 'PRESS', **km_kwargs)

def unregister_keymaps():
    addon.unregister_keymaps()

def register():
    addon.register()
    
    addon.type_extend("WindowManager", "batch_ops", BatchOpsProps)
    addon.type_extend("Screen", "batch_ops", ScreenProps)
    
    register_keymaps()

def unregister():
    addon.unregister()
