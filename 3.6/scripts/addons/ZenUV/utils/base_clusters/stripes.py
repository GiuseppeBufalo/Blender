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
from ZenUV.utils.transform import centroid_3d
from ZenUV.utils.constants import u_axis, v_axis


class LimManager:

    def __init__(self, points, HT) -> None:
        self.VStripeHT = HT  # {"HEAD", "TAIL"}
        self.points = np.array(points)
        self.u_distrib = self.points * u_axis
        self.v_distrib = self.points * v_axis
        self.max_u = np.max(self.u_distrib, 0)
        self.min_u = np.min(self.u_distrib, 0)
        self.max_v = np.max(self.v_distrib, 1)
        self.min_v = np.min(self.v_distrib, 1)
        self.avg_u = np.median(self.u_distrib, 0)
        self.avg_v = np.median(self.v_distrib, 1)

    def lim_by_axes(self, direction, lim):
        axis = {(0, 1): 1, (1, 0): 0}[direction[:]]
        distrib = self.points[:, axis]
        if lim == "MIN":
            if self.VStripeHT == "HEAD":
                val = np.max(distrib)
            else:
                val = np.min(distrib)
        elif lim == "MID":
            val = np.median(distrib)
        elif lim == "MAX":
            if self.VStripeHT == "HEAD":
                val = np.min(distrib)
            else:
                val = np.max(distrib)  # * direction
        return val


class StripesLimits:

    def __init__(self, stripes) -> None:
        # self.cloud = [o for s in stripes for o in [s.head_co, s.tail_co]]
        self.heads = LimManager([stripe.head_co for stripe in stripes], "HEAD")
        self.tails = LimManager([stripe.tail_co for stripe in stripes], "TAIL")


class StripesManager:

    stripes = []
    result_message = ""

    def _sort_u(self, e):
        return e.head_co.x
        # return e.base_vec.x

    def _sort_v(self, e):
        return e.head_co.y
        # return e.base_vec.y

    def sort(self, direction=None):
        if not self.stripes:
            return False
        if not direction:
            if self.stripes[0].orientation == u_axis:
                self.stripes.sort(key=self._sort_v)
                self._reindexation()
                return True
            else:
                self.stripes.sort(key=self._sort_u)
                self._reindexation()
                return True
        if direction == u_axis:
            self.stripes.sort(key=self._sort_v)
            self._reindexation()
            return True
        elif direction == v_axis:
            self.stripes.sort(key=self._sort_u)
            self._reindexation()
            return True
        return False

    def _reindexation(self):
        for i, stripe in enumerate(self.stripes):
            stripe.index = i

    def append(self, stripe):
        self.stripes.append(stripe)

    def extend(self, stripe):
        for st in stripe:
            self.stripes.append(st)

    def clear(self):
        self.stripes.clear()

    def show_stripes(self, ids=True):
        print("Stripe Pool indexes:")
        for stripe in self.stripes:
            # print(stripe)
            print(f"{stripe.index} --> {[edge.index_in_stripe for edge in stripe.stripe]}")

    def show_pool(self, ids=True):
        print("Stripe Pool:")
        print(self)
        print(self.stripes)

    def get_loops_stripes(self):
        return [stripe.get_loops_stripe() for stripe in self.stripes]

    def orient_stripes(self):
        for stripe in self.stripes:
            stripe.orient()

    def set_orientation(self):
        for stripe in self.stripes:
            stripe.orientation = stripe._get_base_orientation()
            stripe.orient()


class Stripe():

    stripe = []

    def __init__(self, stripe, uv_layer, index) -> None:
        self.uv_layer = uv_layer
        self.index = index
        self.stripe = stripe
        self.distribution = []

        self._init()

        self.orientation = self._get_real_orientation()

        # if need_orient:
        #     self.orientation = self._get_base_orientation()
        #     self.orient()

        # print("In INIT ---------------------")
        # print(f"Tail {self.tail_co} --- Head {self.head_co}")
        # print("Orientation: ", self.orientation)
        # print("#############################")

    def _init(self):
        self.head = self.stripe[0]
        self.tail = self.stripe[-1]
        self.head_co = self.head.vert.uv_co
        self.tail_co = self.tail.other_vert.uv_co

        self.base_vec = self.tail_co - self.head_co

        self.uv_cycled = self.head_co == self.tail_co
        self.mesh_cycled = self.head.vert.mesh_vert.co == self.tail.other_vert.mesh_vert.co
        self.uv_length = self._get_stripe_uv_length()
        # self.mesh_length = self._get_stripe_mesh_length()

    # def _get_orientation(self):
    #     if abs(self.base_vec.dot(u_axis)) < abs(self.base_vec.dot(v_axis)):
    #         return v_axis
    #     else:
    #         return u_axis

    def _get_base_orientation(self):
        if abs(self.base_vec.dot(u_axis)) < abs(self.base_vec.dot(v_axis)):
            return v_axis
        else:
            return u_axis

    def _get_real_orientation(self):
        bo = self._get_base_orientation()
        if bo == v_axis:
            if self.tail_co.y > self.head_co.y:
                return v_axis
            else:
                return v_axis * -1
        else:
            if self.tail_co.x > self.head_co.x:
                return u_axis
            else:
                return u_axis * -1

    def set_positions(self):
        if self.distribution:
            for i in range(len(self.stripe)):
                self.stripe[i].vert.set_position(self.distribution[i])
            self.stripe[-1].other_vert.set_position(self.distribution[-1])

    # def distribute(self, base_position, distribution):
    #     for edge, co in zip(self.stripe, distribution):
    #         uv_co = base_position
    #         edge.vert.set_position(uv_co)
    #         base_position = uv_co + Vector(co)
    #     self.stripe[-1].other_vert.set_position(base_position)
    #     return base_position

    def _get_start(self):
        return self.head_co

    def _get_end(self):
        return self.tail_co

    def geometry_distribution(self):
        return [(edge.mesh_verts[0].co - edge.mesh_verts[1].co).magnitude for edge in self.stripe]

    def _get_stripe_mesh_length(self):
        return sum([(edge.mesh_verts[0].co - edge.mesh_verts[1].co).magnitude for edge in self.stripe])

    def uv_edges_distribution(self):
        return [(edge.vert.uv_co - edge.other_vert.uv_co).magnitude for edge in self.stripe]

    def _get_stripe_uv_length(self):
        return sum([(edge.vert.uv_co - edge.other_vert.uv_co).magnitude for edge in self.stripe])

    def get_loops_stripe(self):
        data = [edge.vert.link_loops for edge in self.stripe]
        data.append(self.tail.other_vert.link_loops)
        return data

    def update(self):
        self._init()

    def _get_head_co(self):
        self.head_co = self.stripe[0].vert.uv_co
        return self.head_co

    def _get_tail_co(self):
        index = -1
        if self.is_cycled()["MESH"]:
            index = -2
        self.tail_co = self.stripe[index].other_vert.uv_co
        return self.tail_co

    def orient_worked(self):
        if self.tail_co.x < self.head_co.x:
            if self.tail_co.y > self.head_co.y:
                self.reverse()
        elif self.tail_co.x == self.head_co.x:
            if self.tail_co.y > self.head_co.y:
                self.reverse()
        self.update()

    def orient(self):
        if self.orientation == v_axis:
            if self.tail_co.y > self.head_co.y:
                self.reverse()
        else:
            if self.tail_co.x < self.head_co.x:
                self.reverse()
        self.update()

    def get_reversed(self):
        return [loop for loop in reversed(self.stripe)]

    def reverse(self):
        for edge in self.stripe:
            edge.reverse()
        self.stripe.reverse()
        self.update()

    def is_cycled(self):
        return {"MESH": self.mesh_cycled, "UV": self.uv_cycled}


class UvStripes:

    def __init__(self, uv_edges, uv_layer) -> None:
        self.uv_layer = uv_layer
        self.uv_edges = uv_edges
        self.stripes = []
        self.for_obj = False

    def is_cluster_holey(self):
        self._uv_edges_from_co()
        return len(self.stripes) > 1

    def get_stripes_from_selection(self):
        if not self.stripes:
            self._uv_edges_from_co()

        pool = StripesManager()
        pool.clear()

        for index, st in enumerate(self.stripes):
            for idx, edge in enumerate(st):
                edge.index_in_stripe = idx
            pool.append(Stripe(st, self.uv_layer, index))

        # for st in pool.stripes:
        #     print(st.index)

        pool.set_orientation()
        pool.sort(direction=None)

        return pool

    def get_stripes_from_borders(self, split_mode='CORNER'):
        pool = StripesManager()
        pool.clear()
        if not self.stripes:
            self._uv_edges_from_co()

        for stripe in self.stripes:
            message, stripe_block = self.split_stripes_by_points(stripe, split_mode)
            pool.result_message = message
            # print("Stripe Block", len(stripe_block))
            # self.set_clockwise_border_direction()
            if not stripe_block:
                return pool

            for index, st in enumerate(stripe_block):
                for idx, edge in enumerate(st):
                    edge.index_in_stripe = idx
                pool.append(Stripe(st, self.uv_layer, index))
                # pool.extend(Stripe(st, self.uv_layer, index))

        return pool

    def return_break(self, stripe, message):
        cycled = stripe[0].vert.uv_co == stripe[-1].other_vert.uv_co
        print("Cycled: ", cycled)
        if cycled:
            return message, []
        else:
            return "", stripe

    def split_stripes_by_points(self, stripe, mode):

        corners = []
        if mode == 'CORNER':
            self.update_corners()
            corners = [edge.index for edge in stripe if edge.other_vert.corner]
            if not corners:
                message = "No Corner vertices were found."
                return self.return_break(stripe, message)

        elif mode == 'PINS':
            self.update_pinned()
            corners = [edge.index for edge in stripe if edge.other_vert.pinned]
            if not corners:
                message = "No Pinned vertices were found."
                return self.return_break(stripe, message)

        elif mode == 'CORNER_AND_PINS':
            self.update_corners_and_pinned()
            corners = [edge.index for edge in stripe if edge.other_vert.pinned or edge.other_vert.corner]
            if not corners:
                message = "No Corner or Pinned vertices were found."
                return self.return_break(stripe, message)

        else:
            print("mode must be in {'CORNER','PINS','CORNER_AND_PINS'}")

        # self.show_stripe(stripe)
        if not corners and stripe[0].vert.uv_co == stripe[-1].other_vert.uv_co:
            return "No Corners were found.", []

        stripe = self._refit_stripe(stripe)

        splitted = []
        n_stripe = []
        for edge in stripe:
            n_stripe.append(edge)
            if edge.index in corners:
                splitted.append(n_stripe)
                n_stripe = []

        return "Finished", splitted

    def sort_border_stripes(self):
        pass

    def set_clockwise_border_direction(self):
        for stripe in self.stripes:
            stripe.reverse()

    def get_holes(self):
        if not self.stripes:
            self._uv_edges_from_co()
        lengths = []
        for stripe in self.stripes:
            _l = [edge.get_len() for edge in stripe]
            lengths.append(sum(_l))
        clean = self.stripes.copy()
        clean.pop(lengths.index(max(lengths)))
        return clean

    def get_injectors(self, current_index):
        self.current_index = current_index
        injectors = []
        for hole in self.get_holes():
            verts_co = []
            verts_count = 0
            indexes = []
            for edge in hole:
                for vert in edge.mesh_verts:
                    verts_co.append(vert.co)
                    verts_count += 1
                indexes.append([edge.vert.index, edge.other_vert.index])
            injectors.append(self._compound_injector(verts_co, verts_count, indexes))

        return injectors

    def _compound_injector(self, verts_co, verts_count, indexes):
        offset = 0
        if self.for_obj:
            offset = 1
        cen = centroid_3d(verts_co)
        cap = []
        for edge in indexes:
            cap.append([self.current_index + offset, edge[0] + offset, edge[1] + offset])
        self.current_index += 1
        return cen, cap

    def _uv_edges_from_co(self):

        def _sort_edges(e):
            return (e.verts_co[0] + e.verts_co[1]).magnitude

        unsorted_edges = [e for e in self.uv_edges]
        unsorted_edges.sort(key=_sort_edges)
        stripes = []
        while unsorted_edges:
            current_edge = unsorted_edges.pop()

            if current_edge.get_direction() == "CCV":
                current_edge.reverse()

            vert_start, vert_end = current_edge.vert.uv_co, current_edge.other_vert.uv_co
            stripe = [current_edge]

            ok = True
            while ok:
                ok = False
                i = len(unsorted_edges)
                while i:
                    i -= 1
                    edge = unsorted_edges[i]
                    e_start, e_end = edge.vert.uv_co, edge.other_vert.uv_co
                    if e_start == vert_end:
                        stripe.append(edge)
                        vert_end = stripe[-1].other_vert.uv_co
                        ok = 1
                        del unsorted_edges[i]
                    elif e_end == vert_end:
                        edge.reverse()
                        stripe.append(edge)
                        vert_end = stripe[-1].other_vert.uv_co
                        ok = 1
                        del unsorted_edges[i]
                    elif e_end == vert_start:
                        stripe.insert(0, edge)
                        vert_start = stripe[0].vert.uv_co
                        ok = 1
                        del unsorted_edges[i]
                    elif e_start == vert_start:
                        edge.reverse()
                        stripe.insert(0, edge)
                        vert_start = stripe[0].vert.uv_co
                        ok = 1
                        del unsorted_edges[i]

            stripes.append(stripe)
        self.stripes = stripes

    def update_corners(self):
        for v in [v for e in self.uv_edges for v in e.verts]:
            v.update_corner()

    def update_pinned(self):
        for v in [v for e in self.uv_edges for v in e.verts]:
            v.update_pinned()

    def update_corners_and_pinned(self):
        for v in [v for e in self.uv_edges for v in e.verts]:
            v.update_pinned()
            v.update_corner()

    def _refit_stripe(self, stripe):
        if not stripe:
            return list()
        # stripe = self.stripes[0].copy()
        if stripe[0].vert.corner or stripe[0].vert.pinned or len(stripe) == 1:
            return stripe
        # self.show_stripe(stripe)
        # print("Stripe in POP: ", stripe)
        head = []
        ok = True
        f = len(stripe)
        i = 0
        while ok or i == f:
            edge = stripe.pop(0)
            head.append(edge)
            if edge.other_vert.corner or edge.other_vert.pinned:
                ok = False
            i += 1
        # self.show_stripe(head)
        # self.show_stripe(stripe)
        stripe.extend(head)
        # self.show_stripe(stripe)
        return stripe

    def show_stripe(self, stripe):
        print("Stripe condition:")
        arr = ""
        for edge in stripe:
            if edge.vert.corner:
                arr += f"{edge.vert.index}<"
            elif edge.other_vert.corner:
                arr += f">{edge.other_vert.index}."
            else:
                arr += "_"
        print(arr + "\n")
