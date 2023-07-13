

def poweroftwo(minvalue, maxvalue):
    items = []

    while minvalue <= maxvalue:
        items.append(minvalue)
        minvalue *= 2

    return [(str(i), str(i), "") for i in items]



prefs_tab_items = [("GENERAL", "General", ""),
                   ("CREATEEXPORT", "Decal Creation + Export", ""),
                   ("ABOUT", "About", "")]

prefs_asset_loader_tab_items = [("DECALS", "Decals", "Settings governing how Decal Libraries are displayed in the Object Mode Pie Menu"),
                                ("TRIMS", "Trims", "Settings governing how Trim Sheet Libraries are displayed in the Edit Mode Pie Menu")]

prefs_newlibmode_items = [("IMPORT", "Import Existing", "Import an existing Decal Library or Trim Sheet Library"),
                          ("EMPTY", "Create Empty", "Create and empty Decal Library")]

prefs_decalmode_items = [("INSERT", "Insert", ""),
                         ("REMOVE", "Remove", ""),
                         ("NONE", "None", "")]



decaltype_items = [("NONE", "None", ""),
                   ("MATERIAL", "Material", ""),
                   ("SIMPLE", "Simple", ""),
                   ("SUBSET", "Subset", ""),
                   ("PANEL", "Panel", ""),
                   ("INFO", "Info", "")]

texturetype_items = [("NONE", "None", ""),
                     ("AO_CURV_HEIGHT", "AO Curvature Height", ""),
                     ("NORMAL", "Normal", ""),
                     ("MASKS", "Masks", ""),
                     ("COLOR", "Color", ""),
                     ("EMISSION", "Emission", "")]



trimtexturetype_items = [("NONE", "None", ""),
                         ("AO", "AO", ""),
                         ("CURVATURE", "Curvature", ""),
                         ("HEIGHT", "Height", ""),
                         ("NORMAL", "Normal", ""),
                         ("COLOR", "Color", ""),
                         ("EMISSION", "Emission", ""),
                         ("METALLIC", "Metallic", ""),
                         ("ROUGHNESS", "Roughness", ""),
                         ("ALPHA", "Alpha", ""),
                         ("SUBSET", "Subset", ""),
                         ("MATERIAL2", "Material2", "")]

atlastexturetype_items = [("NONE", "None", ""),
                          ("AO", "AO", ""),
                          ("CURVATURE", "Curvature", ""),
                          ("HEIGHT", "Height", ""),
                          ("NORMAL", "Normal", ""),
                          ("COLOR", "Color", ""),
                          ("EMISSION", "Emission", ""),
                          ("METALLIC", "Metallic", ""),
                          ("ROUGHNESS", "Roughness", ""),
                          ("ALPHA", "Alpha", ""),
                          ("SUBSET", "Subset", ""),
                          ("MATERIAL2", "Material2", "")]



interpolation_items = [("Linear", "Linear", "Smooth, with the potential of transparent colors bleeding in"),
                       ("Closest", "Closest", "Pixelated, but without any bleeding issues")]

alpha_blendmode_items = [("BLEND", "Blend", "Not alpha sorted, but faster"),
                         ("HASHED", "Hashed", "Alpha sorted, but slower and noisier")]

edge_highlights_items = [("0", "0", ""),
                         ("0.5", "0.5", ""),
                         ("1", "1", "")]

auto_match_items = [("AUTO", "Auto", "Automatically Match Materials, if a supported Material is under the Decal"),
                    ("MATERIAL", "Material", "Match to selected Material"),
                    ("OFF", "Off", "Don't Match Materials at all")]

align_mode_items = [("RAYCAST", "Mouse Pointer", "Insert and Align Decal at Mouse Pointer"),
                    ("CURSOR", "3D Cursor", "Insert and Align Decal at 3D Cursor")]

pack_images_items = [("PACKED", "Pack", "Store Decal and Trim Sheet Textures directly in the blend file. Increased file sizes, but allows scenes to be loaded at different computers, even ones without DECALmachine installed"),
                     ("UNPACKED", "Unpack", "Unpack Decal and Trim Sheet Textures to the Decal and Trim Libraries\nALT: Unpack them locally, relative to the blend file")]



create_type_items = [("DECAL", "Decal", "Create Decals"),
                     ("ATLAS", "Atlas", "Create Decal Atlases"),
                     ("TRIMSHEET", "Trim Sheet", "Create Trim Sheets and associated Trim Decals")]



bake_supersample_items = [("0", "Off", ""),
                          ("2", "2x", ""),
                          ("4", "4x", "")]

create_bake_resolution_items = poweroftwo(64, 1024)

create_bake_aosamples_items = poweroftwo(128, 512)

create_bake_emissionsamples_items = poweroftwo(512, 4096)

create_decaltype_items = [("SIMPLESUBSET", "Simple/Subset", "Create Simple and Subset Decals"),
                          ("PANEL", "Panel", "Create Panel Decals"),
                          ("INFO", "Info", "Create Info Decals")]

create_infotype_items = [("IMAGE", "Image", "Create Info Decals from Images"),
                         ("FONT", "Text", "Create info Decals from Text"),
                         ("GEOMETRY", "Geometry", "Create Infor Decals from Geometry")]

create_infotext_align_items = [("left", "Left", ""),
                               ("center", "Center", ""),
                               ("right", "Right", "")]


create_trimtype_items = [("NEW", "New", "Create new Trim Sheet from existing Textures"),
                         ("IMPORT", "Import", "Import Trim Sheet from data.json")]



create_atlascreation_type_items = [("NEW", "New", "Create new Atlas from Decals"),
                                   ("IMPORT", "Import", "Import Atlas from data.json")]

create_atlas_mode_items = [('INITIATE', 'Initiate', ''),
                           ('REPACK', 'Re-Pack', 'Automatically position Decals in Atlas according changes in Decal Scale, Atlas Resolution and Padding'),
                           ('TWEAK', 'Tweak', 'Manually position and scale Decals in the Atlas')]

create_atlas_size_mode_items = [('SMALLEST', 'Smallest', 'Find the smallest possible packing solution'),
                                ('SPECIFIC', 'Specific', "Use specific resolution to pack Atlas\nNote, it's still possible for the smallest packing solution found to end up higher than the chosen resolution")]

create_atlas_type_items = [('COMBINED', 'Combined', 'Pack Combined Atlas from Simple, Subset, Panel and Info Decals'),
                           ('NORMAL', 'Normal', 'Pack Normal Atlas from Simple, Subset and Panel Decals'),
                           ('INFO', 'Info', 'Pack Info Atlas from Info Decals')]

create_atlas_prepack_items = [('NONE', 'None', "Don't pre-pack Panel Decals, treat them like any other decal"),
                              ('STRETCH', 'Stretch', 'Pack Panel Decals first at the top, and stretch them horizontally across the Atlas'),
                              ('REPEAT', 'Repeat', 'Pack Panel Decals first at the top, and repeat them horizontally across the Atlas')]

create_atlas_trim_sort_items = [('NAME', 'Name', ''),
                                ('PACK', 'Pack', '')]


create_atlastype_textype_mapping_dict = {'COMBINED': ['COLOR', 'NORMAL', 'AO_CURV_HEIGHT', 'EMISSION', 'MASKS'],
                                         'NORMAL': ['NORMAL', 'AO_CURV_HEIGHT', 'EMISSION', 'MASKS'],
                                         'INFO': ['COLOR', 'EMISSION', 'MASKS']}


textype_color_mapping_dict = {'NORMAL': (128, 128, 255),
                              'ALPHA': 0,
                              'AO': 255,
                              'AO_CURV_HEIGHT': (255, 128, 128),
                              'COLOR': (128, 128, 128),
                              'CURVATURE': 128,
                              'EMISSION': (0, 0, 0),
                              'HEIGHT': 128,
                              'MASKS': (255, 0, 0),
                              'MATERIAL2': 0,
                              'SUBSET': 0}



update_library_version_items = [("18", "1.8 - 1.9.4", "Update Decals from DECALmachine 1.8 - 1.9.4"),
                                ("20", "2.0.x", "Update Decals from DECALmachine 2.0 - 2.0.1")]

update_library_version_30_items = [("18", "1.8 - 1.9.4", "Update Decals from DECALmachine 1.8 - 1.9.4"),
                                   ("20", "2.0.x", "Update Decals from DECALmachine 2.0 - 2.0.1"),
                                   ("21", "2.1 - 2.4.1", "Update Decals from DECALmachine 2.1 - 2.4.1")]



adjust_mode_items = [("HEIGHT", "Height", ""),
                     ("WIDTH", "Width", ""),
                     ("PARALLAX", "Paralax", ""),
                     ("AO", "Ambient Occlusion", ""),
                     ("STRETCH", "Panel UV Stretch", ""),
                     ("EMISSION", "Emission", "")]

cutter_method_items = [("CONSTRUCT", "Construct Cutter", ""),
                       ("MESHCUT", "Mesh Cut", "")]

select_mode_items = [('ALL', 'All', ''),
                     ('COMMONPARENT', 'Common Parent', '')]

align_trim_items = [('LEFT', 'Left', ''),
                    ('RIGHT', 'Right', ''),
                    ('TOP', 'Top', ''),
                    ('BOTTOM', 'Bottom', '')]


trimunwrap_fit_items = [('AUTO', 'Auto', ''),
                        ('STRETCH', 'Stretch', ''),
                        ('FITINSIDE', 'Fit Inside', ''),
                        ('FITOUTSIDE', 'Fit Outside', '')]


trimadjust_fit_items = [('NONE', 'None', ''),
                        ('AUTO', 'Auto', ''),
                        ('STRETCH', 'Stretch', ''),
                        ('FITINSIDE', 'Fit Inside', ''),
                        ('FITOUTSIDE', 'Fit Outside', '')]


uv_up_axis_mapping_dict = {(1, 0): (0, 1),
                           (0, 1): (-1, 0),
                           (-1, 0): (0, -1),
                           (0, -1): (1, 0)}


box_unwrap_items = [('SELECTION', 'Selected Only', 'Box Unwrap the Selected Objects only'),
                    ('SHARED', 'Shared Materials', 'Box Unwrap all Visible Objects, that share Trim Sheet Materials with the Selected Objects'),
                    ('VISIBLE', 'All Visible', 'Box Unwrap all Visible Objects with Trim Sheet Materials')]


mirror_props = ['type',
                'merge_threshold',
                'mirror_object',
                'mirror_offset_u',
                'mirror_offset_v',
                'offset_u',
                'offset_v',
                'show_expanded',
                'show_in_editmode',
                'show_on_cage',
                'show_render',
                'show_viewport',
                'use_axis',
                'use_bisect_axis',
                'use_bisect_flip_axis',
                'use_clip',
                'use_mirror_merge',
                'use_mirror_u',
                'use_mirror_v',
                'use_mirror_vertex_groups']


export_type_items = [('ATLAS', 'Atlas', ''),
                     ('BAKE', 'Bake', '')]

exporttexturetype_items = [("NONE", "None", "Empty"),
                           ("ALPHA", "Alpha", "Alpha"),
                           ("AO", "Ambient Occlusion", "Ambient Occlusion"),
                           ("CURVATURE", "Curvature", "Curvature"),
                           ("HEIGHT", "Height", "Height"),
                           ("MATERIAL2", "Material2", "Matetial 2"),
                           ("METALLIC", "Metallic", "Metallic"),
                           ("ROUGHNESS", "Roughness", "Roughness"),
                           ("SMOOTHNESS", "Smoothness", "Smoothness"),
                           ("SUBSET", "Subset", "Subset"),
                           ("SUBSETOCCLUSION", "Subset Occlusion", "Subset Occlusion"),
                           ("WHITEHEIGHT", "White Height", "White Height")]

export_atlas_model_format_items = [('OBJ', '.obj', '.obj'),
                                   ('FBX', '.fbx', '.fbx'),
                                   ('GLTF', '.glTF', '.glTF')]

export_baketype_decaltype_mapping_dict = {'NORMAL': ['SIMPLE', 'SUBSET', 'PANEL'],
                                          'COLOR': ['INFO'],
                                          'AO_CURV_HEIGHT': ['SIMPLE', 'SUBSET', 'PANEL'],
                                          'SUBSET': ['SUBSET', 'PANEL'],
                                          'EMISSION_NORMAL': ['SIMPLE', 'SUBSET', 'PANEL'],
                                          'EMISSION_COLOR': ['INFO']
                                          }
