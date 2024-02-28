import unreal

class TakeRecorder:
    def __init__(self):
        unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
        self.take_recorder_panel = unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()
    
    def start_recording(self):
        self.take_recorder_panel.start_recording()

    def stop_recording(self):
        self.take_recorder_panel.stop_recording()

    # def set_name_take(self):
        # Implement somehow

curTakeRec = TakeRecorder()
# curTakeRec.start_recording()
curTakeRec.stop_recording()
