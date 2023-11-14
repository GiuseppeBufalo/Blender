# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import PointerProperty, BoolProperty, EnumProperty
from bpy.types import PropertyGroup

from ZenUV.draw.osl_draw import (
    callback_solver,
    ZUV_OT_DrawTagged,
)
from ZenUV.ui.labels import ZuvLabels
from bpy.app.handlers import persistent


def draw_switch(context, primary):
    vizers = context.scene.zen_display
    for vizer, value in vizers.items():
        if vizer == primary or vizer == 'stack_display_solver' or vizer == 'stack_display_mode':
            continue
        vizers[vizer] = False
        # print(vizer, value)


class ZUV_PT_OSL_Display(PropertyGroup):

    def update_tagged(self, context):
        if self.tagged:
            draw_switch(context, 'tagged')
            bpy.ops.view3d.zenuv_draw_tagged("INVOKE_DEFAULT")

    def update_stacked(self, context):
        draw_switch(context, 'stacked')
        callback_solver(self, context)

    def update_m_stacked(self, context):
        draw_switch(context, 'm_stacked')
        callback_solver(self, context, manual=True)

    def update_s_stacked(self, context):
        draw_switch(context, 's_stacked')
        callback_solver(self, context)

    def update_ast_stacked(self, context):
        draw_switch(context, 'ast_stacked')
        callback_solver(self, context)

    def update_finished(self, context):
        draw_switch(context, 'finished')
        callback_solver(self, context)

    def update_p_excluded(self, context):
        draw_switch(context, 'p_excluded')
        callback_solver(self, context)

    def update_stretch(self, context):
        draw_switch(context, 'stretch')
        callback_solver(self, context)

    def disable_all_draws(self, context):
        draw_switch(context, 'disable')
        callback_solver(self, context)

    def update_display_solver(self, context):
        mode = self.stack_display_mode
        if mode == 'SIMILAR':
            self.stacked = self.stack_display_solver
        if mode == 'SELECTED':
            self.s_stacked = self.stack_display_solver
        if mode == 'STACKED':
            self.ast_stacked = self.stack_display_solver
        if mode == 'PRIMARY':
            self.masters = self.stack_display_solver
        if mode == 'REPLICAS':
            self.stacks = self.stack_display_solver
        if mode == 'SINGLES':
            self.singles = self.stack_display_solver

    def update_stack_display_mode(self, context):
        pass

    tagged: BoolProperty(
        name=ZuvLabels.PROP_TAGGED_LABEL,
        description=ZuvLabels.PROP_TAGGED_DESC,
        default=False,
        update=update_tagged
    )
    stacked: BoolProperty(
        name=ZuvLabels.PROP_STACKED_LABEL,
        description=ZuvLabels.PROP_STACKED_DESC,
        default=False,
        update=update_stacked
    )
    m_stacked: BoolProperty(
        name=ZuvLabels.PROP_M_STACKED_LABEL,
        description=ZuvLabels.PROP_M_STACKED_DESC,
        default=False,
        update=update_m_stacked
    )
    s_stacked: BoolProperty(
        name=ZuvLabels.PROP_S_STACKED_LABEL,
        description=ZuvLabels.PROP_S_STACKED_DESC,
        default=False,
        update=update_s_stacked
    )
    ast_stacked: BoolProperty(
        name=ZuvLabels.PROP_AST_STACKED_LABEL,
        description=ZuvLabels.PROP_AST_STACKED_DESC,
        default=False,
        update=update_ast_stacked
    )
    masters: BoolProperty(
        name=ZuvLabels.PROP_ENUM_STACK_DISPLAY_MASTERS_LABEL,
        description=ZuvLabels.PROP_ENUM_STACK_DISPLAY_MASTERS_DESC,
        default=False,
        update=disable_all_draws
    )
    stacks: BoolProperty(
        name=ZuvLabels.PROP_ENUM_STACK_DISPLAY_STACKS_LABEL,
        description=ZuvLabels.PROP_ENUM_STACK_DISPLAY_STACKS_DESC,
        default=False,
        update=disable_all_draws
    )
    singles: BoolProperty(
        name=ZuvLabels.PROP_ENUM_STACK_DISPLAY_SINGLES_LABEL,
        description=ZuvLabels.PROP_ENUM_STACK_DISPLAY_SINGLES_DESC,
        default=False,
        update=disable_all_draws
    )
    finished: BoolProperty(
        name=ZuvLabels.OT_FINISHED_DISPLAY_LABEL,
        default=False,
        description=ZuvLabels.OT_FINISHED_DISPLAY_DESC,
        update=update_finished
    )
    p_excluded: BoolProperty(
        name=ZuvLabels.OT_EXCL_DISPLAY_LABEL,
        default=False,
        description=ZuvLabels.OT_EXCL_DISPLAY_DESC,
        update=update_p_excluded
    )
    st_uv_area_only: BoolProperty(
        name=ZuvLabels.PROP_ST_UV_AREA_ONLY_LABEL,
        default=False,
        description=ZuvLabels.PROP_ST_UV_AREA_ONLY_DESC
    )
    stack_display_mode: EnumProperty(
        name=ZuvLabels.PREF_STACK_DISPLAY_MODE_LABEL,
        description=ZuvLabels.PREF_STACK_DISPLAY_MODE_DESC,
        items=(
            ('SIMILAR', ZuvLabels.PROP_ENUM_STACK_DISPLAY_SIMILAR_LABEL, ZuvLabels.PROP_ENUM_STACK_DISPLAY_SIMILAR_DESC),
            ('SELECTED', ZuvLabels.PROP_ENUM_STACK_DISPLAY_SELECTED_LABEL, ZuvLabels.PROP_ENUM_STACK_DISPLAY_SELECTED_DESC),
            ('STACKED', ZuvLabels.PROP_ENUM_STACK_DISPLAY_STACKED_LABEL, ZuvLabels.PROP_ENUM_STACK_DISPLAY_STACKED_DESC),
            ('PRIMARY', ZuvLabels.PROP_ENUM_STACK_DISPLAY_MASTERS_LABEL, ZuvLabels.PROP_ENUM_STACK_DISPLAY_MASTERS_DESC),
            ('REPLICAS', ZuvLabels.PROP_ENUM_STACK_DISPLAY_STACKS_LABEL, ZuvLabels.PROP_ENUM_STACK_DISPLAY_STACKS_DESC),
            ('SINGLES', ZuvLabels.PROP_ENUM_STACK_DISPLAY_SINGLES_LABEL, ZuvLabels.PROP_ENUM_STACK_DISPLAY_SINGLES_DESC),
        ),
        default='SIMILAR',
        update=update_display_solver
    )
    stack_display_solver: BoolProperty(
        name=ZuvLabels.PROP_STACK_DISPLAY_SOLVER_LABEL,
        default=False,
        description=ZuvLabels.PROP_STACK_DISPLAY_SOLVER_DESC,
        update=update_display_solver
    )
    stretch: BoolProperty(
        name=ZuvLabels.OT_STRETCH_DISPLAY_LABEL,
        default=False,
        description=ZuvLabels.OT_STRETCH_DISPLAY_DESC,
        update=update_stretch
    )


draw_classes = (
    # ZUV_OT_DrawFinished,
    ZUV_OT_DrawTagged,
    ZUV_PT_OSL_Display,
)


@persistent
def OSLDrawLoadDisable(context):
    bpy.context.scene.zen_display.stacked = False
    bpy.context.scene.zen_display.finished = False
    bpy.context.scene.zen_display.stretch = False


def register():
    """Registering Operators"""
    for cl in draw_classes:
        register_class(cl)

    bpy.types.Scene.zen_display = PointerProperty(type=ZUV_PT_OSL_Display)

    bpy.app.handlers.load_post.append(OSLDrawLoadDisable)


def unregister():
    """Unegistering Operators"""
    OSLDrawLoadDisable(bpy.context)

    for cl in draw_classes:
        unregister_class(cl)

    bpy.app.handlers.load_post.remove(OSLDrawLoadDisable)
    del bpy.types.Scene.zen_display


if __name__ == "__main__":
    pass
