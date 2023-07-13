def plating_poll(cls, context):
    return context.active_object and \
        ((context.active_object.type == 'MESH' and \
        context.active_object.mode == 'OBJECT') or \
        (context.active_object.type == 'MESH' and \
        context.active_object.mode == 'EDIT' and \
        context.scene.tool_settings.mesh_select_mode[2]) or \
        (context.active_object.type == 'MESH' and \
        context.active_object.mode == 'EDIT' and \
        context.scene.tool_settings.mesh_select_mode[1]))