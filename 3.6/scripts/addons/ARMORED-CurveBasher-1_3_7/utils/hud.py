import bpy
# import gpu

# from gpu_extras.batch import batch_for_shader

from .. utils import addon
from .. utils import colors
from .. utils import draw


addon_name = 'CURVE BASHER'


def draw_kitbasher_hud(self, context):
    # draw_hud_background(self)

    draw.draw_title(self, addon_name)
    draw.draw_string(self, f'\'{self.profile_name}\'')
    
    # if self.expanded_HUD:
    if addon.get_prefs().expanded_hud:
        draw.draw_body(self, layout_kitbasher_expanded(self))
    else:
        draw.draw_body(self, layout_kitbasher_collapsed(self))

    # (Optional).
    draw.draw_preset_keymap(self) # Scroll Up/Down

# def draw_hud_background(self):
#     offset_x = 20
#     offset_y = -10
#     width = 310
#     height = 250
#     vertices = (
#         (self.mouse_x + offset_x, self.mouse_y + offset_y), (self.mouse_x + offset_x + width, self.mouse_y + offset_y),
#         (self.mouse_x + offset_x, self.mouse_y + offset_y - height), (self.mouse_x + offset_x + width, self.mouse_y + offset_y - height)
#     )

#     indices = (
#         (0, 1, 2), (2, 1, 3))

#     shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
#     batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

#     shader.bind()
#     shader.uniform_float("color", colors.HUD_BACKGROUND)
#     batch.draw(shader)

#     return shader, batch


# LAYOUTS -----------------------------------------------------------------------------------------

def layout_kitbasher_collapsed(self):
    # FORMAT = Tuple: (Attribute Name, Value, Hotkey) or String: 'SEPARATOR'

    body = [
            ('TYPE:', self.mode_name,      'switch 1-3'     ),
            ('Mode:', self.transform_name, 'switch S, R, T, G' ),
            'SEPARATOR',

            ('EXPAND HUD >>', '', 'F1' )
        ]
    
    return body


def layout_kitbasher_expanded(self):
    # FORMAT = (Attribute Name, Value, Hotkey) or 'SEPARATOR'

    body = [
            ('TYPE:', self.mode_name,      'switch 1-3'     ),
            ('Mode:', self.transform_name, 'switch S, R, T, G' ),
            'SEPARATOR',
        ]
    
    if self.master_curve.get('mode') == 2:
        array_type_str = self.array_type.replace('_', ' ').lower().title()
        array_options = [
            ('Array Type:', array_type_str, 'toggle F' ),
        ]

        if self.array_type == 'FIXED_COUNT':
            array_options.append(
                ('Count:', self.array_count, 'SHIFT + Scroll Up/Down' ),
            )

        array_options.append(('Caps', addon.get_prefs().array_caps, 'toggle C'))
        array_options.append('SEPARATOR',)
        body.extend(array_options)
    

    global_options = [
            ('Shading:',   addon.get_prefs().smoothing.lower().capitalize(), 'cycle A' ),
            'SEPARATOR',
            
            ('Wireframe:',   addon.get_prefs().wireframe, 'toggle W' ),
            ('Outline:',     addon.get_prefs().outline,   'toggle Z' ),
            ('Stretch-fit:', self.master_curve.data.use_stretch,   'toggle X' ),
            'SEPARATOR',

            ('Select Curve Points', '', 'TAB' ),  
            ('Reset Transforms',    '', 'ALT + S, R, T, G' ),  
            ('Randomize Transform', '', 'hold ALT' ),  
            ('Ultra Randomize',     '', 'hold ALT + SHIFT' ),  
            'SEPARATOR',

            ('<< COLLAPSE HUD',  '', 'F1' )
        ]

    body.extend(global_options)
    
    return body