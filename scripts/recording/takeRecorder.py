import unreal
import scripts.utils.UEFileManagerScript as UEFileManager
import scripts.utils.popUp as popUp
import scripts.state.stateManagerScript as stateManagerScript
import scripts.export.exportAndSend as exportAndSend
import re

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
        self.stateManager = stateManager

        unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
        self.take_recorder_panel = unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()
        self.levelSequence = unreal.LevelSequence
        self.metadata = self.take_recorder_panel.get_take_meta_data()
        self.UEFileFuncs = UEFileManager.UEFileFunctionalities()        

    # make it callable
    def __call__(self):
        return True

    @staticmethod
    def _sanitize_name(name: str, replacement: str = "_") -> str:
        if name is None:
            return ""

        # any character _not_ in A–Z a–z 0–9 space _ or -
        _SANITIZE_RE = re.compile(r'[^0-9A-Za-z _-]')
        return _SANITIZE_RE.sub(replacement, name)

    def get_slate(self) -> str:
        """Retrieve the slate information from the take recorder panel."""
        self.metadata = self.take_recorder_panel.get_take_meta_data()
        return self.metadata.get_slate()

    def set_slate_name(self, name : str) -> None:
        """
        Sets the slate name for the Take Recorder panel.
        
        :param name: The name to set as the slate.
        """
        clean_name = self._sanitize_name(name)
        self.metadata = self.take_recorder_panel.get_take_meta_data()
        self.metadata.set_slate(clean_name)

    def get_sources(self):
        """Retrieve the sources from the take recorder panel."""
        lala = unreal.TakeRecorderBlueprintLibrary().get_take_recorder_panel()
        return lala.get_sources()

    def get_slate_from_take(self) -> str:
        """Retrieve the slate information from the current take."""
        lala = unreal.TakeRecorderBlueprintLibrary().get_take_recorder_panel()
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
        if self.take_recorder_ready():
            self.take_recorder_panel.start_recording()
            return

    def stop_recording(self):
        """
        Stop recording.

        This function stops the recording process using the take recorder panel.
        """
        try:
            self.take_recorder_panel.stop_recording()
        except Exception as e:
            print(f"Error stopping recording: {e}")
            popUp.show_popup_message("Error stopping recording", f"Error stopping recording: {e}")

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

    def fetch_last_animation(self, actor_name="GlassesGuyRecord"):
        """
        Fetch last animation.

        Returns:
        - level_sequence (unreal.AnimSequence): The last recorded level sequence.
        """
        last_record = self.fetch_last_recording()

        if last_record is None:
            print("No last recording found, returning None None")
            return None, None

        last_record = last_record.get_full_name()
        unrealTake = last_record.replace("LevelSequence ", "")
        unrealScene = unrealTake.split(".")[1]
        unrealTake = unrealTake.split(".")[0]
        animLocation = unrealTake + f"_Subscenes/Animation/{actor_name}" + "_" + unrealScene
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
        err = self.take_recorder_panel.can_start_recording()
        print(f"Take Recorder readiness check: {err}")
        unreal.log_warning(f"Take Recorder is not ready to start recording because: {err}.")
        return not err or str(err).strip() == ""
    
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

    def export_animation(self, location, folder, gloss_name, actor_name="GlassesGuyRecord"):
        if not gloss_name:
            gloss_name = self.stateManager.get_gloss_name()
        print(f"Exporting last recording: {gloss_name}...")

        last_anim, location = self.fetch_last_animation(actor_name=actor_name)
        if last_anim is None:
            self.stateManager.flip_export_status()
            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            popUp.show_popup_message("replay", "[TakeRecorder.py] No last recording found")
            return False
        
        success, full_export_path = exportAndSend.export_animation(location, self.stateManager.folder, gloss_name)

        if not success:
            self.stateManager.flip_export_status()
            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            popUp.show_popup_message("Export Failed", f"[TakeRecorder.py] Export failed for {gloss_name}")
            return False

        print(f"Exporting last recording done: {gloss_name}\tPath: {location}")

        # Export fbx to Vicon PC
        exportAndSend.copy_paste_file_to_vicon_pc(
            source=full_export_path
        )

        return True

    def add_actor_to_take_recorder(self, actor: unreal.Actor):
        """
        Adds an actor to the Take Recorder as a source.
        """
        if not actor:
            unreal.log_error("No actor provided.")
            return

        # Grab source container
        sources = self.take_recorder_panel.get_sources()

        # Use the Actor-source helper
        new_source = unreal.TakeRecorderActorSource.add_source_for_actor(actor, sources)
        if new_source:
            unreal.log(f"Added '{actor.get_name()}' to Take Recorder sources.")
        else:
            unreal.log_error(f"Failed to add '{actor.get_name()}' to Take Recorder sources.")
