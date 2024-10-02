import bpy
from bpy.types import Operator, Panel, Menu
from bpy.props import StringProperty

########### Scripting Settings ###########

class MP_PT_Scripting_Settings(Panel):
    bl_idname = 'mp.scripting_settings'
    bl_label = "Scripting Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Item"
    
    def draw(self, context):
        layout = self.layout
        layout.scale_y = 1.2

        layout.menu(MP_MT_RunScript.bl_idname)

class MP_MT_RunScript(Menu):
    bl_label = "Script Çalıştır"
    bl_idname = "mp.run_sript"

    def draw(self, context):
        layout = self.layout

        for text in bpy.data.texts:
            layout.operator("mp.confirm_run_script", text=text.name).text_name = text.name

class MP_OT_ConfirmRunScript(Operator):
    bl_idname = "mp.confirm_run_script"
    bl_label = "Script Çalıştırılacak!"

    text_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"{self.text_name} isimli script çalıştırılacak.")
        layout.label(text="Devam etmek istiyor musunuz?")
        
    def execute(self, context):
        text_block = bpy.data.texts.get(self.text_name)
        
        if text_block:
            current_type = context.area.type
            context.area.type = 'TEXT_EDITOR'
            context.space_data.text = text_block
            bpy.ops.text.run_script()
            context.area.type = current_type
            self.report({'INFO'}, f"{self.text_name} çalıştırıldı.")
        else:
            self.report({'ERROR'}, f"Text bloğu bulunamadı: {self.text_name}")
                
        return {'FINISHED'}