from enum import Enum
import os
from datetime import datetime
import re

class Status(Enum):
    START = "start"
    STOP = "stop"
    FBX_EXPORT = "fbxExport"
    REPLAY_RECORD = "replayRecord"
    FETCH_LAST_ANIMATION = "fetchLastAnimation"
    EXPORT_FBX = "exportFbx"
    IDLE = "idle"
    RECORDING = "recording"
    BUSY = "busy"
    DIE = "die"
    RESETTING = "resetting"
    EXPORT_SUCCESS = "exportSuccess"
    EXPORT_FAIL = "exportFail"

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

    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'initialized'):  # Initialize once
            self.recording_status = Status.IDLE  # Default state
            self.gloss_name = None
            self.gloss_name_cleaned = None
            self.initialized = True
            self.level_sequence_name = None
            self.export_status = Status.IDLE
            self.last_location = None
            self.upload_location = None

            self.folder = None
            if args:
                self.set_folder(args[0])

    def set_endpoint_file(self, endpoint_file):
        """Sets the endpoint file."""
        print(f"Setting endpoint file to: {endpoint_file}")
        self.upload_location = endpoint_file
        return self.upload_location
    
    def set_folder(self, folder):
        """Sets the folder path."""
        print(f"Setting folder to: {folder}")
        self.folder = folder
        # Create a subfolder based on the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        date_folder = os.path.join(self.folder, current_date)
        os.makedirs(date_folder, exist_ok=True)
        print(f"Created subfolder: {date_folder}")
        self.folder = date_folder + "\\"
        return self.folder

    @staticmethod
    def _sanitize_name(name: str, replacement: str = "_") -> str:
        # any character _not_ in A–Z a–z 0–9 space _ or -
        _SANITIZE_RE = re.compile(r'[^0-9A-Za-z _-]')
        return _SANITIZE_RE.sub(replacement, name)

    def set_gloss_name(self, gloss_name):
        """Sets the glossName."""
        self.gloss_name = gloss_name
        self.gloss_name_cleaned = self._sanitize_name(gloss_name)
        return self.gloss_name

    def get_gloss_name(self):
        """Returns the current glossName."""
        return self.gloss_name
    
    def set_last_location(self, location):
        print(f"Setting last location: {location}")
        self.last_location = location
        return self.last_location
    
    def get_last_location(self):
        return self.last_location
    
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
        print(f"Recording status set to: {status}")

    def get_recording_status(self) -> Status:
        """Returns the current recording status."""
        return self.recording_status
    
    def get_export_status(self):
        """Returns the current export status."""
        return self.export_status
    
    def flip_export_status(self):
        """Flips the export status."""
        if self.export_status == Status.IDLE:
            self.export_status = Status.BUSY
        else:
            self.export_status = Status.IDLE

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
