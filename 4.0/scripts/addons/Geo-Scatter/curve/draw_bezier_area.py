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

import time
import datetime
import numpy as np

import bpy
import bmesh
from bpy.types import Operator
from bpy.props import StringProperty, FloatProperty, BoolProperty
import mathutils
from mathutils import Matrix, Color, Vector, Quaternion
from mathutils.geometry import intersect_line_plane
from bpy_extras import view3d_utils

from ..manual.debug import log, debug_mode, verbose
from ..manual.navigator import ToolNavigator
from ..widgets.theme import ToolTheme
# from ..widgets.widgets import ToolOverlay
from ..widgets.widgets import ToolWidgets
from ..widgets.infobox import SC5InfoBox, generic_infobox_setup

from ..resources.translate import translate
from ..utils.extra_utils import dprint


class ToolBox():
    tool = None
    reference = None


class SCATTER5_OT_tool_base(Operator, ):
    bl_idname = "scatter5.tool_widget_inspector_base"
    bl_label = "Tool Base"
    bl_description = "Tool Base"
    bl_options = {'INTERNAL'}
    
    tool_id = "scatter5.tool_widget_inspector_base"
    tool_label = "Tool Base"
    # tool_overlay = True
    
    # # >>> HACK ----------------------------------------------------------
    # USE_DISPLACED_TOOLTIP_PREVENTION_HACK = True
    # # <<< HACK ----------------------------------------------------------
    
    @classmethod
    def poll(cls, context, ):
        return True
    
    def _in_region(self, mouse_x, mouse_y, region, ):
        x = region.x
        y = region.y
        w = region.width
        h = region.height
        if(mouse_x > x and mouse_x < x + w):
            if(mouse_y > y and mouse_y < y + h):
                return True
        return False
    
    def _is_viewport(self, context, event, ):
        mx = event.mouse_x
        my = event.mouse_y
        
        region = None
        for a in context.screen.areas:
            if(a.type == 'VIEW_3D'):
                for r in a.regions:
                    if(r.type == 'WINDOW'):
                        ok = self._in_region(mx, my, r, )
                        if(not ok):
                            continue
                        region = r
        
        if(region is not None):
            if(region == context.region):
                return True
        
        return False
    
    def _is_sidebar(self, context, event, ):
        mx = event.mouse_x
        my = event.mouse_y
        
        region = None
        for a in context.screen.areas:
            if(a.type == 'VIEW_3D'):
                for r in a.regions:
                    # if(r.type in ('TOOL_HEADER', 'HEADER', 'TOOLS', 'UI', 'HUD', )):
                    if(r.type in ('UI', )):
                        ok = self._in_region(mx, my, r, )
                        if(not ok):
                            continue
                        
                        if(a == self._invoke_area):
                            region = r
        
        if(region is not None):
            return True
        
        return False
    
    def _cleanup(self, context, event, ):
        pass
    
    @verbose
    def _abort(self, context, event, ):
        ToolBox.tool = None
        ToolBox.reference = None
        
        ToolWidgets.deinit()
        
        # if(self.tool_overlay):
        #     ToolOverlay.hide()
        #     ToolOverlay.deinit()
        
        self._cleanup(context, event, )
        
        try:
            # if invoke calls abort, this might not be set yet
            context.window_manager.event_timer_remove(self._nav_timer)
        except Exception as e:
            pass
        
        context.window.cursor_modal_restore()
        context.workspace.status_text_set(text=None, )
        
        self._aborted = True
    
    '''
    def _widgets_any_event(self, context, event, ):
        # NOTE: this might not be used at all.. idle/outside/press/move/release should cover every case.. at least all widget code will be at one place, and not split into two functions called at different times..
        pass
    '''
    
    def _on_any_modal_event(self, context, event, ):
        pass
    
    # @verbose
    def _widgets_clear(self, context, event, ):
        ToolWidgets._cache[self.tool_id]['screen_components'] = []
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: sadly i need this special function because when lmb is down, only mouse events have some callbacks, so until i move mouse, no change in drawing occur, so this is specially called when any modifier key is pressed or released so event modifier property changes.
        # TODO: this feels messy, say for example that i want something else to be in `cursor_components`, at the same time as modifiers, if i replace list of components, i will lose other elements of cursor, if i extend, every change will add to that another draw call, only i can loop through list primitives, identify those that belong to modifier and do something with it.. not great.. maybe add some id to each component? something that drawing function will ignore, but i can use for identifying? or some other separate callback for always refreshing elements? last time i did not like it. forgot why.
        pass
    
    # @verbose
    def _widgets_mouse_outside(self, context, event, ):
        self._widgets_clear(context, event, )
    
    # @verbose
    def _widgets_mouse_idle(self, context, event, ):
        center = (event.mouse_region_x, event.mouse_region_y, )
        radius = 120
        color = (1.0, 1.0, 1.0, 0.2, )
        thickness = 2.0
        
        steps = 4
        offset = np.pi / 4
        vs = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep + offset) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep + offset) * radius)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = [
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {'center': center, 'radius': radius, 'steps': 32, 'color': color, 'thickness': thickness, },
            },
            {
                'function': 'thick_line_2d',
                'arguments': {'a': vs[0], 'b': vs[2], 'color': color, 'thickness': thickness, },
            },
            {
                'function': 'thick_line_2d',
                'arguments': {'a': vs[1], 'b': vs[3], 'color': color, 'thickness': thickness, },
            },
        ]
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_press(self, context, event, ):
        center = (event.mouse_region_x, event.mouse_region_y, )
        radius = 120
        color = (1.0, 1.0, 1.0, 1.0, )
        thickness = 2.0
        
        steps = 4
        offset = np.pi / 4
        vs = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep + offset) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep + offset) * radius)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = [
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {'center': center, 'radius': radius, 'steps': 32, 'color': color, 'thickness': thickness, },
            },
            {
                'function': 'thick_line_2d',
                'arguments': {'a': vs[0], 'b': vs[2], 'color': color, 'thickness': thickness, },
            },
            {
                'function': 'thick_line_2d',
                'arguments': {'a': vs[1], 'b': vs[3], 'color': color, 'thickness': thickness, },
            },
        ]
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_move(self, context, event, ):
        center = (event.mouse_region_x, event.mouse_region_y, )
        radius = 120
        color = (1.0, 1.0, 1.0, 1.0, )
        thickness = 2.0
        
        steps = 4
        offset = np.pi / 4
        vs = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep + offset) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep + offset) * radius)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = [
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {'center': center, 'radius': radius, 'steps': 32, 'color': color, 'thickness': thickness, },
            },
            {
                'function': 'thick_line_2d',
                'arguments': {'a': vs[0], 'b': vs[2], 'color': color, 'thickness': thickness, },
            },
            {
                'function': 'thick_line_2d',
                'arguments': {'a': vs[1], 'b': vs[3], 'color': color, 'thickness': thickness, },
            },
        ]
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_move_inbetween(self, context, event, ):
        pass
    
    # @verbose
    def _widgets_mouse_release(self, context, event, ):
        center = (event.mouse_region_x, event.mouse_region_y, )
        radius = 120
        color = (1.0, 1.0, 1.0, 0.2, )
        thickness = 2.0
        
        steps = 4
        offset = np.pi / 4
        vs = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep + offset) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep + offset) * radius)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = [
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {'center': center, 'radius': radius, 'steps': 32, 'color': color, 'thickness': thickness, },
            },
            {
                'function': 'thick_line_2d',
                'arguments': {'a': vs[0], 'b': vs[2], 'color': color, 'thickness': thickness, },
            },
            {
                'function': 'thick_line_2d',
                'arguments': {'a': vs[1], 'b': vs[3], 'color': color, 'thickness': thickness, },
            },
        ]
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _action_begin(self, context, event, ):
        pass
    
    # @verbose
    def _action_update(self, context, event, ):
        pass
    
    # @verbose
    def _action_update_inbetween(self, context, event, ):
        pass
    
    # @verbose
    def _action_finish(self, context, event, ):
        if(self._dirty):
            # NOTE: cpu tools have to do following before using point data, gpu tools are refreshed on redraw
            self._refresh(context, event, )
            self._dirty = False
        
        pass
    
    # @verbose
    def _on_any_key_press(self, context, event, ):
        pass
    
    # @verbose
    def _on_any_key_repeat(self, context, event, ):
        pass
    
    # @verbose
    def _on_any_key_release(self, context, event, ):
        pass
    
    def _is_key_event(self, context, event, ):
        types = {
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
            'LEFT_CTRL', 'LEFT_ALT', 'LEFT_SHIFT', 'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT', 'OSKEY',
            'APP', 'GRLESS', 'ESC', 'TAB', 'RET', 'SPACE', 'LINE_FEED', 'BACK_SPACE', 'DEL',
            'SEMI_COLON', 'PERIOD', 'COMMA', 'QUOTE', 'ACCENT_GRAVE', 'MINUS', 'PLUS', 'SLASH', 'BACK_SLASH', 'EQUAL', 'LEFT_BRACKET', 'RIGHT_BRACKET',
            'LEFT_ARROW', 'DOWN_ARROW', 'RIGHT_ARROW', 'UP_ARROW',
            'NUMPAD_0', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9',
            'NUMPAD_PERIOD', 'NUMPAD_SLASH', 'NUMPAD_ASTERIX', 'NUMPAD_MINUS', 'NUMPAD_ENTER', 'NUMPAD_PLUS',
            'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18', 'F19', 'F20', 'F21', 'F22', 'F23', 'F24',
            'PAUSE', 'INSERT', 'HOME', 'PAGE_UP', 'PAGE_DOWN', 'END',
            'MEDIA_PLAY', 'MEDIA_STOP', 'MEDIA_FIRST', 'MEDIA_LAST',
            # 'TEXTINPUT', 'WINDOW_DEACTIVATE',
        }
        if(event.type in types):
            return True
        return False
    
    def _modal_shortcuts(self, context, event, ):
        # # is called from `_modal`, after all else is handled (apart from exit), any custom keys can be put here..
        # if(event.type in {'F', } and event.value == 'PRESS'):
        #     print('F on')
        # elif(event.type in {'F', } and event.value == 'RELEASE'):
        #     print('F off')
        pass
    
    def _status_action(self, context, event, ):
        t = "Action text.."
        bpy.context.workspace.status_text_set(text=t, )
    
    def _status_idle(self, context, event, ):
        t = "Idle text.."
        bpy.context.workspace.status_text_set(text=t, )
    
    @verbose
    def _refresh(self, context, event, ):
        pass
    
    def _modal(self, context, event, ):
        # ------------------------------------------------------------------ refresh >>>
        # NOTE: it is possible to resize viewport while tool is running (because i allow clicking on sidebar) so invalidate on any resize, both gpu and cpu
        region = context.region
        if(self._region_x != region.x):
            self._region_x = region.x
            self._dirty = True
        if(self._region_y != region.y):
            self._region_y = region.y
            self._dirty = True
        if(self._region_width != region.width):
            self._region_width = region.width
            self._dirty = True
        if(self._region_height != region.height):
            self._region_height = region.height
            self._dirty = True
        
        if(self._tool_processing_type == 'GPU'):
            # NOTE: if dirty, refresh gpu tools automatically, cpu manually at specified event, usually when user action is finished and delay can be expected..
            if(self._dirty):
                # NOTE: it is here if window was resized, otherwise gpu is refreshed on screen redraw..
                self._refresh(context, event, )
                self._dirty = False
        # ------------------------------------------------------------------ refresh <<<
        
        # if i need something to be constantly refreshed.. not widgets..
        self._on_any_modal_event(context, event, )
        
        # NOTE: sidebar disabled for now..
        # # ------------------------------------------------------------------ area >>>
        # in_sidebar = self._is_sidebar(context, event, )
        # if(in_sidebar):
        #     if(not self._lmb):
        #         self._widgets_mouse_outside(context, event, )
        #         # standard cursor only on sidebar and only when mouse is not dragged there while lmb is down
        #         context.window.cursor_modal_restore()
        #         return {'PASS_THROUGH'}
        # # ------------------------------------------------------------------ area <<<
        
        # everywhere else use tool cursor, even on disabled areas, so user is reminded that tool is running
        context.window.cursor_modal_set(self._cursor)
        
        # TODO: i meant that for anything that is linked to mouse directly, i mean `cursor_components`, but is it good approach? shouldn't it be part of idle/press/move/release? with all the troubles with navigation, this is another thing to worry about.. lets think about that some more..
        '''
        self._widgets_any_event(context, event, )
        '''
        
        # # if i need something to be constantly refreshed.. not widgets..
        # self._on_any_modal_event(context, event, )
        
        # key events, runs event when mouse is pressed
        if(event.value in {'PRESS', 'RELEASE', }):
            if(self._is_key_event(context, event, )):
                if(event.value == 'PRESS'):
                    if(event.is_repeat):
                        self._on_any_key_repeat(context, event, )
                    else:
                        self._on_any_key_press(context, event, )
                if(event.value == 'RELEASE'):
                    self._on_any_key_release(context, event, )
        
        # ------------------------------------------------------------------ navigation >>>
        if(self._nav and event.type == 'TIMER'):
            # redraw while navigating
            self._widgets_mouse_idle(context, event, )
            self._status_idle(context, event, )
        if(self._nav and event.type != 'TIMER'):
            # i was navigating and now i am not because some other event is here, turn nav off and run anotehr idle redraw
            self._nav = False
            self._widgets_mouse_idle(context, event, )
            self._status_idle(context, event, )
            
            if(self._tool_processing_type == 'CPU'):
                # NOTE: delay refresh for cpu tools.. gpu are refreshed on screen redraw
                self._dirty = True
        
        if(event.type != 'TIMER'):
            # now test if i have another nav event
            # NOTE: warning, in no way i can rely on `self._nav` being correct, when user stops navigating and then does not move mouse or hit any key, no event is fired so i cannot know what is happening, this is only for timer to redraw screen. and screen drawing should be in idle mode, no cursor changes, or i get cursor glitches.. so it will look that user does not iteract with anything, i draw idle state, then user starts navigating and idle state is redrawn, then stops, then idle is being drawn until something happen..
            self._nav = self._navigator.run(context, event, None, )
            
            # NOTE: for 3d mouse use passing event out, becuase from some unknown reason, if operator is called directly, returns cancelled even when event iscorrect type.
            # TODO: investigate why ndof events are rejected in source/blender/editors/space_view_3d/view3d_navigate_ndof.c @499
            if(not self._nav):
                if(event.type.startswith('NDOF_')):
                    self._nav = True
                    return {'PASS_THROUGH'}
                if(event.type.startswith('TRACKPAD')):
                    self._nav = True
                    return {'PASS_THROUGH'}
        
        if(self._nav):
            return {'RUNNING_MODAL'}
        # ------------------------------------------------------------------ navigation <<<
        # context.area.tag_redraw()
        # ------------------------------------------------------------------ props >>>
        mod = False
        if(event.ctrl != self._ctrl):
            self._ctrl = event.ctrl
            mod = True
        if(event.alt != self._alt):
            self._alt = event.alt
            mod = True
        if(event.shift != self._shift):
            self._shift = event.shift
            mod = True
        if(event.oskey != self._oskey):
            self._oskey = event.oskey
            mod = True
        if(mod):
            # NOTE: i think this is redundant, this should be handled in widgets drawing key mouse functions, if some modifier is on, draw something extra
            self._widgets_modifiers_change(context, event, )
        
        if(event.is_tablet):
            self._pressure = event.pressure
            if(self._pressure <= 0.001):
                # prevent zero pressure which might sometimes happen..
                self._pressure = 0.001
        # ------------------------------------------------------------------ props <<<
        # ------------------------------------------------------------------ action >>>
        in_viewport = self._is_viewport(context, event, )
        
        if(not self._lmb):
            # call idle when mouse is not pressed down, so i detect modifiers and update
            # when mouse is down press,move and release hadles things..
            self._widgets_mouse_idle(context, event, )
            self._status_idle(context, event, )
        
        if(event.type == 'LEFTMOUSE' and event.value == 'PRESS'):
            if(not in_viewport):
                return {'RUNNING_MODAL'}
            self._lmb = True
            self._action_begin(context, event, )
            self._widgets_mouse_press(context, event, )
            self._status_action(context, event, )
        elif(event.type == 'MOUSEMOVE'):
            if(self._lmb):
                self._action_update(context, event, )
                self._widgets_mouse_move(context, event, )
                self._status_action(context, event, )
        elif(event.type == 'INBETWEEN_MOUSEMOVE'):
            if(self._lmb):
                self._action_update_inbetween(context, event, )
                self._widgets_mouse_move_inbetween(context, event, )
        elif(event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            if(not self._lmb):
                return {'RUNNING_MODAL'}
            self._lmb = False
            self._action_finish(context, event, )
            self._widgets_mouse_release(context, event, )
            self._status_action(context, event, )
            return {'RUNNING_MODAL'}
        # ------------------------------------------------------------------ action <<<
        self._modal_shortcuts(context, event, )
        # ------------------------------------------------------------------ exit >>>
        if(event.type in {'RIGHTMOUSE', 'ESC', 'RET', }):
            self._abort(context, event, )
            return {'CANCELLED'}
        # ------------------------------------------------------------------ exit <<<
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event, ):
        # m = "{: <{namew}} >>> {}".format(self.modal.__qualname__, 'modal', namew=36, )
        # log(m, prefix='>>>', color='YELLOW', )
        
        if(self._aborted):
            return {'CANCELLED'}
        
        # # >>> HACK ----------------------------------------------------------
        # if(self.USE_DISPLACED_TOOLTIP_PREVENTION_HACK):
        #     if(not self._lmb):
        #         if(event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 'TIMER', }):
        #             is_viewport = self._is_viewport(context, event, )
        #             if(not self.__tooltip_pass_through and is_viewport):
        #                 d = time.time() - self.__tooltip_last_time
        #
        #                 # source/blender/editors/include/UI_interface.h
        #                 # /* How long before a tool-tip shows. */
        #                 # #define UI_TOOLTIP_DELAY 0.5
        #                 # #define UI_TOOLTIP_DELAY_LABEL 0.2
        #
        #                 if(d > 0.5 + 0.01):
        #                     self.__tooltip_pass_through = True
        #                     m = "{: <{namew}} >>> {}".format(self.modal.__qualname__, 'USE_DISPLACED_TOOLTIP_PREVENTION_HACK', namew=36, )
        #                     log(m, prefix='>>>', color='CYAN', )
        #
        #                     return {'PASS_THROUGH'}
        #             elif(not is_viewport):
        #                 self.__tooltip_last_time = time.time()
        #                 self.__tooltip_pass_through = False
        # # <<< HACK ----------------------------------------------------------
        
        try:
            r = self._modal(context, event, )
            return r
        except Exception as e:
            self._abort(context, event, )
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
            return {'CANCELLED'}
    
    def _invoke(self, context, event, ):
        context.window.cursor_modal_set('WAIT')
        if(self._tool_processing_type == 'GPU'):
            # NOTE: always refresh on startup..
            self._refresh(context, event, )
            self._dirty = False
        context.window.cursor_modal_set(self._cursor)
    
    @verbose
    def _setup(self, context, event, ):
        # setup tool specific attributes.. like define runtime attributes, store initial values, etc..
        self._theme = ToolTheme(self, )
        ToolWidgets.init(self, context, )
        ToolWidgets._cache[self.tool_id] = {
            'screen_components': [],
            'cursor_components': [],
        }
    
    def _base_setup(self, context, event, ):
        # setup tool base specific attributes.. now it is only to differentiate between cpu or gpu based tool
        self._tool_processing_type = 'CPU'
        # self._tool_processing_type = 'GPU'
    
    def invoke(self, context, event, ):
        m = "{: <{namew}} >>> {}".format(self.invoke.__qualname__, 'invoke', namew=36, )
        # log(m, prefix='>>>', color='YELLOW', )
        log(m, prefix='>>>', )
        
        if(ToolBox.reference is not None):
            try:
                ToolBox.reference._abort(context, event, )
            except Exception as e:
                # NOTE: panic!
                panic(self.invoke.__qualname__)
        
        ToolBox.tool = self.tool_id
        ToolBox.reference = self
        
        # # >>> HACK ----------------------------------------------------------
        # if(self.USE_DISPLACED_TOOLTIP_PREVENTION_HACK):
        #     self.__tooltip_last_time = time.time()
        #     self.__tooltip_pass_through = False
        #     # true because button is on sidebar.. where annoying delayed and displaced tooltips are shown.. right?
        #     self.__tooltip_sidebar = True
        # # <<< HACK ----------------------------------------------------------
        
        self._aborted = False
        
        # NOTE: so i can identify correct 3d view in draw handlers.. maybe use that also for modal evnt handling
        self._invoke_area = context.area
        self._invoke_region = context.region
        
        self._region_x = context.region.x
        self._region_y = context.region.y
        self._region_width = context.region.width
        self._region_height = context.region.height
        
        # if(self.tool_overlay):
        #     ToolOverlay.init()
        #     ToolOverlay.show(self, context, )
        
        # o = context.object
        # self._o = o
        # self._key = o.name
        
        # base tool class setup
        self._base_setup(context, event, )
        # tool specific setup
        self._setup(context, event, )
        
        self._lmb = False
        self._pressure = 1.0
        self._nav = False
        # NOTE: dirty on True to force refresh (on any modal event if _dirty set from outside) for gpu and cpu delayed refresh on user action
        self._dirty = True
        self._cursor = 'PAINT_CROSS'
        
        self._ctrl = event.ctrl
        self._alt = event.alt
        self._shift = event.shift
        self._oskey = event.oskey
        
        # timer used for screen redrawing during navigation
        self._nav_timer_time_step = 1 / 30
        self._nav_timer = context.window_manager.event_timer_add(self._nav_timer_time_step, window=context.window, )
        
        self._navigator = ToolNavigator(context, )
        
        context.window.cursor_modal_set('WAIT')
        
        try:
            # finish invoke, process geometry, setup offscreen drawing, etc. anything that might throw an error..
            self._invoke(context, event, )
        except Exception as e:
            self._abort(context, event, )
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
            return {'CANCELLED'}
        
        context.window.cursor_modal_set(self._cursor)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}


class SCATTER5_OT_bezier_area_base(SCATTER5_OT_tool_base, ):
    bl_idname = "scatter5.bezier_area_base"
    bl_label = "Bezier Area Base"
    bl_description = ""
    bl_options = set()
    
    tool_id = "scatter5.bezier_area_base"
    tool_label = "Bezier Area Base"
    
    EPSILON = 0.001
    
    edit_existing: StringProperty(default="")
    
    @classmethod
    def poll(cls, context, ):
        # NOTE: because curve identification is done by passing name to public operator, this is pointless..
        # emitter = bpy.context.scene.scatter5.emitter
        # if(emitter is None):
        #     return False
        # psy_active = emitter.scatter5.get_psy_active()
        # if(psy_active is None):
        #     return False
        # target = psy_active.s_mask_curve_ptr
        # if(target is None):
        #     return False
        # if(target.type != 'CURVE'):
        #     return False
        # if(target.mode != 'OBJECT'):
        #     return False
        return True
    
    # ------------------------------------------------------------------ widgets >>>
    
    def _widgets_mouse_outside(self, context, event, ):
        self._widgets_clear(context, event, )
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
        # self._prepend_grid(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
        # self._prepend_grid(context, event, )
    
    def _status_action(self, context, event, ):
        t = ""
        bpy.context.workspace.status_text_set(text=t, )
    
    def _status_idle(self, context, event, ):
        t = ""
        bpy.context.workspace.status_text_set(text=t, )
    
    '''
    def _prepend_grid(self, context, event, ):
        # TODO: draw something nice in viewport to have some indication where curve will be.
        d = 10.0
        co = (0.0, 0.0, self._z_offset, )
        no = (0.0, 0.0, 1.0, )
        grid = {
            'function': 'square_fill_3d',
            'arguments': {
                'co': co,
                'no': no,
                'edge_length': d,
                'color': (1.0, 1.0, 1.0, 0.1, ),
            },
        }
        ToolWidgets._cache[self.tool_id]['screen_components'].insert(0, grid)
        ToolWidgets._tag_redraw()
    '''
    
    # ------------------------------------------------------------------ widgets <<<
    # ------------------------------------------------------------------ tracking >>>
    
    def _project(self, context, event, ):
        region = context.region
        rv3d = context.region_data
        coord = (event.mouse_region_x, event.mouse_region_y, )
        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        loc, nor, idx, dst = self._bvh.ray_cast(origin, direction, )
        
        nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
        
        return loc, nor, idx, dst
    
    def _barycentric_weights(self, p, a, b, c, ):
        v0 = b - a
        v1 = c - a
        v2 = p - a
        d00 = v0.dot(v0)
        d01 = v0.dot(v1)
        d11 = v1.dot(v1)
        d20 = v2.dot(v0)
        d21 = v2.dot(v1)
        denom = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1.0 - v - w
        return u, v, w
    
    def _interpolate_smooth_face_normal(self, loc, nor, idx, ):
        if(loc is None):
            return nor
        if(self._bm is None):
            return nor
        if(not self._bm.is_valid):
            return nor
        
        f = self._bm.faces[idx]
        if(not f.smooth):
            return nor
        
        # smooth surface, iterpolate normal..
        vs = f.verts
        ws = self._barycentric_weights(loc, *[v.co.copy() for v in vs])
        ns = [v.normal.copy() for v in vs]
        n = Vector()
        for i, ni in enumerate(ns):
            # we want... a shrubbery! ni! ni! ni!
            n += ni * ws[i]
        n.normalize()
        return n
    
    def _on_any_modal_event(self, context, event, ):
        # constant project to surface on any event..
        self._loc = None
        self._nor = None
        
        # NOTE: no need for this now, lets leave it like before as early warning that context is wrong
        # # NOTE: this might not be enough of checks..
        # if(context.region_data is None):
        #     return
        # if(type(context.region_data) != bpy.types.RegionView3D):
        #     return
        
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            self._loc = loc
            self._nor = nor
            
            self._last_valid_loc = self._loc
            self._last_valid_nor = self._nor
    
    # ------------------------------------------------------------------ tracking <<<
    # ------------------------------------------------------------------ startup >>>
    
    def _prepare_once(self, context, event, ):
        # ls = []
        # for o in context.scene.objects:
        #     if(o.type == 'MESH'):
        #         if(o.visible_get()):
        #             ls.append(o)
        # NOTE: just single object for now.. when multi surface is supported, i'll be ready
        # ls = [self.surface, ]
        ls = self._surfaces
        
        if(not len(ls)):
            raise Exception("{} need mesh object in scene to operate..".format(self.pcv_label))
        
        import uuid
        import bmesh
        from mathutils.bvhtree import BVHTree
        
        depsgraph = context.evaluated_depsgraph_get()
        dt = []
        for o in ls:
            if(o.type != 'MESH'):
                # WATCH: ignore non mesh objects
                continue
            
            eo = o.evaluated_get(depsgraph)
            m = eo.matrix_world
            bm = bmesh.new()
            # NOTE: currently, face normals are not used for anything and calculating them in advance causes error in 3.1.2 and 3.2 alpha: https://developer.blender.org/T97025
            # NOTE: when face normals are used for something, either uncomment back (if fixed in api) or don't forget to manually update each face normal by `face.normal_update()` before reading normal value
            # bm.from_object(eo, depsgraph, cage=False, face_normals=True, )
            bm.from_object(eo, depsgraph, )
            bm.transform(m)
            bmesh.ops.triangulate(bm, faces=bm.faces, )
            me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
            bm.to_mesh(me)
            bm.free()
            me.calc_loop_triangles()
            vs = np.zeros((len(me.vertices) * 3), dtype=np.float64, )
            me.vertices.foreach_get('co', vs, )
            vs.shape = (-1, 3, )
            tris = np.zeros((len(me.loop_triangles) * 3), dtype=np.int64, )
            me.loop_triangles.foreach_get('vertices', tris, )
            tris.shape = (-1, 3, )
            
            smooth = np.zeros(len(me.loop_triangles), dtype=bool, )
            me.loop_triangles.foreach_get('use_smooth', smooth, )
            
            bpy.data.meshes.remove(me)
            dt.append([vs, tris, smooth, ])
        
        vl = 0
        tl = 0
        for i, d in enumerate(dt):
            vs, tris, _ = d
            vl += len(vs)
            tl += len(tris)
        
        vi = 0
        ti = 0
        avs = np.zeros((vl, 3), dtype=np.float64, )
        atris = np.zeros((tl, 3), dtype=np.int64, )
        asmooth = np.zeros(tl, dtype=bool, )
        for i, d in enumerate(dt):
            vs, tris, smooth = d
            avs[vi:vi + len(vs)] = vs
            tris = tris + vi
            atris[ti:ti + len(tris)] = tris
            asmooth[ti:ti + len(smooth)] = smooth
            vi += len(vs)
            ti += len(tris)
        
        me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
        me.vertices.add(len(avs))
        me.vertices.foreach_set('co', avs.flatten(), )
        
        me.loops.add(len(atris) * 3)
        me.polygons.add(len(atris))
        lt = np.full(len(atris), 3, dtype=np.int64, )
        ls = np.arange(0, len(atris) * 3, 3, dtype=np.int64, )
        me.polygons.foreach_set('loop_total', lt.flatten(), )
        me.polygons.foreach_set('loop_start', ls.flatten(), )
        me.polygons.foreach_set('vertices', atris.flatten(), )
        me.polygons.foreach_set('use_smooth', asmooth.flatten(), )
        if(bpy.app.version < (4, 0, 0)):
            # NOTE: useful in 3.4, deprecated and doing nothing in 3.5/3.6, removed in 4.0
            me.calc_normals()
        me.validate()
        
        # # DEBUG
        # o = bpy.data.objects.new('debug', me, )
        # bpy.context.view_layer.active_layer_collection.collection.objects.link(o)
        # # DEBUG
        
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        self._bm = bm
        
        # epsilon = 0.001
        epsilon = 0.0
        bvh = BVHTree.FromBMesh(bm, epsilon=epsilon, )
        self._bvh = bvh
        
        # -------------------------------------------------------------------
        
        # # get surface bounding box, apply world matrix, get max z
        # o = self.surface
        # bbox = np.array(o.bound_box, dtype=np.float64, )
        # ones = np.ones(len(bbox), dtype=np.float64, )
        # vs = np.c_[bbox[:, 0], bbox[:, 1], bbox[:, 2], ones]
        # model = np.array(o.matrix_world)
        # vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
        # maxz = np.max(vs[:, 2])
        
        maxz = np.max(avs[:, 2])
        
        o = self._target
        # apply all current transformations
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix()
        # move to max z
        m = Matrix()
        m[2][3] = maxz
        # apply inversion so existing data stays in place
        o.data.transform(m.inverted())
        o.matrix_world = m
        
        self._z_offset = maxz
        
        # -------------------------------------------------------------------
        
        bpy.data.meshes.remove(me)
    
    @verbose
    def _setup(self, context, event, ):
        self._loc = None
        self._nor = None
        self._last_valid_loc = None
        self._last_valid_nor = None
        
        self._prepare_once(context, event, )
        
        self._spline = None
        
        self._path = []
        self._path_inbetween = []
        
        super()._setup(context, event, )
    
    # ------------------------------------------------------------------ startup <<<
    
    def modal(self, context, event, ):
        if(event.type in {'Z', } and (event.oskey or event.ctrl)):
            # NOTE: pass through undo
            return {'PASS_THROUGH'}
        
        # NOTE: if i allow undo to be used, then i must update references to blender data, because after undo they are no longer valid
        try:
            # self.surface.name
            for s in self._surfaces:
                s.name
            # self.target.name
            self._target.name
            self.curves.name
        except ReferenceError:
            # self.surface = bpy.context.scene.scatter5.emitter
            self._surfaces = [bpy.data.objects.get(n) for n in self._surfaces_names]
            for s in self._surfaces:
                if(s is None):
                    self.report({'ERROR'}, "Data has been removed. Cannot continue.")
                    self._abort(context, event, )
                    return {'CANCELLED'}
            # self.target = bpy.data.objects.get(self.edit_existing)
            self._target = bpy.data.objects.get(self.edit_existing)
            self.curves = self._target.data
        except AttributeError:
            self.report({'ERROR'}, "Data has been removed. Cannot continue.")
            self._abort(context, event, )
            return {'CANCELLED'}
        
        return super().modal(context, event, )
    
    def _cleanup(self, context, event, ):
        # NOTE: full override, base tool does not use any trickes requiring calling super()._cleanup(...)
        # self.InfoBox_draw_bezier_area.deinit()
        SC5InfoBox.deinit()
        bpy.context.window_manager.scatter5.mode = ""


class SCATTER5_OT_draw_bezier_area(SCATTER5_OT_bezier_area_base, ):
    bl_idname = "scatter5.draw_bezier_area"
    bl_label = "Draw Curve"
    bl_description = translate("Draw bezier-area(s) with a lasso tool.")
    bl_options = {'REGISTER'}
    
    tool_id = "scatter5.draw_bezier_area"
    tool_label = "Draw Curve"
    
    # ------------------------------------------------------------------ widgets >>>
    
    def _widgets_mouse_idle(self, context, event, ):
        x = event.mouse_region_x
        y = event.mouse_region_y
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = []
        ToolWidgets._tag_redraw()
        
        # self._prepend_grid(context, event, )
    
    def _widgets_mouse_press(self, context, event, ):
        x = event.mouse_region_x
        y = event.mouse_region_y
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        
        ls = []
        ls.extend([
            {
                'function': 'tri_fan_tess_fill_2d',
                'arguments': {
                    'vertices': self._path,
                    # 'color': self._theme._fill_color,
                    'color': wfc,
                },
            },
            {
                'function': 'tri_fan_tess_thick_outline_2d',
                'arguments': {
                    'vertices': self._path,
                    # 'color': self._theme._outline_color,
                    'color': woc,
                },
            },
        ])
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._tag_redraw()
        
        # self._prepend_grid(context, event, )
    
    # ------------------------------------------------------------------ widgets <<<
    # ------------------------------------------------------------------ action >>>
    
    def _action_begin(self, context, event, ):
        super()._action_begin(context, event, )
        
        self._path = []
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween = []
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
        
        self._add_spline(context, event, )
        self._add_point(context, event, )
    
    def _action_update(self, context, event, ):
        super()._action_update(context, event, )
        
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
        
        self._add_point(context, event, )
    
    def _action_update_inbetween(self, context, event, ):
        super()._action_update_inbetween(context, event, )
        # self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
    
    def _action_finish(self, context, event, ):
        super()._action_finish(context, event, )
        
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
        
        self._add_point(context, event, )
        
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    # ------------------------------------------------------------------ action <<<
    # ------------------------------------------------------------------ curve >>>
    
    def _add_spline(self, context, event, ):
        spline = self.curves.splines.new('NURBS')
        spline.use_cyclic_u = True
        self._spline = spline
    
    '''
    def _add_point(self, context, event, ):
        spline = self._spline
        
        region = context.region
        rv3d = context.region_data
        max_distance = 10 ** 6
        plane_co = Vector((0.0, 0.0, self._z_offset))
        plane_no = Vector((0.0, 0.0, 1.0))
        
        coord = self._path[-1]
        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        end = origin + (direction * max_distance)
        v = mathutils.geometry.intersect_line_plane(origin, end, plane_co, plane_no, )
        v.z = 0.0
        v.resize_4d()
        
        if(len(self._path) == 1):
            # adding new spline add one new point, so no need to add point before i need two..
            pass
        else:
            spline.points.add(1)
        spline.points[-1].co = v
    '''
    
    def _add_point(self, context, event, ):
        spline = self._spline
        
        v = Vector()
        # various ways to recover from situation when mouse cursor is not above surface..
        if(self._loc is None):
            # i was not able to project mouse on surface
            region = context.region
            rv3d = context.region_data
            if(self._last_valid_loc is not None):
                # take depth of last successful projection
                depth = self._last_valid_loc
            else:
                # mouse was not yet above surface, use surface location. not great, but what else we can do?
                # depth = self.surface.location
                depth = Vector(np.array([s.location for s in self._surfaces], dtype=np.float64, ).mean(axis=0, ))
            # get closest location on surface
            origin = view3d_utils.region_2d_to_location_3d(region, rv3d, self._path[-1], depth, )
            l, n, i, d = self._bvh.find_nearest(origin)
            
            # # DEBUG --------------------------------------------------------
            # from ..manual import debug
            # vs = np.array([
            #     origin,
            #     l,
            # ], dtype=np.float32, )
            # cs = np.array([
            #     (1, 0, 0, 1),
            #     (1, 1, 0, 1),
            # ], dtype=np.float32, )
            # debug.points(bpy.data.objects['Empty'], vs, None, cs, )
            # # DEBUG --------------------------------------------------------
            
            if(l is not None):
                v = l.copy()
            else:
                # for some uknown reason i was not able to get any location on mesh
                if(len(spline.points) >= 1):
                    # so if i have some points in curve, use last point
                    v = Vector(spline.points[-1][:3])
                else:
                    # or leave at zero
                    pass
        else:
            # happy time, we got hit on surface
            v = self._loc.copy()
            
            # # DEBUG --------------------------------------------------------
            # from ..manual import debug
            # vs = np.array([
            #     v,
            # ], dtype=np.float32, )
            # cs = np.array([
            #     (1, 1, 1, 1),
            # ], dtype=np.float32, )
            # debug.points(bpy.data.objects['Empty'], vs, None, cs, )
            # # DEBUG --------------------------------------------------------
        
        # move to z offset to be on surface after transformation
        v.z -= self._z_offset
        # and move slightly up to keep curve above surface
        v.z += self.EPSILON
        v.resize_4d()
        
        if(len(self._path) == 1):
            # adding new spline add one new point, so no need to add point before i need two..
            pass
        else:
            spline.points.add(1)
        spline.points[-1].co = v
    
    # ------------------------------------------------------------------ curve <<<
    
    def invoke(self, context, event, ):
        bpy.context.window_manager.scatter5.mode = "DRAW_AREA"
        
        #add infobox on screen
        t = generic_infobox_setup(translate("Bezier-Area(s) Drawing Mode"),
                                  translate("Draw on the screen to generate bezier curves."),
                                  ["• "+translate("Press 'ENTER' to Confirm"),
                                   ], )
        SC5InfoBox.init(t)
        
        # # id
        # self.surface = bpy.context.scene.scatter5.emitter
        # # # TODO: use `edit_existing` in public operator to get correct object
        # # self.target = self.surface.scatter5.get_psy_active().s_mask_curve_ptr
        # # self.curves = self.target.data
        # self.target = bpy.data.objects.get(self.edit_existing)
        # if(self.target is None):
        #     # NOTE: button disappers when no curve is selected, if curve is deleted and stays in prop as invalid, it is still in data to be edited, if blend is saved and reopened, data are still there, i guess because of existing reference to it. if i remove data with python, button is reverted back. sooo, this might not never happen, but lets keep it here.
        #     self.report({'ERROR'}, "Curve object not found.")
        #     self._abort(context, event, )
        #     return {'CANCELLED'}
        
        self._emitter = bpy.context.scene.scatter5.emitter
        
        #get active psy, or group
        itm = self._emitter.scatter5.get_psy_active()
        if (itm is None):
            itm = self._emitter.scatter5.get_group_active()
        surfaces = itm.get_surfaces()
        
        self._surfaces = surfaces
        self._surfaces_names = [o.name for o in surfaces]
        self._target = bpy.data.objects.get(self.edit_existing)
        if(self._target is None):
            # NOTE: button disappers when no curve is selected, if curve is deleted and stays in prop as invalid, it is still in data to be edited, if blend is saved and reopened, data are still there, i guess because of existing reference to it. if i remove data with python, button is reverted back. sooo, this might not never happen, but lets keep it here.
            self.report({'ERROR'}, "Curve object not found.")
            self._abort(context, event, )
            return {'CANCELLED'}
        self._target_name = self._target.name
        
        self.curves = self._target.data
        
        '''
        # get surface bounding box, apply world matrix, get max z
        o = self.surface
        bbox = np.array(o.bound_box, dtype=np.float64, )
        ones = np.ones(len(bbox), dtype=np.float64, )
        vs = np.c_[bbox[:, 0], bbox[:, 1], bbox[:, 2], ones]
        model = np.array(o.matrix_world)
        vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
        maxz = np.max(vs[:, 2])
        
        o = self.target
        # apply all current transformations
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix()
        # move to max z
        m = Matrix()
        m[2][3] = maxz
        # apply inversion so existing data stays in place
        o.data.transform(m.inverted())
        o.matrix_world = m
        
        self._z_offset = maxz
        '''
        return super().invoke(context, event, )


class SCATTER5_OT_brush_bezier_area(SCATTER5_OT_bezier_area_base, ):
    bl_idname = "scatter5.brush_bezier_area"
    bl_label = "Brush Curve"
    bl_description = translate("Draw bezier-area(s) with a brush tool.")
    bl_options = {'REGISTER'}
    
    tool_id = "scatter5.brush_bezier_area"
    tool_label = "Brush Curve"
    
    radius: FloatProperty(name=translate("Radius"), default=50.0, min=1.0, soft_max=300.0, precision=0, subtype='PIXEL', description=translate("Tool active radius"), )
    radius_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    
    # ------------------------------------------------------------------ widgets >>>
    
    def _widgets_mouse_idle(self, context, event, ):
        coord = (event.mouse_region_x, event.mouse_region_y, )
        woc = self._theme._outline_color
        wfc = self._theme._fill_color
        radius = self.radius
        if(self.radius_pressure):
            pressure = event.pressure
            if(pressure == 0.0):
                pressure = 1.0
            radius = radius * pressure
        ls = [
            # circle
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius,
                    'steps': self._theme._circle_steps,
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                }
            },
            {
                'function': 'circle_fill_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius,
                    'steps': self._theme._circle_steps,
                    'color': wfc,
                }
            },
        ]
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        coord = (event.mouse_region_x, event.mouse_region_y, )
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        radius = self.radius
        if(self.radius_pressure):
            pressure = event.pressure
            if(pressure == 0.0):
                pressure = 1.0
            radius = radius * pressure
        ls = [
            # circle
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius,
                    'steps': self._theme._circle_steps,
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                }
            },
            {
                'function': 'circle_fill_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius,
                    'steps': self._theme._circle_steps,
                    'color': wfc,
                }
            },
        ]
        
        if(getattr(self, '_del_vs') is not None):
            if(len(self._del_vs)):
                ls.extend((
                    {
                        'function': 'multiple_thick_lines_3d',
                        'arguments': {
                            'vertices': self._del_vs,
                            'indices': self._del_es,
                            'matrix': Matrix(),
                            'color': (1, 0, 0, 0.7),
                            'thickness': 1.0,
                        }
                    },
                ))
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._tag_redraw()
    
    # ------------------------------------------------------------------ widgets <<<
    # ------------------------------------------------------------------ action >>>
    
    def _action_begin(self, context, event, ):
        super()._action_begin(context, event, )
        
        self._path = []
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween = []
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
        
        self._radii = []
        
        radius = self.radius
        if(self.radius_pressure):
            pressure = event.pressure
            if(pressure == 0.0):
                pressure = 1.0
            radius = radius * pressure
        self._radii.append(radius)
        
        # self._projected_path = []
        
        self._add_spline(context, event, )
        # self._add_point(context, event, )
        self._add_circle(context, event, )
    
    def _action_update(self, context, event, ):
        super()._action_update(context, event, )
        
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
        
        radius = self.radius
        if(self.radius_pressure):
            pressure = event.pressure
            if(pressure == 0.0):
                pressure = 1.0
            radius = radius * pressure
        self._radii.append(radius)
        
        # self._add_point(context, event, )
        self._add_circle(context, event, )
    
    def _action_update_inbetween(self, context, event, ):
        super()._action_update_inbetween(context, event, )
        # self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
    
    def _action_finish(self, context, event, ):
        super()._action_finish(context, event, )
        
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
        
        radius = self.radius
        if(self.radius_pressure):
            pressure = event.pressure
            if(pressure == 0.0):
                pressure = 1.0
            radius = radius * pressure
        self._radii.append(radius)
        
        # self._add_point(context, event, )
        self._add_circle(context, event, )
        
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    # ------------------------------------------------------------------ action <<<
    # ------------------------------------------------------------------ curve >>>
    
    def _add_spline(self, context, event, ):
        spline = self.curves.splines.new('NURBS')
        spline.use_cyclic_u = True
        self._spline = spline
    
    def _add_point(self, context, event, ):
        spline = self._spline
        
        v = Vector()
        # various ways to recover from situation when mouse cursor is not above surface..
        if(self._loc is None):
            # i was not able to project mouse on surface
            region = context.region
            rv3d = context.region_data
            if(self._last_valid_loc is not None):
                # take depth of last successful projection
                depth = self._last_valid_loc
            else:
                # mouse was not yet above surface, use surface location. not great, but what else we can do?
                # depth = self.surface.location
                depth = Vector(np.array([s.location for s in self._surfaces], dtype=np.float64, ).mean(axis=0, ))
            # get closest location on surface
            origin = view3d_utils.region_2d_to_location_3d(region, rv3d, self._path[-1], depth, )
            l, n, i, d = self._bvh.find_nearest(origin)
            
            # # DEBUG --------------------------------------------------------
            # from ..manual import debug
            # vs = np.array([
            #     origin,
            #     l,
            # ], dtype=np.float32, )
            # cs = np.array([
            #     (1, 0, 0, 1),
            #     (1, 1, 0, 1),
            # ], dtype=np.float32, )
            # debug.points(bpy.data.objects['Empty'], vs, None, cs, )
            # # DEBUG --------------------------------------------------------
            
            if(l is not None):
                v = l.copy()
            else:
                # for some uknown reason i was not able to get any location on mesh
                if(len(spline.points) >= 1):
                    # so if i have some points in curve, use last point
                    v = Vector(spline.points[-1][:3])
                else:
                    # or leave at zero
                    pass
        else:
            # happy time, we got hit on surface
            v = self._loc.copy()
            
            # # DEBUG --------------------------------------------------------
            # from ..manual import debug
            # vs = np.array([
            #     v,
            # ], dtype=np.float32, )
            # cs = np.array([
            #     (1, 1, 1, 1),
            # ], dtype=np.float32, )
            # debug.points(bpy.data.objects['Empty'], vs, None, cs, )
            # # DEBUG --------------------------------------------------------
        
        # move to z offset to be on surface after transformation
        v.z -= self._z_offset
        # and move slightly up to keep curve above surface
        v.z += self.EPSILON
        v.resize_4d()
        
        if(len(self._path) == 1):
            # adding new spline add one new point, so no need to add point before i need two..
            pass
        else:
            spline.points.add(1)
        spline.points[-1].co = v
    
    def _add_circle(self, context, event, ):
        spline = self._spline
        
        '''
        v = Vector()
        # various ways to recover from situation when mouse cursor is not above surface..
        if(self._loc is None):
            # i was not able to project mouse on surface
            region = context.region
            rv3d = context.region_data
            if(self._last_valid_loc is not None):
                # take depth of last successful projection
                depth = self._last_valid_loc
            else:
                # mouse was not yet above surface, use surface location. not great, but what else we can do?
                depth = Vector(np.array([s.location for s in self._surfaces], dtype=np.float64, ).mean(axis=0, ))
            # get closest location on surface
            origin = view3d_utils.region_2d_to_location_3d(region, rv3d, self._path[-1], depth, )
            l, n, i, d = self._bvh.find_nearest(origin)
            
            if(l is not None):
                v = l.copy()
            else:
                # for some uknown reason i was not able to get any location on mesh
                if(len(spline.points) >= 1):
                    # so if i have some points in curve, use last point
                    v = Vector(spline.points[-1][:3])
                else:
                    # or leave at zero
                    pass
        else:
            # happy time, we got hit on surface
            v = self._loc.copy()
        
        # move to z offset to be on surface after transformation
        v.z -= self._z_offset
        # and move slightly up to keep curve above surface
        v.z += self.EPSILON
        # v.resize_4d()
        
        self._projected_path.append(v)
        '''
        
        path = []
        radii = []
        region = context.region
        rv3d = context.region_data
        for i, coord in enumerate(self._path):
            direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
            loc, nor, idx, dst = self._bvh.ray_cast(origin, direction, )
            if(loc):
                loc.z -= self._z_offset
                path.append(loc)
                
                r = self._radii[i]
                
                w = region.width
                h = region.height
                c = Vector((w / 2, h / 2, ))
                a = c - Vector((r / 2, 0.0))
                b = c + Vector((r / 2, 0.0))
                a3 = view3d_utils.region_2d_to_location_3d(region, rv3d, a, loc)
                b3 = view3d_utils.region_2d_to_location_3d(region, rv3d, b, loc)
                r = ((a3.x - b3.x) ** 2 + (a3.y - b3.y) ** 2 + (a3.z - b3.z) ** 2) ** 0.5
                
                radii.append(r)
        
        steps = 16
        c = np.zeros((steps, 3), dtype=np.float64, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=int, )
        # c[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        # c[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        c[:, 0] = np.sin(a * angstep)
        c[:, 1] = np.cos(a * angstep)
        
        # tris = mathutils.geometry.tessellate_polygon((c, ))
        c = np.concatenate([np.zeros((1, 3), dtype=np.float64, ), c])
        i = np.arange(steps, dtype=int, )
        tris = np.c_[np.zeros(steps, dtype=np.float64, ), i + 1, np.roll(i, -1) + 1, ]
        
        l = len(path)
        lt = len(tris)
        lv = len(c)
        vs = np.zeros((l * (steps + 1), 3), dtype=np.float64, )
        triangles = np.zeros((l * len(tris), 3), dtype=int, )
        for i, p in enumerate(path):
            cc = c.copy()
            cc[:, 0] = p.x + (cc[:, 0] * radii[i])
            cc[:, 1] = p.y + (cc[:, 1] * radii[i])
            cc[:, 2] = p.z + cc[:, 2]
            vs[i * (steps + 1):(i + 1) * (steps + 1)] = cc
            tt = tris.copy()
            tt += i * lv
            triangles[i * lt:(i + 1) * lt] = tt
        
        vs2d = np.c_[vs[:, 0], vs[:, 1]]
        '''
        hull = np.array(mathutils.geometry.convex_hull_2d(vs2d), dtype=int, )
        hull_vs2d = vs2d[hull]
        # hvs = np.c_[hull_vs[:, 0], hull_vs[:, 1], np.zeros(len(hull_vs), dtype=np.float64, )]
        hull_indices = np.arange(len(hull_vs2d), dtype=int, ) + len(vs2d)
        
        vs = np.concatenate([vs2d, hull_vs2d, ])
        
        c = vs.mean(axis=0, )
        hvs = vs[hull_indices] - c
        f = 1.2
        hvs = hvs * f
        vs[hull_indices] = hvs + c
        
        # vs = np.c_[vs[:, 0], vs[:, 1], np.zeros(len(vs), dtype=np.float64, )]
        
        i = np.arange(len(hull_indices), dtype=int, )
        es = np.c_[hull_indices[i], np.roll(hull_indices[i], -1), ]
        '''
        
        # vert_coords, edges, faces, _, _, _ = mathutils.geometry.delaunay_2d_cdt(vs, es, [], 0, 0.00001, True)
        # vert_coords, edges, faces, _, _, _ = mathutils.geometry.delaunay_2d_cdt(vs2d, [], [], 0, 0.00001, True)
        # vert_coords, edges, faces, _, _, _ = mathutils.geometry.delaunay_2d_cdt(vs2d, [], [], 0, 0.00001, True)
        # vert_coords, edges, faces, _, _, _ = mathutils.geometry.delaunay_2d_cdt(vs2d, [], triangles, 0, 0.00001, True)
        vert_coords, edges, faces, _, _, _ = mathutils.geometry.delaunay_2d_cdt(vs2d, [], triangles, 3, 0.00001, True)
        vs = np.array(vert_coords)
        vs = np.c_[vs[:, 0], vs[:, 1], np.zeros(len(vs), dtype=vs.dtype, )]
        
        # print(vs)
        # print(hull_vs)
        
        import uuid
        me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
        me.from_pydata(vs, edges, faces)
        me.validate()
        me.update()
        
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        
        es = []
        for e in bm.edges:
            if(e.is_boundary):
                es.append((e.verts[0].index, e.verts[1].index, ))
        
        bm.free()
        bpy.data.meshes.remove(me)
        
        
        
        self._del_vs = vs
        # self._del_es = edges
        self._del_es = es
        
        # steps = 16
        # vs = np.zeros((steps, 2), dtype=np.float64, )
        # angstep = 2 * np.pi / steps
        # a = np.arange(steps, dtype=int, )
        # vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        # vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        
        # from ..manual import debug
        # debug.points_2d(context.region, context.region_data, bpy.data.objects['Empty'], self._path, None, )
        # debug.points_2d(context.region, context.region_data, bpy.data.objects['Empty'], self._projected_path, None, )
        # debug.points(self._target, self._projected_path, None, None, )
        # debug.points(self._target, path, None, None, )
        # debug.points(bpy.data.objects['Empty'], path, None, None, )
        # debug.points(bpy.data.objects['Empty'], vs, None, None, )
        # debug.points(self._target, vs, None, None, )
        # debug.points(self._target, hull_vs, None, None, )
    
    # ------------------------------------------------------------------ curve <<<
    
    def invoke(self, context, event, ):
        bpy.context.window_manager.scatter5.mode = "DRAW_AREA"
        
        #add infobox on screen
        t = generic_infobox_setup(translate("Bezier-Area(s) Drawing Mode"),
                                  translate("Draw on the screen to generate bezier curves."),
                                  ["• "+translate("Press 'ENTER' to Confirm"), ], )
        SC5InfoBox.init(t)
        
        self._emitter = bpy.context.scene.scatter5.emitter
        psys = self._emitter.scatter5.get_psy_active()
        surfaces = psys.get_surfaces()
        self._surfaces = surfaces
        self._surfaces_names = [o.name for o in surfaces]
        self._target = bpy.data.objects.get(self.edit_existing)
        if(self._target is None):
            # NOTE: button disappers when no curve is selected, if curve is deleted and stays in prop as invalid, it is still in data to be edited, if blend is saved and reopened, data are still there, i guess because of existing reference to it. if i remove data with python, button is reverted back. sooo, this might not never happen, but lets keep it here.
            self.report({'ERROR'}, "Curve object not found.")
            self._abort(context, event, )
            return {'CANCELLED'}
        self._target_name = self._target.name
        
        self.curves = self._target.data
        
        return super().invoke(context, event, )


def panic(where, ):
    m = "{: <{namew}} >>> {}".format(where, "panic! > {}".format(ToolBox.tool), namew=36, )
    # log(m, prefix='>>>', color='ERROR', )
    log(m, prefix='>>>', )
    
    import traceback
    traceback.print_exc()
    
    m = "{: <{namew}} >>> {}".format(where, "shutdown everything!", namew=36, )
    # log(m, prefix='>>>', color='ERROR', )
    log(m, prefix='>>>', )
    
    ToolBox.tool = None
    ToolBox.reference = None
    ToolWidgets.deinit()
    # ToolOverlay.deinit()
    SC5InfoBox.deinit()
    
    bpy.context.window.cursor_modal_restore()
    bpy.context.workspace.status_text_set(text=None, )
    
    bpy.context.window_manager.scatter5.mode = ""


def init():
    pass


def deinit():
    # stop everything that might be persistent..
    ToolWidgets.deinit()
    # ToolOverlay.deinit()
    SC5InfoBox.deinit()
    
    ToolBox.tool = None
    if(ToolBox.reference is not None):
        # ToolBox.reference._aborted = True
        ToolBox.reference._abort(context, event, )
    ToolBox.reference = None


class SCATTER5_OT_add_curve_area(Operator, ):
    bl_idname = "scatter5.add_curve_area"
    bl_label = ""
    bl_description = translate("Add a new bezier-area at cursor location.")
    bl_options = {'INTERNAL', 'UNDO', }
    
    api: StringProperty(default="", )
    
    def execute(self, context):
        scat_scene = bpy.context.scene.scatter5
        location = bpy.context.scene.cursor.location
        location.z += 2
        bpy.ops.curve.primitive_bezier_circle_add(location=location)
        # TODO: is the use of exec really needed? don't like any exec anywhere.. there should be another way
        exec(f"{self.api} = bpy.data.objects['{bpy.context.active_object.name}']")
        return {'FINISHED'}


classes = (
    SCATTER5_OT_add_curve_area,
    SCATTER5_OT_draw_bezier_area,
    # SCATTER5_OT_brush_bezier_area,
)
