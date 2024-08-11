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

# Copyright 2022, Dmitry Aleksandrovich Maslov (ABTOMAT)

import os
import shutil

from PIL import Image
# try:
#     from PIL import Image
# except ImportError:
#     import Image

import json


folderTemplates = 'templates'
folderIcons = 'icons'

jsonNamedColors = os.path.dirname(__file__) + os.sep + os.pardir + os.sep + 'namedColors.json'


# Reading named colors from json

fileNamedColorsJSON = open(jsonNamedColors)
namedColors = json.load(fileNamedColorsJSON)
fileNamedColorsJSON.close()

iconSetNames = []

print("Scanning for templates...")
for entry in os.scandir(folderTemplates):
    if entry.is_dir():
        iconSetNames.append(entry.name)

if not os.path.isdir(folderIcons):
    print(f'Directory "{folderIcons}" does not exist, creating it.')
    os.mkdir(folderIcons)

for iconSetName in iconSetNames:

    iconSetTemplatePath = folderTemplates + os.sep + iconSetName
    iconSetResultPath = folderIcons + os.sep + iconSetName

    if not os.path.isdir(iconSetResultPath):

        print(f'Directory "{iconSetResultPath}" does not exist, creating it.')
        os.mkdir(iconSetResultPath)

    else:

        print(f"{iconSetResultPath} already exists, removing its contents if any")

        with os.scandir(iconSetResultPath) as entries:
            for entry in entries:
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)

    print(f'Generating "{iconSetName}" Icon Set')

    for direction in ["45", "90"]:

        templateInner = Image.open(iconSetTemplatePath + os.sep + direction + "-base.png")
        templateOuter = Image.open(iconSetTemplatePath + os.sep + direction + "-overlay.png")

        for color in namedColors:

            templateInnerColored = templateInner.copy()

            pixdata = templateInnerColored.load()
            for y in range(templateInnerColored.size[1]):
                for x in range(templateInnerColored.size[0]):
                    pixdata[x, y] = (int((pixdata[x, y][0]/255.0 * namedColors[color][0]/255.0)*255),
                                     int((pixdata[x, y][1]/255.0 * namedColors[color][1]/255.0)*255),
                                     int((pixdata[x, y][2]/255.0 * namedColors[color][2]/255.0)*255),
                                     pixdata[x, y][3])

            result = Image.alpha_composite(templateInnerColored, templateOuter)

            numpadKeysAndAngles = {}

            if direction == "45":

                numpadKeysAndAngles = {
                    "3": 0,
                    "9": 90,
                    "7": 180,
                    "1": -90
                }

            elif direction == "90":
                numpadKeysAndAngles = {
                    "6": 0,
                    "8": 90,
                    "4": 180,
                    "2": -90
                }

            for numpadKey in numpadKeysAndAngles:
                resultRotated = result.rotate(numpadKeysAndAngles[numpadKey])
                resultRotated.save(iconSetResultPath + os.sep + color+"Position"+numpadKey + ".png", "PNG")

print("Icon generation done!")
