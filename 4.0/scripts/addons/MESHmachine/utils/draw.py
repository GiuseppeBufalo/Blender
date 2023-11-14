import bpy
from mathutils import Vector, Matrix
import gpu
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
import blf
from . registration import get_prefs
from . ui import require_header_offset
from .. colors import red



def vert_debug_print(debug, vert, msg, end="\n"):
    if debug:
        if type(debug) is list:
            if vert.index in debug:
                print(msg, end=end)
        else:
            print(msg, end=end)


def debug_draw_sweeps(self, sweeps, draw_loops=False, draw_handles=False):

    if draw_loops:
        self.loops = []

    if draw_handles:
        self.handles = []


    for sweep in sweeps:
        v1_co = sweep["verts"][0].co
        v2_co = sweep["verts"][1].co

        if draw_loops:
            loops = sweep.get("loops")

            if loops:
                remote1_co = loops[0][1]
                remote2_co = loops[1][1]

                self.loops.extend([v1_co, remote1_co, v2_co, remote2_co])

        if draw_handles:
            handles = sweep.get("handles")

            if handles:
                handle1_co = handles[0]
                handle2_co = handles[1]

                self.handles.extend([v1_co, handle1_co, v2_co, handle2_co])



def use_legacy_line_smoothing(alpha, width):

    if get_prefs().use_legacy_line_smoothing and alpha < 1:
        try:
            import bgl

            bgl.glEnable(bgl.GL_BLEND)
            bgl.glLineWidth(width)
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
        except:
            pass


def draw_point(co, mx=Matrix(), color=(1, 1, 1), size=6, alpha=1, xray=True, modal=True):
    def draw():
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co]})
        batch.draw(shader)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_points(coords, indices=None, mx=Matrix(), color=(1, 1, 1), size=6, alpha=1, xray=True, modal=True):
    def draw():
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        if indices:
            if mx != Matrix():
                batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co for co in coords]}, indices=indices)
            else:
                batch = batch_for_shader(shader, 'POINTS', {"pos": coords}, indices=indices)

        else:
            if mx != Matrix():
                batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co for co in coords]})
            else:
                batch = batch_for_shader(shader, 'POINTS', {"pos": coords})

        batch.draw(shader)


    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_line(coords, indices=None, mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        nonlocal indices

        if not indices:
            indices = [(i, i + 1) for i in range(0, len(coords)) if i < len(coords) - 1]

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        batch = batch_for_shader(shader, 'LINES', {"pos": [mx @ co for co in coords]}, indices=indices)
        batch.draw(shader)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_lines(coords, indices=None, mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        nonlocal indices

        if not indices:
            indices = [(i, i + 1) for i in range(0, len(coords), 2)]

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        if mx != Matrix():
            batch = batch_for_shader(shader, 'LINES', {"pos": [mx @ co for co in coords]}, indices=indices)

        else:
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)

        batch.draw(shader)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_vector(vector, origin=Vector((0, 0, 0)), mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        coords = [mx @ origin, mx @ origin + mx.to_3x3() @ vector]

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        batch = batch_for_shader(shader, 'LINES', {"pos": coords})
        batch.draw(shader)


    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_vectors(vectors, origins, mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        coords = []

        for v, o in zip(vectors, origins):
            coords.append(mx @ o)
            coords.append(mx @ o + mx.to_3x3() @ v)

        indices = [(i, i + 1) for i in range(0, len(coords), 2)]

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
        batch.draw(shader)


    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_circle(coords, size=10, width=1, segments=64, color=(1, 1, 1), alpha=1, xray=True, modal=True):
    def draw():
        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        draw_circle_2d(coords, (*color, alpha), size, segments=segments)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_mesh_wire(batch, color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        nonlocal batch
        coords, indices = batch


        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        use_legacy_line_smoothing(alpha, width)

        b = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
        b.draw(shader)

        del shader
        del b

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')



def draw_stashes_VIEW3D(scene, batch):
    draw_mesh_wire(batch, color=(0.4, 0.7, 1), xray=scene.MM.draw_active_stash_xray, alpha=0.4)



def draw_stashes_HUD(context, stasheslen, invalidstasheslen):
    view = context.space_data

    if stasheslen > 0 and len(context.selected_objects) > 0 and view.overlay.show_overlays:

        offset = get_prefs().stashes_hud_offset

        if require_header_offset(context, top=True):
            offset = int(25 * context.preferences.view.ui_scale)

        width = context.region.width
        height = context.region.height
        scale = context.preferences.view.ui_scale * get_prefs().modal_hud_scale
        center = (width) / 2

        color = get_prefs().modal_hud_color
        font = 1
        fontsize = int(12 * scale)

        blf.size(font, fontsize, 72)
        blf.color(font, *color, 0.5)
        blf.position(font, center - int(60 * scale), height - offset - int(15 * scale), 0)

        blf.draw(font, "Stashes:")

        blf.color(font, *color, 1)
        blf.position(font, center, height - offset - int(15 * scale), 0)
        blf.draw(font, "%d" % (stasheslen))

        if invalidstasheslen:
            blf.color(font, *red, 1)
            blf.position(font, center + int(20 * scale), height - offset - int(15 * scale), 0)
            blf.draw(font, "%d" % (invalidstasheslen))


def draw_region_border(context, color=(1, 1, 1), alpha=1, width=2, title="", subtitle=""):
    region = context.region


    coords = [(width, width), (region.width - width, width), (region.width - width, region.height - width), (width, region.height - width)]
    indices =[(0, 1), (1, 2), (2, 3), (3, 0)]

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    shader.bind()
    shader.uniform_float("color", (*color, alpha))

    gpu.state.depth_test_set('NONE')
    gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
    gpu.state.line_width_set(width)

    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    batch.draw(shader)



    offset = 10

    if require_header_offset(context, top=True):
        offset += int(25 * context.preferences.view.ui_scale)

    if title:
        center = (region.width) / 2 - 50
        scale = context.preferences.view.ui_scale * get_prefs().modal_hud_scale

        font = 1
        fontsize = int(16 * scale)

        blf.size(font, fontsize, 72)
        blf.color(font, *color, 0.5)
        blf.position(font, center - int(60 * scale), region.height - offset - int(fontsize), 0)

        blf.draw(font, title)

        if subtitle:
            subcenter = (region.width) / 2 - 20
            subfontsize = int(12 * scale)

            blf.size(font, subfontsize, 72)
            blf.color(font, *color, 1)
            blf.position(font, subcenter - int(60 * scale), region.height - offset - int(fontsize) - int(subfontsize) - 5, 0)

            blf.draw(font, subtitle)


def draw_label(context, title='', coords=None, center=True, color=(1, 1, 1), alpha=1):
    if coords:
        width, height = coords

    else:
        region = context.region
        width = region.width / 2
        height = region.height / 2

    scale = context.preferences.view.ui_scale * get_prefs().modal_hud_scale

    font = 1
    fontsize = int(12 * scale)

    blf.size(font, fontsize, 72)
    blf.color(font, *color, alpha)

    if center:
        blf.position(font, width - (int(len(title) * scale * 7) / 2), height + int(fontsize), 0)
    else:
        blf.position(font, *(coords), 1)


    blf.draw(font, title)
