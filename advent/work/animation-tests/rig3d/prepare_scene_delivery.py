import bpy

scene = bpy.context.scene
scene.render.filepath = "//dec01-frames/frame"
scene.frame_set(37)
for item in bpy.context.selected_objects:
    item.select_set(False)
rig = bpy.data.objects["Kinematic cat arms"]
bpy.context.view_layer.objects.active = rig
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_perspective = "CAMERA"
            area.spaces.active.overlay.show_overlays = False
            area.spaces.active.shading.type = "SOLID"
            area.spaces.active.shading.color_type = "MATERIAL"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
