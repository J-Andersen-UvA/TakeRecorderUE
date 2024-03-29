import unreal
import os

#########################################################################################################
#                                            UEFileManager                                              #
#########################################################################################################


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
            files_list = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
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
            if ("/Game" in dir):
                # Get the complete path in windows form
                complete_path = "C:/" + project_path + "/Content" + dir.split("/Game")[1]
            else:
                complete_path = "C:/" + project_path + "/Content" + dir

            if (mode == "windows"):
                files = [complete_path + "/" + file for file in self.get_all_files_in_directory(complete_path)]
            else:
                files = [dir + file for file in self.get_all_files_in_directory(complete_path)]

            return files

        return []

#########################################################################################################
#                                            RecorderFuncs                                              #
#########################################################################################################

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
    """

    def __init__(self):
        unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
        self.take_recorder_panel = unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()

        # a = unreal.LayersSubsystem()
        # self.world = a.get_world()
        self.takeMeta = unreal.TakeMetaData()

        self.UEFileFuncs = UEFileFunctionalities()

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

    def __fetch_last_recording(self):
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
        anim_dir = self.__fetch_last_recording().get_path_name()
        anim_dir = anim_dir.split(".")[0] + "_Subscenes/Animation/"
        project_path = self.UEFileFuncs.get_project_path()

        return self.UEFileFuncs.fetch_files_from_dir_in_project(anim_dir, project_path, mode="UE")



#########################################################################################################
#                                               TEST                                                    #
#########################################################################################################

curTakeRec = TakeRecorder()
# curTakeRec.start_recording()
# curTakeRec.stop_recording()
files = curTakeRec.fetch_last_recording_assets()
print('files: ', files)

ass = '/Game/Cinematics/Takes/2024-02-29/Scene_1_2548_Subscenes/Animation/glassesGuysActorBP_Scene_1_2548'
print(unreal.EditorAssetLibrary.does_asset_exist(ass))

assetTool = unreal.AssetToolsHelpers.get_asset_tools()
assetTool.export_assets([ass], "C:/Users/VICON/Desktop/test")

bpFuncs = unreal.SequencerTools()
bpFuncs.export_anim_sequence()
