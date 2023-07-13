import bpy
import blf
import os

from .. utils import addon
from .. utils.colors import *


dpi = 72
shadow = True

# FOR ADDON UI TITLE
font_size_title = 25

# FOR SINGLE COLUMN UI LINE
font_size_string = 14

# FOR 3 COLUMN UI LINE
# font_size_body = 11
font_size_prop = 11
font_size_val  = 16
font_size_key  = 11

# DEFAULT FONT
font_id = 1


def get_scale():
	sys_scale = bpy.context.preferences.system.ui_scale if addon.get_prefs().system_scale else 1
	hud_scale = addon.get_prefs().hud_scale
	return sys_scale * hud_scale


def draw_title(self, text):
	# Only the title uses a custom font.

	# font_path = os.path.join(addon.get_path(), 'resources', 'fonts', 'Akrobat-Bold.ttf')

	# if os.path.isfile(font_path):
	# 	font_id = blf.load(font_path)
	# else:
	# 	font_id = 0 # default font
	
	font_id = 1		# FORCE IT FOR NOW

	blf.size(font_id, int(font_size_title * get_scale()), dpi) 

	cursor_offset_x = 30  # positive means right
	cursor_offset_y = 0   # negative means down

	x = self.mouse_x + cursor_offset_x
	y = self.mouse_y + cursor_offset_y * get_scale()

	if shadow:
		c = 1  # Shadow Offset and other clever stuff.
	else:
		c = 0

	# If Shadow is True we draw the UI twice (first for shadow, second for normal color).
	for i in range(c+1):
		if c == 1:
			blf.color(font_id, *SHADOW_COLOR, 0.5)
			c = 0
		else:
			blf.color(font_id, *TITLE_COLOR,  1.0)

		blf.position(font_id, (x -i), (y + i), 0)
		blf.draw(font_id, text)
	

def draw_string(self, text):
	# Draw a single line of text. I use this to draw the name of the kitbash.

	cursor_offset_x =  30  					# positive means right. (prev 22 to account for apostrophe)
	cursor_offset_y = -30  * get_scale()	# negative means down.

	x = self.mouse_x + cursor_offset_x
	y = self.mouse_y + cursor_offset_y

	blf.size(font_id, int(font_size_string  * get_scale()), dpi) 

	if shadow:
		so = 1  # Shadow Offset and other clever stuff.
	else:
		so = 0

	# If Shadow is True we draw the UI twice (first for shadow, second for normal color).
	for i in range(so+1):
		if so == 1:
			blf.color(font_id, *SHADOW_COLOR, 0.5)
			so = 0
		else:
			blf.color(font_id, *WHITE,  1.0)

		blf.position(font_id, (x -i), (y + i), 0)
		blf.draw(font_id, text)


def draw_body(self, string_matrix, cursor_offset_x=30, cursor_offset_y=-65):
	# Run the draw_complex_line function as many times as required to draw the full matrix of strings.

	blf.size(font_id, int(font_size_prop * get_scale()), dpi)
	line_height = blf.dimensions(font_id, 'M')[1] * 2.2

	offset_y = 0
	for compound_string in string_matrix:
		if compound_string == 'SEPARATOR':
			offset_y -= 10 * get_scale()
		else:
			draw_complex_line(self, compound_string, offset_y, cursor_offset_x, cursor_offset_y)
			offset_y -= line_height


def draw_complex_line(self, compound_string, offset_y=0, cursor_offset_x=30, cursor_offset_y=-65, prop_width=80, val_width=110, fs_offset=0):
	# Draw a single like of packed elements with the format (prop, val, key).

	# cursor_offset_x =  30  # positive means right.
	# cursor_offset_y = -65  # negative means down.
	
	x = self.mouse_x + cursor_offset_x
	y = self.mouse_y + cursor_offset_y * get_scale()

	if shadow:
		so = 1  # Shadow Offset.
	else:
		so = 0

	# If Shadow is True we draw the UI twice (first for shadow, second for normal color).
	for i in range(so+1):
		prop, val, key = compound_string

		# Draw Property
		if so == 1:
			blf.color(font_id, *SHADOW_COLOR, 0.5)
		else:
			blf.color(font_id, *WHITE,  1.0)

		blf.size(font_id, int(font_size_prop * get_scale()) + fs_offset, dpi)

		blf.position(font_id, (x - i), (y + offset_y + i), 0)
		blf.draw(font_id, str(prop))

		# Draw Value
		if so == 1:
			blf.color(font_id, *SHADOW_COLOR, 0.5)
		else:
			if type(val) == str:
				if val in {'PROFILE', 'ARRAY', 'KITBASH'}:
					blf.color(font_id, *HIGHLIGHT_COLOR,  1.0)
				else:
					blf.color(font_id, *WHITE,  1.0)

			elif type(val) == bool and val == True:
				blf.color(font_id, *TRUE_COLOR, 1.0)

			elif type(val) == bool and val == False:
				blf.color(font_id, *FALSE_COLOR, 1.0)
			
			else:
				blf.color(font_id, *WHITE,  1.0)
		
		if type(val) == float:
			val = '%.3f'%(val)

		blf.size(font_id, int(font_size_val * get_scale()), dpi)
		blf.position(font_id, (x - i + prop_width * get_scale()), (y + offset_y + i), 0)
		blf.draw(font_id, str(val))

		# Draw Keymap
		if so == 1:
			blf.color(font_id, *SHADOW_COLOR, 0.5)
		else:
			blf.color(font_id, *WHITE,  0.5)

		blf.size(font_id, int(font_size_key * get_scale()), dpi)
		blf.position(font_id, (x - i + prop_width * get_scale() + val_width * get_scale()), (y + offset_y + i), 0)
		blf.draw(font_id, str(key))

		so = 0

def draw_preset_keymap(self, offset_y=35, cursor_offset_x=30, cursor_offset_y=-65, prop_width=80, val_width=110):
	# Added this specific keymap separately so advanced users can hide it and make the HUD cleaner.
	# Addon Preference to Show/Hide this keymap has NOT been implemented yet.

	# cursor_offset_x =  30  # positive means right.
	# cursor_offset_y = -65  # negative means down.
	
	x = self.mouse_x + cursor_offset_x
	y = self.mouse_y + cursor_offset_y * get_scale()

	if shadow:
		so = 1  # Shadow Offset.
	else:
		so = 0
	
	key = 'Scroll Up/Down'

	for i in range(so+1):

		if so == 1:
			blf.color(font_id, *SHADOW_COLOR, 0.5)
		else:
			blf.color(font_id, *WHITE,  0.5)

		blf.size(font_id, int(font_size_key * get_scale()), dpi)
		blf.position(font_id, (x - i + prop_width * get_scale() + val_width * get_scale()), (y + offset_y * get_scale() + i), 0)
		blf.draw(font_id, str(key))

		so = 0