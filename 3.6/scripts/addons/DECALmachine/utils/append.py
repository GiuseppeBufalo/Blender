import bpy
import os


def append_group(filepath, name, link=False, relative=False):
    return append_element(filepath, "groups", name, link, relative)


def append_collection(filepath, name, link=False, relative=False):
    return append_element(filepath, "collections", name, link, relative)


def append_object(filepath, name, link=False, relative=False):
    return append_element(filepath, "objects", name, link, relative)


def append_material(filepath, name, link=False, relative=False):
    return append_element(filepath, "materials", name, link, relative)


def append_scene(filepath, name, link=False, relative=False, unlink_collection=True):
    return append_element(filepath, "scenes", name, link, relative)


def append_world(filepath, name, link=False, relative=False):
    return append_element(filepath, "worlds", name, link, relative)


def append_nodetree(filepath, name, link=False, relative=False):
    return append_element(filepath, "node_groups", name, link, relative)


def append_element(filepath, collection, name, link, relative):
    if os.path.exists(filepath):

        with bpy.data.libraries.load(filepath, link=link, relative=relative) as (data_from, data_to):
            if name in getattr(data_from, collection):
                getattr(data_to, collection).append(name)

            else:
                print(f" WARNING: '{name}' does not exist in {filepath}/{collection}")
                return

        return getattr(data_to, collection)[0]

    else:
        print(f" WARNING: The file '{filepath}' does not exist")
