import unreal
import json
import sys
import os
import subprocess
import yaml

import scripts.skeletalMeshNameFetcher as skeletalMeshNameFetcher
import scripts.takeRecorder as takeRecorder
import scripts.levelSequence as levelSequence
import scripts.wsCommunicationScript as wsCommunicationScript
import scripts.stateManagerScript as stateManagerScript
import scripts.exportAndSend as exportAndSend
import scripts.popUp as popUp
import scripts.callback as callback
import scripts.editorFuncs as editorFuncs

# Set the parameters from the config file
params = None
with open('C:\\Users\\VICON\\Desktop\\Code\\TakeRecorderUE\\version2\\config.yaml', 'r') as file:
    params = yaml.safe_load(file)

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

    def __init__(self, tk: takeRecorder.TakeRecorder, file):
        self.replayEnabled = True
        self.keepLastRecording = True
        self.babylonAutoPlay = True
        self.pathServer = callback.PathFlaskApp(params["pathServerPort"])
        self.actorName = params["actor_name"]
        self.replayActor = params["replay_actor_name"]
        # self.actorName = "GlassesGuyRecord_C_1"
    #     self.startRecordStatus = startRecordStatus

    def start(self) -> None:
        """
        Start the take recorder.

        Registers a Slate post-tick callback to execute 'tick' method.
        """
        self.slate_post_tick_handle = unreal.register_slate_post_tick_callback(self.tick)
        popUp.show_popup_message("KeepRunningTakeRecorder", f"Tick hook started, keepingLastRecording: {self.keepLastRecording}")

    def stop(self) -> None:
        """
        Stop the take recorder.

        Unregisters the Slate post-tick callback.
        """
        if self.slate_post_tick_handle is not None:
            unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)
            self.slate_post_tick_handle = None
        unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)

    def tick(self, delta_time: float) -> None:
        """
        Perform actions based on the current state.

        If the recording state is "start", begin recording.
        If the recording state is "stop", stop recording.
        """
        if stateManager.get_recording_status() == stateManagerScript.Status.START:
            stateManager.set_recording_status(stateManagerScript.Status.RECORDING)
            tk.start_recording()
            ws_JSON = {
                "handler": "startRecordingConfirmed",
            }
            wsCom.ws.send(json.dumps(ws_JSON))
        
        if stateManager.get_recording_status() == stateManagerScript.Status.STOP:
            tk.stop_recording()
            stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            ws_JSON = {
                "handler": "stopRecordingConfirmed",
            }
            wsCom.ws.send(json.dumps(ws_JSON))    

            if self.replayEnabled:
                print("Replaying recorded animation...")
                replay_actor = editorFuncs.get_actor_by_name(self.replayActor)
                # Check if the actor reference was found
                if replay_actor is None:
                    raise ValueError(f"Actor '{self.replayActor}' not found in the current world.")

                last_record = tk.fetch_last_recording()
                if last_record is not None:
                    last_record = last_record.get_full_name()
                unrealTake = last_record.replace("LevelSequence ", "")
                unrealScene = unrealTake.split(".")[1]
                unrealTake = unrealTake.split(".")[0]
                animLocation = unrealTake + "_Subscenes/Animation/GlassesGuyRecord" + "_" + unrealScene
                animation_asset = unreal.load_asset(animLocation)

                print(f"Replaying: {animLocation}")
                # Call the replay_anim function with the found actor and correct animation asset
                tk.replay_anim(
                    replay_actor=replay_actor,
                    anim=animation_asset
                )        

        # if stateManager.get_recording_status() == stateManagerScript.Status.FBX_EXPORT:
        #     stateManager.set_recording_status(stateManagerScript.Status.IDLE)

        #     self.rename_last_recording(stateManager.folder, stateManager.get_gloss_name())
        #     print("Exporting last recording...")
        #     exportAndSend.ExportandSend(stateManager.get_gloss_name(), tk.fetch_last_recording())

        #     # Automatically convert to GLB and wait for Babylon
        #     callback.Callback().send_message("path", stateManager.folder + "\\" + stateManager.get_gloss_name() + ".fbx")
        #     if self.babylonAutoPlay:
        #         # callback.Callback().send_message_to("path", stateManager.folder + "glb\\" + stateManager.get_gloss_name() + ".glb", "/send-path", "localhost", 5000)
        #         # callback.Callback().send_message_to_ws("path", stateManager.folder + "glb\\" + stateManager.get_gloss_name() + ".glb", "localhost", 5000)
        #         if not self.pathServer._is_running:
        #             self.pathServer.launch()
        #         path = stateManager.folder + "glb\\" + stateManager.get_gloss_name() + ".glb"
        #         if self.pathServer._path == path:
        #             self.pathServer.change_path("reload")
        #         else:
        #             self.pathServer.change_path(stateManager.folder + "glb\\" + stateManager.get_gloss_name() + ".glb")

        # if stateManager.get_recording_status() == stateManagerScript.Status.REPLAY_RECORD:
        #     if self.replayEnabled:
        #         print("Replaying recorded animation...")
        #         replay_actor = editorFuncs.get_actor_by_name(self.replayActor)
        #         # Check if the actor reference was found
        #         if replay_actor is None:
        #             raise ValueError(f"Actor '{self.replayActor}' not found in the current world.")

        #         last_record = tk.fetch_last_recording().get_full_name()
        #         unrealTake = last_record.replace("LevelSequence ", "")
        #         animLocation = unrealTake + "_Subscenes/Animation/GlassesGuyRecord" + "_" + unrealScene
        #         animation_asset = unreal.load_asset(animLocation)

        #         # Call the replay_anim function with the found actor and correct animation asset
        #         tk.replay_anim(
        #             replay_actor=replay_actor,
        #             anim=animation_asset
        #         )

        if stateManager.get_recording_status() == stateManagerScript.Status.EXPORT_FBX:
            glosName = stateManager.get_gloss_name()
            print(f"Exporting last recording: {glosName}...")

            last_record = tk.fetch_last_recording().get_full_name()
            unrealTake = last_record.replace("LevelSequence ", "")
            unrealScene = unrealTake.split(".")[1]
            unrealTake = unrealTake.split(".")[0]
            animLocation = unrealTake + "_Subscenes/Animation/GlassesGuyRecord" + "_" + unrealScene
            unrealTake = unrealTake + "_Subscenes/GlassesGuyRecord" + "_" + unrealScene
            print(unrealTake, glosName)

            self.rename_last_recording(stateManager.folder, glosName)
            exportAndSend.export_animation(animLocation, stateManager.folder, glosName)
            wsCom.send_fbx_to_url(stateManager.folder + glosName + ".fbx", avatar_name=self.actorName)

            print("Converting: ", stateManager.folder + glosName + ".fbx")
            result = subprocess.run(["C:\\Program Files\\nodejs\\node.exe", "C:\\Users\\VICON\\Desktop\\Code\\TakeRecorderUE\\version2\\autoConvertFBXGLB\\fbx2gltf.js", stateManager.folder + glosName + ".fbx"])
            print(result)

            if self.babylonAutoPlay:
                if not self.pathServer._is_running:
                    self.pathServer.launch()
                path = stateManager.folder + "glb\\" + stateManager.get_gloss_name() + ".glb"

                # Because converter auto increments the name of the file, we need to fetch the highest number and use that as path
                if os.path.exists(path):
                    i = 1
                    while os.path.exists(stateManager.folder + "glb\\" + stateManager.get_gloss_name() + f"_{i}.glb"):
                        path = stateManager.folder + "glb\\" + stateManager.get_gloss_name() + f"_{i}.glb"
                        i += 1

                print(f"Setting path of path server to: {path}")
                self.pathServer.change_path(path)
                callback.Callback().send_message_to("path", path, "/set_path", params["pathServerAddr"], params["pathServerPort"])

                # Fetch path from server and check if it is the same as the path we just set, if not kill the server and launch a new one
                if self.pathServer._path != path:
                    callback.Callback().send_message_to("", "", "/turn_off", params["pathServerAddr"], params["pathServerPort"])
                    self.pathServer.launch()
                    

            stateManager.set_recording_status(stateManagerScript.Status.IDLE)

            # Lastly, let the websocket know that the fbx has been exported
            # ws_JSON = {
            #     "handler": "fbxExportNameConfirmed",
            # }
            # wsCom.ws.send(json.dumps(ws_JSON))

    def rename_last_recording(self, cur_path, gloss_name):
        # Check if last path already exists and rename it to _old_{1} if it does
        complete_path = cur_path + "\\" + gloss_name + ".fbx"
        if os.path.exists(complete_path):
            print(f"File already exists: {complete_path}")
            i = 1
            old_path = cur_path + "\\" + gloss_name + f"_old_{i}.fbx"
            while os.path.exists(old_path):
                i += 1
                old_path = cur_path + "\\" + gloss_name + f"_old_{i}.fbx"
            print(f"Renaming to: {old_path}")
            os.rename(complete_path, old_path)


stateManager = stateManagerScript.StateManager(params["output_dir"])
tk = takeRecorder.TakeRecorder()

KeepRunningTakeRecorder(tk, "").start()

# host = "wss://leffe.science.uva.nl:8043/unrealServer/"
host = params["websocketServer"]
# host = "ws://localhost:5012/"
if len(sys.argv) > 1:
    host = sys.argv[1]
wsCom = wsCommunicationScript.websocketCommunication(host, tk)
wsCom.keep_running_take_recorder = tk
