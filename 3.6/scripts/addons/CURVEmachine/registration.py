

classes = {'CORE': [('preferences', [('CURVEmachinePreferences', '')]),
                    ('ui.panels', [('PanelCURVEmachine', 'curve_machine')]),
                    ('ui.operators.help', [('GetSupport', 'get_curvemachine_support')])],

           'MENU': [('ui.menus', [('MenuCurveMachine', 'curve_machine')])],


           'ADD': [('operators.add', [('AddSinglePointPOLYCurve', 'add_single_point_poly_curve')])],

           'BLEND': [('operators.blend', [('Bendulate', 'bendulate'),
                                          ('Interpolate', 'interpolate_points')])],

           'MERGE': [('operators.merge', [('MergeToLastPoint', 'merge_to_last_point')]),
                     ('operators.merge', [('MergeToCenter', 'merge_to_center')])],

           'REBUILD': [('operators.rebuild', [('GapShuffle', 'gap_shuffle')])],

           'TRANSFORM': [('operators.transform', [('SlidePoint', 'slide_point')])],
           }


keys = {'MENU': [{'label': 'Menu', 'keymap': 'Curve', 'idname': 'wm.call_menu', 'type': 'Y', 'value': 'PRESS', 'properties': [('name', 'MACHIN3_MT_curve_machine')]}],

        'BLEND': [{'label': 'Blendulate', 'keymap': 'Curve', 'idname': 'machin3.bendulate', 'type': 'B', 'ctrl': True, 'value': 'PRESS', 'properties': []}],

        'MERGE': [{'label': 'Merge to Last', 'keymap': 'Curve', 'idname': 'machin3.merge_to_last_point', 'type': 'ONE', 'value': 'PRESS', 'properties': []},
                  {'label': 'Merge to Center', 'keymap': 'Curve', 'idname': 'machin3.merge_to_center', 'type': 'ONE', 'shift': True, 'value': 'PRESS', 'properties': []},
                  {'label': 'Connect', 'keymap': 'Curve', 'idname': 'curve.make_segment', 'type': 'ONE', 'alt': True, 'value': 'PRESS', 'properties': []}],


        'TRANSFORM': [{'keymap': 'Curve', 'idname': 'machin3.slide_point', 'type': 'G', 'value': 'PRESS', 'properties': []},
                      {'keymap': 'Curve', 'idname': 'machin3.slide_point', 'type': 'G', 'value': 'DOUBLE_CLICK', 'properties': []}],
        }
