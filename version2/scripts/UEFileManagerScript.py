import unreal
import os
import scripts.popUp as popUp

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
    def __init__(self):
        pass

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
            popUp.show_popup_message("UEFileManager", "Not a valid dir")

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
