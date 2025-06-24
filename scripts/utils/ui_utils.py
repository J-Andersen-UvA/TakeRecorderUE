# scripts/utils/ui_utils.py

import os, sys, unreal, uuid
from typing import Callable

# ─── Bootstrap so `import scripts.*` works ────────────────────────────────────
project_dir = unreal.SystemLibrary.get_project_directory().rstrip(os.sep)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

class ButtonRegistry:
    _callbacks = {}
    @classmethod
    def register(cls, button_id: str, callback: Callable):
        cls._callbacks[button_id] = callback
    @classmethod
    def execute(cls, button_id: str):
        cb = cls._callbacks.get(button_id)
        if cb:
            try: cb()
            except Exception as e: unreal.log_error(f"[ButtonRegistry] {button_id} error: {e}")
        else:
            unreal.log_error(f"[ButtonRegistry] No callback for '{button_id}'")

class Button:
    def __init__(self,
                 menu_path: str,
                 section_name: str,
                 label: str,
                 callback: Callable,
                 tooltip: str = "",
                 overwrite: bool = False,
                 tab: bool = False):
        """
        :param menu_path:    "LevelEditor.MainMenu" (to create a new tab)
                             or "LevelEditor.MainMenu.YourTab" (to add under existing)
        :param section_name: e.g. "ToucanToolsSection"
        :param label:        visible text (for the tab if tab=True, otherwise for the button)
        :param callback:     zero-arg Python function (only used if tab=False)
        :param tooltip:      hover text
        :param overwrite:    if True, remove any existing button with same ID
        :param tab:          if True *only* creates the top-level tab, no button entry
        """
        menus = unreal.ToolMenus.get()
        parts = menu_path.split(".")

        # 1) Handle top-level tab creation
        if len(parts) == 2:
            main_menu = menus.extend_menu(menu_path)  # LevelEditor.MainMenu
            # IMPORTANT: use keyword args in the correct order!
            sub_menu = main_menu.add_sub_menu(
                owner=main_menu.get_name(),    # e.g. "LevelEditor.MainMenu"
                section_name=section_name,          # your section ID in the parent
                name=label.replace(" ", "_"),  # INTERNAL tab name
                label=label,                   # VISIBLE tab name
                tool_tip=tooltip               # hover text
            )
            menus.refresh_all_widgets()

            # if user only wanted a tab, stop here:
            if tab:
                return

            # otherwise, fall through to create a button _inside_ this submenu
            menu = sub_menu

        else:
            # 2) Not a new top-level tab: extend an existing menu
            menu = menus.extend_menu(menu_path)

        # 3) Make sure our section exists
        menu.add_section(section_name, section_name)

        # 4) Register callback and determine our button ID
        self.button_id = f"Btn_{section_name}_{label}".replace(" ", "_")
        ButtonRegistry.register(self.button_id, callback)

        # 5) Optionally remove an old entry
        if overwrite:
            try:
                menu.remove_menu_entry(section_name, self.button_id)
            except Exception:
                pass

        # 6) Build the button entry
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

        # 7) Add it under our section and refresh
        menu.add_menu_entry(section_name, entry)
        menus.refresh_all_widgets()
