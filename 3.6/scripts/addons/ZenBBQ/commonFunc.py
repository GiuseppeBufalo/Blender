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

# Copyright 2022, Dmitry Aleksandrovich Maslov (ABTOMAT)

import random
import bmesh
import bpy
import addon_utils

from . import globals as ZBBQ_Globals

from .ico import ZBBQ_Icons
from .units import ZBBQ_Units
from .colors import ZBBQ_Colors
from .consts import ZBBQ_Consts
from .vlog import Log

_CACHE_ADDON_VERSION = None


class ZBBQ_CommonFunc:

    # ==== Checking the required conditions to use Zen BBQ

    def ObjectIsConvenient(obj):
        # Checks if this object can be used with this addon
        return obj.type == "MESH"

    def ObjectHasDataLayer(obj):
        if ZBBQ_Consts.customDataLayerName in obj.data.attributes.keys():
            return True
        return False

    # ==== Adding the stuff needed for further Zen BBQ operations

    def ObjectAddDataLayer(obj):
        # print("Adding Data Layer for the given object!")
        obj.data.attributes.new(
            name=ZBBQ_Consts.customDataLayerName,
            type="FLOAT", domain="POINT")

    def ObjectRemoveDataLayer(obj):
        # print("Removing Data Layer from the given object!")
        obj.data.attributes.remove(obj.data.attributes[ZBBQ_Consts.customDataLayerName])

    # ==== Whole object operations

    @classmethod
    def ObjectIsReadyForBevel(cls, obj):
        # Just checking if this object is ready for bevel, but not doing anything
        if (cls.ObjectIsConvenient(obj)
                and cls.ObjectHasDataLayer(obj)
                and ZBBQ_MaterialFunc.ObjectHasMaterialsFilled(obj)
                and ZBBQ_MaterialFunc.ObjectHasShaderNodeNormal(obj)):

            return True
        return False

    @classmethod
    def ObjectGetReadyForBevel(cls, obj):
        # Checking if this object is ready for bevel AND fixing what's needed
        # The returned object will contain info about need to update BMesh

        result = {'success': False, 'dataLayerWasAdded': False}

        if not cls.ObjectIsConvenient(obj):
            # We can't get object ready if it's not convenient at all
            return result

        if not cls.ObjectHasDataLayer(obj):

            cls.ObjectAddDataLayer(obj)
            result['dataLayerWasAdded'] = True

        if not ZBBQ_MaterialFunc.ObjectHasMaterialsFilled(obj):
            ZBBQ_MaterialFunc.ObjectFillMissingMatsWithDefaultZenBBQMaterial(obj)

        if not ZBBQ_MaterialFunc.ObjectHasShaderNodeNormal(obj):
            ZBBQ_MaterialFunc.ObjectAddShaderNodeNormal(obj)

        result['success'] = True
        return result

    @classmethod
    def ObjectCleanupFromForBevel(cls, obj):
        # Remove all traces of Zen BBQ usage from the object given

        print(f"Cleaning up object: {obj}")

        if not cls.ObjectIsConvenient(obj):
            # We can't get object ready if it's not convenient at all
            return

        # Material/Shader handling

        if ZBBQ_MaterialFunc.ObjectHasMaterialsFilled(obj):

            for i in range(len(obj.material_slots)):
                mat = obj.material_slots[i].material

                if mat.name == ZBBQ_Consts.defaultMaterialName:
                    # If there is Zen BBQ default material, we just remove it
                    obj.material_slots[i].material = None
                else:
                    # User's material.
                    # Remove Zen BBQ node if present.
                    ZBBQ_MaterialFunc.MaterialRemoveShaderNodeNormal(mat)

                    # Remove nodes that are not linked:
                    ZBBQ_MaterialFunc.MaterialRemoveShaderNodeGroupsByNodeTreeName(mat, ZBBQ_Consts.shaderNodeTreeNormalName)

                    # Remove override node if present
                    toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode
                    ZBBQ_MaterialFunc.MaterialRemoveOverrideNode(mat, toggleNodeTreeName)  # To-Do: Multiple options

                    # Remove nodes that are not linked:
                    ZBBQ_MaterialFunc.MaterialRemoveShaderNodeGroupsByNodeTreeName(mat, toggleNodeTreeName)

        # Data Layer Handling

        if cls.ObjectHasDataLayer(obj):
            cls.ObjectRemoveDataLayer(obj)

        return

    @classmethod
    def GlobalCleanup(cls):

        OpDrawHighlight = eval("bpy.ops.zbbq.draw_highlight")
        if OpDrawHighlight.poll():
            OpDrawHighlight('INVOKE_DEFAULT', mode='OFF')

        for obj in [obj for obj in bpy.context.scene.objects if cls.ObjectIsConvenient(obj)]:
            ZBBQ_CommonFunc.ObjectCleanupFromForBevel(obj)

        ZBBQ_MaterialFunc.RemoveDefaultZenBBQMaterialFromSceneIfPresent()

        # We also must remove bevel nodes and override nodes from all materials in scene even it they are not currently used on objects!

        toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode

        for mat in bpy.data.materials:
            ZBBQ_MaterialFunc.MaterialRemoveShaderNodeNormal(mat)
            ZBBQ_MaterialFunc.MaterialRemoveOverrideNode(mat, toggleNodeTreeName)  # To-Do: Multiple options

            # Remove nodes that are not linked:
            ZBBQ_MaterialFunc.MaterialRemoveShaderNodeGroupsByNodeTreeName(mat, ZBBQ_Consts.shaderNodeTreeNormalName)
            ZBBQ_MaterialFunc.MaterialRemoveShaderNodeGroupsByNodeTreeName(mat, toggleNodeTreeName)

        ZBBQ_MaterialFunc.RemoveNodeTreeFromSceneIfPresent(ZBBQ_Consts.shaderNodeTreeNormalName)
        ZBBQ_MaterialFunc.RemoveNodeTreeFromSceneIfPresent(ZBBQ_Consts.shaderNodeTreePreviewMetallicName)

        # To-Do: Should we remember (and restore) if there was Eevee engine?
        # Or not because we ask user's confirmation before setting Cycles?

        from .sceneConfig import ZBBQ_PreviewRenderPresetsSet, ZBBQ_PreviewRenderConfigIsNotTouched

        userConfig = bpy.context.scene.ZBBQ_PreviewRenderUserConfig
        if bpy.context.scene.render.engine == 'CYCLES' and not ZBBQ_PreviewRenderConfigIsNotTouched():
            if userConfig.isSet:
                ZBBQ_PreviewRenderPresetsSet(None, -1)
            else:
                pass
                #  ZBBQ_PreviewRenderPresetsSetDefault(None) @ Keep current user's settings instead

        bpy.context.scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce = False
        bpy.context.scene.ZBBQ_HasPresetsIncluded = False
        ZBBQ_Globals.displaySceneIncludedBevelPresets = False

    # ==== Mesh Ops

    @classmethod
    def SetBevelRadiusToSelectedGeometry(cls, objects, radius, boundaryLoopOnlyMode):

        for obj in objects:

            if not cls.ObjectIsConvenient(obj):
                # Non-mesh objects are ignored
                continue

            if obj.data.total_vert_sel == 0:
                continue

            getObjectReadyForBevel = cls.ObjectGetReadyForBevel(obj)

            if not getObjectReadyForBevel['success']:
                # In a normal situation, this should never happen
                print('[Zen BBQ] Error: Unable to get the object ready for Zen BBQ! (In a normal situation, this should never happen)')
                continue

            if getObjectReadyForBevel['dataLayerWasAdded']:

                # If the object was "clear" before, we add a preview node

                toggleNodeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode
                toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode

                for mat in obj.data.materials:
                    ZBBQ_MaterialFunc.MaterialAddOverrideNode(mat, toggleNodeName, toggleNodeTreeName)

            bm = bmesh.from_edit_mesh(obj.data)

            dataLayer = bm.verts.layers.float.get(ZBBQ_Consts.customDataLayerName)
            # bm = bmesh.from_edit_mesh(obj.data)

            if boundaryLoopOnlyMode:
                Log.debug("boundaryLoopOnlyMode ON!")

                for v in [v for v in bm.verts if v.select]:
                    # Check if this is boundary of the selection.
                    # This means that at least one loop of the vertex has vertex not selected
                    # OR this vertex has is_boundary True

                    if v.is_boundary:
                        v[dataLayer] = radius
                    else:
                        for edge in v.link_edges:
                            if not edge.verts[0].select or not edge.verts[1].select:
                                # selection boundary
                                v[dataLayer] = radius
                                break

            else:  # No need to check if this is selection boundary
                for v in [v for v in bm.verts if v.select]:
                    v[dataLayer] = radius

            from .draw_sets import ZBBQ_EdgeLayerManager, mark_groups_modified
            mark_groups_modified(ZBBQ_EdgeLayerManager, obj)
            bmesh.update_edit_mesh(obj.data)

    @classmethod
    def SetBevelRadiusToObjects(cls, objects, radius):

        for obj in objects:

            if not cls.ObjectIsConvenient(obj):
                # Non-mesh objects are ignored
                continue

            getObjectReadyForBevel = cls.ObjectGetReadyForBevel(obj)

            if not getObjectReadyForBevel['success']:
                # In a normal situation, this should never happen
                print('[Zen BBQ] Error: Unable to get the object ready for Zen BBQ! (In a normal situation, this should never happen)')
                continue

            if getObjectReadyForBevel['dataLayerWasAdded']:

                # If the object was "clear" before, we add a preview node

                toggleNodeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode
                toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode

                for mat in obj.data.materials:
                    ZBBQ_MaterialFunc.MaterialAddOverrideNode(mat, toggleNodeName, toggleNodeTreeName)

            needToFreeBM = False

            if obj.data.is_editmode:  # Happens on scene load
                bm = bmesh.from_edit_mesh(obj.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                needToFreeBM = True

            dataLayer = bm.verts.layers.float.get(ZBBQ_Consts.customDataLayerName)
            for v in bm.verts:
                v[dataLayer] = radius

            if needToFreeBM:
                bm.to_mesh(obj.data)
                bm.free()  # Need to free memory if bm was created via new()
            else:
                bmesh.update_edit_mesh(obj.data)

            from .draw_sets import ZBBQ_EdgeLayerManager, mark_groups_modified
            mark_groups_modified(ZBBQ_EdgeLayerManager, obj)

    @classmethod
    def SmartSelectByRadiusValues(cls, objects, radii, threshold, addToSelection):

        for obj in objects:

            if not cls.ObjectIsConvenient(obj):
                # Non-mesh objects are ignored
                continue

            bm = bmesh.from_edit_mesh(obj.data)

            if not cls.ObjectHasDataLayer(obj):
                # We do not add Data Layer if there is none
                # Instead, we consider all vertices to have zero radius
                # And select them all if radii contains zero
                if 0 in radii:
                    for vert in bm.verts:
                        vert.select = True
            else:

                dataLayer = bm.verts.layers.float.get(ZBBQ_Consts.customDataLayerName)

                # vertsNotSelected = [vert for vert in bm.verts if not vert.select]

                if not addToSelection:
                    for vert in bm.verts:
                        vert.select = False
                    for edge in bm.edges:
                        edge.select = False
                    for face in bm.faces:
                        face.select = False

                for valueToCheck in radii:

                    # To-Do: iterate from end removing already selected vertices for optimization
                    for vert in bm.verts:
                        if abs(vert[dataLayer] - valueToCheck) <= threshold*valueToCheck:
                            vert.select = True

                # Also selecting other types of elements: edges and polygons
                # To-Do: Some optimization can be done

                for edge in bm.edges:
                    if all(vert.select for vert in edge.verts):
                        edge.select = True
                for face in bm.faces:
                    if all(vert.select for vert in face.verts):
                        face.select = True

            bmesh.update_edit_mesh(obj.data)

    # ==== Common

    def Report(op, text):
        op.report({'INFO'}, '[Zen BBQ] '+text)

    def Log(op, text):  # For cases when OP.report is not available
        print('[Zen BBQ] '+text)

    StrConfirmQuestionCachedVriants = ["OK?", "proceed?", "right?", "confirm?", "mmkay?", "srsly?", "correct?", "shall we?"]
    StrConfirmQuestionAnchorObj = None
    StrConfirmQuestionCachedVal = random.choice(StrConfirmQuestionCachedVriants)

    @classmethod
    def StrConfirmQuestion(cls, anchorObj):
        if anchorObj is not None and cls.StrConfirmQuestionAnchorObj != anchorObj:
            cls.StrConfirmQuestionAnchorObj = anchorObj
            cls.StrConfirmQuestionCachedVal = random.choice(cls.StrConfirmQuestionCachedVriants)
        return cls.StrConfirmQuestionCachedVal

    def View3DIsModeRendered():
        for space in bpy.context.area.spaces:
            if space.type == 'VIEW_3D':
                if space.shading.type == "RENDERED":
                    return True
        return False

    @classmethod
    def IsRenderPreviewActive(cls):
        return bpy.context.scene.render.engine == 'CYCLES' and not bpy.context.scene.cycles.preview_pause and cls.View3DIsModeRendered()

    # ==== Preferences

    # Returns pointer to the preferences object of the addon
    def GetPrefs():
        return bpy.context.preferences.addons[ZBBQ_Consts.addonId].preferences

    def GetAddonVersion():
        global _CACHE_ADDON_VERSION
        if _CACHE_ADDON_VERSION is None:
            for addon in addon_utils.modules():
                if addon.bl_info['name'] == 'Zen BBQ':
                    ver = addon.bl_info['version']
                    _CACHE_ADDON_VERSION = '%i.%i.%i' % (ver[0], ver[1], ver[2])
                    break

        return _CACHE_ADDON_VERSION if _CACHE_ADDON_VERSION else '0.0.0'

    # Returns currently selected presets if there is one or None otherwise
    def GetActiveBevelPresetGroup():

        prefs = ZBBQ_CommonFunc.GetPrefs()

        if prefs is None:
            return None

        if len(prefs.bevelPresetGroups) == 0:
            return None

        elif int(prefs.bevelPresetGroupsDropdown) == len(prefs.bevelPresetGroups):
            return bpy.context.scene.ZBBQ_PresetsIncluded

        elif int(prefs.bevelPresetGroupsDropdown) > len(prefs.bevelPresetGroups):
            prefs.bevelPresetGroupsDropdown = str(len(prefs.bevelPresetGroups) - 1)

        return prefs.bevelPresetGroups[int(prefs.bevelPresetGroupsDropdown)]

    @classmethod
    def GetActiveBevelPreset(cls):
        return cls.GetActiveBevelPresetGroup().GetActiveBevelPreset()

    @classmethod
    def CreateBevelPresetGroup(cls, title, units):

        prefs = cls.GetPrefs()

        # Making preset group title unique

        titleIncrement = 0
        titleResult = title
        titleIsUnique = False

        while not titleIsUnique:
            titleIsUnique = True
            for bpg in prefs.bevelPresetGroups:
                if bpg.title == titleResult:
                    titleIsUnique = False
                    titleIncrement += 1
                    titleResult = f'{title} {titleIncrement:03}'

        bpg = prefs.bevelPresetGroups.add()

        bpg.title = titleResult

        unitInfo = ZBBQ_Units[units]
        bpg.unitSystem = unitInfo.unitSystem

        colors = list(ZBBQ_Colors.values())

        for i in range(6):
            preset = bpg.bevelPresets.add()
            preset.unitSystem = unitInfo.unitSystem  # Need to set this first for correct list of Enum options
            preset.radius = unitInfo.defaultValues[i]  # To-Do: Have some standard values for each unit
            preset.units = units
            preset.colorId = [*ZBBQ_Colors][i]
            preset.color = colors[i].color

        prefs.bevelPresetGroupsDropdown = str(len(prefs.bevelPresetGroups) - 1)

        return bpg

    @classmethod
    def BevelPresetGroupsCreateDefaultIfNone(cls):
        prefs = cls.GetPrefs()
        if len(prefs.bevelPresetGroups) == 0:
            cls.BevelPresetGroupsCreateDefault()

    @classmethod
    def BevelPresetGroupsCreateDefault(cls):
        prefs = cls.GetPrefs()

        cls.CreateBevelPresetGroup('Default mm',     'MILLIMETERS')
        cls.CreateBevelPresetGroup('Default cm',     'CENTIMETERS')
        cls.CreateBevelPresetGroup('Default m',      'METERS')
        cls.CreateBevelPresetGroup('Default inches', 'INCHES')

        if ZBBQ_Globals.displaySceneIncludedBevelPresets:
            prefs.bevelPresetGroupsDropdown = str(len(prefs.bevelPresetGroups))
        else:
            prefs.bevelPresetGroupsDropdown = '1'

    @classmethod
    def BevelPresetGroupsResetToDefault(cls):
        prefs = cls.GetPrefs()

        for i in range(len(prefs.bevelPresetGroups)-1, -1, -1):
            prefs.bevelPresetGroups.remove(i)

        cls.BevelPresetGroupsCreateDefault()

    ULIndexToPieMenuNumKey = {
        0: 9,
        1: 6,
        2: 3,
        3: 1,
        4: 4,
        5: 7
    }

    PieMenuIndexToPieMenuNumKey = {
        0: 4,
        1: 6,
        2: 8,
        3: 2,
        4: 7,
        5: 9,
        6: 1,
        7: 3
    }

    @classmethod
    def ULIndexAndColorToPieMenuIconId(cls, index, color):
        return ZBBQ_Icons[f'{color}Position{cls.ULIndexToPieMenuNumKey[index]}'].id()

    @classmethod
    def PieMenuIndexAndColorToPieMenuIconId(cls, index, color):
        return ZBBQ_Icons[f'{color}Position{cls.PieMenuIndexToPieMenuNumKey[index]}'].id()

    def ColoredEdgesEnableIfNeverUsed():
        # print(f"bpy.context.scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce: {bpy.context.scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce}")
        if not bpy.context.scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce:
            OpDrawHighlight = eval("bpy.ops.zbbq.draw_highlight")
            if OpDrawHighlight.poll():
                OpDrawHighlight('INVOKE_DEFAULT', mode='ON')


class ZBBQ_MaterialFunc:

    def ObjectHasMaterialsFilled(obj):

        if len(obj.material_slots) == 0:
            return False

        for matSlot in obj.material_slots:
            if matSlot.material is None:
                return False

        return True

    # ==== Node Trees

    @classmethod
    def GetOrCreateNodeTree(cls, toggleNodeTreeName):
        if toggleNodeTreeName not in bpy.data.node_groups.keys():

            if toggleNodeTreeName == ZBBQ_Consts.shaderNodeTreeNormalName:
                cls.CreateNodeTreeNormal()

            elif toggleNodeTreeName == ZBBQ_Consts.shaderNodeTreePreviewMetallicName:
                cls.CreateNodeTreePreviewMetallic()

            else:
                print(f"Error! Have no instructions to create node tree {toggleNodeTreeName}!")
                return None

        return bpy.data.node_groups[toggleNodeTreeName]

    @classmethod
    def RemoveNodeTreeFromSceneIfPresent(cls, nodeTreeName):
        if nodeTreeName in bpy.data.node_groups.keys():
            bpy.data.node_groups.remove(bpy.data.node_groups[nodeTreeName])
            # print(f"Removed {nodeTreeName}!")

    def CreateNodeTreeNormal():

        nodeGroup = bpy.data.node_groups.new(
            ZBBQ_Consts.shaderNodeTreeNormalName,
            'ShaderNodeTree')

        snInput = nodeGroup.nodes.new('NodeGroupInput')
        snInput.location = (0, -100)
        nodeGroup.inputs.new('NodeSocketVectorXYZ', 'Normal')

        snOutput = nodeGroup.nodes.new('NodeGroupOutput')
        snOutput.location = (400, 0)
        nodeGroup.outputs.new('NodeSocketVectorXYZ', 'Normal')

        snAttribute = nodeGroup.nodes.new('ShaderNodeAttribute')
        snAttribute.attribute_name = ZBBQ_Consts.customDataLayerName
        snAttribute.location = (0, 100)

        snBevel = nodeGroup.nodes.new('ShaderNodeBevel')
        snBevel.samples = bpy.context.scene.ZBBQ_PreviewRenderUserConfig.bevelNodeSamples
        snBevel.location = (200, 5)

        nodeGroup.links.new(
            snBevel.inputs['Radius'],
            snAttribute.outputs['Fac'])
        nodeGroup.links.new(
            snBevel.inputs['Normal'],
            snInput.outputs['Normal'])

        nodeGroup.links.new(snBevel.outputs[0], snOutput.inputs[0])

    def NodeTreeNormalPresent():
        return ZBBQ_Consts.shaderNodeTreeNormalName in bpy.data.node_groups.keys()

    @classmethod
    def NodeTreeNormalSetSamples(cls, samples):
        # print(f"Set samples: {samples}")

        if not cls.NodeTreeNormalPresent():
            cls.CreateNodeTreeNormal()

        nodeTreeNormal = bpy.data.node_groups[ZBBQ_Consts.shaderNodeTreeNormalName]
        for node in nodeTreeNormal.nodes:
            if node.type == "BEVEL":
                node.samples = samples
                break

    @classmethod
    def NodeTreeNormalGetSamples(cls):

        if not cls.NodeTreeNormalPresent():
            return bpy.context.scene.ZBBQ_PreviewRenderUserConfig.bevelNodeSamples  # Return value from prefs

        nodeTreeNormal = bpy.data.node_groups[ZBBQ_Consts.shaderNodeTreeNormalName]
        for node in nodeTreeNormal.nodes:
            if node.type == "BEVEL":
                # print(f"Samples value is: {node.samples}")
                return node.samples

    def CreateNodeTreePreviewMetallic():

        nodeGroup = bpy.data.node_groups.new(
            ZBBQ_Consts.shaderNodeTreePreviewMetallicName,
            'ShaderNodeTree')

        # Basic Shader, Inout and Output

        snInput = nodeGroup.nodes.new('NodeGroupInput')
        snInput.location = (0, -5)
        nodeGroup.inputs.new('NodeSocketShader', 'Surface')

        snShader = nodeGroup.nodes.new('ShaderNodeBsdfPrincipled')
        snShader.location = (200, 0)
        # snShader.inputs['Base Color'].default_value = (0.2, 0.2, 0.2, 1)
        snShader.inputs['Base Color'].default_value = (0.105, 0.090, 0.134, 1)
        snShader.inputs['Metallic'].default_value = 1

        snOutput = nodeGroup.nodes.new('NodeGroupOutput')
        snOutput.location = (500, -5)
        nodeGroup.outputs.new('NodeSocketShader', 'Surface')
        nodeGroup.links.new(snShader.outputs['BSDF'], snOutput.inputs[0])

        # ZenBBQ Node

        if ZBBQ_Consts.shaderNodeTreeNormalName not in bpy.data.node_groups.keys():
            ZBBQ_MaterialFunc.CreateNodeTreeNormal()

        snZenBBQNormal = nodeGroup.nodes.new('ShaderNodeGroup')
        snZenBBQNormal.name = ZBBQ_Consts.shaderNodeNormalName
        snZenBBQNormal.node_tree = bpy.data.node_groups[ZBBQ_Consts.shaderNodeTreeNormalName]
        snZenBBQNormal.location = (0, -565)

        nodeGroup.links.new(snZenBBQNormal.outputs['Normal'], snShader.inputs['Normal'])

    # ==== Material

    def MaterialGetShaderNodeGroups(mat, nodeTreeName, usageCheck):

        # usageCheck:
        #
        # NOCHECK — don't check
        # ANY — for True answer, the node should have at least one active output
        # OVERRIDE — for True answer, the node should have at least one active output with type "surface" linked to Material Output

        result = []

        if not mat.use_nodes:
            return result

        for node in mat.node_tree.nodes:
            if node.type == 'GROUP':
                if node.node_tree and node.node_tree.name == nodeTreeName:

                    if usageCheck == 'NOCHECK':
                        result.append(node)

                    elif usageCheck in ['ANY', 'OVERRIDE']:

                        for output in node.outputs:
                            if len(output.links) > 0:
                                if usageCheck == 'ANY':
                                    result.append(node)
                                else:  # OVERRIDE, also check if it is really connected to the output
                                    for link in output.links:
                                        if link.to_node and link.to_node.type == 'OUTPUT_MATERIAL':
                                            result.append(node)
                                            break

        return result

    def MaterialRemoveShaderNodeGroupsByNodeTreeName(mat, nodeTreeName):

        # Important! This function does not restore links!
        # It just removed node by nodeTreeName!
        # If you need to save links,
        # please use MaterialRemoveShaderNodeNormal or MaterialRemoveOverrideNode instead!

        if mat.node_tree is None:
            return

        nodesToRemove = []

        for node in mat.node_tree.nodes:
            if node.type == 'GROUP':
                if node.node_tree and node.node_tree.name == nodeTreeName:
                    nodesToRemove.append(node)

        for node in nodesToRemove:
            mat.node_tree.nodes.remove(node)

    @classmethod
    def MaterialHasShaderNodesNormal(cls, mat):
        return cls.MaterialGetShaderNodeGroups(mat, ZBBQ_Consts.shaderNodeTreeNormalName, 'ANY')

    @classmethod
    def MaterialAddShaderNodeNormal(cls, mat):

        if len(cls.MaterialHasShaderNodesNormal(mat)) > 0:
            return  # Don't add bevel node if there already is one

        if not mat.use_nodes:
            mat.use_nodes = True

        matLinks = mat.node_tree.links
        matNodes = mat.node_tree.nodes
        sockNormalInputs = []

        for node in matNodes:
            # This should be a Surface node (for example, Principied BSDF)
            if len([sockOutShader for sockOutShader in node.outputs if sockOutShader.type == 'SHADER']) > 0:
                # It also needs to have Normal input, if so, add it to the list for further work
                if 'Normal' in node.inputs:
                    sockNormalInputs.append(node.inputs['Normal'])

        for sockNormalInput in sockNormalInputs:

            sockNormalOriginalOut = None
            if len(sockNormalInput.links) > 0:
                sockNormalOriginalOut = sockNormalInput.links[0].from_socket
                matLinks.remove(sockNormalInput.links[0])

            snZenBBQNormal = matNodes.new('ShaderNodeGroup')
            snZenBBQNormal.node_tree = cls.GetOrCreateNodeTree(ZBBQ_Consts.shaderNodeTreeNormalName)
            snZenBBQNormal.name = ZBBQ_Consts.shaderNodeNormalName
            snZenBBQNormal.location = (sockNormalInput.node.location[0]-200, sockNormalInput.node.location[1])

            matLinks.new(snZenBBQNormal.outputs['Normal'], sockNormalInput)

            if sockNormalOriginalOut is not None:
                matLinks.new(snZenBBQNormal.inputs['Normal'], sockNormalOriginalOut)

    @classmethod
    def MaterialRemoveShaderNodeNormal(cls, mat):

        materialNeedsToBeManuallyUpdated = True

        if not mat.use_nodes:
            return

        matLinks = mat.node_tree.links
        matNodes = mat.node_tree.nodes

        nodesToRemove = cls.MaterialHasShaderNodesNormal(mat)
        for nodeToRemove in nodesToRemove:

            socketsToNormalOriginal = []
            socketFromNormalOriginal = None

            inNormal = nodeToRemove.inputs['Normal']
            outNormal = nodeToRemove.outputs['Normal']

            if len(inNormal.links) > 0:
                socketFromNormalOriginal = inNormal.links[0].from_socket

                for link in outNormal.links:
                    socketsToNormalOriginal.append(link.to_socket)

                for socketToNormalOriginal in socketsToNormalOriginal:
                    matLinks.new(socketToNormalOriginal, socketFromNormalOriginal)
                    materialNeedsToBeManuallyUpdated = False

            matNodes.remove(nodeToRemove)

        # Clutchy way to update material after node removal
        # is to re-create one of output links (for sure, currently all of them)
        # To-Do: Move this to separate function

        if materialNeedsToBeManuallyUpdated:

            for node in matNodes:
                if node.type == 'OUTPUT_MATERIAL':
                    for sockInput in node.inputs:
                        if len(sockInput.links) > 0:
                            originalFrom = sockInput.links[0].from_socket
                            originalTo = sockInput.links[0].to_socket

                            matLinks.remove(sockInput.links[0])
                            matLinks.new(originalFrom, originalTo)

    @classmethod
    def MaterialAddOverrideNode(cls, mat, toggleNodeName, toggleNodeTreeName):

        cls.MaterialRemoveOverrideNode(mat, toggleNodeTreeName)  # Clear it in before just in case

        # if cls.MaterialHasShaderNodeGroup(mat, toggleNodeTreeName, 'OVERRIDE'):
        #     return  # Don't add override node if there already is one

        if not mat.use_nodes:
            mat.use_nodes = True

        matLinks = mat.node_tree.links
        matNodes = mat.node_tree.nodes

        for node in matNodes:
            if node.type == 'OUTPUT_MATERIAL':

                outSurface = node.inputs['Surface']

                snOverrideSurface = matNodes.new('ShaderNodeGroup')
                snOverrideSurface.name = toggleNodeName
                snOverrideSurface.node_tree = cls.GetOrCreateNodeTree(toggleNodeTreeName)  # To-Do: Always use this func
                snOverrideSurface.location = (outSurface.node.location[0]-100, outSurface.node.location[1]+150)

                if len(outSurface.links) > 0:
                    originalFromSocket = outSurface.links[0].from_socket
                    matLinks.remove(outSurface.links[0])
                    matLinks.new(snOverrideSurface.inputs['Surface'], originalFromSocket)

                matLinks.new(snOverrideSurface.outputs['Surface'], node.inputs['Surface'])

    def MaterialRemoveOverrideNode(mat, toggleNodeTreeName):  # To-Do: Work with multiple override node tree names

        if not mat.use_nodes:
            return

        matLinks = mat.node_tree.links
        matNodes = mat.node_tree.nodes

        nodesMatOutput = [node for node in matNodes if node.type == 'OUTPUT_MATERIAL']
        overrideNodesToBeDeleted = []

        for nodeMatOutput in nodesMatOutput:

            nodeToCheck = nodeMatOutput

            while nodeToCheck is not None:

                socketsToCheck = [sockInShader for sockInShader in nodeToCheck.inputs if sockInShader.type == 'SHADER']
                nodeToCheck = None

                if len(socketsToCheck) == 0:
                    break

                for sockInShader in socketsToCheck:
                    if len(sockInShader.links) == 0:
                        continue  # Nothing is attached to output, nothing to do here

                    snSurfaceOut = sockInShader.links[0].from_node
                    sockSurfaceIn = sockInShader.links[0].to_socket

                    nodeToCheck = snSurfaceOut

                    if snSurfaceOut.type == 'GROUP' and snSurfaceOut.node_tree and snSurfaceOut.node_tree.name == toggleNodeTreeName:

                        inSurfaceOriginalSocket = None

                        if len(snSurfaceOut.inputs['Surface'].links) > 0:
                            inSurfaceOriginalSocket = snSurfaceOut.inputs['Surface'].links[0].from_socket

                        overrideNodesToBeDeleted.append(snSurfaceOut)
                        matLinks.remove(sockInShader.links[0])
                        if inSurfaceOriginalSocket is not None:
                            matLinks.new(sockSurfaceIn, inSurfaceOriginalSocket)

        for nodeToDelete in overrideNodesToBeDeleted:
            matNodes.remove(nodeToDelete)

    @classmethod
    def ObjectHasShaderNodeNormal(cls, obj):

        if len(obj.data.materials) == 0:
            return False

        # To-Do: Return True ONLY if all materials have Shader Node
        for mat in obj.data.materials:
            # Default Material already has the needed node
            if mat.name != ZBBQ_Consts.defaultMaterialName and len(cls.MaterialHasShaderNodesNormal(mat)) == 0:
                return False
        return True

    @classmethod
    def GetOrCreateDefaultZenBBQMaterialInScene(cls):
        mat = bpy.data.materials.get(ZBBQ_Consts.defaultMaterialName)
        if mat is None:
            mat = bpy.data.materials.new(name=ZBBQ_Consts.defaultMaterialName)
            cls.CreateDefaultMaterial(mat)
        return mat

    @classmethod
    def CreateDefaultMaterial(cls, mat):  # We must get a material to build into, for reasons

        mat.use_nodes = True

        matLinks = mat.node_tree.links
        matNodes = mat.node_tree.nodes

        # Clean everything up

        for i in reversed(range(len(matNodes))):
            matNodes.remove(matNodes[i])

        # Re-create structure

        snMatOutput = matNodes.new('ShaderNodeOutputMaterial')
        snMatOutput.location = (300, 300)

        if ZBBQ_Consts.shaderNodeTreePreviewMetallicName not in bpy.data.node_groups.keys():
            ZBBQ_MaterialFunc.CreateNodeTreePreviewMetallic()

        snZenBBQPreviewMetallic = matNodes.new('ShaderNodeGroup')
        snZenBBQPreviewMetallic.name = ZBBQ_Consts.shaderNodeTreePreviewMetallicName
        snZenBBQPreviewMetallic.node_tree = bpy.data.node_groups[ZBBQ_Consts.shaderNodeTreePreviewMetallicName]
        snZenBBQPreviewMetallic.location = (100, 275)

        matLinks.new(snZenBBQPreviewMetallic.outputs['Surface'], snMatOutput.inputs['Surface'])

    @classmethod
    def RemoveDefaultZenBBQMaterialFromSceneIfPresent(cls):
        mat = bpy.data.materials.get(ZBBQ_Consts.defaultMaterialName)
        if mat:
            bpy.data.materials.remove(mat)
            # print(f"Removed material {ZBBQ_Consts.defaultMaterialName}!")

    @classmethod
    def ObjectFillMissingMatsWithDefaultZenBBQMaterial(cls, obj):
        mat = cls.GetOrCreateDefaultZenBBQMaterialInScene()

        if len(obj.material_slots) == 0:
            # print('Appending the default Zen BBQ material')
            obj.data.materials.append(mat)
        else:
            for matSlot in obj.material_slots:
                if matSlot.material is None:
                    matSlot.material = mat

    @classmethod
    def ObjectAddShaderNodeNormal(cls, obj):
        for mat in obj.data.materials:
            cls.MaterialAddShaderNodeNormal(mat)

    @classmethod
    def ObjectRemoveShaderNodeNormal(cls, obj):
        for mat in obj.data.materials:
            cls.MaterialRemoveShaderNodeNormal(mat)

    @classmethod
    def ShaderNodeToggleModeAndObjects(cls, objects, toggleNodeTreeName, usageCheck='ANY'):

        # toggleMode switches to ON if at least one obj has preview not active
        result = {'toggleMode': 'OFF', 'objectsToToggle': []}

        for obj in objects:
            if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                continue

            addToResult = False

            if not cls.ObjectHasMaterialsFilled(obj):
                # Default material is already metallic and is has bevel node so it does not switch
                if toggleNodeTreeName in [ZBBQ_Consts.shaderNodeTreePreviewMetallicName, ZBBQ_Consts.shaderNodeTreeNormalName]:
                    continue
                else:
                    addToResult = True
                    result['toggleMode'] = 'ON'
            else:

                for mat in obj.data.materials:

                    if mat.name == ZBBQ_Consts.defaultMaterialName:
                        # Default material is already metallic and is has bevel node so it does not switch
                        if toggleNodeTreeName in [ZBBQ_Consts.shaderNodeTreePreviewMetallicName, ZBBQ_Consts.shaderNodeTreeNormalName]:
                            continue

                    addToResult = True

                    if len(cls.MaterialGetShaderNodeGroups(mat, toggleNodeTreeName, usageCheck)) == 0:
                        result['toggleMode'] = 'ON'

            if addToResult:
                result['objectsToToggle'].append(obj)

        return result
