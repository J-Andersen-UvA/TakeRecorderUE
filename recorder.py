import unreal
import sys

import scripts.recording.takeRecorder as takeRecorder
import scripts.communication.wsCommunicationScript as wsCommunicationScript
import scripts.state.stateManagerScript as stateManagerScript
import scripts.utils.popUp as popUp
import scripts.utils.editorFuncs as editorFuncs
import scripts.utils.CSVWriter as CSVWriter
from scripts.config.params import Config
from scripts.utils.ui_utils import Button
import scripts.export.exportAndSend as exportAndSend
from scripts.utils.logger import RecordingLog, guess_gloss_from_filename
_log = RecordingLog()

_take_recorder_started = False

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

    def __init__(self, tk: takeRecorder.TakeRecorder, stateManager : stateManagerScript, file):
        print("Initializing KeepRunningTakeRecorder...")
        self.tk = tk
        self.stateManager = stateManager
        self.actorName = params.actor_name
        self.actorNameShorthand = params.actor_name_shorthand
        self.replayActor = editorFuncs.get_actor_by_name(params.replay_actor_name)
        if self.replayActor is None:
            print(f"[recorder.py] Replay actor '{params.replay_actor_name}' not found in the level.")
            popUp.show_popup_message("KeepRunningTakeRecorder", f"[recorder.py] Replay actor '{params.replay_actor_name}' not found in the level.")

        self.slate_post_tick_handle = None
        self.resettingPopUpText = None
        self.resettingPopUpTitle = None

        self.CSVWriter = CSVWriter.LiveLinkCSVManagerWrapper(stateManager)
        # self.CSVWriter.check_cur_subject_available()

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
        if self.stateManager.get_recording_status() == stateManagerScript.Status.RESETTING:

            # Wait until Unreal confirms everything is saved
            if not self.tk.take_recorder_ready():
                return

            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            print("[recorder.py] Resetting state to idle.")

            if self.resettingPopUpText:
                popUp.show_popup_message(self.resettingPopUpTitle, self.resettingPopUpText)
                self.resettingPopUpText = None
                self.resettingPopUpTitle = None

            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.DIE:
            self.stop()  # Unregister the callback when stopping
            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.START:
            self.tk.set_slate_name(self.stateManager.get_gloss_name())
            print(f"[recorder.py] Starting recording with slate name: {self.stateManager.get_gloss_name()}")
            self.tk.start_recording()
            if self.CSVWriter and not self.CSVWriter.manager.is_recording():
                self.CSVWriter.start_recording(self.stateManager.get_gloss_name())
            self.stateManager.set_recording_status(stateManagerScript.Status.RECORDING)
            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.STOP:
            self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            self.tk.stop_recording()
            if self.CSVWriter:
                ok = self.CSVWriter.stop_and_export(self.stateManager.get_gloss_name())
                for csv_path in self.CSVWriter.last_file_paths:
                    gloss = guess_gloss_from_filename(csv_path)

                    # Add to logging system
                    _log.add_asset(
                        gloss,
                        "blendshape_csv",
                        csv_path,
                        machine="UE",
                        status="ready"
                    )

                    if csv_path:
                        unreal.log(f"[recorder.py] Exporting CSV file at: {csv_path}")
                        success, msg = exportAndSend.copy_paste_file_to_vicon_pc(
                            source=csv_path,
                            destination_root="//VICON-SB001869/Recordings"
                        )
                        if not success:
                            popUp.show_popup_message(
                                "CSV Export",
                                f"[recorder.py] CSV export to Vicon PC failed: {msg}"
                            )

                if not ok:
                    unreal.log_error("[CSVWriter] Failed to export CSV file.")
                else:
                    self.CSVWriter.check_last_file()

            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.REPLAY_RECORD:

            # Wait until Unreal finished saving the take.
            if not self.tk.take_recorder_ready():
                return

            print("[recorder.py] Replaying last recording...")

            last_anim, location = self.tk.fetch_last_animation(actor_name=self.actorNameShorthand)
            old_location = self.stateManager.get_last_location()

            # If missing or identical → retry (UE might still be finishing)
            if last_anim is None or location == old_location:

                for _ in range(10):  # give UE more time
                    last_anim, location = self.tk.fetch_last_animation(actor_name=self.actorNameShorthand)
                    if last_anim is not None and location != old_location:
                        break

                # After retries, still nothing or same recording
                if last_anim is None:
                    self.resettingPopUpTitle = "replay"
                    self.resettingPopUpText = "[recorder.py] No last recording found."
                    self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
                    return

                if location == old_location:
                    self.resettingPopUpTitle = "replay"
                    self.resettingPopUpText = "[recorder.py] Replaying the same recording. Please re-record."
                    self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
                    return

            # Successful new take → replay
            print(f"[recorder.py] Replaying animation at: {location}")
            self.tk.replay_anim(
                replay_actor=self.replayActor,
                anim=last_anim
            )

            # Update last location
            self.stateManager.set_last_location(location)

            self.resettingPopUpText = None
            self.resettingPopUpTitle = None

            self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            return

        # Exporting needs to be done through the main thread since UE5.5, the subthread communicating with the websocket therefore
        # communicates with this main thread loop
        if self.stateManager.get_recording_status() in (stateManagerScript.Status.FBX_EXPORT, stateManagerScript.Status.EXPORT_FBX):
            # don’t start the export until the panel is ready
            if not self.tk.take_recorder_ready():
                return

            anim, location = self.tk.fetch_last_animation(actor_name=self.actorNameShorthand)
            self.stateManager.set_last_location(location)
            if not self.tk.export_animation(location, self.stateManager.folder, self.stateManager.gloss_name_of_stopped_recording, actor_name=self.actorNameShorthand):
                self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
            else:
                self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)

        # If the recording status is idle, we check if the gloss name is different from the last one
        if self.stateManager.get_recording_status() == stateManagerScript.Status.IDLE:
            if self.stateManager.gloss_name_cleaned != self.tk.get_slate() and self.stateManager.gloss_name_cleaned not in ["", None]:
                print(f"[recorder.py] Gloss name changed from {self.tk.get_slate()} to {self.tk._sanitize_name(self.stateManager.get_gloss_name())}")
                self.tk.set_slate_name(self.stateManager.get_gloss_name())

        return

def main():
    global _take_recorder_started

    if _take_recorder_started:
        popUp.show_popup_message("Take Recorder", "Take Recorder is already running.\nPlease restart Unreal Engine to reset it.")
        return

    _take_recorder_started = True

    print("[recorder`.py] Starting recorder...")
    stateManager = stateManagerScript.StateManager(params.record_path)
    stateManager.set_folder(params.record_path)
    stateManager.set_endpoint_file(params.export_endpoint)
    stateManager.set_recording_status(stateManagerScript.Status.IDLE)
    tk = takeRecorder.TakeRecorder(stateManager)
    tk.add_actor_to_take_recorder(editorFuncs.get_actor_by_shorthand(params.actor_name_shorthand))

    ktk = KeepRunningTakeRecorder(tk, stateManager, "")
    ktk.start()

    host = params.ws_url
    if len(sys.argv) > 1:
        host = sys.argv[1]
    wsCom = wsCommunicationScript.websocketCommunication(host, tk, ktk, params.actor_name, params.replay_actor_name)
    # wsCom.keep_running_take_recorder = tk

# 1) Create a brand-new tab called “ToucanTools”
Button(
    menu_path="LevelEditor.MainMenu",
    section_name="ToucanToolsSection",
    label="ToucanTools",
    callback=lambda: None,
    tooltip="I asked my bird if it could multitask. It said, “Toucan!”",
    overwrite=True,
    tab=True  # <== this makes it a tab, not a button
)

# 2) Now add a real button under that tab
Button(
    menu_path="LevelEditor.MainMenu.ToucanTools",  # <== must match the internal name you used above
    section_name="TakeRecorderSection",
    label="Run Take Recorder",
    callback=main,
    tooltip="Runs the Take Recorder to record animations.",
    overwrite=True
)
