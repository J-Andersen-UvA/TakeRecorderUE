import unreal
import sys

import scripts.recording.takeRecorder as takeRecorder
import scripts.communication.wsCommunicationScript as wsCommunicationScript
import scripts.state.stateManagerScript as stateManagerScript
import scripts.utils.popUp as popUp
import scripts.utils.editorFuncs as editorFuncs
from scripts.config.params import Config

# Set the parameters from the config file
params = Config()

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
        self.actorName = params.actor_name
        self.actorNameShorthand = params.actor_name_shorthand
        self.replayActor = editorFuncs.get_actor_by_name(params.replay_actor_name)
        if self.replayActor is None:
            print(f"[recorder.py] Replay actor '{params.replay_actor_name}' not found in the level.")
            popUp.show_popup_message("KeepRunningTakeRecorder", f"[recorder.py] Replay actor '{params.replay_actor_name}' not found in the level.")

        self.slate_post_tick_handle = None
        self.resettingPopUpText = None
        self.resettingPopUpTitle = None

    def start(self) -> None:
        """
        Start the take recorder.

        Registers a Slate post-tick callback to execute 'tick' method.
        """
        print("[recorder.py] Starting Take Recorder...")
        self.slate_post_tick_handle = unreal.register_slate_post_tick_callback(self.tick)
        popUp.show_popup_message("KeepRunningTakeRecorder", f"[recorder.py] Tick hook started, keeping double recordings: True")

    def stop(self) -> None:
        """
        Safely stop the take recorder and unregister the Slate post-tick callback.
        """
        if self.slate_post_tick_handle is not None:
            try:
                print("[recorder.py] Unregistering Slate post-tick callback...")
                unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)
                self.slate_post_tick_handle = None
                print("[recorder.py] Slate post-tick callback unregistered successfully.")
            except Exception as e:
                print(f"[recorder.py] Error during unregistration: {e}")
                popUp.show_popup_message("KeepRunningTakeRecorder", f"[recorder.py] Error during unregistration: {str(e)}")
        else:
            print("[recorder.py] Slate post-tick callback was already unregistered or never registered.")

    def tick(self, delta_time: float) -> None:
        """
        Perform actions based on the current state.

        If the recording state is "start", begin recording.
        If the recording state is "stop", stop recording.
        If the recording state is "replay_record", replay the last recording.
        """
        # When resetting, we are waiting for the take recorder to be ready (making it so he has saved the last recording)
        if stateManager.get_recording_status() == stateManagerScript.Status.RESETTING:
            # don’t go to IDLE until Unreal tells us it’s safe
            if not self.tk.take_recorder_ready():
                return

            stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            print("[recorder.py] Resetting state to idle.")
            
            if self.resettingPopUpText:
                popUp.show_popup_message(self.resettingPopUpTitle, self.resettingPopUpText)
                self.resettingPopUpText = None
                self.resettingPopUpTitle = None
            return

        if stateManager.get_recording_status() == stateManagerScript.Status.DIE:
            self.stop()  # Unregister the callback when stopping
            return

        if stateManager.get_recording_status() == stateManagerScript.Status.START:
            self.tk.set_slate_name(stateManager.get_gloss_name())
            print(f"[recorder.py] Starting recording with slate name: {stateManager.get_gloss_name()}")
            self.tk.start_recording()
            stateManager.set_recording_status(stateManagerScript.Status.RECORDING)
            return

        if stateManager.get_recording_status() == stateManagerScript.Status.STOP:
            stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            self.tk.stop_recording()
            return

        if stateManager.get_recording_status() == stateManagerScript.Status.REPLAY_RECORD:
            # ensure we’ve got the very latest take
            if not self.tk.take_recorder_ready():
                return

            print("[recorder.py] Replaying last recording...")
            last_anim, location = self.tk.fetch_last_animation(actor_name=self.actorNameShorthand)

            if last_anim is None or location == stateManager.get_last_location():
                for _ in range(5):
                    last_anim, location = self.tk.fetch_last_animation(actor_name=self.actorNameShorthand)
                    if last_anim is not None:
                        break

                self.resettingPopUpText = "[recorder.py] No last recording found. Set state to idle."
                self.resettingPopUpTitle = "replay"
                if location == stateManager.get_last_location():
                    self.resettingPopUpText = "[recorder.py] Replaying the same recording. Set state to idle. Please re-record if you want the export to work."
                    self.resettingPopUpTitle = "replay"

                stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
                return

            print(f"[recorder.py] Replaying animation at: {location}")
            self.tk.replay_anim(
                replay_actor=self.replayActor,
                anim=last_anim
            )

            self.resettingPopUpText = None
            self.resettingPopUpTitle = None
            stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            return

        # Exporting needs to be done through the main thread since UE5.5, the subthread communicating with the websocket therefore
        # communicates with this main thread loop
        if stateManager.get_recording_status() in (stateManagerScript.Status.FBX_EXPORT, stateManagerScript.Status.EXPORT_FBX):
            # don’t start the export until the panel is ready
            if not self.tk.take_recorder_ready():
                return

            anim, location = self.tk.fetch_last_animation(actor_name=self.actorNameShorthand)
            stateManager.set_last_location(location)
            if not self.tk.export_animation(location, stateManager.folder, stateManager.get_gloss_name(), actor_name=self.actorNameShorthand):
                stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
            else:
                stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)

        # If the recording status is idle, we check if the gloss name is different from the last one
        if stateManager.get_recording_status() == stateManagerScript.Status.IDLE:
            if stateManager.gloss_name_cleaned != self.tk.get_slate() and stateManager.gloss_name_cleaned not in ["", None]:
                print(f"[recorder.py] Gloss name changed from {self.tk.get_slate()} to {self.tk._sanitize_name(stateManager.get_gloss_name())}")
                self.tk.set_slate_name(stateManager.get_gloss_name())

        return

print("[recorder.py] Starting recorder...")
stateManager = stateManagerScript.StateManager(params.record_path)
stateManager.set_folder(params.record_path)
stateManager.set_endpoint_file(params.export_endpoint)
stateManager.set_recording_status(stateManagerScript.Status.IDLE)
tk = takeRecorder.TakeRecorder(stateManager)

ktk = KeepRunningTakeRecorder(tk, "")
ktk.start()

host = params.ws_url
if len(sys.argv) > 1:
    host = sys.argv[1]
wsCom = wsCommunicationScript.websocketCommunication(host, tk, ktk, params.actor_name, params.replay_actor_name)
# wsCom.keep_running_take_recorder = tk
