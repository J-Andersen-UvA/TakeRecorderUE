import unreal
import sys

import scripts.recording.takeRecorder as takeRecorder
import scripts.communication.wsCommunicationScript as wsCommunicationScript
import scripts.state.stateManagerScript as stateManagerScript
import scripts.utils.popUp as popUp
import scripts.utils.editorFuncs as editorFuncs
import scripts.utils.CSVWriter as CSVWriter
from scripts.utils.diagnostics import DiagnosticsLogger
from scripts.config.params import Config
from scripts.utils.ui_utils import Button
from scripts.replay.playLastActor import PlayLastActor
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

        # Initialize actors and their shorthands from the config
        self.actorName = params.actor_name
        self.actorNameShorthand = params.actor_name_shorthand
        self.replayActor = PlayLastActor(
            editorFuncs.get_actor_by_name(params.replay_actor_name),
            self.actorName,
            self.actorNameShorthand,
        )
        if not self.replayActor.is_valid:
            print(f"[recorder.py] Replay actor '{params.replay_actor_name}' not found in the level.")
            popUp.show_popup_message("KeepRunningTakeRecorder", f"[recorder.py] Replay actor '{params.replay_actor_name}' not found in the level.")

        # Second actor (optional)
        self.actorName2 = params.get('actor2_name')
        self.actorName2Shorthand = params.get('actor2_name_shorthand')
        replay_actor2_name = params.get('replay_actor2_name')
        self.replayActor2 = PlayLastActor(
            editorFuncs.get_actor_by_name(replay_actor2_name),
            self.actorName2,
            self.actorName2Shorthand,
        ) if replay_actor2_name else None
        if replay_actor2_name and not self.replayActor2.is_valid:
            print(f"[recorder.py] Replay actor '{replay_actor2_name}' not found in the level.")
            popUp.show_popup_message("KeepRunningTakeRecorder", f"[recorder.py] Replay actor '{replay_actor2_name}' not found in the level.")

        # Third actor, vicon no replay (optional)
        self.actorName3 = params.get('actor3_name')
        self.actorName3Shorthand = params.get('actor3_name_shorthand')

        self.replayActors = [actor for actor in (self.replayActor, self.replayActor2) if actor and actor.is_valid]

        self.slate_post_tick_handle = None
        self.resettingPopUpText = None
        self.resettingPopUpTitle = None

        self._replay_retry_count = 0
        self._replay_retry_max = 60  # ticks; tune as needed

        self.CSVWriter = CSVWriter.LiveLinkCSVManagerWrapper(stateManager)
        self._last_stopped_take_root = None
        self.diagnostics = DiagnosticsLogger()
        self.diagnostics.sample("init", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
        # self.CSVWriter.check_cur_subject_available()

    def cleanup_loaded_assets(self) -> None:
        self.diagnostics.sample("before_collect_garbage", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
        if hasattr(unreal, "SystemLibrary") and hasattr(unreal.SystemLibrary, "collect_garbage"):
            try:
                unreal.SystemLibrary.collect_garbage()
            except Exception as e:
                unreal.log_warning(f"[recorder.py] Failed to collect garbage after asset processing: {e}")
        self.diagnostics.sample("after_collect_garbage", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())

    def get_replay_gloss(self):
        return self.stateManager.gloss_name_of_stopped_recording or self.stateManager.get_gloss_name()

    def load_replay_animations(self, replay_gloss):
        for replay_actor in self.replayActors:
            replay_actor.load_animation(self.tk, self._last_stopped_take_root, replay_gloss)

    def replay_animations_ready(self, old_location):
        return bool(self.replayActors) and all(
            replay_actor.has_new_animation(old_location)
            for replay_actor in self.replayActors
        )

    def replay_locations_for_diagnostics(self, replay_gloss):
        extra = {
            "replay_gloss": replay_gloss,
            "last_stopped_take_root": self._last_stopped_take_root,
        }
        for replay_actor in self.replayActors:
            extra[replay_actor.actor_shorthand] = replay_actor.last_location
        return extra

    def retry_or_timeout_replay(self):
        self._replay_retry_count += 1
        if self._replay_retry_count < self._replay_retry_max:
            return False

        self._replay_retry_count = 0
        self.resettingPopUpTitle = "replay"
        self.resettingPopUpText = "[recorder.py] No new recording found to replay (timed out)."
        self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
        self.diagnostics.sample("replay_timed_out", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
        return True

    def set_replay_actor_animations(self):
        for replay_actor in self.replayActors:
            replay_extra = {
                "actor": replay_actor.actor_name,
                "shorthand": replay_actor.actor_shorthand,
                "location": replay_actor.last_location,
            }
            self.diagnostics.sample("before_replay_actor", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra=replay_extra)
            replay_actor.set_loaded_anim()
            self.diagnostics.sample("after_replay_actor", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra=replay_extra)

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

            self._last_stopped_take_root = self.tk.fetch_last_recording_root_path()
            self.diagnostics.sample("resetting_ready", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            self.diagnostics.sample(
                "idle_after_resetting",
                state=self.stateManager.get_recording_status(),
                gloss=self.stateManager.get_gloss_name(),
                extra={"last_stopped_take_root": self._last_stopped_take_root},
            )
            print("[recorder.py] Resetting state to idle.")

            if self.resettingPopUpText:
                popUp.show_timed_popup(self.resettingPopUpTitle, self.resettingPopUpText, seconds=5)
                # popUp.show_popup_message(self.resettingPopUpTitle, self.resettingPopUpText)
                self.resettingPopUpText = None
                self.resettingPopUpTitle = None

            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.DIE:
            self.stop()  # Unregister the callback when stopping
            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.START:
            self.tk.set_slate_name(self.stateManager.get_gloss_name())
            print(f"[recorder.py] Starting recording with slate name: {self.stateManager.get_gloss_name()}")
            self.diagnostics.sample("before_start_recording", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())

            try:
                self.tk.start_recording()
            except Exception as e:
                unreal.log_error(f"[recorder.py] Take Recorder failed to start: {e}")
                popUp.show_popup_message(
                    "Take Recorder Error",
                    f"Failed to start recording:\n{e}\n\nCheck Project Settings > Engine > General Settings > Timecode Provider."
                )
                self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
                self.diagnostics.sample("start_recording_failed", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"error": str(e)})
                return

            if self.CSVWriter and not self.CSVWriter.manager.is_recording():
                self.CSVWriter.set_save_folder(self.stateManager.folder)
                self.CSVWriter.start_recording(self.stateManager.get_gloss_name())

            self.stateManager.set_recording_status(stateManagerScript.Status.RECORDING)
            self.diagnostics.sample("after_start_recording", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.STOP:
            self.diagnostics.sample("before_stop_recording", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            self.tk.stop_recording()
            self.diagnostics.sample("after_stop_recording", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
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

            self.diagnostics.sample("after_stop_csv", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.REPLAY_RECORD:
            if not self.tk.take_recorder_ready():
                return

            self.diagnostics.sample("before_replay_fetch", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            old_location = self.stateManager.get_last_location()
            replay_gloss = self.get_replay_gloss()
            self.load_replay_animations(replay_gloss)

            self.diagnostics.sample(
                "after_replay_fetch",
                state=self.stateManager.get_recording_status(),
                gloss=self.stateManager.get_gloss_name(),
                extra=self.replay_locations_for_diagnostics(replay_gloss),
            )

            if not self.replay_animations_ready(old_location):
                self.retry_or_timeout_replay()
                return

            self._replay_retry_count = 0
            self.set_replay_actor_animations()
            self.stateManager.set_last_location(self.replayActors[0].last_location)
            self.diagnostics.sample("after_replay", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            return

        # Exporting needs to be done through the main thread since UE5.5, the subthread communicating with the websocket therefore
        # communicates with this main thread loop
        if self.stateManager.get_recording_status() in (stateManagerScript.Status.FBX_EXPORT, stateManagerScript.Status.EXPORT_FBX):
            # don’t start the export until the panel is ready
            if not self.tk.take_recorder_ready():
                return

            location = None
            location2 = None
            location3 = None

            export_gloss = self.stateManager.gloss_name_of_stopped_recording or self.stateManager.get_gloss_name()

            location = self.tk.fetch_animation_path_for_recording_root(self._last_stopped_take_root, self.actorNameShorthand)
            if location is None:
                location = self.tk.fetch_animation_path_by_slate(self.actorNameShorthand, export_gloss)
            if location is None:
                location = self.tk.fetch_last_animation_path(actor_name=self.actorNameShorthand)
            self.stateManager.set_last_location(location)
            self.diagnostics.sample("before_export_actor1", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location})
            if not self.tk.export_animation(location, self.stateManager.folder, self.stateManager.gloss_name_of_stopped_recording, actor_name=self.actorNameShorthand, avatar=self.actorNameShorthand):
                self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
            else:
                self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)
            self.diagnostics.sample("after_export_actor1", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location})

            if self.actorName2Shorthand:
                location2 = self.tk.fetch_animation_path_for_recording_root(self._last_stopped_take_root, self.actorName2Shorthand)
                if location2 is None:
                    location2 = self.tk.fetch_animation_path_by_slate(self.actorName2Shorthand, export_gloss)
                if location2 is None:
                    location2 = self.tk.fetch_last_animation_path(actor_name=self.actorName2Shorthand)
                self.diagnostics.sample("before_export_actor2", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location2})
                if not self.tk.export_animation(location2, self.stateManager.folder, self.stateManager.gloss_name_of_stopped_recording, actor_name=self.actorName2Shorthand, subfolder="CC", avatar=self.actorName2Shorthand, preview_mesh=False):
                    self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
                elif self.stateManager.get_recording_status() != stateManagerScript.Status.EXPORT_FAIL:  # only set to success if the first export didn’t fail
                    self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)
                self.diagnostics.sample("after_export_actor2", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location2})

            if self.actorName3Shorthand:
                location3 = self.tk.fetch_animation_path_for_recording_root(self._last_stopped_take_root, self.actorName3Shorthand)
                if location3 is None:
                    location3 = self.tk.fetch_animation_path_by_slate(self.actorName3Shorthand, export_gloss)
                if location3 is None:
                    location3 = self.tk.fetch_last_animation_path(actor_name=self.actorName3Shorthand)
                self.diagnostics.sample("before_export_actor3", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location3})
                if not self.tk.export_animation(location3, self.stateManager.folder, self.stateManager.gloss_name_of_stopped_recording, actor_name=self.actorName3Shorthand, subfolder="Vicon", avatar=self.actorName3Shorthand, preview_mesh=False):
                    self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
                elif self.stateManager.get_recording_status() != stateManagerScript.Status.EXPORT_FAIL:  # only set to success if the first export didn’t fail
                    self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)
                self.diagnostics.sample("after_export_actor3", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location3})

            location = None
            location2 = None
            location3 = None
            self.cleanup_loaded_assets()
            self.diagnostics.sample("after_export_branch", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())

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
    # First actor
    tk.add_actor_to_take_recorder(editorFuncs.get_actor_by_shorthand(params.actor_name_shorthand))

    if params.get('actor2_name_shorthand'):
        # Second actor
        tk.add_actor_to_take_recorder(editorFuncs.get_actor_by_shorthand(params.get('actor2_name_shorthand')))
    if params.get('actor3_name_shorthand'):
        # Third actor
        tk.add_actor_to_take_recorder(editorFuncs.get_actor_by_shorthand(params.get('actor3_name_shorthand')))

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
