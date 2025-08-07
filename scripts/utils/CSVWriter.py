import unreal
import scripts.utils.editorFuncs as editorFuncs
from scripts.config.params import Config
import scripts.state.stateManagerScript as stateManagerScript
params = Config()

class LiveLinkFaceCSVWriterComponent:
    """
    Custom component to write Live Link Face data to CSV files.
    """

    def __init__(self, statemanager : stateManagerScript.StateManager, subj_name: str = "iPhone"):
        super().__init__()
        # Find the Actor in your level that has the CSV‐writer component
        my_actor = editorFuncs.get_actor_by_name(params.actor_name)
        if not my_actor:
            unreal.log_error("Actor not found!")
            raise RuntimeError

        self.CSVWriterComp = my_actor.get_component_by_class(unreal.LiveLinkFaceCSVWriterComponent)

        self.CSVWriterComp.set_subject_name(unreal.Name(subj_name))
        self.CSVWriterComp.set_filename("MyCaptureData")
        self.set_save_folder(statemanager.folder)
    
    def start_recording(self):
        success = self.CSVWriterComp.start_recording()
        if success:
            unreal.log("[CSVWriter] Recording started")
        else:
            unreal.log_error("[CSVWriter] Failed to start recording")

    def stop_recording(self):
        success = self.CSVWriterComp.stop_recording()
        if success:
            unreal.log("[CSVWriter] Recording stopped")
        else:
            unreal.log_error("[CSVWriter] Failed to stop recording")
    
    def export_file(self):
        success = self.CSVWriterComp.export_file()
        if success:
            unreal.log("[CSVWriter] CSV file exported successfully")
        else:
            unreal.log_error("[CSVWriter] Failed to export CSV file")
        return success

    def set_save_folder(self, folder: str):
        self.CSVWriterComp.set_save_folder(folder)
        unreal.log(f"[CSVWriter] Save folder set to: {folder}")
        return folder
    
    def set_filename(self, filename: str):
        self.CSVWriterComp.set_filename(filename)
        unreal.log(f"[CSVWriter] Filename set to: {filename}")
        return filename
