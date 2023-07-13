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

# (c) 2022 Jakub Uhlik

import numpy as np
import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
import mathutils
from mathutils import Vector, Matrix

import platform

from .theme import ToolTheme


# NOTE: it made some circular import problems, that is why log finctions are repeated here. uncomment if needed
'''
def debug_mode():
    return (bpy.app.debug_value != 0)


def colorize(msg, ):
    if(platform.system() == 'Windows'):
        return msg
    # return "{}{}{}".format("\033[42m\033[30m", msg, "\033[0m", )
    return "{}{}{}".format("\033[43m\033[30m", msg, "\033[0m", )


def log(msg, indent=0, prefix='>', ):
    m = "{}{} {}".format("    " * indent, prefix, colorize(msg, ), )
    if(debug_mode()):
        print(m)
'''


class SC5InfoBox():
    _initialized = False
    _handle = None
    # _sv3d = None
    _theme = None
    
    INFO = None
    
    # defaults
    FONT_ID = 0
    UI_SCALE = 1.0
    DEFAULT_BOX_OUTER_PADDING = 20
    DEFAULT_BOX_CORNER_RADIUS = 10
    DEFAULT_TEXT_PADDING = 10
    
    # outside of box so shadow have space
    BOX_OUTER_PADDING = int(DEFAULT_BOX_OUTER_PADDING * UI_SCALE)
    BOX_CORNER_RADIUS = int(DEFAULT_BOX_CORNER_RADIUS * UI_SCALE)
    BOX_SHADOW_COLOR = (0.0, 0.0, 0.0, 0.5, )
    BOX_FILL_COLOR = (0.12, 0.12, 0.12, 0.95, )
    BOX_OUTLINE_COLOR = (0.12, 0.12, 0.12, 0.95, )
    # text offset from box edges
    TEXT_PADDING = int(DEFAULT_TEXT_PADDING * UI_SCALE)
    
    # logo data
    LOGO_COLOR = (1.0, 1.0, 1.0, 1.0)
    LOGO_VS = np.array([(0.11751269549131393, 0.6072840094566345, 0.0), (0.12841850519180298, 0.6378181576728821, 0.0), (0.14277447760105133, 0.6656177639961243, 0.0),
                        (0.16040848195552826, 0.6908094882965088, 0.0), (0.18114860355854034, 0.7135199308395386, 0.0), (0.20482267439365387, 0.7338758707046509, 0.0),
                        (0.23125870525836945, 0.7520041465759277, 0.0), (0.2586445212364197, 0.7671027779579163, 0.0), (0.28689053654670715, 0.779304027557373, 0.0),
                        (0.31601640582084656, 0.788689374923706, 0.0), (0.34604158997535706, 0.7953400611877441, 0.0), (0.4088685214519501, 0.8007632493972778, 0.0),
                        (0.4088685214519501, 0.6854098439216614, 0.0), (0.38104140758514404, 0.6818395256996155, 0.0), (0.3547997772693634, 0.675152599811554, 0.0),
                        (0.3302208483219147, 0.6652109026908875, 0.0), (0.30738189816474915, 0.6518765091896057, 0.0), (0.2863602638244629, 0.6350112557411194, 0.0),
                        (0.26723310351371765, 0.614477276802063, 0.0), (0.2554401457309723, 0.5981579422950745, 0.0), (0.24580229818820953, 0.580971360206604, 0.0),
                        (0.23826812207698822, 0.5628536939620972, 0.0), (0.23278608918190002, 0.5437411069869995, 0.0), (0.2293047308921814, 0.5235697031021118, 0.0),
                        (0.22777247428894043, 0.5022755861282349, 0.0), (0.4540034830570221, 0.5022755861282349, 0.0), (0.45401448011398315, 0.3296409845352173, 0.0),
                        (0.44749876856803894, 0.2785767614841461, 0.0), (0.44127991795539856, 0.25449997186660767, 0.0), (0.42313313484191895, 0.20916445553302765, 0.0),
                        (0.3976585865020752, 0.16746269166469574, 0.0), (0.3651973307132721, 0.12924639880657196, 0.0), (0.3260901868343353, 0.0943671464920044, 0.0),
                        (0.2838923931121826, 0.0650947168469429, 0.0), (0.23961150646209717, 0.041690029203891754, 0.0), (0.1933279037475586, 0.023828670382499695, 0.0),
                        (0.1451219767332077, 0.011186277493834496, 0.0), (0.09507405757904053, 0.0034382862504571676, 0.0), (0.043264441192150116, 0.00026023591635748744, 0.0),
                        (0.043264441192150116, 0.11587312072515488, 0.0), (0.10130566358566284, 0.12187999486923218, 0.0), (0.1532825082540512, 0.13366149365901947, 0.0),
                        (0.17806659638881683, 0.14250990748405457, 0.0), (0.2019544541835785, 0.1534934788942337, 0.0), (0.22487598657608032, 0.16673466563224792, 0.0),
                        (0.2467610239982605, 0.18235616385936737, 0.0), (0.27396097779273987, 0.20721641182899475, 0.0), (0.29603463411331177, 0.23462684452533722, 0.0),
                        (0.305217981338501, 0.2492510825395584, 0.0), (0.32001566886901855, 0.28026282787323, 0.0), (0.3302381634712219, 0.31352612376213074, 0.0),
                        (0.3361061215400696, 0.348921537399292, 0.0), (0.3381064534187317, 0.38959193229675293, 0.0), (0.3380848467350006, 0.38980528712272644, 0.0),
                        (0.33802330493927, 0.3900197148323059, 0.0), (0.3379267752170563, 0.39023616909980774, 0.0), (0.33780011534690857, 0.3904556930065155, 0.0),
                        (0.3362891674041748, 0.39244702458381653, 0.0), (0.3224151134490967, 0.36038318276405334, 0.0), (0.30631333589553833, 0.3317207992076874, 0.0),
                        (0.28807422518730164, 0.30630502104759216, 0.0), (0.26778796315193176, 0.2839806377887726, 0.0), (0.24554485082626343, 0.2645927667617798, 0.0),
                        (0.22143514454364777, 0.2479863315820694, 0.0), (0.1955491602420807, 0.23400631546974182, 0.0), (0.16797712445259094, 0.22249779105186462, 0.0),
                        (0.10813597589731216, 0.2062748521566391, 0.0), (0.04263397306203842, 0.19807769358158112, 0.0), (0.04263397306203842, 0.3148772418498993, 0.0),
                        (0.07197821885347366, 0.3187074363231659, 0.0), (0.09953095763921738, 0.32599014043807983, 0.0), (0.12519431114196777, 0.3368654251098633, 0.0),
                        (0.14887043833732605, 0.35147327184677124, 0.0), (0.1599327176809311, 0.3602207899093628, 0.0), (0.18044444918632507, 0.38069021701812744, 0.0),
                        (0.1954469382762909, 0.40039926767349243, 0.0), (0.2051517516374588, 0.4171237051486969, 0.0), (0.21284765005111694, 0.4346778690814972, 0.0),
                        (0.21844398975372314, 0.4527454972267151, 0.0), (0.2218501716852188, 0.47101035714149475, 0.0), (0.222975492477417, 0.4891563057899475, 0.0),
                        (0.22265446186065674, 0.4980856776237488, 0.0), (0.0013189741875976324, 0.4980856776237488, 0.0), (0.0015018392587080598, 0.6974402070045471, 0.0),
                        (0.004821633920073509, 0.7221896648406982, 0.0), (0.01072516106069088, 0.7461130619049072, 0.0), (0.019030094146728516, 0.7692733407020569, 0.0),
                        (0.04211472347378731, 0.8135554790496826, 0.0), (0.07199470698833466, 0.8546484112739563, 0.0), (0.1060294657945633, 0.8900363445281982, 0.0),
                        (0.1439233124256134, 0.9200889468193054, 0.0), (0.18538062274456024, 0.9451760053634644, 0.0), (0.2301057130098343, 0.9656672477722168, 0.0),
                        (0.2778029441833496, 0.9819322228431702, 0.0), (0.32044756412506104, 0.9920110702514648, 0.0), (0.36407291889190674, 0.9978706240653992, 0.0),
                        (0.40894266963005066, 0.9997674226760864, 0.0), (0.40894266963005066, 0.8853038549423218, 0.0), (0.3317645490169525, 0.8748103976249695, 0.0),
                        (0.29797685146331787, 0.8661330938339233, 0.0), (0.2659858465194702, 0.854373037815094, 0.0), (0.23598724603652954, 0.839246928691864, 0.0),
                        (0.20817676186561584, 0.8204715251922607, 0.0), (0.18275021016597748, 0.7977637648582458, 0.0), (0.15990318357944489, 0.7708404064178467, 0.0),
                        (0.14794105291366577, 0.7528394460678101, 0.0), (0.13798469305038452, 0.7340907454490662, 0.0), (0.12993215024471283, 0.7146375775337219, 0.0),
                        (0.1236814484000206, 0.6945231556892395, 0.0), (0.11617753654718399, 0.6524834632873535, 0.0), (0.11398942768573761, 0.6083963513374329, 0.0)], dtype=np.float32, )
    LOGO_FS = np.array([(106, 86, 107), (64, 63, 72), (63, 62, 73), (64, 72, 71), (62, 61, 73), (61, 60, 74), (60, 59, 75), (59, 58, 76), (61, 74, 73), (58, 57, 77),
                        (74, 60, 75), (66, 65, 70), (65, 64, 71), (68, 67, 69), (67, 66, 69), (65, 71, 70), (72, 63, 73), (70, 69, 66), (75, 59, 76), (76, 58, 77),
                        (78, 77, 57), (79, 78, 57), (80, 79, 24), (79, 57, 24), (81, 80, 24), (83, 82, 110), (82, 81, 0), (110, 82, 0), (85, 84, 108), (84, 83, 108),
                        (85, 108, 107), (87, 86, 106), (86, 85, 107), (87, 106, 105), (89, 88, 103), (88, 87, 104), (103, 88, 104), (91, 90, 101), (90, 89, 102),
                        (101, 90, 102), (93, 92, 99), (92, 91, 100), (99, 92, 100), (95, 94, 98), (94, 93, 98), (97, 96, 95), (98, 97, 95), (98, 93, 99), (87, 105, 104),
                        (40, 39, 37), (39, 38, 37), (37, 36, 40), (36, 35, 41), (35, 34, 42), (42, 34, 43), (34, 33, 43), (33, 32, 45), (32, 31, 46), (31, 30, 47),
                        (32, 46, 45), (30, 29, 48), (29, 28, 49), (30, 48, 47), (28, 27, 50), (27, 26, 50), (28, 50, 49), (26, 25, 55), (25, 24, 57), (33, 45, 44),
                        (43, 33, 44), (41, 40, 36), (42, 41, 35), (13, 12, 11), (11, 10, 13), (10, 9, 14), (9, 8, 15), (8, 7, 15), (15, 7, 16), (7, 6, 16), (6, 5, 17),
                        (5, 4, 17), (4, 3, 18), (17, 4, 18), (3, 2, 19), (2, 1, 19), (3, 19, 18), (1, 0, 20), (6, 17, 16), (10, 14, 13), (15, 14, 9), (19, 1, 20),
                        (21, 20, 0), (22, 21, 0), (22, 0, 23), (23, 0, 81), (24, 23, 81), (48, 29, 49), (101, 100, 91), (46, 31, 47), (51, 50, 26), (52, 51, 26),
                        (53, 52, 26), (54, 53, 26), (55, 54, 26), (56, 55, 25), (57, 56, 25), (102, 89, 103), (83, 110, 109), (83, 109, 108)], dtype=np.int32, )
    LOGO_ES = np.array([[95, 96], [94, 95], [93, 94], [92, 93], [91, 92], [90, 91], [89, 90], [96, 97], [97, 98], [88, 89], [98, 99], [99, 100], [100, 101], [87, 88],
                        [101, 102], [102, 103], [10, 11], [9, 10], [103, 104], [8, 9], [86, 87], [7, 8], [104, 105], [6, 7], [85, 86], [105, 106], [5, 6], [84, 85],
                        [106, 107], [4, 5], [83, 84], [107, 108], [3, 4], [11, 12], [12, 13], [13, 14], [2, 3], [14, 15], [108, 109], [15, 16], [1, 2], [16, 17],
                        [17, 18], [0, 1], [109, 110], [0, 110], [18, 19], [19, 20], [20, 21], [21, 22], [22, 23], [23, 24], [24, 25], [82, 83], [81, 82], [80, 81],
                        [79, 80], [78, 79], [77, 78], [76, 77], [75, 76], [74, 75], [57, 58], [56, 57], [55, 56], [54, 55], [53, 54], [52, 53], [73, 74], [51, 52],
                        [58, 59], [72, 73], [25, 26], [71, 72], [59, 60], [70, 71], [50, 51], [69, 70], [68, 69], [60, 61], [26, 27], [49, 50], [61, 62], [27, 28],
                        [62, 63], [48, 49], [47, 48], [63, 64], [64, 65], [28, 29], [46, 47], [65, 66], [67, 68], [66, 67], [45, 46], [29, 30], [44, 45], [43, 44],
                        [30, 31], [42, 43], [41, 42], [40, 41], [39, 40], [31, 32], [32, 33], [33, 34], [34, 35], [35, 36], [38, 39], [36, 37], [37, 38]], dtype=np.int32, )
    
    # NOTE: will fail when running headless: SystemError: GPU functions for drawing are not available in background mode
    if(not bpy.app.background):
        LOGO_FILL_SHADER = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        LOGO_FILL_BATCH = batch_for_shader(LOGO_FILL_SHADER, 'TRIS', {"pos": LOGO_VS[:, :2], }, indices=LOGO_FS, )
        LOGO_OUTLINE_SHADER = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        LOGO_OUTLINE_BATCH = batch_for_shader(LOGO_OUTLINE_SHADER, 'LINES', {'pos': LOGO_VS, }, indices=LOGO_ES, )
    
    @classmethod
    def init(cls, info, ):
        if(cls._initialized):
            # log("SC5InfoBox.init() denied, already running..", indent=0, prefix='>>>', )
            return
        
        # log("SC5InfoBox.init()", indent=0, prefix='>>>', )
        
        cls._theme = ToolTheme()
        cls.BOX_SHADOW_COLOR = cls._theme._info_box_shadow_color
        cls.BOX_FILL_COLOR = cls._theme._info_box_fill_color
        cls.BOX_OUTLINE_COLOR = cls._theme._info_box_outline_color
        cls.LOGO_COLOR = cls._theme._info_box_logo_color
        
        cls.INFO = info
        
        # # recalculate according to ui scale
        # u = bpy.context.preferences.addons['Scatter5'].preferences.ui_scale_viewport
        # cls.UI_SCALE = bpy.context.preferences.system.ui_scale * u
        cls.UI_SCALE = cls._theme._ui_scale * cls._theme._info_box_scale
        
        cls.BOX_OUTER_PADDING = int(cls.DEFAULT_BOX_OUTER_PADDING * cls.UI_SCALE)
        cls.BOX_CORNER_RADIUS = int(cls.DEFAULT_BOX_CORNER_RADIUS * cls.UI_SCALE)
        cls.TEXT_PADDING = int(cls.DEFAULT_TEXT_PADDING * cls.UI_SCALE)
        
        # cls._sv3d = sv3d
        # if(cls._sv3d is not None):
        #     # draw only in specific 3d view >> custom modal operators with overlay..
        #     # cls._handle = cls._sv3d.draw_handler_add(cls._post_pixel_handler, (context, ), 'WINDOW', 'POST_PIXEL')
        #     cls._handle = cls._sv3d.draw_handler_add(cls._post_pixel_handler, (), 'WINDOW', 'POST_PIXEL')
        #     print("!")
        # else:
        #     # draw in all 3d views >> using builtin tools like weight paint..
        #     cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._post_pixel_handler, (), 'WINDOW', 'POST_PIXEL')
        
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._post_pixel_handler, (), 'WINDOW', 'POST_PIXEL')
        
        cls._initialized = True
        cls._setup()
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            # log("SC5InfoBox.deinit() denied, not running..", indent=0, prefix='>>>', )
            return
        
        # log("SC5InfoBox.deinit()", indent=0, prefix='>>>', )
        
        # if(cls._sv3d is not None):
        #     cls._sv3d.draw_handler_remove(cls._handle, 'WINDOW', )
        # else:
        #     bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        
        cls.INFO = None
        # cls._sv3d = None
        cls._handle = None
        
        cls._theme = None
        
        cls._initialized = False
        cls._cleanup()
        cls._tag_redraw()
    
    @classmethod
    def _setup_text(cls, ):
        # find longest line in pixels and sum whole paragraph height
        max_line_width = 0
        total_height = 0
        for i, item in enumerate(reversed(cls.INFO)):
            s = int(round(item['style']['size'] * cls.UI_SCALE))
            blf.size(cls.FONT_ID, s, 72)
            for j, t in enumerate(item['text']):
                if(t is None):
                    l = int(np.ceil(item['style']['separator'] * cls.UI_SCALE))
                    total_height += l
                    continue
                
                w, _ = blf.dimensions(cls.FONT_ID, t)
                _, h = blf.dimensions(cls.FONT_ID, 'F')
                ml = int(np.ceil(item['style']['margin_left'] * cls.UI_SCALE))
                l = int(np.ceil(item['style']['line_height'] * cls.UI_SCALE))
                total_height += l
                if(w + ml > max_line_width):
                    max_line_width = w + ml
        
        max_line_width += 2 * cls.TEXT_PADDING
        total_height += 2 * cls.TEXT_PADDING
        # subtract last line height without spacing
        total_height -= l - h
        
        cls._max_line_width = int(np.ceil(max_line_width))
        cls._total_height = int(np.ceil(total_height))
    
    @classmethod
    def _rounded_rectangle(cls, a, b, radius, steps=32, ):
        c = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        aa = np.arange(steps, dtype=np.int32, )
        c[:, 0] = np.sin(aa * angstep) * radius
        c[:, 1] = np.cos(aa * angstep) * radius
        
        q = int(steps / 4)
        trc = c[:q + 1].copy()
        brc = c[q:q * 2 + 1].copy()
        blc = c[q * 2:q * 3 + 1].copy()
        tlc = c[q * 3:].copy()
        tlc = np.concatenate([tlc, c[0].copy().reshape((-1, 2))])
        
        trc[:, 0] += b[0] - radius
        trc[:, 1] += b[1] - radius
        brc[:, 0] += b[0] - radius
        brc[:, 1] += a[1] + radius
        blc[:, 0] += a[0] + radius
        blc[:, 1] += a[1] + radius
        tlc[:, 0] += a[0] + radius
        tlc[:, 1] += b[1] - radius
        
        vs = np.concatenate([trc, brc, blc, tlc, ])
        indices = np.array(mathutils.geometry.tessellate_polygon((vs, )), dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def _clone_texture(cls, tex, ):
        w = tex.width
        h = tex.height
        f = tex.format
        b = tex.read()
        # NOTE: should i be explicit about data type? i think i should..
        a = np.array(b, dtype=np.float32, )
        a = a.copy()
        b = gpu.types.Buffer('FLOAT', (w, h, 4), a.flatten())
        t = gpu.types.GPUTexture((w, h), format=f, data=b, )
        return t
    
    @classmethod
    def _setup_box(cls, ):
        w = cls._max_line_width
        h = cls._total_height
        p = cls.BOX_OUTER_PADDING
        cls._box_width = w + (p * 2)
        cls._box_height = h + (p * 2)
        
        # draw rounded rectange as source of shadow
        cls._tex_color = gpu.types.GPUTexture((cls._box_width, cls._box_height), format='RGBA32F', )
        cls._fbo = gpu.types.GPUFrameBuffer(color_slots=cls._tex_color, )
        
        with cls._fbo.bind():
            cls._tex_color.clear(format='FLOAT', value=(0.0, ), )
            
            a = [p, p]
            b = [w + p, h + p]
            # color = [0.0, 0.0, 0.0, 1.0]
            color = cls.BOX_SHADOW_COLOR
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    
                    vertices, indices = cls._rounded_rectangle(a, b, cls.BOX_CORNER_RADIUS, steps=32, )
                    vertices[:, 0] *= (1 / cls._box_width)
                    vertices[:, 1] *= (1 / cls._box_height)
                    vertices *= 2.0
                    vertices -= 1.0
                    
                    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                    batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
                    gpu.state.blend_set('ALPHA')
                    shader.bind()
                    shader.uniform_float('color', color, )
                    batch.draw(shader)
                    gpu.state.blend_set('NONE')
        
        # blur rectangle
        vert = '''
        uniform mat4 ModelViewProjectionMatrix;
        in vec2 pos;
        out vec2 uv;
        void main()
        {
            gl_Position = ModelViewProjectionMatrix * vec4(pos.xy, 1.0f, 1.0f);
            uv = pos.xy;
        }
        '''
        # https://github.com/mrdoob/three.js/blob/c93db539b230417f6b8a5261fbc52bba1cd39d7d/examples/jsm/shaders/HorizontalBlurShader.js
        frag_h = '''
        in vec2 uv;
        uniform sampler2D color;
        uniform float h;
        out vec4 fragColor;
        void main() {
            vec4 sum = vec4(0.0);
            sum += texture(color, vec2(uv.x - 4.0 * h, uv.y)) * 0.051;
            sum += texture(color, vec2(uv.x - 3.0 * h, uv.y)) * 0.0918;
            sum += texture(color, vec2(uv.x - 2.0 * h, uv.y)) * 0.12245;
            sum += texture(color, vec2(uv.x - 1.0 * h, uv.y)) * 0.1531;
            sum += texture(color, vec2(uv.x, uv.y ) ) * 0.1633;
            sum += texture(color, vec2(uv.x + 1.0 * h, uv.y)) * 0.1531;
            sum += texture(color, vec2(uv.x + 2.0 * h, uv.y)) * 0.12245;
            sum += texture(color, vec2(uv.x + 3.0 * h, uv.y)) * 0.0918;
            sum += texture(color, vec2(uv.x + 4.0 * h, uv.y)) * 0.051;
            fragColor = sum;
            //fragColor = vec4(uv.x, uv.y, 0.0, 1.0);
        }
        '''
        frag_v = '''
        in vec2 uv;
        uniform sampler2D color;
        uniform float v;
        out vec4 fragColor;
        void main() {
            vec4 sum = vec4(0.0);
            sum += texture(color, vec2(uv.x, uv.y - 4.0 * v)) * 0.051;
            sum += texture(color, vec2(uv.x, uv.y - 3.0 * v)) * 0.0918;
            sum += texture(color, vec2(uv.x, uv.y - 2.0 * v)) * 0.12245;
            sum += texture(color, vec2(uv.x, uv.y - 1.0 * v)) * 0.1531;
            sum += texture(color, vec2(uv.x, uv.y ) ) * 0.1633;
            sum += texture(color, vec2(uv.x, uv.y + 1.0 * v)) * 0.1531;
            sum += texture(color, vec2(uv.x, uv.y + 2.0 * v)) * 0.12245;
            sum += texture(color, vec2(uv.x, uv.y + 3.0 * v)) * 0.0918;
            sum += texture(color, vec2(uv.x, uv.y + 4.0 * v)) * 0.051;
            fragColor = sum;
        }
        '''
        
        # blur horizontally
        texture = cls._tex_color
        cls._h_color = gpu.types.GPUTexture((cls._box_width, cls._box_height), format='RGBA32F', )
        cls._h_fbo = gpu.types.GPUFrameBuffer(color_slots=cls._h_color, )
        with cls._h_fbo.bind():
            cls._h_color.clear(format='FLOAT', value=(0.0, ), )
            
            coords = ((0, 0), (1, 0), (1, 1), (0, 1))
            shader = gpu.types.GPUShader(vert, frag_h, )
            indices = mathutils.geometry.tessellate_polygon((coords, ))
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords, }, indices=indices, )
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    # gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    projection = Matrix.LocRotScale(Vector((-1, -1, 0.0)), None, Vector((2.0, 2.0, 1.0)))
                    gpu.matrix.load_projection_matrix(projection)
                    
                    gpu.state.blend_set('ALPHA')
                    shader.bind()
                    shader.uniform_sampler("color", texture)
                    shader.uniform_float("h", 1 / cls._box_width)
                    batch.draw(shader)
                    gpu.state.blend_set('NONE')
        
        texture = cls._h_color
        
        # and blur vertically
        cls._v_color = gpu.types.GPUTexture((cls._box_width, cls._box_height), format='RGBA32F', )
        cls._v_fbo = gpu.types.GPUFrameBuffer(color_slots=cls._v_color, )
        with cls._v_fbo.bind():
            cls._v_color.clear(format='FLOAT', value=(0.0, ), )
            
            coords = ((0, 0), (1, 0), (1, 1), (0, 1))
            shader = gpu.types.GPUShader(vert, frag_v, )
            indices = mathutils.geometry.tessellate_polygon((coords, ))
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords, }, indices=indices, )
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    # gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    projection = Matrix.LocRotScale(Vector((-1, -1, 0.0)), None, Vector((2.0, 2.0, 1.0)))
                    gpu.matrix.load_projection_matrix(projection)
                    
                    gpu.state.blend_set('ALPHA')
                    shader.bind()
                    shader.uniform_sampler("color", texture)
                    shader.uniform_float("v", 1 / cls._box_height)
                    batch.draw(shader)
                    gpu.state.blend_set('NONE')
        
        texture = cls._v_color
        
        # now draw it again with some shadow offset
        cls._fin_color = gpu.types.GPUTexture((cls._box_width, cls._box_height), format='RGBA32F', )
        cls._fin_fbo = gpu.types.GPUFrameBuffer(color_slots=cls._fin_color, )
        with cls._fin_fbo.bind():
            cls._fin_color.clear(format='FLOAT', value=(0.0, ), )
            
            shadow_offset = 5
            position = 0, -((1 / cls._box_height) * shadow_offset)
            coords = ((0, 0), (1, 0), (1, 1), (0, 1))
            shader = shader = gpu.shader.from_builtin('2D_IMAGE')
            indices = mathutils.geometry.tessellate_polygon((coords, ))
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "texCoord": coords, }, indices=indices, )
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    gpu.matrix.translate(position)
                    # gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    projection = Matrix.LocRotScale(Vector((-1, -1, 0.0)), None, Vector((2.0, 2.0, 1.0)))
                    gpu.matrix.load_projection_matrix(projection)
                    
                    gpu.state.blend_set('ALPHA')
                    shader.bind()
                    shader.uniform_sampler("image", texture)
                    batch.draw(shader)
                    gpu.state.blend_set('NONE')
            
            # and draw zero color rectange into original location to knock out shadow from inside of box
            a = [p, p]
            b = [w + p, h + p]
            color = [0.0, 0.0, 0.0, 0.0]
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    vertices, indices = cls._rounded_rectangle(a, b, cls.BOX_CORNER_RADIUS, steps=32, )
                    vertices[:, 0] *= (1 / cls._box_width)
                    vertices[:, 1] *= (1 / cls._box_height)
                    vertices *= 2.0
                    vertices -= 1.0
                    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                    batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
                    shader.bind()
                    shader.uniform_float('color', color, )
                    batch.draw(shader)
        
        # that's mine finished box texture, lets hope it stays in memory
        # TODO: when this is cleared from memory? there is `bpy.types.Image.gl_touch` for images, do i need something similar? i don't see anything in docs..
        # cls._texture = cls._fin_color
        cls._texture = cls._clone_texture(cls._fin_color)
        
        cls._tex_color = None
        cls._fbo = None
        cls._h_color = None
        cls._h_fbo = None
        cls._v_color = None
        cls._v_fbo = None
        cls._fin_color = None
        cls._fin_fbo = None
        
        '''
        # # # # debug
        buffer = cls._texture.read()
        # print(buffer)
        buffer.dimensions = cls._box_width * cls._box_height * 4
        image_name = "pcv_debug"
        if(image_name not in bpy.data.images):
            bpy.data.images.new(image_name, cls._box_width, cls._box_height, float_buffer=True, )
        image = bpy.data.images[image_name]
        image.scale(cls._box_width, cls._box_height, )
        # print(image.size[:])
        a = np.array(buffer)
        # print(np.sum(a.flatten()))
        # print(a.flatten().tolist())
        image.pixels = a.flatten()
        # # # # debug
        '''
    
    @classmethod
    def _setup(cls, ):
        cls._setup_text()
        cls._setup_box()
    
    @classmethod
    def _cleanup(cls, ):
        # clear (set to None) all that might take memory..
        # print(dir(cls))
        cls._max_line_width = None
        cls._total_height = None
        cls._box_height = None
        cls._box_width = None
        
        cls._fbo = None
        cls._tex_color = None
        cls._h_fbo = None
        cls._h_color = None
        cls._v_fbo = None
        cls._v_color = None
        cls._fin_fbo = None
        cls._fin_color = None
        
        cls._texture = None
    
    @classmethod
    def _thick_line_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(((a[0], a[1], 0.0, ), (b[0], b[1], 0.0, ), ), dtype=np.float32, )
        indices = np.array(((0, 1), ), dtype=np.int32, )
        shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def _draw_logo(cls, height, ):
        color = cls.LOGO_COLOR
        cls.LOGO_SCALE = height * cls.UI_SCALE
        
        x = cls.BOX_OUTER_PADDING + cls.TEXT_PADDING
        # y = cls._total_height - (cls.BOX_OUTER_PADDING + cls.TEXT_PADDING) + int(6 * cls.UI_SCALE)
        y = cls._total_height - cls.BOX_OUTER_PADDING - cls.TEXT_PADDING + (cls.TEXT_PADDING / 2)
        
        # TODO: this should be called just once per viewport, no need to do it 3 times for each viewport, but like that is easy to implement now..
        # NOTE: fix info location when region overlap is enabled
        x_correction = 0
        if(bpy.context.preferences.system.use_region_overlap):
            vwx, vwy, vww, vwh = gpu.state.viewport_get()
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if(area.type == 'VIEW_3D'):
                        wh = -1
                        th = -1
                        tw = -1
                        ok = False
                        for r in area.regions:
                            if(r.type == 'TOOLS'):
                                th = r.height
                                tw = r.width
                            if(r.type == 'WINDOW'):
                                if(r.width == vww and r.height == vwh):
                                    ok = True
                                wh = r.height
                        if(ok):
                            # if(wh > 0 and th > 0 and tw > 0 and wh == th):
                            if(wh > 0 and th > 0 and tw > 0):
                                x_correction = tw
        
        x += x_correction
        
        # draw filled triangles
        with gpu.matrix.push_pop():
            gpu.matrix.translate((x, y))
            gpu.matrix.scale((cls.LOGO_SCALE, cls.LOGO_SCALE))
            cls.LOGO_FILL_SHADER.bind()
            cls.LOGO_FILL_SHADER.uniform_float("color", color, )
            gpu.state.blend_set('ALPHA')
            cls.LOGO_FILL_BATCH.draw(cls.LOGO_FILL_SHADER)
            gpu.state.blend_set('NONE')
        
        # draw thick line outline to have it looking antialiased..
        with gpu.matrix.push_pop():
            gpu.matrix.translate((x, y))
            gpu.matrix.scale((cls.LOGO_SCALE, cls.LOGO_SCALE))
            cls.LOGO_OUTLINE_SHADER.bind()
            cls.LOGO_OUTLINE_SHADER.uniform_float('color', color, )
            cls.LOGO_OUTLINE_SHADER.uniform_float("lineWidth", 1.0, )
            _, _, w, h = gpu.state.viewport_get()
            cls.LOGO_OUTLINE_SHADER.uniform_float("viewportSize", (w, h, ))
            gpu.state.blend_set('ALPHA')
            cls.LOGO_OUTLINE_BATCH.draw(cls.LOGO_OUTLINE_SHADER)
            gpu.state.blend_set('NONE')
    
    @classmethod
    def _draw_box(cls, ):
        _, _, w, h = gpu.state.viewport_get()
        
        # TODO: this should be called just once per viewport, no need to do it 3 times for each viewport, but like that is easy to implement now..
        # NOTE: fix info location when region overlap is enabled
        x_correction = 0
        if(bpy.context.preferences.system.use_region_overlap):
            vwx, vwy, vww, vwh = gpu.state.viewport_get()
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if(area.type == 'VIEW_3D'):
                        wh = -1
                        th = -1
                        tw = -1
                        ok = False
                        for r in area.regions:
                            if(r.type == 'TOOLS'):
                                th = r.height
                                tw = r.width
                            if(r.type == 'WINDOW'):
                                if(r.width == vww and r.height == vwh):
                                    ok = True
                                wh = r.height
                        if(ok):
                            # if(wh > 0 and th > 0 and tw > 0 and wh == th):
                            if(wh > 0 and th > 0 and tw > 0):
                                x_correction = tw
        
        position = (0 + x_correction, 0, )
        
        # draw box shadow texture first
        texture = cls._texture
        
        width = texture.width
        height = texture.height
        coords = ((0, 0), (1, 0), (1, 1), (0, 1))
        shader = gpu.shader.from_builtin('2D_IMAGE')
        indices = mathutils.geometry.tessellate_polygon((coords, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "texCoord": coords, }, indices=indices, )
        
        with gpu.matrix.push_pop():
            gpu.matrix.translate(position)
            gpu.matrix.scale((width, height))
            gpu.state.blend_set('ALPHA')
            shader.bind()
            shader.uniform_sampler("image", texture)
            batch.draw(shader)
            gpu.state.blend_set('NONE')
        
        # then draw box fill
        w = cls._max_line_width
        h = cls._total_height
        p = cls.BOX_OUTER_PADDING
        a = [p + x_correction, p]
        b = [w + p + x_correction, h + p]
        # color = (0.3, 0.3, 0.3, 0.5)
        color = cls.BOX_FILL_COLOR
        vertices, indices = cls._rounded_rectangle(a, b, cls.BOX_CORNER_RADIUS, steps=32, )
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
        
        # and lastly draw box outline to have it looking antialiased
        o = 0
        a = [p - o + x_correction, p - o]
        b = [w + p + o + x_correction, h + p + o]
        vertices, indices = cls._rounded_rectangle(a, b, cls.BOX_CORNER_RADIUS, steps=32 * 2, )
        color = cls.BOX_OUTLINE_COLOR
        # thickness = 2
        thickness = cls._theme._info_box_outline_thickness
        z = np.zeros(len(vertices), dtype=np.float32, )
        vs = np.c_[vertices[:, 0], vertices[:, 1], z]
        i = np.arange(len(vs), dtype=np.int32, )
        indices = np.c_[i, np.roll(i, -1), ]
        shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vs, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def _draw_text(cls, ):
        x = cls.BOX_OUTER_PADDING + cls.TEXT_PADDING
        y = cls.BOX_OUTER_PADDING + cls.TEXT_PADDING
        
        # TODO: this should be called just once per viewport, no need to do it 3 times for each viewport, but like that is easy to implement now..
        # NOTE: fix info location when region overlap is enabled
        x_correction = 0
        if(bpy.context.preferences.system.use_region_overlap):
            vwx, vwy, vww, vwh = gpu.state.viewport_get()
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if(area.type == 'VIEW_3D'):
                        wh = -1
                        th = -1
                        tw = -1
                        ok = False
                        for r in area.regions:
                            if(r.type == 'TOOLS'):
                                th = r.height
                                tw = r.width
                            if(r.type == 'WINDOW'):
                                if(r.width == vww and r.height == vwh):
                                    ok = True
                                wh = r.height
                        if(ok):
                            # if(wh > 0 and th > 0 and tw > 0 and wh == th):
                            if(wh > 0 and th > 0 and tw > 0):
                                x_correction = tw
        
        x += x_correction
        
        # loop from last item in list (should be logo), the rest should be lines of text (or dividers)
        for i, item in enumerate(reversed(cls.INFO)):
            s = int(round(item['style']['size'] * cls.UI_SCALE))
            
            blf.size(cls.FONT_ID, s, 72)
            blf.color(cls.FONT_ID, *item['style']['color'])
            blf.enable(cls.FONT_ID, blf.SHADOW)
            blf.shadow(cls.FONT_ID, 3, 0.0, 0.0, 0.0, 0.5)
            blf.shadow_offset(cls.FONT_ID, 0, -2)
            
            for j, t in enumerate(reversed(item['text'])):
                if(t is None):
                    l = int(np.ceil(item['style']['separator'] * cls.UI_SCALE))
                    y += l
                    continue
                
                w, _ = blf.dimensions(cls.FONT_ID, t)
                _, h = blf.dimensions(cls.FONT_ID, 'F')
                ml = int(np.ceil(item['style']['margin_left'] * cls.UI_SCALE))
                l = int(np.ceil(item['style']['line_height'] * cls.UI_SCALE))
                
                blf.position(cls.FONT_ID, x + ml, y, 0, )
                blf.draw(cls.FONT_ID, t)
                
                if('line' in item):
                    # divider
                    yy = y + int(l / 2) - (item['style']['size'] * cls.UI_SCALE) - (1 * cls.UI_SCALE)
                    a = (x + ml, yy, )
                    # TODO: this might not be right, some combinations of paddings cause line to be longer then it should be. and it also displaces logo, but that is unrelated to lines
                    b = (x + cls._max_line_width - cls.BOX_OUTER_PADDING, yy, )
                    cls._thick_line_2d(a, b, color=item['style']['color'], thickness=item['style']['size'] * cls.UI_SCALE, )
                
                if('logo' in item):
                    # call logo function
                    cls._draw_logo(item['height'], )
                
                y += l
    
    @classmethod
    def _post_pixel_handler(cls, ):
        cls._draw_box()
        cls._draw_text()
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


# TODO: link values to widgets.theme.ToolTheme directly. i don't need them defined here
HEADER_COLOR = (1.0, 1.0, 1.0, 1.0, )
BODY_COLOR = (0.8, 0.8, 0.8, 1.0, )
# NOTE: these will be properly scaled by ui_scale and theme._info_box_scale later, these are values at final scale 1.0 @ 72dpi
H1 = (18, 26, )
H2 = (14, 20, )
P = (12, 16, )
P_SEPARATOR = 6
HEADER_LOGO_OFFSET = 22


def generic_infobox_setup(h1, h2, ls, ):
    '''
    h1 - main header line
    h2 - second header line
    - both header lines are offset to right to make space for logo
    - then divider line is drawn
    ls - list of shortcuts for brush
    '''
    
    _theme = ToolTheme()
    HEADER_COLOR = _theme._info_box_text_header_color
    BODY_COLOR = _theme._info_box_text_body_color
    
    t = [
        # sizes at 72 dpi
        {
            'style': {
                'size': H1[0],
                'color': HEADER_COLOR,
                'line_height': H1[1],
                'margin_left': HEADER_LOGO_OFFSET,
            },
            # should be fixed for each mode
            'text': [h1, ],
        },
        {
            'style': {
                'size': H2[0],
                'color': HEADER_COLOR,
                'line_height': H2[1],
                'margin_left': HEADER_LOGO_OFFSET,
            },
            # should be fixed for each mode
            'text': [h2, ],
        },
        {
            'style': {
                'size': 2,
                'color': HEADER_COLOR,
                'line_height': 12,
                'margin_left': 0,
            },
            'text': ["", ],
            # divider line
            'line': True,
        },
        {
            'style': {
                'size': P[0],
                'color': BODY_COLOR,
                'line_height': P[1],
                'margin_left': 0,
                'separator': P_SEPARATOR,
            },
            'text': ls,
        },
        {
            # logo have to be as last element (i.e. reversed >> first) so i don't have messed up line spacing. and it contains nothing, zero sizes. draw function will make everything..
            'style': {'size': 0, 'color': HEADER_COLOR, 'line_height': 0, 'margin_left': 0, },
            'text': ["", ],
    
            'logo': True,
            # it is always in top left corner..
            # line 1: 26 + line 2: 20 = 46 - 10 padding - 2 = 34.. don't ask me why, but looks better..
            'height': 34,
        },
    ]
    return t


'''
class SCATTER5_OT_infobox_test_operator(bpy.types.Operator, ):
    bl_idname = "scatter5.infobox_test_operator"
    bl_label = "InfoBox Test Operator"
    
    def __init__(self):
        print("start..")
    
    def __del__(self):
        print("end.")
    
    def modal(self, context, event):
        if(event.type in {'ESC', }):
            print("exiting..")
            
            SC5InfoBox.deinit()
            
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        print("invoke..")
        
        ls = ["• Press 'ANY' key to continue"] * 5
        ls = ['{} ({})'.format(t, i) for i, t in enumerate(ls)]
        t = generic_infobox_setup("Manual Distribution Mode",
                                  "Brush Name",
                                  ls, )
        SC5InfoBox.init(t)
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class SCATTER5_OT_infobox_test_operator2(bpy.types.Operator, ):
    bl_idname = "scatter5.infobox_test_operator2"
    bl_label = "InfoBox Test Operator"
    
    def __init__(self):
        print("start..")
    
    def __del__(self):
        print("end.")

    class SC5InfoBox_TestOp2(SC5InfoBox):
        pass
    
    def modal(self, context, event):
        if(event.type in {'RET', }):
            print("exiting..")
            
            self.SC5InfoBox_TestOp2.deinit()
            
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        print("invoke..")
        
        t = generic_infobox_setup("Another test",
                                  "Brush Name",
                                  ["• Press 'ANY' key to continue"] * 10, )
        self.SC5InfoBox_TestOp2.init(t)
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
'''


classes = ()

'''
if(bpy.app.debug_value != 0):
    classes += (SCATTER5_OT_infobox_test_operator, )
'''
