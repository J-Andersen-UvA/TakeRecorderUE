# scripts/utils/ui_utils.py

import os
import sys
import unreal
from typing import Callable

# ──────────────────────────────────────────────────────────────────────────────
# Make sure "scripts/" (which lives at ProjectDir/scripts) is on sys.path
project_dir = unreal.SystemLibrary.get_project_directory().rstrip(os.sep)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    unreal.log(f"[ui_utils] added project directory to sys.path: {project_dir}")
# ──────────────────────────────────────────────────────────────────────────────

class ButtonRegistry:
    _callbacks = {}
    @classmethod
    def register(cls, button_id: str, callback: Callable):
        cls._callbacks[button_id] = callback
    @classmethod
    def execute(cls, button_id: str):
        cb = cls._callbacks.get(button_id)
        if cb:
            try:
                cb()
            except Exception as e:
                unreal.log_error(f"[ButtonRegistry] Error in '{button_id}': {e}")
        else:
            unreal.log_error(f"[ButtonRegistry] No callback for '{button_id}'")

class Button:
    """
    :param menu_path:    e.g. "LevelEditor.MainMenu.Tools"
    :param section_name: e.g. "TakeRecorderSection"
    :param label:        visible text in the menu
    :param callback:     zero-arg Python callable to run on click
    :param tooltip:      optional hover text
    :param button_id:    OPTIONAL explicit internal name; if omitted, it's derived from section+label
    :param overwrite:    if True, remove any existing entry with the same button_id before adding
    """
    def __init__(
        self,
        menu_path: str,
        section_name: str,
        label: str,
        callback: Callable,
        tooltip: str = "",
        button_id: str = None,
        overwrite: bool = True
    ):
        # 1) Compute a deterministic ID if none provided
        self.button_id = button_id or f"Btn_{section_name}_{label}".replace(" ", "_")
        ButtonRegistry.register(self.button_id, callback)

        # 2) Grab the menu & ensure the section exists
        tm   = unreal.ToolMenus.get()
        menu = tm.extend_menu(menu_path)
        menu.add_section(section_name, section_name)

        # 3) If requested, remove any prior entry with the same name
        if overwrite:
            try:
                menu.remove_menu_entry(section_name, self.button_id)
            except Exception:
                pass

        # 4) Build the new entry
        entry = unreal.ToolMenuEntry(
            name=self.button_id,
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        entry.set_label(label)
        if tooltip:
            entry.set_tool_tip(tooltip)
        entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            custom_type=unreal.Name(""),
            string=(
                f"from scripts.utils.ui_utils import ButtonRegistry\n"
                f"ButtonRegistry.execute('{self.button_id}')"
            )
        )

        # 5) Add (or re-add) the entry into our section
        menu.add_menu_entry(section_name, entry)
        tm.refresh_all_widgets()


