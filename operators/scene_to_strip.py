import bpy

from .. import fountain
from pathlib import Path


class SCREENWRITER_OT_scenes_to_strips(bpy.types.Operator):
    """Convert screenplay data to scene and text strips"""
    bl_idname = "screenwriter.scenes_to_strips"
    bl_label = "Create Sequence"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = bpy.context.space_data
        try: 
            filepath = bpy.context.area.spaces.active.text.filepath
            if filepath.strip() == "": return False
            return ((space.type == 'TEXT_EDITOR')
                    and Path(filepath).suffix == ".fountain")
        except AttributeError: return False

    def execute(self, context):

        fountain_script = bpy.context.area.spaces.active.text.as_string()
        if fountain_script.strip() == "": return {"CANCELLED"}

        F = fountain.Fountain(fountain_script)

        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()   

        addSceneChannel = 1
        previous_time = 0
        previous_line = 0
        lines_pr_minute = 59
        first_duration = 0
        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)
        count = 0
        f_collected = []
        duration = 0
        
        for fc, f in enumerate(F.elements):
            if f.element_type == 'Scene Heading':
                f_collected.append(f)

        for fc, f in enumerate(f_collected):
            if str(f.scene_number) != "": f.scene_number = f.scene_number+ " "
            name = str(f.scene_number + f.element_text.title())
            new_scene = bpy.data.scenes.new(name=name)

            cam = bpy.data.cameras.new("Camera")
            cam.lens = 35
            cam_obj1 = bpy.data.objects.new("Camera", cam)
            cam_obj1.location = (9.69, -10.85, 12.388)
            cam_obj1.rotation_euler = (0.6799, 0, 0.8254)
            new_scene.collection.objects.link(cam_obj1)

            if fc == 0:
                for ec, e in enumerate(f_collected):
                    if ec == fc + 1:
                        first_duration = int((((e.original_line)/lines_pr_minute)*60)*fps)
                        duration = first_duration
                print("Fc "+str(e.original_line)+" ec "+str(f.original_line))
            else:
                for ec, e in enumerate(f_collected):
                    if ec == fc+1:            
                        duration = int((((e.original_line - f.original_line)/lines_pr_minute)*60)*fps)
                        
            in_time =  duration + previous_time
            bpy.data.scenes[name].frame_start = 0
            bpy.data.scenes[name].frame_end = duration
            newScene=bpy.context.scene.sequence_editor.sequences.new_scene(f.element_text.title(), new_scene, addSceneChannel, previous_time)
            bpy.context.scene.sequence_editor.sequences_all[newScene.name].scene_camera = bpy.data.objects[cam.name]
            #bpy.context.scene.sequence_editor.sequences_all[newScene.name].animation_offset_start = 0
            bpy.context.scene.sequence_editor.sequences_all[newScene.name].frame_final_end = in_time
            bpy.context.scene.sequence_editor.sequences_all[newScene.name].frame_start = previous_time
            previous_time = in_time
            previous_line = f.original_line
            
        bpy.ops.sequencer.set_range_to_strips()

        characters_pr_minute = 900
        for fc, f in enumerate(F.elements):
            if f.element_type == 'Dialogue':
                name = str(f.element_text)
                duration = int(((len(f.original_content)/characters_pr_minute)*60)*fps)
                in_time = int(((f.original_line/lines_pr_minute)*60)*fps)
                
                text_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
                    name=name,
                    type='TEXT',
                    channel=addSceneChannel+1,
                    frame_start=in_time,
                    frame_end=in_time + duration
                    )
                text_strip.font_size = int(bpy.context.scene.render.resolution_y/18)
                text_strip.text = str(name)
                text_strip.use_shadow = True
                text_strip.select = True
                text_strip.wrap_width = 0.85
                text_strip.location[1] = 0.10
                text_strip.blend_type = 'ALPHA_OVER'

        return {'FINISHED'}