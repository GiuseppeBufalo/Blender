import bpy
import rna_keymap_ui
import inspect

from bpy.props import EnumProperty, BoolProperty, StringProperty, FloatProperty

from .. utils import addon
from .. customize import keymaps


def toggle_n_panel(self, context):
        from .. ui import panels
        classes = (
            panels.CURVEBASH_PT_Panel,
            panels.CURVEBASH_PT_SubPanel_Keymaps,   # Not registering seems to be enough to disable it.
            )

        for cls in classes:
            if self.show_n_panel:
                bpy.utils.register_class(cls)
            else:
                bpy.utils.unregister_class(cls)


class ARMORED_PT_Curve_Basher_Preferences(bpy.types.AddonPreferences):
    bl_idname = addon.get_name()

    # MODAL KITBASHER
    # mk_init_scale : FloatProperty(name='First Scale', default=.1, 
    #         description='Mesh Scale the first time the tool is run in a session on a virgin curve (default = .1)')

    wireframe : BoolProperty(name='Wireframe', default=False, 
            description='Show Wireframe during modal')
    
    outline : BoolProperty(name='Outline', default=True,  
            description='Show Outline during modal')
    
    smoothing : EnumProperty(name='Smooth Shade', default='ANGLE',  
            items=[ ('ANGLE',  'Angle Based', 'Angle based shading'),
                    ('FLAT',   'Flat', 'Flat shading'),
                    ('SMOOTH', 'Smooth', 'Smooth Shading'),   ])
    
    stretch : BoolProperty(name='Stretch', default=True,  
            description='Stretch-fit the kitbash to the length of the curve it\'s applied on')

    stretch_fit_new : BoolProperty(name='Stretch Fit New', default=True,  
            description='Enable curve stretch-fit (simulate X Press) on first time curves with no radius')
    
    array_caps : BoolProperty(name='Array Caps', default=True,  
            description='Enable Caps on Array types (if available)')

    hide_source_caps : BoolProperty(name='Hide Source Caps', default=True,
            description='Geometry for caps is created at the center of the scene and then linked to an array. This option hides that source geometry',)

    autofit_exits_slide : BoolProperty(name='Autofit Exits Slide', default=True,  
            description='Pressing F while using array types will automatically exits Slide Mode')

    autofit_enables_stretch : BoolProperty(name='Autofit Enables Stretch-fit', default=True,  
            description='Pressing F to toggle an array to FIT_CURVE will automatically enable Stretch to Bounds (when not in Slide Mode')
    
    expanded_hud : BoolProperty(name='Expanded HUD', default=True,
            description='Display all properties and shortcuts in the modal HUD',)
    
    system_scale : BoolProperty(name='Adapt to HiDPI', default=True,
            description='Scale the HUD based on your system scale',)

    hud_scale : FloatProperty(name='HUD Scale', default=1,
            description='Make the HUD bigger or smaller',
            min=0.2)

    show_n_panel : BoolProperty(name='Show N Panel', default=True,
            description='Show the Curve Basher tab in Blender\'s N Panel', update=toggle_n_panel)
    
    # WIRE GENERATOR
    # wg_init_scale : FloatProperty(name='First Scale', default=.1, 
    #         description='Mesh Scale the first time the tool is run in a session (default = .1)')


    # RAYCAST CABLE
    # rc_init_scale : FloatProperty(name='First Scale', default=.1, 
    #         description='Mesh Scale the first time the tool is run in a session (default = .1)')


    # DEVELOPER PROPERTIES
    debug : BoolProperty(name='Debug Mode', default=False,
            description='Prints a lot of junk in the console so I can see what the addon is doing (NOT MEANT FOR END USERS)')

    rc_undo_push : BoolProperty(name='Curvecast', default=True,
            description='Extra undo step in the invoke method (sometimes prevents glitches like cables rendering black)')

    wg_undo_push : BoolProperty(name='Wire Generator', default=True,
            description='Extra undo step in the invoke method (sometimes prevents glitches like cables rendering black)')

    mk_override_apply_locations_rotation : BoolProperty(name='Override Apply All Transforms', default=False,
            description='Applying the scale of a  standard Bezier curves transfers that scale to its control points, this setting bypasses that')

    mk_inverse_scale_points : BoolProperty(name='Inverse Scale Curve Points', default=True,
            description='Applying the scale of a standard Bezier curve transfers that scale to its control points, this setting counteracts that effect)')
    
#     mk_override_local_materials : BoolProperty(name='Override Local Materials', default=False,
#             description='Overwrite Local Scene materials with Source Pack materials')

    gravity_dimensions_override : FloatProperty(name='Gravity Min Dimensions', default=0.01,
            description='Gravity volumes misbehave when the surrounding objects have no dimensions, this value is only used in that specific scenario',
            min=0.0001)


    def draw(self, context):

        def draw_keymap(category, idname):
            km = kc.keymaps[category]
            kmi = km.keymap_items[idname]
            layout.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, right, 0)

        layout = self.layout
        layout.use_property_split = False
        
        box = layout.box()
        col = box.column()
        # split = col.split(factor=.3)
        row = col.row(align=True)
        # row.label(text='Quickstart Video')
        row.operator('curvebash.open_url', text='Quickstart Video', icon='FILE_MOVIE').url = 'https://www.youtube.com/watch?v=6UesTk-pUNk'
        row.separator()
        row.operator('curvebash.open_url', text='What\'s New?', icon='FILE_MOVIE').url = 'https://www.youtube.com/watch?v=ILPQUOWS2e0'
        layout.separator()

        layout.use_property_split = False

        layout.label(text='KEYMAPS:')

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user                 # keyconfigs.addon is not saved across sessions
                                                    
        box = layout.box()
        box.label(text='NEVER DELETE KEYMAPS, only Disable or Edit them!!!', icon='ERROR')
        sub = box.box()
        row = sub.row()
        
        row.label(text='TIP: Some tools do different things depending what mode you\'re in.')#; row.operator('wm.url_open', text='', icon='FILE_MOVIE').url = 'www.youtube.com'
        # layout.separator()
        box.separator()

        box.label(text='\u2022 Curvebasher / Preset Browser :')

        col = box.column()   # Why even use a column? shut up and learn!

        split = col.split(factor=.15)
        left = split.row()
        right = split.row()
        left.label(text='Object')
        draw_keymap(category='Object Mode', idname='curvebash.kitbasher_modal')

        split = col.split(factor=.15)
        left = split.row()
        right = split.row()
        left.label(text='Edit Mesh')
        draw_keymap(category='Mesh', idname='curvebash.kitbasher_modal')

        split = col.split(factor=.15)
        left = split.row()
        right = split.row()
        left.label(text='Edit Curve')
        draw_keymap(category='Curve', idname='curvebash.kitbasher_modal')

        box.separator()

        box.label(text='\u2022 Curvecast :')

        col = box.column()

        split = col.split(factor=.15)
        left = split.row()
        right = split.row()
        left.label(text='Object')
        draw_keymap(category='Object Mode', idname='curvebash.raycast_curve')

        box.separator()

        # box.label(text='\u2022 Wire Generator :')

        # col = box.column()

        # split = col.split(factor=.15)
        # left = split.row()
        # right = split.row()
        # left.label(text='Object')
        # draw_keymap(category='Object Mode', idname='object.curvebash_wire_generator')

        # split = col.split(factor=.15)
        # left = split.row()
        # right = split.row()
        # left.label(text='Edit Curve')
        # draw_keymap(category='Curve', idname='curvebash.raycast_curve')

        layout.use_property_split = True

        layout.label(text='USER INTERFACE:')
        box = layout.box()
        box.prop(self, 'show_n_panel')

        # layout.label(text='TOOL OPTIONS:')

        # MODAL KITBASHER >> --------------------------
        split = layout.split(factor=.5)
        box = split.box()
        box.label(text='Curvebasher / Preset Browser:')

        col = box.column(heading='Display')
        col.prop(self, 'smoothing')
        col.separator()

        col = box.column(heading='In-Modal')
        col.prop(self, 'wireframe')
        col.prop(self, 'outline')
        box.separator()

        box = box.column(heading='Array')
        box.prop(self, 'array_caps')
        box.prop(self, 'hide_source_caps')
        # box.prop(self, 'autofit_exits_slide')
        box.prop(self, 'autofit_enables_stretch')
        box.separator()

        col = box.column(heading='Other')
        col.prop(self, 'stretch_fit_new')
        box.separator()

        col = box.column(heading='HUD')
        col.prop(self, 'expanded_hud')
        col.prop(self, 'system_scale')
        col.prop(self, 'hud_scale')

        # # WIRE GENERATOR >> --------------------------
        # split = layout.split(factor=.5)
        # box = split.box()
        # box.label(text='Wire Generator:')
        # box.prop(self, 'wg_init_scale')
        
        # # RAYCAST CABLE >> --------------------------
        # split = layout.split(factor=.5)
        # box = split.box()
        # box.label(text='Raycast Cable:')
        # box.prop(self, 'rc_init_scale')

        box = layout.box()
        box.label(text='DEVELOPER OPTIONS - Do not touch!', icon='ERROR')
        col = box.column()
        col.prop(self, 'debug', toggle=True)
        col.separator()
        
        col = box.column(heading='Undo Push')
        col.prop(self, 'rc_undo_push')
        col.prop(self, 'wg_undo_push')
        col.separator()
        
        col = box.column(heading='Scale Fix')
        col.label(text='Curvebash Browser:')
        col.prop(self, 'mk_override_apply_locations_rotation')
        col.prop(self, 'mk_inverse_scale_points')
        # col = box.column()
        # col.prop(self, 'mk_override_local_materials')

        col = box.column(heading='')
        col.label(text='Wire Generator:')
        col.prop(self, 'gravity_dimensions_override')





classes = (
    ARMORED_PT_Curve_Basher_Preferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
