import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix
from uuid import uuid4
from . utils.draw import draw_stashes_HUD, draw_stashes_VIEW3D
from . utils.math import flatten_matrix
from . utils.mesh import get_coords
from . utils.stash import get_version_as_tuple
from . utils.registration import reload_msgbus
from . import bl_info


@persistent
def update_msgbus(none):
    reload_msgbus()



@persistent
def update_stashes(none):
    scene = bpy.context.scene
    objects = [obj for obj in bpy.data.objects if obj.MM.stashes]
    version = '.'.join([str(v) for v in bl_info['version']])

    revision = bl_info.get("revision")

    if revision and not scene.MM.revision:
        scene.MM.revision = revision

    for obj in objects:
        updatable = [stash for stash in obj.MM.stashes if get_version_as_tuple(stash.version) < (0, 7)]

        if updatable:
            print(f"INFO: Updating {obj.name}'s stashes to version {version}")

            for stash in updatable:
                stash.version = version
                stash.uuid = str(uuid4())

                if stash.obj:
                    stash.obj.MM.stashuuid = stash.uuid

                    deltamx = stash.obj.MM.stashtargetmx.inverted_safe() @ stash.obj.MM.stashmx

                    if deltamx == Matrix():
                        stash.self_stash = True

                    stash.obj.MM.stashdeltamx = flatten_matrix(deltamx)
                    stash.obj.MM.stashorphanmx = flatten_matrix(stash.obj.MM.stashtargetmx)

                    stash.obj.MM.stashmx.identity()
                    stash.obj.MM.stashtargetmx.identity()




stashesHUD = None
oldactive = None
oldstasheslen = 0
oldinvalidstasheslen = 0


@persistent
def stashes_HUD(none):
    global stashesHUD, oldactive, oldstasheslen, oldinvalidstasheslen

    if stashesHUD and "RNA_HANDLE_REMOVED" in str(stashesHUD):
        stashesHUD = None

    active = getattr(bpy.context, 'active_object', None)

    if active:
        stasheslen = len(active.MM.stashes)
        invalidstasheslen = len([stash for stash in active.MM.stashes if not stash.obj])

        if not stashesHUD:
            oldactive = active
            oldstasheslen = stasheslen
            oldinvalidstasheslen = invalidstasheslen

            stashesHUD = bpy.types.SpaceView3D.draw_handler_add(draw_stashes_HUD, (bpy.context, stasheslen, invalidstasheslen), 'WINDOW', 'POST_PIXEL')

        if active != oldactive or stasheslen != oldstasheslen or invalidstasheslen != oldinvalidstasheslen:
            oldactive = active
            oldstasheslen = stasheslen
            oldinvalidstasheslen = invalidstasheslen

            bpy.types.SpaceView3D.draw_handler_remove(stashesHUD, 'WINDOW')
            stashesHUD = bpy.types.SpaceView3D.draw_handler_add(draw_stashes_HUD, (bpy.context, stasheslen, invalidstasheslen), 'WINDOW', 'POST_PIXEL')

    elif stashesHUD:
        bpy.types.SpaceView3D.draw_handler_remove(stashesHUD, 'WINDOW')
        stashesHUD = None



stashesVIEW3D = None
oldstashuuid = None


@persistent
def stashes_VIEW3D(scene):
    global stashesVIEW3D, oldstashuuid

    if stashesVIEW3D and "RNA_HANDLE_REMOVED" in str(stashesVIEW3D):
        stashesVIEW3D = None

    C = bpy.context

    active = C.active_object if getattr(C, 'active_object', None) and C.active_object.MM.stashes else None
    stash = active.MM.stashes[active.MM.active_stash_idx] if active and active.MM.stashes[active.MM.active_stash_idx].obj else None

    if scene.MM.draw_active_stash and stash:
        if not stashesVIEW3D:
            oldstashuuid = stash.uuid

            batch = get_coords(stash.obj.data, mx=active.matrix_world, offset=0.002, indices=True)
            stashesVIEW3D = bpy.types.SpaceView3D.draw_handler_add(draw_stashes_VIEW3D, (scene, batch, ), 'WINDOW', 'POST_VIEW')

        if oldstashuuid != stash.uuid:
            oldstashuuid = stash.uuid

            batch = get_coords(stash.obj.data, mx=active.matrix_world, offset=0.002, indices=True)
            bpy.types.SpaceView3D.draw_handler_remove(stashesVIEW3D, 'WINDOW')
            stashesVIEW3D = bpy.types.SpaceView3D.draw_handler_add(draw_stashes_VIEW3D, (scene, batch, ), 'WINDOW', 'POST_VIEW')


    elif stashesVIEW3D:
        bpy.types.SpaceView3D.draw_handler_remove(stashesVIEW3D, 'WINDOW')
        stashesVIEW3D = None
