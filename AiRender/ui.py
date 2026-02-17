import bpy
from .operators import _active_job

class AIR_PT_panel(bpy.types.Panel):
    bl_label = "AI Render"
    bl_idname = "AIR_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AI Render'

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        # API Key Section
        col = layout.column()
        col.label(text="Settings")
        col.prop(scene, "ai_api_key")

        # Prompt Section
        box = layout.box()
        box.label(text="AI Prompt")
        box.prop(scene, "ai_prompt", text="")
        row = box.row()
        row.prop(scene, "ai_img_strength", slider=True)
        row.prop(scene, "ai_enhance_prompt", text="Auto-Enhance")

        # Preset Buttons
        preset_box = layout.box()
        preset_box.label(text="Prompt Presets")
        row = preset_box.row(align=True)
        row.operator("air.apply_preset", text="Cinematic").preset_key = "CINEMATIC"
        row.operator("air.apply_preset", text="Product").preset_key = "PRODUCT"
        row = preset_box.row(align=True)
        row.operator("air.apply_preset", text="Concept").preset_key = "CONCEPT"
        row.operator("air.apply_preset", text="Anime").preset_key = "ANIME"
        preset_box.operator("air.apply_preset", text="Architectural").preset_key = "ARCH"

        # Resolution
        layout.separator()
        layout.prop(scene, "ai_resolution")

        # Overlay Controls
        overlay_box = layout.box()
        overlay_box.label(text="Viewport Overlay")
        overlay_box.prop(scene, "ai_overlay_enabled")
        overlay_box.prop(scene, "ai_overlay_opacity")

        # Render Button
        layout.separator()
        row = layout.row()
        # Disable if job running or no key
        if not scene.ai_api_key:
            row.enabled = False
            btn_text = "Enter API Key"
        elif _active_job:
            row.enabled = False
            btn_text = "Generating..."
        else:
            row.enabled = True
            btn_text = "Capture & Render"
            
        row.operator("air.render", text=btn_text, icon='RENDER_STILL')

        # Status
        layout.label(text=f"Status: {scene.ai_status}")

def register():
    bpy.utils.register_class(AIR_PT_panel)

def unregister():
    bpy.utils.unregister_class(AIR_PT_panel)
