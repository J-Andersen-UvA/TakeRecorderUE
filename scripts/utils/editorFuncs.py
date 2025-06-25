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
    
def load_and_apply_livelink_preset(path: str = "/Game/viconPC.viconPC") -> bool:
    preset = unreal.load_asset(path)
    if not preset:
        unreal.log_error(f"[LiveLink] Couldn’t find preset at '{path}'")
        return False

    # 1) Try to apply; will fail if sources already exist
    if not preset.apply_to_client():
        unreal.log_warning("[LiveLink] First apply failed—clearing existing preset entries and retrying…")
        # 2) On failure, call the “recreate” variant to force-overwrite
        if preset.add_to_client(recreate_presets=True):
            unreal.log("[LiveLink] Succeeded on retry with recreate_presets=True")
            return True
        else:
            unreal.log_error("[LiveLink] Still failed to apply preset after retry")
            return False

    unreal.log(f"[LiveLink] Applied preset: {path}")
    return True

def bake_active_livelink_into_actor_anim_bp(
    actor: unreal.Actor,
    variable_name: str = "LiveLinkSubjectName"
) -> bool:
    """
    Finds the given Actor in the level, locates its Anim BP, sets that BP’s
    default `variable_name` on the Class Default Object to the first enabled
    LiveLink subject, then compiles & saves the Blueprint asset.

    Returns True on success, False on any error.
    """
    # 1) Get the SkeletalMeshComponent
    skel_comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    if not skel_comp:
        unreal.log_error(f"[LiveLinkTools] No SkeletalMeshComponent on '{actor.get_name()}'")
        return False

    # 2) Read the Anim BP class
    anim_class = skel_comp.get_editor_property("anim_class")
    if not anim_class:
        unreal.log_error(f"[LiveLinkTools] '{actor.get_name()}' has no Anim BP assigned")
        return False

    # 3) Derive the Blueprint asset path (strip "_C")
    full_path = anim_class.get_path_name()                  # "/Game/Path/MyBP.MyBP_C"
    base_path, suffix = full_path.rsplit(".", 1)
    bp_name = suffix[:-2] if suffix.endswith("_C") else suffix
    bp_asset_path = f"{base_path}.{bp_name}"                # "/Game/Path/MyBP.MyBP"

    # 4) Load the Blueprint asset
    bp_asset = unreal.load_asset(bp_asset_path)
    if not bp_asset or not isinstance(bp_asset, unreal.Blueprint):
        unreal.log_error(f"[LiveLinkTools] Could not load Blueprint asset '{bp_asset_path}'")
        return False

    # 5) Get the first enabled LiveLink subject
    subjects = unreal.LiveLinkBlueprintLibrary.get_live_link_enabled_subject_names(False)
    if not subjects:
        unreal.log_warning("[LiveLinkTools] No enabled LiveLink subjects")
        return False
    subject = subjects[0]

    # 6) Load the generated class and its CDO
    gen_class_path = f"{bp_asset_path}_C"
    bp_class = unreal.load_object(None, gen_class_path)
    if not bp_class:
        unreal.log_error(f"[LiveLinkTools] Could not load generated class '{gen_class_path}'")
        return False
    cdo = unreal.get_default_object(bp_class)

    # 7) Verify the CDO has the variable and set it
    try:
        cdo.set_editor_property(variable_name, subject)
    except Exception as e:
        unreal.log_error(f"[LiveLinkTools] Failed to set '{variable_name}' on {bp_name} : {e}")
        return False

    # 8) Compile & save the Blueprint asset
    unreal.BlueprintEditorLibrary.compile_blueprint(bp_asset)
    unreal.EditorAssetLibrary.save_asset(bp_asset_path)
    unreal.log(f"[LiveLinkTools] Set default '{variable_name}' = '{subject}' on '{bp_name}'")

    return True
