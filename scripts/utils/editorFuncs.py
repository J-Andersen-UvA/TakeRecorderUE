import unreal

def get_actor_by_name(name):
    """
    Fetch an actor by name.

    Params:
    - name (str): The name of the actor to fetch.
    """
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if name in actor.get_name():
            return actor
    return None

def get_actor_by_shorthand(short_name):
    """
    Fetch an actor by shorthand name.

    Params:
    - short_name (str): The shorthand name of the actor to fetch.
    """
    found = []
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if short_name in actor.get_name():
            found.append(actor)

    if len(found) == 1:
        return found[0]
    elif len(found) > 1:
        print(f"Multiple actors found with shorthand '{short_name}': {[actor.get_name() for actor in found]}")
        print(f"Returning the first one: {found[0].get_name()}")
        return found[0]

    print(f"No actor found with shorthand '{short_name}'")
    return None
    
def load_and_apply_livelink_preset(path: str = '/Game/viconPC.viconPC') -> bool:
    """
    Load a Live Link Preset asset at the given content path
    (e.g. '/Game/LiveLinkPresets/MyDefaultPreset.MyDefaultPreset')
    and apply it (removing any previous sources/subjects).
    """
    preset = unreal.load_asset(path)
    if not preset:
        unreal.log_error(f"[LiveLink] Couldn’t find preset asset at '{path}'")
        return False

    # apply_to_client() replaces all sources and subjects with those in the preset
    success = preset.apply_to_client()
    if success:
        unreal.log(f"[LiveLink] Applied Live Link preset: {path}")
    else:
        unreal.log_error(f"[LiveLink] Failed to apply preset: {path}")
    return success