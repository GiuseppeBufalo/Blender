
def get_3dview_area(context):
    for screen in context.workspace.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                return area

def get_window_region_from_area(area):
    for region in area.regions:
        if region.type == 'WINDOW':
            return region, region.data
