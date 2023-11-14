bl_info = {
    "name": "Smart Fill",
    "category": "Mesh",
    "author": "roaoao",
    "version": (1, 4, 0),
    "blender": (2, 80, 0),
}

import bpy
import bmesh
import traceback
import numpy as np
from itertools import chain
from bpy.props import (
    BoolProperty,
    IntProperty,
    StringProperty,
)
from mesh_looptools import (
    get_connected_input,
    get_connected_selections,
    edgekey,
    dict_face_faces,
)
from rna_keymap_ui import draw_kmi

MOUSEWHEEL_KMIS = []
prev_sel_verts = None

PI = np.pi
PI05 = np.pi * 0.5

GR = "gr_"
BR = "br_"
SKIP_SAVE_PROPS = {'number_cuts', 'span', 'offset', 'twist_offset'}


# from CGCookie's blender-addon-updater with minor changes
def make_annotations(cls):
    """Converts class fields to annotations if running with Blender 2.80+"""
    if bpy.app.version < (2, 80):
        return cls
    if bpy.app.version < (2, 93, 0):
        bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    else:
        bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, bpy.props._PropertyDeferred)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


def prefs():
    if hasattr(bpy.context, "user_preferences"):  # 2.7x
        return bpy.context.user_preferences.addons[__name__].preferences
    elif hasattr(bpy.context, "preferences"):
        return bpy.context.preferences.addons[__name__].preferences


def get_bm(verts=False, edges=False, faces=False):
    bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    if verts:
        bm.verts.index_update()
    if edges:
        bm.edges.index_update()
    if faces:
        bm.faces.index_update()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm


def get_sel_verts(bm, update=False):
    if update:
        bm.verts.index_update()

    return [v.index for v in bm.verts if v.select and not v.hide]


def save_faces(bm, data=None):
    if not data:
        data = set()

    for f in bm.faces:
        if f.select and not f.hide:
            data.add(f.index)
    return data


def restore_faces(bm, data):
    for f in bm.faces:
        if f.index in data:
            f.select = True


def get_idname_from_operator(operator):
    if not operator:
        return None

    if hasattr(bpy.context.active_operator.bl_rna, "bl_idname"):
        return bpy.context.active_operator.bl_rna.bl_idname

    return bpy.context.active_operator.bl_idname.lower().replace("_ot_", ".")


def get_operator_from_idname(idname):
    mod_name, name = idname.split(".")
    mod = getattr(bpy.ops, mod_name)
    return getattr(mod, name)


def get_default_f_kmi():
    kms = bpy.context.window_manager.keyconfigs.user.keymaps
    kmis = kms["Mesh"].keymap_items if "Mesh" in kms else ()
    for kmi in kmis:
        if kmi.active and kmi.type == 'F' and \
                kmi.idname != "mesh.smart_fill" and \
                not kmi.ctrl and not kmi.shift and \
                not kmi.alt and not kmi.oskey and \
                kmi.key_modifier == 'NONE':
            return kmi
    return None


def run_default_f_operator(kmi=None, undo=True):
    if hasattr(bpy.types, "MESH_OT_f2"):
        bpy.ops.mesh.f2('INVOKE_DEFAULT')
    else:
        bpy.ops.mesh.edge_face_add('INVOKE_DEFAULT')

    return
    """
    # todo : figure out what this code (that will never-execute) was for...
    if not kmi:
        kmi = get_default_f_kmi()
    if kmi:
        operator = get_operator_from_idname(kmi.idname)
        try:
            operator('INVOKE_DEFAULT', undo, **kmi.properties)
        except:
            pass
    """


def _update_mouse_wheel(self, context):
    pr = prefs()
    for kmi in MOUSEWHEEL_KMIS:
        kmi.active = pr.mouse_wheel


def get_islands(bm):

    def walk_faces(faces, face, sel_faces, used_faces, island):
        for f in faces[face]:
            if f in sel_faces and f not in used_faces:
                used_faces.add(f)
                island.append(f)
                walk_faces(faces, f, sel_faces, used_faces, island)

    faces = dict_face_faces(bm)
    sel_faces = {f.index for f in bm.faces if f.select}
    used_faces = set()
    islands = []

    while sel_faces:
        f = sel_faces.pop()
        if f in used_faces:
            continue
        island = []
        islands.append(island)
        island.append(f)
        walk_faces(faces, f, sel_faces, used_faces, island)

    return islands


def angle_between(v1, v2):
    v1_u = v1 / np.linalg.norm(v1)
    v2_u = v2 / np.linalg.norm(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


class Vert:
    def __init__(self, index, co):
        self.index = index
        self.co = co
        self.is_corner = False
        self.prev = None
        self.prev_corner = None
        self.next = None
        self.ori = False
        self.edge_index = 0

    @property
    def angle(self):
        v1 = np.subtract(self.prev.co, self.co)
        v2 = np.subtract(self.next.co, self.co)
        return angle_between(v1, v2)

    @property
    def cross(self):
        if not self.prev:
            return None

        v1 = np.subtract(self.co, self.prev.co)
        v2 = np.subtract(self.next.co, self.co)
        return np.cross(v1, v2)

    @property
    def vector(self):
        return np.subtract(self.next.co, self.co)

    def vector_to(self, vert):
        return np.subtract(vert.co, self.co)


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    f1_kmi = None
    f2_kmi = None

    props_dialog = BoolProperty(
        name="Show Properties Dialog",
        description="Show properties dialog in 3D View")
    mouse_wheel = BoolProperty(
        name="Use Ctrl/Shift+MouseWheel to adjust properties",
        description="Use Ctrl/Shift+MouseWheel to adjust properties",
        update=_update_mouse_wheel)
    reset_values = BoolProperty(
        name="Reset Values",
        description="Reset values on next use of make edge / face")

    def draw(self, context):
        pr = prefs()
        layout = self.layout
        layout.prop(pr, "props_dialog")
        layout.prop(pr, "mouse_wheel")
        layout.prop(pr, "reset_values")

        f1_kmi = False
        f2_kmi = False
        f3_kmi = False
        f3_kmi_ls = []
        kc = context.window_manager.keyconfigs.user
        kms = kc.keymaps
        kmis = kms["Mesh"].keymap_items if "Mesh" in kms else ()
        for kmi in kmis:
            if f1_kmi and f2_kmi and f3_kmi:
                break
            if kmi.idname == "mesh.edge_face_add":
                f1_kmi = kmi
            if kmi.idname == "mesh.f2":
                f2_kmi = kmi
            if kmi.idname == "mesh.smart_fill_repeat":
                if not f3_kmi:
                    f3_kmi = True
                f3_kmi_ls.append(kmi)

        if f1_kmi or f2_kmi:
            layout.label(text="Default Hotkeys:")
        if f1_kmi:
            box = layout.box()
            box.label(text="Add Edge / Face")
            draw_kmi(kms, kc, kms["Mesh"], f1_kmi, box, 0)
        if f2_kmi:
            box = layout.box()
            box.label(text="Mesh F2")
            draw_kmi(kms, kc, kms["Mesh"], f2_kmi, box, 0)
        if f3_kmi and self.mouse_wheel:
            layout.label(text="Hotkeys to adjust properties:")
            for k in f3_kmi_ls:
                if 'hkey_desc' in k.properties:
                    box = layout.box()
                    box.label(text=k.properties['hkey_desc'])
                    draw_kmi(kms, kc, kms["Mesh"], k, box, 0)
   

def init_verts(bm, loop, circular):
    prev_vert = None
    first_vert = None
    for vi in loop:
        v = bm.verts[vi]
        vert = Vert(vi, v.co)
        vert.prev = prev_vert
        if prev_vert:
            prev_vert.next = vert
        if not first_vert:
            first_vert = vert
        prev_vert = vert

    if circular:
        first_vert.prev = vert
        vert.next = first_vert

    return first_vert


def update_edges(first_vert, circular):
    prev_corner = None
    ori_f, ori_t = 0, 0
    num_corners = 0
    min_edge_len_f = -1
    min_edge_len_t = -1
    max_edge_len = -1
    first_vert.edge_index = -1
    last_vert = first_vert if circular else None
    vert = first_vert
    used_verts = set()
    while True:
        vert.prev_corner = prev_corner

        if vert.prev:
            vert.ori = vert.prev.ori
            vert.edge_index = 0 if vert.prev.is_corner else \
                vert.prev.edge_index + 1

        if vert.prev and vert.next:
            vert.is_corner = vert.angle < 0.7 * PI
            if vert.is_corner and prev_corner and \
                    angle_between(prev_corner.cross, vert.cross) >= PI05:
                vert.ori = not vert.ori

            if vert.is_corner:
                num_corners += 1

                if circular and not first_vert.is_corner:
                    first_vert = vert
                    last_vert = vert
                    vert.edge_index = -1
                    ori_f, ori_t = 0, 0
                    num_corners = 0
                    min_edge_len_f = -1
                    min_edge_len_t = -1
                    max_edge_len = -1
                    continue

            if vert.is_corner and prev_corner and vert.ori == prev_corner.ori:
                edge_len = vert.edge_index + 1
                if vert.ori:
                    if min_edge_len_t < 0 or min_edge_len_t > edge_len:
                        min_edge_len_t = edge_len
                else:
                    if min_edge_len_f < 0 or min_edge_len_f > edge_len:
                        min_edge_len_f = edge_len
                if max_edge_len < edge_len:
                    max_edge_len = edge_len

            if vert.is_corner:
                if vert.ori:
                    ori_t += 1
                else:
                    ori_f += 1

        if vert.is_corner:
            prev_corner = vert
        vert = vert.next

        if vert == last_vert or vert.index in used_verts:
            break

        used_verts.add(vert.index)

    if circular:
        first_vert.edge_index = 0 if first_vert.prev.is_corner else \
            first_vert.prev.edge_index + 1

    return (
        first_vert,
        ori_t >= ori_f,
        min_edge_len_t if ori_t >= ori_f else min_edge_len_f,
        max_edge_len,
        num_corners,
        ori_t == 0 or ori_f == 0
    )


def get_vert_to_fill(bm, first_vert, circular):
    first_vert, ori, min_edge_len, max_edge_len, num_corners, same_ori = \
        update_edges(first_vert, circular)

    if circular and same_ori and (min_edge_len > 1 or max_edge_len <= 1):
        return None, first_vert, min_edge_len, max_edge_len

    vert = first_vert
    last_vert = None if circular else first_vert
    used_verts = set()
    while vert:
        if vert.is_corner and vert.prev_corner and \
                vert.edge_index == min_edge_len - 1 and \
                vert.ori == ori and \
                angle_between(vert.prev_corner.cross, vert.cross) < PI05:
            return vert, first_vert, min_edge_len, max_edge_len
        vert = vert.next
        if vert:
            if vert == last_vert or vert and vert.index in used_verts:
                break
            used_verts.add(vert.index)

    return None, first_vert, min_edge_len, max_edge_len


def fill_vert(bm, vert, face_example, first_vert):
    vert_example = bm.verts[vert.index]
    A = vert
    B = vert.prev_corner
    C = vert.next
    D = vert.prev_corner.prev
    a, b, c, d = vert.prev, vert, vert.next, vert.prev_corner.prev
    len_old = (A.co - B.co).length
    len_new = (C.co - D.co).length
    scale = len_new / len_old
    for i in range(0, vert.edge_index + 1):
        if i < vert.edge_index:
            # k = (i + 1) / (vert.edge_index + 1)
            ac_mid = (a.co + c.co) / 2
            co = 2 * (ac_mid - b.co) + b.co
            co = scale * (co - c.co) + c.co
            v = bm.verts.new(co.to_tuple(), vert_example)
            v.index = len(bm.verts) - 1
            bm.verts.ensure_lookup_table()
            d = Vert(v.index, co)

        flip_normal = False
        mat_index = -1
        smooth = False
        if bm.verts[b.index].link_faces:
            va = bm.verts[a.index]
            vb = bm.verts[b.index]
            vc = bm.verts[c.index]
            link_face = None
            for f in vb.link_faces:
                vis = {v.index for v in f.verts}
                if va.index in vis or vc.index in vis:
                    link_face = f
                    break
            if link_face:
                fa, fc = None, None
                for i, v in enumerate(link_face.verts):
                    if v == vb:
                        fa = link_face.verts[i - 1]
                        fc = link_face.verts[(i + 1) % len(link_face.verts)]
                        break
                if va == fa or vc == fc:
                    flip_normal = True
            else:
                f.normal_update()
                if angle_between(f.normal, face_example.normal) >= PI05:
                    f.normal_flip()

            mat_index = f.material_index
            smooth = f.smooth

        try:
            verts = [
                bm.verts[a.index],
                bm.verts[b.index],
                bm.verts[c.index],
                bm.verts[d.index],
            ]
            if flip_normal:
                verts.reverse()
            f = bm.faces.new(verts)
            f.select = True
            f.index = len(bm.faces) - 1
            if mat_index >= 0:
                f.material_index = mat_index
            f.smooth = smooth
        except:
            pass

        if a == first_vert:
            first_vert = d
        elif b == first_vert:
            first_vert = c

        c.prev = d
        d.next = c

        a = a.prev
        b = b.prev
        c = d
        d = vert.prev_corner.prev

    return first_vert


def plaster_fill(bm, loop, circular):
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    face = bm.faces[0] if len(bm.faces) else None

    first_vert = init_verts(bm, loop, circular)

    updated = False
    while True:
        vert_to_fill, first_vert, min_edge_len, max_edge_len =\
            get_vert_to_fill(bm, first_vert, circular)
        if not vert_to_fill:
            break

        updated = True
        first_vert = fill_vert(bm, vert_to_fill, face, first_vert)

    if updated:
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        loop = []
        vert = first_vert
        last_vert = first_vert if circular else None
        while True:
            loop.append(vert.index)
            vert = vert.next
            if vert == last_vert:
                break

    return loop, min_edge_len, max_edge_len


class MESH_OT_smart_fill(bpy.types.Operator):
    bl_idname = "mesh.smart_fill"
    bl_label = "Smart Fill"
    bl_description = "Smart fill"
    bl_options = {'REGISTER', 'UNDO'}

    no_props = False

    prev_sel_verts = None
    mode = None
    submode = 0

    reset = BoolProperty(default=True)
    number_cuts = bpy.props.IntProperty()
    twist_offset = bpy.props.IntProperty()

    @classmethod
    def save_state(cls):
        bm = get_bm()
        cls.prev_sel_verts = get_sel_verts(bm, True)

    @classmethod
    def check_state(cls, sel_verts):
        if not bpy.context.active_operator or not cls.mode:
            return False
        return cls.prev_sel_verts == sel_verts

    def next_mode(self, context):
        cls = self.__class__
        mode, submode = cls.mode, cls.submode
        if mode:
            submode += 1

        bm = get_bm(True, True, True)
        sel_verts = get_sel_verts(bm)

        if self.check_state(sel_verts):
            return mode, submode

        sel_mode = context.tool_settings.mesh_select_mode

        # Face Mode
        if sel_mode[2]:
            sel_faces = [f for f in bm.faces if f.select and not f.hide]
            if len(sel_faces) == 1:
                return 'GF', 0

            islands = get_islands(bm)
            num_islands = len(islands)

            if num_islands == 1:
                return 'GF', 0

            if num_islands == 2:
                return 'BGF', 0

            if num_islands > 2:
                return 'GF', 0

        # Edge Mode
        elif sel_mode[1]:
            # 1 edge - F2
            sel_edges = [e for e in bm.edges if e.select and not e.hide]
            if len(sel_edges) <= 1:
                return 'F', 0

            edge_keys = [edgekey(e) for e in sel_edges]
            loops = get_connected_selections(edge_keys)
            num_loops = len(loops)

            if num_loops == 1:
                return 'GF', 0

            elif num_loops == 2:
                return 'BGF', 0

            elif num_loops > 2:
                return 'GF', 0

            pass

        # Vertex Mode
        else:
            if len(sel_verts) < 3:
                return 'F', 0

            sel_edges = [e for e in bm.edges if e.select and not e.hide]
            edge_keys = [edgekey(e) for e in sel_edges]
            loops = get_connected_selections(edge_keys)
            num_loops = len(loops)

            num_loop_verts = 0
            for loop, _ in loops:
                for _ in loop:
                    num_loop_verts += 1
            if num_loop_verts != len(sel_verts):
                return 'B', 0

            if num_loops == 1:
                return 'GF', 0

            elif num_loops == 2:
                return 'BGF', 0

            elif num_loops > 2:
                return 'GF', 0

        return 'B', 0

    def gen_args(self, pre=None):
        args = {}
        cls_data = None
        if hasattr(self.__class__, "__annotations__"):  # 2.8x
            cls_data = self.__class__.__annotations__
        else:  # 2.7x
            cls_data = self.__class__.order
        for k in cls_data:
            if pre:
                if k.startswith(pre):
                    args[k[3:]] = getattr(self, k)
            else:
                if k.startswith(BR) or k.startswith(GR):
                    args[k] = getattr(self, k)
        return args

    def try_bridge(self, aop):
        pr = prefs()
        aop_idname = get_idname_from_operator(aop)
        values = self.gen_args(BR)
        if pr.reset_values and self.reset:
            props = None
            if hasattr(bpy.types, "MESH_OT_bridge_edge_loops"):  # 2.7x
                props = bpy.types.MESH_OT_bridge_edge_loops.bl_rna.properties
            elif hasattr(bpy.ops.mesh.bridge_edge_loops, "get_rna_type"):
                tp = bpy.ops.mesh.bridge_edge_loops.get_rna_type()
                props = tp.properties
            for k, p in props.items():
                if hasattr(p, "default"):
                    values[k] = p.default

        else:
            if aop and aop_idname == "mesh.bridge_edge_loops":
                bl_props = None
                if hasattr(bpy.types, "MESH_OT_bridge_edge_loops"):  # 2.7x
                    tp = bpy.types.MESH_OT_bridge_edge_loops
                    bl_props = tp.bl_rna.properties
                elif hasattr(bpy.ops.mesh.bridge_edge_loops, "get_rna_type"):
                    tp = bpy.ops.mesh.bridge_edge_loops.get_rna_type()
                    bl_props = tp.properties
                for k, v in aop.properties.items():
                    p = bl_props[k]
                    if p.type == 'ENUM':
                        values[k] = p.enum_items[v].identifier
                    else:
                        values[k] = v

        bpy.ops.mesh.bridge_edge_loops(**values)
        bpy.ops.mesh.beautify_fill()
        bpy.ops.mesh.tris_convert_to_quads()

    def try_grid(self, delete_faces=False):
        self.bm = getattr(self, "bm", None)
        if not self.bm or not self.bm.is_valid:
            self.bm = get_bm(True, True, True)
        bm = self.bm

        sel_edges = [e for e in bm.edges if e.select]
        def select_loop(loop, circular):
            prev_v = None
            bm.verts.ensure_lookup_table()
            it = chain(loop, [loop[0]]) if circular else loop
            for vi in it:
                v = bm.verts[vi]
                if prev_v:
                    for e in v.link_edges:
                        for ev in e.verts:
                            if ev == prev_v:
                                e.select = True
                prev_v = v

        if delete_faces:
            try:
                bpy.ops.mesh.dissolve_faces()
            except:
                return
            bpy.ops.mesh.delete(type='ONLY_FACE')
            sel_edges = [e for e in sel_edges if e.is_valid]
            for e in sel_edges:
                e.select = True

        # save_selection(bm, clear=True)
        edge_keys = [edgekey(e) for e in sel_edges]
        loops = get_connected_selections(edge_keys)

        new_loops = []
        spans = []
        for loop, circular in loops:
            num_verts = len(loop)
            if num_verts > 3:
                loop, min_edge_len, max_edge_len = \
                    plaster_fill(bm, loop, circular)
                spans.append(max_edge_len)
            else:
                spans.append(0)

            new_loops.append((loop, circular))
        loops = new_loops

        sel_faces = save_faces(bm)

        self.show_grid_props = False
        for i, (loop, circular) in enumerate(loops):
            num_verts = len(loop)
            if num_verts <= 3:
                continue

            bpy.ops.mesh.select_all(action='DESELECT')
            bm = bm if bm.is_valid else get_bm()
            select_loop(loop, circular)

            try:
                args = self.gen_args(GR)
                if self.auto_grid:
                    if spans[i] != -1:
                        args["span"] = self.gr_span = spans[i]
                    else:
                        args.pop("span", None)
                    args["offset"] = self.gr_offset = 0
                elif spans[i]:
                    args["span"] = self.gr_span
                    args["offset"] = self.gr_offset
                bpy.ops.mesh.fill_grid('INVOKE_DEFAULT', **args)
                self.show_grid_props = True
            except:
                MESH_OT_smart_fill.no_props = True
                v1, v2 = None, None
                use_fill = False
                bm = bm if bm.is_valid else get_bm()
                for vi in loop:
                    v = bm.verts[vi]
                    if not v1:
                        v1 = v
                    elif not v2:
                        v2 = v
                    else:
                        if angle_between(
                                np.subtract(v1.co, v2.co),
                                np.subtract(v.co, v2.co)) < PI * 0.99:
                            use_fill = True
                            break
                if use_fill:
                    bpy.ops.mesh.edge_face_add()

            bm = bm if bm.is_valid else get_bm()
            save_faces(bm, sel_faces)

        restore_faces(bm, sel_faces)

    @classmethod
    def poll(self, context):
        return context.edit_object

    def draw(self, context):
        cls = self.__class__
        layout = self.layout

        pre = None
        if self.submode_name == "B":
            pre = BR
        elif self.submode_name == "G" and self.show_grid_props:
            pre = GR

        if not pre:
            return

        if hasattr(cls, "__annotations__"):  # 2.8x
            # checking here to avoid more conditionals inside draw for loop
            if bpy.app.version < (2, 93):
                for k in cls.__annotations__:
                    if k.startswith(pre):
                        func, data = cls.__annotations__[k]
                        if func is bpy.props.BoolProperty:
                            layout.prop(self, k)
                        else:
                            col = layout.column(align=True)
                            col.label(text=data["name"])
                            col.prop(self, k, text="")
            else:      
                for k in cls.__annotations__:
                    if k.startswith(pre):
                        data = cls.__annotations__[k]
                        if data.function is bpy.props.BoolProperty:
                            layout.prop(self, k)
                        else:
                            col = layout.column(align=True)
                            col.label(text=data.keywords["name"])
                            col.prop(self, k, text="")
        else:  # 2.7x
            for k in cls.order:
                if k.startswith(pre):
                    func, data = getattr(cls, k)
                    if func is bpy.props.BoolProperty:
                        layout.prop(self, k)
                    else:
                        col = layout.column(align=True)
                        col.label(text=data["name"])
                        col.prop(self, k, text="")

    def execute(self, context):
        self.bm = get_bm(True, True, True)
        self.auto_grid = getattr(self, "auto_grid", False)
        MESH_OT_smart_fill.no_props = False

        if self.mode == 'F':
            run_default_f_operator(self.fkmi)
            return {'CANCELLED'}

        elif self.mode == 'B':
            bpy.ops.mesh.edge_face_add()
            return {'CANCELLED'}

        elif self.mode == 'GF':
            self.show_grid_props = True
            self.submode %= 2
            if self.submode == 0:
                self.try_grid(True)
            elif self.submode == 1:
                run_default_f_operator()
            self.auto_grid = False

        elif self.mode == 'BGF':
            submode = self.submode % 3
            if submode == 0:
                self.try_bridge(context.active_operator)
            elif submode == 1:
                self.try_grid(True)
            elif submode == 2:
                run_default_f_operator()

        self.save_state()
        return {'FINISHED'}

    def invoke(self, context, event):
        cls = self.__class__

        self.auto_grid = True
        self.fkmi = get_default_f_kmi()

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        cls.mode, cls.submode = self.next_mode(context)
        cls.submode_name = cls.mode[cls.submode % len(cls.mode)]
        if cls.submode > 0:
            bpy.ops.ed.undo()

        ret = self.execute(context)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        return ret


class MESH_OT_smart_fill_popup(bpy.types.Operator):
    bl_idname = "mesh.smart_fill_popup"
    bl_label = "Smart Fill Popup"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        bpy.ops.mesh.smart_fill('INVOKE_DEFAULT', True, reset=True)
        ao = context.active_operator
        if not ao or ao.bl_idname != MESH_OT_smart_fill.__name__ or \
                MESH_OT_smart_fill.no_props:
            return {'CANCELLED'}
        if prefs().props_dialog:
            bpy.ops.screen.redo_last('INVOKE_DEFAULT')
        return {'CANCELLED'}


def gen_default_args(prop):
    args = dict(
        name=prop.name,
        description=prop.description,
        default=prop.default,
    )
    if hasattr(prop, "hard_min"):
        args["min"] = prop.hard_min
    if hasattr(prop, "hard_max"):
        args["max"] = prop.hard_max
    if hasattr(prop, "soft_min"):
        args["soft_min"] = prop.soft_min
    if hasattr(prop, "soft_max"):
        args["soft_max"] = prop.soft_max

    options = set()
    if prop.is_skip_save and prop.identifier not in SKIP_SAVE_PROPS:
        options.add('SKIP_SAVE')
    args["options"] = options

    return args


def fill_properties(cls, pre):
    cls_props = None
    if hasattr(cls, "bl_rna"):  # 2.7x
        cls_props = cls.bl_rna.properties.items()
    elif hasattr(cls, "get_rna_type"):  # 2.80+
        cls_bl_rna = cls.get_rna_type()
        cls_props = cls_bl_rna.properties.items()
        if '__annotations__' not in MESH_OT_smart_fill.__dict__:
            setattr(MESH_OT_smart_fill, '__annotations__', {})
    for k, v in cls_props:
        if v.type == 'POINTER':
            continue
        args = gen_default_args(v)

        if v.identifier == "span":
            args["min"] = 0
            args["soft_min"] = 0
        elif v.identifier == "interpolation":
            args["default"] = 'LINEAR'

        if v.type == 'INT':
            prop = bpy.props.IntProperty(**args)
        elif v.type == 'FLOAT':
            prop = bpy.props.FloatProperty(**args)
        elif v.type == 'BOOLEAN':
            prop = bpy.props.BoolProperty(**args)
        elif v.type == 'ENUM':
            items = []
            for item in v.enum_items:
                items.append((item.identifier, item.name, item.description))
            args["items"] = items
            prop = bpy.props.EnumProperty(**args)
        else:
            continue
        if hasattr(MESH_OT_smart_fill, "order"):  # 2.7x
            setattr(MESH_OT_smart_fill, pre + k, prop)
            MESH_OT_smart_fill.order.append(pre + k)
        else:  # 2.80+
            MESH_OT_smart_fill.__dict__['__annotations__'][pre + k] = prop


class MESH_OT_smart_fill_repeat(bpy.types.Operator):
    bl_idname = "mesh.smart_fill_repeat"
    bl_label = "Smart Fill (Repeat)"

    delta = IntProperty(options={'SKIP_SAVE'})
    mode = StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def poll(self, context):
        if not prefs().mouse_wheel:
            return False

        if not context.edit_object or not context.active_operator:
            return False

        idname = get_idname_from_operator(context.active_operator)
        return idname == MESH_OT_smart_fill.bl_idname

    def execute(self, context):
        aop = context.active_operator
        args = aop.gen_args()
        if aop.submode_name == "B":
            if self.mode == 'TWIST':
                args["br_twist_offset"] += self.delta
            elif self.mode == 'NUM_CUTS':
                args["br_number_cuts"] = \
                    max(args["br_number_cuts"] + self.delta, 0)

        elif aop.submode_name == "G":
            if self.mode == 'TWIST':
                args["gr_offset"] += self.delta
            elif self.mode == 'NUM_CUTS':
                args["gr_span"] = max(args["gr_span"] + self.delta, 0)
        else:
            return {'CANCELLED'}

        args["reset"] = False

        if bpy.app.version < (2, 80):  # 2.7x
            bpy.ops.ed.undo()
        bpy.ops.mesh.smart_fill(True, **args)

        return {'CANCELLED'}


class KMH():
    items = {}
    km = None

    @staticmethod
    def keymap(name="Window", space_type_='EMPTY', region_type_='WINDOW'):
        KMH.km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            name, space_type=space_type_, region_type=region_type_)

    @staticmethod
    def operator(
            bl_class,
            key, ctrl=False, shift=False, alt=False, oskey=False,
            key_mod='NONE', **props):
        item = KMH.km.keymap_items.new(
            bl_class.bl_idname, key, 'PRESS',
            ctrl=ctrl, shift=shift, alt=alt, oskey=oskey, key_modifier=key_mod)

        if props:
            for p in props.keys():
                setattr(item.properties, p, props[p])

        if KMH.km.name not in KMH.items:
            KMH.items[KMH.km.name] = []
        KMH.items[KMH.km.name].append(item)

        return item

    @staticmethod
    def unregister():
        keymaps = bpy.context.window_manager.keyconfigs.addon.keymaps
        for k, i in KMH.items.items():
            if k in keymaps:
                for item in i:
                    try:
                        keymaps[k].keymap_items.remove(item)
                    except:
                        continue


classes = (
    AddonPreferences,
    MESH_OT_smart_fill,
    MESH_OT_smart_fill_popup,
    MESH_OT_smart_fill_repeat,
)


def register():
    if bpy.app.background:
        return

    if bpy.app.version < (2, 80):  # 2.7x
        fill_properties(bpy.types.MESH_OT_bridge_edge_loops, BR)
        fill_properties(bpy.types.MESH_OT_fill_grid, GR)
        bpy.utils.register_module(__name__)
    else:
        fill_properties(bpy.ops.mesh.bridge_edge_loops, BR)
        fill_properties(bpy.ops.mesh.fill_grid, GR)
        for c in classes:
            make_annotations(c)
            bpy.utils.register_class(c)

    pr = prefs()

    KMH.keymap("Mesh")
    KMH.operator(MESH_OT_smart_fill_popup, 'F')

    kmi = KMH.operator(
        MESH_OT_smart_fill_repeat, 'WHEELDOWNMOUSE', shift=True)
    kmi.properties.delta = -1
    kmi.properties.mode = 'TWIST'
    kmi.active = pr.mouse_wheel
    kmi.properties['hkey_desc'] = 'Decrease Twists'
    MOUSEWHEEL_KMIS.append(kmi)

    kmi = KMH.operator(
        MESH_OT_smart_fill_repeat, 'WHEELUPMOUSE', shift=True)
    kmi.properties.delta = 1
    kmi.properties.mode = 'TWIST'
    kmi.active = pr.mouse_wheel
    kmi.properties['hkey_desc'] = 'Increase Twists'
    MOUSEWHEEL_KMIS.append(kmi)

    kmi = KMH.operator(
        MESH_OT_smart_fill_repeat, 'WHEELDOWNMOUSE', ctrl=True)
    kmi.properties.delta = -1
    kmi.properties.mode = 'NUM_CUTS'
    kmi.active = pr.mouse_wheel
    kmi.properties['hkey_desc'] = 'Decrease Cuts'
    MOUSEWHEEL_KMIS.append(kmi)

    kmi = KMH.operator(
        MESH_OT_smart_fill_repeat, 'WHEELUPMOUSE', ctrl=True)
    kmi.properties.delta = 1
    kmi.properties.mode = 'NUM_CUTS'
    kmi.active = pr.mouse_wheel
    kmi.properties['hkey_desc'] = 'Increase Cuts'
    MOUSEWHEEL_KMIS.append(kmi)


def unregister():
    if bpy.app.background:
        return

    if bpy.app.version < (2, 80):  # 2.7x
        bpy.utils.unregister_module(__name__)
    else:
        for c in reversed(classes):
            bpy.utils.unregister_class(c)

    KMH.unregister()
    MOUSEWHEEL_KMIS.clear()
