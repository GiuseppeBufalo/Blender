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

""" Logging """

import sys


class Log:

    ENABLE_DEBUG = False

    @classmethod
    def debug(cls, *args, **kwargs):
        if cls.ENABLE_DEBUG:
            print('UV DEBUG:', *args, **kwargs)

    @classmethod
    def debug_header(cls, *args):
        if cls.ENABLE_DEBUG:
            print(f' {str(*args):-^120} ')

    @classmethod
    def debug_header_short(cls, *args):
        if cls.ENABLE_DEBUG:
            print(f'\t\t{str(*args):=^50}')

    @classmethod
    def info(cls, *args, **kwargs):
        print('UV INFO:', *args, **kwargs)

    @classmethod
    def split(cls, *args, **kwargs):
        print('\n', *args, **kwargs)

    @classmethod
    def warn(cls, *args, **kwargs):
        print('UV WARN:', *args, **kwargs)

    @classmethod
    def error(cls, *args, **kwargs):
        print('UV ERROR:', *args, **kwargs, file=sys.stderr)
