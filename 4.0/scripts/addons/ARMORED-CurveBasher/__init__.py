bl_info = {
    'name'        : 'Curve Basher',
    'description' : 'Curve Generators and Kitbashing Tools',
    'author'      : 'Armored Colony',
    'version'     : (1, '3 (Rev 9) [BOREALOPELTA]',),
    'blender'     : (2, 90),
    # 'location'    : 'View3D > Add > Mesh',
    # 'warning'     : 'Whatever', # Used for warning icon and text in addons panel.
    # 'wiki_url'    : 'www.armoredColony.com\n', # This should be for Documentation.
    'category'    : 'ARMORED',
}


import bpy
from . utils import modules
from . utils import properties


# FOLDERS WITH CLASSES THAT NEED TO BE REGISTERED IN BLENDER (operators, panels, etc)
sub_folders = [
    'config', # Register first and unregister last for safety (contains the addon preferences class).
    'ui',
    'operators_internal',
    'operators',
    'customize',
]

def register():
    for sub_folder in sub_folders:
        modules.register_all_modules(sub_folder, action='register', debug=False)
    properties.register()


def unregister():
    for sub_folder in sub_folders:
        modules.register_all_modules(sub_folder, action='unregister', debug=False)
    properties.unregister()