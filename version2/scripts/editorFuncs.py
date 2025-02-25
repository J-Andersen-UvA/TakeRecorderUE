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

def open_anim_in_window(path):
    """
    Open an animation asset in a new window.

    Params:
    - path (str): The path to the animation asset.
    """
    animation_asset = unreal.EditorAssetLibrary.load_asset(path)
    if animation_asset:
        unreal.AssetToolsHelpers.get_asset_tools().open_editor_for_assets([animation_asset])
        editor_window = unreal.SystemLibrary.get_editor_main_window()
        if editor_window:
            editor_window.resize(1920, 1080)
            editor_window.set_focus()
    else:
        print(f"Failed to load animation asset: {path}")
