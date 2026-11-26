import json
import math

import bpy
from mathutils import Vector

scene=bpy.context.scene
rig=bpy.data.objects["Kinematic cat arms"]
hinge=bpy.data.objects["Front board hinge / axis through spine"]
book=bpy.data.objects["Book upright in supporting paw"]
angles=[]
contact_errors=[]
shoulder_gaps=[]
support_errors=[]
camera_drift=[]
for frame in range(1,241):
    scene.frame_set(frame)
    if frame==1:
        camera_initial=scene.camera.matrix_world.copy()
        support_initial=rig.pose.bones["hold_paw"].head.copy()
    camera_drift.append(sum(abs(a-b) for row_a,row_b in zip(camera_initial,scene.camera.matrix_world) for a,b in zip(row_a,row_b)))
    angles.append(hinge.rotation_euler.z)
    for key in ["open","hold"]:
        upper,forearm,hand=(rig.pose.bones[f"{key}_{part}"] for part in ["upper","forearm","paw"])
        shoulder_gaps.extend([(upper.tail-forearm.head).length,(forearm.tail-hand.head).length])
    support_errors.append((support_initial-rig.pose.bones["hold_paw"].head).length)
    if frame >=182:
        paw_center=rig.pose.bones["open_paw"].matrix @ Vector((0,.008,0))
        intended_center=hinge.matrix_world @ Vector((.47,-.039-.071,.937*.479+.049))
        contact_errors.append((paw_center-intended_center).length)
assert abs(angles[168])<1e-8
assert abs(math.degrees(angles[-1])+147)<1e-4
assert all(angles[i+1] <= angles[i]+1e-6 for i in range(len(angles)-1))
assert max(shoulder_gaps)<1e-5, max(shoulder_gaps)
assert max(support_errors)<1e-5, max(support_errors)
assert max(contact_errors)<1e-5, max(contact_errors)
assert max(camera_drift)<1e-8
print(json.dumps(dict(total_frames=len(angles),first_movement_frame=next(i+1 for i,a in enumerate(angles) if a < -.000001),opened_degrees=abs(math.degrees(angles[-1])),max_joint_gap=max(shoulder_gaps),max_grip_path_deviation=max(contact_errors),max_support_drift=max(support_errors),max_camera_drift=max(camera_drift)), indent=2))
