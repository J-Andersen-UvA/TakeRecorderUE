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

def bake_active_livelink_into_actor_anim_bp(actor: unreal.Actor, source_var_map : dict) -> bool:
    try:
        skel = _find_skel_comp(actor)
        bp_asset, cdo = _load_anim_bp_and_cdo(skel)
        subjects = _gather_live_link_subjects()
        if not subjects:
            unreal.log_warning("No enabled LiveLink subjects")
            return False

        assignments = _detect_sources(subjects, source_var_map)
        if not assignments:
            unreal.log_error("Found LiveLink sources, but none matched your SOURCE_VAR_MAP")
            return False

        # TODO: there is no has_any_property() in CDO, so this is commented out. For now lets pray
        # verify all your expected variables exist on the CDO
        # for var in assignments:
        #     if not cdo.has_any_property(var):
        #         raise RuntimeError(f"Blueprint has no variable '{var}'")

        # now set them
        for var, sub_name in assignments.items():
            print(f"Binding {var} to subject '{sub_name}'")
            cdo.set_editor_property(var, sub_name)

        # compile & save
        unreal.BlueprintEditorLibrary.compile_blueprint(bp_asset)
        unreal.EditorAssetLibrary.save_asset(bp_asset.get_path_name())
        unreal.log("[LiveLinkTools] Successfully bound subjects: " + str(assignments))
        return True

    except Exception as e:
        unreal.log_error(f"[LiveLinkTools] {e}")
        return False

def _find_skel_comp(actor):
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    if not comp:
        raise RuntimeError(f"No SkeletalMeshComponent on {actor.get_name()}")
    return comp

def _load_anim_bp_and_cdo(skel_comp):
    anim_cls = skel_comp.get_editor_property("anim_class")
    full_path = anim_cls.get_path_name() if anim_cls else None
    base_path, suffix = full_path.rsplit(".", 1) if full_path else (None, None)
    bp_name = suffix[:-2] if suffix.endswith("_C") else suffix
    bp_asset_path = base_path + "." + bp_name
    bp_asset = unreal.load_asset(bp_asset_path)
    gen_class_path = bp_asset_path + "_C"
    bp_class = unreal.load_object(None, gen_class_path)
    cdo = unreal.get_default_object(bp_class)
    print(f"Loaded AnimBP: {bp_asset_path}, CDO: {cdo}")
    return bp_asset, cdo

def _gather_live_link_subjects():
    return unreal.LiveLinkBlueprintLibrary.get_live_link_subjects(
        include_disabled_subject=False,
        include_virtual_subject=False
    )

def _detect_sources(subject_keys, source_var_map):
    """
    Returns a dict { BlueprintVarName: subject_name } 
    based on SOURCE_VAR_MAP.
    """
    result = {}
    for key in subject_keys:
        src_txt = unreal.LiveLinkBlueprintLibrary.get_source_type_from_guid(key.source)
        src_txt = str(src_txt)

        for predicate, var_name in source_var_map.items():
            if predicate(src_txt):
                print(f"Matched source '{src_txt}' to variable '{var_name}'")
                result[var_name] = key.subject_name
                break
    return result

# # example usage bake active_livelink_into_actor_anim_bp 
# actor = get_actor_by_shorthand("GlassesGuyRecord")

# SOURCE_VAR_MAP = {
#     lambda src_txt: "Vicon" in src_txt:        "ViconSubject",
#     lambda src_txt: "ARKit" in src_txt:        "phone1_SubjectLLF",
# }

# bake_active_livelink_into_actor_anim_bp(actor, SOURCE_VAR_MAP)