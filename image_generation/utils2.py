#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import sys, os, random
import bpy, bpy_extras

"""
Utility functions for interacting with Blender in a CLEVR-like scene generation context.
All code here assumes Blender 2.80+ (where 'layers' have been replaced by 'collections').
"""


def extract_args(input_argv=None):
    """
    Pull out command-line arguments after "--". Blender ignores command-line flags
    after --, so we pass them along to our own script.
    """
    if input_argv is None:
        input_argv = sys.argv
    if '--' not in input_argv:
        return []
    idx = input_argv.index('--')
    return input_argv[idx+1:]


def delete_object(obj):
    """
    Delete a specified blender object.
    Works for Blender 2.80+.
    """
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.delete()


def get_camera_coords(cam, pos):
    """
    Given a camera and a 3D position, return (px, py, pz) in image coordinates
    and normalized device coordinate depth (-1..1).
    """
    scene = bpy.context.scene
    x, y, z = bpy_extras.object_utils.world_to_camera_view(scene, cam, pos)
    scale = scene.render.resolution_percentage / 100.0
    w = int(scale * scene.render.resolution_x)
    h = int(scale * scene.render.resolution_y)
    px = int(round(x * w))
    py = int(round(h - y * h))
    return (px, py, z)


def set_layer(obj, layer_idx):
    """
    In Blender 2.80+, "layers" have been replaced by "collections."
    This function simulates moving an object to a collection named "Layer_{layer_idx}".
    By default, everything is in the master collection.
    """
    # Remove from all collections first
    for c in bpy.data.collections:
        if obj.name in c.objects:
            c.objects.unlink(obj)

    # Ensure the scene collection is retrieved
    scene_collection = bpy.context.scene.collection
    layer_name = f"Layer_{layer_idx}"

    # If layer_idx == 0, link to the main scene collection
    if layer_idx == 0:
        if obj.name not in scene_collection.objects:
            scene_collection.objects.link(obj)
        return

    # Otherwise, create or get a sub-collection
    if layer_name not in bpy.data.collections:
        new_coll = bpy.data.collections.new(layer_name)
        scene_collection.children.link(new_coll)

    target_coll = bpy.data.collections[layer_name]
    if obj.name not in target_coll.objects:
        target_coll.objects.link(obj)


def add_object(object_dir, name, scale, loc, theta=0):
    """
    Load an object from a .blend in object_dir. The .blend is named <name>.blend,
    containing an object named <name> at the origin with unit size.
      - scale: float
      - loc: (x, y) location on ground plane
      - theta: rotation around Z
    """
    count = 0
    for obj in bpy.data.objects:
        if obj.name.startswith(name):
            count += 1

    filepath = os.path.join(object_dir, f"{name}.blend", "Object", name)
    bpy.ops.wm.append(filename=filepath)

    new_name = f"{name}_{count}"
    bpy.data.objects[name].name = new_name

    obj = bpy.data.objects[new_name]
    bpy.context.view_layer.objects.active = obj

    # Rotate, scale, translate
    obj.rotation_euler[2] = theta
    bpy.ops.transform.resize(value=(scale, scale, scale))
    x, y = loc
    bpy.ops.transform.translate(value=(x, y, scale))


def load_materials(material_dir):
    """
    Load each .blend file in material_dir, which should contain a NodeTree
    with the same name as the file.
    """
    for fn in os.listdir(material_dir):
        if fn.endswith('.blend'):
            name = os.path.splitext(fn)[0]
            filepath = os.path.join(material_dir, fn, 'NodeTree', name)
            bpy.ops.wm.append(filename=filepath)


def add_material(name, **properties):
    """
    Create a new material from a pre-loaded node group named `name`.
    Then assign it to the active object.
    We expect that node group to have a Color input we can override.
    """
    # Create a new material
    mat = bpy.data.materials.new(name="MaterialTemp")
    mat.use_nodes = True

    # Attach to active object
    obj = bpy.context.active_object
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat

    # Find the output node
    output_node = None
    for n in mat.node_tree.nodes:
        if n.type == 'OUTPUT_MATERIAL':
            output_node = n
            break

    # Add a group node referencing our preloaded node group
    group_node = mat.node_tree.nodes.new('ShaderNodeGroup')
    group_node.node_tree = bpy.data.node_groups[name]

    # If there's a "Color" input, set it
    for inp in group_node.inputs:
        if inp.name in properties:
            inp.default_value = properties[inp.name]

    # Link
    mat.node_tree.links.new(group_node.outputs['Shader'], output_node.inputs['Surface'])
