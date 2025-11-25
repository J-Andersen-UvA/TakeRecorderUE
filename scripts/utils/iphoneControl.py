import unreal

def open_iphone_control_menu(path = "/Game/BPs/EUW_LLFPhoneStatus.EUW_LLFPhoneStatus"):
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    widget = unreal.load_object(None, path)
    subsystem.spawn_and_register_tab(widget)
