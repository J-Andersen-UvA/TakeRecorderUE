from scripts.utils.ui_utils import Button
import scripts.utils.editorFuncs as editorFuncs
from scripts.config.params import Config

params = Config()
actor = editorFuncs.get_actor_by_shorthand(params.actor_name_shorthand)


# 1) Create a brand-new tab called “ToucanTools”
Button(
    menu_path="LevelEditor.MainMenu",
    section_name="ToucanToolsSection",
    label="ToucanTools",
    callback=lambda: None,
    tooltip="I asked my bird if it could multitask. It said, “Toucan!”",
    overwrite=True,
    tab=True  # <== this makes it a tab, not a button
)

Button(
    menu_path="LevelEditor.MainMenu.ToucanTools",
    section_name="LiveLink",
    label="Load Default LiveLink Preset",
    callback=lambda: editorFuncs.load_and_apply_livelink_preset(),
    tooltip="Load & apply your default Live Link preset",
    overwrite=True
)

Button(
    menu_path="LevelEditor.MainMenu.ToucanTools",
    section_name="LiveLinkSection",
    label="Bake LiveLink to AnimBP",
    callback=lambda: editorFuncs.bake_active_livelink_into_actor_anim_bp(actor, variable_name="Vicon Subject"),
    tooltip="Set the RecordingActor’s AnimBP to use the current LiveLink source by default",
    overwrite=True
)
