bl_info = {
    'name': 'ConjureSDF',
    'description': 'SDF Modelling tools',
    'author': 'João Desager',
    'version': (0, 1, 5),
    'blender': (3, 3, 9),
    'doc_url': 'https://youtube.com/playlist?list=PLI9-AusNnApr21k2uiQgcBeOo0oSf0g5_',
    'tracker_url': 'https://twitter.com/JohnKazArt',
    'category': '3D View'
}



def register():
    from .addon.registration import register_addon
    register_addon()

def unregister():
    from .addon.registration import unregister_addon
    unregister_addon()
