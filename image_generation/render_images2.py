#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import print_function
import math, sys, random, argparse, json, os, tempfile
from datetime import datetime as dt
from collections import Counter

"""
Renders random scenes using Blender, each with a random number of objects;
each object has a random size, position, color, and shape. Objects will be
nonintersecting but may partially occlude each other. Output images will be
written to disk as PNGs, and we will also write a JSON file for each image with
ground-truth scene information.

This file is meant to be run from Blender 2.80+ like:

blender --background --python render_images.py -- [args]

Any command-line arguments after `--` will be forwarded to this script.

For help:

python render_images.py --help
"""

INSIDE_BLENDER = True
try:
    import bpy, bpy_extras
    from mathutils import Vector
except ImportError:
    INSIDE_BLENDER = False

if INSIDE_BLENDER:
    try:
        import utils
    except ImportError as e:
        print("\nERROR")
        print("Running render_images.py from Blender and cannot import utils.py.") 
        print("Make sure that utils.py is on Blender's Python path.")
        sys.exit(1)


parser = argparse.ArgumentParser()

# Input options
parser.add_argument('--base_scene_blendfile', default='data/base_scene.blend',
    help="Base blender file on which all scenes are based; includes ground plane, lights, and camera.")
parser.add_argument('--properties_json', default='data/properties.json',
    help="JSON file defining objects, materials, sizes, and colors.")
parser.add_argument('--shape_dir', default='data/shapes',
    help="Directory where .blend files for object models are stored")
parser.add_argument('--material_dir', default='data/materials',
    help="Directory where .blend files for materials are stored")
parser.add_argument('--shape_color_combos_json', default=None,
    help="Optional path to a JSON file mapping shape names to a list of allowed colors.")

# Settings for objects
parser.add_argument('--min_objects', default=3, type=int,
    help="The minimum number of objects to place in each scene")
parser.add_argument('--max_objects', default=10, type=int,
    help="The maximum number of objects to place in each scene")
parser.add_argument('--min_dist', default=0.25, type=float,
    help="The minimum allowed distance between object centers")
parser.add_argument('--margin', default=0.4, type=float,
    help="Objects must be at least this distance apart along left/right/front/back directions.")
parser.add_argument('--min_pixels_per_object', default=200, type=int,
    help="All objects will have at least this many visible pixels in the rendered image.")
parser.add_argument('--max_retries', default=50, type=int,
    help="Number of placement attempts per object before re-placing all objects.")

# Output settings
parser.add_argument('--start_idx', default=0, type=int,
    help="Index at which to start numbering rendered images.")
parser.add_argument('--num_images', default=5, type=int,
    help="The number of images to render")
parser.add_argument('--filename_prefix', default='CLEVR',
    help="Prefix prepended to the rendered images and JSON scenes")
parser.add_argument('--split', default='new',
    help="Name of the split (train, val, test, etc.). Used in filenames and JSON.")
parser.add_argument('--output_image_dir', default='../output/images/',
    help="Where to store output images. Created if it doesn't exist.")
parser.add_argument('--output_scene_dir', default='../output/scenes/',
    help="Where to store output JSON scene structures. Created if it doesn't exist.")
parser.add_argument('--output_scene_file', default='../output/CLEVR_scenes.json',
    help="Path to write a single JSON file containing all scene information.")
parser.add_argument('--output_blend_dir', default='output/blendfiles',
    help="Where to store Blender scene files if --save_blendfiles=1.")
parser.add_argument('--save_blendfiles', type=int, default=0,
    help="If 1, save a .blend file for each generated image (size ~5-10MB each).")
parser.add_argument('--version', default='1.0',
    help="String stored in the 'version' field of the generated JSON.")
parser.add_argument('--license', default="Creative Commons Attribution (CC-BY 4.0)",
    help="String stored in the 'license' field of the generated JSON.")
parser.add_argument('--date', default=dt.today().strftime("%m/%d/%Y"),
    help="String stored in the 'date' field of the generated JSON (defaults to today).")

# Rendering options
parser.add_argument('--use_gpu', default=0, type=int,
    help="If 1, use GPU-accelerated rendering via CUDA (NVIDIA GPUs).")
parser.add_argument('--width', default=320, type=int,
    help="Image width in pixels")
parser.add_argument('--height', default=240, type=int,
    help="Image height in pixels")
parser.add_argument('--key_light_jitter', default=1.0, type=float,
    help="Random jitter magnitude for key light position.")
parser.add_argument('--fill_light_jitter', default=1.0, type=float,
    help="Random jitter magnitude for fill light position.")
parser.add_argument('--back_light_jitter', default=1.0, type=float,
    help="Random jitter magnitude for back light position.")
parser.add_argument('--camera_jitter', default=0.5, type=float,
    help="Random jitter magnitude for camera position.")
parser.add_argument('--render_num_samples', default=512, type=int,
    help="Number of Cycles samples. Higher => slower but less noisy.")
parser.add_argument('--render_min_bounces', default=8, type=int,
    help="Minimum number of transparent bounces.")
parser.add_argument('--render_max_bounces', default=8, type=int,
    help="Maximum number of transparent bounces.")
parser.add_argument('--render_tile_size', default=256, type=int,
    help="Tile size for rendering. Usually bigger is better for GPU.")

def main(args):
    num_digits = 6
    prefix = f'{args.filename_prefix}_{args.split}_'
    img_template = f'{prefix}%0{num_digits}d.png'
    scene_template = f'{prefix}%0{num_digits}d.json'
    blend_template = f'{prefix}%0{num_digits}d.blend'

    img_template = os.path.join(args.output_image_dir, img_template)
    scene_template = os.path.join(args.output_scene_dir, scene_template)
    blend_template = os.path.join(args.output_blend_dir, blend_template)

    if not os.path.isdir(args.output_image_dir):
        os.makedirs(args.output_image_dir)
    if not os.path.isdir(args.output_scene_dir):
        os.makedirs(args.output_scene_dir)
    if args.save_blendfiles == 1 and not os.path.isdir(args.output_blend_dir):
        os.makedirs(args.output_blend_dir)

    all_scene_paths = []

    for i in range(args.num_images):
        img_path = img_template % (i + args.start_idx)
        scene_path = scene_template % (i + args.start_idx)
        all_scene_paths.append(scene_path)
        blend_path = None
        if args.save_blendfiles == 1:
            blend_path = blend_template % (i + args.start_idx)

        num_objects = random.randint(args.min_objects, args.max_objects)
        render_scene(
            args,
            num_objects=num_objects,
            output_index=(i + args.start_idx),
            output_split=args.split,
            output_image=img_path,
            output_scene=scene_path,
            output_blendfile=blend_path,
        )

    # After rendering all images, combine the individual JSON scene files
    # into a single JSON file.
    all_scenes = []
    for scene_path in all_scene_paths:
        with open(scene_path, 'r') as f:
            all_scenes.append(json.load(f))

    output = {
        'info': {
            'date': args.date,
            'version': args.version,
            'split': args.split,
            'license': args.license,
        },
        'scenes': all_scenes
    }
    with open(args.output_scene_file, 'w') as f:
        json.dump(output, f)


def render_scene(
    args,
    num_objects=5,
    output_index=0,
    output_split='none',
    output_image='render.png',
    output_scene='render_json',
    output_blendfile=None,
):
    """
    Render a single scene:
      1. Load the base scene .blend
      2. Set up GPU/CPU rendering, resolution, etc.
      3. Randomly place objects
      4. Check that each object is visible
      5. Render, save PNG
      6. Save scene JSON
      7. Optionally save .blend
    """
    # Load the main .blend file
    bpy.ops.wm.open_mainfile(filepath=args.base_scene_blendfile)

    # Set up the Cycles renderer
    render_args = bpy.context.scene.render
    render_args.engine = 'CYCLES'
    render_args.filepath = output_image
    render_args.resolution_x = args.width
    render_args.resolution_y = args.height
    render_args.resolution_percentage = 100
    # Set tile size for Cycles
    bpy.context.scene.cycles.tile_x = args.render_tile_size
    bpy.context.scene.cycles.tile_y = args.render_tile_size

    if args.use_gpu == 1:
        # Modern approach for GPU with CUDA
        cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
        cycles_prefs.compute_device_type = 'CUDA'
        # Enable all CUDA devices
        for device in cycles_prefs.devices:
            if device.type == 'CUDA':
                device.use = True
        # Use GPU
        bpy.context.scene.cycles.device = 'GPU'

    # Some Cycles-specific settings
    bpy.data.worlds['World'].cycles.sample_as_light = True
    bpy.context.scene.cycles.blur_glossy = 2.0
    bpy.context.scene.cycles.samples = args.render_num_samples
    bpy.context.scene.cycles.transparent_min_bounces = args.render_min_bounces
    bpy.context.scene.cycles.transparent_max_bounces = args.render_max_bounces

    # This structure will hold ground-truth information
    scene_struct = {
        'split': output_split,
        'image_index': output_index,
        'image_filename': os.path.basename(output_image),
        'objects': [],
        'directions': {},
    }

    # Create a temporary plane to figure out cardinal directions
    bpy.ops.mesh.primitive_plane_add(size=10)
    plane = bpy.context.object

    def rand(L):
        return 2.0 * L * (random.random() - 0.5)

    # Add random camera jitter
    if args.camera_jitter > 0:
        cam = bpy.data.objects['Camera']
        for i in range(3):
            cam.location[i] += rand(args.camera_jitter)

    # Determine left/right/front/behind unit vectors (on the plane)
    camera = bpy.data.objects['Camera']
    plane_normal = plane.data.vertices[0].normal

    quat = camera.matrix_world.to_quaternion()
    cam_behind = quat @ Vector((0, 0, -1))
    cam_left = quat @ Vector((-1, 0, 0))
    cam_up = quat @ Vector((0, 1, 0))

    plane_behind = (cam_behind - cam_behind.project(plane_normal)).normalized()
    plane_left = (cam_left - cam_left.project(plane_normal)).normalized()
    plane_up = cam_up.project(plane_normal).normalized()

    # Delete the plane, store directions
    scene_struct['directions']['behind'] = tuple(plane_behind)
    scene_struct['directions']['front']  = tuple(-plane_behind)
    scene_struct['directions']['left']   = tuple(plane_left)
    scene_struct['directions']['right']  = tuple(-plane_left)
    scene_struct['directions']['above']  = tuple(plane_up)
    scene_struct['directions']['below']  = tuple(-plane_up)

    # Remove the plane
    utils.delete_object(plane)

    # Add random jitter to lamp positions
    if args.key_light_jitter > 0:
        for i in range(3):
            bpy.data.objects['Lamp_Key'].location[i] += rand(args.key_light_jitter)
    if args.back_light_jitter > 0:
        for i in range(3):
            bpy.data.objects['Lamp_Back'].location[i] += rand(args.back_light_jitter)
    if args.fill_light_jitter > 0:
        for i in range(3):
            bpy.data.objects['Lamp_Fill'].location[i] += rand(args.fill_light_jitter)

    # Place random objects
    objects, blender_objects = add_random_objects(scene_struct, num_objects, args, camera)

    # Render the final image
    scene_struct['objects'] = objects
    scene_struct['relationships'] = compute_all_relationships(scene_struct)

    # Attempt render until it succeeds (rare Blender crashes)
    while True:
        try:
            bpy.ops.render.render(write_still=True)
            break
        except Exception as e:
            print(e)

    # Save the scene JSON
    with open(output_scene, 'w') as f:
        json.dump(scene_struct, f, indent=2)

    # Optionally save the .blend file
    if output_blendfile is not None:
        bpy.ops.wm.save_as_mainfile(filepath=output_blendfile)


def add_random_objects(scene_struct, num_objects, args, camera):
    """
    Add random objects to the scene, ensure they’re visible,
    and return their attribute info plus the Blender objects themselves.
    """
    # Load property file
    with open(args.properties_json, 'r') as f:
        properties = json.load(f)
        color_name_to_rgba = {}
        for name, rgb in properties['colors'].items():
            rgba = [float(c) / 255.0 for c in rgb] + [1.0]
            color_name_to_rgba[name] = rgba
        material_mapping = [(v, k) for k, v in properties['materials'].items()]
        object_mapping   = [(v, k) for k, v in properties['shapes'].items()]
        size_mapping     = list(properties['sizes'].items())

    shape_color_combos = None
    if args.shape_color_combos_json is not None:
        with open(args.shape_color_combos_json, 'r') as f:
            shape_color_combos = list(json.load(f).items())

    positions = []
    objects = []
    blender_objects = []

    for i in range(num_objects):
        # Choose random size
        size_name, r = random.choice(size_mapping)

        # Try to place without collisions or violating margins
        num_tries = 0
        while True:
            num_tries += 1
            if num_tries > args.max_retries:
                # If we fail too many times, delete all and restart
                for obj in blender_objects:
                    utils.delete_object(obj)
                return add_random_objects(scene_struct, num_objects, args, camera)

            x = random.uniform(-3, 3)
            y = random.uniform(-3, 3)
            dists_good = True
            margins_good = True

            for (xx, yy, rr) in positions:
                dx, dy = x - xx, y - yy
                dist = math.sqrt(dx*dx + dy*dy)
                if dist - r - rr < args.min_dist:
                    dists_good = False
                    break
                # Check margin along cardinal directions
                for direction_name in ['left', 'right', 'front', 'behind']:
                    direction_vec = scene_struct['directions'][direction_name]
                    # direction_vec[2] should be 0 for these directions
                    margin_val = dx * direction_vec[0] + dy * direction_vec[1]
                    if 0 < margin_val < args.margin:
                        margins_good = False
                        break
                if not dists_good or not margins_good:
                    break

            if dists_good and margins_good:
                break

        # Choose shape and color
        if shape_color_combos is None:
            obj_name, obj_name_out = random.choice(object_mapping)
            color_name, rgba = random.choice(list(color_name_to_rgba.items()))
        else:
            obj_name_out, color_choices = random.choice(shape_color_combos)
            color_name = random.choice(color_choices)
            obj_name = [k for k, v in object_mapping if v == obj_name_out][0]
            rgba = color_name_to_rgba[color_name]

        # If it’s a cube, adjust the scaling factor
        if obj_name == 'Cube':
            r /= math.sqrt(2)

        theta = 360.0 * random.random()

        # Actually add the object to Blender
        utils.add_object(args.shape_dir, obj_name, r, (x, y), theta=theta)
        obj = bpy.context.object
        blender_objects.append(obj)
        positions.append((x, y, r))

        # Attach a random material
        mat_name, mat_name_out = random.choice(material_mapping)
        utils.add_material(mat_name, Color=rgba)

        # Record data for this object
        pixel_coords = utils.get_camera_coords(camera, obj.location)
        objects.append({
            'shape': obj_name_out,
            'size': size_name,
            'material': mat_name_out,
            '3d_coords': tuple(obj.location),
            'rotation': theta,
            'pixel_coords': pixel_coords,
            'color': color_name,
        })

    # Check visibility (shadeless pass)
    # all_visible = check_visibility(blender_objects, args.min_pixels_per_object)
    # if not all_visible:
    #     print('Some objects occluded; re-placing objects')
    #     for obj in blender_objects:
    #         utils.delete_object(obj)
    #     return add_random_objects(scene_struct, num_objects, args, camera)

    return objects, blender_objects


def compute_all_relationships(scene_struct, eps=0.2):
    """
    Compute directional relationships between all pairs of objects.
    Returns a dict of lists.
    """
    all_relationships = {}
    for name, direction_vec in scene_struct['directions'].items():
        if name == 'above' or name == 'below':
            continue
        all_relationships[name] = []
        for i, obj1 in enumerate(scene_struct['objects']):
            coords1 = obj1['3d_coords']
            related = set()
            for j, obj2 in enumerate(scene_struct['objects']):
                if i == j:
                    continue
                coords2 = obj2['3d_coords']
                diff = [coords2[k] - coords1[k] for k in [0,1,2]]
                dot = sum(diff[k] * direction_vec[k] for k in [0,1,2])
                if dot > eps:
                    related.add(j)
            all_relationships[name].append(sorted(list(related)))
    return all_relationships


def check_visibility(blender_objects, min_pixels_per_object):
    """
    Render with unique shadeless materials to check that each object
    is visible above a certain pixel threshold.
    """
    f, path = tempfile.mkstemp(suffix='.png')
    os.close(f)
    object_colors = render_shadeless(blender_objects, path=path)

    img = bpy.data.images.load(path)
    pixels = list(img.pixels)
    color_count = Counter((pixels[i], pixels[i+1], pixels[i+2], pixels[i+3])
                          for i in range(0, len(pixels), 4))
    # Clean up temp file
    os.remove(path)

    # Expect len(color_count) == number_of_objects + 1 (background)
    if len(color_count) != len(blender_objects) + 1:
        return False

    # Check that each object has enough visible pixels
    for _, count in color_count.most_common():
        if count < min_pixels_per_object:
            return False
    return True


def render_shadeless(blender_objects, path='flat.png'):
    """
    Assign a unique emission material to each object and render in Cycles
    with no lighting. Then we count pixels to ensure each object is visible.
    """
    render_args = bpy.context.scene.render

    # Store old settings
    old_engine = render_args.engine
    old_filepath = render_args.filepath
    old_filter_size = bpy.context.scene.render.filter_size

    # Use Cycles, disable AA by making filter_size=0
    render_args.engine = 'CYCLES'
    render_args.filepath = path
    bpy.context.scene.render.filter_size = 0.0

    # Temporarily hide lights & ground
    utils.set_layer(bpy.data.objects['Lamp_Key'], 2)
    utils.set_layer(bpy.data.objects['Lamp_Fill'], 2)
    utils.set_layer(bpy.data.objects['Lamp_Back'], 2)
    utils.set_layer(bpy.data.objects['Ground'], 2)

    # Assign random shadeless (emission) materials
    object_colors = set()
    old_materials = []
    for i, obj in enumerate(blender_objects):
        old_materials.append(obj.data.materials[0])
        # Create a new material for emission
        mat = bpy.data.materials.new(name=f"TempEm_{i}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        # Clear default nodes
        for n in nodes:
            nodes.remove(n)
        node_emission = nodes.new(type='ShaderNodeEmission')
        # Find a new random color not used yet
        while True:
            r, g, b = [random.random() for _ in range(3)]
            if (r, g, b) not in object_colors:
                break
        object_colors.add((r, g, b))
        node_emission.inputs[0].default_value = [r, g, b, 1.0]

        node_output = nodes.new(type='ShaderNodeOutputMaterial')
        mat.node_tree.links.new(node_emission.outputs[0], node_output.inputs[0])

        # Assign to object
        obj.data.materials[0] = mat

    # Render
    bpy.ops.render.render(write_still=True)

    # Restore original materials
    for mat, obj in zip(old_materials, blender_objects):
        obj.data.materials[0] = mat

    # Show lights & ground again
    utils.set_layer(bpy.data.objects['Lamp_Key'], 0)
    utils.set_layer(bpy.data.objects['Lamp_Fill'], 0)
    utils.set_layer(bpy.data.objects['Lamp_Back'], 0)
    utils.set_layer(bpy.data.objects['Ground'], 0)

    # Restore old settings
    render_args.filepath = old_filepath
    render_args.engine = old_engine
    bpy.context.scene.render.filter_size = old_filter_size

    return object_colors


if __name__ == '__main__':
    if INSIDE_BLENDER:
        argv = utils.extract_args()
        args = parser.parse_args(argv)
        main(args)
    elif '--help' in sys.argv or '-h' in sys.argv:
        parser.print_help()
    else:
        print('This script is intended to be called from Blender, for example:')
        print('blender --background --python render_images.py -- [args]')
        print()
        print('Or view all arguments by:')
        print('python render_images.py --help')
