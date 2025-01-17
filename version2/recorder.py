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
import params as paramsmanager

# Set the parameters from the config file
params = paramsmanager.Params().get()

class KeepRunningTakeRecorder:
    """
    Utility class for managing continuous recording with the Take Recorder.

    This class provides functionality to start and stop recording using the
    provided 'stateManager'. It utilizes Slate post-tick callbacks
    to continuously monitor the recording state and take appropriate actions.
    We are also able to replay the last recording.

    We need to hook on the tick function because in Unreal Engine, many API
    calls, especially thoserelated to editor functions, must be called from
    the main thread.

    Methods:
    - start(): Start the take recorder.
    - stop(): Stop the take recorder.
    - tick(delta_time: float): Perform actions based on the current state.
    """

    def __init__(self, tk: takeRecorder.TakeRecorder, file):
        print("Initializing KeepRunningTakeRecorder...")
        self.tk = tk
        self.actorName = params["actor_name"]
        self.replayActor = params["replay_actor_name"]
        self.slate_post_tick_handle = None

    def start(self) -> None:
        """
        Start the take recorder.

        Registers a Slate post-tick callback to execute 'tick' method.
        """
        print("Starting Take Recorder...")
        self.slate_post_tick_handle = unreal.register_slate_post_tick_callback(self.tick)
        popUp.show_popup_message("KeepRunningTakeRecorder", f"Tick hook started, keeping double recordings: True")

    def stop(self) -> None:
        """
        Safely stop the take recorder and unregister the Slate post-tick callback.
        """
        if self.slate_post_tick_handle is not None:
            try:
                print("Unregistering Slate post-tick callback...")
                unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)
                self.slate_post_tick_handle = None
                print("Slate post-tick callback unregistered successfully.")
            except Exception as e:
                print(f"Error during unregistration: {e}")
                popUp.show_popup_message("KeepRunningTakeRecorder", f"Error during unregistration: {str(e)}")
        else:
            print("Slate post-tick callback was already unregistered or never registered.")

    def tick(self, delta_time: float) -> None:
        """
        Perform actions based on the current state.

        If the recording state is "start", begin recording.
        If the recording state is "stop", stop recording.
        If the recording state is "replay_record", replay the last recording.
        """
        # When resetting, we are waiting for the take recorder to be ready (making it so he has saved the last recording)
        if stateManager.get_recording_status() == stateManagerScript.Status.RESETTING:
            if self.tk.take_recorder_ready():
                print("Resetting state to idle.")
                stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            return

        if stateManager.get_recording_status() == stateManagerScript.Status.DIE:
            self.stop()  # Unregister the callback when stopping
            return

        if stateManager.get_recording_status() == stateManagerScript.Status.START:
            self.tk.start_recording()
            stateManager.set_recording_status(stateManagerScript.Status.RECORDING)
            return

        if stateManager.get_recording_status() == stateManagerScript.Status.STOP:
            self.tk.stop_recording()
            stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            return

        if stateManager.get_recording_status() == stateManagerScript.Status.REPLAY_RECORD:
            print("TEST: Replaying last recording...")
            replay_actor = editorFuncs.get_actor_by_name(self.replayActor)
            # Check if the actor reference was found
            if replay_actor is None:
                # stateManager.set_recording_status(stateManagerScript.Status.IDLE)
                stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
                popUp.show_popup_message("replay", f"Actor '{self.replayActor}' not found in the current world. Set state to idle.")
                raise ValueError(f"Actor '{self.replayActor}' not found in the current world.")

            print("TEST: FETCHING LAST ANIMATION")
            last_anim, location = self.tk.fetch_last_animation()

            if last_anim is None:
                # stateManager.set_recording_status(stateManagerScript.Status.IDLE)
                stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
                popUp.show_popup_message("replay", "No last recording found. Set state to idle.")
                return

            print(f"Replaying animation at: {location}")
            self.tk.replay_anim(
                replay_actor=replay_actor,
                anim=last_anim
            )

            stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            # stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            return

        # Exporting needs to be done through the main thread since UE5.5, the subthread communicating with the websocket therefore
        # communicates with this main thread loop
        if stateManager.get_recording_status() == stateManagerScript.Status.FBX_EXPORT or stateManager.get_recording_status() == stateManagerScript.Status.EXPORT_FBX:
            anim, location = self.tk.fetch_last_animation()
            stateManager.set_last_location(location)
            if not self.tk.export_animation(location, stateManager.folder, stateManager.get_gloss_name()):
                stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
            else:
                stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)

        return

print("Starting recorder...")
stateManager = stateManagerScript.StateManager(params["output_dir"])
stateManager.set_folder(params["output_dir"])
stateManager.set_recording_status(stateManagerScript.Status.IDLE)
tk = takeRecorder.TakeRecorder(stateManager)

ktk = KeepRunningTakeRecorder(tk, "")
ktk.start()

host = params["websocketServer"]
if len(sys.argv) > 1:
    host = sys.argv[1]
wsCom = wsCommunicationScript.websocketCommunication(host, tk, ktk, params["actor_name"], params["replay_actor_name"])
# wsCom.keep_running_take_recorder = tk
