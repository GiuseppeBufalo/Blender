from .. utils.ui import get_icon



def extrude_menu(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator("machin3.punchit", text="Punch It", icon_value=get_icon('fist'))
