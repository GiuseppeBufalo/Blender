


def generate_csdf_prim_ID(existing_IDs):
    from random import randint
    random_ID = randint(0, 9999)

    while random_ID in existing_IDs:
        random_ID = randint(0, 9999)

    return random_ID



def NewTreeListItem( treeList, node):
    item = treeList.add()
    item.set_obj(node.obj)

    item.indent = 0
    item.nodeIndex = node.selfIndex
    item.childCount = node.childCount
    return item

def InsertBeneath( treeList, parentIndex, parentIndent, node):
    after_index = parentIndex + 1

    item = NewTreeListItem(treeList,node)
    item.indent = parentIndent+1
    item_index = len(treeList) -1 #because add() appends to end.
    treeList.move(item_index,after_index)

    return treeList[after_index], after_index



def get_treelist_candidates(treeList, current_treeList_idx, current_treeList_item_indent):
    treelist_candidates = []
    for idx, item in enumerate(treeList):
        # items before the current item can only be considered if they are not seperated from the current item
        # by an item with an indent value lower than the current item

        if idx < current_treeList_idx:
            if item.indent < current_treeList_item_indent:
                treelist_candidates.clear()
        elif idx > current_treeList_idx:
            # as soon as we find an item after the current item that has an indent lower than the current item
            # we should exit the loop
            if item.indent < current_treeList_item_indent:
                break

        if item.indent == current_treeList_item_indent:
            treelist_candidates.append(idx)

    return treelist_candidates


def get_new_treelist_item_index(treeList, current_treeList_idx, current_treeList_item_indent):

    treelist_candidates = get_treelist_candidates(treeList, current_treeList_idx, current_treeList_item_indent)
    treelist_self_index = treelist_candidates.index(current_treeList_idx)

    treelist_target_index = None

    if (treelist_self_index+1) < len(treelist_candidates):
        treelist_target_index = treelist_candidates[treelist_self_index+1]-1
    else:
        reduced_treelist = treeList[current_treeList_idx:]
        for idx, item in enumerate(reduced_treelist):
            if item.indent < current_treeList_item_indent:
                treelist_target_index = current_treeList_idx + idx - 1
                break
        if not treelist_target_index:
            treelist_target_index = len(treeList)-1
        

    return treelist_target_index



def add_csdf_scene_node(obj, parent, context):

    # prevent active item callback and selection state handler from firing
    settings = context.scene.csdf

    csdf_scene_nodes = context.scene.CSDF_SceneNodes

    node = csdf_scene_nodes.add()
    node.set_obj(obj)
    node.selfIndex = len(csdf_scene_nodes)-1

    treeList = context.scene.CSDF_OutlinerTree

    for idx, parentnode in enumerate(csdf_scene_nodes):
        if parentnode.obj.name == parent.name:
            node.parentIndex = idx
            
            # update parent
            parentnode.childCount = parentnode.childCount+1
            childindex = parentnode.childIndices.add()
            childindex.idx = node.selfIndex

            # update OutlinerItem if it exists
            for idx, item in enumerate(treeList):
                if item.obj == parentnode.obj:

                    item_target_idx = get_new_treelist_item_index(treeList, idx, item.indent)

                    # add a nested item if parent is not 0
                    if item.expanded:
                        settings.block_index_callback = True
                        _, item_idx = InsertBeneath(treeList, item_target_idx, item.indent, node)
                        context.scene.CSDF_OutlinerTree_index = item_idx

                    item.childCount = item.childCount + 1
            break

    # add to top level if parent is 0
    if 0 == node.parentIndex :
        NewTreeListItem(treeList, node)

        settings.block_index_callback = True
        context.scene.CSDF_OutlinerTree_index = len(treeList)-1



def filter_selection(csdf_scene_nodes, selection):
    """
    Filters selected objects and returns their CSDF scene nodes, and a string of nodes in the selection that were skipped.

    returns nodes that are nested the least deep, and share the same parent.
    In the case of nodes with differing parents but identical nesting levels, the last created ones are returned.(may change in the future)
    """


    # if someone has indented more than this... that's a problem
    lowest_num_parents = 999
    parent_idx = None
    nodes_to_move = []
    nodes_junk = []
    

    for node in csdf_scene_nodes:

        # we only care about moving nodes whose objects are selected
        if node.obj not in selection:
            continue

        # ignore root node
        if node.selfIndex == 0:
            continue

        num_parents = 0
        curr_node = node
        # lowest possible parent index is 0, only the root node has -1
        # which is excluded in this for loop
        while curr_node.parentIndex != 0:
            num_parents += 1
            curr_node = csdf_scene_nodes[curr_node.parentIndex]

        if num_parents == lowest_num_parents:
            # if the selection contains nodes with the same # of parents but different direct parents, throw away the old nodes
            if node.parentIndex != parent_idx:
                nodes_junk += nodes_to_move
                nodes_to_move = []
            nodes_to_move.append(node)
            parent_idx = node.parentIndex
        elif num_parents < lowest_num_parents:
            # previous nodes are all worse than this new node, so put them into junk
            nodes_junk += nodes_to_move
            nodes_to_move = []

            nodes_to_move.append(node)

            lowest_num_parents = num_parents
            parent_idx = node.parentIndex
        else:
            # otherwise, nested more deeply than our best nodes so far, we don't move those
            nodes_junk.append(node)
            

    nodes_junk = [node.obj.name + "\n" for node in nodes_junk]
    nodes_junk_str = """"""
    nodes_junk_str = nodes_junk_str.join(nodes_junk)

    return nodes_to_move, nodes_junk_str


def sort_nodes_by_parent(csdf_scene_nodes, nodes):
    """
    Returns nodes, sorted by their order of appearance in the parent node's childIndices
    """
    parent_node = csdf_scene_nodes[nodes[0].parentIndex]
    childindices = [child.idx for child in parent_node.childIndices]
    selected_node_indices = [node.selfIndex for node in nodes]

    sorted_nodes = []
    for childidx in childindices:
        if childidx in selected_node_indices:
            sorted_nodes.append(nodes[selected_node_indices.index(childidx)])

    return sorted_nodes

