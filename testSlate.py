import unreal

# lala = unreal.TakeMetaData()

# lala.unlock()

# lala.set_slate("lala")
# lala.set_take_number(1)

# print(lala.get_slate())


# tk = unreal.TakeRecorderBlueprintLibrary()
# unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
# panel = unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()

# metadata = panel.get_take_meta_data()
# sourcelist = panel.get_sources()
# levelsequence = panel.get_level_sequence()

# # trp = unreal.TakeRecorderPanel()

# # print(trp.get_take_meta_data())

# tkparama = unreal.TakeRecorderProjectParameters()

# dirpath = unreal.DirectoryPath()
# dirpath.path = "/Game"

# tkparama.default_slate = "lala"
# tkparama.root_take_save_dir = dirpath

# tkparam = unreal.TakeRecorderParameters()

# # tkparam.set_editor_properties({"default_slate": "lala"})
# # tkparam.set_editor_properties({"root_take_save_dir": "/Game"})


# # tk.start_recording(levelsequence, sourcelist, metadata, tkparam)

# # tkSimple = unreal.TakeRecorderPanel()
# # tkSimple.start_recording()

# #start record


class TakeRecordera:
    

    def __init__(self):
        unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
        self.start_recording = (
            unreal.TakeRecorderBlueprintLibrary.start_recording
        )
        self.get_take_recorder_panel = (
            unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()
        )
        self.get_level_sequence = (
            self.get_take_recorder_panel.get_level_sequence()
        )
        self.get_sources = (
            self.get_take_recorder_panel.get_sources()
        )
        self.metadata = (
            self.get_take_recorder_panel.get_take_meta_data()
        )
        
        self.get_level_sequence.find_meta_data_by_class(unreal.TakeMetaData.get_class(unreal.Actor.get_class("Jesse")))
        
        
        
        # Example usage
        self.projectParameters = unreal.TakeRecorderProjectParameters(
            default_slate="lala",
            root_take_save_dir=unreal.DirectoryPath(path="/Game"),
            take_save_dir="/Game",
        )
        
        self.parameters = unreal.TakeRecorderParameters()

        
        
        self.start_recording(self.get_level_sequence, self.get_sources, self.metadata, self.parameters)


TakeRecordera()