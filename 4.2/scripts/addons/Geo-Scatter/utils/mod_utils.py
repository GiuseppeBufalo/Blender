
#modstack related functions

import bpy


def viewport_mostack_optimization(o,dict=None): #typical use case of a with object... please implement this shit if actually using this.
    """temporarily hide/restore all modstack viewport options for perfs, otherwise python evaluate whole blender scene at each line of code"""

    if (dict is None):
        dict = {m.name:m.show_viewport for m in o.modifiers}
        for m in o.modifiers: 
            m.show_viewport = False
            m.show_render = False
        return dict 

    for key, value in dict.items():
        o.modifiers[key].show_viewport = value
        o.modifiers[key].show_render = value

    return None 


def is_a_above_b(o,a,b):
    """check modifier order (compare index)"""

    if (a==b):
        return False
    dict = {m.name:i for i, m in enumerate(o.modifiers)}
    return dict[a.name]<dict[b.name]


def get_mod_idx(o,mod):
    """get index of mod"""

    for i,m in enumerate(o.modifiers):
        if (m==mod):
            return i


def move_queue(o,mod, mode="bottom",):

    dict = viewport_mostack_optimization(o)

    idx = 0 if (mode=="top") else -1
    move_operator = bpy.ops.object.modifier_move_up if (mode=="top") else bpy.ops.object.modifier_move_down

    while (o.modifiers[idx]!=mod):
        move_operator({"object":o},modifier=mod.name)

    viewport_mostack_optimization(o,dict=dict)    

    return None 


def order_by_names(o, names=[],strict=True,modtype_filter=[]):
    """order the modstack by names, filter by type option"""

    dict = viewport_mostack_optimization(o)

    def find_first_idx():
    
        for m in o.modifiers:

            #filter by type
            if modtype_filter:
                if (m.type not in modtype_filter):
                    continue 

            #filter by name strict
            if strict:
                if (m.name in names):
                    return get_mod_idx(o,m) 

            #filter by name relax
            else: 
                for n in names: 
                    if (n in m.name):
                        return  get_mod_idx(o,m) 

        return None 

    #find the mod in this list that is the highest of all 
    first_idx = find_first_idx()

    #move to the top
    for n in reversed(names):
        for m in o.modifiers:  
            
            #filters
            if (modtype_filter and (m.type not in modtype_filter)):
                continue 
            if (strict and (m.name!=n)):
                continue
            if (n not in m.name):
                continue  
            
            #move until 
            top = o.modifiers[first_idx]
            while is_a_above_b(o,top,m):
                bpy.ops.object.modifier_move_up({"object":o},modifier=m.name)
        
    viewport_mostack_optimization(o,dict=dict)    

    return None