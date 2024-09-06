from enum import Enum

class Status(Enum):
    START = "start"
    STOP = "stop"
    FBX_EXPORT = "fbxExport"
    REPLAY_RECORD = "replayRecord"
    EXPORT_FBX = "exportFbx"
    IDLE = "idle"
    RECORDING = "recording"

class StateManager:
    """
    Singleton class that manages the state of recorder and glossName for the entire system.
    Ensures only one instance of this class exists.
    """
    _instance = None  # Class-level variable to store the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Initialize once
            self.recording_status = Status.IDLE  # Default state
            self.gloss_name = None
            self.initialized = True
            self.level_sequence_name = None

    def set_gloss_name(self, gloss_name):
        """Sets the glossName."""
        self.gloss_name = gloss_name
        return self.gloss_name

    def get_gloss_name(self):
        """Returns the current glossName."""
        return self.gloss_name
    
    def set_level_sequence_name(self, level_sequence_name):
        """Sets the level sequence name."""
        self.level_sequence_name = level_sequence_name

    def get_level_sequence_name(self):
        """Returns the current level sequence name."""
        return self.level_sequence_name

    def set_recording_status(self, status):
        """Sets the recording status using the Status enum."""
        if status not in Status:
            raise ValueError(f"Invalid status: {status}")
        self.recording_status = status

    def get_recording_status(self) -> Status:
        """Returns the current recording status."""
        return self.recording_status

# # Example Usage
# sm = StateManager()

# # Set gloss name
# sm.set_gloss_name("MyGlossName")

# # Set recording status
# sm.set_recording_status(Status.START)

# # Get current gloss name and recording status
# current_gloss_name = sm.get_gloss_name()
# current_status = sm.get_recording_status()

# print(current_gloss_name)  # Output: MyGlossName
# print(current_status)      # Output: Status.START
