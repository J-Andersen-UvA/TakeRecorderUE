import unreal
import os

def get_all_files_in_directory(directory):
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

    return files_list

def get_project_path():
    # Get the project path
    project_path = unreal.Paths.project_dir()

    return project_path

class TakeRecorder:
    def __init__(self):
        unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
        self.take_recorder_panel = unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()

        # a = unreal.LayersSubsystem()
        # self.world = a.get_world()
        self.takeMeta = unreal.TakeMetaData()

    def start_recording(self):
        self.take_recorder_panel.start_recording()

    def stop_recording(self):
        self.take_recorder_panel.stop_recording()

    def fetch_last_recording(self):
        return self.take_recorder_panel.get_last_recorded_level_sequence()

    def set_name_take(self, name):
        take_metadata = self.takeMeta.get_slate()
        print(take_metadata)
        # Implement somehow

curTakeRec = TakeRecorder()
# curTakeRec.start_recording()
# curTakeRec.stop_recording()
# curTakeRec.fetch_last_recording().get_path_name()
print('curTakeRec.fetch_last_recording().get_path_name(): ', curTakeRec.fetch_last_recording().get_path_name() + "_Subscenes/Animation")
anim_dir = curTakeRec.fetch_last_recording().get_path_name() + "_Subscenes/Animation"
print('anim_dir: ', anim_dir)
project_path = get_project_path().rstrip("/")
project_path = project_path.split("../")[-1]
print('project_path: ', project_path)
all_files = get_all_files_in_directory("C:/" + project_path + anim_dir + "/")
print('project_path + anim_dir: ', r"C:/" + project_path + "Content" + anim_dir + "/")
print('unreal.EditorAssetLibrary.does_directory_exist(project_path): ', unreal.EditorAssetLibrary.does_directory_exist(r"C:/" + project_path + "Content" + anim_dir + "/"))
print(all_files)


unreal.EditorAssetLibrary.does_directory_exist(unreal.Paths.project_dir())
print('unreal.EditorAssetLibrary.does_directory_exist(unreal.Paths.project_dir()): ', unreal.EditorAssetLibrary.does_directory_exist(unreal.Paths.project_dir().strip("../")[-1]))

# does_directory_have_assets