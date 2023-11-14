
#Some function i use sometimes if context override do not work 

import bpy
import copy 
from mathutils import Euler, Vector, Color

class mode_override(object):
    """support for selection/active & also mode, i don't think that classic override support mode?"""

    api_convert = {
        "OBJECT"        : "OBJECT"       , 
        "EDIT_MESH"     : "EDIT"         , 
        "SCULPT"        : "SCULPT"       , 
        "PAINT_VERTEX"  : "VERTEX_PAINT" , 
        "PAINT_WEIGHT"  : "WEIGHT_PAINT" , 
        "PAINT_TEXTURE" : "TEXTURE_PAINT",
        }

    def __init__(self, selection=[], active=None, mode="",):
        self._selection, self._active, self._mode = bpy.context.selected_objects, bpy.context.object, bpy.context.mode #should prolly save obj by name to avoid potential crash?
        self.selection, self.active, self.mode = selection, active, mode
        return None 

    def __enter__(self,):
        #deselect
        for o in self._selection:
            o.select_set(state=False)
        #select new 
        for o in self.selection:
            o.select_set(state=True)
        #set active
        bpy.context.view_layer.objects.active = self.active
        #set mode 
        try: #this is utterly ridiculous, this operator below might throw an error that there's no active object, even if WE DEFINED ONE RIGHT ABOVE.. WTFF
            bpy.ops.object.mode_set(mode=self.api_convert[self.mode])
        except Exception as e:
            print("an error occured")
            print(e)
        return None 

    def __exit__(self,*args):
        #deselect
        for o in self.selection:
            o.select_set(state=False)
        #select old
        for o in self._selection:
            o.select_set(state=True)
        #set active
        bpy.context.view_layer.objects.active = self._active
        #set mode 
        try:
            bpy.ops.object.mode_set(mode=self.api_convert[self._mode])
        except Exception as e:
            print("an error occured")
            print(e)
        return None 


class attributes_override(object):
    """temporary set attrs from given list of instructions [object,attr_name,temporary_value],[..]] 
    we will use getattr/setattr on these instructions upon enter/exit"""

    def serialize_storage(self,):
        """naive serialization attempt on bpy types, we might need to implement new types later"""
        
        def serialize_element(e):

            #manual serialization?
            #if (type(e) in [Euler, Vector, Color, bpy.types.bpy_prop_array]):
            #    return e[:] 
            #return e
                
            #deepcopy method? perhaps not all types implemented __deep_copy__
            return copy.deepcopy(e)

        try:    
            for i,storage in enumerate(self.old_val.copy()):
                self.old_val[i][2] = serialize_element(storage[2])
        except:
            print("Scatter5.override_utils.attributes_override.serialize_storage() -> SERIALIZATION FAILED")

        return None 

    def __init__(self, *args, enable=True, serialize=True):

        #instances attributes
        self.enable = enable
        self.new_val = [] #== instructions
        self.old_val = [] #== storage purpose

        #only if user enables it
        if (not self.enable):
            return None

        #fill instructions/storage lists
        for o,a,v in args: #o,a,v == object,attribute_name,new_value

            if (not hasattr(o,a)):
                continue

            #check if override needed
            current_value = getattr(o,a)
            if (v==current_value):
                continue

            #store values in dict
            self.new_val.append([o,a,v])
            self.old_val.append([o,a,current_value]) #storing bpy.object might cause crash...?

            continue

    #note: if stored value is bpy array for ex, it is not be reliable, need to serialize
        self.serialize_storage()

        return None

    def __enter__(self,):

        #only if user enables it
        if (not self.enable):
            return None

        #setattr from instructions
        for o,a,v in self.new_val:
            #print("new_val:",o,a,v)
            setattr(o,a,v)

        return None

    def __exit__(self,*args):

        #only if user enables it
        if (not self.enable):
            return None

        #restore attributes from storage
        for o,a,v in self.old_val:
            #print("old_val:",o,a,v)
            setattr(o,a,v)

        return None