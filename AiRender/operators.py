import bpy
import threading
import time
from . import client
from . import utils

_active_job = False

class AIRenderJob(threading.Thread):
    def __init__(self, context, init_image_path):
        super().__init__()
        self.context = context
        self.init_image_path = init_image_path
        
        # Prepare Prompt
        prompt = context.scene.ai_prompt
        if context.scene.ai_enhance_prompt:
            style_suffix = ", high quality CGI render, physically based rendering, detailed materials and textures, 8k, cinematic lighting, photorealistic, Ray Tracing, Global Illumination, sharp details, professional photography"
            prompt += style_suffix
            
        self.param_prompt = prompt
        self.param_api_key = context.scene.ai_api_key
        self.param_strength = context.scene.ai_img_strength
        self.param_w = context.scene.render.resolution_x
        self.param_h = context.scene.render.resolution_y
    
    def run(self):
        global _active_job
        _active_job = True
        
        try:
            # Step 1: Encode Image (Base64) - Bypass Upload
            image_url = None
            if self.init_image_path:
                print(f"Encoding {self.init_image_path}...")
                image_url = client.encode_image_to_base64(self.init_image_path)
                print(f"Encoded Image (Base64 prefix): {image_url[:30]}...")

            # Step 2: Generate
            print(f"Sending generation request... (Strength: {self.param_strength})")
            
            self.result_url = client.send_api_request(
                self.param_api_key, 
                self.param_prompt, 
                image_url=image_url,
                strength=self.param_strength,
                width=self.param_w, 
                height=self.param_h
            )
            self.success = True
            self.error_msg = None
        except Exception as e:
            self.success = False
            self.error_msg = str(e)
            self.result_url = None
            print(f"Job Error: {e}")

        # Schedule the UI update on the main thread
        bpy.app.timers.register(self._main_thread_callback)

    def _main_thread_callback(self):
        scene = self.context.scene
        
        if self.success:
            try:
                scene.ai_status = "Downloading Image..."
                temp_path = utils.get_temp_path()
                client.download_image(self.result_url, temp_path)
                
                scene.ai_status = "Updating Viewport..."
                plane = utils.get_or_create_overlay_plane(self.context)
                if plane:
                    utils.fit_overlay_to_camera(plane, scene)
                    mat = utils.create_overlay_material(scene, temp_path)
                    if plane.data.materials:
                        plane.data.materials[0] = mat
                    else:
                        plane.data.materials.append(mat)
                
                # Force Viewport Update
                utils.force_viewport_shading(self.context)
                
                scene.ai_status = "Done"
            except Exception as e:
                scene.ai_status = "Download Failed"
                print(f"Download/Update Error: {e}")
        else:
            scene.ai_status = "API Error"
            print(f"API Job Failed: {self.error_msg}")
            
            print(f"API Job Failed: {self.error_msg}")
            
            # Show error in a popup
            # We capture self.error_msg in a local variable for the closure
            msg = self.error_msg
            def draw_error(popup, context):
                popup.layout.label(text=f"Error: {msg}")
            bpy.context.window_manager.popup_menu(draw_error, title="AI Render Error", icon='ERROR')

        global _active_job
        _active_job = False
        return None # Unregister timer

class AIR_OT_render(bpy.types.Operator):
    bl_idname = "air.render"
    bl_label = "AI Render"
    bl_description = "Generate image using Fal.ai"

    def execute(self, context):
        global _active_job
        if _active_job:
            self.report({'WARNING'}, "Job already running")
            return {'CANCELLED'}

        if not context.scene.ai_api_key:
            self.report({'ERROR'}, "Please set your Fal.ai API Key first")
            return {'CANCELLED'}

        if not context.scene.camera:
            self.report({'ERROR'}, "No Active Camera. Please add a camera to the scene.")
            return {'CANCELLED'}

        # 1. Render the current viewport (init image)
        # We need to temporarily hide the overlay plane so we don't render the previous result
        # into the new input!
        scene = context.scene
        overlay_was_enabled = scene.ai_overlay_enabled
        if overlay_was_enabled:
            # Temporarily hide it for render
            utils.update_overlay_visibility(scene) # Logic might need adjustment.
            # Or manually find object and hide_render is already True?
            # Our utils.create_overlay_plane sets hide_render=True, so it Should not appear in F12 render.
            pass
            
        context.scene.ai_status = "Capturing Viewport..."
        
        # Render to temp path
        import os
        import tempfile
        temp_render_path = os.path.join(tempfile.gettempdir(), "ai_input_capture.png")
        
        scene.render.filepath = temp_render_path
        scene.render.image_settings.file_format = 'PNG'
        
        # Render frame - This is blocking UI, which is fine for local render
        bpy.ops.render.render(write_still=True)
        
        context.scene.ai_status = "Uploading..."
        AIRenderJob(context, temp_render_path).start()
        return {'FINISHED'}

class AIR_OT_apply_preset(bpy.types.Operator):
    bl_idname = "air.apply_preset"
    bl_label = "Apply Prompt Preset"
    preset_key: bpy.props.StringProperty() # type: ignore

    PROMPT_PRESETS = {
        "CINEMATIC": "Ultra realistic cinematic render, dramatic lighting, shallow depth of field, global illumination, film grain, epic composition",
        "PRODUCT": "Studio product shot, soft box lighting, clean background, photorealistic materials",
        "CONCEPT": "High detail concept art, cinematic lighting, painterly style, artstation quality",
        "ANIME": "High quality anime style, clean line art, vibrant colors, soft lighting",
        "ARCH": "Photorealistic architectural visualization, global illumination, natural light, modern materials",
    }

    def execute(self, context):
        if self.preset_key in self.PROMPT_PRESETS:
            context.scene.ai_prompt = self.PROMPT_PRESETS[self.preset_key]
        return {'FINISHED'}

classes = (
    AIR_OT_render,
    AIR_OT_apply_preset,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
