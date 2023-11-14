# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# (c) 2022 Jakub Uhlik

import platform

import bpy
import numpy as np


def debug_mode():
    return (bpy.app.debug_value != 0)


def colorize(msg, ):
    if(platform.system() == 'Windows'):
        return msg
    # return "{}{}{}".format("\033[42m\033[30m", msg, "\033[0m", )
    return "{}{}{}".format("\033[43m\033[30m", msg, "\033[0m", )


def log(msg, indent=0, prefix='>', ):
    m = "{}{} {}".format("    " * indent, prefix, colorize(msg, ), )
    if(debug_mode()):
        print(m)


def verbose(fn, ):
    from functools import wraps
    
    @wraps(fn)
    def wrapper(*args, **kwargs, ):
        # hide all log message preparation behind debug_mode(), inspect module is not meant for production.. so don't even import it without debug mode enabled
        if(debug_mode()):
            import inspect
            import os
            
            # log(fn.__qualname__, prefix='>>>', )
            skip_ui_calls = True
            code_context = False
            
            s = inspect.stack()
            w = s[0]
            # c = s[1]
            if(len(s) == 1):
                # for callbacks, e.g. msgbus update function
                c = ['?'] * 5
            else:
                c = s[1]
            
            _, cpyfnm = os.path.split(c[1])
            cfn = c[3]
            cln = c[2]
            if(code_context):
                cc = c[4][0].strip()
            
            is_ui = False
            if(cpyfnm == 'ui.py' and cfn == 'draw'):
                # assuming all ui classes are in `ui.py`
                is_ui = True
            
            if(skip_ui_calls and is_ui):
                pass
            else:
                if(code_context):
                    m = "{: <{namew}} >>> {} > {}:{} '{}'".format(fn.__qualname__, cfn, cpyfnm, cln, cc, namew=36, )
                else:
                    m = "{: <{namew}} >>> {} > {}:{}".format(fn.__qualname__, cfn, cpyfnm, cln, namew=36, )
                log(m, prefix='>>>', )
        
        r = fn(*args, **kwargs, )
        return r
    return wrapper


def stopwatch(fn, ):
    from functools import wraps
    
    @wraps(fn)
    def wrapper(*args, **kwargs, ):
        if(debug_mode()):
            import time
            import datetime
            
            t = time.time()
            log("stopwatch > '{}':".format(fn.__qualname__), 0)
        
        r = fn(*args, **kwargs, )
        
        if(debug_mode()):
            d = datetime.timedelta(seconds=time.time() - t)
            log("stopwatch completed in {}.".format(d), 1)
        
        return r
    
    return wrapper


def profile(fn, ):
    from functools import wraps
    
    @wraps(fn)
    def wrapper(*args, **kwargs, ):
        if(debug_mode()):
            log("profile > '{}':".format(fn.__qualname__), 0)
            import cProfile
            import pstats
            import io
            
            pr = cProfile.Profile()
            pr.enable()
        
        r = fn(*args, **kwargs, )
        
        if(debug_mode()):
            pr.disable()
            s = io.StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats()
            
            print(s.getvalue())
            log("profile completed.", 1)
        
        return r
    return wrapper


def points(o, vs, ns=None, cs=None, ):
    try:
        from point_cloud_visualizer.mechanist import PCVOverseer
    except ImportError:
        return None
    
    pcv = PCVOverseer(o)
    
    vs = np.array(vs, dtype=np.float32, )
    vs.shape = (-1, 3, )
    if(ns is not None):
        ns = np.array(ns, dtype=np.float32, )
        ns.shape = (-1, 3, )
    if(cs is not None):
        cs = np.array(cs, dtype=np.float32, )
        cs.shape = (-1, 4, )
    
    pcv.load(vs, ns, cs, True, )
    o.point_cloud_visualizer.display.vertex_normals = True
    o.point_cloud_visualizer.display.vertex_normals_size = 1.0
    o.point_cloud_visualizer.display.vertex_normals_alpha = 1.0
    o.point_cloud_visualizer.display.point_size = 6
    o.point_cloud_visualizer.display.draw_in_front = True
    
    return pcv


def points_2d(region, rv3d, o, vs, cs=None, ):
    try:
        from point_cloud_visualizer.mechanist import PCVOverseer
    except ImportError:
        return None
    
    from bpy_extras import view3d_utils
    
    z = (0.0, 0.0, 0.0, )
    ls = []
    for i, v in enumerate(vs):
        v3 = view3d_utils.region_2d_to_location_3d(region, rv3d, v, z, )
        ls.append(v3.to_tuple())
    vs = np.array(ls, dtype=np.float32, )
    if(cs is not None):
        cs = np.array(cs, dtype=np.float32, )
    
    pcv = PCVOverseer(o)
    pcv.load(vs, None, cs, True, )
    o.point_cloud_visualizer.display.vertex_normals = False
    o.point_cloud_visualizer.display.vertex_normals_size = 1.0
    o.point_cloud_visualizer.display.vertex_normals_alpha = 1.0
    o.point_cloud_visualizer.display.point_size = 6
    o.point_cloud_visualizer.display.draw_in_front = True
    
    return pcv
