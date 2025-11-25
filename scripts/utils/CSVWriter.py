from csv import writer
import unreal
import os
import scripts.utils.editorFuncs as editorFuncs
from scripts.config.params import Config
import scripts.state.stateManagerScript as stateManagerScript
import scripts.utils.popUp as popUp
from scripts.utils.logger import RecordingLog, guess_gloss_from_filename
_log = RecordingLog()

params = Config()

class LiveLinkCSVManagerWrapper:
    def __init__(self, statemanager):
        self.state_manager = statemanager
        self.manager = unreal.get_editor_subsystem(
            unreal.LiveLinkFaceCSVWriterManager
        )
        if not self.manager:
            unreal.log_error("[CSVWriter] LiveLinkFaceCSVWriterManager not found")
            raise RuntimeError

        # 1) set the export path from the state manager
        self.set_save_folder(self.state_manager.folder)

        # 2) writers for each device + active writer
        #    (you probably create them from EUW / BP using CreateWriterForDevice
        #     and CreateActivePhoneWriter; Python can assume they exist)
        self.last_file_paths = []  # list of all exported csvs

    def set_save_folder(self, folder: str):
        folder = os.path.normpath(folder or "")
        os.makedirs(folder, exist_ok=True)
        self.manager.set_export_path(folder)
        unreal.log(f"[CSVWriter] Export path set to: {folder}")
        return folder

    def start_recording(self, gloss: str):
        """
        Called when recording starts. Optionally use 'gloss'
        to adjust filenames before starting.
        """
        self.manager.apply_name_to_filenames(gloss)
        ok = self.manager.start_recording()
        unreal.log(f"[CSVWriter] Manager start_recording -> {ok}")
        return ok

    def stop_and_export(self, gloss: str):
        self.manager.stop_recording()
        ok = self.manager.export_all_files()

        self.last_file_paths = []
        exported = list(self.manager.last_exported_files)

        if not exported:
            unreal.log_warning("[CSVWriter] No exported files reported by plugin.")

        self.last_file_paths = []

        for path in exported:
            path = os.path.normpath(path)

            if os.path.exists(path):
                self.last_file_paths.append(path)
            else:
                unreal.log_error(f"[CSVWriter] Exported file missing: {path}")

        return ok

    def check_last_file(self):
        if not self.last_file_paths:
            popUp.show_popup_message("[CSVWriter] Error", "No CSV files recorded or exported.")
            return None
        
        results = []
        for path in self.last_file_paths:
            # If it is the switches CSV, check for minimum rows 2
            if path.endswith("_Switches.csv"):
                ok = self.check_file_minimum_rows(path, min_rows=2)
            else:
                ok = self.check_file_minimum_rows(path)
            results.append((path, ok))
        
        return results      # returns list of (path, True/False)
        
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
