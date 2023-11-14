

def setup_surface_snapping(scene):
    if scene.DM.enable_surface_snapping:
        settings = scene.tool_settings

        settings.snap_elements = {'FACE'}
        settings.snap_target = 'MEDIAN'
        settings.use_snap_align_rotation = True
