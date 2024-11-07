import unreal
import scripts.UEFileManagerScript as UEFileManager
import scripts.popUp as popUp
import os
import scripts.stateManagerScript as stateManagerScript
import scripts.exportAndSend as exportAndSend

class TakeRecorder:
    """
    Class for recording functionality in Unreal Engine.

    This class provides methods to start/stop recording and fetch the last recorded sequence and its assets.

    Methods:
    - __init__(self): Constructor method to initialize the TakeRecorder.
    - start_recording(self): Start recording.
    - stop_recording(self): Stop recording.
    - fetch_last_recording(self): Fetch last recording.
    - fetch_last_recording_assets(self): Fetch last recording assets.
    - set_name_take(self, name): Set name for the recording take.

    - get_slate(self): Get the current slate str
    - get_sources(self): Get the take recorder sourcs for the
    current take recorder panel
    - get_slate_from_take(self): get the slate from the take
    - is_recording(self): check if we are recording currently
    """

    def __init__(self, stateManager):
        unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
        self.take_recorder_panel = (
            unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()
        )

        # a = unreal.LayersSubsystem()
        # self.world = a.get_world()
        self.levelSequence = unreal.LevelSequence
        self.metadata = unreal.TakeMetaData

        self.UEFileFuncs = UEFileManager.UEFileFunctionalities()
        self.TakeRecorderBPL = unreal.TakeRecorderBlueprintLibrary()
        
        self.stateManager = stateManager

    # make it callable
    def __call__(self):
        return True

    def get_slate(self) -> str:
        """Retrieve the slate information from the take recorder panel."""
        lala = self.TakeRecorderBPL.get_take_recorder_panel()
        return lala.get_take_meta_data().get_slate()

    def get_sources(self):
        """Retrieve the sources from the take recorder panel."""
        lala = self.TakeRecorderBPL.get_take_recorder_panel()
        return lala.get_sources()

    def get_slate_from_take(self) -> str:
        """Retrieve the slate information from the current take."""
        lala = self.TakeRecorderBPL.get_take_recorder_panel()
        lala.get_class()
        return unreal.TakeMetaData().get_slate()

    def is_recording(self) -> bool:
        """Check if recording is currently in progress."""
        return unreal.TakeRecorderBlueprintLibrary.is_recording()

    def start_recording(self):
        """
        Start recording.

        This function starts the recording process using the take recorder panel.
        """
        self.take_recorder_panel.start_recording()

    def stop_recording(self):
        """
        Stop recording.

        This function stops the recording process using the take recorder panel.
        """
        self.take_recorder_panel.stop_recording()

    def replay_last(self, replay_actor):
        """
        Start replaying.

        This function starts the replaying process using the take recorder panel.
        """
        # cur_level_sequence_actor.call_method(
        #     "Event Replay Recording", args=(self.fetch_last_recording(),)
        # )
        replay_actor.call_method("playThisAnim", args=(self.fetch_last_recording(),))
    
    def replay_anim(self, replay_actor, anim):
        """
        Start replaying.

        This function starts the replaying process using the take recorder panel.
        """
        replay_actor.call_method("playThisAnim", args=(anim,))

    def fetch_last_recording(self):
        """
        Fetch last recording.

        Returns:
        - level_sequence (unreal.LevelSequence): The last recorded level sequence.
        """
        return self.take_recorder_panel.get_last_recorded_level_sequence()
        # return self.take_recorder_panel.get_level_sequence()

    def fetch_last_animation(self):
        """
        Fetch last animation.

        Returns:
        - level_sequence (unreal.AnimSequence): The last recorded level sequence.
        """
        last_record = self.fetch_last_recording()

        if last_record is None:
            return None, None

        last_record = last_record.get_full_name()
        unrealTake = last_record.replace("LevelSequence ", "")
        unrealScene = unrealTake.split(".")[1]
        unrealTake = unrealTake.split(".")[0]
        animLocation = unrealTake + "_Subscenes/Animation/GlassesGuyRecord" + "_" + unrealScene
        animation_asset = unreal.load_asset(animLocation)

        return animation_asset, animLocation

    def fetch_last_recording_assets(self):
        """
        Fetch last recording assets.

        This function fetches the assets recorded in the last recording session.

        Returns:
        - files_list (list): A list of file names of assets recorded in the last session.
        """
        # Fetch last recording path in UE path form
        anim_dir = self.fetch_last_recording().get_path_name()
        anim_dir = anim_dir.split(".")[0] + "_Subscenes/Animation/"
        project_path = self.UEFileFuncs.get_project_path()

        return self.UEFileFuncs.fetch_files_from_dir_in_project(
            anim_dir, project_path, mode="UE"
        )

    def take_recorder_ready(self):
        """
        Check if the take recorder is ready.

        This function checks if the take recorder panel is ready for recording.

        Returns:
        - ready (bool): True if the take recorder is ready, False otherwise.
        """
        print(self.take_recorder_panel.can_start_recording())
        return self.take_recorder_panel.can_start_recording()
    
    def error_test(self):
        """
        Check if the take recorder is ready.

        This function checks if the take recorder panel is ready for recording.

        Returns:
        - ready (bool): True if the take recorder is ready, False otherwise.
        """
        print("Error Test")
        popUp.show_popup_message("Error Test", "This is a pop-up message from Unreal Python!")
        return False

    def export_animation(self, location, folder, gloss_name):
        glosName = self.stateManager.get_gloss_name()
        print(f"Exporting last recording: {glosName}...")

        last_anim, location = self.fetch_last_animation()
        if last_anim is None:
            popUp.show_popup_message("replay", "No last recording found")
            self.stateManager.flip_export_status()
            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            return False
        
        self.rename_last_recording(self.stateManager.folder, glosName)
        exportAndSend.export_animation(location, self.stateManager.folder, glosName)

        print(f"Exporting last recording done: {glosName}\tPath: {location}")

        return True

    def rename_last_recording(self, cur_path, gloss_name, keepLastRecording=True):
        if not keepLastRecording:
            return

        print(f"Last recording: {gloss_name}\tPath: {cur_path}\tGoing to rename it...")
        # Check if last path already exists and rename it to _old_{1} if it does
        complete_path = cur_path + "\\" + gloss_name + ".fbx"
        if os.path.exists(complete_path):
            print(f"File already exists: {complete_path}")
            i = 1
            old_path = cur_path + "\\" + gloss_name + f"_old_{i}.fbx"
            while os.path.exists(old_path):
                print(f"Old path already exists: {old_path}")
                i += 1
                old_path = cur_path + "\\" + gloss_name + f"_old_{i}.fbx"
            print(f"Renaming to: {old_path}")
            os.rename(complete_path, old_path)

