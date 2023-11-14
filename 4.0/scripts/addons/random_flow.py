# ##### BEGIN LICENSE BLOCK #####
#
# Royalty Free License
#
# The Royalty Free license grants you, the purchaser, the ability to make use of the purchased
# product for personal, educational, or commercial purposes as long as those purposes do not
# violate any of the following:
#
#   You may not resell, redistribute, or repackage the purchased product without explicit
#   permission from the original author
#
#   You may not use the purchased product in a logo, watermark, or trademark of any kind
#
#   Exception: shader, material, and texture products are exempt from this rule. These products
#   are much the same as colors, and such are a secondary meaning and may be used as part of a
#   logo, watermark, or trademark.
#
# ##### END LICENSE BLOCK #####

bl_info = {
	'name': 'Random Flow',
	'author': 'Ian Lloyd Dela Cruz',
	'version': (1, 0, 0),
	'blender': (2, 93, 0),
	'location': '3d View > Tool shelf',
	'description': 'Collection of random greebling functionalities',
	'warning': '',
	'wiki_url': '',
	'tracker_url': '',
	'category': 'Mesh'}

import bpy
import bgl
import blf
import gpu
from gpu_extras.batch import batch_for_shader
import numpy as np
from random import random, sample, uniform, choice, choices, seed, shuffle, triangular
from collections import Counter
import bmesh
import math
from math import *
import mathutils
from mathutils import *
from mathutils.geometry import intersect_line_plane
from mathutils.bvhtree import BVHTree
from itertools import chain
from bpy.props import *
from bpy_extras import view3d_utils
import rna_keymap_ui
from bpy.types import (
		AddonPreferences,
		PropertyGroup,
		Operator,
		Menu,
		Panel,
		)

def auto_smooth(obj, deg=radians(30), set=True):

	obj.data.use_auto_smooth = set
	obj.data.auto_smooth_angle = deg

	mesh = obj.data
	if mesh.is_editmode:
		bm = bmesh.from_edit_mesh(mesh)
	else:
		bm = bmesh.new()
		bm.from_mesh(mesh)

	for f in bm.faces:
		f.smooth = set

	if mesh.is_editmode:
		bmesh.update_edit_mesh(mesh)
	else:
		bm.to_mesh(mesh)
		mesh.update()

def get_evaluated_mesh(context, obj):

	dg = context.evaluated_depsgraph_get()
	obj_eval = obj.evaluated_get(dg)
	mesh_from_eval = obj_eval.to_mesh()

	return mesh_from_eval

def clear_customdata(obj):

	mesh = obj.data

	if mesh.edges:
		bvl_wght = sum(e.bevel_weight for e in mesh.edges)/len(mesh.edges)
		if bvl_wght == 0: mesh.use_customdata_edge_bevel = False

def assign_mat(self, source, target, mat_index):

	idx = mat_index
	mats = source.data.materials
	if mats:
		if idx > -1:
			if idx <= (len(mats) - 1):
				this_mat = source.data.materials[idx]
				target.data.materials.append(this_mat)
			else:
				self.report({'WARNING'}, "Material not found.")
		else:
			this_mat = source.active_material
			target.data.materials.append(this_mat)

def random_walk(bm, idx, size, snum, sampling='FACE', path='NONE', split=True):

	split_edg = []
	cells = []

	seed_counter = 0
	bm.faces.ensure_lookup_table()
	while idx:
		seed(snum)
		x = choice(list(idx))
		idx.remove(x)

		f = bm.faces[x]

		face_cell = [f]
		edge_cell = list(f.edges)
		walk = 0

		seed_counter += 1
		while walk < size:
			last_f = f
			sampler = seed_counter if sampling == 'FACE' else walk if sampling == 'EDGE' else 0
			seed(snum + sampler)
			if path != 'NONE':
				link_edges = {e: e.calc_length() for e in f.edges}
				edge = sample(list(link_edges.keys()), len(link_edges.keys()))
				edge_length = list(link_edges.values())
			else:
				edge = sample(list(f.edges), len(f.edges))
				edge_length = [0]
			for e in edge:
				length = max(edge_length) if path == 'LONGEST' \
					else min(edge_length) if path == 'SHORTEST' else 0
				if e.calc_length() != length:
					nextf = list(filter(lambda i: i.index in idx, e.link_faces))
					if nextf:
						f = nextf[0]
						idx.remove(f.index)
						face_cell.append(f)
						edge_cell.extend(list(f.edges))
						walk += 1
						break
			else:
				if last_f == face_cell[-1]:
					f = choice(face_cell)
					check = all(e in edge_cell for e in f.edges)
					if check: break

		cells.append(face_cell)

		if split:
			for e in edge_cell:
				check = all(f in face_cell for f in e.link_faces)
				if not check and \
					not e in split_edg: split_edg.append(e)

	return split_edg, cells

def clip_center(bm, obj, dist=0.001):

	mirror = obj.modifiers.get("Mirror")
	if mirror:
		dir = ["x","y","z"]
		for v in bm.verts:
			for i, n in enumerate(dir):
				if mirror.use_axis[i]:
					if -dist <= v.co[i] <= dist: setattr(v.co, n, 0)

def get_axis_faces(bm, obj, dist=1e-4):

	mirror = obj.modifiers.get("Mirror")
	faces = set()
	if mirror:
		dir = ["x","y","z"]
		for f in bm.faces:
			for i, n in enumerate(dir):
				if mirror.use_axis[i]:
					if -dist <= f.calc_center_median()[i] <= dist: faces.add(f)

	return list(faces)

def remove_axis_faces(bm, obj):

	axisf = get_axis_faces(bm, obj)
	bmesh.ops.delete(bm, geom=axisf, context='FACES')

def get_singles(verts):

	singles = []
	for v in verts:
		if len(v.link_edges) == 2:
			if v.is_boundary:
				direction = [(e.verts[1].co - e.verts[0].co) for e in v.link_edges]
				v1 = direction[0]
				v2 = direction[1]
				a1 = v1.angle(v2)
				if a1 > pi * 0.5:
					a1 = pi - a1
				if degrees(a1) == 0: singles.append(v)
			else:
				singles.append(v)

	return singles

def copy_modifiers(objs, mod_types=[]):

	sce = bpy.context.scene
	rf_props = sce.rflow_props

	orig_obj = objs[0]
	selected_objects = [o for o in objs if o != orig_obj]

	if rf_props.all_mods: mod_types.clear()

	def copy_mod_settings(obj, mSrc):

		mDst = obj.modifiers.get(mSrc.name, None) or \
			obj.modifiers.new(mSrc.name, mSrc.type)

		properties = [p.identifier for p in mSrc.bl_rna.properties
					  if not p.is_readonly]

		for prop in properties:
			setattr(mDst, prop, getattr(mSrc, prop))

	for obj in selected_objects:
		for mSrc in orig_obj.modifiers:
			if not mod_types:
				try:
					copy_mod_settings(obj, mSrc)
				except: pass
			else:
				if mSrc.type in mod_types:
					copy_mod_settings(obj, mSrc)

def remove_obj(obj):

	sce = bpy.context.scene

	in_master = True
	for c in bpy.data.collections:
		if obj.name in c.objects:
			c.objects.unlink(obj)
			in_master = False
			break

	if in_master:
		if obj.name in sce.collection.objects:
			sce.collection.objects.unlink(obj)

	bpy.data.objects.remove(obj)

def move_center_origin(origin, obj):

	pivot = obj.matrix_world.inverted() @ origin
	obj.data.transform(Matrix.Translation(-pivot))
	obj.matrix_world.translation = origin

def select_isolate(context, obj, obj_list):

	for o in obj_list:
		if o != obj:
			o.select_set(False)
		else:
			o.select_set(True)
			context.view_layer.objects.active = o

class MESH_OT_r_extrude(Operator):
	'''Randomly select faces and extrude them'''
	bl_idname = 'rand_extrude.rflow'
	bl_label = 'Random Extrude'
	bl_options = {'REGISTER', 'UNDO'}

	loop_objs : EnumProperty(
		name = "Loop Objects",
		items = (
			('1', '1','Add loop object 1'),
			('2', '2','Add loop object 2'),
			('3', '3','Add loop object 3'),
			('4', '4','Add loop object 4'),
			('5', '5','Add loop object 5'),
			('6', '6','Add loop object 6')),
		options = {"ENUM_FLAG"})
	lratio : FloatVectorProperty(
		name        = "Loop Ratio",
		description = "Number of randomized faces per loop",
		default     = (0.5,0.5,0.5,0.5,0.5,0.5),
		size        = 6,
		min         = 0.0,
		max         = 1.0,
		step        = 1
		)
	lratio_seed : IntVectorProperty(
		name        = "Seed per loop ratio",
		description = "Randomize loop ration seed",
		default     = (1,1,1,1,1,1),
		size        = 6,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	init_size : FloatProperty(
		name        = "Panel Size",
		description = "Randomized panel size",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 5,
		subtype     = "PERCENTAGE"
		)
	min_depth : FloatProperty(
		name        = "Minimum Depth",
		description = "Minimum inset depth",
		default     = 1e-2,
		min         = 0.0,
		max         = 1.0,
		step        = 1.0,
		precision   = 4
		)
	ldepth : FloatVectorProperty(
		name        = "Loop Depth",
		description = "Inset depth per loop",
		default     = (0.05,0.05,0.05,0.05,0.05,0.05),
		size        = 6,
		min         = 0.0,
		max         = 1.0,
		step        = 1.0,
		precision   = 2
		)
	ldepth_seed : IntVectorProperty(
		name        = "Loop Depth Seed",
		description = "Inset seed per loop",
		default     = (1,1,1,1,1,1),
		size        = 6,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	cuts : IntProperty(
		name        = "Subdivide",
		description = "Number of subdivision cuts",
		default     = 0,
		min         = 0,
		max         = 6,
		step        = 1
		)
	rand_seed : IntProperty(
		name        = "Randomize",
		description = "Randomize result",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	cuts_base : IntProperty(
		name        = "Subdivide Base",
		description = "Number of subdivision cuts for base object",
		default     = 0,
		min         = 0,
		max         = 6,
		step        = 1
		)
	cut_threshold : FloatProperty(
		name        = "Cut Off",
		description = "Cut edge at angle threshold",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	only_quads : BoolProperty(
		name        = "Quads Only",
		description = "Randomize only quad faces",
		default     = False
		)
	cut_grid : BoolProperty(
		name        = "Subdivide Faces",
		description = "Use grid fill subdivision",
		default     = False
		)
	subd_once : BoolProperty(
		name        = "Original Only",
		description = "Use subdivision on original object only",
		default     = False
		)
	cut_on_loops : BoolProperty(
		name        = "Exponential Subdivision",
		description = "Use same subdivision cuts per loop",
		default     = False
		)
	split_edg : BoolProperty(
		name        = "Face Islands",
		description = "Split edges of randomized faces",
		default     = True
		)
	inset_indv : BoolProperty(
		name        = "Inset Individual",
		description = "Inset individual faces",
		default     = False
		)
	use_clip : BoolProperty(
		name        = "Clip Center",
		description = "Clip center verts when using mirror modifier",
		default     = False
		)
	clip_dist : FloatProperty(
		name        = "Clip Distance",
		description = "Distance within which center vertices are clipped",
		default     = 0.001,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	use_dissolve : BoolProperty(
		name        = "Dissolve Edges",
		description = "Use limited dissolve to remove subdivision from loop object (Slower)",
		default     = True
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.mode == "OBJECT"

	def execute(self, context):
		obj = context.active_object
		orig_mesh = obj.data
		cont_mesh = obj.data

		loop_objs = set()
		loop_count = [int(i) for i in self.loop_objs] \
			if self.loop_objs else [0]

		for i in range(0, max(loop_count)):
			bm = bmesh.new()
			temp_mesh = bpy.data.meshes.new(".temp")
			bm.from_mesh(cont_mesh if not self.subd_once else orig_mesh)

			if i == 0 or \
				self.subd_once:
				bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
				bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=self.cuts_base, use_grid_fill=True)

			if self.only_quads:
				non_quads = list(filter(lambda f: len(f.verts) != 4, bm.faces))
				bmesh.ops.delete(bm, geom=non_quads, context='FACES')

			remove_axis_faces(bm, obj)
			if not self.cut_on_loops:
				subdv_cuts = self.cuts if i == 0 else 1
			else: subdv_cuts = self.cuts
			bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=subdv_cuts, use_grid_fill=self.cut_grid)

			if i == 0:
				idx = set([f.index for f in bm.faces])
				size = int(len(idx) * (self.init_size/100))
				_, cells = random_walk(bm, idx, size, self.lratio[i], sampling='FACE', split=False)

				ratio = self.lratio[i]
				seed(self.lratio_seed[i])
				remf = list(sample(list(cells), int(len(cells) * (1.0 - ratio))))
				remf = sum(remf, [])
			else:
				ratio = self.lratio[i]
				seed(self.lratio_seed[i])
				remf = list(sample(list(bm.faces), int(len(bm.faces) * (1.0 - ratio))))

			bmesh.ops.delete(bm, geom=remf, context='FACES')

			seed(self.ldepth_seed[i])
			if self.inset_indv:
				if self.split_edg: bmesh.ops.split_edges(bm, edges=bm.edges)
				bmesh.ops.inset_individual(bm, faces=bm.faces, use_even_offset=True, \
					depth=uniform(self.min_depth, self.ldepth[i]))
			else:
				if self.split_edg:
					list_e = [e for e in bm.edges if e.is_boundary or \
						(e.calc_face_angle(None) and e.calc_face_angle(None) >= self.cut_threshold)]
					bmesh.ops.split_edges(bm, edges=list_e)
				bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
					depth=uniform(self.min_depth, self.ldepth[i]))

			if self.use_clip:
				clip_center(bm, obj, self.clip_dist)
				remove_axis_faces(bm, obj)

			bm.to_mesh(temp_mesh)
			bm.free()

			cont_mesh = temp_mesh

			if str(i+1) in self.loop_objs:
				new_obj = bpy.data.objects.new(obj.name + "_RExtr", temp_mesh)
				orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
				new_obj.scale = orig_scale
				new_obj.rotation_euler = orig_rot.to_euler()
				new_obj.location = orig_loc
				new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
				new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

				assign_mat(self, obj, new_obj, self.mat_index)
				copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

				context.scene.collection.objects.link(new_obj)
				loop_objs.add(new_obj)

		if self.use_dissolve:
			for o in loop_objs:
				mesh = o.data
				bm = bmesh.new()
				bm.from_mesh(mesh)

				bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
					use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

				bm.to_mesh(mesh)
				bm.free()

		if not context.scene.rflow_props.select_active:
			if loop_objs:
				objs = [obj] + list(loop_objs)
				select_isolate(context, objs[-1], objs)

		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text="Loops | Ratio | Seed" + (" " * 3) + "(shift+click to add multiple or remove)")
		col.row(align=True).prop(self, "loop_objs", expand=True)
		col.row(align=True).prop(self, "lratio", text="")
		col.row(align=True).prop(self, "lratio_seed", text="")
		col.label(text="Loops Inset Depth | Seed")
		col.row(align=True).prop(self, "ldepth", text="")
		col.row(align=True).prop(self, "ldepth_seed", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Panel Size:")
		row.row(align=True).prop(self, "init_size", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Min Depth:")
		row.row(align=True).prop(self, "min_depth", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivide Loop:")
		row.row(align=True).prop(self, "cuts", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivide Base:")
		row.row(align=True).prop(self, "cuts_base", text="")
		col.separator(factor=0.5)
		if not self.inset_indv:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Cut Off:")
			row.row(align=True).prop(self, "cut_threshold", text="")
			col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "cut_on_loops")
		flow.prop(self, "only_quads")
		flow.prop(self, "cut_grid")
		flow.prop(self, "subd_once")
		flow.prop(self, "inset_indv")
		flow.prop(self, "split_edg")
		col.prop(self, "use_clip")
		if self.use_clip:
			col.prop(self, "clip_dist")
		col.prop(self, "use_dissolve")
		if self.use_dissolve:
			col.prop(self, "angle")

	def invoke(self, context, event):
		obj = context.active_object
		self.lratio_seed = (1,1,1,1,1,1)
		self.ldepth_seed = (1,1,1,1,1,1)
		self.cut_grid = False
		self.mat_index = -1
		self.loop_objs = set()

		obj.update_from_editmode()
		has_face = [f for f in obj.data.polygons if f.select]

		if has_face:
			return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class MESH_OT_r_panels(Operator):
	'''Create paneling details'''
	bl_idname = 'rand_panels.rflow'
	bl_label = 'Random Panels'
	bl_options = {'REGISTER', 'UNDO'}

	solver : EnumProperty(
		name = 'Solver',
		items = (
			('FACE', 'Face',''),
			('EDGE', 'Edge',''),
			('NONE', 'None','')),
		default = 'FACE'
		)
	path : EnumProperty(
		name = 'Path',
		items = (
			('NONE', 'None',''),
			('SHORTEST', 'Shortest',''),
			('LONGEST', 'Longest','')),
		default = 'NONE'
		)
	size_mode : EnumProperty(
		name = 'Size Mode',
		items = (
			('PERCENT', 'Percent',''),
			('NUMBER', 'Number','')),
		default = 'PERCENT'
		)
	panel_size_percent : FloatProperty(
		name        = "Panel Size",
		description = "Randomized panel size",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 5,
		subtype     = "PERCENTAGE"
		)
	panel_size_number : IntProperty(
		name        = "Panel Size",
		description = "Randomized panel size",
		default     = 1,
		min         = 0,
		max         = 1000,
		step        = 1
		)
	cuts_smooth : FloatProperty(
		name        = "Smooth",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for panel object",
		default     = 0,
		min         = 0,
		max         = 12,
		step        = 1
		)
	edge_seed : IntProperty(
		name        = "Seed",
		description = "Randomize panel cuts",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	thickness : FloatProperty(
		name        = "Inset Thickness",
		default     = 0.01,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	depth : FloatProperty(
		name        = "Inset Depth",
		default     = 0.01,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	cut_threshold : FloatProperty(
		name        = "Cut Off",
		description = "Cut edge at angle threshold",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	clear_faces : EnumProperty(
		name = 'Clear Faces',
		items = (
			('NONE', 'None',''),
			('INNER', 'Inner',''),
			('OUTER', 'Outer','')),
		default = 'NONE'
		)
	cells_height_min : FloatProperty(
		name        = "Min",
		description = "Minimum randomized cell height",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	cells_height_max : FloatProperty(
		name        = "Max",
		description = "Maximum randomized cell height",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	height_seed : IntProperty(
		name        = "Height Seed",
		description = "Height randomize seed",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	use_clip : BoolProperty(
		name        = "Clip Center",
		description = "Clip center verts when using mirror modifier",
		default     = False
		)
	clip_dist : FloatProperty(
		name        = "Clip Distance",
		description = "Distance within which center vertices are clipped",
		default     = 0.001,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	use_dissolve : BoolProperty(
		name        = "Dissolve Edges",
		description = "Use limited dissolve to unify faces",
		default     = False
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.mode == "OBJECT"

	def execute(self, context):
		obj = bpy.context.active_object
		orig_mesh = obj.data

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		sharp_edg = [e for e in bm.edges if e.calc_face_angle(None) \
			and e.calc_face_angle(None) >= self.cut_threshold]
		bmesh.ops.split_edges(bm, edges=sharp_edg)

		bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=self.cuts_smooth, \
			cuts=self.cuts_base, use_grid_fill=True, use_smooth_even=True)

		idx = set([f.index for f in bm.faces])
		if self.size_mode == 'PERCENT':
			numf = len(bm.faces)
			size = int(numf * (self.panel_size_percent/100))
		else: size = self.panel_size_number

		split_edg, cells = random_walk(bm, idx, size, self.edge_seed, sampling=self.solver, path=self.path)

		bmesh.ops.split_edges(bm, edges=split_edg)
		ret = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
			thickness=self.thickness, depth=self.depth)

		if self.clear_faces != 'NONE':
			remf = list(set(bm.faces).difference(set(ret['faces']))) \
				if self.clear_faces == 'INNER' else ret['faces']
			bmesh.ops.delete(bm, geom=remf, context='FACES')

		if sum([self.cells_height_min, self.cells_height_max]) > 0 \
			and self.clear_faces != 'INNER':
			for i, c in enumerate(cells):
				seed(self.height_seed + i)
				up = uniform(self.cells_height_min, self.cells_height_max)
				fv = list(dict.fromkeys(sum((list(f.verts) for f in c), [])))
				for v in fv:
					norms  = [f.normal for f in v.link_faces if f in c]
					n = sum(norms, Vector()) / len(norms)
					v.co += up * n

		if self.use_dissolve:
			bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
				use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

		if self.use_clip:
			clip_center(bm, obj, self.clip_dist)
			remove_axis_faces(bm, obj)

		bm.to_mesh(temp_mesh)
		bm.free()

		new_obj = bpy.data.objects.new(obj.name + "_RPanel", temp_mesh)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc
		new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
		new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

		assign_mat(self, obj, new_obj, self.mat_index)
		copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

		context.scene.collection.objects.link(new_obj)

		if not context.scene.rflow_props.select_active:
			objs = [obj, new_obj]
			select_isolate(context, new_obj, objs)

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Solver:")
		row.row(align=True).prop(self, "solver", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Path:")
		row.row(align=True).prop(self, "path", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Size Mode:")
		row.row(align=True).prop(self, "size_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Panel Size:")
		if self.size_mode == 'PERCENT':
			row.row(align=True).prop(self, "panel_size_percent", text="")
		else:
			row.row(align=True).prop(self, "panel_size_number", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Panel Seed:")
		row.row(align=True).prop(self, "edge_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Thickness:")
		row.row(align=True).prop(self, "thickness", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Depth:")
		row.row(align=True).prop(self, "depth", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Off:")
		row.row(align=True).prop(self, "cut_threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Clear Faces:")
		row.row(align=True).prop(self, "clear_faces", expand=True)
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Height:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cells_height_min")
		split.row(align=True).prop(self, "cells_height_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Height Seed:")
		row.row(align=True).prop(self, "height_seed", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		col.prop(self, "use_clip")
		if self.use_clip:
			col.prop(self, "clip_dist")
		col.prop(self, "use_dissolve")
		if self.use_dissolve:
			col.prop(self, "angle")

	def invoke(self, context, event):
		obj = context.active_object
		self.cuts_base = 0
		self.edge_seed = 1
		self.cells_height_max = 0.0
		self.cells_height_min = 0.0
		self.height_seed = 1
		self.mat_index = -1

		obj.update_from_editmode()
		has_face = [f for f in obj.data.polygons if f.select]

		if has_face:
			return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class MESH_OT_r_scatter(Operator):
	'''Create scatter details'''
	bl_idname = 'rand_scatter.rflow'
	bl_label = 'Random Scatter'
	bl_options = {'REGISTER', 'UNDO'}

	scatter_type : EnumProperty(
		name = 'Type',
		description = "Scatter type",
		items = (
			('CUBE', 'Cube',''),
			('MESH', 'Mesh',''),
			('COLLECTION', 'Collection','')),
		default = 'CUBE'
		)
	list : StringProperty(
		name        = "Mesh",
		description = "Mesh object for scatter"
		)
	list_col : StringProperty(
		name        = "Collections",
		description = "Collection objects for scatter"
		)
	meshes : CollectionProperty(type=PropertyGroup)
	collections : CollectionProperty(type=PropertyGroup)
	coll_seed : IntProperty(
		name        = "Object Seed",
		description = "Randomize seed for collection objects",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	scatter_seed : IntProperty(
		name        = "Scatter Seed",
		description = "Randomize scatter points",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	scatter_points : IntProperty(
		name        = "Scatter Points",
		description = "Number of scatter points",
		default     = 10,
		min         = 1,
		max         = 1000,
		step        = 1
		)
	size_seed : IntProperty(
		name        = "Size Seed",
		description = "Randomize size of scatter object",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	size_min : FloatProperty(
		name        = "Min",
		description = "Minimum scatter size",
		default     = 0.1,
		min         = 0.0,
		step        = 0.1,
		precision   = 2
		)
	size_max : FloatProperty(
		name        = "Max",
		description = "Maximum scatter size",
		default     = 1.0,
		min         = 0.0,
		step        = 0.1,
		precision   = 2
		)
	scale_seed : IntVectorProperty(
		name        = "Scatter Seed",
		description = "Scatter object scaling seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		max			= 10000,
		step        = 1
		)
	scale : FloatVectorProperty(
		name        = "Scale",
		default     = (1.0,1.0,1.0),
		size        = 3,
		min         = 0.01,
		step        = 1.0,
		description = "Randomized faces scale"
		)
	rot_axis : FloatVectorProperty(
		name        = "Rotation",
		description = "Rotate axis",
		default     = (0,0,0),
		size        = 3,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "EULER"
		)
	rot_seed : IntVectorProperty(
		name        = "Rotation Seed",
		description = "Scatter object rotation seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		max			= 10000,
		step        = 1
		)
	explode_min : FloatProperty(
		name        = "Min",
		description = "Minimum explode offset",
		default     = 0.0,
		min         = 0.0,
		max         = 2.0,
		step        = 0.1,
		precision   = 3
		)
	explode_max : FloatProperty(
		name        = "Max",
		description = "Maximum explode offset",
		default     = 0.0,
		min         = 0.0,
		max         = 2.0,
		step        = 0.1,
		precision   = 3
		)
	explode_seed : IntProperty(
		name        = "Explode Seed",
		description = "Randomize explode offset of scatter object",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	margin : FloatProperty(
		name        = "Scatter margin relative to face",
		description = "Margin",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.mode == "OBJECT"

	def point_on_triangle(self, face):
		'''https://blender.stackexchange.com/a/221597'''

		a, b, c = map(lambda v: v.co, face.verts)
		a2b = b - a
		a2c = c - a
		height = triangular(low=0.0, high=1.0, mode=0.0)

		return a + a2c*height + a2b*(1-height) * random(), face.normal, face.calc_center_median()

	def execute(self, context):
		obj = bpy.context.active_object
		orig_mesh = obj.data

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)
		bm.to_mesh(temp_mesh)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')

		triangles = bmesh.ops.triangulate(bm, faces=bm.faces)['faces']
		surfaces = map(lambda t: t.calc_area(), triangles)
		seed(self.scatter_seed)
		listp = choices(population=triangles, weights=surfaces, k=self.scatter_points)
		points = map(self.point_on_triangle, listp)

		def get_rot(track, obj):

			quat = normal.to_track_quat(track, 'Y')
			mat = obj.matrix_world @ quat.to_matrix().to_4x4()
			rot = mat.to_3x3().normalized()

			return rot

		cont = True
		scatter_obj = None
		scatter_type = self.scatter_type

		for i, p in enumerate(list(points)):
			bm_scatter = bmesh.new()
			scatter_data = bpy.data.meshes.new(".temp_scatter")

			loc = p[0]
			normal = p[1]
			center = p[2]

			if scatter_type == 'CUBE':
				seed(self.size_seed + i)
				scatter_verts = bmesh.ops.create_cube(bm_scatter, size=uniform(self.size_min, self.size_max))['verts']
				rot = get_rot('-Z', obj)
			else:
				if scatter_type == 'MESH':
					scatter_obj = bpy.data.objects.get(self.list)
				elif scatter_type == 'COLLECTION':
					collection = bpy.data.collections.get(self.list_col)
					if collection:
						mesh_objs = [o for o in bpy.data.collections.get(self.list_col).all_objects \
							if o.type == 'MESH' and o != obj]
						if mesh_objs:
							seed(self.coll_seed + i)
							coll_obj = choice(mesh_objs)
							scatter_obj = bpy.data.objects.get(coll_obj.name)

				if scatter_obj:
					bm_scatter.from_mesh(scatter_obj.data)
					scatter_verts = bm_scatter.verts
					rot = get_rot('Z', scatter_obj)
				else: cont = False

			if cont:
				loc += ((center-loc) * self.margin)
				if sum([self.explode_min, self.explode_max]) > 0:
					seed(self.explode_seed + i)
					loc += normal * uniform(self.explode_min, self.explode_max)

				bmesh.ops.translate(
					bm_scatter,
					verts   = scatter_verts,
					vec     = loc
					)

				if scatter_type != 'CUBE':
					seed(self.size_seed + i)
					sz = uniform(self.size_min, self.size_max)
					bmesh.ops.scale(
						bm_scatter,
						vec     = Vector((sz, sz, sz)),
						space   = Matrix.Translation(loc).inverted(),
						verts   = scatter_verts
						)

				def sca_seed(x, y, z):

					scale = [x, y, z]
					for n, v in enumerate(scale):
						seed(self.scale_seed[n] + i)
						scale[n] = uniform(self.size_min, v)
						seed(0)

					return scale

				x, y, z = self.scale
				scale = sca_seed(x, y, z)
				bmesh.ops.scale(
					bm_scatter,
					vec     = Vector(scale),
					space   = Matrix.Translation(loc).inverted(),
					verts   = scatter_verts
					)

				def rot_seed(x, y, z):

					axis = [x, y, z]
					for n, v in enumerate(axis):
						if self.rot_seed[n] > 1:
							seed(self.rot_seed[n] + i)
							axis[n] = uniform(-v, v)
						else: axis[n] = v
						seed(0)

					return Euler(Vector(axis))

				x, y, z = self.rot_axis
				rot_axis = rot_seed(x, y, z)
				_, orig_rot, _ = obj.matrix_world.decompose()
				bmesh.ops.rotate(
					bm_scatter,
					verts   = scatter_verts,
					cent    = loc,
					matrix  = orig_rot.to_matrix().inverted() @ rot @ rot_axis.to_matrix()
					)

			bm_scatter.to_mesh(scatter_data)
			bm_scatter.free()

			bm.from_mesh(scatter_data)
			bpy.data.meshes.remove(scatter_data)

		bmesh.ops.delete(bm, geom=triangles, context='FACES')

		bm.to_mesh(temp_mesh)
		bm.free()

		if temp_mesh.polygons:
			new_obj = bpy.data.objects.new(obj.name + "_RScatter", temp_mesh)
			orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
			new_obj.scale = orig_scale
			new_obj.rotation_euler = orig_rot.to_euler()
			new_obj.location = orig_loc
			new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
			new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

			assign_mat(self, obj, new_obj, self.mat_index)
			copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

			context.scene.collection.objects.link(new_obj)

			if not context.scene.rflow_props.select_active:
				objs = [obj, new_obj]
				select_isolate(context, new_obj, objs)

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Type:")
		row.row(align=True).prop(self, "scatter_type", expand=True)
		if self.scatter_type == 'MESH':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mesh:")
			row.prop_search(
				self,
				"list",
				self,
				"meshes",
				text="",
				icon = "MESH_DATA"
				)
		if self.scatter_type == 'COLLECTION':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Collection:")
			row.prop_search(
				self,
				"list_col",
				self,
				"collections",
				text="",
				icon = "OUTLINER_COLLECTION"
				)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Object Seed:")
			row.row(align=True).prop(self, "coll_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Points:")
		row.row(align=True).prop(self, "scatter_points", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Point Seed:")
		row.row(align=True).prop(self, "scatter_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Scatter Size:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "size_min")
		split.row(align=True).prop(self, "size_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Size Seed:")
		row.row(align=True).prop(self, "size_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Scatter Scale:")
		row.row(align=True).prop(self, "scale", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Scale Seed:")
		row.row(align=True).prop(self, "scale_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation:")
		row.row(align=True).prop(self, "rot_axis", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation Seed:")
		row.row(align=True).prop(self, "rot_seed", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Explode:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "explode_min")
		split.row(align=True).prop(self, "explode_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Explode Seed:")
		row.row(align=True).prop(self, "explode_seed", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")

	def invoke(self, context, event):
		sce = context.scene
		obj = context.active_object
		self.coll_seed = 1
		self.scatter_seed = 1
		self.size_seed = 1
		self.scale_seed = (1,1,1)
		self.rot_axis = (0,0,0)
		self.rot_seed = (1,1,1)
		self.mat_index = -1

		self.list = ""
		self.meshes.clear()
		self.list_col = ""
		self.collections.clear()

		obj.update_from_editmode()
		has_face = [f for f in obj.data.polygons if f.select]

		if has_face:
			for o in sce.objects:
				if o.type == 'MESH' and \
					o != obj:
					newListItem = self.meshes.add()
					newListItem.name = o.name

			for c in bpy.data.collections:
				newListItem = self.collections.add()
				newListItem.name = c.name

			return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class MESH_OT_r_tubes(Operator):
	'''Create random tubes'''
	bl_idname = 'rand_tubes.rflow'
	bl_label = 'Random Tubes'
	bl_options = {'REGISTER', 'UNDO'}

	solver : EnumProperty(
		name = 'Solver',
		items = (
			('NONE', 'None',''),
			('SHORTEST', 'Shortest',''),
			('LONGEST', 'Longest','')),
		default = 'NONE'
		)
	panel_num : IntProperty(
		name        = "Number",
		description = "Panel amount",
		default     = 5,
		min         = 1,
		step        = 1
		)
	edg_length : IntProperty(
		name        = "Length",
		description = "Randomized Edge Length",
		default     = 5,
		min         = 1,
		step        = 1
		)
	edg_seed : IntProperty(
		name        = "Seed",
		description = "Random edge walk seed",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	edg_offset_min : FloatProperty(
		name        = "Min",
		description = "Minimum edge offset",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	edg_offset_max : FloatProperty(
		name        = "Max",
		description = "Maximum edge offset",
		default     = 0.1,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	offset_seed : IntProperty(
		name        = "Offset Seed",
		description = "Random offset seed",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	margin : FloatProperty(
		name        = "Margin",
		description = "Margin from boundary edges",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	width : FloatProperty(
		name        = "Depth",
		description = "Depth of curve object",
		default     = 0.05,
		min         = 0,
		max         = 100,
		step        = 0.1,
		precision   = 4
	)
	resnum : IntProperty(
		name        = "Resolution",
		description = "Bevel resolution of curve object",
		default     = 6,
		min         = 1,
		max         = 100,
		step        = 1
	)
	bvl_offset : FloatProperty(
		name        = "Width",
		description = "Bevel width",
		default     = 0.0,
		min         = 0.0,
		max         = 100,
		step        = 0.1,
		precision   = 4
	)
	bvl_seg : IntProperty(
		name        = "Segments",
		description = "Bevel segments",
		default     = 2,
		min         = 1,
		max         = 100,
		step        = 1
	)
	bevel_angle : FloatProperty(
		name        = "Angle Limit",
		description = "Maximum angle threshold for curve points to get beveled",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for panel object",
		default     = 0,
		min         = 0,
		max         = 12,
		step        = 1
		)
	cuts_smooth : FloatProperty(
		name        = "Smooth",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	smooth_shade : BoolProperty(
		name        = "Shade Smooth",
		description = "Smooth shade curve object",
		default     = True
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.mode == "OBJECT"

	def curve_convert(self, obj, width, resnum, smooth=True):

		bpy.ops.object.convert(target='CURVE')

		obj.data.fill_mode = 'FULL'
		obj.data.bevel_depth = width
		obj.data.bevel_resolution = resnum

		for spline in obj.data.splines:
			spline.use_smooth = smooth

	def execute(self, context):
		obj = bpy.context.active_object
		orig_mesh = obj.data

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		face_sel = [f for f in bm.faces if not f.select]
		bmesh.ops.delete(bm, geom=face_sel, context='FACES')

		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		if self.margin > 0:
			margin = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
				thickness=self.margin, depth=0.0)['faces']
			bmesh.ops.delete(bm, geom=margin, context='FACES')

		bm.to_mesh(temp_mesh)
		bm.free()

		bm = bmesh.new()
		bm.from_mesh(temp_mesh)

		bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=self.cuts_smooth, \
			cuts=self.cuts_base, use_grid_fill=True, use_smooth_even=True)

		oldv = list(bm.verts)
		idx = set([e.index for e in bm.edges])
		cells = []

		size = self.edg_length

		pnum = 0
		while idx and pnum < self.panel_num:
			seed(self.edg_seed)
			x = choice(list(idx))
			idx.remove(x)

			bm.edges.ensure_lookup_table()
			edg = bm.edges[x]
			cell = [x]
			walk = 0

			while walk < size:
				last_e = edg
				loops = sample(list(edg.link_loops), len(edg.link_loops))
				for loop in loops:
					link_edges = {e.index: e.calc_length() for e in loop.vert.link_edges}
					if len(set(list(link_edges.keys())).intersection(set(cell))) < 2:
						for e in loop.vert.link_edges:
							edge_length = list(link_edges.values())
							length_solver = min(edge_length) if self.solver == 'LONGEST' \
								else max(edge_length) if self.solver == 'SHORTEST' else 0.0
							if e.index in idx and \
								e.calc_length() != length_solver:
								v = last_e.other_vert(loop.vert)
								for link_e in v.link_edges:
									if link_e.index in idx: idx.remove(link_e.index)
								edg = bm.edges[e.index]
								idx.remove(e.index)
								cell.append(e.index)
								walk += 1
								break

				if last_e.index == cell[-1]:
					break
				walk += 1

			if cell:
				for v in bm.edges[cell[-1]].verts:
					if len([e for e in v.link_edges if e.index in cell]) < 2:
						for e in v.link_edges:
							if e.index in idx: idx.remove(e.index)

				cells.append(cell)
				pnum += 1

		for i, edges in enumerate(cells):
			edg = [e for e in bm.edges if e.index in edges]
			ret = bmesh.ops.duplicate(bm, geom=edg)['vert_map']
			newv = [v for v in ret if not v in oldv]
			ends = list(filter(lambda v: len(v.link_edges) < 2, newv))
			bmesh.ops.extrude_vert_indiv(bm, verts=ends)
			for v1 in newv:
				source_v = list(filter(lambda v: v.co == v1.co, oldv))
				if source_v:
					v0 = source_v[0]
					seed(self.offset_seed + i)
					v1.co += (v0.normal * (v0.calc_shell_factor() \
						* uniform(self.edg_offset_min, self.edg_offset_max)))
					seed(0)

		bmesh.ops.delete(bm, geom=oldv, context='VERTS')

		if self.bvl_offset > 0:
			sharp_verts = []
			for v in bm.verts:
				angle = v.calc_edge_angle(None)
				if angle and \
					angle >= self.bevel_angle:
					sharp_verts.append(v)

			bmesh.ops.bevel(
				bm,
				geom            = sharp_verts,
				offset          = self.bvl_offset,
				offset_type     = 'OFFSET',
				segments        = self.bvl_seg,
				profile         = 0.5,
				affect          = 'VERTICES',
				)

		bm.to_mesh(temp_mesh)
		bm.free()

		if temp_mesh.vertices:
			new_obj = bpy.data.objects.new(obj.name + "_RPipes", temp_mesh)
			orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
			new_obj.scale = orig_scale
			new_obj.rotation_euler = orig_rot.to_euler()
			new_obj.location = orig_loc
			new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
			new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

			context.scene.collection.objects.link(new_obj)

			new_obj.select_set(True)
			select_isolate(context, new_obj, [obj, new_obj])
			self.curve_convert(new_obj, self.width, self.resnum, self.smooth_shade)
			copy_modifiers([obj, new_obj], mod_types=['MIRROR'])
			assign_mat(self, obj, new_obj, self.mat_index)

			if context.scene.rflow_props.select_active:
				objs = [obj, new_obj]
				select_isolate(context, obj, objs)
		else:
			bpy.data.meshes.remove(temp_mesh)

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Solver:")
		row.row(align=True).prop(self, "solver", expand = True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Amount:")
		row.row(align=True).prop(self, "panel_num", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Length:")
		row.row(align=True).prop(self, "edg_length", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Seed:")
		row.row(align=True).prop(self, "edg_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "edg_offset_min")
		split.row(align=True).prop(self, "edg_offset_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset Seed:")
		row.row(align=True).prop(self, "offset_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Curve:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "width")
		split.row(align=True).prop(self, "resnum")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bevel:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "bvl_offset")
		split.row(align=True).prop(self, "bvl_seg")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Angle Limit:")
		row.row(align=True).prop(self, "bevel_angle", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		col.prop(self, "smooth_shade")

	def invoke(self, context, event):
		obj = context.active_object
		self.edg_seed = 1
		self.offset_seed = 1
		self.cuts_base = 0
		self.mat_index = -1

		obj.update_from_editmode()
		has_face = [f for f in obj.data.polygons if f.select]

		if has_face:
			return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class MESH_OT_quad_slice(Operator):
	'''Draw lines from vertices or edges using view or tangent as direction'''
	bl_idname = 'quad_slice.rflow'
	bl_label = 'Quad Slice'
	bl_options = {'REGISTER', 'UNDO'}

	direction : EnumProperty(
		name = "Direction",
		items = (
			('VIEW', 'View','Use view angle as direction'),
			('TANGENT', 'Tangent','Use tangents from selected as direction')),
		default = 'VIEW')
	tangent_idx : IntProperty(
		name        = "Tangent",
		description = "Tangent index",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	origin : EnumProperty(
		name = "Origin",
		items = (
			('VERT', 'Verts','Source cut lines from selected verts'),
			('EDGE', 'Edges','Source cut lines from selected edges')),
		default = 'VERT')
	use_geo_v : EnumProperty(
		name = "Geometry",
		items = (
			('SHARED', 'Shared Face','Limit cut to shared face'),
			('ALL', 'All Faces','Cut all faces')),
		default = 'SHARED')
	face_idx : IntProperty(
		name        = "Face",
		description = "Shared face to cut",
		default     = 1,
		min         = 1,
		max         = 10000,
		step        = 1
		)
	use_geo_f : EnumProperty(
		name = "Geometry",
		items = (
			('SELECT', 'Selected','Limit cut to selected faces'),
			('ALL', 'All Faces','Cut all faces')),
		default = 'SELECT')
	limit : EnumProperty(
		name = "Limit",
		items = (
			('NONE', 'None','Limit cut to none'),
			('LINE1', 'X','Limit to cut direction X'),
			('LINE2', 'Y','Limit to cut direction Y')),
		default = 'NONE')
	slide_factor : FloatProperty(
		name        = "Factor",
		description = "Split location on selected edge",
		default     = 0.5,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
	)
	cut_rot : FloatProperty(
		name        = "Rotation",
		description = "Rotate to X axis",
		default     = 0,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	remove_singles : BoolProperty(
		name        = "Remove Singles",
		description = "Remove verts with only two connecting edges",
		default     = False
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.mode == "EDIT"

	def execute(self, context):
		obj = context.active_object
		mesh = obj.data

		rv3d = context.region_data
		vrot = rv3d.view_rotation

		mesh = obj.data
		bm = bmesh.from_edit_mesh(mesh)

		def get_visible_elem(bm):

			verts = [v for v in bm.verts if not v.hide]
			edges = [e for e in bm.edges if not e.hide]
			faces = [f for f in bm.faces if not f.hide]

			return verts, edges, faces

		orig_geo = []
		split_verts = []

		if self.origin == 'EDGE':
			edg = [e for e in bm.edges if e.select]
			ret = bmesh.ops.bisect_edges(bm, edges=edg, cuts=1, edge_percents={e:self.slide_factor for e in edg})
			split_verts = [v for v in ret['geom_split'] if isinstance(v, bmesh.types.BMVert)]

		e, v, f = get_visible_elem(bm)
		orig_geo = e + v + f + split_verts

		if self.has_face:
			if self.use_geo_f == 'SELECT':
				faces = [f for f in bm.faces if f.select]
				if faces:
					fv = sum([f.verts[:] for f in faces], [])
					fe = sum([f.edges[:] for f in faces], [])
					orig_geo = fv + fe + faces + split_verts
		else:
			if self.use_geo_v == 'SHARED':
				lfaces = [[i.index for i in v.link_faces] for v in bm.verts if v.select]
				shared_f = list(set(lfaces[0]).intersection(*lfaces))
				if shared_f:
					bm.faces.ensure_lookup_table()
					n = len(shared_f)
					face = bm.faces[shared_f[(n + (self.face_idx - 1)) % n]]
					orig_geo = face.verts[:] + face.edges[:] + [face] + split_verts

		xt = None; yt = None
		if self.direction == 'TANGENT':
			faces = sum([list(v.link_faces) for v in bm.verts if v.select], [])
			if faces:
				tangents = [[tuple(f.calc_tangent_edge()), tuple(f.normal)] for f in faces]
				n = len(tangents)
				t = tangents[(n + (self.tangent_idx - 1)) % n]
				xt = Vector(t[0])
				yt = xt.cross(Vector(t[1]))

		x = vrot @ Vector((0,-1,0))
		y = vrot @ Vector((-1,0,0))

		if xt and yt:
			x = xt; y = yt

		tangents = [x, y]
		tangents = tangents[:-1] if self.limit == 'LINE1' else tangents[-1:] \
			if self.limit == 'LINE2' else tangents

		origin = [v for v in bm.verts if v.select] if self.origin == 'VERT' else split_verts

		new_geo = []
		for v in origin:
			co = v.co
			normal = v.normal
			for t in tangents:
				P = x.cross(y)
				M = Matrix.Rotation(self.cut_rot, 3, P)
				t = t @ M
				geo = list(dict.fromkeys(orig_geo + new_geo))
				ret = bmesh.ops.bisect_plane(bm, geom=geo, plane_co=co, plane_no=t)

				new_geo.extend(ret['geom'] + ret['geom_cut'])
				new_geo = list(dict.fromkeys(new_geo))

		bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])

		if self.remove_singles:
			singles = get_singles(bm.verts)
			bmesh.ops.dissolve_verts(bm, verts=singles)

		bmesh.update_edit_mesh(mesh)

		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Direction:")
		row.row(align=True).prop(self, "direction", expand=True)
		if self.direction == 'TANGENT':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Tangent:")
			row.row(align=True).prop(self, "tangent_idx", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Origin:")
		row.row(align=True).prop(self, "origin", expand=True)
		if self.has_face:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Geometry:")
			row.row(align=True).prop(self, "use_geo_f", expand=True)
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Geometry:")
			row.row(align=True).prop(self, "use_geo_v", expand=True)
			if self.use_geo_v == 'SHARED':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Face:")
				row.row(align=True).prop(self, "face_idx", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Limit:")
		row.row(align=True).prop(self, "limit", expand=True)
		if self.origin == 'EDGE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Factor:")
			row.row(align=True).prop(self, "slide_factor", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation:")
		row.row(align=True).prop(self, "cut_rot", text="")
		col.separator(factor=0.5)
		col.prop(self, "remove_singles")

	def invoke(self, context, event):
		self.face_idx = 1
		self.tangent_idx = 1
		self.origin = 'VERT'
		self.use_geo_v = 'SHARED'
		self.use_geo_f = 'SELECT'
		self.cut_rot = 0
		self.slide_factor = 0.5

		obj = context.active_object
		obj.update_from_editmode()
		self.has_face = [f for f in obj.data.polygons if f.select]

		return context.window_manager.invoke_props_popup(self, event)

class MESH_OT_auto_smooth(Operator):
	'''Smooth shade active object and use auto-smooth. Ctrl+click for popup menu'''
	bl_idname = 'auto_smooth.rflow'
	bl_label = 'Auto Smooth'
	bl_options = {'REGISTER', 'UNDO'}

	deg : FloatProperty(
		name        = "Angle",
		description = "Auto smooth angle",
		default     = radians(30),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	set_auto_smooth : BoolProperty(
		name        = "Use Auto Smooth",
		description = "Toggle auto smooth on or off",
		default     = True
		)
	clear_cn : BoolProperty(
		name        = "Clear Custom Split Normals Data",
		description = "Remove the custom split normals layer, if it exists",
		default     = False
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		objs = context.selected_objects

		for o in objs:
			mesh = o.data

			auto_smooth(o, self.deg, self.set_auto_smooth)
			o.update_from_editmode()

			if self.clear_cn and mesh.has_custom_normals:
				bpy.ops.mesh.customdata_custom_splitnormals_clear()

			mesh.update()

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(self, "deg")
		col.separator()
		col.prop(self, "set_auto_smooth")
		col.prop(self, "clear_cn")

	def invoke(self, context, event):
		self.set_auto_smooth = True
		self.clear_cn = False

		if event.ctrl:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return self.execute(context)

class MESH_OT_scatter_origin(Operator):
	'''Sets origin for scatter objects'''
	bl_idname = 'set_origin.rflow'
	bl_label = 'Set Origin'
	bl_options = {'REGISTER', 'UNDO'}

	origin : EnumProperty(
		name = "Origin",
		items = (
			('AXIS', 'Axis','Use axes for new origin'),
			('SELECTED', 'Selected','Use selected verts for new origin')),
		default = 'AXIS')
	space : EnumProperty(
		name = "Space",
		items = (
			('LOCAL', 'Local','Use objects local matrix'),
			('GLOBAL', 'Global','Use global matrix')),
		default = 'LOCAL')
	axis : EnumProperty(
		name = "Origin",
		items = (
			('X', 'X',''),
			('Y', 'Y',''),
			('Z', 'Z','')),
		default = 'Z')
	location : EnumProperty(
		name = "Location",
		items = (
			('POSITIVE', 'Positive','Find outermost verts in the positive axis direction'),
			('NEGATIVE', 'Negative','Find outermost verts in the negative axis direction')),
		default = 'POSITIVE')
	tolerance : FloatProperty(
		name        = "Tolerance",
		description = "Tolerance threshold for finding verts based on location",
		default     = 1e-5,
		min         = 0.0,
		max         = 1.0,
		step        = 1.0,
		precision   = 5
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.mode == "OBJECT"

	def execute(self, context):
		objs = context.selected_objects

		for o in objs:
			mesh = o.data
			M = o.matrix_world if self.space == 'GLOBAL' else Matrix()

			bm = bmesh.new()
			bm.from_mesh(mesh)

			point = None
			if self.origin == 'AXIS':
				axis = ['X','Y','Z'].index(self.axis)
				verts = sorted(bm.verts, key=lambda v: (M @ v.co)[axis])
				pos = (M @ verts[-1 if self.location == 'POSITIVE' else 0].co)[axis]
				point = [o.matrix_world @ v.co for v in verts if abs((M @ v.co)[axis] - pos) < self.tolerance]
			else:
				point = [o.matrix_world @ v.co for v in bm.verts if v.select]
				if not point:
					self.report({'WARNING'}, "No verts selected.")

			bm.to_mesh(mesh)
			bm.free()

			if point:
				new_origin = sum(point, Vector()) / len(point)
				move_center_origin(new_origin, o)

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.2, align=True)
		row.label(text="Origin:")
		row.row(align=True).prop(self, "origin", expand=True)
		col1 = col.column()
		col1.enabled = self.origin == 'AXIS'
		row = col1.row().split(factor=0.2, align=True)
		row.label(text="Space:")
		row.row(align=True).prop(self, "space", expand=True)
		row = col1.row().split(factor=0.2, align=True)
		row.label(text="Axis:")
		row.row(align=True).prop(self, "axis", expand=True)
		row = col1.row().split(factor=0.2, align=True)
		row.label(text="Location:")
		row.row(align=True).prop(self, "location", expand=True)
		row = col1.row().split(factor=0.2, align=True)
		row.label(text="Tolerance:")
		row.row(align=True).prop(self, "tolerance", expand=True)

	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self)

class MESH_OT_clean_up(Operator):
	'''Limited dissolve, remove doubles and zero area faces from selected objects'''
	bl_idname = 'clean_up.rflow'
	bl_label = 'Clean Up'
	bl_options = {'REGISTER', 'UNDO'}

	rem_double_faces : BoolProperty(
		name        = "Remove Face Doubles",
		description = "Remove overlapping faces",
		default     = False
		)
	rem_doubles : BoolProperty(
		name        = "Remove Doubles",
		description = "Remove overlapping verts",
		default     = False
		)
	doubles_dist : FloatProperty(
		name        = "Merge Distance",
		description = "Maximum distance between elements to merge",
		default     = 0.0001,
		min         = 0.0,
		max         = 10,
		step        = 0.1,
		precision   = 4
		)
	lim_dissolve : BoolProperty(
		name        = "Limited Dissolve",
		description = "Use limited dissolve to unify faces",
		default     = False
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	use_clip : BoolProperty(
		name        = "Clip Center",
		description = "Clip center verts when using mirror modifier",
		default     = False
		)
	clip_dist : FloatProperty(
		name        = "Clip Distance",
		description = "Distance within which center vertices are clipped",
		default     = 0.001,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	deg_dissolve : BoolProperty(
		name        = "Degenerate Dissolve",
		description = "Remove zero area faces and zero length edges",
		default     = False
		)
	deg_dist : FloatProperty(
		name        = "Merge Distance",
		description = "Maximum distance between elements to merge",
		default     = 0.0001,
		min         = 0.0,
		max         = 10,
		step        = 0.1,
		precision   = 4
		)
	remove_singles : BoolProperty(
		name        = "Remove Singles",
		description = "Remove verts with only two connecting edges",
		default     = False
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.type == 'MESH'

	def clean_double_faces(self, bm):

		double_faces = []
		f_centers = [tuple(f.calc_center_median()) for f in bm.faces]
		dup_centers = [k for k, v in Counter(f_centers).items() if v > 1]
		for f in bm.faces:
			if tuple(f.calc_center_median()) in dup_centers \
				and not f in double_faces: double_faces.append(f)

		bmesh.ops.delete(bm, geom=double_faces, context='FACES')

	def execute(self, context):
		objs = context.selected_objects

		for o in objs:
			if o.type == 'MESH':
				mesh = o.data
				if mesh.is_editmode:
					bm = bmesh.from_edit_mesh(mesh)
				else:
					bm = bmesh.new()
					bm.from_mesh(mesh)

				if self.rem_double_faces:
					self.clean_double_faces(bm)

				if self.rem_doubles:
					bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=self.doubles_dist)

				if self.lim_dissolve:
					bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
						use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

				if self.use_clip:
					clip_center(bm, o, self.clip_dist)
					remove_axis_faces(bm, o)

				if self.deg_dissolve:
					bmesh.ops.dissolve_degenerate(bm, dist=self.deg_dist, edges=bm.edges)

				if self.remove_singles:
					singles = get_singles(bm.verts)
					bmesh.ops.dissolve_verts(bm, verts=singles)

				if mesh.is_editmode:
					bmesh.update_edit_mesh(mesh)
				else:
					bm.to_mesh(mesh)
					mesh.update()
					bm.free()

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		flow = col.column_flow(columns=2)
		flow.prop(self, "rem_doubles")
		flow.prop(self, "lim_dissolve")
		flow.prop(self, "use_clip")
		flow.prop(self, "deg_dissolve")
		flow.prop(self, "doubles_dist")
		flow.prop(self, "angle")
		flow.prop(self, "clip_dist")
		flow.prop(self, "deg_dist")
		col.prop(self, "rem_double_faces")
		col.prop(self, "remove_singles")

	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self)

class UI_MT_random_flow(Menu):
	bl_label = "Random FLow"
	bl_idname = "UI_MT_random_flow"

	def draw(self, context):
		obj = context.active_object
		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.operator("rand_extrude.rflow", icon="ORIENTATION_NORMAL")
		layout.operator("rand_panels.rflow", icon="MESH_GRID")
		layout.operator("rand_scatter.rflow", icon="OUTLINER_OB_POINTCLOUD")
		layout.operator("rand_tubes.rflow", icon="IPO_CONSTANT")
		layout.separator()
		if obj and obj.data.is_editmode:
			layout.operator("quad_slice.rflow", icon="GRID")
		layout.operator("auto_smooth.rflow", icon="OUTLINER_OB_MESH")
		layout.separator()
		layout.menu("UI_MT_rflow_extras")
		layout.menu("UI_MT_rflow_settings")

class UI_MT_rflow_extras(Menu):
	bl_label = "Extras"
	bl_idname = "UI_MT_rflow_extras"

	def draw(self, context):
		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.operator("set_origin.rflow", icon="OBJECT_ORIGIN")
		layout.operator("clean_up.rflow", icon="MESH_DATA")

class UI_MT_rflow_settings(Menu):
	bl_label = "Settings"
	bl_idname = "UI_MT_rflow_settings"

	def draw(self, context):
		sce = context.scene
		rf_props = sce.rflow_props

		layout = self.layout
		layout.prop(rf_props, "select_active")
		layout.prop(rf_props, "all_mods")

class UI_PT_rflow_addon_pref(AddonPreferences):
	bl_idname = __name__

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		wm = context.window_manager
		kc = wm.keyconfigs.user
		km = kc.keymaps['3D View Generic']
		kmi = get_hotkey_entry_item(km, 'wm.call_menu', 'UI_MT_random_flow')
		if kmi:
			col.context_pointer_set("keymap", km)
			rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
		else:
			col.label(text="No hotkey found!", icon="ERROR")
			col.operator("add_hotkey.rflow", text="Add hotkey")

def get_hotkey_entry_item(km, kmi_name, kmi_value):

	for i, km_item in enumerate(km.keymap_items):
		if km.keymap_items.keys()[i] == kmi_name:
			if km.keymap_items[i].properties.name == kmi_value:
				return km_item
	return None

def add_hotkey():

	addon_prefs = bpy.context.preferences.addons[__name__].preferences

	kc = bpy.context.window_manager.keyconfigs.addon
	if kc:
		km = kc.keymaps.new(name='3D View Generic', space_type='VIEW_3D', region_type='WINDOW')
		kmi = km.keymap_items.new('wm.call_menu', 'Q', 'PRESS', ctrl=False, shift=True, alt=False)
		kmi.properties.name = 'UI_MT_random_flow'
		kmi.active = True
		addon_keymaps.append((km, kmi))

def remove_hotkey():

	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)

	addon_keymaps.clear()

class USERPREF_OT_change_hotkey(Operator):
	'''Add hotkey'''
	bl_idname = "add_hotkey.rflow"
	bl_label = "Add Hotkey"
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):
		add_hotkey()
		return {'FINISHED'}

addon_keymaps = []

class RFlow_Props(PropertyGroup):

	select_active : BoolProperty(
		default     = True,
		name        = "Select Active",
		description = "Always select active or source object after operation"
		)
	all_mods : BoolProperty(
		default     = False,
		name        = "Copy All Modifiers",
		description = "Copy all modifiers from source object to random objects"
		)

classes = (
	MESH_OT_r_extrude,
	MESH_OT_r_panels,
	MESH_OT_r_scatter,
	MESH_OT_r_tubes,
	MESH_OT_quad_slice,
	MESH_OT_auto_smooth,
	MESH_OT_scatter_origin,
	MESH_OT_clean_up,
	UI_MT_random_flow,
	UI_MT_rflow_extras,
	UI_MT_rflow_settings,
	UI_PT_rflow_addon_pref,
	USERPREF_OT_change_hotkey,
	RFlow_Props,
	)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.rflow_props = PointerProperty(
		type        = RFlow_Props,
		name        = "Random Flow Properties",
		description = ""
		)

	add_hotkey()

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

	del bpy.types.Scene.rflow_props

	remove_hotkey()

if __name__ == '__main__':
	register()