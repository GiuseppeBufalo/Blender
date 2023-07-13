################################################################################################################
### This is the main class for orchestrating the decoration of plating and greebles.
################################################################################################################

import bpy
import bmesh
from math import radians

from ..plating_gen.plating_functions import plating_gen_exec
from ..greeble_gen.greeble_functions import greeble_gen_exec
from ..utils import uvcalc_smart_project
import numpy as np
import sys

class AbstractDecorator:
    """Abstract class to define distributing a number of a number of points for an object."""

    def decorator_name():
        """Name of Decorator"""
        pass

    def decorate(self, level, face_ids, obj, bm, context):
        """Decorate the object with a pattern."""
        return []

    def draw(preference, layout):
        """Render User Interface Options."""
        pass

    def get_selection_types():
        """Get the valid types of selection options this decorator will process for other levels."""
        return []

    def set_selection(self, level, obj, bm):
        """Set the desired selection for when processing a level."""
        pass

    def smart_project(self):
        """Whether this decorator uses smart project."""
        return False


def get_decorator(decorator_type):
    """Get the relevant decorator based on the class name."""
    for subclass in AbstractDecorator.__subclasses__():
        if subclass.__name__ == decorator_type:
            return subclass()
    return None

def get_selection_types(decorator_type):
    """Get all possible selection types for a given decorator."""
    for subclass in AbstractDecorator.__subclasses__():
        if subclass.__name__ == decorator_type:
            return getattr(subclass, 'get_selection_types')()
    return []

# ###
# ### New Decorators go below.
# ###
class PlatingGeneratorDecorator(AbstractDecorator):
    """"Add Plates"""

    remaining_face_ids = []

    def __init__(self):
        self.remaining_face_ids = []

    def decorator_name():
        return "Plates"

    def decorate(self, level, face_ids, obj, bm, context):
        props = level.plating_props
        if 'face_was_not_selected_prop' in bm.faces.layers.int:
            face_was_not_selected_prop = bm.faces.layers.int.get('face_was_not_selected_prop')
        else:
            face_was_not_selected_prop = bm.faces.layers.int.new('face_was_not_selected_prop')

        # extrude any boundary edges to give thickness for the algorithm to calculate on
        bmesh.ops.extrude_edge_only(bm, edges=[e for e in bm.edges if e.is_boundary])
        bm.faces.ensure_lookup_table()

        #assume all faces were not selected to start with.
        for face_id in face_ids:
            try:
                bm.faces[face_id][face_was_not_selected_prop] = 1
            except IndexError:
                pass

        # determine whether the faces were selected based on pattern type.  Some pattern types (e.g. Selecteded Edges) do not expect faces to be selected.
        if props.pattern_type in {'1', '5'}:
            for f in bm.faces:
                f[face_was_not_selected_prop] = 0
        else:
            for f in bm.faces:
                f[face_was_not_selected_prop] = 0 if f[face_was_not_selected_prop] else 1
                f.select_set(not f[face_was_not_selected_prop])

        # Execute the plating generator code.
        props.update_draw_only = False
        plating_gen_exec(props, obj, bm, context, seed=obj.plating_generator.master_seed)

        face_was_not_selected_prop = bm.faces.layers.int.get('face_was_not_selected_prop')
        unselected_faces = [f for f in bm.faces if f[face_was_not_selected_prop] == 1]
        
        # also extend the region if bevels were applied.
        if props.groove_bevel_amount > 0:
            for i in range(0, props.groove_bevel_segments):
                extended_region = bmesh.ops.region_extend(bm, geom=unselected_faces, use_faces=True)['geom']
                for f in extended_region:
                    unselected_faces.append(f)

        selection_level = int(level.selection_level)
        if selection_level == 0:
            # get the face groups of this selection.
            face_group_ids = find_face_group_ids(bm)                

            rng = np.random.RandomState(level.selection_amount_seed + obj.plating_generator.master_seed)
            chance = 1 - (level.selection_amount * 0.01)
            fg_refs = range(0, len(face_group_ids))
            random_fgs = rng.choice(fg_refs, size = int(chance * len(face_group_ids)), replace=False)
            random_fgs = [face_group_ids[fg_ref] for fg_ref in random_fgs]

            bm.faces.ensure_lookup_table()
            faces_to_delete = []
            for fg in random_fgs:
                for f_index in fg:
                    bm.faces[f_index].select_set(False)
                    faces_to_delete.append(bm.faces[f_index])

            

            linked_faces = select_linked(bm, faces_to_delete)

            bmesh.ops.delete(bm, geom=linked_faces, context='FACES')
            bm.faces.ensure_lookup_table()
    
        

        return unselected_faces

    def get_selection_types():
        return [('0', 'Tops',''),
                ('1', 'Sides','')]

    def set_selection(self, level, obj, bm):
        # we need to determine whether tops or sides (or both) are needed.
        top_faces = [f for f in bm.faces if f.select]
        side_faces = [f for f in bm.faces if not f.select]

        for f in bm.faces:
            f.select_set(False)

        if "0" in level.selection_type:
            for f in top_faces:
                f.select_set(True)

        if "1" in level.selection_type:
            for f in side_faces:
                f.select_set(True)

        if level.select_remaining:
            for f in bm.faces:
                if f.select:
                    f.select_set(f.index not in self.remaining_face_ids)

        # weight by percentage
        if level.selection_amount < 100:

            # get the face groups of this selection.
            face_group_ids = find_face_group_ids(bm)                

            rng = np.random.RandomState(level.selection_amount_seed + obj.plating_generator.master_seed)
            chance = 1 - (level.selection_amount * 0.01)
            fg_refs = range(0, len(face_group_ids))
            random_fgs = rng.choice(fg_refs, size = int(chance * len(face_group_ids)), replace=False)
            random_fgs = [face_group_ids[fg_ref] for fg_ref in random_fgs]

            bm.faces.ensure_lookup_table()
            for fg in random_fgs:
                for f_index in fg:
                    bm.faces[f_index].select_set(False)



        self.remaining_face_ids.extend([f.index for f in bm.faces if f.select])
        self.remaining_face_ids = list(set(self.remaining_face_ids))

    def smart_project(self):
        return True

class GreebleDecorator(AbstractDecorator):
    """"Add Greebles"""

    def decorator_name():
        return "Greebles"

    def decorate(self, level, face_ids, obj, bm, context):
        props = level.greeble_props
        #assume all faces were not selected as we are going to run over everything
        if 'face_was_not_selected_prop' in bm.faces.layers.int:
            face_was_not_selected_prop = bm.faces.layers.int.get('face_was_not_selected_prop')
        else:
            face_was_not_selected_prop = bm.faces.layers.int.new('face_was_not_selected_prop')

        for f in bm.faces:
            f[face_was_not_selected_prop] = 1

        if len([f for f in bm.faces if f.select]):
            greeble_gen_exec(props, obj, bm, context, seed=obj.plating_generator.master_seed)

        return [f for f in bm.faces if f[face_was_not_selected_prop] == 1]


    def get_selection_types():

        return [('0', 'All','')]

    def set_selection(self, level, obj, bm):
        for f in bm.faces:
            f.select_set(True)

        # weight by percentage
        if level.selection_amount < 100:

            # get the face groups of this selection.
            face_group_ids = find_face_group_ids(bm)                

            rng = np.random.RandomState(level.selection_amount_seed + obj.plating_generator.master_seed)
            chance = 1 - (level.selection_amount * 0.01)
            fg_refs = range(0, len(face_group_ids))
            random_fgs = rng.choice(fg_refs, size = int(chance * len(face_group_ids)), replace=False)
            random_fgs = [face_group_ids[fg_ref] for fg_ref in random_fgs]

            bm.faces.ensure_lookup_table()
            for fg in random_fgs:
                for f_index in fg:
                    bm.faces[f_index].select_set(False)

def find_face_group_ids(bm_in):
    """Finds groups of linked faces"""
    bm = bm_in.copy()

    for f in bm.faces:
        f.tag = False

    # We use quite a bit of recursion so we lift the recursion limit here.
    limit_temp = sys.getrecursionlimit()
    sys.setrecursionlimit(10**6) 
    try:
        face_groups = []
        for f in bm.faces:
            potential_face_group = []
            calc_face_groups(f, potential_face_group)
            if len(potential_face_group) > 0:
                face_groups.append(potential_face_group)


        face_group_ids = []
        for fg in face_groups:
            face_group_ids.append([f.index for f in fg if f.is_valid])

    finally:
        sys.setrecursionlimit(limit_temp) 
        bm.free()




    return face_group_ids


def select_linked(bm_in, faces):
    """Select all faces linked to this one"""
    bm = bm_in.copy()

    face_ids = [f.index for f in faces]

    for f in bm.faces:
        f.tag = False
    
    linked_faces = []
    # We use quite a bit of recursion so we lif t the recursion limit here.
    limit_temp = sys.getrecursionlimit()
    sys.setrecursionlimit(10**6) 
    try:
        bm.faces.ensure_lookup_table()
        for f_id in face_ids:
            f = bm.faces[f_id]
            face_group = []
            calc_face_groups(f, face_group, select_check=False)
            linked_faces.extend(face_group)

        linked_faces = list(set(linked_faces))
        linked_faces = [bm_in.faces[f.index] for f in linked_faces]

    finally:
        sys.setrecursionlimit(limit_temp) 
        bm.free()



    return linked_faces



def calc_face_groups(f, potential_face_group, select_check=True):
    """Recursive function to find groups of linked faces/"""
    if select_check and (not f.select or f.tag):
        return
    elif f.tag:
        return
    
    f.tag = True
    potential_face_group.append(f)

    link_faces = [linked_face for e in f.edges
            for linked_face in e.link_faces if linked_face is not f]

    for link_face in link_faces:
        calc_face_groups(link_face, potential_face_group, select_check=select_check)

    return potential_face_group


def decorate(obj, context):
    """This will take the given object and use the associated levels to decorate it with."""

    context.view_layer.update()

    # get the levels, the parent object (object that is the target for generating plates.)
    levels = obj.plating_generator.levels
    parent_object = obj.plating_generator.parent_obj
    bms = []
    bms_to_smart_project = []

    # initiate decorator map.
    levels_to_decorators = {}
    for level in levels:
        levels_to_decorators[level.name] = get_decorator(level.type)

    i = 0
    for level in levels:
        if not level.is_enabled or not level.selection_level:
            # if the level is not enabled or we do not have a selecton level, just add an empty bmesh.
            bms.append(bmesh.new())
            continue

        #get the relevant properties, whatever we may use.
        try:
            # the selection level determines whether we need to reference another level when processing.
            selection_level = int(level.selection_level)
            selected_edge_indexes = []

            decorator = levels_to_decorators[level.name]

            # if we are at the zero level, we are just referencing the main object. Otherwise get the preferred level and process on that.
            if selection_level == 0:
                bm = bmesh.new()
                bm.from_mesh(parent_object.data)
                face_ids = [face_ref.face_id for face_ref in obj.plating_generator.face_ids]
                edge_ids = [edge_ref.edge_id for edge_ref in obj.plating_generator.edge_ids]
                bm.faces.ensure_lookup_table()
                
                for f in bm.faces:
                    f.select_set(False)
                for face_id in face_ids:
                    try:
                        bm.faces[face_id].select_set(True)
                    except IndexError:
                        pass
                bm.edges.ensure_lookup_table()
                for e in bm.edges:
                    e.select_set(False)
                for edge_id in edge_ids:
                    try:
                        bm.edges[edge_id].select_set(True)
                    except IndexError:
                        pass
            else:
                # get the required level, which should be one below it.
                index = selection_level - 1
                if index >= len(levels):
                    continue
                target_level = levels[index]
                try:
                    bm = bms[index].copy()
                except IndexError:
                    bm = bms[i-1].copy()

                # target_decorator = get_decorator(target_level.type)
                target_decorator = levels_to_decorators[target_level.name]


                # set the selection based on what the decorator wants to do.
                target_decorator.set_selection(level, obj, bm)

            # weight by min face area
            if level.min_selection_area > 0:
                for f in bm.faces:
                    if f.select and f.calc_area() <= level.min_selection_area:
                        f.select_set(False)

            # re-get the associated face ids.
            face_ids = [f.index for f in bm.faces if f.select]

            # mark faces that were not selected.
            if 'face_was_not_selected_prop' in bm.faces.layers.int:
                face_was_not_selected_prop = bm.faces.layers.int.get('face_was_not_selected_prop')
            else:
                face_was_not_selected_prop = bm.faces.layers.int.new('face_was_not_selected_prop')

            # Now decorate the object, returning any faces that may need to be deleted.
            unselected_faces = []
            if obj.plating_generator.generate_uvs and decorator.smart_project():
                unselected_faces = decorator.decorate(level, face_ids, obj, bm, context)
                bms_to_smart_project.append(bm)
            else:
                unselected_faces = decorator.decorate(level, face_ids, obj, bm, context)  

            # delete the faces and also remove the not selected property from the layers.
            bmesh.ops.delete(bm, geom=unselected_faces, context='FACES')
            bm.faces.layers.int.remove(face_was_not_selected_prop)

            bms.append(bm)
        finally:
            
            i+=1

    # hide any levels by clearing the data
    for i in range(0, len(levels)):
        level = levels[i]
        bm = bms[i]
        if not level.visible:
            bm.clear()

    # now start processing the overall object, merging all the bmeshes together.
    overall_bm = bmesh.new()

    # consolidate smart projection first.
    for bm in bms_to_smart_project:
        mesh = bpy.data.meshes.new("Plating Temp Mesh")
        bm.to_mesh(mesh)
        overall_bm.from_mesh(mesh)
        bm.free()
        bpy.data.meshes.remove(mesh)

    overall_bm.to_mesh(obj.data)
    uvcalc_smart_project.smart_project(obj.data, projection_limit=obj.plating_generator.uv_projection_limit)
    overall_bm.clear()
    overall_bm.from_mesh(obj.data)

    # add the remaining meshes that do not need smart projection.
    for bm in bms:
        if bm not in bms_to_smart_project:
            mesh = bpy.data.meshes.new("Plating Temp Mesh")
            bm.to_mesh(mesh)
            overall_bm.from_mesh(mesh)
            bm.free()
            bpy.data.meshes.remove(mesh)

    # commit all this to the object.
    overall_bm.to_mesh(obj.data)


def get_decorator_method_items():
    """Get all possible decorator items in a format Blender understands for enumerators."""
    items = []
    i = 0
    for subclass in AbstractDecorator.__subclasses__():
        items.append((subclass.__name__, subclass.decorator_name(),''))
        i+=1
    return items

# global items reference needed by Blender.
decorator_method_items  = get_decorator_method_items()