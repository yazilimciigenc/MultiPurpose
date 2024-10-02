import bpy
import os
from bpy.types import Operator, Panel
from bpy.props import StringProperty

############################ Link Operations ############################

class MP_PT_LinkOperations(Panel):
    bl_label = "Link"
    bl_idname = "mp.link_operations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MP'

    def draw(self, context):
        layout = self.layout
        layout.scale_y = 1.2
        
        layout.operator("mp.find_file_paths", text="Dosyaları Bul", icon="FILE_FOLDER")
        
        layout.operator("mp.library_make", text="Rigi Aktif Et", icon="ARMATURE_DATA")
        
        layout.operator("mp.relations_make", text="Shape Keys Aktif Et", icon="SHAPEKEY_DATA")

def file_existing(path, file_name):
    file_path = os.path.join(path, file_name)
    return os.path.isfile(file_path)

class MP_OT_FindFilePaths(Operator):
    bl_idname = "mp.find_file_paths"
    bl_label = "Kayıp Dosyaları Bul"
    bl_options = {'REGISTER', 'UNDO'}

    directory: StringProperty(
        name="Directory",
        subtype='DIR_PATH'
    )

    def execute(self, context):
        folder_path = self.directory
        
        if "Animasyon Kütüphanesi" not in folder_path:
            self.report({'WARNING'}, "Animasyon Kütüphanesi isimli klasoru seciniz!")
        else:
            for library in bpy.data.libraries:
                
                file_path = library.filepath
                file_name = os.path.basename(file_path)
                
                
                result = find_file(folder_path, file_name)
                
                if result:
                    library.filepath = result
                else:
                    print("Dosya bulunamadı.")
            bpy.ops.wm.save_mainfile()
            bpy.ops.wm.revert_mainfile()
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MP_OT_LibraryMake(Operator):
    bl_idname = "mp.library_make"
    bl_label = "Rigi Aktif Et"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            selected_objects = bpy.context.selected_objects
            object_name = selected_objects[0].name.split()[0]
            
            bpy.ops.object.make_override_library()
            
            harfler = {"ü":"U", "i":"I", "ş":"S", "ö":"O", "ç":"C", "ğ":"G"}
            for key, value in harfler.items():
                object_name = object_name.replace(key, value)
            
            for object in bpy.data.objects:
                if object.type == "ARMATURE" and object_name.upper() in object.name:
                    bpy.ops.object.select_all(action='DESELECT')
                    obj = bpy.data.objects.get(object.name)
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                    
                    bpy.ops.object.make_local(type='SELECT_OBJECT')
                    break
        except:
            pass
        
        return {'FINISHED'}
    
class MP_OT_RelationsMake(Operator):
    bl_idname = "mp.relations_make"
    bl_label = "Shape Keys Aktif Et"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.make_local(type='SELECT_OBDATA_MATERIAL')
        
        selected_objects = bpy.context.selected_objects
        for object in selected_objects:
            if object.type == "MESH":
                try:
                    bpy.data.objects[object.name].modifiers["Armature"].show_in_editmode = True
                    bpy.data.objects[object.name].modifiers["Armature"].show_on_cage = True
                except:
                    pass
                
        return {'FINISHED'}