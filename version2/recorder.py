import unreal
import json
import sys

import scripts.skeletalMeshNameFetcher as skeletalMeshNameFetcher
import scripts.takeRecorder as takeRecorder
import scripts.levelSequence as levelSequence
import scripts.wsCommunicationScript as wsCommunicationScript
import scripts.stateManagerScript as stateManagerScript
import scripts.exportAndSend as exportAndSend
import scripts.popUp as popUp


#########################################################################################################
#                                            asyncFuncs                                                 #
#########################################################################################################

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
        self.sequencerTools = levelSequence.SequencerTools(tk.fetch_last_recording(), file)
        self.replayEnabled = False
    #     self.startRecordStatus = startRecordStatus

    def start(self) -> None:
        """
        Start the take recorder.

        Registers a Slate post-tick callback to execute 'tick' method.
        """
        self.slate_post_tick_handle = unreal.register_slate_post_tick_callback(self.tick)
        popUp.show_popup_message("KeepRunningTakeRecorder", "Tick hook started")

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

        if stateManager.get_recording_status() == stateManagerScript.Status.FBX_EXPORT:
            stateManager.set_recording_status(stateManagerScript.Status.IDLE)

            print("Exporting last recording...")
            exportAndSend.ExportandSend(stateManager.get_gloss_name(), tk.fetch_last_recording())

        if stateManager.get_recording_status() == stateManagerScript.Status.REPLAY_RECORD:
            if self.replayEnabled:
                print("Replaying recorded animation...")
                tk.start_replaying(
                    self.sequencerTools.get_level_sequence_actor_by_name("GlassesGuyRecord_C_1"),
                )

        if stateManager.get_recording_status() == stateManagerScript.Status.EXPORT_FBX:
            stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            glosName = stateManager.get_gloss_name()
            print(f"Exporting last recording: {glosName}...")

            last_record = tk.fetch_last_recording().get_full_name()
            unrealTake = last_record.replace("LevelSequence ", "")
            unrealScene = unrealTake.split(".")[1]
            unrealTake = unrealTake.split(".")[0]
            unrealTake = unrealTake + "_Subscenes/GlassesGuyRecord" + "_" + unrealScene
            print(unrealTake, glosName)

            exportAndSend.export_fbx('/Game/mainlevel', unrealTake, unrealTake, "D:\\RecordingsUE\\" + glosName + ".fbx")

            anim_path = unrealTake + "_Subscenes/Animation/" + unrealScene
            wsCom.send_fbx_to_url("D:\\RecordingsUE\\" + glosName + ".fbx", avatar_name=skeletalMeshNameFetcher.get_skeletal_mesh_name_from_animation(anim_path))


stateManager = stateManagerScript.StateManager()
tk = takeRecorder.TakeRecorder()

KeepRunningTakeRecorder(tk, "").start()

host = "wss://leffe.science.uva.nl:8043/unrealServer/"
if len(sys.argv) > 1:
    host = sys.argv[1]
wsCom = wsCommunicationScript.websocketCommunication(host, tk)
