import unreal
import os
import scripts.utils.editorFuncs as editorFuncs
from scripts.config.params import Config
import scripts.state.stateManagerScript as stateManagerScript
import scripts.utils.popUp as popUp
from scripts.utils.logger import RecordingLog, guess_gloss_from_filename
_log = RecordingLog()

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
            unreal.log_error("[CSVWriter] Actor not found!")
            raise RuntimeError

        self.CSVWriterComp = my_actor.get_component_by_class(unreal.LiveLinkFaceCSVWriterComponent)

        self.CSVWriterComp.set_subject_name(unreal.Name(subj_name))
        self.subj_name = subj_name
        self.set_save_folder(statemanager.folder)
        self.CSVWriterComp.set_filename("MyCaptureData")

        self.last_file_path = None
    
    def start_recording(self):
        success = self.CSVWriterComp.start_recording()
        if success:
            unreal.log("[CSVWriter] Recording started")
        else:
            unreal.log_error("[CSVWriter] Failed to start recording")

    def stop_recording(self):
        self.CSVWriterComp.stop_recording()

    def export_file(self):
        success = self.CSVWriterComp.export_file()
        if success:
            unreal.log("[CSVWriter] CSV file exported successfully")
            csv_path = self.last_file_path
            gloss = guess_gloss_from_filename(csv_path)
            _log.add_asset(gloss, "blendshape_csv", csv_path, machine="UE", status="ready")
        else:
            unreal.log_error("[CSVWriter] Failed to export CSV file")
        return success

    def set_save_folder(self, folder: str):
        # Normalize and ensure the directory exists before setting it
        folder = os.path.normpath(folder or "")
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            unreal.log_error(f"[CSVWriter] Could not create folder '{folder}': {e}")
        self.CSVWriterComp.set_save_folder(folder)
        unreal.log(f"[CSVWriter] Save folder set to: {folder}")
        return folder

    def set_filename(self, filename: str):
        self.CSVWriterComp.set_filename(filename)
        unreal.log(f"[CSVWriter] Filename set to: {filename}")
        folder = os.path.normpath(self.CSVWriterComp.get_save_folder())
        self.last_file_path = os.path.join(folder, f"{filename}.csv")
        return filename
    
    def check_last_file(self):
        """
        Check if the last exported file exists and return its path.
        """
        if not self.last_file_path:
            popUp.show_popup_message("[CSVWriter] Error", "No last_file_path set in CSVWriter.")
            return None
        
        return self.check_file_minimum_rows(self.last_file_path)
        
    def check_file_minimum_rows(self, file_path, min_rows: int = 50):
        """
        Check if the file CSV file has at least `min_rows` rows.
        """
        if not file_path:
            unreal.log_error("[CSVWriter] No file path set. Please export a file first.")
            return False
        
        file_path = os.path.normpath(file_path)
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                if len(lines) < min_rows:
                    popUp.show_popup_message("[CSVWriter] Warning", f"File '{file_path}' has only {len(lines)} rows. Check the iPhone.")
                    return False
                else:
                    unreal.log(f"[CSVWriter] File '{file_path}' has sufficient rows: {len(lines)}")
                    return True
        except Exception as e:
            unreal.log_error(f"[CSVWriter] Error checking file: {e}")
            return False

    # Doesnt work currently, needs to be fixed
    # def check_cur_subject_available(self):
    #     """
    #     Check if the subject is available in the Live Link system.
    #     """
    #     if self.CSVWriterComp.is_subject_available():
    #         unreal.log(f"[CSVWriter] Subject '{self.subj_name}' is available.")
    #         return True

    #     popUp.show_popup_message("[CSVWriter] Error", f"Subject '{self.subj_name}' is not available. Make sure the iPhone is connected and the Live Link Face app is running. Restart UE.")
    #     return False
