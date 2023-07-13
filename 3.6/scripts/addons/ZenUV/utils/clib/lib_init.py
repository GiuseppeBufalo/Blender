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

# See 'ZenUV/utils/clib/API.pdf' for more details

import os
import stat
import ctypes
import platform
import datetime
import re
from mathutils import Color

from ..blender_zen_utils import get_zen_platform

ZEN_LIB_NAME = {
    "Linux": "zen_uv_lib_linux_64_v1_0_0.so",
    "Darwin": "zen_uv_lib_mac_intel_64_v1_0_0.dylib",
    "DarwinSilicon": "zen_uv_lib_mac_silicon_64_v1_0_0.dylib",
    "Windows": "zen_uv_lib_win_64_v1_0_0.dll"
    }


def get_zenlib_name():
    return ZEN_LIB_NAME[get_zen_platform()]


def get_zenlib_version():
    result = re.match(r'^zen_uv_lib_.*_v(\d+)_(\d+)_(\d+).[^.]*', get_zenlib_name())
    if result:
        return [int(result.group(1)), int(result.group(2)), int(result.group(3))]
    else:
        return [0, 0, 0]


def get_zenlib_path():
    return os.path.dirname(os.path.abspath(__file__)) + os.path.sep + get_zenlib_name()


def is_zenlib_present():
    return os.path.isfile(get_zenlib_path())


def create_zenlib():
    if is_zenlib_present():
        return ctypes.cdll.LoadLibrary(get_zenlib_path())
    else:
        return None


_zen_relax_app_path = None


RELAX_APP_NAME = {
    "Linux": "ZenRelax_linux_64_v1_0_0",
    "Darwin": "ZenRelax_mac_intel_64_v1_0_0",
    "DarwinSilicon": "ZenRelax_mac_silicon_64_v1_0_0",
    "Windows": "ZenRelax_win_64_v1_0_0.exe"
}


def get_zen_relax_name():
    return RELAX_APP_NAME[get_zen_platform()]


def get_zen_relax2_app():
    global _zen_relax_app_path
    if _zen_relax_app_path is not None:
        return _zen_relax_app_path
    _zen_relax_app_path = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + get_zen_relax_name()

    if platform.system() in {'Darwin', 'Linux'}:
        app_flags = os.stat(_zen_relax_app_path).st_mode
        if not bool(app_flags & stat.S_IXUSR):
            print('WARNING! Exec denied, changing privileges ...')
            app_flags = app_flags | stat.S_IXUSR

            os.chmod(_zen_relax_app_path, app_flags)

    return _zen_relax_app_path


LIB = None
zuvOS = None
zuv = None


def register_library():
    global LIB
    global zuv
    global zuvOS

    if LIB is None:
        LIB = create_zenlib()
        zuvOS = ZenUvOS(LIB)

        if LIB:
            zuv = ZenUv(LIB)
            print("Zen UV Library: REGISTERED.")
    else:
        print("Zen UV: Zen UV Core Library was not correctly previously removed!")


def unregister_library():
    global LIB
    global zuv
    global zuvOS

    # del zuvOS
    zuvOS = None

    if LIB:
        # del zuv
        zuv = None

        import _ctypes

        if (platform.system() == 'Windows'):
            _ctypes.FreeLibrary(LIB._handle)
        else:
            _ctypes.dlclose(LIB._handle)
        print("Zen UV Library: UNREGISTERED.")

        # del LIB
        LIB = None


# COLOR CONSTANTS
ZEN_THEME_COLOR_BLACK = 56
ZEN_THEME_COLOR_RED = 88
ZEN_THEME_COLOR_GREEN = 63
ZEN_THEME_COLOR_YELLOW = 95
ZEN_THEME_COLOR_BLUE = 216
ZEN_THEME_COLOR_MAGENTA = 248
ZEN_THEME_COLOR_CYAN = 223
ZEN_THEME_COLOR_DARK_RED = 72

ZEN_THEME_COLOR_DARK_GREEN = 60
ZEN_THEME_COLOR_DARK_YELLOW = 76
ZEN_THEME_COLOR_DARK_BLUE = 136
ZEN_THEME_COLOR_DARK_MAGENTA = 152
ZEN_THEME_COLOR_DARK_CYAN = 140

ZEN_THEME_COLOR_WHITE = 255

ZEN_ICON_RED_32 = 0
ZEN_ICON_WHITE_32 = 1


class ZenUv(ctypes.Structure):
    # Initializing
    def __init__(self, p_lib):
        self.lib = None
        self.setLib(p_lib)

    # Deleting (Calling destructor)
    def __del__(self):
        if self.lib:
            self.lib.ZenUv_delete(self.obj)

    # Private methods
    def __appendAdj(self, typeAB, key, input):
        if self.lib:
            numInp = len(input)
            array_type = ctypes.c_int32 * numInp
            arr = array_type(*input)
            self.lib.ZenUv_appendAdj(self.obj, typeAB, key, arr, ctypes.c_uint32(numInp))

    def setLib(self, p_lib):
        if self.lib != p_lib:
            self.lib = p_lib

            if self.lib:
                PZenUv = ctypes.POINTER(ZenUv)
                self.lib.ZenUv_new.restype = PZenUv
                self.lib.ZenUv_new.argtypes = ()

                self.obj = self.lib.ZenUv_new()

                self.lib.ZenUv_appendAdj.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32, ctypes.POINTER(ctypes.c_int32), ctypes.c_uint32]
                self.lib.ZenUv_appendAdj.restype = None

                self.lib.ZenUv_calc.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_bool), ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32)]
                self.lib.ZenUv_calc.restype = ctypes.POINTER(ctypes.c_int32)

                self.lib.ZenUv_getErrorStr.argtypes = [ctypes.c_int32]
                self.lib.ZenUv_getErrorStr.restype = ctypes.c_char_p

    # Public methods
    def calcMapping(self, adjA, adjB):
        if self.lib:
            for vertex, neighbours in adjA.items():
                self.__appendAdj(0, vertex, neighbours)

            for vertex, neighbours in adjB.items():
                self.__appendAdj(1, vertex, neighbours)

            iso = ctypes.c_bool()
            arrSize = ctypes.c_int32()
            errCode = ctypes.c_int32()
            arrOut = self.lib.ZenUv_calc(self.obj, ctypes.byref(iso), ctypes.byref(arrSize), ctypes.byref(errCode))

            out_mapping = []
            for i in range(arrSize.value):
                out_mapping.append(arrOut[i])

            return iso.value, out_mapping, errCode.value

    def getErrorStr(self, ec):
        if self.lib:
            errStr = self.lib.ZenUv_getErrorStr(ec)
            return errStr.decode("utf-8")


# RGB Converting Function


def RGB2Color(color):
    """
    converts input RGB tuple in to Integer representation
    input Tuple can be:
        rgb int:    (128, 56, 14)
        rgb float:  (0.32, 0.89, 0.14)
    """
    if isinstance(color[0], float):
        color = Color((color[0], color[1], color[2]))
        r = int(color.r * 255)
        g = int(color.g * 255)
        b = int(color.b * 255)
    else:
        r = color[0]
        g = color[1]
        b = color[2]

    if (r == 0 and g == 0 and b == 0):
        return 56

    RGBint = (((((r << 8) | g) << 8) | b) << 8)
    return RGBint


class ZenUvProgressTheme(ctypes.Structure):
    _fields_ = [
        ("widgetColor", ctypes.c_uint64),
        ("widgetBorderColor", ctypes.c_uint64),
        ("progrBackColor", ctypes.c_uint64),
        ("progrSelColor", ctypes.c_uint64),
        ("labelColor", ctypes.c_uint64),
        ("iconID", ctypes.c_int32)
        ]


class ZenUvProgressBounds(ctypes.Structure):
    _fields_ = [
        ("widgetWidth", ctypes.c_int32),
        ("widgetHeight", ctypes.c_int32),
        ("spacingX", ctypes.c_int32),
        ("spacingY", ctypes.c_int32)
        ]


class ZenUvOS(ctypes.Structure):
    def __init__(self, p_lib):
        self.lib = None
        self.setLib(p_lib)

    # Deleting (Calling destructor)
    def __del__(self):
        if self.lib:
            self.lib.ZenUvOS_delete(self.obj)

    def setLib(self, p_lib):
        if self.lib != p_lib:
            self.lib = p_lib
            self.tm_progress = datetime.datetime.now()
            if self.lib:
                PZenUvOS = ctypes.POINTER(ZenUvOS)
                self.lib.ZenUvOS_new.restype = PZenUvOS
                self.lib.ZenUvOS_new.argtypes = ()

                self.obj = self.lib.ZenUvOS_new()

    # Set TaskbarProgress

    def setTaskbarProgressTheme(self, progressTheme):
        if self.lib:
            self.lib.ZenUvOS_SetTaskbarProgressTheme(self.obj, progressTheme)

    def setTaskbarProgressBounds(self, progressBounds):
        if self.lib:
            self.lib.ZenUvOS_SetTaskbarProgressBounds(self.obj, progressBounds)

    def setTaskbarProgress(self, position, max, force=False, text=''):
        if self.lib:
            delta_send = datetime.datetime.now() - self.tm_progress
            if (force or (delta_send.total_seconds() > 0.5)):
                self.lib.ZenUvOS_SetTaskbarProgress(self.obj, position, max, text)
                self.tm_progress = datetime.datetime.now()

    def setTaskbarProgressVisible(self, visible, text=''):
        if self.lib:
            self.lib.ZenUvOS_SetTaskbarProgressVisible(self.obj, visible, text)

    def getMainWindowTitle(self):
        if self.lib:
            s = ctypes.create_unicode_buffer('', 4096)
            self.lib.ZenUvOS_GetMainWindowTitle(self.obj, s, 4096)
            return s.value

    def setMainWindowTitle(self, text):
        if self.lib:
            self.lib.ZenUvOS_SetMainWindowTitle(self.obj, text)


def getText(prefix, preposition, pos, _max):
    """
    Creates text for the progress bar.
    """
    percent = 0
    if _max != 0:
        if not percent > 100:
            percent = int(round(pos / _max * 100, 0))
        else:
            percent = 100
    return "{} {} {} 100%".format(prefix, percent, preposition)


def init_progress(context, message='Prepare things...', text_only=False):
    """ Init the Progress widget and return Progress Class and Current Window Title"""
    # from ZenUV.utils.clib.lib_init import (
    #     # ZenUvOS,
    #     ZenUvProgressTheme,
    #     RGB2Color,
    #     ZEN_ICON_RED_32
    # )
    global zuvOS

    bl_theme = context.preferences.themes[0].user_interface

    progressAmorphicTheme = ZenUvProgressTheme(
        RGB2Color(bl_theme.wcol_progress.inner),  # "widgetColor"
        RGB2Color(bl_theme.wcol_progress.outline),  # "widgetBorderColor"
        RGB2Color(bl_theme.wcol_tool.inner),  # "progrBackColor"
        # RGB2Color((0.392, 0.392, 0.392)),  # "progrBackColor"
        (
            RGB2Color(bl_theme.wcol_tool.inner) if text_only else
            RGB2Color(bl_theme.wcol_progress.item)  # "progrSelColor"
        ),
        # RGB2Color(bl_theme.wcol_progress.item),  # "progrSelColor"
        RGB2Color(bl_theme.wcol_progress.text),  # "labelColor"
        ZEN_ICON_RED_32
    )
    if zuvOS:
        zuvOS.setTaskbarProgressTheme(progressAmorphicTheme)
        # wasTitle = zuvOS.getMainWindowTitle()
        zuvOS.setTaskbarProgressVisible(True, text=message)
    return zuvOS  # , wasTitle


def finish_progress(zuvOS):
    """ Finished Progress. Disable Widget and Restore Current Window Title"""
    # restore to defaults
    zuvOS.setTaskbarProgressVisible(False)
    # zuvOS.setMainWindowTitle(wasTitle)


def StackSolver():
    global zuv
    if zuv:
        return zuv
    return None


if __name__ == '__main__':
    pass
