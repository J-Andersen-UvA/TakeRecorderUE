import unreal
import scripts.popUp as popUp

class SequencerTools:
    _instance = None  # Class-level variable to store the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SequencerTools, cls).__new__(cls)
        return cls._instance

    def __init__(self, rootSequence, file):
        """
        Initialize a SequencerTools instance.

        Params:
        - rootSequence (unreal.MovieSceneSequence): The root sequence to export.
        - levelSequence (unreal.LevelSequence): The level sequence to export.
        - file (str): The file path to export the sequence to.

        Initializes 'params' with SequencerExportFBXParams containing the provided
        parameters and executes the export.
        """
        if not hasattr(self, 'initialized'):  # Initialize once
            self.initialized = True
            self.rootSequence = ("" if rootSequence == None else rootSequence)

            self.sequence = unreal.load_asset(self.rootSequence, unreal.LevelSequence)
            
            bindings = self.sequence.get_bindings()
            tracks = self.sequence.get_tracks()
            export_options = unreal.FbxExportOption()
            export_options.ascii = True
            export_options.level_of_detail = False
    
            self.params = unreal.SequencerExportFBXParams(
                world=unreal.EditorLevelLibrary.get_editor_world(),
                root_sequence=self.sequence,
                sequence=self.sequence,
                fbx_file_name=("D:\\RecordingsUE\\TEST.fbx" if file == "" else file),
                bindings=bindings,
                tracks=tracks,
                export_options=export_options
            )

    def set_root_sequence(self, root_sequence):
        """
        Set the root sequence to export.

        Params:
        - root_sequence (unreal.MovieSceneSequence): The root sequence to export.
        """
        try:
            self.rootSequence = unreal.load_asset(root_sequence, unreal.MovieSceneSequence)
        except:
            popUp.show_popup_message("SequencerTools", "Error: Could not load root sequence")
    
    def set_level_sequence(self, level_sequence):
        """
        Set the level sequence to export.

        Params:
        - level_sequence (unreal.LevelSequence): The level sequence to export.
        """
        try:
            self.sequence = unreal.load_asset(level_sequence, unreal.LevelSequence)
        except:
            popUp.show_popup_message("SequencerTools", "Error: Could not load level sequence")

    def set_file(self, file):
        """
        Set the file path to export the sequence to.

        Params:
        - file (str): The file path to export the sequence to.
        """
        self.params.fbx_file_name = file

    def execute_export(self) -> bool:
        """
        Execute the export of the level sequence to FBX.

        Returns:
            bool: True if the export was successful, False otherwise.
        """
        try:
            return unreal.SequencerTools.export_level_sequence_fbx(params=self.params)
        except:
            popUp.show_popup_message("SequencerTools", "Error: Could not export level sequence")
            return False

    def set_sequence_and_export(self, file, sequence=None):
        """
        Set the level sequence and file path and execute the export.

        Params:
        - sequence (unreal.LevelSequence): The level sequence to export.
        - file (str): The file path to export the sequence to.
        """
        if sequence is not None:
            self.set_level_sequence(sequence)
        else:
            self.set_level_sequence(self.rootSequence)
        self.set_file(file)

        return self.execute_export()

    def get_level_sequence_actor_by_name(name):
        level_sequence_actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for level_sequence_actor in level_sequence_actors:
            if level_sequence_actor.get_name() == name:
                return level_sequence_actor
        return None
