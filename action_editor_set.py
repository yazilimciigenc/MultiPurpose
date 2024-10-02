import bpy
from bpy.types import Operator, Panel, Menu
from bpy.props import StringProperty

############################ Action Editor Operations ############################

class MP_MT_DeleteActionsMenu(Menu):
    bl_label = "Action Sil"
    bl_idname = "mp.delete_actions_menu"

    def draw(self, context):
        layout = self.layout
        
        for action in bpy.data.actions:
            op = layout.operator("mp.delete_action_confirm", text=action.name)
            op.action = action.name 

class MP_OT_DeleteActionConfirm(Operator):
    bl_idname = "mp.delete_action_confirm"
    bl_label = "Action Sil"
    action: StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return bpy.ops.mp.delete_action('INVOKE_DEFAULT', action=self.action)

class MP_OT_DeleteAction(Operator):
    bl_idname = "mp.delete_action"
    bl_label = "Action Silinecek!"
    action: StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"'{self.action}' isimli action silinecek.")
        layout.label(text="Emin misiniz?")

    def execute(self, context):
        bpy.data.actions.remove(bpy.data.actions[self.action])
        self.report({'INFO'}, f'"{self.action}" isimli action silindi!')
        return {'FINISHED'}

class MP_OT_ActionEditorHeader(bpy.types.Operator):
    bl_idname = "mp.action_editor_header_menu"
    bl_label = "Action Editor Header Menu"

    def execute(self, context):
        bpy.ops.wm.call_menu(name="mp.delete_actions_menu")
        return {'FINISHED'}

def draw_header(self, context):
    if context.space_data.mode == 'ACTION':
        layout = self.layout
        layout.operator("mp.action_editor_header_menu", text="Action Sil", icon="DOWNARROW_HLT")
        layout.operator("mp.delete_action_assets", text="Assetleri Sil", icon="ASSET_MANAGER")
        
class MP_OT_DeleteActionAssets(bpy.types.Operator):
    bl_idname = "mp.delete_action_assets"
    bl_label = "Delete Action Assets"
    bl_description = "Delete all Action assets in the current Blender project"

    def execute(self, context):
        # Asset olan action'ları bul ve sil
        actions_to_remove = [action for action in bpy.data.actions if action.asset_data is not None]
        
        for action in actions_to_remove:
            bpy.data.actions.remove(action)
        
        self.report({'INFO'}, f"Deleted {len(actions_to_remove)} action assets.")
        return {'FINISHED'}