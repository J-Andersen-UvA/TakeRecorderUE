from scripts.utils.ui_utils import Button
import scripts.utils.editorFuncs as editorFuncs

Button(
    menu_path="LevelEditor.MainMenu.ToucanTools",
    section_name="LiveLink",
    label="Load Default LiveLink Preset",
    callback=lambda: editorFuncs.load_and_apply_livelink_preset(),
    tooltip="Load & apply your default Live Link preset",
    overwrite=True
)
