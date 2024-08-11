import bpy

from bpy.types import Operator

from ...util.csdf_primitives import get_treelist_candidates, filter_selection, sort_nodes_by_parent, get_new_treelist_item_index, NewTreeListItem
from ...util.object import get_active_and_selected



class CSDF_OT_MODSTACK_MOVE_ITEM(bpy.types.Operator):
    bl_idname = "csdf.modstack_moveitem"
    bl_label = "Move Item"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))
    
    to_topbottom: bpy.props.BoolProperty(name="to top/bottom", description="move completely to the top or bottom of the stack", default=False, options={'SKIP_SAVE'})

    # @classmethod
    # def poll(cls, context):
    #     obj = context.active_object
    #     if obj.get('csdfData'):
    #         if obj.csdfData.is_root:
    #             return True

    def execute(self, context):
        
        # this should never get called, as the UI only shows up with a root in the scene or primitives selected so
        root = bpy.context.scene.objects.get("CSDF Root")
        if not root:
            self.report({'ERROR'}, "No CSDF Root in the scene")
            return {'CANCELLED'}

        csdf_scene_nodes = context.scene.CSDF_SceneNodes
        treeList = context.scene.CSDF_OutlinerTree
        active_idx = context.scene.CSDF_OutlinerTree_index

        selection = context.selected_objects
        
        settings = bpy.context.scene.csdf

        settings.block_index_callback = True
        settings.block_selection_handler = True

        # ------------------------------------------------------------------------------------------
        if len(selection) == 0:
        
            object_to_move = treeList[active_idx].obj
            object_to_move.select_set(True)
            context.view_layer.objects.active = object_to_move
            selection = context.selected_objects

            self.report({'ERROR'}, "Nothing was selected/active in 3D viewport. \nMade active item in SDF outliner the active object")

        # ------------------------------------------------------------------------------------------
        nodes_to_move, nodes_junk_str = filter_selection(csdf_scene_nodes, selection)
        # from filter_selection, we know all nodes share the same parent
        nodes_to_move = sort_nodes_by_parent(csdf_scene_nodes, nodes_to_move)

        if nodes_junk_str:
            self.report({'ERROR'}, "These objects in the selection couldn't be moved. \nAs they are children of other objects in the selection, \nOr have differing parents: \n\n" + nodes_junk_str)

        # ------------------------------------------------------------------------------------------
        # if parent index is not -1, just get the parent node, and read its childIndices
        # otherwise find its next neighbour on the left in the csdf_scene_nodes, that has the same parentIndex 
        if self.direction == 'DOWN':
            nodes_to_move.reverse()

        # ------------------------------------------------------------------------------------------
        new_indices = self.find_new_node_indices(csdf_scene_nodes, nodes_to_move)

        if len(new_indices) == 0:
            return {'CANCELLED'}    

        # needed, else operations done before this operator are also undone 
        # (like moving the prim, not changing the selection, and running this operator)
        bpy.ops.ed.undo_push() 
                   
        # ------------------------------------------------------------------------------------------
        self.move_primitives(csdf_scene_nodes, treeList, nodes_to_move, new_indices)


        # ------------------------------------------------------------------------------------------
        # changing the active index with multiple objects selected is tricky. As doing so triggers the selectModifier_Item callback function for the active index
        # which will clear the current selection and only select/make active the object in the active index.
        # For this reason, callbacks are temporarily blocked for one time (and the block_index_callback is set back to False in the selectModifier_Item callback)

        # update active index in ui list to keep up with where the selected object has moved to
        for idx, item in enumerate(treeList):
            if item.obj == context.active_object:
                context.scene.CSDF_OutlinerTree_index = idx

        # force shader recompilation
        settings.force_reload = True
        
        # moved this to above self.move_primitives() to work better with other operators
        # bpy.ops.ed.undo_push()

        return {'FINISHED'}
    

    def find_new_node_indices(self, csdf_scene_nodes, nodes_to_move):

        # find new node indices for selected nodes
        new_indices = []
        for node_idx, node in enumerate(nodes_to_move):

            parent_node = csdf_scene_nodes[node.parentIndex]
            parent_child_indices = [child.idx for child in parent_node.childIndices]

            # min is of course 0
            max_idx = len(parent_child_indices)-1

            node_childIndices_index = None
            for idx, child_index in enumerate(parent_child_indices):
                if node.selfIndex == child_index:
                    node_childIndices_index = idx

            offset = -1
            if self.direction == 'DOWN':
                offset = 1

            new_node_childIndices_index = node_childIndices_index+offset
            # TODO : adjust index to be equal to index in nodes_to_move (when moving up)
            # or equal to max_idx - idx (when moving down)
            if self.to_topbottom:
                if self.direction == 'DOWN':
                    new_node_childIndices_index = max_idx-node_idx
                elif self.direction == 'UP':
                    new_node_childIndices_index = node_idx
            
            new_node_childIndices_index = min(max(0, new_node_childIndices_index), max_idx)
            if new_node_childIndices_index == node_childIndices_index:
                new_indices.append((-1,-1))
            else:
                new_indices.append((node_childIndices_index, new_node_childIndices_index))

        return new_indices
    
    
    def move_primitives(self, csdf_scene_nodes, treeList, nodes_to_move, new_indices):

        # move nodes around in csdf_scene_nodes
        # and update treeList
        for node_idx, node in enumerate(nodes_to_move):
            old_new_index = new_indices[node_idx]
            old_childIndices_index = old_new_index[0]
            new_childIndices_index = old_new_index[1]

            # means this node can't move, is at top or bottom of childIndices list
            if old_childIndices_index == -1:
                continue

            parent_node = csdf_scene_nodes[node.parentIndex]
            parent_node.childIndices.move(old_childIndices_index, new_childIndices_index)


            current_treeList_data = [[idx, item] for idx, item in enumerate(treeList) if item.nodeIndex == node.selfIndex]
            if not current_treeList_data:
                continue

            current_treeList_idx = current_treeList_data[0][0]
            current_treeList_item_indent = current_treeList_data[0][1].indent
            current_treeList_item_expanded = current_treeList_data[0][1].expanded

            dir = -1
            if self.direction == 'DOWN':
                dir = 1


            treelist_candidates = get_treelist_candidates(treeList, current_treeList_idx, current_treeList_item_indent)

            treelist_self_index = treelist_candidates.index(current_treeList_idx)
            target_item_idx = treelist_self_index+dir

            # nodes_to_move are reversed when moving DOWN, so bottom item is moved first
            if self.to_topbottom:
                if self.direction == 'DOWN':
                    target_item_idx = (len(treelist_candidates)-1)-node_idx
                elif self.direction == 'UP':
                    target_item_idx = node_idx

            target_idx = treelist_candidates[target_item_idx]


            if self.direction == 'DOWN' and treeList[target_idx].expanded:
                # go to next item
                target_item_idx += 1
                if target_item_idx < len(treelist_candidates):
                    # get the next item in the list of candidates, target the item right before it
                    target_treeList_idx = treelist_candidates[target_item_idx]-1
                else:
                    # previous item was already the last candidate, and it's expanded so we just need to put ourselves at the last index in the treeList
                    target_treeList_idx =  len(treeList)-1
            else:
                target_treeList_idx = treelist_candidates[target_item_idx]


            if target_treeList_idx >= len(treeList):
                continue
            if target_treeList_idx < 0:
                continue

            treeList.move(current_treeList_idx, target_treeList_idx)
            
            # move children if it has any
            if current_treeList_item_expanded:

                offset = 1
                if self.direction == 'DOWN':
                    offset = 0

                reduced_treeList = treeList[current_treeList_idx+offset:]
                child_items_data = []

                for item in reduced_treeList:
                    if item.indent > current_treeList_item_indent:
                        current_treeList_idx += offset
                        target_treeList_idx += offset
                        child_items_data.append((current_treeList_idx, target_treeList_idx))
                    else:
                        break

                if self.direction == 'DOWN':
                    child_items_data.reverse()

                for item in child_items_data:
                    treeList.move(item[0], item[1])
            


class CSDF_OT_SELECT_NESTED_PRIMITIVES(bpy.types.Operator):
    bl_idname = "csdf.modstack_selectnestedprimitives"
    bl_label = "Select nested primitives"

    def execute(self, context):
        
        # this should never get called, as the UI only shows up with a root in the scene or primitives selected so
        root = bpy.context.scene.objects.get("CSDF Root")
        if not root:
            self.report({'ERROR'}, "No CSDF Root in the scene")
            return {'CANCELLED'}

        csdf_scene_nodes = context.scene.CSDF_SceneNodes
        treeList = context.scene.CSDF_OutlinerTree
        active_idx = context.scene.CSDF_OutlinerTree_index

        active_item = treeList[active_idx]
        node = csdf_scene_nodes[active_item.nodeIndex]

        self.recursive_select(csdf_scene_nodes, node)


        return {'FINISHED'}
    

    def recursive_select(self, csdf_scene_nodes, node):
        childIndices = [child.idx for child in node.childIndices]
        for idx in childIndices:
            child_node = csdf_scene_nodes[idx]
            child_node.obj.select_set(True)

            if child_node.childCount:
                self.recursive_select(csdf_scene_nodes, child_node)



class CSDF_OT_UNNEST_PRIMITIVE(bpy.types.Operator):
    """Reduce nesting by one level. \nNest under active primitive"""
    bl_idname = "csdf.modstack_unnestprimitive"
    bl_label = "Reduce nesting by one level. \nNest under active primitive"
    # TODO : Ctrl to immediately move to the root

    unnest: bpy.props.BoolProperty(name="un nest", description="move completely to the top or bottom of the stack", default=True, options={'SKIP_SAVE'})



    def execute(self, context):
        
        # this should never get called, as the UI only shows up with a root in the scene or primitives selected so
        root = bpy.context.scene.objects.get("CSDF Root")
        if not root:
            self.report({'ERROR'}, "No CSDF Root in the scene")
            return {'CANCELLED'}

        selected_objects = None
        active_obj = None
        if self.unnest:
            selected_objects = context.selected_objects
        else:
            active_obj, selected_objects = get_active_and_selected(context)

        csdf_scene_nodes = context.scene.CSDF_SceneNodes
        nodes, nodes_junk_str = self.filter_sort_selection(selected_objects, csdf_scene_nodes)

        if not self.unnest:
            nodes.reverse()

        if nodes_junk_str:
            self.report({'ERROR'}, "These objects in the selection couldn't be moved. \nAs they are children of other objects in the selection, \nOr have differing parents: \n\n" + nodes_junk_str)

        if not self.unnest:
            if len(nodes) < 1:
                self.report({'ERROR'}, "Selection needs to contain one or more selected SDF primitive and one active SDF primitive.")
                return {'FINISHED'}

        # have to ignore the active object when nesting under it
        if not self.unnest:
            active_obj.select_set(False)
            selected_objects[0].select_set(True)
        # TODO refactor this and the other modstack operators to have a common set of functions, no/less need for bpy.ops in other ops
        # works properly for now, might cause issues with additional undo's down the line
        try:
            bpy.ops.csdf.modstack_moveitem(direction='DOWN', to_topbottom=True)
        except:
            pass

        # have to ignore the active object when nesting under it
        if not self.unnest:
            active_obj.select_set(True)


        update_scene(nodes, csdf_scene_nodes, context, self.unnest, active_obj)

        settings = bpy.context.scene.csdf
        settings.force_reload = True

        # TODO BUG very strange
        # weird hack to get shader to recompile when unnesting a prim that is nested 2 or more levels deep
        settings.block_index_callback = True
        active_idx = context.scene.CSDF_OutlinerTree_index
        context.scene.CSDF_OutlinerTree_index = active_idx

        return {'FINISHED'}
    


    def filter_sort_selection(self, selected_objects, csdf_scene_nodes):
        nodes, nodes_junk_str = filter_selection(csdf_scene_nodes, selected_objects)
        # from filter_selection, we know all nodes share the same parent
        if nodes:
            nodes = sort_nodes_by_parent(csdf_scene_nodes, nodes)   
        return nodes, nodes_junk_str   






def update_scene(nodes, csdf_scene_nodes, context, unnest, active_obj):
    for node in reversed(nodes):
        # means this node is already at root level
        if unnest and node.parentIndex == 0:
            continue

        # find parent nodes
        parent_node = csdf_scene_nodes[node.parentIndex]
        if unnest:
            newparent_node = csdf_scene_nodes[parent_node.parentIndex]

            newparent_node_childIndices = [child.idx for child in newparent_node.childIndices]
            node_target_idx = newparent_node_childIndices.index(parent_node.selfIndex)
        else:
            newparent_node = [node for node in csdf_scene_nodes if node.obj == active_obj][0]
            node_target_idx = len(newparent_node.childIndices)-1

        update_nodes(node, parent_node, newparent_node, node_target_idx)

        treeList = context.scene.CSDF_OutlinerTree
        update_treeList(context, treeList, node, parent_node, newparent_node, unnest)



def update_nodes(node, parent_node, newparent_node, node_target_idx):
    # remove node from its parent node data
    parent_node_childIndices = [child.idx for child in parent_node.childIndices]
    node_childIndices_idx = parent_node_childIndices.index(node.selfIndex)

    parent_node.childIndices.remove(node_childIndices_idx)
    parent_node.childCount = len(parent_node.childIndices)

    # add node to newparent node
    node.parentIndex = newparent_node.selfIndex
    childindex = newparent_node.childIndices.add()
    childindex.idx = node.selfIndex
    newparent_node.childCount += 1
    curr_node_child_idx = len(newparent_node.childIndices)-1
    newparent_node.childIndices.move(curr_node_child_idx, node_target_idx+1)



def update_treeList(context, treeList, node, parent_node, newparent_node, unnest):

    # TODO might be worth swapping out if necessary in the future

    # # using a for loop with ifs in it, is about 10% faster
    # node_item_list = None
    # parent_node_item_list = None
    # newparent_node_item_list = None

    # for idx, item in enumerate(treeList):
    #     item_obj = item.obj
    #     item_list = (idx, item)

    #     if item_obj == node.obj:
    #         node_item_list = item_list
    #     if item_obj == parent_node.obj:
    #         parent_node_item_list = item_list
    #     if item_obj == newparent_node.obj:
    #         newparent_node_item_list = item_list


    node_item_list =            [(idx, item) for idx, item in enumerate(treeList) if item.obj == node.obj]
    parent_node_item_list =     [(idx, item) for idx, item in enumerate(treeList) if item.obj == parent_node.obj]
    newparent_node_item_list =  [(idx, item) for idx, item in enumerate(treeList) if item.obj == newparent_node.obj]

    node_item,              node_item_idx =            validate_tree_item_list(node_item_list)
    parent_node_item,       parent_node_item_idx =     validate_tree_item_list(parent_node_item_list)
    newparent_node_item,    newparent_node_item_idx =  validate_tree_item_list(newparent_node_item_list)


    if parent_node_item:
        parent_node_item.childCount -= 1
        if parent_node_item.childCount == 0:
            parent_node_item.expanded = False


    if newparent_node_item or newparent_node.selfIndex == 0:

        if newparent_node.selfIndex == 0:

            node_item_newindent = 0
            node_item_newidx = len(treeList)-1

            # only makes sense when old parent is right under root I guess?
            # node_item_newidx = get_new_treelist_item_index(treeList, parent_node_item_idx, parent_node_item.indent)

        else:
            newparent_node_item.childCount += 1

            node_item_newindent = newparent_node_item.indent + 1
            node_item_newidx = get_new_treelist_item_index(treeList, newparent_node_item_idx, newparent_node_item.indent)

        
        # when unnesting by one level, this is always true
        if parent_node.parentIndex == newparent_node.selfIndex:
            if parent_node_item:
                node_item_newidx = get_new_treelist_item_index(treeList, parent_node_item_idx, parent_node_item.indent)



        if node_item:
            # TODO : collapsing/unfolding item to "automatically" update all the nested indents is a bit of a hack
            item_was_expanded = False

            if node_item.expanded:
                item_was_expanded = True
                bpy.ops.object.csdf_expandoutlineritem(button_id=node_item_idx)

            node_item.indent = node_item_newindent

            # NOTE : this might cause issues elsewhere
            # when moving node_item down, by more than 1 spot

            if ((node_item_newidx+1) - node_item_idx) >= 2:
                # only valid when not un/renesting to the root
                if newparent_node.selfIndex != 0:
                    node_item_newidx -= 1
                    newparent_node_item_idx -= 1

            if unnest:
                if ((node_item_newidx+1) - node_item_idx) == 1:
                    node_item_newidx = node_item_idx-1
            
            treeList.move(node_item_idx, node_item_newidx+1)

            if item_was_expanded:
                bpy.ops.object.csdf_expandoutlineritem(button_id=node_item_idx)

            if newparent_node_item:
                if not newparent_node_item.expanded:
                    if node_item.expanded:
                        bpy.ops.object.csdf_expandoutlineritem(button_id=node_item_idx)
                    treeList.remove(node_item_newidx+1)

                    bpy.ops.object.csdf_expandoutlineritem(button_id=newparent_node_item_idx)
                
        else:
            if newparent_node_item:
                if newparent_node_item.expanded:
                    make_new_tree_item(context, treeList, node, node_item_newindent, node_item_newidx)
                else:
                    bpy.ops.object.csdf_expandoutlineritem(button_id=newparent_node_item_idx)
            elif newparent_node.selfIndex == 0:
                make_new_tree_item(context, treeList, node, node_item_newindent, node_item_newidx)

    # new parent doesn't exist in UI list, and we're not moving to the root level
    elif node_item:
        if node_item.expanded:
            bpy.ops.object.csdf_expandoutlineritem(button_id=node_item_idx)
        treeList.remove(node_item_idx)



def validate_tree_item_list(item_list):
    if item_list:
        return item_list[0][1], item_list[0][0]
    else:
        return None, None



def make_new_tree_item(context, treeList, node, node_item_newindent, node_item_newidx):
    item = NewTreeListItem(treeList, node)
    item.indent = node_item_newindent
    item_index = len(treeList) -1 #because add() appends to end.
    treeList.move(item_index, node_item_newidx+1)

    context.scene.CSDF_OutlinerTree_index = node_item_newidx+1       


