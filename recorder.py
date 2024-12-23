import unreal
import os

# import time
import threading
import sys

# import aiohttp
import asyncio
import httpx
import websocket
import ssl
import json
import requests
# import subprocess
from multiprocessing import Process, Queue


# Function to get the name of the skeletal mesh from the animation
def get_skeletal_mesh_name_from_animation(animation_path):
    print(f"Loading animation asset from path: {animation_path}")
    # Load the animation asset
    animation_asset = unreal.load_asset(animation_path)
    
    # Check if the asset was successfully loaded
    if not animation_asset:
        print("Failed to load asset. Please check the asset path.")
        return None
    
    # Check if the asset is a valid animation asset
    if not isinstance(animation_asset, unreal.AnimSequence):
        print(f"Loaded asset is not an AnimSequence. It is a {type(animation_asset).__name__}.")
        return None

    print(f"Successfully loaded animation asset: {animation_asset.get_name()}")

    # Get the skeleton from the animation asset
    skeleton = animation_asset.get_editor_property('skeleton')
    if not skeleton:
        print("Failed to get skeleton from the animation asset.")
        return None
    
    print(f"Skeleton: {skeleton.get_name()}")

    if "_Skeleton" in skeleton.get_name():
        return skeleton.get_name().replace("_Skeleton", "")
    
    # Get all skeletal mesh references associated with the skeleton
    skeletal_meshes = skeleton.get_referencers(unreal.SkeletalMesh)
    if not skeletal_meshes:
        print("No skeletal meshes found for this animation.")
        return None
    
    # Get the name of the first skeletal mesh found (assuming there's at least one)
    skeletal_mesh_name = skeletal_meshes[0].get_name()
    return skeletal_mesh_name

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

    def start_replaying(self, cur_level_sequence_actor):
        """
        Start replaying.

        This function starts the replaying process using the take recorder panel.
        """
        # call custom event from cur_level_sequence_actor to stop replay system (Event Stop Record)
        cur_level_sequence_actor.call_method(
            "Event Replay Recording", args=(self.fetch_last_recording(),)
        )

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


class TakeRecorderSetActor:
    def __init__(self):
        self.takeRecorderAS = unreal.TakeRecorderActorSource()
        self.takeRecorderAS.set_source_actor(
            unreal.EditorLevelLibrary.get_all_level_actors()[0]
        )

        print(self.takeRecorderAS.get_source_actor().get_path_name())
        print("init")

    # Get level sequence actor by name
    def set_level_sequence_actor_by_name(self, name):
        level_sequence_actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for level_sequence_actor in level_sequence_actors:
            if level_sequence_actor.get_name() == name:
                self.takeRecorderAS.set_source_actor(level_sequence_actor)
                return level_sequence_actor
        print("Name: " + name + "not found")
        return None


class SequencerTools:
    def __init__(self, rootSequence, levelSqeuence, file):
        """
        Initialize a SequencerTools instance.

        Params:
        - rootSequence (unreal.MovieSceneSequence): The root sequence to export.
        - levelSequence (unreal.LevelSequence): The level sequence to export.
        - file (str): The file path to export the sequence to.

        Initializes 'params' with SequencerExportFBXParams containing the provided
        parameters and executes the export.
        """
        self.rootSequence = rootSequence
        
        sequence = unreal.load_asset(self.rootSequence, unreal.LevelSequence)
        
        
        bindings = sequence.get_bindings()
        tracks = sequence.get_tracks()
        export_options = unreal.FbxExportOption()
        export_options.ascii = True
        export_options.level_of_detail = False
 
        self.params = unreal.SequencerExportFBXParams(
            world=unreal.EditorLevelLibrary.get_editor_world(),
            root_sequence=sequence,
            sequence=sequence,
            fbx_file_name=file,
            bindings=bindings,
            tracks=tracks,
            export_options=export_options
        )
        self.execute_export()

    def execute_export(self) -> bool:
        """
        Execute the export of the level sequence to FBX.

        Returns:
            bool: True if the export was successful, False otherwise.
        """
        return unreal.SequencerTools.export_level_sequence_fbx(params=self.params)


def get_level_sequence_actor_by_name(name):
    level_sequence_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for level_sequence_actor in level_sequence_actors:
        if level_sequence_actor.get_name() == name:
            return level_sequence_actor
    return None


#########################################################################################################
#                                            asyncFuncs                                                 #
#########################################################################################################

startRecordStatus = ""
global glossNameLS
global levelSequenceName

def setRecord(value=None):
    global startRecordStatus
    if value:
        startRecordStatus = value
    else:
        return startRecordStatus

def setGlosName(glosName):
    global glossNameLS
    glossNameLS = glosName

def setSequenceName(sequenceName):
    global levelSequenceName
    levelSequenceName = sequenceName
    
def getGlosName():
    global glossNameLS
    return glossNameLS

def getSequenceName():
    global levelSequenceName
    return levelSequenceName


class KeepRunningTakeRecorder:
    """
    Utility class for managing continuous recording with the Take Recorder.

    This class provides functionality to start and stop recording using the
    provided 'startRecordStatus' function. It utilizes Slate post-tick callbacks
    to continuously monitor the recording state and take appropriate actions.

    Attributes:
    - startRecordStatus: Status var to start recording.

    Methods:
    - start(): Start the take recorder.
    - stop(): Stop the take recorder.
    - tick(delta_time: float): Perform actions based on the current state.
    """

    def __init__(self):
        self.startRecordStatus = startRecordStatus

    def start(self) -> None:
        """
        Start the take recorder.

        Registers a Slate post-tick callback to execute 'tick' method.
        """
        self.slate_post_tick_handle = unreal.register_slate_post_tick_callback(
            self.tick
        )
        print("started")

    def stop(self) -> None:
        """
        Stop the take recorder.

        Unregisters the Slate post-tick callback.
        """
        unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)
        
    def tick(self, delta_time: float) -> None:
        """
        Perform actions based on the current state.

        If the recording state is "start", begin recording.
        If the recording state is "stop", stop recording.
        """
        if setRecord() == "start":
            setRecord("idle")
            tk.start_recording()
            
            ws_JSON = {
            "handler": "startRecordingConfirmed",
             }
            ws.send(json.dumps(ws_JSON))
            

        if setRecord() == "stop":
            setRecord("idle")
            tk.stop_recording()
            
            ws_JSON = {
            "handler": "stopRecordingConfirmed",
                }
            ws.send(json.dumps(ws_JSON))
            
            

        if setRecord() == "fbxExport":
            setRecord("idle")
            ExportandSend("lala")
        if setRecord() == "replayRecord":
            setRecord("idle")
            tk.start_replaying(
                get_level_sequence_actor_by_name("GlassesGuyRecord_C_1"),
            )
            print("replay")
        if setRecord() == "exportFbx":
            global glosNameGlobal
            print(glosNameGlobal)
            setRecord("idle")
            last_record = tk.fetch_last_recording()
            last_record = last_record.get_full_name()
            unrealTake = last_record.replace("LevelSequence ", "")
            unrealScene = unrealTake.split(".")[1]
            unrealTake = unrealTake.split(".")[0]
            #add _Subscenes/GlassesGuyRecord
            unrealTake = unrealTake + "_Subscenes/GlassesGuyRecord" + "_" +unrealScene
            print(unrealTake, glosNameGlobal)
            # tk.start_replaying(
            #     get_level_sequence_actor_by_name("GlassesGuyRecord"),
            # )
            export_fbx('/Game/mainlevel', unrealTake, unrealTake, "D:\\RecordingsUE\\"+glosNameGlobal+".fbx")

            anim_path = unrealTake + "_Subscenes/Animation/" + unrealScene
            send_fbx_to_url("D:\\RecordingsUE\\"+glosNameGlobal+".fbx", avatar_name=get_skeletal_mesh_name_from_animation(anim_path))
            




KeepRunningTakeRecorder().start()


class UnrealAsyncFuncs:
    """
    Utility class for asynchronous execution of Unreal Engine functions.

    This class allows for asynchronous execution of Unreal Engine functions
    by registering a Slate post-tick callback and executing the provided
    callback function during each tick. It provides methods to start and
    stop the asynchronous execution.

    Attributes:
    - frame_count (int): Counter for the number of ticks.
    - max_count (int): Maximum number of ticks before stopping.
    - callback (function): Callback function to execute during each tick.
    - unrealClass (object): Instance of the Unreal Engine class to execute.
    - doneCallback (function): Callback function to execute when done.
    - glossName (str): Name for the asynchronous function (optional).

    Methods:
    - start(): Start the asynchronous execution.
    - stop(): Stop the asynchronous execution.
    - tick(delta_time: float): Callback function executed during each tick.
        Increments the tick counter and stops execution if max_count is reached.
    """

    def __init__(
        self, unrealClass=None, callback=None, doneCallback=None, glossName=None
    ):
        self.frame_count = 0
        self.max_count = 101
        self.callback = callback
        self.unrealClass = unrealClass
        self.doneCallback = doneCallback
        self.glossName = glossName

    def start(self) -> None:
        """
        Start the asynchronous execution.

        Registers a Slate post-tick callback to execute the 'tick' method.
        Resets the frame count.
        """
        if not callable(self.unrealClass):
            raise ValueError("unrealClass must be callable")
        self.slate_post_tick_handle = unreal.register_slate_post_tick_callback(
            self.tick
        )
        self.frame_count = 0

    def stop(self) -> None:
        """
        Stop the asynchronous execution.

        Unregisters the Slate post-tick callback.
        Executes the 'doneCallback' if provided.
        """
        unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)
        if self.doneCallback:
            self.doneCallback(self)

    def tick(self, delta_time: float) -> None:
        """
        Callback function executed during each tick.

        Increments the tick counter and stops execution if max_count is reached.
        Executes the 'callback' function if provided.
        """
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


#########################################################################################################
#                                               FBX EXPORT AND SENDER                                   #
#########################################################################################################


class ExportandSend:
    """
    Utility class for exporting and sending files asynchronously.

    This class provides methods to execute export operations and send files
    asynchronously to a specified URL.

    Attributes:
    - glossName (str): Name used for the file export.
    - file (str): File path for the export operation.

    Methods:
    - execExport(): Execute the export operation.
    - done(future): Callback function executed when the operation is done.
    - send_file_to_url(file_path, url): Asynchronously send a file to a URL.
    """

    def __init__(self, glossName, unreal_take):
        self.glossName = glossName
        self.unreal_take = unreal_take
        self.file = "D:\\RecordingsUE\\" + self.glossName + ".fbx"
        self.execExport()
        
    def execExport(self) -> None:
        print(self.unreal_take)

                
        if SequencerTools(
            rootSequence=self.unreal_take,
            levelSqeuence=self.unreal_take,
            file=self.file,
        ):
            pass

        asyncio.run(
            self.send_file_to_url(
                self.file, "https://leffe.science.uva.nl:8043/fbx2glb/upload/"
            )
        )

    def execExportLast(self) -> None:
        """
        Execute the export operation.

        Creates a SequencerTools instance to fetch the last recording and
        export it using asyncio to send the file to a specified URL.
        """
        if SequencerTools(
            rootSequence=tk.fetch_last_recording(),
            levelSqeuence=tk.fetch_last_recording(),
            file=self.file,
        ):
            pass

        asyncio.run(
            self.send_file_to_url(
                self.file, "https://leffe.science.uva.nl:8043/fbx2glb/upload/"
            )
        )

    def done(self, future):
        print(future.result())

    async def send_file_to_url(self, file_path, url):
        """
        Asynchronously send a file to a URL.

        Parameters:
        - file_path (str): File path of the file to send.
        - url (str): URL to send the file to.

        Prints the response from the server after sending the file.
        """
        print("Sending file...")
        async with httpx.AsyncClient(verify=False) as client:
            # Open the file and prepare it for sending. No need to use aiohttp.FormData with httpx.
            with open(file_path, "rb") as file:
                files = {"file": (file_path, file, "multipart/form-data")}
                response = await client.post(
                    url,
                    files=files,
                )  # 'verify=False' skips SSL verification.

                # No need to check _is_multipart or to explicitly close the file; it's managed by the context manager.
                print(response.text)


#########################################################################################################
#                                               WEBSOCKET CLIENT (YES CLIENT)                           #
#########################################################################################################



def export_fbx(map_asset_path, sequencer_asset_path, root_sequencer_asset_path, output_file):
	# Load the map, get the world
	world = unreal.EditorLoadingAndSavingUtils.load_map(map_asset_path)
	# Load the sequence asset
	sequence = unreal.load_asset(sequencer_asset_path, unreal.LevelSequence)
	root_sequence = unreal.load_asset(root_sequencer_asset_path, unreal.LevelSequence)
	# Set Options
	export_options = unreal.FbxExportOption()
	export_options.ascii = False
	export_options.level_of_detail = True
	export_options.export_source_mesh = True
	export_options.map_skeletal_motion_to_root = True
	export_options.export_source_mesh = True
	export_options.vertex_color = True
	export_options.export_morph_targets = True
	export_options.export_preview_mesh = True
	export_options.force_front_x_axis = False
	# Get Bindings
	bindings = sequence.get_bindings()
	tracks = sequence.get_tracks()
	# Export
	export_fbx_params = unreal.SequencerExportFBXParams(world, sequence, root_sequence, bindings, tracks, export_options, output_file)
	unreal.SequencerTools.export_level_sequence_fbx(export_fbx_params)    

def send_fbx_to_url(file_path, avatar_name="glassesGuy"):
    """
    Synchronously send a file to a URL.

    Parameters:
    - file_path (str): File path of the file to send.

    Prints the response from the server after sending the file.
    """
    print("Sending file...")
    with open(file_path, "rb") as file:
        files = {"file": (file_path, file, "multipart/form-data")}
        response = requests.post(
            "https://leffe.science.uva.nl:8043/fbx2glb/upload/",
            files=files,
            verify=False  # Skips SSL verification.
        )


        ws_JSON = {
            "handler": "fbxExportNameConfirmed",
            "glosName": glosNameGlobal,
            "avatarName": avatar_name
        }
        ws.send(json.dumps(ws_JSON))
                
                
global glosNameGlobal
            
def glosName(glosName):
    global glosNameGlobal
    glosNameGlobal = glosName
    return glosName

# websocket.enableTrace(True)


def on_close(ws, close_status_code, close_msg):
    print("### CLOSED AND KILLED PYTHON PROCESS ###")
    sys.exit()


def on_message(ws, message):
    global startRecordStatus
    message = json.loads(message)
    if message["set"] == "startRecord":
        print(setRecord("start"))
        #get last recording from takerecorder
     
        
    if message["set"] == "broadcastGlos":
        print(glosName(message["handler"]))
        ws_JSON = {
            "handler": "broadcastGlosConfirmed",
            "glosName": message["handler"]
        }
        ws.send(json.dumps(ws_JSON))
        
    if message["set"] == "ping":
        ws_JSON = {
            "handler": "pong",
        }
        ws.send(json.dumps(ws_JSON))
        
    if message["set"] == "stopRecord":
        print(setRecord("stop"))
    if message["set"] == "fbxExport":
        print(setRecord("fbxExport"))
    if message["set"] == "replayRecord":
        print(setRecord("replayRecord"))
        
    if message["set"] == "exportLevelSequenceName":
        print(setRecord("exportFbx"))
        
    if message["set"] == "fbxExportName":
        print(setRecord("fbxExportName"))
        setGlosName(message["glosName"])
        setSequenceName(message["data"])
        ws_JSON = {
        "data": "fbxExportNameConfirmed",
        "glosName": message["glosName"]
        }
        
        ws.send(json.dumps(ws_JSON))
        
    if message["set"] == "isRecording":
        ws_JSON = {
            "handler": "isRecordingConfirmed",
            "isRecording": tk.is_recording()
        }
        ws.send(json.dumps(ws_JSON))
        

if len(sys.argv) < 2:
    host = "wss://leffe.science.uva.nl:8043/unrealServer/"
else:
    host = sys.argv[1]

ws = websocket.WebSocketApp(host, on_message=on_message, on_close=on_close)
thread = threading.Thread(
    target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}
)
thread.start()

#request broadcastglos
ws_JSON = {
    "handler": "requestGlos",
}
ws.send(json.dumps(ws_JSON))
 