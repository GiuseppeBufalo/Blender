
def get_3dview_area(context):
    for screen in context.workspace.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                return area

def get_3dview_space(area):
    for space in area.spaces:
        if space.type == 'VIEW_3D':
            return space
