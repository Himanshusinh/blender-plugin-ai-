#!/bin/bash
# Launches Blender and loads the AiRender addon package
# We use --python-expr to append the current directory to path and import the module

CURRENT_DIR=$(pwd)
/Applications/Blender.app/Contents/MacOS/Blender --python-expr "import sys; sys.path.append('$CURRENT_DIR'); import bpy; bpy.ops.preferences.addon_enable(module='AiRender')"
