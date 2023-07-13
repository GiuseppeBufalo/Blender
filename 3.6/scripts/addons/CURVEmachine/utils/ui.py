import bpy
from mathutils import Vector
import rna_keymap_ui
from bl_ui.space_statusbar import STATUSBAR_HT_header as statusbar
from bpy_extras.view3d_utils import region_2d_to_location_3d 


icons = None


def get_icon(name):
    global icons

    if not icons:
        from .. import icons

    return icons[name].icon_id



def init_cursor(self, event, offsetx=20, offsety=20):
    self.last_mouse_x = event.mouse_x
    self.last_mouse_y = event.mouse_y

    self.region_offset_x = event.mouse_x - event.mouse_region_x
    self.region_offset_y = event.mouse_y - event.mouse_region_y

    self.HUD_x = event.mouse_x - self.region_offset_x + offsetx
    self.HUD_y = event.mouse_y - self.region_offset_y + offsety


def wrap_cursor(self, context, event, x=False, y=False):
    if x:
        if event.mouse_region_x <= 0:
            context.window.cursor_warp(context.region.width + self.region_offset_x - 10, event.mouse_y)

        if event.mouse_region_x >= context.region.width - 1:  # the -1 is required for full screen, where the max region width is never passed
            context.window.cursor_warp(self.region_offset_x + 10, event.mouse_y)

    if y:
        if event.mouse_region_y <= 0:
            context.window.cursor_warp(event.mouse_x, context.region.height + self.region_offset_y - 10)

        if event.mouse_region_y >= context.region.height - 1:
            context.window.cursor_warp(event.mouse_x, self.region_offset_y + 100)



def get_zoom_factor(context, depth_location, scale=10, ignore_obj_scale=False):

    if scale == 1:
        scale = 1.1

    center = Vector((context.region.width / 2, context.region.height / 2))
    offset = center + Vector((scale, 0))

    center_3d = region_2d_to_location_3d(context.region, context.region_data, center, depth_location)
    offset_3d = region_2d_to_location_3d(context.region, context.region_data, offset, depth_location)


    if not ignore_obj_scale and context.active_object:
        mx = context.active_object.matrix_world.to_3x3()
        zoom_vector = mx.inverted_safe() @ Vector(((center_3d - offset_3d).length, 0, 0))
        return zoom_vector.length

    return (center_3d - offset_3d).length



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
            print(" »", ", ".join(message))
        else:
            print(" »", message)




def draw_keymap_items(kc, name, keylist, layout, skip_box_label=False):
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

                label = item.get("label", None)

                if not label:
                    label = name.title().replace("_", " ")

                if len(keylist) > 1:
                    if idx == 0 and not skip_box_label:
                        box.label(text=name.title().replace("_", " "))

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


def get_event_icon(event_type):

    if 'MOUSE' in event_type:
        return 'MOUSE_LMB' if 'LEFT' in event_type else 'MOUSE_RMB' if 'RIGHT' in event_type else 'MOUSE_MMB'

    elif 'EVT_TWEAK' in event_type:
        return f"MOUSE_{'LMB' if event_type.endswith('_L') else 'RMB' if event_type.endswith('_R') else 'MMB'}_DRAG"

    else:
        return f'EVENT_{event_type}'


def get_keymap_item(name, idname, key=None, alt=False, ctrl=False, shift=False, properties=[], iterate=False):

    def return_found_item():
        found = True if key is None else all([kmi.type == key and kmi.alt is alt and kmi.ctrl is ctrl and kmi.shift is shift])

        if found:
            if properties:
                if all([getattr(kmi.properties, name, False) == prop for name, prop in properties]):
                    return kmi
            else:
                return kmi

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.user

    km = kc.keymaps.get(name)

    if bpy.app.version >= (3, 0, 0):
        alt = int(alt)
        ctrl = int(ctrl)
        shift = int(shift)


    if km:

        if iterate:
            kmis = [kmi for kmi in km.keymap_items if kmi.idname == idname]

            for kmi in kmis:
                r = return_found_item()

                if r:
                    return r


        else:
            kmi = km.keymap_items.get(idname)

            if kmi:
                return return_found_item()




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



def navigation_passthrough(event, alt=True, wheel=False):
    if alt and wheel:
        return event.type in {'MIDDLEMOUSE'} or event.type.startswith('NDOF') or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'} and event.value == 'PRESS') or event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}
    elif alt:
        return event.type in {'MIDDLEMOUSE'} or event.type.startswith('NDOF') or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'} and event.value == 'PRESS')
    elif wheel:
        return event.type in {'MIDDLEMOUSE'} or event.type.startswith('NDOF') or event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}
    else:
        return event.type in {'MIDDLEMOUSE'} or event.type.startswith('NDOF')


def scroll_up(event, wheel=True, key=False):
    up_key = 'ONE'

    if event.value == 'PRESS':
        if wheel and key:
            return event.type in {'WHEELUPMOUSE', up_key}
        elif wheel:
            return event.type in {'WHEELUPMOUSE'}
        else:
            return event.type in {up_key}


def scroll_down(event, wheel=True, key=False):
    down_key = 'TWO'

    if event.value == 'PRESS':
        if wheel and key:
            return event.type in {'WHEELDOWNMOUSE', down_key}
        elif wheel:
            return event.type in {'WHEELDOWNMOUSE'}
        else:
            return event.type in {down_key} and event.value == 'PRESS'


def get_mousemove_divisor(event, normal=10, shift=100, ctrl=10, sensitivity=1):
    
    divisor = shift if event.shift else ctrl if event.ctrl else normal
    ui_scale = bpy.context.preferences.system.ui_scale

    return divisor * ui_scale * sensitivity
