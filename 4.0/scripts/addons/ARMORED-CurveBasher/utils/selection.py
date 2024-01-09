import bpy

from mathutils import Vector

from .. utils import addon
from .. utils import objects
from .. utils import transforms


def edge_to_curve(self, context):
    # Converts a selection of edges into a curve.
    # Non-linked edges will create multiple curves.

    sel_mode = context.tool_settings.mesh_select_mode[:] 

    # Vertex Mode.
    if sel_mode[0]:
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

    bpy.ops.mesh.duplicate() # Does NOT throw errors when nothing is selected.

    try:
        bpy.ops.mesh.separate(type='SELECTED')
    except RuntimeError:
        return None

    # bpy.ops.object.editmode_toggle()
    bpy.ops.object.mode_set(mode='OBJECT')
    
    context.object.select_set(False)
    context.view_layer.objects.active = context.selected_objects[-1]

    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.convert(target='CURVE')
    
    # bpy.ops.object.editmode_toggle()
    # bpy.ops.curve.spline_type_set(type='BEZIER')
    # bpy.ops.curve.handle_type_set(type='FREE_ALIGN')
    # bpy.ops.object.editmode_toggle()

    curves = context.selected_objects

    return curves


def filter_incompatible_types(self, context, selection):
    # A selection of curves is required for correct operations. This function will try
    # to convert your selections to curves or return None which will Abort the operator.

    new_selection  = set()
    curve_profiles = set()
    multi_splines  = set()

    for element in selection:

        if element.type == 'CURVE':
            if len(element.data.splines) > 1:
                multi_splines.add(element)
                if addon.debug(): print(f'element {element.name} is a multi-spline')
    
            else:
                new_selection.add(element)

                ob = element.get('geo')
                if ob is None:
                    continue
                
                ob = context.scene.objects.get(ob)
                if ob is None:
                    if addon.debug():
                        print('Missing object, clearing IDs')
                    del element['geo']
                    del element['mode']
                    del element['index']
                    element['virgin'] = True
                    continue

                if ob.get('curve') != element.name:     # The object belongs to a different curve.
                    try:
                        if addon.debug():
                            print('Geo belongs to a different curve, clearing IDs')
                        del element['geo']
                        del element['mode']
                        del element['index']
                        element['virgin'] = True
                        continue
                    except KeyError:
                        pass
                
                ob.select_set(True)
                if ob.type == 'CURVE':
                    curve_profiles.add(ob)

        elif element.type == 'MESH':
            # Kitbash is probably selected.
            try:
                curve = bpy.data.objects[element['curve']]
                curve.select_set(True)
                element.select_set(True)
                new_selection.add(curve)

            # DISCARD
            except KeyError:
                self.report({'INFO'}, 'Curve Basher\n Discarded unexpected selection type. Expected Kitbash')
                element.select_set(False)
                if element == context.object:
                    context.view_layer.objects.active = None
                # return None
    
        # DISCARD
        else:
            self.report({'INFO'}, 'Curve Basher\n Discarded unexpected selection type. Expected Curve/Edge/Kitbash')
            element.select_set(False)
            if element == context.object:
                context.view_layer.objects.active = None
            # return None
    
    # if context.object in curve_profiles:
        # if addon.debug(): print(f'Switching active from unwanted profile to curve {var}')
        # context.view_layer.objects.active = bpy.data.objects[context.object['curve']]

    for curve in multi_splines:
        if curve in curve_profiles:
            if addon.debug():
                print(f'curve {curve.name} is in Profiles set, skip')
            continue

        if addon.debug(): print(f'curve {curve.name} is NOT in profiles set >> splitting')
        split_curves = split_unlinked_splines(self, context, curve=curve)

        if split_curves:
            for curve in split_curves:
                new_selection.add(curve)
        
        # ABORT
        else:
            self.report({'ERROR'}, 'Curve Basher\n Cannot split POLY splines, aborting. Convert to BEZIER first')
            return None

    # Remove any Curve Profiles found to prevent recursion (Curve-Profiles being added to Curve-Profiles).
    new_selection = new_selection.difference(curve_profiles)

    new_selection = list(new_selection) # Convert it to a list because we might iterate through the data several times.

    # Don't think we need this but better safe than sorry.
    if not new_selection:
        self.report({'ERROR'}, 'Curve Basher\n No compatible curves in selection, aborting.')
        return None

    if addon.debug():
        print(f'Original elements: {selection}')
        print(f'Curve Profiles:    {curve_profiles}')
        print(f'Final Selection:   {new_selection}\n')
       
    return new_selection


def split_unlinked_splines(self, context, curve):
    '''
    Certain tools/operations can create a curve with multiple unlinked splines. This function creates a 
    duplicate of each unlinked spline into a new curve and deletes the original multi-spline object.
    
    Returns: single-spline curve objects (list).
    '''
    transforms.apply_transforms(curve)  # This needs ALL transforms, including scale? Do NOT swap for apply_location_rotation only.
    multi_spline = curve.data.splines

    found_incompatible = False

    # SAFETY CHECK >>
    # Splitting POLY splines is not supported yet.
    for spline in multi_spline:

        if spline.type != 'BEZIER':
            return None

    single_spline_curves = list()
        
    # for i, spline in enumerate(multi_spline):
    for spline in multi_spline:

        curve_data = bpy.data.curves.new('BezierCurve', 'CURVE')
        curve_data.dimensions = '3D'
            
        new_spline = curve_data.splines.new(type='BEZIER')

        new_points = new_spline.bezier_points
        old_points =     spline.bezier_points

        new_spline.bezier_points.add( len(spline.bezier_points) -1) # The curve already has 1 point.
        
        # Make the new spline points match the original ones.
        for new_point, old_point in zip(new_points, old_points):
            new_point.co = old_point.co

            # Handle Locations.
            new_point.handle_left.xyz   = old_point.handle_left.xyz
            new_point.handle_right.xyz  = old_point.handle_right.xyz
            
            # Handle Types.
            new_point.handle_left_type  = old_point.handle_left_type
            new_point.handle_right_type = old_point.handle_right_type

        # Create a new curve object to house the duplicate spline data.
        new_curve = bpy.data.objects.new('BezierCurve', curve_data)
        # bpy.data.collections['Collection'].objects.link(new_curve)
        bpy.context.collection.objects.link(new_curve)
        new_curve.select_set(True)
        
        # No longer needed if we just apply transforms before duplicating the original curve.
        # Match the new curves to the original curve transforms.
        # new_curve.location       = curve.location
        # new_curve.scale          = curve.scale
        # new_curve.rotation_euler = curve.rotation_euler
        
        single_spline_curves.append(new_curve)
    
    temp_mesh = curve.data
    bpy.data.objects.remove(curve)
    bpy.data.curves.remove(temp_mesh)

    if not context.object:
        context.view_layer.objects.active = single_spline_curves[-1]

    return single_spline_curves


def split_unlinked_splines_legacy(self, context, curve):
    # Separates unconnected splines into individual curve objects (one spline per object).

    context.view_layer.objects.active = curve

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')

    while len(curve.data.splines) > 1:

        for point in curve.data.splines[0].bezier_points:
            point.select_control_point = True
        
        bpy.ops.curve.separate()
        
    bpy.ops.object.mode_set(mode='OBJECT')