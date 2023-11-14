
#some numpy functions 

import numpy as np


def np_remap(vs, array_min="AUTO", array_max="AUTO", normalized_min=0, normalized_max=1, skip_denominator=False):
    """remap values to given minimal and maximal""" 

    #possibility of remap from given min max:
    if (array_min=="AUTO"):
        array_min = vs.min(axis=0)
    else: #if remap, then need to cut array min and max 
        vs = np.where((vs<array_min),array_min,vs)

    if (array_max=="AUTO"):
        array_max = vs.max(axis=0)
    else: #if remap, then need to cut array min and max 
        vs = np.where((vs>array_max),array_max,vs)

    nom = (vs-array_min)*(normalized_max-normalized_min)
    denominator = array_max-array_min

    if not skip_denominator: #may cause crashes, with normal for example. didn't get why..
        denominator[denominator==0] = 1

    return normalized_min + nom/denominator 


def np_apply_transforms(o, co):
    """local to global numpy coordinates"""

    m = np.array(o.matrix_world)    
    mat = m[:3, :3].T
    loc = m[:3, 3]
    return co @ mat + loc


def np_global_to_local(obj, co):
    """local co to local obj"""

    mwi = obj.matrix_world.inverted()
    m = np.array(mwi)
    mat = m[:3, :3].T
    loc = m[:3, 3]
    return co @ mat + loc
