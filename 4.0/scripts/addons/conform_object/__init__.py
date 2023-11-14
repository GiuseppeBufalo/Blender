# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Conform Object",
    "author" : "Mark Kingsnorth",
    "description" : "Deform an object to the surface of another.",
    "blender" : (3, 0, 0),
    "version" : (1, 4, 5),
    "location" : "",
    "warning" : "",
    "category" : "Mesh",
    "wiki_url": "https://conform-object-docs.readthedocs.io/",
    "doc_url": "https://conform-object-docs.readthedocs.io/",
}

import bpy
from . import ui, operators, property, draw
import shutil
import os
from bpy.app.handlers import persistent, depsgraph_update_post





@persistent
def depsgraph(none):
    if hasattr(bpy.context, 'space_data'):
        enable_viewer = bpy.context.window_manager.conform_object_ui.enable_viewer
        if enable_viewer:
            draw.register(bpy.context)
        else:
            draw.unregister()


    if not hasattr(bpy.context, 'visible_objects') or not bpy.context.visible_objects:
        return
    else:

        for obj in bpy.data.objects:
            if obj.conform_object.is_grid_obj:
                # check all object modifiers in scene to see if it is being used, if not delete it.
                found = False
                for obj2 in bpy.data.objects:
                    for mod in obj2.modifiers:
                        if mod.type == "SURFACE_DEFORM" and mod.target  == obj:
                            found=True
                            break
                    if found:
                        break
                if not found:
                    lattice_object = operators.get_lattice_obj(obj)
                    if lattice_object:
                        data_to_remove = lattice_object.data
                        bpy.data.objects.remove(lattice_object)
                        bpy.data.lattices.remove(data_to_remove) 
                    data = obj.data
                    bpy.data.objects.remove(obj)
                    bpy.data.meshes.remove(data)
            elif obj.conform_object.is_conform_obj:
                grid_obj = operators.get_grid_obj(obj)
                if not obj.conform_object.is_conform_shrinkwrap and grid_obj not in obj.children:
                    # pass
                    operators.conform_undo(obj, bpy.context, remove_grid = False, set_active=False, reset_matrix=False)




def load_presets():
    """Load preset files if they have not been already"""
    presets_folder = bpy.utils.user_resource('SCRIPTS', path="presets")
    my_presets = os.path.join(presets_folder, 'operator', 'conform_object.conform')
    if not os.path.isdir(my_presets):
        my_bundled_presets = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'presets')

        # makedirs() will also create all the parent folders (like "object")
        os.makedirs(my_presets)

        # Get a list of all the files in your bundled presets folder
        files = os.listdir(my_bundled_presets)

        # Copy them
        [shutil.copy2(os.path.join(my_bundled_presets, f), my_presets) for f in files]


def register():
    operators.register()
    ui.register()
    property.register()
    

    load_presets()

    depsgraph_update_post.append(depsgraph)



def unregister():
    depsgraph_update_post.remove(depsgraph)

    property.unregister()
    operators.unregister()
    ui.unregister()
    

