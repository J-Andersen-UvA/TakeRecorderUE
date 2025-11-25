from scripts.utils.ui_utils import Button
import scripts.utils.editorFuncs as editorFuncs
from scripts.config.params import Config
from scripts.utils.iphoneControl import open_iphone_control_menu

params = Config()
actor = editorFuncs.get_actor_by_shorthand(params.actor_name_shorthand)

SOURCE_VAR_MAP = {
    lambda src_txt: "Vicon" in src_txt:        "ViconSubject",
    lambda src_txt: "ARKit" in src_txt:        "phone1_SubjectLLF",
}


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
    section_name="LiveLink",
    label="Bake LiveLink to AnimBP",
    callback=lambda: editorFuncs.bake_active_livelink_into_actor_anim_bp(actor, SOURCE_VAR_MAP),
    tooltip="Set the RecordingActor’s AnimBP to use the current LiveLink source by default",
    overwrite=True
)

Button(
    menu_path="LevelEditor.MainMenu.ToucanTools",
    section_name="iPhones",
    label="Open iPhone Control Menu",
    callback=open_iphone_control_menu,
    tooltip="Open the iPhone control menu",
    overwrite=True
)
