import bpy
import os
import tempfile

OVERLAY_PLANE_NAME = "AI_Viewport_Overlay"
OVERLAY_MAT_NAME = "AI_Overlay_Material"

def get_temp_path(filename="ai_render_output.png"):
    return os.path.join(tempfile.gettempdir(), filename)

def get_or_create_overlay_plane(context):
    scene = context.scene
    cam = scene.camera
    if not cam:
        return None 
        # raising error here might break the thread loop if not caught, better to return None and handle upstream

    if OVERLAY_PLANE_NAME in bpy.data.objects:
        plane = bpy.data.objects[OVERLAY_PLANE_NAME]
        # Ensure it's still parented to camera just in case
        if plane.parent != cam:
             plane.parent = cam
        return plane

    bpy.ops.mesh.primitive_plane_add()
    plane = context.active_object
    plane.name = OVERLAY_PLANE_NAME
    plane.parent = cam
    plane.matrix_parent_inverse.identity()
    plane.hide_select = True
    plane.hide_render = True

    fit_overlay_to_camera(plane, scene)
    return plane

def fit_overlay_to_camera(plane, scene):
    if not plane: return
    
    cam = scene.camera
    if not cam: return

    # Ensure parentage if not already (safeguard)
    if plane.parent != cam:
        plane.parent = cam
        plane.matrix_parent_inverse.identity()

    # Camera looks down -Z. A plane on local XY at negative Z faces the camera.
    distance = 1.0
    plane.location = (0, 0, -distance)
    plane.rotation_euler = (0, 0, 0) # Plane XY faces +Z, which is back at camera.

    frame = cam.data.view_frame(scene=scene)
    frame_distance = abs(frame[0].z) or 1.0
    scale_factor = distance / frame_distance
    width = abs(frame[0].x - frame[3].x) * scale_factor
    height = abs(frame[0].y - frame[1].y) * scale_factor

    # Blender's default plane is 2x2 units, so scale is half the target size.
    plane.scale = (width / 2, height / 2, 1)

def create_overlay_material(scene, image_path):
    if OVERLAY_MAT_NAME in bpy.data.materials:
        mat = bpy.data.materials[OVERLAY_MAT_NAME]
    else:
        mat = bpy.data.materials.new(OVERLAY_MAT_NAME)
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    emission = nodes.new("ShaderNodeEmission")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    out = nodes.new("ShaderNodeOutputMaterial")

    try:
        img = bpy.data.images.load(image_path, check_existing=False) # Reload to force update
        tex.image = img
    except Exception as e:
        print(f"Failed to load image: {e}")
        return mat

    links.new(tex.outputs["Color"], emission.inputs["Color"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    mix.inputs["Fac"].default_value = scene.ai_overlay_opacity
    mix.name = "OverlayMix"

    return mat

def update_overlay_opacity(scene):
    if OVERLAY_MAT_NAME in bpy.data.materials:
        mat = bpy.data.materials[OVERLAY_MAT_NAME]
        if mat.node_tree:
            mix = mat.node_tree.nodes.get("OverlayMix")
            if mix:
                mix.inputs["Fac"].default_value = scene.ai_overlay_opacity

def update_overlay_visibility(scene):
    if OVERLAY_PLANE_NAME in bpy.data.objects:
        bpy.data.objects[OVERLAY_PLANE_NAME].hide_viewport = not scene.ai_overlay_enabled

def force_viewport_shading(context):
    """
    Switches the active 3D view to Material Preview mode AND Camera View.
    """
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Switch to Material Preview
                    if space.shading.type == 'SOLID':
                        space.shading.type = 'MATERIAL'
                    
                    # Switch to Camera View
                    if space.region_3d.view_perspective != 'CAMERA':
                        try:
                            # We can toggle it via operator or setting attribute
                            # Operator is safer as it handles context
                            # But we need to override context for the area
                            override = context.copy()
                            override['area'] = area
                            override['region'] = area.regions[4] # Usually window region? Safe to just set attribute
                            space.region_3d.view_perspective = 'CAMERA'
                        except:
                            pass
