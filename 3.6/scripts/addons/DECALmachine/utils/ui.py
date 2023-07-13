import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
import blf
import rna_keymap_ui
from bl_ui.space_statusbar import STATUSBAR_HT_header as statusbar
from . registration import get_prefs

import gpu
from gpu_extras.batch import batch_for_shader


icons = None


def get_icon(name):
    global icons

    if not icons:
        from .. import icons

    return icons[name].icon_id



def init_cursor(self, event, offsetx=0, offsety=20):
    self.last_mouse_x = event.mouse_x
    self.last_mouse_y = event.mouse_y

    self.region_offset_x = event.mouse_x - event.mouse_region_x
    self.region_offset_y = event.mouse_y - event.mouse_region_y

    self.HUD_x = event.mouse_x - self.region_offset_x + offsetx
    self.HUD_y = event.mouse_y - self.region_offset_y + offsety


def wrap_cursor(self, context, event):




    if event.mouse_region_x <= 0:
        context.window.cursor_warp(context.region.width + self.region_offset_x - 10, event.mouse_y)

    if event.mouse_region_x >= context.region.width - 1:  # the -1 is required for full screen, where the max region width is never passed
        context.window.cursor_warp(self.region_offset_x + 10, event.mouse_y)

    if event.mouse_region_y <= 0:
        context.window.cursor_warp(event.mouse_x, context.region.height + self.region_offset_y - 10)

    if event.mouse_region_y >= context.region.height - 1:
        context.window.cursor_warp(event.mouse_x, self.region_offset_y + 100)


def warp_cursor_to_object_origin(context, event, obj):
    region_offset_x = event.mouse_x - event.mouse_region_x
    region_offset_y = event.mouse_y - event.mouse_region_y

    loc, _, _ = obj.matrix_world.decompose()
    co = location_3d_to_region_2d(context.region, context.space_data.region_3d, loc, default=None)

    context.window.cursor_warp(co.x + region_offset_x, co.y + region_offset_y)



def update_HUD_location(self, event, offsetx=0, offsety=20):

    self.HUD_x = event.mouse_x - self.region_offset_x + offsetx
    self.HUD_y = event.mouse_y - self.region_offset_y + offsety


def draw_init(self, event, HUDx_offset=0, HUDy_offset=20):
    self.font_id = 1
    self.offset = 0


def draw_title(self, title, subtitle=None, subtitleoffset=125, HUDcolor=None, HUDalpha=0.5, shadow=True):
    if not HUDcolor:
        HUDcolor = get_prefs().modal_hud_color
    shadow = (0, 0, 0)

    scale = bpy.context.preferences.view.ui_scale * get_prefs().modal_hud_scale

    if shadow:
        blf.color(self.font_id, *shadow, HUDalpha * 0.7)
        blf.position(self.font_id, self.HUD_x - 7 + 1, self.HUD_y - 1, 0)
        blf.size(self.font_id, int(20 * scale), 72)
        blf.draw(self.font_id, "• " + title)

    blf.color(self.font_id, *HUDcolor, HUDalpha)
    blf.position(self.font_id, self.HUD_x - 7, self.HUD_y, 0)
    blf.size(self.font_id, int(20 * scale), 72)
    blf.draw(self.font_id, "» " + title)

    if subtitle:
        if shadow:
            blf.color(self.font_id, *shadow, HUDalpha / 2 * 0.7)
            blf.position(self.font_id, self.HUD_x - 7 + int(subtitleoffset * scale), self.HUD_y, 0)
            blf.size(self.font_id, int(15 * scale), 72)
            blf.draw(self.font_id, subtitle)

        blf.color(self.font_id, *HUDcolor, HUDalpha / 2)
        blf.position(self.font_id, self.HUD_x - 7 + int(subtitleoffset * scale), self.HUD_y, 0)
        blf.size(self.font_id, int(15 * scale), 72)
        blf.draw(self.font_id, subtitle)


def draw_prop(self, name, value, offset=0, decimal=2, active=True, HUDcolor=None, prop_offset=120, hint="", hint_offset=200, shadow=True):
    if not HUDcolor:
        HUDcolor = get_prefs().modal_hud_color
    shadow = (0, 0, 0)

    if active:
        alpha = 1
    else:
        alpha = 0.4

    scale = bpy.context.preferences.view.ui_scale * get_prefs().modal_hud_scale

    offset = self.offset + int(offset * scale)
    self.offset = offset


    if shadow:
        blf.color(self.font_id, *shadow, alpha * 0.7)
        blf.position(self.font_id, self.HUD_x + int(20 * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
        blf.size(self.font_id, int(11 * scale), 72)
        blf.draw(self.font_id, name)

    blf.color(self.font_id, *HUDcolor, alpha)
    blf.position(self.font_id, self.HUD_x + int(20 * scale), self.HUD_y - int(20 * scale) - offset, 0)
    blf.size(self.font_id, int(11 * scale), 72)
    blf.draw(self.font_id, name)




    if type(value) is str:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(14 * scale), 72)
            blf.draw(self.font_id, value)

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(14 * scale), 72)
        blf.draw(self.font_id, value)

    elif type(value) is bool:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(14 * scale), 72)
            blf.draw(self.font_id, str(value))

        if value:
            blf.color(self.font_id, 0.5, 1, 0.5, alpha)
        else:
            blf.color(self.font_id, 1, 0.3, 0.3, alpha)

        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(14 * scale), 72)
        blf.draw(self.font_id, str(value))

    elif type(value) is int:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(20 * scale), 72)
            blf.draw(self.font_id, "%d" % (value))

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(20 * scale), 72)
        blf.draw(self.font_id, "%d" % (value))

    elif type(value) is float:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(16 * scale), 72)
            blf.draw(self.font_id, "%.*f" % (decimal, value))

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(16 * scale), 72)
        blf.draw(self.font_id, "%.*f" % (decimal, value))


    if get_prefs().modal_hud_hints and hint:
        if shadow:
            blf.color(self.font_id, *shadow, 0.6 * 0.7)
            blf.position(self.font_id, self.HUD_x + int(hint_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(11 * scale), 72)
            blf.draw(self.font_id, "%s" % (hint))

        blf.color(self.font_id, *HUDcolor, 0.6)
        blf.position(self.font_id, self.HUD_x + int(hint_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(11 * scale), 72)
        blf.draw(self.font_id, "%s" % (hint))


def draw_info(self, text, size, offset=0, HUDcolor=None, HUDalpha=0.5, shadow=True):
    if not HUDcolor:
        HUDcolor = get_prefs().modal_hud_color
    shadow = (0, 0, 0)

    scale = bpy.context.preferences.view.ui_scale * get_prefs().modal_hud_scale

    offset = self.offset + int(offset * scale)
    self.offset = offset

    if shadow:
        blf.color(self.font_id, *shadow, HUDalpha * 0.7)
        blf.position(self.font_id, self.HUD_x + int(20 * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
        blf.size(self.font_id, int(size * scale), 72)
        blf.draw(self.font_id, text)

    blf.color(self.font_id, *HUDcolor, HUDalpha)
    blf.position(self.font_id, self.HUD_x + int(20 * scale), self.HUD_y - int(20 * scale) - offset, 0)
    blf.size(self.font_id, int(size * scale), 72)
    blf.draw(self.font_id, text)


def draw_text(self, text, x, y, size=11, offsetx=0, offsety=0, HUDcolor=None, HUDalpha=0.5, shadow=True):
    if not HUDcolor:
        HUDcolor = get_prefs().modal_hud_color
    shadow = (0, 0, 0)

    scale = bpy.context.preferences.view.ui_scale * get_prefs().modal_hud_scale

    if shadow:
        blf.color(self.font_id, *shadow, HUDalpha * 0.7)
        blf.position(self.font_id, x - offsetx * size * scale, y - 1 - offsety * size * scale, 0)
        blf.size(self.font_id, int(size * scale), 72)
        blf.draw(self.font_id, text)

    blf.color(self.font_id, *HUDcolor, HUDalpha)
    blf.position(self.font_id, x - offsetx * size * scale, y - offsety * size * scale, 0)
    blf.size(self.font_id, int(size * scale), 72)
    blf.draw(self.font_id, text)


def draw_lines2d(coords, color=(1, 1, 1), width=1, alpha=1):
    indices = [(i, i + 1) for i in range(0, len(coords), 2)]

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    shader.bind()
    shader.uniform_float("color", (*color, alpha))

    gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
    gpu.state.line_width_set(width)

    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    batch.draw(shader)



def popup_message(message, title="Info", icon="INFO", terminal=True):
    def draw_message(self, context):
        if isinstance(message, list):
            for m in message:
                self.layout.label(text=m)
        else:
            self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw_message, title=title, icon=icon)

    if terminal:
        if icon == "FILE_TICK":
            icon = "ENABLE"
        elif icon == "CANCEL":
            icon = "DISABLE"
        print(icon, title)

        if isinstance(message, list):
            print(" •", ", ".join(message))
        else:
            print(" •", message)



def draw_pil_warning(layout, needed="for decal creation"):
    if get_prefs().pil:
        pass

    elif get_prefs().pilrestart:
        box = layout.box()
        column = box.column()

        column.label(text="PIL has been installed. Restart Blender now.", icon='INFO')

    else:
        box = layout.box()
        column = box.column()
        column.label(text="PIL is needed %s. Internet connection required." % (needed), icon_value=get_icon('error'))
        column.operator("machin3.install_pil", text="Install PIL", icon="PREFERENCES")


def draw_keymap_items(kc, name, keylist, layout):
    drawn = []

    idx = 0

    for item in keylist:
        keymap = item.get("keymap")
        isdrawn = False

        if keymap:
            km = kc.keymaps.get(keymap)

            kmi = None
            if km:
                idname = item.get("idname")

                for kmitem in km.keymap_items:
                    if kmitem.idname == idname:
                        properties = item.get("properties")

                        if properties:
                            if all([getattr(kmitem.properties, name, None) == value for name, value in properties]):
                                kmi = kmitem
                                break

                        else:
                            kmi = kmitem
                            break


            if kmi:
                if idx == 0:
                    box = layout.box()

                if len(keylist) == 1:
                    label = name.title().replace("_", " ")

                else:
                    if idx == 0:
                        box.label(text=name.title().replace("_", " "))

                    label = item.get("label")

                row = box.split(factor=0.15)
                row.label(text=label)

                rna_keymap_ui.draw_kmi(["ADDON", "USER", "DEFAULT"], kc, km, kmi, row, 0)

                infos = item.get("info", [])
                for text in infos:
                    row = box.split(factor=0.15)
                    row.separator()
                    row.label(text=text, icon="INFO")

                isdrawn = True
                idx += 1

        drawn.append(isdrawn)
    return drawn



def init_status(self, context, title='', func=None):
    self.bar_orig = statusbar.draw

    if func:
        statusbar.draw = func
    else:
        statusbar.draw = draw_basic_status(self, context, title)


def draw_basic_status(self, context, title):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text=title)

        row.label(text="", icon='MOUSE_LMB')
        row.label(text="Finish")

        if context.window_manager.keyconfigs.active.name.startswith('blender'):
            row.label(text="", icon='MOUSE_MMB')
            row.label(text="Viewport")

        row.label(text="", icon='MOUSE_RMB')
        row.label(text="Cancel")

    return draw


def finish_status(self):
    statusbar.draw = self.bar_orig



def get_keymap_item(name, idname, key, alt=False, ctrl=False, shift=False, properties=[]):
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.user

    km = kc.keymaps.get(name)

    if bpy.app.version >= (3, 0, 0):
        alt = int(alt)
        ctrl = int(ctrl)
        shift = int(shift)

    if km:
        kmi = km.keymap_items.get(idname)

        if kmi:
            if all([kmi.type == key and kmi.alt is alt and kmi.ctrl is ctrl and kmi.shift is shift]):

                if properties:
                    if all([getattr(kmi.properties, name, False) == prop for name, prop in properties]):
                        return kmi
                else:
                    return kmi
    return False



def init_prefs(context):
    if context.preferences.edit.use_enter_edit_mode:
        context.preferences.edit.use_enter_edit_mode = False
