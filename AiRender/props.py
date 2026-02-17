import bpy
from .utils import update_overlay_visibility, update_overlay_opacity

def update_resolution_callback(self, context):
    scene = context.scene
    w, h = map(int, scene.ai_resolution.split("x"))
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    
    cam = scene.camera
    if cam:
        aspect = w / h
        cam.data.sensor_fit = 'AUTO'
        base_sensor = 36.0
        if aspect >= 1.0:
            cam.data.sensor_width = base_sensor
            cam.data.sensor_height = base_sensor / aspect
        else:
            cam.data.sensor_height = base_sensor
            cam.data.sensor_width = base_sensor * aspect
        cam.data.update()

def load_env_key():
    import os
    # Look for .env in the parent directory of this addon package
    # current file is .../AiRender/props.py
    # we want .../.env
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir) # .../blenderplugins
    env_path = os.path.join(parent_dir, ".env")
    
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip().startswith("FAL_KEY="):
                        return line.strip().split("=", 1)[1].strip()
        except:
            pass
    return ""

def register_properties():
    # Scene Properties
    bpy.types.Scene.ai_prompt = bpy.props.StringProperty(
        name="Prompt",
        default="",
        maxlen=4000
    )
    
    bpy.types.Scene.ai_api_key = bpy.props.StringProperty(
        name="Fal.ai API Key",
        default=load_env_key(),
        description="Enter your Fal.ai API Key here",
        subtype='PASSWORD'
    )

    bpy.types.Scene.ai_img_strength = bpy.props.FloatProperty(
        name="Image Strength",
        description="How much the AI should respect the input image (0.0 = Creative, 1.0 = Strict)",
        min=0.0,
        max=1.0,
        default=0.75
    )

    bpy.types.Scene.ai_enhance_prompt = bpy.props.BoolProperty(
        name="Enhance Prompt",
        description="Automatically add 'cinematic, photorealistic render' to the prompt",
        default=True
    )

    bpy.types.Scene.ai_resolution = bpy.props.EnumProperty(
        name="Resolution",
        items=[
            ('1920x1080', "1920 × 1080 (Landscape)", ""),
            ('1080x1920', "1080 × 1920 (Portrait)", ""),
            ('2048x2048', "2048 × 2048 (Square)", ""),
            ('3840x2160', "3840 × 2160 (4K)", ""),
        ],
        default='1920x1080',
        update=update_resolution_callback
    )

    bpy.types.Scene.ai_overlay_enabled = bpy.props.BoolProperty(
        name="Overlay Enabled",
        default=True,
        update=lambda self, ctx: update_overlay_visibility(ctx.scene)
    )

    bpy.types.Scene.ai_overlay_opacity = bpy.props.FloatProperty(
        name="Overlay Opacity",
        min=0.0,
        max=1.0,
        default=0.6,
        update=lambda self, ctx: update_overlay_opacity(ctx.scene)
    )

    bpy.types.Scene.ai_status = bpy.props.StringProperty(
        name="Status",
        default="Idle"
    )

def unregister_properties():
    del bpy.types.Scene.ai_prompt
    del bpy.types.Scene.ai_api_key
    del bpy.types.Scene.ai_img_strength
    del bpy.types.Scene.ai_enhance_prompt
    del bpy.types.Scene.ai_resolution
    del bpy.types.Scene.ai_overlay_enabled
    del bpy.types.Scene.ai_overlay_opacity
    del bpy.types.Scene.ai_status
