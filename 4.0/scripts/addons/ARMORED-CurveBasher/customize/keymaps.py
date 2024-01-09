import bpy
from .. utils import addon


addon_keymaps = []

def create_keymaps():

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon.keymaps    # kc shold not go into .keymaps, but its a calculater risk.

    def create_kmi(category, idname, key, event, ctrl=False, alt=False, shift=False, active=True):
        kmi = km.keymap_items.new(idname, key, event, ctrl=ctrl, alt=alt, shift=shift)
        # kmi.properties.name = idname 
        kmi.active = active
        addon_keymaps.append((category, km, kmi))
        return kmi

    # USE EXISTING CATEGORIES!!!

    cat = 'Object Mode'
    km = kc[cat] if kc.get(cat) else kc.new(name=cat)

    create_kmi(cat, idname='curvebash.kitbasher_modal', key='J', event='PRESS')
    create_kmi(cat, idname='curvebash.raycast_curve', key='C', event='PRESS')
    # create_kmi(cat, idname='object.curvebash_wire_generator', key='W', event='PRESS', ctrl=True, shift=True)

    cat = 'Curve'
    km = kc[cat] if kc.get(cat) else kc.new(name=cat)

    create_kmi(cat, idname='curvebash.kitbasher_modal', key='J', event='PRESS')
    create_kmi(cat, idname='curvebash.raycast_curve', key='C', event='PRESS')

    cat = 'Mesh'
    km = kc[cat] if kc.get(cat) else kc.new(name=cat)

    create_kmi(cat, idname='curvebash.kitbasher_modal', key='J', event='PRESS')


def destroy_keymaps():
    for _, km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register():
    create_keymaps()


def unregister():
    destroy_keymaps()