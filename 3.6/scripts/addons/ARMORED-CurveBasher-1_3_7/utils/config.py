import bpy
import os

# from .. utils import addon

# from .. customize import matcaps, keymaps, themes, system
from configparser import ConfigParser

def create_config_file():
    config = ConfigParser()
    filename = 'Curve_Basher_prefs.ini'
    filepath = os.path.join(bpy.utils.user_resource('SCRIPTS', 'ADDONS', create=True), filename)
    # print(f'filepath: {filepath}')

    config.add_section('keymap')
    config.add_section('matcap')
    config.add_section('theme')
    config.add_section('system')
    config.add_section('operator_refresh')

def load_config():
    config.read(filepath)
    for section in config.sections():
        # print(f'SECTION {section}')

        for (prop, _) in config.items(section):
            val = config.getboolean(section, prop)
            state = 'ENABLED' if val else 'DISABLED'
            
            # In case the the preferences reset because the addon was disabled and enabled again.
            if state != getattr(get_prefs(), prop):
                setattr(get_prefs(), prop, state)
                print(f'config {prop} different blender')
            else:
                print(f'config {prop} matches blender')


create_config_file()