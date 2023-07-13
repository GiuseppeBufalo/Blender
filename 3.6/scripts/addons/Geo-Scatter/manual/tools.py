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

raise Exception("do not use")

import time
import numpy as np

import bpy
import mathutils
from mathutils import Matrix, Color, Vector, Quaternion
from mathutils.geometry import intersect_line_plane
from bpy_extras import view3d_utils

from .debug import log, debug_mode, verbose
from .navigator import ToolNavigator
from ..widgets.theme import ToolTheme
from ..widgets.widgets import ToolWidgets, ToolOverlay


class ToolBox():
    tool = None
    reference = None


class SCATTER5_OT_tool_base(bpy.types.Operator, ):
    bl_idname = "scatter5.tool_widget_inspector_base"
    bl_label = "Tool Base"
    bl_description = "Tool Base"
    bl_options = {'INTERNAL'}
    
    tool_id = "scatter5.tool_widget_inspector_base"
    tool_label = "Tool Base"
    tool_overlay = True
    
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
        
        if(self.tool_overlay):
            ToolOverlay.hide()
            ToolOverlay.deinit()
        
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
        
        if(self.tool_overlay):
            ToolOverlay.init()
            ToolOverlay.show(self, context, )
        
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


class SCATTER5_OT_tool_lasso_base(SCATTER5_OT_tool_base, ):
    bl_idname = "scatter5.tool_lasso_base"
    bl_label = "Lasso Base"
    bl_description = "Lasso Base"
    
    tool_id = "scatter5.tool_lasso_base"
    tool_label = "Lasso Base"
    
    def _widgets_mouse_outside(self, context, event, ):
        self._widgets_clear(context, event, )
    
    def _widgets_mouse_idle(self, context, event, ):
        x = event.mouse_region_x
        y = event.mouse_region_y
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = []
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        x = event.mouse_region_x
        y = event.mouse_region_y
        
        ls = []
        ls.extend([
            {
                'function': 'tri_fan_tess_fill_2d',
                'arguments': {
                    'vertices': self._path,
                    'color': self._theme._fill_color,
                },
            },
            {
                'function': 'tri_fan_tess_thick_outline_2d',
                'arguments': {
                    'vertices': self._path,
                    'color': self._theme._outline_color,
                },
            },
        ])
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _action_begin(self, context, event, ):
        super()._action_begin(context, event, )
        self._path = []
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween = []
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
    
    # @verbose
    def _action_update(self, context, event, ):
        super()._action_update(context, event, )
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
    
    # @verbose
    def _action_update_inbetween(self, context, event, ):
        super()._action_update_inbetween(context, event, )
        # self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
    
    # @verbose
    def _action_finish(self, context, event, ):
        super()._action_finish(context, event, )
        self._path.append((event.mouse_region_x, event.mouse_region_y, ))
        self._path_inbetween.append((event.mouse_region_x, event.mouse_region_y, ))
    
    @verbose
    def _setup(self, context, event, ):
        self._path = []
        self._path_inbetween = []
        super()._setup(context, event, )


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
    ToolOverlay.deinit()
    
    bpy.context.window.cursor_modal_restore()
    bpy.context.workspace.status_text_set(text=None, )


def init():
    pass


def deinit():
    # stop everything that might be persistent..
    ToolWidgets.deinit()
    ToolOverlay.deinit()
    
    ToolBox.tool = None
    if(ToolBox.reference is not None):
        # ToolBox.reference._aborted = True
        ToolBox.reference._abort(context, event, )
    ToolBox.reference = None


classes = ()
