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

import bmesh
import bpy
import bgl
import gpu
import mathutils

from gpu_extras.batch import batch_for_shader

from .consts import ZBBQ_Consts
from .commonFunc import ZBBQ_CommonFunc
from .blender_zen_utils import ZenPolls

ZBBQ_ShaderColoredEdges = None
ZBBQ_BatchColoredEdges = None
ZBBQ_DrawHandlerColoredEdges = None

ZBBQ_OverlaySurfaces = None


class ZBBQ_OverlaySurface():

    obj = None
    shader = None
    batch = None

    def __init__(self, obj):
        self.obj = obj
        self.shader = ZBBQ_ShaderColoredEdges

    @classmethod
    def BuildForObject(cls, obj):

        if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
            return None

        surface = cls(obj)
        surface.Rebuild()

        return surface

    def Rebuild(self):

        colorUndetected = (0.2, 0.2, 0.2, 1.0)

        radiusToColor = {}
        bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()
        for bp in bpg.bevelPresets:
            radiusToColor[bp.radius*bp.unitAndSceneScaleMultiplier()] = (bp.color.r, bp.color.g, bp.color.b, 1.0)

        threshold = ZBBQ_CommonFunc.GetPrefs().smartSelectRadiusThreshold*0.01

        vertCoords = []
        vertColors = []

        needToFreeBM = False

        if self.obj.data.is_editmode:  # Happens on scene load
            bm = bmesh.from_edit_mesh(self.obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(self.obj.data)
            needToFreeBM = True

        dataLayer = bm.verts.layers.float.get(ZBBQ_Consts.customDataLayerRadiusName)

        if dataLayer is not None:

            vertCoords = [vert.co for verts in [edge.verts for edge in bm.edges] for vert in verts]

            colorMatched = False

            for edge in bm.edges:
                for vert in edge.verts:
                    # vertCoords.append(vert.co)

                    colorMatched = False
                    for rtc in radiusToColor.items():
                        if abs(vert[dataLayer] - rtc[0]) <= threshold*rtc[0]:
                            vertColors.append(rtc[1])
                            colorMatched = True
                            break
                        if colorMatched:
                            break

                    if not colorMatched:
                        vertColors.append(colorUndetected)

        else:  # Consider every vertex to have zero radius

            # Find out if we have color for zero value. If not, undetected color will be used
            zeroColor = colorUndetected
            for rtc in radiusToColor.items():
                if rtc[0] == 0:
                    zeroColor = rtc[1]
                    break

            # for edge in bm.edges:
            #     for vert in edge.verts:
            #         vertCoords.append(vert.co)
            #         vertColors.append(zeroColor)

            vertCoords = [vert.co for verts in [edge.verts for edge in bm.edges] for vert in verts]
            vertColors = [zeroColor]*len(vertCoords)

        if needToFreeBM:
            bm.free()

        MatObjWorld = self.obj.matrix_world

        for i in range(len(vertCoords)):
            vertCoords[i] = MatObjWorld @ mathutils.Vector(vertCoords[i])

        self.batch = batch_for_shader(ZBBQ_ShaderColoredEdges, 'LINES', {"pos": vertCoords, "color": vertColors})

    def draw(self):
        self.shader.bind()
        self.batch.draw(self.shader)


class ZBBQ_Overlay():

    @staticmethod
    def ColoredEdgesRebuildForObjectsInModeIfDisplayed():

        global ZBBQ_DrawHandlerColoredEdges
        if ZBBQ_DrawHandlerColoredEdges is None:
            return

        ZBBQ_Overlay.ColoredEdgesRebuildForObjectsInMode()

    @staticmethod
    def ColoredEdgesRebuildForObjectsInMode():

        global ZBBQ_OverlaySurfaces
        ZBBQ_OverlaySurfaces = []

        for obj in [obj for obj in bpy.context.selected_editable_objects if ZBBQ_CommonFunc.ObjectIsConvenient(obj)]:
            ZBBQ_OverlaySurfaces.append(ZBBQ_OverlaySurface.BuildForObject(obj))

    @staticmethod
    def ColoredEdgesRebuildForObject(obj):

        # print(f"Rebuilding buffer for {obj.name}")

        global ZBBQ_OverlaySurfaces

        for surface in ZBBQ_OverlaySurfaces:
            if surface.obj == obj:
                surface.Rebuild()
                break

    @classmethod
    def ColoredEdgesDisplayEnable(cls):

        # print("Enable overlay!")

        global ZBBQ_DrawHandlerColoredEdges
        if ZBBQ_DrawHandlerColoredEdges is not None:
            cls.ColoredEdgesDisplayDisable()
        ZBBQ_DrawHandlerColoredEdges = bpy.types.SpaceView3D.draw_handler_add(cls.ColoredEdgesDisplayDraw, (), 'WINDOW', 'POST_VIEW')

        # To-Do: Better check if there were made mesh edits since last switch (will it even give any noticeable performance boost?)
        ZBBQ_Overlay.ColoredEdgesRebuildForObjectsInMode()

        cls.View3DRedraw()

    def ColoredEdgesDisplayDisable():

        # print("Disable overlay!")

        global ZBBQ_DrawHandlerColoredEdges
        if ZBBQ_DrawHandlerColoredEdges is not None:
            bpy.types.SpaceView3D.draw_handler_remove(ZBBQ_DrawHandlerColoredEdges, 'WINDOW')
            ZBBQ_DrawHandlerColoredEdges = None

    def ColoredEdgesDisplayDraw():
        bgl.glLineWidth(3)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

        for surface in ZBBQ_OverlaySurfaces:
            surface.draw()

        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        bgl.glDisable(bgl.GL_BLEND)

    def View3DRedraw():
        for area in bpy.context.window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def register():
    global ZBBQ_ShaderColoredEdges, ZBBQ_OverlaySurfaces

    if ZBBQ_ShaderColoredEdges is None:
        ZBBQ_ShaderColoredEdges = gpu.shader.from_builtin(
            '3D_SMOOTH_COLOR' if ZenPolls.version_lower_3_5_0 else 'SMOOTH_COLOR')

    if ZBBQ_OverlaySurfaces is None:
        ZBBQ_OverlaySurfaces = []


def unregister():

    if ZBBQ_DrawHandlerColoredEdges is not None:
        ZBBQ_Overlay.ColoredEdgesDisplayDisable()

    global ZBBQ_ShaderColoredEdges, ZBBQ_OverlaySurfaces

    if ZBBQ_ShaderColoredEdges is not None:
        ZBBQ_ShaderColoredEdges = None

    if ZBBQ_OverlaySurfaces is not None:
        ZBBQ_OverlaySurfaces = None
