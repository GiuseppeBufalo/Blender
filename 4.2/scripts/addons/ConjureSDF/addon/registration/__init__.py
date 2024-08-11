import bpy



def register_addon():

    # Properties
    from ..property import register_properties
    register_properties()


    from ..engine import register_render_engines
    register_render_engines()

    from ..meshing import register_meshing
    register_meshing()


    # Operators
    from ..operator import register_operators
    register_operators()

    # Menus
    from ..menu import register_menus
    register_menus()



def unregister_addon():

    # Menus
    from ..menu import unregister_menus
    unregister_menus()

    # Operators
    from ..operator import unregister_operators
    unregister_operators()


    from ..meshing import unregister_meshing
    unregister_meshing()

    from ..engine import unregister_render_engines
    unregister_render_engines()


    # Properties
    from ..property import unregister_properties
    unregister_properties()
