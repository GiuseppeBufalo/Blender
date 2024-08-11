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

import os
import platform
import bpy
from .commonFunc import ZBBQ_MaterialFunc
from .vlog import Log


class ZBBQ_Bake:
    bakingQueue = []
    bakedMats = []
    activeContext = None

    bakeFinished = False

    def BakeFolderIsValid():
        s_dir = bpy.context.scene.ZBBQ_BakeSaveToFolderExpand
        return (os.path.exists(s_dir) and os.path.isdir(s_dir))

    def BakeFolderOpen():
        s_dir = bpy.context.scene.ZBBQ_BakeSaveToFolderExpand
        bpy.ops.wm.path_open(filepath=s_dir)

    def GetBakeMacro():
        class RENDER_OT_bake_macro(bpy.types.Macro):
            bl_idname = "render.bake_macro"
            bl_label = "Bake Macro"

            @classmethod
            def define(cls, idname, **kwargs):
                op = super().define(idname).properties
                for key, val in kwargs.items():
                    setattr(op, key, val)

        old = getattr(bpy.types, "RENDER_OT_bake_macro", False)
        if old:
            bpy.utils.unregister_class(old)
        bpy.utils.register_class(RENDER_OT_bake_macro)
        return RENDER_OT_bake_macro

    @classmethod
    def ClearQueuesEtc(cls):
        cls.bakedMats = []
        cls.bakingQueue = []

    @classmethod
    def ObjectBakeNormalNext(cls):

        if(len(cls.bakingQueue) > 0):
            obj = cls.bakingQueue[0]

            Log.debug(f"[ObjectBakeNormal] started for {obj.name}")
            for mat in obj.data.materials:
                if(not ZBBQ_MaterialFunc.MaterialHasShaderNodesBakingImage(mat)):
                    ZBBQ_MaterialFunc.MaterialAddShaderNodeBakingImage(mat)

            cls.bakedMats.append(mat)

            # Deselect all andthen select obj
            for ob in bpy.context.view_layer.objects:
                try:
                    ob.select_set(False)
                except Exception as e:
                    Log.warn('BAKE SELECT:', e)

            obj.select_set(True)

            # Render properties

            bpy.context.scene.cycles.time_limit = 20
            # bpy.context.scene.cycles.bake_type = 'NORMAL'

            bpy.context.scene.render.bake.use_selected_to_active = False

            # if(cls.activeContext is not None):
            #     Log.debug(f"Context Window: {bpy.context.window} Active Window: {cls.activeContext.window}")

            # bpy.app.handlers.object_bake_complete.append(self.onBakeCompleted)

            # bpy.ops.object.bake('INVOKE_DEFAULT', type='NORMAL')  # invoked externally

            # Need to remember bakings

    @classmethod
    def AddObjectToBakingNormalQueue(cls, obj):
        cls.bakingQueue.append(obj)

    @classmethod
    def OnBakigCompleted(cls):

        Log.debug("[OnBakigCompleted] Invoked!")

        # Remove last rendered
        if(len(cls.bakingQueue) > 0):
            cls.bakingQueue.pop(0)

        # Needs to be done externally, from macros
        # Render Next
        if(len(cls.bakingQueue) > 0):
            cls.ObjectBakeNormalNext()
