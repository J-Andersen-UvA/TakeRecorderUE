import unreal
import json
import sys
import os
import subprocess

import scripts.skeletalMeshNameFetcher as skeletalMeshNameFetcher
import scripts.takeRecorder as takeRecorder
import scripts.levelSequence as levelSequence
import scripts.wsCommunicationScript as wsCommunicationScript
import scripts.stateManagerScript as stateManagerScript
import scripts.exportAndSend as exportAndSend
import scripts.popUp as popUp
import scripts.callback as callback

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
        self.replayEnabled = False
        self.keepLastRecording = True
        self.babylonAutoPlay = True
        self.pathServer = callback.PathFlaskApp()
        self.actorName = "GlassesGuyRecord_C_1"
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
            stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            tk.stop_recording()
            ws_JSON = {
                "handler": "stopRecordingConfirmed",
            }
            wsCom.ws.send(json.dumps(ws_JSON))            

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

        if stateManager.get_recording_status() == stateManagerScript.Status.REPLAY_RECORD:
            if self.replayEnabled:
                print("Replaying recorded animation...")
                tk.start_replaying(
                    levelSequence.SequencerTools(tk.fetch_last_recording(), "").get_level_sequence_actor_by_name(self.actorName),
                )

        if stateManager.get_recording_status() == stateManagerScript.Status.EXPORT_FBX:
            stateManager.set_recording_status(stateManagerScript.Status.IDLE)
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
                    while os.path.exists(path):
                        i += 1
                        path = stateManager.folder + "glb\\" + stateManager.get_gloss_name() + f"_{i}.glb"
                    path = stateManager.folder + "glb\\" + stateManager.get_gloss_name() + f"_{i-1}.glb"
                self.pathServer.change_path(path)

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


stateManager = stateManagerScript.StateManager()
tk = takeRecorder.TakeRecorder()

KeepRunningTakeRecorder(tk, "").start()

host = "wss://leffe.science.uva.nl:8043/unrealServer/"
# host = "ws://localhost:5012/"
if len(sys.argv) > 1:
    host = sys.argv[1]
wsCom = wsCommunicationScript.websocketCommunication(host, tk)
wsCom.keep_running_take_recorder = tk