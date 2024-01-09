import bpy
import blf

def close(handle):
    bpy.context.window_manager.my_toolqt.running_qt = 0
    if "QuickTexture" in bpy.data.collections:
        bpy.data.collections["QuickTexture"].hide_viewport = True
        bpy.data.collections["QuickTexture"].hide_render = True
    if handle:
        bpy.types.SpaceView3D.draw_handler_remove(handle, "WINDOW")
    return {"FINISHED"}

def draw_text(text, regX, regY, color, row, offset, align, size):
    text = str(text)
    height = blf.dimensions(0, 'I')[1]*1.3
    spacing = blf.dimensions(0, '___')[0]

    if align == 'Center':
        blf.position(0, regX/2 + offset, regY - height * row, 0)
    elif align == 'Top':
        blf.position(0, regX/2 + offset, regY - height * row, 0)
    elif align == 'Left':
        blf.position(0, spacing + offset, height * row*1.5, 0)
    elif align == 'Right':
        blf.position(0, regX - spacing + offset, height * row*1.5, 0)
    elif align == 'Bottom':
        blf.position(0, regX/2 + offset, height * row*1.5, 0)

    if size:
        blf.size(
            0,
            bpy.context.preferences.addons[__package__].preferences.text_size * 0.9,
        )
    else:
        blf.size(
            0,
            bpy.context.preferences.addons[__package__].preferences.text_size,
        )

    if color == 0:
        blf.color(
            0,
            bpy.context.preferences.addons[__package__].preferences.col_primary[0],
            bpy.context.preferences.addons[__package__].preferences.col_primary[1],
            bpy.context.preferences.addons[__package__].preferences.col_primary[2],
            bpy.context.preferences.addons[__package__].preferences.col_primary[3],
        )
    elif color == 1:
        blf.color(
            0,
            bpy.context.preferences.addons[__package__].preferences.col_secondary[0],
            bpy.context.preferences.addons[__package__].preferences.col_secondary[1],
            bpy.context.preferences.addons[__package__].preferences.col_secondary[2],
            bpy.context.preferences.addons[__package__].preferences.col_secondary[3],
        )
    else:
        blf.color(
            0,
            bpy.context.preferences.addons[__package__].preferences.col_tertiary[0],
            bpy.context.preferences.addons[__package__].preferences.col_tertiary[1],
            bpy.context.preferences.addons[__package__].preferences.col_tertiary[2],
            bpy.context.preferences.addons[__package__].preferences.col_tertiary[3],
        )
    blf.draw(0, text)