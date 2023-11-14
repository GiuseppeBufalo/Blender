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

import numpy as np
from mathutils import Vector
from ZenUV.utils.constants import u_axis, v_axis
# from ZenUV.utils.transform import BoundingBox2d


class DistributeUtils:

    def __init__(self, stripe, limits, Props) -> None:
        self.props = Props
        self.limits = limits
        self.props.iter_counter += 1

        self.stripe = self._orient_stripe(stripe)

        self.distribution = self._get_distribution()

        self.length = sum(self.distribution)

        self.head = self.stripe._get_start()
        self.tail = self.stripe._get_end()
        self.base_vector = self.tail - self.head
        self.bbox_u = self.base_vector * v_axis
        self.bbox_v = self.base_vector * u_axis

        self.init_direction = self.stripe.orientation
        self.direction = self._get_direction_vector(self.props.orient_along)

        self.base_position = self._get_position_limits("HEAD")

        self.scale = self._get_scale()

        dynamic_base = self.base_position

        # Offset system
        if not self.props.orient_along == 'INPLACE':
            dynamic_base = self.offset_stripes(dynamic_base)

        # Vector corrections in border mode
        dynamic_base = self.borders_processing(dynamic_base)

        # Create distribution of the stripe
        self._distribute()
        self.stripe.distribution = self._calc_points_coo(dynamic_base)

        self.stripe.set_positions()

        # Store tail
        self.props.prev_tail = self.stripe.distribution[-1]
        # Store head
        self.props.prev_head = self.stripe.distribution[0]

    def borders_processing(self, dynamic_base):
        if self.props.sources == "BORDERS":
            # Store start position of overall border
            if self.props.iter_counter == 0:
                self.props.border_head = dynamic_base
                self.props.prev_tail = None
            # Set base from stored tail
            if self.props.prev_tail:
                dynamic_base = self.props.prev_tail
        return dynamic_base

    def offset_stripes(self, dynamic_base):
        vec = dynamic_base.copy()
        if not self.props.iter_counter == 0:
            solver = {u_axis[:]: self.u_offset, v_axis[:]: self.v_offset}
            vec = solver[(self.direction * self.direction)[:]](vec)
        else:
            vec = self.base_position
            self.props.sequence_head = dynamic_base
        return vec

    def u_offset(self, vec):
        vec.y = self.props.sequence_head.y + (vec.y - self.props.sequence_head.y) * self.props.offset.y
        vec.x = vec.x + (self.props.offset.x - 1) * (self.stripe.index / 8)
        return vec

    def v_offset(self, vec):
        vec.x = self.props.sequence_head.x + (vec.x - self.props.sequence_head.x) * self.props.offset.x
        vec.y = vec.y + (self.props.offset.y - 1) * (self.stripe.index / 8)
        return vec

    def _distribute(self):
        distr = np.full((len(self.distribution), 2), self.direction)
        distr *= np.array([(v, v) for v in self.distribution])
        self.distributed = (distr * self.scale).tolist()

    def _set_points_coo(self, base_position, distribution):
        for edge, co in zip(self.stripe, distribution):
            uv_co = base_position
            edge.vert.set_position(uv_co)
            base_position = uv_co + Vector(co)
        self.stripe[-1].other_vert.set_position(base_position)
        return base_position

    def _calc_points_coo(self, base_position):
        pos = []
        for co in self.distributed:
            uv_co = base_position
            pos.append(uv_co)
            base_position = uv_co + Vector(co)
        pos.append(base_position)
        return pos

    def _get_position_limits(self, side):
        orient_along = self.props.orient_along
        OLimits, VStripeHT = self.sorter_tail_head(side)
        if orient_along in {"U", "AUTO", "V"}:
            VLimDirection = self.direction * self.direction
            crop = VStripeHT * VLimDirection
            if OLimits == "ASIS":
                vec = VStripeHT
                if side == "TAIL":
                    if VLimDirection != self.init_direction:
                        if orient_along == "U":
                            vec = self.base_position - VLimDirection * self.bbox_u.magnitude
                        elif orient_along == "V":
                            vec = self.base_position - VLimDirection * self.bbox_v.magnitude
                return vec
            else:
                if side == 'HEAD':
                    lim_val = self.limits.heads.lim_by_axes(VLimDirection, OLimits)
                if side == 'TAIL':
                    lim_val = self.limits.tails.lim_by_axes(VLimDirection, OLimits)
                lim_vec = VLimDirection * lim_val
            vec = VStripeHT + (lim_vec - crop)
            return vec
        return VStripeHT

    def axis_scaler(self):
        length = 1 if self.length == 0 else self.length

        limiter = self._get_position_limits("TAIL")
        vec = limiter - self.base_position
        direction = self.direction * self.direction

        vec *= direction
        scope = (vec.magnitude, length)

        return self.scaler_inplace() if min(scope) == 0.0 else self._get_scaler(scope)

    def sorter_tail_head(self, side):
        overrided_message = "Position is overrided by Constant of Operator itself."
        if side == 'HEAD':
            if self.props.base_position is not None:
                print(f"Start {overrided_message} {self.props.base_position}")
                return self.head + (self.props.base_position - self.head)
            lim = self.props.starts_pos
            stripe_side = self.head
        elif side == 'TAIL':
            if self.props.end_position is not None:
                print(f"End {overrided_message} {self.props.end_position}")
                return self.props.end_position
            lim = self.props.ends_pos
            stripe_side = self.tail
        return lim, stripe_side

    def _get_scale(self):
        orient_along = self.props.orient_along
        if orient_along == "INPLACE":
            return self.scaler_inplace()
        elif orient_along in {"U", "V", "AUTO"}:
            return self.axis_scaler()
        elif orient_along == "ORIGINAL":
            return self.scaler_original()

    def _get_scaler(self, scope):
        if scope[0] < scope[1]:
            return min(scope) / max(scope)
        else:
            return max(scope) / min(scope)

    def scaler_inplace(self):
        length = 1 if self.length == 0 else self.length
        scope = (self.base_vector.magnitude, length)
        return self._get_scaler(scope)

    def scaler_original(self):
        length = 1 if self.length == 0 else self.length
        # Store base scale
        if self.props.iter_counter == 0:
            self.props.base_scalar = self.base_vector.magnitude

        if self.props.border_proportion == 'GEOMETRY':
            mesh_vec_len = self.stripe._get_stripe_mesh_length()
            scope = (self.props.base_scalar, mesh_vec_len)
            base_vec_length = min(scope) / max(scope)
        elif self.props.border_proportion == 'UV':
            base_vec_length = self.stripe.uv_length
        else:
            base_vec_length = self.base_vector.magnitude
        scope = (base_vec_length * self.props.border_offset, length)
        return self._get_scaler(scope)

    def _get_distribution(self):
        """ Return list with distributed spaces between points """
        spacing = self.props.spacing
        if spacing == 'UV':
            return self.stripe.uv_edges_distribution()
        elif spacing == 'GEOMETRY':
            return self.stripe.geometry_distribution()
        elif spacing == 'EVENLY':
            distr = self.stripe.uv_edges_distribution()
            count = len(distr)
            return [sum(distr) / count] * count

    def _get_direction_vector(self, _dir):
        _rev_dir = -1 if self.props.reverse_dir else 1
        if _dir == "INPLACE":
            return self.base_vector.normalized() * _rev_dir
        elif _dir == "U":
            return u_axis * _rev_dir
        elif _dir == "V":
            return v_axis * -1 * _rev_dir
        elif _dir == "AUTO":
            if abs(self.base_vector.dot(u_axis)) < abs(self.base_vector.dot(v_axis)):
                return v_axis * -1 * _rev_dir
            else:
                return u_axis * _rev_dir
        elif _dir == "ORIGINAL":
            return self.init_direction * _rev_dir

    def _orient_stripe(self, stripe):
        if self.props.sources != 'BORDERS':
            sorting = self.props.sorting
            if sorting == "BOTTOM_RIGHT":
                stripe.reverse()
        return stripe
