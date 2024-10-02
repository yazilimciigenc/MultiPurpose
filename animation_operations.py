import bpy
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty

############################ Animation Operations ############################

class MP_PT_AnimationOperations(Panel):
    bl_label = "Animasyon"
    bl_idname = "mp.animation_operations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MP'

    def draw(self, context):
        layout = self.layout
        layout.scale_y = 1.2
        
        layout.operator("mp.walking_straight", text="Düz Yürüme Döngüsü", icon="CON_LOCLIMIT")
        
        layout.separator()
        
        layout.operator("mp.create_path", text="Karaktere Path Ekle", icon="OUTLINER_OB_CURVE")
        layout.operator("mp.follow_path", text="Path'e Bağla", icon="CON_ROTLIMIT")
        layout.operator("mp.break_path", text="Path'den Ayrıl", icon="FORCE_CURVE")
    
        layout.separator()
    
        layout.operator("mp.root_move", text="Root'u Karaktere Getir", icon="ORIENTATION_CURSOR")

class MP_OT_WalkingStraight(Operator, ImportHelper):
    bl_idname = "mp.walking_straight"
    bl_label = "Düz Yürüme"
    
    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        current_frame = bpy.context.scene.frame_current
        obj = bpy.context.active_object
    
        if obj.type != "ARMATURE":
            return {'CANCELLED'}
        else:
            armature = obj.data
            
        for a in obj.data.bones:
            a.select = False
        
        if 'root' in obj.pose.bones:
            bone = obj.pose.bones['root']
        else:
            for bone in obj.pose.bones:
                if bone.name.startswith("root") and len(bone.name) > 4:
                    bone = obj.pose.bones[bone.name]
                    break
            else:
                return {'CANCELLED'}
            
        first_locations = bone.location[:]
        if len(bone.rotation_mode) == 3:
            first_rotations = bone.rotation_euler[:]
        elif bone.rotation_mode == "QUATERNION":
            first_rotations = bone.rotation_quaternion[:]
        first_scales = bone.scale[:]
            
        if obj.animation_data.action is not None:
            current_action = obj.animation_data.action
        else:
            actions_list = [i.name for i in bpy.data.actions]
            count = 1
            temp_name = "New Action"
            while temp_name in actions_list:
                temp_name = "New Action " + str(count)
                count += 1
            bpy.data.actions.new(name=temp_name)
            current_action = bpy.data.actions[temp_name]
            obj.animation_data.action = current_action
        
        with bpy.data.libraries.load(self.filepath, link=False) as (data_from, data_to):
            for action in data_from.actions:
                anim_action_name = action
                data_to.actions.append(action)
                break

        if anim_action_name in bpy.data.actions:
            anim_action = bpy.data.actions[anim_action_name]
        
        obj.animation_data.action = anim_action
            
        armature.collections_all["Root"].is_visible = True
        bpy.ops.object.mode_set(mode='POSE')
        
        pose_bone = obj.pose.bones.get(bone.name)  
        bpy.ops.pose.select_all(action='DESELECT')
        obj.data.bones[bone.name].select = True
        obj.data.bones.active = obj.data.bones[bone.name]
            
        bpy.context.scene.frame_set(1)
        loc_y_1 = obj.pose.bones["foot_ik.L"].location[1]
        loc_y_1 = abs(round(loc_y_1, 6))
        
        last_frame = max([keyframe.co[0] for fcurve in anim_action.fcurves for keyframe in fcurve.keyframe_points])
        bpy.context.scene.frame_set(int(last_frame))
        loc_y_last = obj.pose.bones["foot_ik.L"].location[1]
        loc_y_last = abs(round(loc_y_last, 6))
        
        total = (loc_y_1 + loc_y_last) * 2
        
        if not anim_action or not current_action:
            print("Belirtilen action'lar bulunamadı.")
            return {'CANCELLED'}

        for fcurve in anim_action.fcurves:
            group_name = fcurve.group.name if fcurve.group else None

            target_fcurve = current_action.fcurves.find(fcurve.data_path, index=fcurve.array_index)
            if not target_fcurve:
                target_fcurve = current_action.fcurves.new(data_path=fcurve.data_path, index=fcurve.array_index)
            
            if group_name:
                if group_name not in current_action.groups:
                    new_group = current_action.groups.new(name=group_name)
                target_fcurve.group = current_action.groups[group_name]

            for keyframe in fcurve.keyframe_points:
                new_keyframe = target_fcurve.keyframe_points.insert(keyframe.co.x + current_frame - 1, keyframe.co.y)
                new_keyframe.interpolation = keyframe.interpolation

            for keyframe in fcurve.keyframe_points:
                new_keyframe_x = keyframe.co.x + current_frame - 1
                if 0 <= new_keyframe_x < len(target_fcurve.keyframe_points):
                    new_keyframe = target_fcurve.keyframe_points[int(new_keyframe_x)]
                    new_keyframe.handle_left_type = keyframe.handle_left_type
                    new_keyframe.handle_right_type = keyframe.handle_right_type

        bpy.context.scene.frame_set(current_frame)
        bpy.context.view_layer.update()
        obj.animation_data.action = current_action
        
        bone.location = first_locations
        if len(bone.rotation_mode) == 3:
            bone.rotation_euler = first_rotations
            bone.keyframe_insert(data_path="rotation_euler", frame=current_frame, group=bone.name)
        elif bone.rotation_mode == "QUATERNION":
            bone.rotation_quaternion = first_rotations
            bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame, group=bone.name)
        bone.scale = first_scales
        bone.keyframe_insert(data_path="location", frame=current_frame, group=bone.name)
        bone.keyframe_insert(data_path="scale", frame=current_frame, group=bone.name)
        
        bpy.context.scene.frame_set(current_frame+int(last_frame)-1)
        bone.location[1] = -total + (first_locations[1])
        bone.keyframe_insert(data_path="location", frame=current_frame+last_frame-1, group=bone.name)
        bone.keyframe_insert(data_path="scale", frame=current_frame+last_frame-1, group=bone.name)
        if len(bone.rotation_mode) == 3:
            bone.keyframe_insert(data_path="rotation_euler", frame=current_frame+last_frame-1, group=bone.name)
        elif bone.rotation_mode == "QUATERNION":
            bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame+last_frame-1, group=bone.name)
            
        action = obj.animation_data.action
        for fcurve in action.fcurves:
            if fcurve.data_path == f'pose.bones["{bone.name}"].location':
                for keyframe in fcurve.keyframe_points:
                    if keyframe.co.x == current_frame or keyframe.co.x == current_frame+int(last_frame)-1:
                        keyframe.interpolation = 'LINEAR'
                        
        for fcurve in action.fcurves:
            if fcurve.data_path == f'pose.bones["{bone.name}"].location' and fcurve.array_index == 1:
                fcurve.extrapolation = 'LINEAR'
                break
        
        if anim_action_name in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[anim_action_name])
        bpy.context.scene.frame_set(current_frame)
        bpy.ops.object.mode_set(mode='OBJECT') 
        
        return {'FINISHED'}

class MP_OT_CreatePath(Operator):
    bl_idname = "mp.create_path"
    bl_label = "Path Oluştur"

    def execute(self, context):
        
        a = bpy.context.active_object
        cursor_first = bpy.context.scene.cursor.location[:]
        
        if a.type == 'ARMATURE':
            obj = a
            armature = obj.data
        else:
            self.report({'WARNING'}, "Lütfen Karakter Rigini Seçiniz!")
            return {'CANCELLED'}
            
        armature.collections_all["Root"].is_visible = True
        
        for a in obj.data.bones:
            a.select = False
        
        for bone in obj.pose.bones:
            if bone.name.startswith("root") and len(bone.name) > 4:
                bone = obj.pose.bones[bone.name]
                break                
        else:
            if 'root' in obj.pose.bones:
                bone = obj.pose.bones['root']
            else:
                self.report({'ERROR'}, "Root Kemiği Bulunamadı!")
                return {'CANCELLED'}
            
        for cons in bone.constraints:
            if cons.type == "FOLLOW_PATH":
                if cons.influence != 0.0 and cons.target is not None:
                    self.report({'WARNING'}, "Burada Zaten Bir Path Var Gibi Gözüküyor!")
                    return {'CANCELLED'}
            
        bpy.ops.object.mode_set(mode='OBJECT')
        current_location = obj.location[:]
        current_frame = bpy.context.scene.frame_current
        
        obj.keyframe_insert(data_path="location", frame=current_frame-1, group="Object Transform")
        if len(obj.rotation_mode) == 3:
            obj.keyframe_insert(data_path="rotation_euler", frame=current_frame-1, group="Object Transform")
        elif obj.rotation_mode == 'QUATERNION':
            obj.keyframe_insert(data_path="rotation_quaternion", frame=current_frame-1, group="Object Transform")
        obj.keyframe_insert(data_path="scale", frame=current_frame-1, group="Object Transform")
        
        obj.location = current_location
        obj.keyframe_insert(data_path="location", frame=current_frame, group="Object Transform")
        if len(obj.rotation_mode) == 3:
            obj.keyframe_insert(data_path="rotation_euler", frame=current_frame, group="Object Transform")
        elif obj.rotation_mode == 'QUATERNION':
            obj.keyframe_insert(data_path="rotation_quaternion", frame=current_frame, group="Object Transform")
        obj.keyframe_insert(data_path="scale", frame=current_frame, group="Object Transform")
        bpy.ops.object.mode_set(mode='POSE')
        
        for cons in bone.constraints:
            if cons.type == "FOLLOW_PATH":
                if cons.target is None:
                    bone.constraints.remove(cons)
                
        bone.bone.select = True
        obj.data.bones.active = obj.data.bones.get(bone.name)
        bpy.context.view_layer.update()
        
        center_bone = bone
        world_matrix = obj.matrix_world @ center_bone.matrix
        global_location = world_matrix @ center_bone.bone.head
        bpy.context.scene.cursor.location = global_location

        cursor_location = bpy.context.scene.cursor.location[:]
        c = cursor_location
        bpy.ops.curve.primitive_bezier_curve_add(radius=1, enter_editmode=False, align='WORLD', 
            location=(c[0], c[1], c[2]), scale=(1, 1, 1))
        
        curve = bpy.context.object
        number = 1
        temp_name = obj.name.replace("RIG-", "") + "_path_" + str(number) 
        while temp_name in bpy.data.objects:
            if obj.name.startswith("RIG-"):
                temp_name = obj.name.replace("RIG-", "") + "_path_" + str(number)
                number += 1
            else:
                temp_name = obj.name + "_path_" + str(number)
                number += 1
        curve.name = temp_name
        
        target_collection_name = "Karakter Pathleri"
        if target_collection_name in bpy.data.collections:
            target_collection = bpy.data.collections[target_collection_name]
        else:
            target_collection = bpy.data.collections.new(target_collection_name)
            bpy.context.scene.collection.children.link(target_collection)
            
        if curve.users_collection:
            old_collection = curve.users_collection[0]
            old_collection.objects.unlink(curve)

        if curve.name not in target_collection.objects:
            target_collection.objects.link(curve)
        
        if curve.type == 'CURVE' and curve.data.splines:
            first_spline = curve.data.splines[0]
            
            if first_spline.bezier_points:
                first_point = first_spline.bezier_points[0].co
            elif first_spline.points:
                first_point = first_spline.points[0].co
            else:
                first_point = None

            if first_point:
                bpy.context.scene.cursor.location = curve.matrix_world @ first_point
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        
        curve.location = c

        constraint = bone.constraints.new('FOLLOW_PATH')
        constraint.name = "_".join(curve.name.split("_")[1:])
        constraint.target = bpy.data.objects[curve.name]
        constraint.use_curve_follow = True
        constraint.forward_axis = 'TRACK_NEGATIVE_Y'
        constraint.up_axis = 'UP_Z'
        constraint.influence = 0.0
        constraint.keyframe_insert(data_path="influence", frame=current_frame-1, group=bone.name)
        constraint.influence = 1.0
        constraint.keyframe_insert(data_path="influence", frame=current_frame, group=bone.name)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.location = (0,0,0)
        if len(obj.rotation_mode) == 3:
            obj.rotation_euler = (0,0,0)
            obj.keyframe_insert(data_path="rotation_euler", frame=current_frame, group="Object Transform")
        elif obj.rotation_mode == 'QUATERNION':
            obj.rotation_quaternion = (1,0,0,0)
            obj.keyframe_insert(data_path="rotation_quaternion", frame=current_frame, group="Object Transform")
        obj.keyframe_insert(data_path="location", frame=current_frame, group="Object Transform")
        obj.keyframe_insert(data_path="scale", frame=current_frame, group="Object Transform")

        curve_data = curve.data
        curve_data.resolution_u = 64
        curve_data.render_resolution_u = 64
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bones = [b.name for b in bpy.context.selected_pose_bones]
        
        for a in bones:
            temp_a = obj.pose.bones[a]
            temp_a.bone.select = True
            obj.data.bones.active = obj.data.bones[a]
            temp_a.keyframe_insert(data_path="location", frame=current_frame-1, group=a)
            temp_a.keyframe_insert(data_path="rotation_euler", frame=current_frame-1, group=a)
            temp_a.keyframe_insert(data_path="rotation_quaternion", frame=current_frame-1, group=a)
            temp_a.keyframe_insert(data_path="scale", frame=current_frame-1, group=a)
        
        for a in bones:
            temp_a = obj.pose.bones[a]
            temp_a.bone.select = True
            obj.data.bones.active = obj.data.bones.get(a)
            obj.data.bones.active = obj.data.bones[a]
            bpy.ops.pose.transforms_clear()
            temp_a.keyframe_insert(data_path="location", frame=current_frame, group=a)
            temp_a.keyframe_insert(data_path="rotation_euler", frame=current_frame, group=a)
            temp_a.keyframe_insert(data_path="rotation_quaternion", frame=current_frame, group=a)
            temp_a.keyframe_insert(data_path="scale", frame=current_frame, group=a)

        bone.bone.select = True
        obj.data.bones.active = obj.data.bones[bone.name]
        bpy.context.view_layer.update()

        bpy.ops.object.mode_set(mode='OBJECT')
            
        bpy.context.scene.cursor.location = cursor_first
        
        return {'FINISHED'}

class MP_OT_FollowPath(Operator, ImportHelper):
    bl_idname = "mp.follow_path"
    bl_label = "Path'e Bağla"

    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        bpy.ops.extensions.package_install(repo_index=0, pkg_id="curve_tools")
        
        bpy.ops.preferences.addon_enable(module="bl_ext.blender_org.curve_tools")
        current_frame = bpy.context.scene.frame_current
        obj = bpy.context.active_object
    
        if obj.type != "ARMATURE":
            return {'CANCELLED'}
        else:
            armature = obj.data
            
        if obj is not None:
            if obj.animation_data.action is not None:
                current_action = obj.animation_data.action
            else:
                actions_list = [i.name for i in bpy.data.actions]
                count = 1
                temp_name = "New Action"
                while temp_name in actions_list:
                    temp_name = "New Action " + str(count)
                    count += 1
                bpy.data.actions.new(name=temp_name)
                current_action = bpy.data.actions[temp_name]
                obj.animation_data.action = current_action
        else:
            return {'CANCELLED'}
        
        with bpy.data.libraries.load(self.filepath, link=False) as (data_from, data_to):
            for action in data_from.actions:
                anim_action_name = action
                data_to.actions.append(action)
                break

        if anim_action_name in bpy.data.actions:
            anim_action = bpy.data.actions[anim_action_name]
        
        obj.animation_data.action = anim_action
            
        armature.collections_all["Root"].is_visible = True
        bpy.ops.object.mode_set(mode='POSE')
        
        for a in obj.data.bones:
            a.select = False
        
        for bone in obj.pose.bones:
            if bone.name.startswith("root") and len(bone.name) > 4:
                bone = obj.pose.bones[bone.name]
                break
        else:
            if 'root' in obj.pose.bones:
                bone = obj.pose.bones['root']
            else:
                return {'CANCELLED'}
        pose_bone = obj.pose.bones.get(bone.name)  
        bpy.ops.pose.select_all(action='DESELECT')
        obj.data.bones[bone.name].select = True
        obj.data.bones.active = obj.data.bones[bone.name]
            
        bpy.context.scene.frame_set(1)
        loc_y_1 = bpy.context.object.pose.bones["foot_ik.L"].location[1]
        loc_y_1 = abs(round(loc_y_1, 6))
        
        last_frame = max([keyframe.co[0] for fcurve in anim_action.fcurves for keyframe in fcurve.keyframe_points])
        bpy.context.scene.frame_set(int(last_frame))
        loc_y_last = bpy.context.object.pose.bones["foot_ik.L"].location[1]
        loc_y_last = abs(round(loc_y_last, 6))
        
        total = (loc_y_1 + loc_y_last) * 2
        
        if not anim_action or not current_action:
            print("Belirtilen action'lar bulunamadı.")
            return {'CANCELLED'}

        for fcurve in anim_action.fcurves:
            target_fcurve = current_action.fcurves.find(fcurve.data_path, index=fcurve.array_index)
            if not target_fcurve:
                target_fcurve = current_action.fcurves.new(data_path=fcurve.data_path, index=fcurve.array_index)
            
            for keyframe in fcurve.keyframe_points:
                new_keyframe = target_fcurve.keyframe_points.insert(keyframe.co.x + current_frame - 1, keyframe.co.y)
                new_keyframe.interpolation = keyframe.interpolation
            
            for keyframe in fcurve.keyframe_points:
                new_keyframe_x = keyframe.co.x + current_frame - 1
                if 0 <= new_keyframe_x < len(target_fcurve.keyframe_points):
                    new_keyframe = target_fcurve.keyframe_points[int(new_keyframe_x)]
                    new_keyframe.handle_left_type = keyframe.handle_left_type
                    new_keyframe.handle_right_type = keyframe.handle_right_type
                else:
                    print(f"Index {int(new_keyframe_x)} geçersiz, keyframe eklenmedi.")

        bpy.context.scene.frame_set(current_frame)
        bpy.context.view_layer.update()
        
        obj.animation_data.action = current_action
        bpy.context.scene.frame_set(current_frame)
        
        offset_value = - ((48.53 * total) + 1.625)
        
        constraint_path = None
        for fcurve in current_action.fcurves:
            if fcurve.data_path.endswith("influence") and bone.name in fcurve.data_path:
                keyframes = [kp.co.x for kp in fcurve.keyframe_points]
                if len(keyframes) == 4:
                    if keyframes[1] <= current_frame <= keyframes[2]:
                        constraint_path = fcurve.data_path
                elif len(keyframes) == 2:
                    if keyframes[1] <= current_frame:
                        constraint_path = fcurve.data_path
                else:
                    self.report({'WARNING'}, "Path bağlanırken bir sorun oluştu, animasyonunuzu kontrol ediniz!")
                    
        if constraint_path is not None:
            constraint_name_mtch = re.search(r'constraints\["([^"]+)"\]', constraint_path)
            constraint_name = constraint_name_mtch.group(1)
            constraint = bone.constraints[constraint_name]
        
        curve = constraint.target
        for bone in bpy.context.selected_pose_bones:
            bone.bone.select = False
        bpy.context.view_layer.update()
        curve.select_set(True)
        bpy.context.view_layer.objects.active = curve
        bpy.ops.curvetools.operatorcurvelength()
        curve_len = bpy.context.scene.curvetools.CurveLength
        half_curve_len = curve_len/ 2.08248
        
        offset_value = offset_value / half_curve_len
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        
        bpy.context.scene.frame_set(current_frame)
        constraint.offset = 0
        constraint.keyframe_insert(data_path="offset", frame=current_frame, group=bone.name)
        
        bpy.context.scene.frame_set(current_frame + 24)
        constraint.offset = offset_value
        constraint.keyframe_insert(data_path="offset", frame=current_frame + 24, group=bone.name) 
        
        action = obj.animation_data.action
        fcurve = None
        for fc in action.fcurves:
            if fc.data_path == f'pose.bones["{bone.name}"].constraints["{constraint.name}"].offset':
                fcurve = fc
                break

        if fcurve is not None:
            for keyframe in fcurve.keyframe_points:
                if keyframe.co[0] in {current_frame, current_frame+24}:
                    keyframe.interpolation = 'LINEAR'
            fcurve.extrapolation = 'LINEAR'
        
        bpy.context.scene.frame_set(current_frame)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        bpy.ops.preferences.addon_disable(module="bl_ext.blender_org.curve_tools")
        
        if anim_action_name in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[anim_action_name])
        
        return {'FINISHED'}
    
def menu_func(self, context):
    self.layout.operator(MP_OT_FollowPath.bl_idname)

class MP_OT_BreakPath(Operator):
    bl_idname = "mp.break_path"
    bl_label = "Path'den Ayrıl"

    def execute(self, context):
        
        current_frame = bpy.context.scene.frame_current
        a = bpy.context.active_object
        
        if a.type == 'ARMATURE':
            obj = a
            armature = obj.data
        else:
            self.report({'WARNING'}, "Lütfen Karakter Rigini Seçiniz!")
            return {'CANCELLED'}
            
        for a in obj.data.bones:
            a.select = False
        
        for bone in obj.pose.bones:
            if bone.name.startswith("root") and len(bone.name) > 4:
                bone = obj.pose.bones[bone.name]
                break
        else:
            if 'root' in obj.pose.bones:
                bone = obj.pose.bones['root']
            else:
                return {'CANCELLED'}
            
        bone.bone.select = True
        obj.data.bones.active = obj.data.bones.get(bone.name)
        bpy.context.view_layer.update()
        
        constraint_path = None
        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            
            mutlak_deger = float('inf')
            for fcurve in action.fcurves:
                if fcurve.data_path.endswith("influence") and bone.name in fcurve.data_path:
                    keyframes = [kp.co.x for kp in fcurve.keyframe_points]
                    last_keyframe = max(keyframes)
                    if len(keyframes) < 4 and current_frame > last_keyframe:
                        if abs(current_frame - int(last_keyframe)) < mutlak_deger:
                            mutlak_deger = abs(current_frame - int(last_keyframe))
                            constraint_path = fcurve.data_path
        
        if constraint_path is not None:
            constraint_name_mtch = re.search(r'constraints\["([^"]+)"\]', constraint_path)
            constraint_name = constraint_name_mtch.group(1)
            constraint = bone.constraints[constraint_name]
            
            obj.location = (0,0,0)
            obj.keyframe_insert(data_path="location", frame=current_frame, group="Object Transform")
            if len(obj.rotation_mode) == 3:
                obj.rotation_euler = (0,0,0)
                obj.keyframe_insert(data_path="rotation_euler", frame=current_frame, group="Object Transform")
            elif obj.rotation_mode == 'QUATERNION':
                obj.rotation_quaternion = (1,0,0,0)
                obj.keyframe_insert(data_path="rotation_quaternion", frame=current_frame, group="Object Transform")
            obj.keyframe_insert(data_path="scale", frame=current_frame, group="Object Transform")
            
            center_bone = bone
            world_matrix = obj.matrix_world @ center_bone.matrix
            global_location = world_matrix @ center_bone.bone.head
            bpy.context.scene.cursor.location = global_location[:]
            cursor_location = bpy.context.scene.cursor.location[:]
            
            if constraint is not None:
                bpy.context.scene.frame_set(current_frame)
                constraint.influence = 1.0
                constraint.keyframe_insert(data_path="influence", frame=current_frame, group=bone.name)
                bpy.context.scene.frame_set(current_frame+1)
                constraint.influence = 0.0
                constraint.keyframe_insert(data_path="influence", frame=current_frame+1, group=bone.name)
            else:
                return {'CANCELLED'}
            
            bpy.context.scene.frame_set(current_frame+1)
            obj.location = cursor_location
            
            obj.keyframe_insert(data_path="location", frame=current_frame+1, group="Object Transform")
            if len(obj.rotation_mode) == 3:
                obj.keyframe_insert(data_path="rotation_euler", frame=current_frame+1, group="Object Transform")
            elif obj.rotation_mode == 'QUATERNION':
                obj.keyframe_insert(data_path="rotation_quaternion", frame=current_frame+1, group="Object Transform")
            obj.keyframe_insert(data_path="scale", frame=current_frame+1, group="Object Transform")
                
            armature.collections_all["Root"].is_visible = True
            bpy.context.scene.frame_set(current_frame)
            
            bpy.ops.object.mode_set(mode='OBJECT')
        
        return {'FINISHED'}

class MP_OT_RootMove(Operator):
    bl_idname = "mp.root_move"
    bl_label = "Root'u taşı"

    def execute(self, context):
        
        current_frame = bpy.context.scene.frame_current
        a = bpy.context.active_object
        
        if a.type == 'ARMATURE':
            obj = a
            armature = obj.data
        else:
            self.report({'WARNING'}, "Lütfen Karakter Rigini Seçiniz!")
            return {'CANCELLED'}
            
        for a in obj.data.bones:
            a.select = False
        
        for bone in obj.pose.bones:
            if bone.name.startswith("root") and len(bone.name) > 4:
                root_bone = obj.pose.bones[bone.name]
                break
        else:
            if 'root' in obj.pose.bones:
                root_bone = obj.pose.bones['root']
            else:
                return {'CANCELLED'}
        
        armature.collections_all["Root"].is_visible = True
        
        root_bone.bone.select = True
        obj.data.bones.active = obj.data.bones.get(root_bone.name)
        bpy.context.view_layer.update()
        
        if "karakter_konumu" in obj.pose.bones:
            location_bone = obj.pose.bones["karakter_konumu"]
        else:
            self.report({'ERROR'}, "Karakter konumu için kemik bulunamadı!")
            return {'CANCELLED'}
        
        bone_names = ["torso", "foot_ik.L", "foot_ik.R", root_bone.name]
        for b_name in bone_names:
            temp_bone = obj.pose.bones[b_name]
            temp_bone.keyframe_insert(data_path="location", frame=current_frame-1, group=b_name)
            if len(temp_bone.rotation_mode) == 3:
                temp_bone.keyframe_insert(data_path="rotation_euler", frame=current_frame-1, group=b_name)
            elif temp_bone.rotation_mode == "QUATERNION":
                temp_bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame-1, group=b_name)
            temp_bone.keyframe_insert(data_path="scale", frame=current_frame-1, group=b_name)
        
        center_bone = location_bone
        world_matrix = obj.matrix_world @ center_bone.matrix
        global_location = world_matrix @ center_bone.bone.head
        root_bone.location = global_location[:]
        
        temp_bone = root_bone
        temp_bone.keyframe_insert(data_path="location", frame=current_frame, group=temp_bone.name)
        if len(temp_bone.rotation_mode) == 3:
            temp_bone.keyframe_insert(data_path="rotation_euler", frame=current_frame, group=temp_bone.name)
        elif temp_bone.rotation_mode == "QUATERNION":
            temp_bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame, group=temp_bone.name)
        temp_bone.keyframe_insert(data_path="scale", frame=current_frame, group=temp_bone.name)
        
        for a in bone_names[:-1]:
            temp_a = obj.pose.bones[a]
            temp_a.bone.select = True
            obj.data.bones.active = obj.data.bones[a]
            bpy.ops.pose.transforms_clear()
            temp_a.keyframe_insert(data_path="location", frame=current_frame, group=a)
            temp_a.keyframe_insert(data_path="rotation_euler", frame=current_frame, group=a)
            temp_a.keyframe_insert(data_path="rotation_quaternion", frame=current_frame, group=a)
            temp_a.keyframe_insert(data_path="scale", frame=current_frame, group=a)
        
        bpy.context.scene.frame_set(current_frame)
        
        return {'FINISHED'}