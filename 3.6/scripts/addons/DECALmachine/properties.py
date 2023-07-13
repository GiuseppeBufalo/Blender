import bpy
from bpy.props import BoolProperty, FloatVectorProperty, FloatProperty, EnumProperty, IntProperty, StringProperty, PointerProperty, CollectionProperty, IntVectorProperty
import os
from mathutils import Matrix
from . utils.math import flatten_matrix
from . utils.system import abspath, load_json, save_json
from . utils.registration import get_prefs
from . utils.batch import toggle_glossyrays, toggle_parallax, toggle_normaltransfer_render, toggle_normaltransfer_viewport, toggle_surface_snapping, toggle_color_interpolation
from . utils.batch import switch_alpha_blendmode, change_ao_strength, invert_infodecals, switch_edge_highlights, toggle_pack_images, toggle_material_visibility, toggle_texture_visibility, toggle_nodetree_visibility, toggle_decaltype_collection_visibility, toggle_decalparent_collection_visibility
from . utils.collection import sort_into_collections, purge_decal_collections
from . utils.material import get_trimsheet_nodes, get_trimsheetgroup_from_trimsheetmat, get_trimsheet_textures, set_node_names_of_atlas_material, get_atlas_textures, get_atlas_nodes
from . utils.trim import set_node_names_of_trimsheet, create_trimsheet_json
from . utils.decal import set_props_and_node_names_of_decal
from . utils.atlas import reset_trim_scale, stretch_trim_scale
from . items import interpolation_items, alpha_blendmode_items, edge_highlights_items, auto_match_items, align_mode_items
from . items import create_bake_resolution_items, create_bake_aosamples_items, bake_supersample_items, create_bake_emissionsamples_items
from . items import create_type_items, create_decaltype_items, create_infotype_items, create_infotext_align_items, create_trimtype_items, update_library_version_items, update_library_version_30_items
from . items import decaltype_items, texturetype_items, pack_images_items, trimtexturetype_items, atlastexturetype_items
from . items import export_type_items, create_atlascreation_type_items, create_atlas_type_items, create_atlas_mode_items, create_atlas_prepack_items, create_atlas_trim_sort_items, exporttexturetype_items, create_atlas_size_mode_items, export_atlas_model_format_items



class DecalLibsCollection(bpy.types.PropertyGroup):
    def update_islocked(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        assetspath = get_prefs().assetspath
        library = self.name

        libtype = 'Trims' if self.istrimsheet else 'Decals'

        hasislocked = os.path.exists(os.path.join(assetspath, libtype, library, ".islocked"))

        if hasislocked:
            self.avoid_update = True
            self.islocked = True

    def update_ispanel(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        assetspath = get_prefs().assetspath
        library = self.name

        hasispanel = os.path.exists(os.path.join(assetspath, 'Decals', library, ".ispanel"))

        if hasispanel:
            self.avoid_update = True
            self.ispanel = True

    def update_isdirty(self, context):
        context.preferences.is_dirty = True

    name: StringProperty()
    isvisible: BoolProperty(default=True, name="Toggle Visibility", description="Hidden Libraries will not show up in the Pie Menu", update=update_isdirty)
    ispanel: BoolProperty(default=False, name="Mark as Panel Decal Library", description="Marked Librares will be accessed by tools like Slice, GPanel and EPanel\nChanging this requires Library Reload", update=update_ispanel)
    ispanelcycle: BoolProperty(default=True, name="Toggle Ability to cycle through Library with Adjust tool", description='Hidden Libaries will not be available for "Panel Scrolling" with the Adjust tool', update=update_isdirty)
    islocked: BoolProperty(default=False, name="Lock a library to prevent User Decal Creation and Removal. Requires Library Reload\nSupplied Libraries can't be unlocked", update=update_islocked)

    istrimsheet: BoolProperty(default=False, description="Is Trim Sheet Library")

    avoid_update: BoolProperty(default=False)


class DecalScalesCollection(bpy.types.PropertyGroup):
    name: StringProperty()
    index: IntProperty()
    scale: FloatVectorProperty(name="Scale")


class ExcludeCollection(bpy.types.PropertyGroup):
    name: StringProperty()
    index: IntProperty()


class PreBakePreviewMaterialsCollection(bpy.types.PropertyGroup):
    name: StringProperty()
    index: IntProperty()
    material: PointerProperty(name="Pre-Preview Material", type=bpy.types.Material)


class TrimsCollection(bpy.types.PropertyGroup):
    def update_name(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        self.avoid_update = True
        self.name = self.name.strip()

        sheet = context.active_object if context.active_object and context.active_object.DM.istrimsheet else None
        if sheet:
            create_trimsheet_json(context.active_object)

    def update_ispanel(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        sheet = context.active_object if context.active_object and context.active_object.DM.istrimsheet else None
        if sheet:
            create_trimsheet_json(sheet)

    def update_isempty(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        sheet = context.active_object if context.active_object and context.active_object.DM.istrimsheet else None
        if sheet:

            if self.isempty:
                for trim in sheet.DM.trimsCOL:
                    if trim != self:
                        trim.isempty = False

            sheet.select_set(True)

            create_trimsheet_json(sheet)

    name: StringProperty(update=update_name)
    uuid: StringProperty(name="trim uuid")
    mx: FloatVectorProperty(name="Matrix", size=16, default=flatten_matrix(Matrix()), subtype="MATRIX")

    isactive: BoolProperty(default=False)
    isempty: BoolProperty(default=False, name="Mark Trim as Empty\nAn Empty Trim is useful for Unwraping large sections of a mesh without detail", update=update_isempty)
    ispanel: BoolProperty(default=False, description="Mark Trim as a Panel\nPanel Trims are treated differently when Unwrapping", update=update_ispanel)

    def update_hide(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        sheet = context.active_object if context.active_object and context.active_object.DM.istrimsheet else None
        if sheet:
            sheet.select_set(True)

            create_trimsheet_json(sheet)

    def update_hide_select(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        sheet = context.active_object if context.active_object and context.active_object.DM.istrimsheet else None
        if sheet:
            sheet.select_set(True)

            create_trimsheet_json(sheet)

    def update_prepack(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None

        if atlas:
            sources = atlas.DM.get('sources')

            if sources:
                sources[self.uuid]['prepack'] = self.prepack

                if self.prepack == 'NONE':
                    reset_trim_scale(atlas, self)

                else:
                    stretch_trim_scale(atlas, self)
                atlas.select_set(True)

    hide: BoolProperty(default=False, name="Toggle Visibility", update=update_hide)
    hide_select: BoolProperty(default=False, name="Toggle Selectability", update=update_hide_select)



    original_size: IntVectorProperty(size=2)
    dummy: PointerProperty(type=bpy.types.Object)
    prepack: EnumProperty(name='Panel Decal Pre-Pack Mode', items=create_atlas_prepack_items, description='Pre-Pack Panel Decal', default='STRETCH', update=update_prepack)


    avoid_update: BoolProperty()


class TrimMapsCollection(bpy.types.PropertyGroup):
    name: StringProperty()
    index: IntProperty()

    texture: StringProperty()

    def update_parallax_amount(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        sheet = context.active_object
        if sheet:
            mat = sheet.active_material

            if mat:
                nodes = get_trimsheet_nodes(mat)

                pg = nodes.get('PARALLAXGROUP')

                if pg:
                    pg.inputs[0].default_value = self.parallax_amount

                    create_trimsheet_json(sheet)

    def update_connect_alpha(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        sheet = context.active_object
        if sheet:
            mat = sheet.active_material

            if mat:
                nodes = get_trimsheet_nodes(mat)
                alpha = nodes.get('ALPHA')

                if alpha:
                    tree = mat.node_tree

                    if self.connect_alpha:
                        tsg = get_trimsheetgroup_from_trimsheetmat(mat)
                        tree.links.new(alpha.outputs[0], tsg.inputs['Alpha'])

                        mat.blend_method = 'BLEND'

                    else:
                        for link in alpha.outputs[0].links:
                            tree.links.remove(link)

                        mat.blend_method = 'OPAQUE'

                    create_trimsheet_json(sheet)


    resolution: IntVectorProperty("Trim Map Resolution", size=2, default=(512, 512))
    parallax_amount: FloatProperty(name="Parallax Amount", default=0.01, update=update_parallax_amount, min=0, step=0.1)
    connect_alpha: BoolProperty(name="Show Alpha", default=False, update=update_connect_alpha)

    avoid_update: BoolProperty()


class AtlasesCollection(bpy.types.PropertyGroup):
    def update_islocked(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        assetspath = get_prefs().assetspath
        name = self.name

        folder = 'Trims' if self.istrimsheet else 'Atlases'

        hasislocked = os.path.exists(os.path.join(assetspath, folder, name, ".islocked"))

        if hasislocked:
            self.avoid_update = True
            self.islocked = True

    name: StringProperty()

    isenabled: BoolProperty(default=True, name="Enable for Export")
    islocked: BoolProperty(default=False, name="Prevent User Overwrite or Removal\nSupplied Atlases can't be unlocked", update=update_islocked)

    istrimsheet: BoolProperty(default=False, description="Is Trim Sheet")

    avoid_update: BoolProperty(default=False)


class PreAtlasMaterialsCollection(bpy.types.PropertyGroup):
    name: StringProperty()
    index: IntProperty()

    material: PointerProperty(name="Pre-Atlas Material", type=bpy.types.Material)
    material_index: IntProperty(name="Material Index")


class PreJoinDecalsCollection(bpy.types.PropertyGroup):
    name: StringProperty()
    index: IntProperty()

    obj: PointerProperty(name="Pre-Join Deccal Object", type=bpy.types.Object)
    isactive: BoolProperty(name="is active", default=False)


class AtlasChannelPackCollection(bpy.types.PropertyGroup):
    def update_name(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        name = self.name.strip().replace(' ', '_').replace(os.sep, '-')

        self.avoid_update = True
        self.name = name

    name: StringProperty(name="Name of Channel Packed Texture", default='channel_pack', update=update_name)

    isenabled: BoolProperty(default=True, description="Enable for Export")

    red: EnumProperty(name="Red Channel", items=exporttexturetype_items, default='NONE')
    green: EnumProperty(name="Green Channel", items=exporttexturetype_items, default='NONE')
    blue: EnumProperty(name="Blue Channel", items=exporttexturetype_items, default='NONE')
    alpha: EnumProperty(name="Alpha Channel", items=exporttexturetype_items, default='NONE')


    avoid_update: BoolProperty(default=False)



class DecalSceneProperties(bpy.types.PropertyGroup):


    register_panel_creation: BoolProperty(name="Show Creation Panel", default=False)
    register_panel_export: BoolProperty(name="Show Export Panel", default=False)
    register_panel_update: BoolProperty(name="Show Update Panel", default=False)
    register_panel_help: BoolProperty(name="Show Help Panel", default=True)



    show_panel_defaults: BoolProperty(description="Show Settings governing Decal Default Behavior ", default=False)
    show_panel_tools: BoolProperty(description="Show secondary Tools, not shown in the Pie Menu", default=False)
    show_panel_utils: BoolProperty(description="Show rarely used Utilities, which can help with Cleanup and Repair", default=False)
    show_panel_developer: BoolProperty(default=True)



    globalscale: FloatProperty(name="Scale", description="Global Scale modifier.\nAdjust as needed, if decals come into the scene too big or small, for the scale you are working at\nGlobal Scale is also multiplied with Panel Width.", default=1, precision=3, min=0.001, max=1000, step=1)
    individualscales: CollectionProperty(type=DecalScalesCollection)
    panelwidth: FloatProperty(name="Panel Width", description="Default Panel Width, used by Slice, GPanel and EPanel, and changed by Adjust", default=0.04, precision=3, step=1, min=0.0000001)
    height: FloatProperty(name="Height", description="Default Decal Height - mid_level in Displace modifier", default=0.9998, precision=4, step=0.001, max=1, min=0.5)

    quickinsertlibrary: StringProperty()
    quickinsertdecal: StringProperty()
    quickinsertisinstant: BoolProperty()
    quickinsertistrim: BoolProperty()



    def update_collections(self, context):

        if self.avoid_update:
            self.avoid_update = False
            return

        decals = [obj for obj in bpy.data.objects if obj.DM.isdecal and not obj.DM.isbackup and context.scene in obj.users_scene]

        for obj in decals:
            sort_into_collections(context, obj, purge=False)

        purge_decal_collections(debug=True)

        if self.collection_decaltype and len(bpy.data.scenes) > 1:
            self.avoid_update = True
            self.collection_decaltype = False

    def update_hide_materials(self, context):
        toggle_material_visibility(self.hide_materials)

    def update_hide_textures(self, context):
        toggle_texture_visibility(self.hide_textures)

    def update_hide_nodetrees(self, context):
        toggle_nodetree_visibility(self.hide_nodetrees)

    def update_hide_decaltype_collections(self, context):
        toggle_decaltype_collection_visibility(self.hide_decaltype_collections)

    def update_hide_decalparent_collections(self, context):
        toggle_decalparent_collection_visibility(self.hide_decalparent_collections)

    def update_glossyrays(self, context):
        toggle_glossyrays(self.glossyrays)

    def update_parallax(self, context):
        toggle_parallax(self.parallax)

    def update_normaltransfer_render(self, context):
        toggle_normaltransfer_render(self.normaltransfer_render)

    def update_normaltransfer_viewport(self, context):
        toggle_normaltransfer_viewport(self.normaltransfer_viewport)

    def update_color_interpolation(self, context):
        toggle_color_interpolation(self.color_interpolation)

    def update_alpha_blendmode(self, context):
        switch_alpha_blendmode(self.alpha_blendmode)

    def update_ao_strength(self, context):
        change_ao_strength(self.ao_strength)

    def update_invert_infodecals(self, context):
        invert_infodecals(self.invert_infodecals)

    def update_edge_highlights(self, context):
        switch_edge_highlights(self.edge_highlights)

    def update_pack_images(self, context):
        toggle_pack_images(self.pack_images)

    def update_enable_surface_snapping(self, context):
        toggle_surface_snapping(self.update_enable_surface_snapping)

    collection_decaltype: BoolProperty(name="Decal Type Collection", description="Create Decal Type Collections", default=True, update=update_collections)
    collection_decalparent: BoolProperty(name="Decal Parent Collection", description="Create Decal Collections based on Decal Parent Object's Membership", default=False, update=update_collections)
    collection_active: BoolProperty(name="Active Collection", description="Add Decals to Active Collection", default=False, update=update_collections)

    hide_materials: BoolProperty(name="Hide Materials", description="Hide Decal Materials from Blenders Material Lists", default=True, update=update_hide_materials)
    hide_textures: BoolProperty(name="Hide Textures", description="Hide Decal Textures from Blender's Image Lists", default=True, update=update_hide_textures)
    hide_nodetrees: BoolProperty(name="Hide Node Trees", description="Hide Decal Node Trees from Blender's Node Group Lists", default=True, update=update_hide_nodetrees)
    hide_decaltype_collections: BoolProperty(name="Hide Decal Type Collections", description="Hide Decal-Type Collections from BatchOps", default=False, update=update_hide_decaltype_collections)
    hide_decalparent_collections: BoolProperty(name="Hide Decal Parent Collections", description="Hide Decal-Paretn Collections from BatchOps", default=False, update=update_hide_decalparent_collections)

    glossyrays: BoolProperty(name="Glossy Rays", description="Enable Glossy Rays for Decals in Cycles", default=True, update=update_glossyrays)
    parallax: BoolProperty(name="Parallax", description="Enable the Parallax Shader Effect for normal mapped Decals and Trim Sheets", default=True, update=update_parallax)

    normaltransfer_render: BoolProperty(name="Normal Transfer Render", description="Use Transfered Normals for Rendering", default=True, update=update_normaltransfer_render)
    normaltransfer_viewport: BoolProperty(name="Normal Transfer Viewport", description="Show Transfered Normals in the Viewport", default=True, update=update_normaltransfer_viewport)

    color_interpolation: EnumProperty(name="Color Interpolation", description="Interpolate Decal Color Maps", items=interpolation_items, default="Closest", update=update_color_interpolation)
    alpha_blendmode: EnumProperty(name="Alpha Blend Mode", description="Set Alpha Blending, relevant especially for overlapping Decals", items=alpha_blendmode_items, default="BLEND", update=update_alpha_blendmode)

    ao_strength: FloatProperty(name="AO Strength", description="Amount of AO mixed into Decal Material's Color and Roughness", default=1, min=0, max=1, step=0.1, update=update_ao_strength)
    invert_infodecals: BoolProperty(name="Invert Info Decals", description="Invert Decal Color Maps", default=False, update=update_invert_infodecals)
    edge_highlights: EnumProperty(name="Edge Highlights", description="Amount of Curvature mixed into Decal Material's Color", items=edge_highlights_items, default="0.5", update=update_edge_highlights)

    pack_images: EnumProperty(name="Pack Images", description="Store Textures in blend file or on disk", items=pack_images_items, default="UNPACKED", update=update_pack_images)

    align_mode: EnumProperty(name="Align Mode", items=align_mode_items, default="RAYCAST")
    auto_match: EnumProperty(name="Auto-Match Materials", description="Match Materials when Inserting them or when using the Re-Apply tool", items=auto_match_items, default="AUTO")
    enable_surface_snapping: BoolProperty(name="Enable Surface Snapping", description="Setup Surface Snapping, whenever a decal is inserted.\nThis changes the existing snapping settings", default=True, update=update_enable_surface_snapping)

    revision: StringProperty()



    def update_update18librarypath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        self.avoid_update = True

        if self.update18librarypath:
            sourcepath = abspath(self.update18librarypath)

            if os.path.exists(sourcepath):

                if os.path.exists(os.path.join(sourcepath, ".is280")):
                    self.update18librarypath = sourcepath

                    assetspath = get_prefs().assetspath

                    if os.path.dirname(sourcepath) == os.path.join(assetspath, 'Decals'):
                        self.avoid_update = True
                        self.updatelibraryinplace = True

                    return

        self.update18librarypath = "CHOOSE A 1.8 - 1.9.4 DECAL LIBRARY!"

    def update_update20librarypath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        self.avoid_update = True

        if self.update20librarypath:
            sourcepath = abspath(self.update20librarypath)

            if os.path.exists(sourcepath):

                if os.path.exists(os.path.join(sourcepath, ".is20")):
                    self.update20librarypath = sourcepath

                    if os.path.exists(os.path.join(sourcepath, ".istrimsheet")) and os.path.exists(os.path.join(sourcepath, "data.json")):
                        self.updatelibraryistrimsheet = True

                    else:
                        self.updatelibraryistrimsheet = False

                    assetspath = get_prefs().assetspath

                    if os.path.dirname(sourcepath) == os.path.join(assetspath, 'Trims' if self.updatelibraryistrimsheet else 'Decals'):
                        self.avoid_update = True
                        self.updatelibraryinplace = True

                    return

        self.update20librarypath = "CHOOSE A 2.0 - 2.0.1 DECAL LIBRARY!"
        self.updatelibraryistrimsheet = False

    def update_update21librarypath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        self.avoid_update = True

        if self.update21librarypath:
            sourcepath = abspath(self.update21librarypath)

            if os.path.exists(sourcepath):

                if os.path.exists(os.path.join(sourcepath, ".is21")):
                    self.update21librarypath = sourcepath

                    if os.path.exists(os.path.join(sourcepath, ".istrimsheet")) and os.path.exists(os.path.join(sourcepath, "data.json")):
                        self.updatelibraryistrimsheet = True

                    else:
                        self.updatelibraryistrimsheet = False

                    assetspath = get_prefs().assetspath

                    if os.path.dirname(sourcepath) == os.path.join(assetspath, 'Trims' if self.updatelibraryistrimsheet else 'Decals'):
                        self.avoid_update = True
                        self.updatelibraryinplace = True

                    return

        self.update21librarypath = "CHOOSE A 2.1 - 2.4.1 DECAL LIBRARY!"
        self.updatelibraryistrimsheet = False

    def update_updatelibraryinplace(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if not self.updatelibraryinplace:
            assetspath = get_prefs().assetspath
            sourcepath = self.update20librarypath if self.updatelibraryversion == '20' else self.update18librarypath if self.updatelibraryversion == '18' else self.update14librarypath

            if self.updatelibraryversion == '20':
                if os.path.dirname(sourcepath) == os.path.join(assetspath, 'Trims' if self.updatelibraryistrimsheet else 'Decals'):
                    self.avoid_update = True
                    self.updatelibraryinplace = True

            else:
                if os.path.dirname(sourcepath) == os.path.join(assetspath, 'Decals'):
                    self.avoid_update = True
                    self.updatelibraryinplace = True


    updatelibraryversion: EnumProperty(name="Legacy Decal Library to Update", items=update_library_version_items, default="20")
    updatelibraryversion30: EnumProperty(name="Legacy Decal Library to Update", items=update_library_version_30_items, default="21")

    update18librarypath: StringProperty(name="Update 1.8 Library Path", subtype='DIR_PATH', update=update_update18librarypath)
    update20librarypath: StringProperty(name="Update 2.0 Library Path", subtype='DIR_PATH', update=update_update20librarypath)
    update21librarypath: StringProperty(name="Update 2.5 Library Path", subtype='DIR_PATH', update=update_update21librarypath)

    updatelibraryinplace: BoolProperty(name="Update in place", default=False, update=update_updatelibraryinplace)
    updatelibraryistrimsheet: BoolProperty(name="Update Library is Trim Decal Libarary", default=False)



    create_type: EnumProperty(name="Create Type", description="Create Type", items=create_type_items, default="DECAL")



    update_fix_legacy_normals: BoolProperty(name="Fix Legacy Normals", default=True)
    update_keep_old_thumbnails: BoolProperty(name="Keep Old Thumbnails", default=False)
    update_store_uuid_with_old_decals: BoolProperty(name="Store UUID with Old Decals", default=True)

    addlibrary_decalname: StringProperty(name="Name (optional)")
    addlibrary_use_filename: BoolProperty(name="Use Image File Name", default=True)
    addlibrary_skip_index: BoolProperty(name="Skip the Index for Decal Names created from File Names", default=False)


    create_decaltype: EnumProperty(name="Decal Type", description="Decal Type", items=create_decaltype_items, default="SIMPLESUBSET")
    create_infotype: EnumProperty(name="Info Decal Creation Type", description="Info Decal Creation Type", items=create_infotype_items, default="IMAGE")
    create_infoimg_crop: BoolProperty(name="Crop", description="Crop transparent areas from Source Images", default=True)
    create_infoimg_padding: IntProperty(name="Padding", description="Add Padding to Source Images", default=1)
    create_infoimg_batch: BoolProperty(name="Batch", default=False)
    create_infotext: StringProperty(name="Enter Text, use \\n for line breaks", default="")
    create_infotext_color: FloatVectorProperty(name="Text Color and Alpha", subtype='COLOR', default=[1, 1, 1, 1], size=4, min=0, max=1)
    create_infotext_bgcolor: FloatVectorProperty(name="Background Color and Alpha", subtype='COLOR', default=[1, 1, 1, 0], size=4, min=0, max=1)
    create_infotext_align: EnumProperty(name="Align Text", items=create_infotext_align_items, default='left')
    create_infotext_size: IntProperty(name="Size", description="Font Size", default=100)
    create_infotext_padding: IntVectorProperty(name="X and Y Padding", default=[1, 1], size=2)
    create_infotext_offset: IntVectorProperty(name="X and Y Offset", default=[0, 0], size=2)

    create_bake_supersample: EnumProperty(name="Supersample", description="Supersample", items=bake_supersample_items, default="2")
    create_bake_supersamplealpha: BoolProperty(name="Supersample Alpha", description="Super Sample Alpha", default=False)
    create_bake_resolution: EnumProperty(name="Resolution", description="Resolution", items=create_bake_resolution_items, default="256")
    create_bake_aosamples: EnumProperty(name="Samples", description="AO Samples", items=create_bake_aosamples_items, default="256")
    create_bake_aocontrast: FloatProperty(name="Contrast", description="AO Contrast", default=1.5, min=0)
    create_bake_curvaturewidth: FloatProperty(name="Width", description="Curvature Width", default=1.0, min=0)
    create_bake_curvaturecontrast: FloatProperty(name="Contrast", description="Curvature Contrast", default=2.0, min=0)
    create_bake_heightdistance: FloatProperty(name="Distance", description="Height Limit", default=1.0, min=0)
    create_bake_emissive: BoolProperty(name="Bake Emission Map", description="Bake Emission Map (requires emissive materials)", default=False)
    create_bake_emissive_bounce: BoolProperty(name="Bake Emissive Bounce", description="Bake Bounced Light", default=False)
    create_bake_emissionsamples: EnumProperty(name="Samples", description="Emission Bounced Light Samples", items=create_bake_emissionsamples_items, default="1024")
    create_bake_limit_alpha_to_active: BoolProperty(name="Limit Alpha to Active", description="Limit Alpha Map Creation from upwards facing Polygons to Active Object", default=True)
    create_bake_limit_alpha_to_boundary: BoolProperty(name="Limit Alpha to Boundary", description="Limit Alpha Map Creation to polygons on the Boundary", default=False)
    create_bake_flatten_alpha_normals: BoolProperty(name="Flatten Alpha Normals", description="Create perfectly flat Normals for upwards facing Polygons", default=True)
    create_bake_maskmat2: BoolProperty(name="Material 2", description="Bake Material 2 Mask, for Panel Decals creating a Material Separation", default=True)

    create_bake_store_subset: BoolProperty(name="Store Subset Material", description="Store custom Subset Material on the Decal Asset, instead of the default Metal Material", default=False)

    create_bake_inspect: BoolProperty(name="Inspect Bakes", description="After Baking, open the folder to inspect Baked Textures", default=False)
    create_force_uuid: BoolProperty(name="Force specific UUID", description="Force using specific UUID, stored on and retrieved from Decal Source Geometry\nEnabling this risks producing duplicate UUIDs among registered Decals. This is to be avoided", default=False)



    def update_create_trim_import_path(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        self.avoid_update = True
        self.create_trim_import_path = abspath(self.create_trim_import_path)

        datapath = os.path.join(self.create_trim_import_path, 'data.json')

        if os.path.exists(datapath):
            sheetdata = load_json(datapath)

            if sheetdata.get('isatlas'):
                self.create_trim_import_keep_trim_uuids = False


    create_trim_type: EnumProperty(name="Trim Sheet Creation Type", description="Trime Sheet Creation Type", items=create_trimtype_items, default="NEW")
    create_trim_import_path: StringProperty(name="Location of Trim Sheet, defined by data.json and related textures", subtype='DIR_PATH', update=update_create_trim_import_path)
    create_trim_import_keep_trim_uuids: BoolProperty(name="Keep Trim UUIDs", description="Keep the same trim UUIDs as the trims/decals in the imported Sheet/Atlas\nIf you import an Atlas as a Trim Sheet, you should keep this turned OFF\nIf you import a Sheet, that is is registered and that you plan to replace, you should enable this", default=False)
    create_trim_import_keep_sheet_uuid: BoolProperty(name="Keep Sheet UUID", description="Keep the same UUID as the initiated or imported Trim Sheet\nIf you modifiy and intend to replace an existing Sheet, that is registered and used in a blend file, you should enable this!", default=False)



    def update_create_atlas_non_uniform_scale(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        atlas = context.active_object if context.active_object.DM.isatlas else None

        if atlas:
            atlas.select_set(True)

    def update_create_atlas_import_path(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        self.avoid_update = True
        self.create_atlas_import_path = abspath(self.create_atlas_import_path)

    create_atlascreation_type: EnumProperty(name="Atlas Creation Type", description="Atlas Creation Type", items=create_atlascreation_type_items, default="NEW")
    create_atlas_import_path: StringProperty(name="Location of Atlas, defined by data.json and related textures", subtype='DIR_PATH', update=update_create_atlas_import_path)

    create_atlas_type: EnumProperty(name="Atlas Type", items=create_atlas_type_items, default='NORMAL')
    create_atlas_padding: IntProperty(name="Atlas Padding", description="Add this amount of empty sapce in pixels between every Decal in the Atlas", default=4, min=0)
    create_atlas_size_mode: EnumProperty(name="Size Mode", items=create_atlas_size_mode_items, default='SMALLEST')
    create_atlas_resolution: IntProperty(name="Atlas Resolution to aim for", default=2048, min=64)
    create_atlas_resolution_increase: IntProperty(name="Atlas Resolution Increase", description="For every packing attempt, increase the atlas resolution by this amount", default=1, min=1)
    create_atlas_prepack: EnumProperty(name="Pre-Pack Panel Decals", items=create_atlas_prepack_items, default='NONE')
    create_atlas_compensate_height: BoolProperty(name="Compensate Height", description="Adjust Height based on Decal size in relation to Atlas size\nEnsures parallax amount in Atlas is the same as in Scene", default=True)
    create_atlas_normalize_height: BoolProperty(name="Normalize Height", description="Normalize atlas height map, utilizing the maximum value range, while keeping mid grey constant", default=True)
    create_atlas_non_uniform_scale: BoolProperty(name="Non-Uniform Gizmo Scaling", description="Allow non-uniform scaling for decals in Atlas", default=False, update=update_create_atlas_non_uniform_scale)



    export_type: EnumProperty(name="Export Type", description="Export Type", items=export_type_items, default="ATLAS")



    def update_export_atlas_textures_folder(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        stripped = os.path.normpath(self.export_atlas_textures_folder.strip().replace('/', os.sep).replace('\\', os.sep))
        self.avoid_update = True
        self.export_atlas_textures_folder = stripped

    def update_export_atlas_models_folder(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        stripped = os.path.normpath(self.export_atlas_models_folder.strip().replace('/', os.sep).replace('\\', os.sep))
        self.avoid_update = True
        self.export_atlas_models_folder = stripped

    export_atlas_create_collections: BoolProperty(name="Create Atlas Collections", description="Create Collections for Atlased Decals per Atlas used", default=True)
    export_atlas_join_atlased_per_parent: BoolProperty(description="Join atlased Decals per Parent Object", default=True)

    export_atlas_textures: BoolProperty(description="Export Atlas Textures to Export Location set below", default=True)
    export_atlas_models: BoolProperty(description="Export Models to Export Location set below", default=False)

    export_atlas_path: StringProperty(name="Export Path", subtype='DIR_PATH', default=os.path.join(os.path.dirname(__file__), 'assets', 'Export', 'atlas'))
    export_atlas_textures_folder: StringProperty(name="Export Textures Folder", default="Textures", update=update_export_atlas_textures_folder)
    export_atlas_models_folder: StringProperty(name="Export Models Folder", default="Models", update=update_export_atlas_models_folder)
    export_atlas_use_textures_folder: BoolProperty(name="Use Textures Folder", default=True)
    export_atlas_use_models_folder: BoolProperty(name="Use Models Folder", default=True)

    export_atlas_texture_alpha: BoolProperty(name="Export Alpha Map", description="Toggle Alpha Map", default=False)
    export_atlas_texture_ao: BoolProperty(name="Export Ambient Occlusion Map", description="Toggle Ambient Occlusion Map", default=False)
    export_atlas_texture_color: BoolProperty(name="Export Color Map", description="Toggle Color Map", default=True)
    export_atlas_texture_curvature: BoolProperty(name="Export Curvature Map", description="Toggle Curvature Map", default=False)
    export_atlas_texture_emission: BoolProperty(name="Export Emission Map", description="Toggle Emission Map", default=True)
    export_atlas_texture_height: BoolProperty(name="Export Height Map", description="Toggle Height Map", default=False)
    export_atlas_texture_normal: BoolProperty(name="Export Normal Map", description="Toggle Normal Map", default=True)
    export_atlas_texture_material2: BoolProperty(name="Export Material 2 Map", description="Toggle Material 2 Map\nMost likely not needed for Export", default=False)
    export_atlas_texture_metallic: BoolProperty(name="Export Metallic Map", description="Toggle Metallic Map", default=False)
    export_atlas_texture_roughness: BoolProperty(name="Export Roughness", description="Toggle Roughness Map", default=False)
    export_atlas_texture_smoothness: BoolProperty(name="Export Smoothness", description="Toggle Smoothness Map\nSmootheness is inverted Roughness", default=False)
    export_atlas_texture_subset: BoolProperty(name="Export Subset Map", description="Toggle Subset Map", default=False)
    export_atlas_texture_subset_occlusion: BoolProperty(name="Export Subset Occlusion Map", description="Toggle Subset Occlusion Map\nA Subset Map, extended with inverted Ambient Occlusion", default=False)
    export_atlas_texture_white_height: BoolProperty(name="Export White Height Map", description="Toggle White Height Map\nA Height map, with its 50% grey value, shifted to White,\nthereby discarding any depth information lighter than mid grey", default=False)

    export_atlas_texture_channel_packCOL: CollectionProperty(name="Atlas Texture Channel Pack", type=AtlasChannelPackCollection)
    export_atlas_texture_channel_packIDX: IntProperty(name="Channel Packed Atlas Map\nUp to 4 monochromatic maps can packed into a single RGB or RGBA texture")

    export_atlas_model_format: EnumProperty("Export Model Format", items=export_atlas_model_format_items, description="Pick Export Format", default='FBX')
    export_atlas_model_unity: BoolProperty("Export Model to Unity", description="Utilize MACHIN3tools' Unity Export Preparation")



    def update_export_bake_y(self, context):
        if self.export_bake_linked_res:
            self.export_bake_y = self.export_bake_x

    export_bake_x: IntProperty(name="X Resolution", default=1024, min=64, update=update_export_bake_y)
    export_bake_y: IntProperty(name="Y Resolution", default=1024, min=64)
    export_bake_linked_res: BoolProperty(name="Force Square Resolution", default=True, update=update_export_bake_y)
    export_bake_supersample: EnumProperty(name="Supersample", description="Supersample", items=bake_supersample_items, default="0")
    export_bake_samples: IntProperty(name="Samples", description="Render Samples", default=32, min=1)
    export_bake_margin: IntProperty(name="Margin", description="Margins in px", default=3, min=1)
    export_bake_distance: FloatProperty(name="Ray Distance", description="Ray Distance", default=0.001, min=0.001, max=1, precision=4)
    export_bake_triangulate: BoolProperty(name="Triangulate", description="Add Triangulatrion Modidfier before Baking", default=False)

    export_bake_color: BoolProperty(name="Color", description="Bake Color Maps from Info Decals", default=True)
    export_bake_normal: BoolProperty(name="Normal", description="Bake Normal Maps from Simple, Subset and Panel Decals", default=True)
    export_bake_emission: BoolProperty(name="Emission", description="Bake Emission Maps from Simple, Subset, Panel and Info Decals", default=True)
    export_bake_aocurvheight: BoolProperty(name="AO / Curvature / Height", description="Bake AO, Curvature, and Height Maps from Simple, Subset and Panel Decals", default=True)
    export_bake_masks: BoolProperty(name="Masks", description="Bake Masks from Simple, Subset, Panel and Info Decals", default=True)

    export_bake_combine_bakes: BoolProperty(name="Combine Bakes", description="Combine Bakes of multiple objects into a single Texture Sheet\nNote, prepare your UVs in a way, that the combined objects actually share the same 0-1 UV space", default=False)
    export_bake_preview: BoolProperty(name="Preview Bakes", description="Preview Bakes directly on the Object\nThis creates a temporary Material and hides the Decals", default=False)
    export_bake_open_folder: BoolProperty(name="Open Bake Folder", description="After baking, open the location of the textures in the file browser", default=True)
    export_bake_substance_naming: BoolProperty(name="Substance Naming", description="Name baked textures in a way, that allows for automatic assignment in Substance Painter", default=False)



    debug: BoolProperty(default=False)
    avoid_update: BoolProperty(default=False)


class DecalObjectProperties(bpy.types.PropertyGroup):
    uuid: StringProperty(name="decal uuid")

    forced_uuid: StringProperty(name="Forced Decal UUID", description="The forced UUID is stored on and retreived from Decal Source Geometry")
    is_forced_uuid: BoolProperty(name="is forced uuid", description="Decal uses forced uuid from source geometry, and doesn't generate a new one when being added to a Library", default=False)

    version: StringProperty(name="decal version")
    decaltype: EnumProperty(name="decal type", items=decaltype_items, default="NONE")
    decallibrary: StringProperty(name="decal library")
    decalname: StringProperty(name="decal name")
    decalmatname: StringProperty(name="decal material name")

    isdecal: BoolProperty(name="is decal", default=False)
    isbackup: BoolProperty(name="is backup", default=False)
    isprojected: BoolProperty(name="is projected", default=False)
    issliced: BoolProperty(name="is sliced", default=False)

    decalbackup: PointerProperty(name="decal backup object", type=bpy.types.Object)
    projectedon: PointerProperty(name="projected on Object", type=bpy.types.Object)
    slicedon: PointerProperty(name="sliced on Object", type=bpy.types.Object)

    creator: StringProperty(name="Decal Creator")

    backupmx: FloatVectorProperty(name="Backup Matrix in Parent's Local Space", subtype="MATRIX", size=16, default=flatten_matrix(Matrix()))



    prebakepreviewmats: CollectionProperty(name="Pre-BakePreview Materials", type=PreBakePreviewMaterialsCollection)



    def update_trimsIDX(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        for idx, trim in enumerate(self.trimsCOL):
            trim.isactive = True if idx == self.trimsIDX else False

        active = context.active_object
        if active:
            active.select_set(True)

            if active.DM.istrimsheet:
                create_trimsheet_json(active)

    def update_trimsheetname(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        self.avoid_update = True
        self.trimsheetname = self.trimsheetname.strip()

        sheet = context.active_object if context.active_object and context.active_object.DM.istrimsheet else None

        if sheet:
            sheet.name = self.trimsheetname
            sheet.data.name = self.trimsheetname

            mat = sheet.active_material

            if mat:
                mat.name = self.trimsheetname
                mat.DM.trimsheetname = self.trimsheetname

                set_node_names_of_trimsheet(sheet, reset_heightnode_names=self.duplicate_sheet)

                if self.duplicate_sheet:
                    self.duplicate_sheet = False

                textures = get_trimsheet_textures(mat)

                for textype, img in textures.items():
                    img.DM.trimsheetname = self.trimsheetname

                create_trimsheet_json(sheet)

            col = sheet.DM.trimcollection

            if col:
                oldname = col.name

                col.name = self.trimsheetname

                trim_decals = [obj for obj in col.objects if obj.DM.istrimdecal and obj.DM.trimsheetuuid == sheet.DM.trimsheetuuid]

                for decal in trim_decals:
                    library = self.trimsheetname
                    basename = decal.DM.decalmatname.replace(oldname + '_', '')
                    decalname = "%s_%s" % (library, basename)

                    decal.name = decalname
                    decal.data.name = decalname

                    decalmat = decal.active_material

                    set_props_and_node_names_of_decal(library, basename, decalobj=decal, decalmat=decalmat)

    istrimsheet: BoolProperty(name="is trim sheet", default=False)
    istrimdecal: BoolProperty(name="is trim decal", default=False)

    trimsheetname: StringProperty(name="Trim Sheet Name", update=update_trimsheetname)
    trimsheetindex: StringProperty(name="Index used for triminstant folder")
    trimsheetuuid: StringProperty(name="trim sheet uuid")
    trimsheetresolution: IntVectorProperty("Trim Sheet Resolution", size=2, default=(1024, 1024))

    trimsCOL: CollectionProperty(name="Trims", type=TrimsCollection)
    trimsIDX: IntProperty(name="Trim / Decal", update=update_trimsIDX)
    trimopspinned: BoolProperty(name="Pin Tools to end of List")

    trimmapsCOL: CollectionProperty(name="Trim Sheet Texture Maps", type=TrimMapsCollection)
    trimmapsIDX: IntProperty(name="Trim Sheet Texture Map")

    trimcollection: PointerProperty(name="Trim Collection", type=bpy.types.Collection)

    show_trim_maps: BoolProperty(description="Show/Hide Trim Sheet Maps", default=True)
    show_trims: BoolProperty(description="Show/Hide Trim Setup", default=True)



    def update_atlasname(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        self.avoid_update = True
        self.atlasname = self.atlasname.strip()

        atlas = context.active_object if context.active_object and context.active_object.DM.isatlas else None

        if atlas:
            name = self.atlasname

            atlas.name = name
            atlas.data.name = name

            atlas.DM.atlascollection.name = '%s (preview)' % (name)

            for trim in atlas.DM.trimsCOL:
                if trim.dummy:
                    trim.dummy.name = "%s Dummy %s" % (name, trim.name)
                    trim.dummy.data.name = "%s Dummy %s" % (name, trim.name)

                    trim.dummy.DM.avoid_update = True
                    trim.dummy.DM.atlasname = name

            mat = atlas.DM.atlasdummymat

            if mat:
                mat.name = name
                mat.DM.atlasname = name

                set_node_names_of_atlas_material(mat, name)

                textures = get_atlas_textures(mat)

                for _, img in textures.items():
                    img.DM.atlasname = name

            solution = atlas.DM.get('solution')

            if solution:
                solution['name'] = name

            solution = atlas.DM.get('solution')
            solutionpath = os.path.join(get_prefs().assetspath, 'Export', 'atlas', "%s_%s" % (atlas.DM.atlasindex, atlas.DM.atlasuuid), 'solution.json')

            if os.path.exists(solutionpath):
                solution = load_json(solutionpath)
                solution['name'] = name
                save_json(solution, solutionpath)

    def update_atlasrefinement(self, context):

        atlas = context.active_object if context.active_object.DM.isatlas else None

        if self.atlasrefinement == 'TWEAK':

            if atlas:
                context.scene.DM.create_atlas_resolution = atlas.DM.atlasresolution[0]

        elif self.atlasrefinement == 'REPACK':
            context.scene.DM.create_atlas_size_mode = 'SPECIFIC'

        atlas.select_set(True)

    def update_atlasdummyparallax(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        atlas = context.active_object if context.active_object.DM.isatlas else None

        if atlas:
            mat = atlas.DM.atlasdummymat

            if mat:
                nodes = get_atlas_nodes(mat)
                pg = nodes.get('PARALLAXGROUP')

                if pg:
                    pg.inputs[0].default_value = self.atlasdummyparallax

    isatlas: BoolProperty(name="is atlas", default=False)
    isatlasdummy: BoolProperty(name="is atlas dummy", default=False)

    atlasname: StringProperty(name="Atlas Name", update=update_atlasname)
    atlasindex: StringProperty(name="Index used for atlas folder")
    atlasuuid: StringProperty(name="atlas uuid")
    atlasresolution: IntVectorProperty("Atlas Resolution", size=2, default=(1024, 1024))
    atlasrefinement: EnumProperty(name="Atlas Refinement", items=create_atlas_mode_items[1:], default='REPACK', update=update_atlasrefinement)
    atlastrimsort: EnumProperty(name="Atlas Trim Sort", items=create_atlas_trim_sort_items, default='NAME')
    atlascollection: PointerProperty(name="Atlas Collection", type=bpy.types.Collection)
    atlasdummymat: PointerProperty(name="Atlas Dummy Mat", type=bpy.types.Material)
    atlasnewdecaloffset: IntProperty("Offset to position newly added Decal to Atlas", default=10)

    show_atlas_props: BoolProperty(name="Show Atlas Properties", default=True)

    atlasresizedown: BoolProperty(name="Scale Atlas Down", description="Scale Atlas Down", default=False)

    preatlasmats: CollectionProperty(name="Pre-Atlas Materials", type=PreAtlasMaterialsCollection)
    prejoindecals: CollectionProperty(name="Pre-Join Decals", type=PreJoinDecalsCollection)
    isjoinedafteratlased: BoolProperty(name="Decal has been joined, after it was atlased", default=False)
    wasjoined: BoolProperty(name="Decal has been stashed away and replaced by a joined Decal", default=False)

    atlasdummyparallax: FloatProperty(name="Parallax Amount", default=0.1, min=0, max=0.5, step=0.1, update=update_atlasdummyparallax)




    duplicate_sheet: BoolProperty()
    avoid_update: BoolProperty()


class DecalMaterialProperties(bpy.types.PropertyGroup):
    uuid: StringProperty(name="decal uuid")
    version: StringProperty(name="decal version")
    decaltype: EnumProperty(name="decal type", items=decaltype_items, default="NONE")
    decallibrary: StringProperty(name="decal library")
    decalname: StringProperty(name="decal name")
    decalmatname: StringProperty(name="decal material name")

    decalnamefromfile: StringProperty(name="decalname from file")

    isdecalmat: BoolProperty(name="is decal material", default=False)
    ismatched: BoolProperty(name="is matched", default=False)
    isparallaxed: BoolProperty(name="is parallaxed", default=False)

    matchedmaterialto: PointerProperty(name="matched Decal Material Parameters to", type=bpy.types.Material)
    matchedmaterial2to: PointerProperty(name="matched Decal Material2 Parameters to", type=bpy.types.Material)
    matchedsubsetto: PointerProperty(name="matched Decal Subset Parameters to", type=bpy.types.Material)
    matchedtrimsheetto: PointerProperty(name="matched Trim Sheet Parameters to", type=bpy.types.Material)

    parallaxnodename: StringProperty(name="parallax node name")
    parallaxdefault: FloatProperty(name="Default Parallax", default=0.1, min=0)

    creator: StringProperty(name="Decal Creator")


    trimsheetname: StringProperty(name="Name")
    trimsheetuuid: StringProperty(name="trim sheet uuid")

    istrimsheetmat: BoolProperty(name="is trim sheet material", default=False)
    istrimdecalmat: BoolProperty(name="is trim decal material", default=False)


    atlasname: StringProperty(name="Name")
    atlasuuid: StringProperty(name="atlas uuid")

    isatlasmat: BoolProperty(name="is atlas material", default=False)
    isatlasbgmat: BoolProperty(name="is atlas background material", default=False)
    isatlasdummymat: BoolProperty(name="is atlas dummy material", default=False)


class DecalImageProperties(bpy.types.PropertyGroup):
    uuid: StringProperty(name="decal uuid")
    version: StringProperty(name="decal version")
    decaltype: EnumProperty(name="decal type", items=decaltype_items, default="NONE")
    decallibrary: StringProperty(name="decal library")
    decalname: StringProperty(name="decal name")
    decalmatname: StringProperty(name="decal material name")

    isdecaltex: BoolProperty(name="is decal texture", default=False)
    decaltextype: EnumProperty(name="decal texture type", items=texturetype_items, default="NONE")

    creator: StringProperty(name="Decal Creator")

    trimsheetname: StringProperty(name="Name")
    trimsheetuuid: StringProperty(name="trim sheet uuid")
    istrimsheettex: BoolProperty(name="is trim sheet texture", default=False)
    istrimdecaltex: BoolProperty(name="is trim decal texture", default=False)
    trimsheettextype: EnumProperty(name="trimsheet texture type", items=trimtexturetype_items, default="NONE")

    atlasname: StringProperty(name="Name")
    atlasuuid: StringProperty(name="atlas uuid")
    isatlastex: BoolProperty(name="is atlas texture", default=False)
    isatlasdummytex: BoolProperty(name="is atlas dummy texture", default=False)
    atlastextype: EnumProperty(name="atlas texture type", items=atlastexturetype_items, default="NONE")


class DecalCollectionProperties(bpy.types.PropertyGroup):
    isdecaltypecol: BoolProperty(name="is decaltype collection", default=False)
    isdecalparentcol: BoolProperty(name="is decal parent collection", default=False)
