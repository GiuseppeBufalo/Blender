
import os
import bpy
import bpy.utils.previews

from dataclasses import dataclass

from .. import colors

ZBBQ_IconsRegistered = None


@dataclass
class ZBBQ_Icon:
    ext: str = ".png"
    relativePath: str = ""
    name: str = None
    preview = None

    def id(self):
        return self.preview.icon_id


relativePathZenCommon = "icons" + os.sep + "ZenCommon" + os.sep

ZBBQ_Icons = {
    'Addon-Logo': ZBBQ_Icon(".png", relativePathZenCommon),
    'Discord-Logo-White_32': ZBBQ_Icon(".png", relativePathZenCommon),

    'zen-uv_32': ZBBQ_Icon(".png", relativePathZenCommon),
    'checker_32': ZBBQ_Icon(".png", relativePathZenCommon),
    'zen-sets_32': ZBBQ_Icon(".png", relativePathZenCommon),
}

# Generated icons for pie menu:

pieMenuIconsSetName = "TriangleUniformFill"

numpadKeys = ["1", "2", "3", "4", "6", "7", "8", "9"]

for color in colors.ZBBQ_Colors:
    for numpadKey in numpadKeys:
        ZBBQ_Icons[f"{color}Position{numpadKey}"] = ZBBQ_Icon(".png", "icons" + os.sep + pieMenuIconsSetName + os.sep)


def register():
    dirIcons = os.path.dirname(__file__)

    global ZBBQ_IconsRegistered

    if ZBBQ_IconsRegistered is None:
        ZBBQ_IconsRegistered = bpy.utils.previews.new()

        for iconName in ZBBQ_Icons:

            iconFilename = dirIcons + os.sep + ZBBQ_Icons[iconName].relativePath + iconName + ZBBQ_Icons[iconName].ext

            ZBBQ_IconsRegistered.load(iconName, iconFilename, 'IMAGE')

            ZBBQ_Icons[iconName].preview = ZBBQ_IconsRegistered[iconName]
            ZBBQ_Icons[iconName].name = iconName


def unregister():

    global ZBBQ_IconsRegistered
    if ZBBQ_IconsRegistered:
        bpy.utils.previews.remove(ZBBQ_IconsRegistered)
        ZBBQ_IconsRegistered = None


if __name__ == "__main__":
    pass
