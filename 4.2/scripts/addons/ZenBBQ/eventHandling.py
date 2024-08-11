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

# Copyright 2022, Dmitry Aleksandrovich Maslov (ABTOMAT)

import bpy
from bpy.app.handlers import persistent
from .operators import ZBBQ_OT_DrawHighlight

from . import globals as ZBBQ_Globals
from .vlog import Log
from .commonFunc import ZBBQ_CommonFunc, ZBBQ_MaterialFunc
# from .bake import ZBBQ_Bake
from .sceneConfig import ZBBQ_BuggedPinkShaderReset3DSpace, ZBBQ_SceneConfigFunc

from timeit import default_timer as timer
from .overlay_msgbox import show_overlay_messagebox, cleanup_overlay_handles
from .draw_sets import (
    ZBBQ_EdgeLayerManager,
    is_draw_handler_enabled,
    check_update_cache_on_change,
    remove_all_handlers3d,
    reset_all_draw_cache
)

from .blender_zen_utils import ZenLocks

ZBBQ_RnaHandleOwnerCommon = None
ZBBQ_RnaHandleOwnerSpaceView3DOverlay = None
ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay = None

ZBBQ_DepsgrapContextModeLast = ""


g_LAST_UPDATE = {}


@persistent
def ZBBQ_CbDepsgraphUpdatePost(scene):

    if ZenLocks.is_depsgraph_update_locked():
        return

    if bpy.context.mode in {'EDIT_MESH'}:

        p_cls_draw_mgr = ZBBQ_EdgeLayerManager

        if is_draw_handler_enabled(ZBBQ_EdgeLayerManager):
            depsgraph = bpy.context.evaluated_depsgraph_get()

            for update in depsgraph.updates:
                if update.id.original in bpy.context.selected_editable_objects:
                    if update.is_updated_geometry:  # or update.is_updated_transform:
                        p_obj = update.id.original

                        global g_LAST_UPDATE
                        if p_obj not in g_LAST_UPDATE:
                            g_LAST_UPDATE[p_obj] = None

                        last_obj_draw_update = 0 if g_LAST_UPDATE[p_obj] is None else g_LAST_UPDATE[p_obj]
                        update_draw_span = timer() - last_obj_draw_update

                        interval = timer()
                        if p_obj.data.is_editmode:

                            Log.debug('Update:', p_obj.name, timer())

                            interval = timer()
                            check_update_cache_on_change(p_cls_draw_mgr, p_obj, update.id)
                            elapsed = timer() - interval

                            if elapsed > 0.2:
                                Log.debug(p_obj.name, 'Check update time exceeded:', elapsed, 'update_draw_span:', update_draw_span)
                                if update_draw_span < elapsed * 2:
                                    Log.debug('Performance limit exceeded! Display cancelled!')
                                    remove_all_handlers3d()

                                    show_overlay_messagebox('ZBBQ_DRAW_HIGHLIGHT',
                                                            'Performance limit exceeded! Display cancelled!')
                            else:
                                Log.debug(p_obj.name, 'Update in limit:', elapsed, "time:", timer())

                            g_LAST_UPDATE[p_obj] = timer()

# @persistent
# def ZBBQ_CbBakePre(dummy1, dummy2):
#     Log.debug("[ZBBQ_CbBakePre] Invoked!")


# @persistent
# def ZBBQ_CbBakeCancel(dummy1, dummy2):
#     Log.debug("[ZBBQ_CbBakeCancel] Invoked!")


# @persistent
# def ZBBQ_CbBakeComplete(dummy1, dummy2):
#     Log.debug("[ZBBQ_CbBakeComplete] Invoked!")

@persistent
def ZBBQ_CbSceneLoaded(scene):

    bpy.context.scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce = False

    ZBBQ_RnaUnsubscribeCommon()
    ZBBQ_RnaUnsubscribeSpaceView3DOverlay()
    ZBBQ_RnaUnsubscribeSpaceView3DOverlayEdgeDisplay()

    ZBBQ_RnaSubscribeCommon()
    ZBBQ_RnaSubscribeSpaceView3DOverlay()
    ZBBQ_RnaSubscribeSpaceView3DOverlayEdgeDisplay()

    remove_all_handlers3d()
    reset_all_draw_cache()

    ZBBQ_SceneConfigFunc.CbOnInit()

    ZBBQ_MaterialFunc.CheckNodeTreesVersionsAndUpdateIfNecessary()
    ZBBQ_CommonFunc.CheckSceneObjectsAndUpdateIfNecessary()


@persistent
def ZBBQ_CbSceneSaved(scene):

    ZBBQ_SceneConfigFunc.CbOnSceneSaved()


_was_draw_enabled = False


def ZBBQ_CbObjectInteractionModeChanged(handle):
    try:
        global _was_draw_enabled
        if bpy.context.mode in {'EDIT_MESH'}:
            if _was_draw_enabled:
                bpy.ops.zbbq.draw_highlight('INVOKE_DEFAULT', mode='ON')
        else:
            _was_draw_enabled = is_draw_handler_enabled(ZBBQ_EdgeLayerManager)
            remove_all_handlers3d()

    except Exception as e:
        Log.debug('Error: TOOL CHANGED:', e)


def ZBBQ_CbSpaceView3DShadingChanged(handle):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            spaceView3D = area.spaces.active
            # print(f"ZBBQ_Globals.buggedPinkShaderReset3DSpaceDeferred: {ZBBQ_Globals.buggedPinkShaderReset3DSpaceDeferred}")
            if (spaceView3D.shading.studio_light != 'Default' and ZBBQ_Globals.buggedPinkShaderReset3DSpaceDeferred):
                ZBBQ_Globals.buggedPinkShaderReset3DSpaceDeferred = False
                ZBBQ_BuggedPinkShaderReset3DSpace(spaceView3D)
                # print("ZBBQ_Globals.buggedPinkShaderReset3DSpaceDeferred Done!")


def ZBBQ_CbSpaceView3DOverlayChanged(handle):

    # msg = "Overlay On/Off changed!"
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            spaceView3D = area.spaces.active
            # msg += f" It is now: {spaceView3D.overlay.show_overlays}"

            if not spaceView3D.overlay.show_overlays:
                temp = bpy.context.scene.ZBBQ_ZenBBQOverlayShow
                ZBBQ_OT_DrawHighlight.InvokeManually('OFF')
                bpy.context.scene.ZBBQ_ZenBBQOverlayShow = temp
                Log.debug("Overlays Off!")
            else:
                ZBBQ_OT_DrawHighlight.InvokeManually('ON' if bpy.context.scene.ZBBQ_ZenBBQOverlayShow else 'OFF')
                Log.debug(f"Overlays Restored! ZBBQ Overlays: {bpy.context.scene.ZBBQ_ZenBBQOverlayShow}")
    # Log.debug(msg)
    Log.debug("Overlay On/Off changed!")


def ZBBQ_CbSpaceView3DOverlayEdgeDisplayChanged(handle):
    Log.debug("Overlay edge display settings changed!")
    # Mark that we don't want to restore user's settings since they're obsolete
    bpy.context.scene.ZBBQ_OverlayConfigIsStored = False


def ZBBQ_RnaSubscribeCommon():

    global ZBBQ_RnaHandleOwnerCommon

    if ZBBQ_RnaHandleOwnerCommon is None:
        ZBBQ_RnaHandleOwnerCommon = object()

    # User changed object interaction mode

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=ZBBQ_RnaHandleOwnerCommon,
        args=(ZBBQ_RnaHandleOwnerCommon,),
        notify=ZBBQ_CbObjectInteractionModeChanged,
        options={"PERSISTENT", }
    )

    # User changed SpaceView3D shading value

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DShading, "type"),
        owner=ZBBQ_RnaHandleOwnerCommon,
        args=(ZBBQ_RnaHandleOwnerCommon,),
        notify=ZBBQ_CbSpaceView3DShadingChanged,
        options={"PERSISTENT", }
    )


def ZBBQ_RnaSubscribeSpaceView3DOverlay():

    Log.debug("Subscribe Overlay On/Off!")

    global ZBBQ_RnaHandleOwnerSpaceView3DOverlay

    if ZBBQ_RnaHandleOwnerSpaceView3DOverlay is None:
        ZBBQ_RnaHandleOwnerSpaceView3DOverlay = object()

    # User changed SpaceView3D overlay on/off

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DOverlay, "show_overlays"),
        owner=ZBBQ_RnaHandleOwnerSpaceView3DOverlay,
        args=(ZBBQ_RnaHandleOwnerSpaceView3DOverlay,),
        notify=ZBBQ_CbSpaceView3DOverlayChanged,
        options={"PERSISTENT", }
    )


def ZBBQ_RnaSubscribeSpaceView3DOverlayEdgeDisplay():

    Log.debug("Subscribe Overlay Edge Display!")

    global ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay

    if ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay is None:
        ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay = object()

    # User changed SpaceView3D overlay settings

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DOverlay, "show_edge_crease"),
        owner=ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay,
        args=(ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay,),
        notify=ZBBQ_CbSpaceView3DOverlayEdgeDisplayChanged,
        options={"PERSISTENT", }
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DOverlay, "show_edge_sharp"),
        owner=ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay,
        args=(ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay,),
        notify=ZBBQ_CbSpaceView3DOverlayEdgeDisplayChanged,
        options={"PERSISTENT", }
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DOverlay, "show_edge_bevel_weight"),
        owner=ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay,
        args=(ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay,),
        notify=ZBBQ_CbSpaceView3DOverlayEdgeDisplayChanged,
        options={"PERSISTENT", }
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DOverlay, "show_edge_seams"),
        owner=ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay,
        args=(ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay,),
        notify=ZBBQ_CbSpaceView3DOverlayEdgeDisplayChanged,
        options={"PERSISTENT", }
    )


def ZBBQ_RnaUnsubscribeCommon():

    global ZBBQ_RnaHandleOwnerCommon

    if ZBBQ_RnaHandleOwnerCommon is not None:
        bpy.msgbus.clear_by_owner(ZBBQ_RnaHandleOwnerCommon)
        ZBBQ_RnaHandleOwnerCommon = None


def ZBBQ_RnaUnsubscribeSpaceView3DOverlayEdgeDisplay():

    global ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay

    if ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay is not None:

        Log.debug("Unsubscribe Overlay Edge Display!")
        bpy.msgbus.clear_by_owner(ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay)
        ZBBQ_RnaHandleOwnerSpaceView3DOverlayEdgeDisplay = None
    else:
        Log.error("Can't unsubscribe Overlay Edge Display! Something went wrong...")


def ZBBQ_RnaUnsubscribeSpaceView3DOverlay():

    global ZBBQ_RnaHandleOwnerSpaceView3DOverlay

    if ZBBQ_RnaHandleOwnerSpaceView3DOverlay is not None:

        Log.debug("Unsubscribe Overlay On/Off Display!")
        bpy.msgbus.clear_by_owner(ZBBQ_RnaHandleOwnerSpaceView3DOverlay)
        ZBBQ_RnaHandleOwnerSpaceView3DOverlay = None
    else:
        Log.error("Can't unsubscribe Overlay On/Off! Something went wrong...")


def register():

    ZBBQ_RnaSubscribeCommon()
    ZBBQ_RnaSubscribeSpaceView3DOverlay()
    ZBBQ_RnaSubscribeSpaceView3DOverlayEdgeDisplay()

    if ZBBQ_CbSceneLoaded not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(ZBBQ_CbSceneLoaded)

    if ZBBQ_CbSceneSaved not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(ZBBQ_CbSceneSaved)

    if ZBBQ_CbDepsgraphUpdatePost not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(ZBBQ_CbDepsgraphUpdatePost)

    # if ZBBQ_CbBakePre not in bpy.app.handlers.object_bake_pre:
    #     bpy.app.handlers.object_bake_pre.append(ZBBQ_CbBakePre)

    # if ZBBQ_CbBakeComplete not in bpy.app.handlers.object_bake_complete:
    #     bpy.app.handlers.object_bake_complete.append(ZBBQ_CbBakeComplete)

    # if ZBBQ_CbBakeCancel not in bpy.app.handlers.object_bake_cancel:
    #     bpy.app.handlers.object_bake_cancel.append(ZBBQ_CbBakeCancel)

    ZBBQ_CommonFunc.BevelPresetGroupsCreateDefaultIfNone()
    bpy.app.timers.register(ZBBQ_SceneConfigFunc.CbOnInit)  # These actions need to be done at add-on init as well as at scene loaded


def unregister():

    cleanup_overlay_handles()

    remove_all_handlers3d()

    ZBBQ_RnaUnsubscribeCommon()
    ZBBQ_RnaUnsubscribeSpaceView3DOverlay()
    ZBBQ_RnaUnsubscribeSpaceView3DOverlayEdgeDisplay()

    if ZBBQ_CbSceneLoaded in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(ZBBQ_CbSceneLoaded)

    if ZBBQ_CbSceneSaved in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(ZBBQ_CbSceneSaved)

    if ZBBQ_CbDepsgraphUpdatePost in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(ZBBQ_CbDepsgraphUpdatePost)

    # if ZBBQ_CbBakePre in bpy.app.handlers.object_bake_pre:
    #     bpy.app.handlers.object_bake_pre.remove(ZBBQ_CbBakePre)

    # if ZBBQ_CbBakeComplete in bpy.app.handlers.object_bake_complete:
    #     bpy.app.handlers.object_bake_complete.remove(ZBBQ_CbBakeComplete)

    # if ZBBQ_CbBakePre in bpy.app.handlers.object_bake_pre:
    #     bpy.app.handlers.object_bake_pre.remove(ZBBQ_CbBakePre)
