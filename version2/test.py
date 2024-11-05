import scripts.takeRecorder as takeRecorder
import unreal
import scripts.editorFuncs as editorFuncs
# import assets_tools
# import assets
from typing import Dict, Any

tk = takeRecorder.TakeRecorder()

# Create an instance of EditorUtilityLibrary
global_editor_utility = unreal.EditorUtilityLibrary()

replay_actor = editorFuncs.get_actor_by_name("playLastActor")

# Check if the actor reference was found
if replay_actor is None:
    raise ValueError("Actor 'playLastActor_C_1' not found in the current world.")

# Load the animation asset and ensure it’s of type AnimationSequence
animation_asset = unreal.load_asset("/Game/Cinematics/Anims/RPMAnims/Alphabet_ShogunPost_RPM")
# animation_asset = unreal.load_asset('/Game/Cinematics/Anims/RPMAnims/PregnantPostProcessed')

# Call the replay_anim function with the found actor and correct animation asset
tk.replay_anim(
    replay_actor=replay_actor,
    anim=animation_asset
)


def fetch_last_recording(take_recorder_panel):
    """
    Fetch last recording.

    Returns:
    - level_sequence (unreal.LevelSequence): The last recorded level sequence.
    """
    return take_recorder_panel.get_last_recorded_level_sequence()



take_recorder_panel = (
    unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()
)

print(fetch_last_recording(take_recorder_panel).get_full_name())