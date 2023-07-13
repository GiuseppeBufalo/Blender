import bpy

from bpy.types import Panel
from bpy.props import StringProperty, BoolProperty

from ... import utility


class BC_PT_error_log(Panel):
    bl_label = 'Error Encountered'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'


    @classmethod
    def poll(cls, context):
        active = utility.tool.active()
        return active and active.idname == utility.tool.name


    def draw(self, context):
        layout = self.layout

        primary = True
        secondary = False

        # UI Width
        units_x = 30

        row = layout.row()
        row.alert = True
        row.alignment = 'CENTER'
        row.label(text=F'{utility.name} Error Report')

        row = layout.row()

        row = layout.row()
        for error, elem in utility.error_elem.items():
            if primary:
                sub = row.row()
                sub.alignment = 'LEFT'
                sub.label(text='Failure:')
                primary = False

            elif not secondary:
                row = layout.row()
                sub = row.row()
                sub.alignment = 'LEFT'
                sub.label(text='Resulting in:')
                secondary = True

            row = layout.row()
            for i, e in enumerate(elem['header'].split(':')):
                sub = row.row()
                sub.alignment = 'LEFT' if i == 0 else 'CENTER'
                sub.alert = i == 0
                sub.label(text=F'  {e}{":" if i == 0 else ""}')

            # UI Width
            _units_x = len(elem['header'] + str(elem['count'])) / 2
            if _units_x > units_x:
                units_x = _units_x

            sub = row.row()
            sub.alignment = 'RIGHT'
            sub.alert = True
            sub.label(text=F'    Count: {elem["count"]}')

            line = elem['body'].split('\n')[-3]
            strip_leading_quote = line.split('"')[1]

            path_type = '\\' # could probably use a lib but this is easy enough
            if strip_leading_quote.split(path_type)[0] == strip_leading_quote:
                path_type = '/'

            name_split = strip_leading_quote.split(F'{utility.name}{path_type}')[-1]
            path_split = name_split[:-3].split(path_type)

            row = layout.row()
            sub = row.row()
            sub.alignment = 'RIGHT'

            ssub = sub.row()
            ssub.active = False
            ssub.alignment = 'RIGHT'
            ssub.label(text='')
            for i, module in enumerate(path_split):
                if not module:
                    continue

                arrow = u'   \N{RIGHTWARDS ARROW}'
                if i + 1 == len(path_split):
                    arrow = ''

                ssub.label(text=F'{module}{arrow}')

            ulambda = u'\N{GREEK SMALL LETTER LAMDA}'
            sub.label(text=F'{ulambda}   {line.split(",")[-1][1:].split("in ")[1]}')

            ssub = sub.row()
            ssub.alignment = 'RIGHT'
            ssub.alert = True
            ssub.label(text=line.split(',')[1][1:])

        # UI Width
        layout.ui_units_x = int(units_x)
