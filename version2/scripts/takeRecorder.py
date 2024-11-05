import unreal
import scripts.UEFileManagerScript as UEFileManager

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

    def __init__(self):
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
