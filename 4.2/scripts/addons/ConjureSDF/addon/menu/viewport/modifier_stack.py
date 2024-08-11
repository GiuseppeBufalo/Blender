import bpy


from bpy.types import PropertyGroup, Panel

from bpy.props import PointerProperty, IntProperty

from ...engine.sdf.builder import PRIMITIVE_NON_ROUNDED

from ...resources import iconloader

from ...operator.modifier_stack.main import update_scene

from ...util.addon import get_prefs
from ...util.object import get_csdf_prims
from ...util.csdf_primitives import generate_csdf_prim_ID, InsertBeneath, add_csdf_scene_node



op_icons = {
            'Union' : 'sdf_union',
            'Diff' : 'sdf_difference',
            'Inters' : 'sdf_intersect',
            'Inset' : 'sdf_inset',
}



def selectModifier_Item(self, context):
    # context = bpy.context
    # obj = context.active_object    

    # the CSDF_OT_MODSTACK_MOVE_ITEM operator has to change the active index while moving items around
    # this is fine for a single selected object as this callback does not really change the selection state then
    # in the case of multiple selected objects however, this callback would ruin that selection (only keeping the object under the active index as selected/active)
    # hence this "block callback" property that is reset here once this callback is triggered.
    settings = bpy.context.scene.csdf

    if settings.block_index_callback:
        settings.block_index_callback = False
        return
    
    settings.block_selection_handler = True
    
    treeList = self.CSDF_OutlinerTree
    idx = self.CSDF_OutlinerTree_index
    obj_to_select = treeList[idx].obj

    # clear selection
    for obj in context.selected_objects:
        obj.select_set(False)
    
    obj_to_select.select_set(True)
    context.view_layer.objects.active = obj_to_select



# Based on
# https://blender.stackexchange.com/questions/250401/create-a-tree-of-string-properties


class CSDF_Scene_Node_Childindex(bpy.types.PropertyGroup):
    idx : bpy.props.IntProperty(default=-1)

# Holds the global list of primitives for CSDF
# **bpy.context.scene.myNodes**
class CSDF_Scene_Node(PropertyGroup):
    selfIndex : bpy.props.IntProperty(default=-1)
    parentIndex : bpy.props.IntProperty(default=-1)
    childCount : bpy.props.IntProperty(default=0)
    childIndices : bpy.props.CollectionProperty(type=CSDF_Scene_Node_Childindex)
    
    obj : PointerProperty(type=bpy.types.Object)

    def set_obj(self, ob):
        self.obj = ob
        self.name = ob.name
        return self.obj

#   This represents an item that in the collection being rendered by
#   props.template_list. This collection is stored in ______
#   The collection represents a currently visible subset of MyListTreeNode
#   plus some extra info to render in a treelike fashion, eg indent.
class CSDF_OutlinerUI_Item(PropertyGroup):
    indent: bpy.props.IntProperty(default=0)
    expanded: bpy.props.BoolProperty(default=False)
    nodeIndex : bpy.props.IntProperty(default=-1) #index into the real tree data.
    childCount: bpy.props.IntProperty(default=0) #should equal myNodes[nodeIndex].childCount
    
    obj : PointerProperty(type=bpy.types.Object)

    def set_obj(self, ob):
        self.obj = ob
        self.name = ob.name
        return self.obj







class CSDF_UL_OUTLINER(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = data

        csdfData = item.obj.csdfData

        op_type = csdfData.operation_type
        op_icon = op_icons[op_type]

        prim_icon = "sdf_" + csdfData.primitive_type

        Outliner_Icon_LineH = iconloader.id('Outliner_LineH')
        Outliner_Icon_LineE = iconloader.id('Outliner_LineE')

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            col = layout.column()
            if item.obj in context.selected_objects:
                col.label(text="", icon='GRIP')
            else:
                col.label(text="", icon='BLANK1')

            csdf_scene_nodes = scene.CSDF_SceneNodes
            item_node = csdf_scene_nodes[item.nodeIndex]
            item_parent_node = csdf_scene_nodes[item_node.parentIndex]

            childIndices = [child.idx for child in item_parent_node.childIndices]

            last_subitem = False
            if childIndices.index(item_node.selfIndex) == item_parent_node.childCount-1:
                last_subitem = True
            

            for i in range(item.indent):
                col = layout.column()
                if last_subitem and i == (item.indent-1):
                    col.label(text="", icon_value=Outliner_Icon_LineE)
                else:
                    col.label(text="", icon_value=Outliner_Icon_LineH)
                    col.enabled = False

            col = layout.column()

            if item.childCount == 0:
                col.label(text="", icon='BLANK1')
                col.enabled = False                       
            #if False:
            #    pass
            elif item.expanded :
                op = col.operator("object.csdf_expandoutlineritem", text="", icon='DISCLOSURE_TRI_DOWN', emboss=False)
                op.button_id = index
            else:
                op = col.operator("object.csdf_expandoutlineritem", text="", icon='DISCLOSURE_TRI_RIGHT', emboss=False)
                op.button_id = index

            row = layout.row(align=True)
            row.label(text="", icon_value=iconloader.id(op_icon))
            row.label(text="", icon_value=iconloader.id(prim_icon))
            
            col = layout.column()
            col.label(text=item.obj.name)

            display_toggle_enabled = True

            child = item_node
            while child.parentIndex != 0:
                parent = csdf_scene_nodes[child.parentIndex]
                if not parent.obj.csdfData.show_viewport:
                    display_toggle_enabled = False
                child = parent

            split = layout.split()
            split.enabled = display_toggle_enabled
            visibility_icon = 'RESTRICT_VIEW_OFF'
            if csdfData.show_viewport == False:
                visibility_icon = 'RESTRICT_VIEW_ON'
            split.prop(csdfData, "show_viewport", text="", icon=visibility_icon, emboss=False)



class CSDF_OT_EXPAND_OUTLINER_ITEM(bpy.types.Operator):
    bl_idname = "object.csdf_expandoutlineritem"
    bl_label = "Expand"
    
    button_id: IntProperty(default=0)

    def execute(self, context):

        # prevent active item callback and selection state handler from firing
        settings = context.scene.csdf
        
        item_index = self.button_id
        treeList = context.scene.CSDF_OutlinerTree
        item = treeList[item_index]
        item_indent = item.indent
        
        nodeIndex = item.nodeIndex

        csdf_scene_nodes = context.scene.CSDF_SceneNodes
        parent_node = csdf_scene_nodes[nodeIndex]
        child_nodes = [csdf_scene_nodes[childidx.idx] for childidx in parent_node.childIndices]


        active_idx = context.scene.CSDF_OutlinerTree_index

        num_children = 0

        if item.expanded:
            item.expanded = False
            
            nextIndex = item_index+1
            while True:
                if nextIndex >= len(treeList):
                    break
                if treeList[nextIndex].indent <= item_indent:
                    break
                treeList.remove(nextIndex)
                num_children += 1

            if (active_idx > item_index) and (active_idx <= item_index+num_children):
                settings.block_index_callback = True
                settings.block_selection_handler = True
                context.scene.CSDF_OutlinerTree_index = item_index

        else:
            item.expanded = True
            
            child_index = item_index
            for child_node in child_nodes:

                new_item, new_item_idx = InsertBeneath(treeList, child_index, item_indent, child_node)

                if active_idx == item_index and context.active_object == new_item.obj:
                    settings.block_index_callback = True
                    settings.block_selection_handler = True
                    context.scene.CSDF_OutlinerTree_index = new_item_idx

                # because each item should be added after the previous one
                child_index += 1

                num_children += 1

            if active_idx > item_index:
                settings.block_index_callback = True
                settings.block_selection_handler = True
                context.scene.CSDF_OutlinerTree_index += num_children

            
        return {'FINISHED'}



# ----- PARENT CLASSES, don't register
class CSDF_PT_VIEW_3D:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CSDF"


# ----- 3D VIEWPORT PANELS

class CSDF_PT_OUTLINER(Panel, CSDF_PT_VIEW_3D):
    bl_label = "Scene"
    bl_order = 0

    def draw(self, context):

        scene = context.scene
        layout = self.layout

        box = layout.box()

        draw_csdf_outliner_panel(box, scene)

        # csdf_scene_nodes = context.scene.CSDF_SceneNodes

        # print("=========================")

        # for node in csdf_scene_nodes:
        #     childindices = [child.idx for child in node.childIndices]

        #     print(node.obj.name)
        #     print("selfIndex: " + str(node.selfIndex))
        #     print(childindices)
        #     child_nodes = [csdf_scene_nodes[idx].obj.name for idx in childindices]
        #     print(child_nodes)
        #     print("-------------")


def draw_csdf_outliner_panel(layout, scene):

    if scene.objects.get("CSDF Root"):
        root = scene.objects["CSDF Root"]
        root_data = root.csdfData

        draw_scene_root_options(layout, scene, root_data)

        layout.separator()
        layout.separator()

        num_prims = len(get_csdf_prims(scene)) - 1
        if num_prims == 0:
            col = layout.column()
            col.label(text="Now add a CSDF primitive (Shift+A)")
            col.label(text="To unlock the Outliner")
            
            col.separator()
            
            row = col.row()
            row.scale_y = 1.3
            op = row.operator(operator="mesh.csdf_addprim", icon_value=iconloader.id('sdf_Sphere'), text='Conjure an Orb to ponder')
            op.prim = 'Sphere'

        row = layout.row()
        row.label(text="Outliner")

        box = layout.box()
        if num_prims == 0:
            box.enabled = False

        draw_outliner(box, scene)


    else:
        col = layout.column()
        col.label(text="Oh Great Wizard.")
        col.label(text="Switch to Conjure Vision.")
        row = layout.row()
        row.use_property_split = True
        row.prop(scene.render, "engine", text="Render Engine")

        layout.separator()

        row = layout.row()
        row.label(text="Then cast the spell below to commence Conjuring")
        row = layout.row()
        row.scale_y = 2
        row.operator(operator="mesh.csdf_addroot", icon='EMPTY_AXIS', text='Add Root')



def draw_scene_root_options(layout, scene, root_data):

    row = layout.row()
    row.label(text="Settings")

    row = layout.row(align=True)
    row.label(icon='MOD_MIRROR')
    sub = row.row(align=True)
    sub.scale_x = 0.6

    sub.prop(root_data, "mirror_world", text="World Mirror", toggle=True)


    row = layout.row(align=True)
    row.label(icon='MOD_MIRROR')
    sub = row.row(align=True)
    sub.scale_x = 0.6

    sub.prop(root_data, "mirror_flips", text="Flip Direction")
    
    
    row = layout.row()
    row1 = row.row()
    row1.prop(root_data, "mirror_smooth", text="Smooth Mirroring")

    row2 = row.row()
    if not root_data.mirror_smooth:
        row2.enabled = False
    row2.prop(root_data, "mirror_smooth_strength", text="Strength")

def draw_outliner(layout, scene):
    row = layout.row()
    row.scale_y = 1.5
    op = row.operator("csdf.modstack_unnestprimitive", text="Unnest", icon_value=iconloader.id('Outliner_Unnest'))
    op.unnest = True
    op = row.operator("csdf.modstack_unnestprimitive", text="Nest under Active", icon_value=iconloader.id('Outliner_Renest'))
    op.unnest = False
    
    row = layout.row()

    row.template_list(
    "CSDF_UL_OUTLINER",
    "",
    scene,
    "CSDF_OutlinerTree",
    scene,
    "CSDF_OutlinerTree_index",
    sort_lock = True
    )


    col = row.column()

    op = col.operator("csdf.modstack_moveitem", text="", icon='TRIA_UP_BAR')
    op.direction = 'UP'
    op.to_topbottom = True

    op = col.operator("csdf.modstack_moveitem", text="", icon='TRIA_UP')
    op.direction = 'UP'    

    op = col.operator("csdf.modstack_moveitem", text="", icon='TRIA_DOWN')
    op.direction = 'DOWN'

    op = col.operator("csdf.modstack_moveitem", text="", icon='TRIA_DOWN_BAR')
    op.direction = 'DOWN'
    op.to_topbottom = True

    col.separator()

    col.operator("csdf.modstack_selectnestedprimitives", text="", icon='OUTLINER')
    
    op = col.operator("object.delete", text="", icon='TRASH')
    op.use_global = False
    op.confirm = False

    row = layout.row()
    # minus 1 because the root node is counted as a prim
    num_prims = max(0, len(get_csdf_prims(scene))-1)
    row.label(text="Primitives: " + str(num_prims)+" / 500" )
    # row = layout.row()
    row.label(text="Memory: " + str(num_prims*112)+" / 65536 bytes" )



class CSDF_PT_PRIMITIVE(bpy.types.Panel):
    """Creates a Panel in the data context of the properties editor"""
    bl_label = "ConjureSDF"
    bl_idname = "DATA_PT_CSDF_PRIMITIVE"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return (context.object.type in ('MESH', 'EMPTY'))

    def draw(self, context):
        obj = context.active_object       
        layout = self.layout
        scene = context.scene

        if not obj.get('csdfData'):
            layout.label(text="Not a CSDF object")
            return

        csdfData = obj.csdfData
        if csdfData.is_root:
            root = obj
        else:
            root = obj.parent

        if root != obj:
            draw_csdf_primitive_panel(layout, obj)

def row_for_mirror(layout):
    row = layout.row(align=True)
    row.label(icon='MOD_MIRROR')
    sub = row.row(align=True)
    sub.scale_x = 0.6
    return row, sub

def draw_csdf_primitive_panel(layout, obj):

    prefs = get_prefs()
    csdfData = obj.csdfData

    box = layout.box()

    icon_name = "sdf_" + csdfData.primitive_type

    row = box.row()
    row.label(text=obj.name, icon_value=iconloader.id(icon_name))

    # TODO : icons, and use expand=True for text-less UI

    # TODO : only works if we can sync the 3d viewport selection back to the modifier stack active item somehow
    # if obj.parent.csdfData.mod_active_object_index != 0:

    box2 = box.box()

    row = box2.row()
    row.label(text="Operation: ")
    row.scale_x = 2
    row.prop(csdfData, "operation_type", icon_only=True, expand=True)

    strength_text = "Strength"
    if csdfData.operation_type == 'Inset':
        strength_text = "Depth"

    # if not csdfData.operation_type == 'Inset':
    row = box2.row()
    row.label(text="Blending: ")
    row.scale_x = 2
    row.prop(csdfData, "operation_blend", icon_only=True, expand=True)

    if (not csdfData.operation_blend == 'n') or csdfData.operation_type == 'Inset':
        row = box2.row()
        row.prop(csdfData, "operation_strength", text=strength_text)

    if csdfData.operation_strength == 0:
        col = box2.column()
        col.alert = True
        col.label(text="Note: Set Blending to none at 0 strength")
        col.label(text="for better performance")

    row = box2.row()
    row.separator()    

    row = box.row()
    row.prop(csdfData, "primitive_type", text="Primitive")

    row = box.row()
    row.prop(prefs.prims, "keep_scale")

    row = box.row()
    row.separator()

    row = box.row()
    row.label(text="Settings:")

    row = box.row()
    row.prop(csdfData, "ignore_mirror", text="Ignore Mirror")

    row = box.row()
    row.prop(csdfData, "solidify", text="Solidify")

    row2 = row.row()
    if not csdfData.solidify:
        row2.enabled = False
    row2.prop(csdfData, "solidify_strength", text="Thickness")

    if csdfData.primitive_type not in PRIMITIVE_NON_ROUNDED:
        row = box.row()
        row.prop(csdfData, "is_rounded", text="Rounded")

        row2 = row.row()
        if not csdfData.is_rounded:
            row2.enabled = False
        row2.prop(csdfData, "rounding", text="Rounding")

    # only needed if params besides scale or rounding are used
    # if csdfData.primitive_type in ('link', 'Cone', 'rCone'):
    #     paramname = "param"
    #     if csdfData.primitive_type == 'link':
    #         paramname = "Thickness"
    #     if csdfData.primitive_type in ('Cone', 'rCone'):
    #         paramname = "r2"

    #     row = box.row()        
    #     row.prop(csdfData, "parm01", text=paramname)



# based on https://blender.stackexchange.com/questions/166469/example-of-persistent-usage-of-bpy-msgbus-and-how-to-manage-it

from bpy.app.handlers import persistent

prev_active_obj = None
prev_selected_objs = None

def CSDF_modstack_selection_state_handler(scene, depsgraph):

    global prev_active_obj
    global prev_selected_objs

    context = bpy.context
    settings = context.scene.csdf

    if not scene.objects.get("CSDF Root"):
        return

    # TODO : this is very hacky
    # if you delete an object, then select another object, and then UNDO. the node data is updated, while the object is not un-deleted yet.
    # it takes 1 undo to deselect the current object, and 1 undo to bring back the deleted object (this is regular blender behaviour)
    # so just in case, on any call of this function let's clean up any nodes that shouldn't be here, just to be safe
    csdf_prims = get_csdf_prims(bpy.context.scene)

    csdf_scene_nodes = scene.CSDF_SceneNodes

    non_existent_obj_nodes = []
    for node in csdf_scene_nodes:
        if not bpy.context.scene.objects.get(node.obj.name):
            non_existent_obj_nodes.append(node)
    if non_existent_obj_nodes:

        nodes_indices = []
        for node in non_existent_obj_nodes:
            node_indices = []

            child = node
            while child.parentIndex != -1:
                parent = csdf_scene_nodes[child.parentIndex]
                child_idxs = [child.idx for child in parent.childIndices]

                index = child_idxs.index(child.selfIndex)
                node_indices.append(index)

                child = parent

            node_indices.reverse()
            nodes_indices.append(node_indices)
        
        zipped_pair = zip(nodes_indices, non_existent_obj_nodes)
        sorted_non_existent_obj_nodes = [node for _, node in sorted(zipped_pair)]

        sorted_non_existent_obj_nodes.reverse()


        non_existent_prims = [node.obj for node in sorted_non_existent_obj_nodes]
        for obj in non_existent_prims:
            clean_scene(context, settings, obj)

        clean_nodes(context, settings, non_existent_prims)
        settings.force_reload = True

    if settings.block_selection_handler:
        settings.block_selection_handler = False
        return
    
 
    active_obj = context.active_object
    selected_objects = context.selected_objects

    settings = bpy.context.scene.csdf

    if not prev_active_obj:
        update_prev_selection(active_obj, selected_objects)
        update_active_Outliner_item(context, settings, active_obj)
        return
    
    # if there is no CSDF root object in the scene, exit function
    if not bpy.context.scene.objects.get("CSDF Root"):
        update_prev_selection(active_obj, selected_objects)
        return
    
    
    # CHECK IF SELECTION CHANGED
    # ---------------------------------------------------------

    if selected_objects == prev_selected_objs:
        if active_obj == prev_active_obj:
            return # selection did not change

    
    # SELECTION HAS CHANGED

    # SELECTION EMPTY, DELETED SOMETHING
    # ---------------------------------------------------------

    if len(selected_objects)==0 and not active_obj:

        # TODO : update scene here so nested nodes are first unparented before deleting their old parents?

        # for obj in prev_selected_objs:
        #     clean_scene(context, settings, obj)

        # clean_nodes(context, settings, prev_selected_objs)

        # normally selection would be empty anyways
        # this way, the UIlist stays visible

        root = context.scene.objects["CSDF Root"]

        # causes undo step, so it takes 2 undos to undo deleting. Messes up renderer
        # root.select_set(True)
        context.view_layer.objects.active = root

        # TODO : update active index, and block index callback beforehand
        settings.block_index_callback = True
        context.scene.CSDF_OutlinerTree_index -= 1

    # ---------------------------------------------------------

    else:
        # if selection has changed, we might have duplicated something
        
        # figure out what was duplicated? filter out non CSDF objects

        dupli_to_original_mapping = []

        selected_csdf_prims = [obj for obj in selected_objects if obj.csdfData.is_csdf_prim]

        existing_csdf_prims = []
        existing_csdf_IDs = []
        # important that we filter out the selection from this list
        for obj in context.scene.objects:
            if (obj.csdfData.is_csdf_prim and obj not in selected_csdf_prims):
                existing_csdf_prims.append(obj)
                existing_csdf_IDs.append(obj.csdfData.ID)

        for dupli_prim in selected_csdf_prims:
            dupli_prim_ID = dupli_prim.csdfData.ID
            if dupli_prim_ID in existing_csdf_IDs:
                orig_prim_ID_idx = existing_csdf_IDs.index(dupli_prim_ID)

                orig_prim = existing_csdf_prims[orig_prim_ID_idx]
                dupli_to_original_mapping.append((dupli_prim, orig_prim))

                new_rand_ID = generate_csdf_prim_ID(existing_csdf_IDs)
                dupli_prim.csdfData.ID = new_rand_ID
                
            else:
                # if a selected object's ID is not in the other existing IDs (that exclude the selection)
                # it must be an object we haven't duplicated. And so we should exit here
                break

        # above for loop breaks on first item if we're not duplicating, so dupli_to_original_mapping will be empty
        if len(dupli_to_original_mapping):

            settings.block_index_callback = True

            csdf_scene_nodes = context.scene.CSDF_SceneNodes

            new_prims_data = []
            for pair in dupli_to_original_mapping:
                orig_prim = pair[1]
                orig_node = [node for node in csdf_scene_nodes if node.obj == orig_prim][0]
                orig_node_idx = orig_node.selfIndex
                parent_node = csdf_scene_nodes[orig_node.parentIndex]

                num_parents = 0
                curr_node = orig_node
                # lowest possible parent index is 0, only the root node has -1
                # which is excluded in this for loop
                while curr_node.parentIndex != 0:
                    num_parents += 1
                    curr_node = csdf_scene_nodes[curr_node.parentIndex]

                childIndices = [child.idx for child in parent_node.childIndices]
                orig_node_parent_childIndices_idx = childIndices.index(orig_node_idx)

                # if the original parent object is in the list of dupli to original mappings
                # we are duplicating this object and its parent. So the duplicated parent should be the parent of this object
                parent_object = parent_node.obj
                for parent_pair in dupli_to_original_mapping:
                    if parent_pair[1].name == parent_object.name:
                        parent_object = parent_pair[0]
                new_prims_data.append( (pair[0], pair[1], parent_object, num_parents, orig_node_parent_childIndices_idx) )

            # https://stackoverflow.com/questions/20145842/python-sorting-by-multiple-criteria
            # https://stackoverflow.com/questions/8966538/syntax-behind-sortedkey-lambda
            new_prims_data = sorted(new_prims_data, key=lambda data: (data[3], data[4]) )

            for data in new_prims_data:
                # by using data[1] we can duplicate under a selected object!
                add_csdf_scene_node(data[0], data[2], context)
                
                # data[0]'s node index, will be the last added node in this for loop
                curr_prim = csdf_scene_nodes[-1]
                curr_prim_idx = curr_prim.selfIndex

                # parent_node = [node for node in csdf_scene_nodes if node.obj == orig_prim][0]
                parent_node = csdf_scene_nodes[curr_prim.parentIndex]
                old_prim_list = [child.idx for child in parent_node.childIndices if csdf_scene_nodes[child.idx].obj == data[1] ]

                # if this is empty, we're duplicating this prim as part of a parent prim that is duplicated
                # if it were empty, we'd skip over this code
                if old_prim_list:
                    old_prim_idx = old_prim_list[0]


                    childIndices = [child.idx for child in parent_node.childIndices]

                    old_prim_child_idx = childIndices.index(old_prim_idx)
                    curr_prim_child_idx = childIndices.index(curr_prim_idx)

                    parent_node.childIndices.move(curr_prim_child_idx, old_prim_child_idx+1)

                    treeList = context.scene.CSDF_OutlinerTree

                    item_dupli_idx = 0
                    for idx, item in enumerate(treeList):
                        if item.obj == data[1]:
                            item_orig_idx = idx
                            item_orig_expanded = item.expanded
                        elif item.obj == data[0]:
                            item_dupli_idx = idx
                            item_dupli_indent = item.indent

                    # if this is still 0, it means the duplicated item was not visible in the outliner (a collapsed sub item) so we can skip this
                    if item_dupli_idx:
                        from ....addon.operator.modifier_stack.main import get_treelist_candidates
                        treelist_candidates = get_treelist_candidates(treeList, item_dupli_idx, item_dupli_indent)

                        target_candidate_idx = treelist_candidates.index(item_orig_idx)

                        if item_orig_expanded:
                            target_idx = treelist_candidates[target_candidate_idx+1]
                        else:
                            target_idx = item_orig_idx+1

                        treeList.move(item_dupli_idx, target_idx)

                        settings.block_index_callback = True
                        context.scene.CSDF_OutlinerTree_index = target_idx
                        





    # update previous selection, for next time this function is called
    update_prev_selection(active_obj, selected_objects)
    # ---------------------------------------------------------


    # SYNC ACTIVE ITEM IN CSDF OUTLINER TO ACTIVE OBJECT IN 3D VIEWPORT
    # ---------------------------------------------------------
    update_active_Outliner_item(context, settings, active_obj)
    # ---------------------------------------------------------

    # settings.force_reload = True



def clean_scene(context, settings, obj):

    # needs to be fetched every time this function is called (often called in a loop for multiple objects)
    # else it's outdated? not sure
    csdf_scene_nodes = context.scene.CSDF_SceneNodes
    deleted_node_list = [node for node in csdf_scene_nodes if node.obj == obj]

    if deleted_node_list:
        deleted_node = deleted_node_list[0]
        child_nodes = [csdf_scene_nodes[child.idx] for child in deleted_node.childIndices]

        settings.block_index_callback = True
        update_scene(child_nodes, csdf_scene_nodes, context, unnest=True, active_obj=None)



def clean_nodes(context, settings, prev_selected_objs):

    csdf_scene_nodes = context.scene.CSDF_SceneNodes
    treeList = context.scene.CSDF_OutlinerTree

    deleted_nodes_offsets = []

    # tag nodes to delete
    offset = 0
    for idx, node in enumerate(csdf_scene_nodes):
        # current selection is empty, but we still know what was selected before this 
        # handler was called
        if node.obj in prev_selected_objs:
            node_offset = -1
            offset += 1
        else:
            node_offset = offset
        
        deleted_nodes_offsets.append(node_offset)

    treeList_length = len(treeList)
    # remove UIlist items, and adjust the childCount and expanded status of their parent items
    for rev_idx, item in enumerate(reversed(treeList)):
        true_idx = (treeList_length-1)-rev_idx
        node_idx = item.nodeIndex

        node_offset = deleted_nodes_offsets[node_idx]

        if node_offset == -1:
            treeList.remove(true_idx)
        
            # update childCount of the "parent" item in the UI list
            node = csdf_scene_nodes[node_idx]
            parent_node = csdf_scene_nodes[node.parentIndex]

            parent_item = [item for item in treeList if item.obj == parent_node.obj]
            if parent_item:
                parent_item = parent_item[0]

                parent_item.childCount -= 1
                if parent_item.childCount <= 0:
                    parent_item.expanded = False
        elif node_offset > 0:
            item.nodeIndex -= node_offset

    # delete nodes in reverse order, adjust selfIndex
    for node in reversed(csdf_scene_nodes):
        node_offset = deleted_nodes_offsets[node.selfIndex]
        if node_offset == -1:
            csdf_scene_nodes.remove(node.selfIndex)
        else:
            node.selfIndex -= node_offset

    # deletes node indices in children of nodes, adjusts indices too
    # adjusts childCount as well
    for node in csdf_scene_nodes:
        if node.childCount:
            parent_node_index = node.selfIndex
            num_child_indices = len(node.childIndices)
            for rev_idx, child_node_idx in enumerate(reversed(node.childIndices)):
                node_offset = deleted_nodes_offsets[child_node_idx.idx]
                true_idx = (num_child_indices-1)-rev_idx

                if node_offset == -1:
                    node.childIndices.remove(true_idx)
                else:
                    child_node_idx.idx -= node_offset
                    csdf_scene_nodes[child_node_idx.idx].parentIndex = parent_node_index
            node.childCount = len(node.childIndices)

    # settings.force_reload = True
            

def update_prev_selection(active_obj, selected_objects):
    global prev_active_obj
    global prev_selected_objs

    prev_active_obj = active_obj
    prev_selected_objs = selected_objects

def update_active_Outliner_item(context, settings, active_obj):
    treeList = context.scene.CSDF_OutlinerTree

    for idx, item in enumerate(treeList):
        if item.obj == active_obj:

            # avoids recursion
            if context.scene.CSDF_OutlinerTree_index != idx:
                # setting it in here avoids setting it without updating the index
                settings.block_index_callback = True
                context.scene.CSDF_OutlinerTree_index = idx



def subscribe_selection_state():

    bpy.app.handlers.depsgraph_update_post.append(CSDF_modstack_selection_state_handler)

    # Register the persistent handler, ensures that the subscription will happen 
    # when a new file is loaded.
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)


def unsubscribe_selection_state():

    if CSDF_modstack_selection_state_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(CSDF_modstack_selection_state_handler)

    # Unregister the persistent handler.
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)


@persistent
def load_handler(dummy):
    subscribe_selection_state()
