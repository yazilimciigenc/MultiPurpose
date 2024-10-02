bl_info = {
    'name': 'Multi Purpose',
    'author': 'Yazılımcı Genç',
    'description': "Bismillah! Blender'da işlerimizi kolaylaştırmak amacıyla yazılmıştır.",
    'blender': (4, 0, 2),
    'version': (1, 0, 6),
    'location': 'View3D > Sidebar > Multi Purpose',
    'warning': '',
    'wiki_url': "",
    'tracker_url': "",
    'category': 'Interface'
}

import bpy
from bpy.props import EnumProperty, StringProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup, Menu, Header
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ImportHelper
import os
import re
from . import addon_updater_ops

from .link_operations import MP_PT_LinkOperations, MP_OT_FindFilePaths, MP_OT_LibraryMake, MP_OT_RelationsMake
#from .animation_operations import MP_PT_AnimationOperations, MP_OT_WalkingStraight, MP_OT_CreatePath, MP_OT_FollowPath, MP_OT_BreakPath, MP_OT_RootMove
from .action_editor_set import MP_MT_DeleteActionsMenu, MP_OT_DeleteActionConfirm, MP_OT_DeleteAction, MP_OT_ActionEditorHeader, MP_OT_DeleteActionAssets
from .scripting_set import MP_PT_Scripting_Settings, MP_MT_RunScript, MP_OT_ConfirmRunScript

    
classes = (
    # Link Operations
    MP_PT_LinkOperations, MP_OT_FindFilePaths, MP_OT_LibraryMake, MP_OT_RelationsMake,
    
    # Animation Operations
    #MP_PT_AnimationOperations, MP_OT_WalkingStraight, MP_OT_CreatePath, 
    #MP_OT_FollowPath, MP_OT_BreakPath, MP_OT_RootMove,
    
    # Action Editor Operations
    MP_MT_DeleteActionsMenu, MP_OT_DeleteActionConfirm, MP_OT_DeleteAction, 
    MP_OT_ActionEditorHeader, MP_OT_DeleteActionAssets,
    
    # Scripting Settings
    MP_PT_Scripting_Settings, MP_MT_RunScript, MP_OT_ConfirmRunScript
)

@addon_updater_ops.make_annotations
class DemoPreferences(bpy.types.AddonPreferences):
	"""Demo bare-bones preferences"""
	bl_idname = __package__

	# Addon updater preferences.

	auto_check_update = bpy.props.BoolProperty(
		name="Auto-check for Update",
		description="If enabled, auto-check for updates using an interval",
		default=False)

	updater_interval_months = bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0)

	updater_interval_days = bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31)

	updater_interval_hours = bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23)

	updater_interval_minutes = bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59)

	def draw(self, context):
		layout = self.layout
		addon_updater_ops.update_settings_ui(self, context)


def register():

    addon_updater_ops.register(bl_info)

    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.DOPESHEET_HT_header.append(draw_header)

    bpy.utils.register_class(DemoPreferences)
    
def unregister():

    addon_updater_ops.unregister()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.DOPESHEET_HT_header.remove(draw_header)

    bpy.utils.unregister_class(DemoPreferences)
    
if __name__ == "__main__":
    register()
