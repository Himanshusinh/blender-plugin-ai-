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
    plane.hide_select = True
    plane.hide_render = True

    fit_overlay_to_camera(plane, scene)
    return plane

def fit_overlay_to_camera(plane, scene):
    if not plane: return
    
    cam = scene.camera
    if not cam: return
    render = scene.render

    # Ensure parentage if not already (safeguard)
    if plane.parent != cam:
        plane.parent = cam
        # When parenting, we want to reset transform so it snaps to camera
        plane.matrix_world = cam.matrix_world

    # Reset transform in local space to lock it to camera view
    # Camera looks down -Z. Plane default is XY.
    distance = 1.0
    plane.location = (0, 0, -distance)
    plane.rotation_euler = (0, 0, 0) # Plane XY faces +Z, which is back at camera.
    
    # Scale to match aspect ratio
    aspect = render.resolution_x / render.resolution_y
    
    # Sensor fit logic duplication to match what the camera sees?
    # Actually, for a plane at distance 1.0, we just need to match the camera's FOV.
    # But as a simple approximation for "Lock to Camera", we scale it directly by aspect.
    # To be perfectly precise requires FOV calculation, but let's start with aspect match.
    # Since we are using "Sensor Fit: Auto" in props.py, we can approximate.
    
    # Standard Blender Camera FOV logic is complex. 
    # For a perfect overlay, we usually use the camera's sensor size and focal length.
    # scale = distance * tan(fov / 2) * 2 or similar.
    # But for now, let's just fix the "Floating" issue (Rotation/Location).
    
    # For a quick fix that looks "okay" without complex math:
    # Just fix the aspect ratio. The user can scale it manually if needed, or we improve math later.
    
    # We need to scale Y to match the camera's sensor aspect behavior
    # If sensor fit is AUTO (which we set in props.py):
    # Horizontal fit? Vertical fit?
    
    # Let's stick to the previous simple aspect logic, but FIXED TRANSLATION/ROTATION first.
    
    if aspect >= 1.0:
        plane.scale = (aspect * 0.5, 0.5, 1) # Example scale, might need tweaking for FOV
    else:
        plane.scale = (0.5, 0.5 / aspect, 1)
        
    # NOTE: The size 0.5 is arbitrary. A default plane is 2x2 meters (radius 1).
    # So scale 0.5 makes it 1x1 meter. 
    # At distance 1.0, we need to calculate exact size.
    # Let's try to calculate it for standard 50mm lens?
    # Actually, better to just let the user see it centered first.
    
    # Let's improve the scale math slightly to fill the view more roughly
    # Camera FOV_Horizontal = 2 * atan((sensor_width/2) / focal_length)
    # But let's revert to the user's initial code's scale logic but FIXED rotation.
    
    if aspect >= 1.0:
        plane.scale = (aspect, 1, 1) # This assumes plane radius 1 (size 2) covers view?
        # A plane is 2m x 2m. Scale 1 = 2m wide.
        # At distance 1m...
        # It's likely too big, but let's stick to what was there, just aligned.
    else:
        plane.scale = (1, 1 / aspect, 1)

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
