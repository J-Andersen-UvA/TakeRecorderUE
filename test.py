import scripts.recording.takeRecorder as takeRecorder
import unreal
import scripts.utils.editorFuncs as editorFuncs
# import assets_tools
# import assets
from typing import Dict, Any
import scripts.utils.popUp as popUp

# tk = takeRecorder.TakeRecorder()

# # Create an instance of EditorUtilityLibrary
# global_editor_utility = unreal.EditorUtilityLibrary()

# replay_actor = editorFuncs.get_actor_by_name("playLastActor")

# # Check if the actor reference was found
# if replay_actor is None:
#     raise ValueError("Actor 'playLastActor_C_1' not found in the current world.")

# # Load the animation asset and ensure it’s of type AnimationSequence
# animation_asset = unreal.load_asset("/Game/Cinematics/Anims/RPMAnims/Alphabet_ShogunPost_RPM")
# # animation_asset = unreal.load_asset('/Game/Cinematics/Anims/RPMAnims/PregnantPostProcessed')

# # Call the replay_anim function with the found actor and correct animation asset
# tk.replay_anim(
#     replay_actor=replay_actor,
#     anim=animation_asset
# )


def fetch_last_recording(take_recorder_panel):
    """
    Fetch last recording.

    Returns:
    - level_sequence (unreal.LevelSequence): The last recorded level sequence.
    """
    return take_recorder_panel.get_last_recorded_level_sequence()

def fetch_last_animation(take_recorder_panel):
    """
    Fetch last animation.

    Returns:
    - level_sequence (unreal.AnimSequence): The last recorded level sequence.
    """
    last_record = fetch_last_recording(take_recorder_panel)

    if last_record is None:
        return None, None

    last_record = last_record.get_full_name()
    unrealTake = last_record.replace("LevelSequence ", "")
    unrealScene = unrealTake.split(".")[1]
    unrealTake = unrealTake.split(".")[0]
    animLocation = unrealTake + "_Subscenes/Animation/GlassesGuyRecord" + "_" + unrealScene
    animation_asset = unreal.load_asset(animLocation)

    return animation_asset, animLocation



take_recorder_panel = (
    unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()
)

loca_1 = "/Game/Cinematics/Takes/2025-02-11/Scene_1_222_Subscenes/Animation/GlassesGuyRecord_Scene_1_222"
_, loca_2 = fetch_last_animation(take_recorder_panel)
popUp.show_popup_message("recordings equal?", f"{loca_1} == {loca_2}\n{loca_1 == loca_2}")

def print_all_actors():
    """
    Fetch an actor by name.

    Params:
    - name (str): The name of the actor to fetch.
    """
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        print(f"Actor found: {actor.get_name()}")

print_all_actors()