import unreal


class UEFileFunctionalities:
    """
    Class for Unreal Engine file functionalities.

    This class provides methods to interact with files and directories within an Unreal Engine project.

    Methods:
    - get_all_files_in_directory(self, directory): Get all files from a single directory (non-recursively).
    - get_project_path(self): Get the project path.
    - fetch_files_from_dir_in_project(self, dir, project_path): Fetch files from a directory in the project.
    """

    def get_all_files_in_directory(self, directory):
        """
        Get all files from a single directory (non-recursively).

        Args:
        - directory (str): The directory path.

        Returns:
        - files_list (list): A list of file names in the directory.
        """
        files_list = []

        # Check if the directory exists
        if os.path.exists(directory) and os.path.isdir(directory):
            # List all files in the directory
            files_list = [
                f
                for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f))
            ]
        else:
            print("Not a valid dir")

        return files_list

    def get_project_path(self):
        """
        Get the project path.

        Returns:
        - project_path (str): The project path in normal Windows path form.
        """
        project_path = unreal.Paths.project_dir().rstrip("/")
        return project_path.split("../")[-1]

    def fetch_files_from_dir_in_project(self, dir, project_path, mode="windows"):
        """
        Fetch files from a directory in the project.

        Args:
        - dir (str): The directory path within the project.
        - project_path (str): The project path.

        Returns:
        - files_list (list): A list of file names in the directory.
        """

        # Check if the UE path exists in the project
        if unreal.EditorAssetLibrary.does_directory_exist(dir + "/"):
            if "/Game" in dir:
                # Get the complete path in windows form
                complete_path = (
                    "C:/" + project_path + "/Content" + dir.split("/Game")[1]
                )
            else:
                complete_path = "C:/" + project_path + "/Content" + dir

            if mode == "windows":
                files = [
                    complete_path + "/" + file
                    for file in self.get_all_files_in_directory(complete_path)
                ]
            else:
                files = [
                    dir + file
                    for file in self.get_all_files_in_directory(complete_path)
                ]

            return files

        return []


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

        self.UEFileFuncs = UEFileFunctionalities()
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



#Get level sequence actor by name
def get_level_sequence_actor_by_name(name):
    level_sequence_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for level_sequence_actor in level_sequence_actors:
        if level_sequence_actor.get_name() == name:
            return level_sequence_actor
    return None

# Start the replay system
def start_replay_system(cur_level_sequence_actor):
    # call custom event from cur_level_sequence_actor to start replay system (Event Start Record)
    cur_level_sequence_actor.call_method("Event Start Record")

# Stop the replay system
def start_replay_recording(cur_level_sequence_actor, take_recorder):
    # call custom event from cur_level_sequence_actor to stop replay system (Event Stop Record)
    cur_level_sequence_actor.call_method("Event Replay Recording", args=(take_recorder.fetch_last_recording(), ))

tk = TakeRecorder()
# start_replay_system(get_level_sequence_actor_by_name("GlassesGuyRecord_C_1"))
stop_replay_system(get_level_sequence_actor_by_name("GlassesGuyRecord_C_1"), tk)



############################################
# Extra debug functions             #
############################################

# get all actor names in the level
# def get_all_actor_names_in_level():
#     all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
#     for actor in all_actors:
#         print(actor.get_name())

# get_all_actor_names_in_level()