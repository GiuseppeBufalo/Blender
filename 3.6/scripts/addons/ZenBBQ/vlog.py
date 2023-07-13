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

# Copyright 2021, Alex Zhornyak

""" Logging """

import sys


class Log:

    ENABLE_DEBUG = False

    @classmethod
    def debug(cls, *args, **kwargs):
        if cls.ENABLE_DEBUG:
            print('[Zen BBQ] DEBUG:', *args, **kwargs)

    @classmethod
    def info(cls, *args, **kwargs):
        print('[Zen BBQ] INFO:', *args, **kwargs)

    @classmethod
    def warn(cls, *args, **kwargs):
        print('[Zen BBQ] WARN:', *args, **kwargs)

    @classmethod
    def error(cls, *args, **kwargs):
        print('[Zen BBQ] ERROR:', *args, **kwargs, file=sys.stderr)
