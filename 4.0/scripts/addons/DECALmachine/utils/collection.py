import bpy


def get_decaltype_collection(context, decaltype):
    scene = context.scene
    mcol = scene.collection

    decalsname = ".Decals" if scene.DM.hide_decaltype_collections else "Decals"
    typename = ".%s" % (decaltype.capitalize()) if scene.DM.hide_decaltype_collections else decaltype.capitalize()

    dcol = bpy.data.collections.get(decalsname)

    if dcol:
        if dcol.name not in mcol.children:
            mcol.children.link(dcol)

    else:
        dcol = bpy.data.collections.new(name=decalsname)
        mcol.children.link(dcol)
        dcol.DM.isdecaltypecol = True

    dtcol = bpy.data.collections.get(typename)

    if dtcol:
        if dtcol.name not in dcol.children:
            dcol.children.link(dtcol)

    else:
        dtcol = bpy.data.collections.new(name=typename)
        dcol.children.link(dtcol)
        dtcol.DM.isdecaltypecol = True

    return dtcol


def get_parent_collections(scene, obj):
    dpcols = []

    if obj.parent:
        cols = [col for col in obj.parent.users_collection if not col.DM.isdecaltypecol]

        for col in cols:
            dpcol = None

            for childcol in col.children:
                if childcol.DM.isdecalparentcol:
                    dpcol = childcol
                    break

            if not dpcol:
                dpcol = bpy.data.collections.new("tempdecals")
                col.children.link(dpcol)
                dpcol.DM.isdecalparentcol = True

            dpcol.name = ".%s_Decals" % (col.name) if scene.DM.hide_decalparent_collections else "%s_Decals" % (col.name)

            dpcols.append(dpcol)

    return dpcols


def unlink_object(obj):
    for col in obj.users_collection:
        col.objects.unlink(obj)


def purge_decal_collections(debug=False):
    decalsname = ".Decals" if bpy.context.scene.DM.hide_decaltype_collections else "Decals"

    purge_collections = [col for col in bpy.data.collections if ((col.DM.isdecaltypecol and col.name != decalsname) or col.DM.isdecalparentcol) and (not col.objects and not col.children)]

    for col in purge_collections:
        if debug:
            print("Removing collection: %s" % (col.name))

        bpy.data.collections.remove(col, do_unlink=True)

    dcol = bpy.data.collections.get(decalsname)

    if dcol and dcol.DM.isdecaltypecol and not dcol.objects and not dcol.children:
        if debug:
            print("Removing collection: %s" % (dcol.name))

        bpy.data.collections.remove(dcol, do_unlink=True)


def sort_into_collections(context, obj, purge=True):

    scene = context.scene
    decaltype = scene.DM.collection_decaltype
    parent = scene.DM.collection_decalparent
    active = scene.DM.collection_active

    sorted_collections = []

    if len(bpy.data.scenes) == 1:
        if decaltype:
            dtcol = get_decaltype_collection(context, obj.DM.decaltype)
            if obj.name not in dtcol.objects:
                dtcol.objects.link(obj)

            sorted_collections.append(dtcol)



    if parent:
        dpcols = get_parent_collections(scene, obj)

        for dpcol in dpcols:
            if obj.name not in dpcol.objects:
                dpcol.objects.link(obj)

        sorted_collections.extend(dpcols)



    if active:
        acol = bpy.context.view_layer.active_layer_collection.collection

        if not any([acol.DM.isdecaltypecol, acol.DM.isdecalparentcol]):
            if obj.name not in acol.objects:
                acol.objects.link(obj)

            sorted_collections.append(acol)



    unlink_collections = [col for col in obj.users_collection if col not in sorted_collections]

    for col in unlink_collections:
        col.objects.unlink(obj)



    if not any([decaltype, parent, active]) or not obj.users_collection:
        mcol = scene.collection

        if obj.name not in mcol.objects:
            mcol.objects.link(obj)

        sorted_collections.append(mcol)


    if purge:
        purge_decal_collections()


def collapse_collection(context, col):

    def get_outliner_area(context):
        for area in context.screen.areas:
            if area.type == 'OUTLINER':
                return area

    layercol = get_layer_collection_from_collection(context.view_layer.layer_collection, col)

    if layercol:
        area = get_outliner_area(context)

        if area:
            override = {'area': area,
                        'collection': layercol}

            context.view_layer.active_layer_collection = layercol

            bpy.ops.outliner.select_walk(override, 'INVOKE_DEFAULT', direction='LEFT', toggle_all=True)


def get_layer_collection_from_collection(layercol, col):

    found = None

    if (layercol.name == col.name):
        return layercol

    for layer in layercol.children:
        found = get_layer_collection_from_collection(layer, col)
        if found:
            return found


def get_atlas_collection(context, atlas):
    scene = context.scene
    mcol = scene.collection

    acol = bpy.data.collections.get(atlas.name)

    if acol:
        return acol

    else:
        acol = bpy.data.collections.new(name=atlas.name)
        mcol.children.link(acol)

    return acol
