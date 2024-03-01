import unreal
import os
import time
import threading
import sys

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
        self.take_recorder_panel = (
            unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()
        )

        # a = unreal.LayersSubsystem()
        # self.world = a.get_world()
        self.takeMeta = unreal.TakeMetaData()

        self.UEFileFuncs = UEFileFunctionalities()

    # make it callable
    def __call__(self):
        return True

    def is_recording(self):
        lala = unreal.TakeRecorderBlueprintLibrary.is_recording()
        print(lala)
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


class SequencerTools:

    def __init__(self, rootSequence, levelSqeuence, file):

        self.params = unreal.SequencerExportFBXParams(
            world=unreal.EditorLevelLibrary.get_editor_world(),
            root_sequence=rootSequence,
            sequence=levelSqeuence,
            fbx_file_name=file,
        )
        self.execute_export()

    def execute_export(self):
        return unreal.SequencerTools.export_level_sequence_fbx(params=self.params)


#########################################################################################################
#                                            asyncFuncs                                                 #
#########################################################################################################


class unrealAsyncFuncs:

    def __init__(self, unrealClass=None, callback=None, doneCallback=None):
        self.frame_count = 0
        self.max_count = 101
        self.callback = callback
        self.unrealClass = unrealClass
        self.doneCallback = doneCallback

    def start(self) -> None:
        if not callable(self.unrealClass):
            raise ValueError("unrealClass must be callable")
        self.slate_post_tick_handle = unreal.register_slate_post_tick_callback(
            self.tick
        )
        self.frame_count = 0

    def stop(self) -> None:
        unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)
        if self.doneCallback:
            self.doneCallback(self)

    def tick(self, delta_time: float) -> None:
        if self.callback:
            self.callback(self)
        self.frame_count += 1
        if self.frame_count >= self.max_count:
            self.stop()


recordCounter = [0]
tk = TakeRecorder()


def make_check_rec(lala):
    print("recording: ", recordCounter[0])
    recordCounter[0] += 1

    if lala.frame_count > 50:
        if tk.is_recording():
            tk.stop_recording()
        lala.stop()


def execExport(lala):
    print(
        "Exported ->",
        SequencerTools(
            rootSequence=tk.fetch_last_recording(),
            levelSqeuence=tk.fetch_last_recording(),
            file="C:\\Users\\gotters\\lala.fbx",
        ),
    )


#########################################################################################################
#                                               TEST                                                    #
#########################################################################################################

# TODO:
# Sequence export async?
# Sequence export op root en level in orde?
# implementatie websock, hoe?
disableRecording = True

if disableRecording:
    # first check if it is recording
    if tk.is_recording():
        sys.exit()
    else:
        tk.start_recording()
    # then check if it is recording and then export asset files
    lala = unrealAsyncFuncs(
        tk.is_recording, callback=make_check_rec, doneCallback=execExport
    )
    # Start the async function
    lala.start()

print(tk.fetch_last_recording().get_path_name())


#
# curTa
# keRec = TakeRecorder()
# # curTakeRec.start_recording()
# # curTakeRec.stop_recording()
# files = curTakeRec.fetch_last_recording_assets()
# print('files: ', files)

# ass = '/Game/Cinematics/Takes/2024-02-29/Scene_1_2548_Subscenes/Animation/glassesGuysActorBP_Scene_1_2548'
# print(unreal.EditorAssetLibrary.does_asset_exist(ass))

# assetTool = unreal.AssetToolsHelpers.get_asset_tools()
# assetTool.export_assets([ass], "C:/Users/VICON/Desktop/test")

# bpFuncs = unreal.SequencerTools()
# bpFuncs.export_anim_sequence()


# Start record

# before start record, check if:
# doesnt it already start record?
# def recordStartup():
#     tk = TakeRecorder()
#     if not tk.is_recording():
#
# else:
#     tk.stop_recording()
#     #go back to start of function
#     recordStartup()
