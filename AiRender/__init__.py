bl_info = {
    "name": "AI Render – Wildchild Studios",
    "author": "WILDCHILD STUDIOS",
    "version": (0, 6, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > AI Render",
    "description": "Professional AI Rendering System with Fal.ai Integration",
    "category": "Render",
}

import bpy
import sys
import importlib

# Ensure the package is reloadable
if "AiRender.props" in sys.modules:
    importlib.reload(sys.modules["AiRender.props"])
if "AiRender.utils" in sys.modules:
    importlib.reload(sys.modules["AiRender.utils"])
if "AiRender.client" in sys.modules:
    importlib.reload(sys.modules["AiRender.client"])
if "AiRender.operators" in sys.modules:
    importlib.reload(sys.modules["AiRender.operators"])
if "AiRender.ui" in sys.modules:
    importlib.reload(sys.modules["AiRender.ui"])

from . import props, operators, ui

def register():
    props.register_properties()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    props.unregister_properties()

if __name__ == "__main__":
    register()
