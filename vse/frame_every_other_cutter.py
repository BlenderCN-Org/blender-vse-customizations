import bpy

## Every Other Cutter
##
## Checker cut every other frame or every other group of n frames from a strip
## or every other strip or every other group of n strips from a strip group.
## Used for eliminating noise such as motion blur frames in repetitive renders.

# pseudocode sketch

def arrange_strips_by_time(strips, descending=False):
    return sorted(strips, lambda x: x.frame_start, reversed=descending)

def select_strip(strip, deselect=False):
    if not strip or not hasattr(strip, 'frame_start'):
        return
    strip.select = not deselect
    return strip

def deselect_strips():
    for strip in bpy.context.scene.sequence_editor.sequences_all:
        select_strip(strip, deselect=True)
    bpy.context.scene.sequence_editor.active_strip = None

def activate_lone_strip(strip):
    deselect_strips()
    select_strip(strip)
    bpy.context.scene.sequence_editor.active_strip = strip
    return strip

def remove_strip(strip):
    select_strip(strip)
    bpy.context.scene.sequence_editor.active_strip = strip
    # TODO non-ops method of removing sequence and strip data
    try:
        bpy.ops.sequencer.delete()
        return True
    except:
        raise Exception("Unable to delete strip - {0}".format(strip))
    return False

def every_other_group_cut(strips):
    if strips.type != list:
        return
    strips_remaining = []
    toggle = False
    arrange_strips_by_time(strips)
    deselect_strips()
    for strip in strips:
        if toggle:
            remove_strip(strip)
            strips_remaining.append(strip)
        toggle = not odds
    return strips_remaining

def copy_strip(strip, create_new=None, channel=None, frame_start=None):
    if not strip or not create_new:
        return
    path = strip.directory  # /!\ fails to load path for image sequence
    channel = strip.channel if not channel else channel
    frame_start = strip.frame_start if not frame_start else frame_start
    new_strip = create_new(name=strip.name, filepath=path, channel=channel, frame_start=frame_start)
    return new_strip

## Switch ops areas
# TODO: break out area ops exec into own script
def switch_area(area=bpy.context.area, area_type=None):
    if not area or not area_type or area.type == area_type:
        return
    try:
        old_type = area.type
        area.type = area_type
    except:
        raise Exception("Unknown area {0} or area type {1}".format(area, area_type))
    return old_type

def switch_areas_run_op(op, params=[]):
    """Run a contextual operation in the associated area"""

    # TODO: account for every ops attr
    ops_areas_map = {
        'view3d': 'VIEW_3D',
        'time': 'TIMELINE',
        'graph': 'GRAPH_EDITOR',
        'action': 'DOPESHEET_EDITOR',
        'nla': 'NLA_EDITOR',
        'image': 'IMAGE_EDITOR',
        'clip': 'CLIP_EDITOR',
        'sequencer': 'SEQUENCE_EDITOR',
        'node': 'NODE_EDITOR',
        'text': 'TEXT_EDITOR',
        'logic': 'LOGIC_EDITOR',
        'buttons': 'PROPERTIES',    # /!\ render, buttons, object and many other ops here
        'outliner': 'OUTLINER',
        'wm': 'USER',
        # other proposed maps
        'object': 'VIEW_3D',    # or 'PROPERTIES'?
        'material': 'VIEW_3D',  # or 'PROPERTIES'?
        'texture': 'VIEW_3D'    # or 'PROPERTIES'?
    }

    # determine run area and swap areas
    op_id = op.idname_py()
    op_key = op_id.split('.', 1)[0]
    new_area = ops_areas_map[op_key]
    old_area = switch_area(area_type=new_area)

    # run op
    if params:
        op(*params)
    else:
        op()

    # revert to original area
    switch_area(area_type=old_area)

    return 0

def switch_areas_run_method(area, method, params=[]):
    """Run a method with the current context switched to the target area"""
    old_area = switch_area(area_type=area)
    res = None
    res = method(*params) if params else method()
    switch_area(area_type=old_area)
    return res

## END switch ops areas

def duplicate_strip(strip):
    activate_lone_strip(strip)
    switch_areas_run_op(bpy.ops.sequencer.duplicate)
    new_strip = bpy.context.scene.sequence_editor.active_strip
    return new_strip

def strip_creator(strip):
    # store method for creating substrip copies of same strip type
    strip_type = strip.type.lower()
    try:
        create_strip = getattr(bpy.context.scene.sequence_editor.sequences, 'new_{0}'.format(strip_type))
    except:
        raise Exception("unable to find a new strip creation method on {0}".format(strip))
    return create_strip

def every_other_frame_cut(strip=bpy.context.scene.sequence_editor.active_strip, interval=1):
    if not strip or not hasattr(strip, 'frame_start') or interval < 1:
        return
    strips_remaining = []
    toggle = False
    deselect_strips()
    activate_lone_strip(strip)
    bpy.context.scene.frame_current = strip.frame_start

    # subcut strip and checker cut
    # TODO verify range includes cut within final incomplete interval
    # TODO allow reverse (neg) strip traversal and checker cutting
    substrips_count = int(strip.frame_final_duration / interval)   # how many frame groups

    strips = [strip]

    for substrip_i in range(substrips_count):

        # Procedure to keep moving start frame of original strip back
        # while modifying duplicate substrips:
        # 1. move interval frames along original strip
        # 2. duplicate original strip to "first" substrip
        # 3. move start frame of original strip back to interval
        # 4. set last frame of "first" substrip to current (intervaled) frame
        # 5. move interval frames along original strip
        # 6. move start frame of original strip back to doubled interval
        # 7. duplicate original strip to "second" substrip
        # 8. set last frame of "second" substrip to current (double intervaled) frame
        # 9. remove the "second" substrip
        # TODO condense this by toggling checkercut param each iteration

        # move ahead interval frames
        bpy.context.scene.frame_current += interval

        # copy strip as first strip
        first_strip = duplicate_strip(strip)
        strips.append(first_strip)

        # cut first strip along interval
        strip.frame_start = bpy.context.scene.frame_current
        first_strip.frame_final_duration = bpy.context.scene.frame_current - first_strip.frame_start

        # move ahead interval frames
        bpy.context.scene.frame_current += interval

        # copy strip as second strip
        second_strip = duplicate_strip(first_strip)
        strips.append(second_strip)

        # cut second strip along doubled interval
        strip.frame_start = bpy.context.scene.frame_current
        second_strip.frame_final_duration = bpy.context.scene.frame_current - second_strip.frame_start

        # select second strip
        activate_lone_strip(second_strip)

        # remove second strip
        bpy.ops.sequencer.remove()
        deselect_strips()

        # only one more noncut strip left
        #if bpy.context.scene.frame_current + interval > strip.frame_start + strip.length:
            # done cutting
        #    break

        continue

strips = [strip for strip in bpy.context.scene.sequence_editor.sequences if strip.select]
len(strips) == 1 and every_other_frame_cut(bpy.context.scene.sequence_editor.active_strip)
#len(strips) > 1 and every_other_group_cut(bpy.context.scene.sequence_editor.sequences)
