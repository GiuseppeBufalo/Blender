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

# Copyright 2021, Alex Zhornyak

import bpy
import gpu
import bmesh
from gpu_extras.batch import batch_for_shader

from timeit import default_timer as timer
from mathutils import Vector
import numpy as np

from .vlog import Log

from .consts import ZBBQ_Consts

from .commonFunc import ZBBQ_CommonFunc
from .blender_zen_utils import ZenPolls


if ZenPolls.version_lower_3_5_0:
    shader_lines = gpu.shader.from_builtin('3D_POLYLINE_SMOOTH_COLOR')
else:
    shader_lines = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')


class BasicCacher:
    def __init__(self) -> None:
        self.obj = None
        self.last_bbox_data = ()
        self.volume = 0
        self.layer_name = ''
        self.force_rebuild_cache = True
        self.batch = None
        self.is_cache_built = False
        self.mtx = None
        self.z_order = 1
        self.force_rebuild_eval_cache = False
        self.bound_box = None
        self.me = None
        self.bm = None
        self.mesh_statistics = ''
        self.last_bm_data = ''
        pass

    def get_bm_data(self, bm: bmesh.types.BMesh):
        return (len(bm.verts), len(bm.edges), len(bm.faces))

    def get_mesh_data(self, mesh):
        return (len(mesh.vertices), len(mesh.edges), len(mesh.polygons))

    def get_bound_box(self, p_obj: bpy.types.Object):
        return [Vector(v) for v in p_obj.bound_box]

    def ensure_mesh(self, p_obj: bpy.types.Object):
        if self.me is None:
            self.me = p_obj.to_mesh()

    def get_bm(self, p_obj):
        if p_obj.is_evaluated:
            if not self.bm:
                self.bm = bmesh.new(use_operators=False)
                self.ensure_mesh(p_obj)
                self.bm.from_mesh(self.me)
            return self.bm
        else:
            return bmesh.from_edit_mesh(p_obj.data)

    def cleanup_mesh(self, p_obj):
        if self.me:
            p_obj.to_mesh_clear()
            self.me = None
        if self.bm:
            self.bm.free()
            self.bm = None

    def get_cache_vol(self, p_obj):
        # Do not combine into single line! Much worse performance!
        if p_obj.is_evaluated:
            self.ensure_mesh(p_obj)
            self.mesh_statistics = self.get_mesh_data(self.me)
            vol = [f.area for f in self.me.polygons if not f.hide]
            return sum(vol)
        else:
            bm = bmesh.from_edit_mesh(p_obj.data)
            self.mesh_statistics = self.get_bm_data(bm)
            vol = [f.calc_area() for f in bm.faces if not f.hide]
            return sum(vol)

    def fill_verts(self, p_obj):
        if p_obj.is_evaluated:
            self.ensure_mesh(p_obj)
            self.verts = np.empty((len(self.me.vertices), 3), 'f')
            self.me.vertices.foreach_get("co", np.reshape(self.verts, len(self.me.vertices) * 3))
        else:
            bm = bmesh.from_edit_mesh(p_obj.data)
            self.verts = [v.co.copy() for v in bm.verts]

    def recalc_mesh(self, p_mgr_cls, p_obj, volume=None):
        self.obj = p_obj

        self.volume = self.get_cache_vol(p_obj) if volume is None else volume
        self.last_bbox_data = self.get_bound_box(p_obj)
        self.last_bm_data = self.mesh_statistics
        self.layer_name = ''
        self.is_cache_built = False
        self.force_rebuild_cache = True

    def is_bmesh_valid(self, p_obj):
        if self.obj != p_obj:
            return False

        # 1) check that verts, edges, faces, loops are the same
        new_bm_data = ''
        if p_obj.is_evaluated:
            if self.last_bbox_data != self.get_bound_box(p_obj):
                # print('Modified bbox: Last', self.last_bbox_data)
                # print('Modified bbox: New', self.get_bound_box(p_obj))
                return False
            self.ensure_mesh(p_obj)
            new_bm_data = self.get_mesh_data(self.me)
        else:
            bm = bmesh.from_edit_mesh(p_obj.data)
            new_bm_data = self.get_bm_data(bm)
        if self.last_bm_data != new_bm_data:
            # print('Modified elems: Last', self.last_bm_data)
            # print('Modified elems: New', new_bm_data)
            return False

        return True

    def is_bmesh_same(self, p_obj):
        if not self.is_bmesh_valid(p_obj):
            return False, None

        # 2) check that volume remains same
        vol = self.get_cache_vol(p_obj)

        if self.volume != vol:
            # print('Modified vol: Last:', self.volume, 'New:', vol)
            return False, vol

        return True, vol

    def check_draw_cache_prepared(self, p_mgr_cls, p_obj, p_display_groups, b_calc_vol=False):
        if b_calc_vol:
            result, vol = self.is_bmesh_same(p_obj)
            if result is False:
                self.recalc_mesh(p_mgr_cls, p_obj, volume=vol)
        else:
            if not self.is_bmesh_valid(p_obj):
                self.recalc_mesh(p_mgr_cls, p_obj)

        if self.force_rebuild_cache:
            try:
                self.build_cache(p_mgr_cls, p_obj, p_display_groups)
            except ReferenceError as e:
                Log.error('BUILD CACHE:', e)
                self.recalc_mesh(p_mgr_cls, p_obj, volume=self.volume)
                self.build_cache(p_mgr_cls, p_obj, p_display_groups)

    def build_cache(self, p_mgr_cls, p_obj, p_display_groups):
        self.batch = None
        self.force_rebuild_cache = False
        self.force_rebuild_eval_cache = True
        if len(p_display_groups):
            p_group = p_display_groups[0]
            self.build_group_cache(p_mgr_cls, p_obj, p_group, p_display_groups)

    # ABSTRACT METHODS
    def build_group_cache(self, p_mgr_cls, p_obj, p_group, p_display_groups):
        raise Exception("ABSTRACT> 'build_cache'")

    def get_edge_z_offset(self, option_enabled):
        if option_enabled is False:
            return 0.0

        try:
            object_volume = self.obj.dimensions.x * self.obj.dimensions.y * self.obj.dimensions.z
            return object_volume / 50000 if object_volume < 5 else 0.0001
        except Exception:
            return 0.0


class BasicSetsCacher(BasicCacher):
    def draw(self, p_mgr_cls, p_obj, p_display_groups):
        if len(p_display_groups):
            p_group = p_display_groups[0]
            try:
                if (not self.is_cache_built) or (self.layer_name != p_group.layer_name):
                    self.force_rebuild_cache = True

                self.check_draw_cache_prepared(p_mgr_cls, p_obj, p_display_groups)

                if self.batch is not None:
                    alpha = 0.4
                    with gpu.matrix.push_pop():
                        gpu.matrix.multiply_matrix(p_obj.matrix_world)
                        self._internal_draw(alpha)
            except Exception as e:
                Log.error('ERROR>', e)
                self.cleanup_mesh(p_obj)

    def _internal_draw(self, p_alpha):
        Log.error("ABSTRACT> '_internal_draw'")


# EDGES
class EdgesCacher(BasicSetsCacher):
    def __init__(self) -> None:
        BasicSetsCacher.__init__(self)

        self.verts = []
        self.indices = []
        self.colors = []
        self.shader = shader_lines
        pass

    def is_bmesh_valid(self, p_obj):
        if super().is_bmesh_valid(p_obj):
            try:
                if not p_obj.is_evaluated:
                    bm = bmesh.from_edit_mesh(p_obj.data)
                    bm.verts.ensure_lookup_table()
                    bm.edges.ensure_lookup_table()
                return True
            except ReferenceError as e:
                Log.debug('BMESH is invalid:', e)
        return False

    def recalc_mesh(self, p_mgr_cls, p_obj, volume=None):
        interval = timer()
        BasicSetsCacher.recalc_mesh(self, p_mgr_cls, p_obj, volume=volume)
        self.fill_verts(p_obj)
        self.indices = []
        Log.debug(p_obj.name, '[Edge Bevel] mesh recalculated:', self.mesh_statistics, 'secs:', timer() - interval)

    def build_group_cache(self, p_mgr_cls, p_obj, p_group, p_display_groups):
        self.is_cache_built = True
        self.layer_name = p_group.layer_name
        self.force_rebuild_eval_cache = True
        if p_group in p_display_groups:

            bm = bmesh.from_edit_mesh(p_obj.data)

            dataLayer = bm.verts.layers.float.get(ZBBQ_Consts.customDataLayerRadiusName)
            if dataLayer is not None:
                radiusToColor = {}
                bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()
                for bp in bpg.bevelPresets:
                    radiusToColor[bp.radius*bp.unitAndSceneScaleMultiplier()] = (bp.color.r, bp.color.g, bp.color.b, 0.75)
                    # radiusToColor[bp.radius*bp.unitAndSceneScaleMultiplier()] = (25/255.0, 191/255.0, 111/255.0, 1)

                threshold = ZBBQ_Consts.overlayEdgeColorDetectionAccuracy

                def get_vert_color(vert):
                    for rtc in radiusToColor.items():
                        if abs(vert[dataLayer] - rtc[0]) <= threshold*rtc[0]:
                            return rtc[1]

                    return ZBBQ_Consts.overlayEdgeColorUndetected

                self.colors = [get_vert_color(v) for v in bm.verts]

                self.indices = [[v.index for v in edge.verts]
                                for edge in bm.edges if not edge.hide
                                and not all(v[dataLayer] == 0 for v in edge.verts)]

            self.build_batch()
        else:
            self.layer = None
            self.indices = []
            self.colors = []
            self.batch = None

    def build_batch(self):
        if len(self.indices):
            self.batch = batch_for_shader(
                self.shader, 'LINES', {"pos": self.verts, "color": self.colors},
                indices=self.indices)
        else:
            self.batch = None

    def _internal_draw(self, p_alpha):
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS_EQUAL')

        edge_active_line_width = 2
        gpu.state.line_width_set(edge_active_line_width)

        self.shader.uniform_float('viewportSize', gpu.state.viewport_get()[2:])
        self.shader.uniform_float('lineWidth', edge_active_line_width * 2)

        try:
            self.batch.draw(self.shader)

        finally:
            # restore opengl defaults
            gpu.state.blend_set('NONE')
            gpu.state.depth_test_set('NONE')
