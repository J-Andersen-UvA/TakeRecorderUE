import unreal
import sys
import gc

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
_active_take_recorder = None
_active_keep_running_take_recorder = None
_active_websocket_communication = None
_active_state_manager = None
_shutdown_callback_handle = None

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
        self._export_retry_count = 0
        self._export_retry_max = 60  # ticks; tune as needed

        self.CSVWriter = CSVWriter.LiveLinkCSVManagerWrapper(stateManager)
        self._last_stopped_take_root = None
        self.diagnostics = DiagnosticsLogger(enabled=False)  # Set to True to enable diagnostics logging
        self.diagnostics.sample("init", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
        # self.CSVWriter.check_cur_subject_available()

    def cleanup_loaded_assets(self) -> None:
        self.diagnostics.sample("before_collect_garbage", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
        if hasattr(unreal, "SystemLibrary") and hasattr(unreal.SystemLibrary, "collect_garbage"):
            try:
                unreal.TraceUtilLibrary.trace_bookmark("MocapPython.GC.Before")
                unreal.SystemLibrary.collect_garbage()
                unreal.TraceUtilLibrary.trace_bookmark("MocapPython.GC.After")
            except Exception as e:
                unreal.log_warning(f"[recorder.py] Failed to collect garbage after asset processing: {e}")
        self.diagnostics.sample("after_collect_garbage", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())

    def get_replay_gloss(self):
        return self.stateManager.gloss_name_of_stopped_recording or self.stateManager.get_gloss_name()

    def get_export_gloss(self):
        return self.stateManager.gloss_name_of_stopped_recording or self.stateManager.get_gloss_name()

    def sync_slate_name(self):
        if self.stateManager.gloss_name_cleaned in ["", None]:
            return

        current_slate = self.tk.get_slate()
        if self.stateManager.gloss_name_cleaned == current_slate:
            return

        print(f"[recorder.py] Gloss name changed from {current_slate} to {self.tk._sanitize_name(self.stateManager.get_gloss_name())}")
        self.tk.set_slate_name(self.stateManager.get_gloss_name())
        self.diagnostics.sample(
            "slate_name_synced",
            state=self.stateManager.get_recording_status(),
            gloss=self.stateManager.get_gloss_name(),
            extra={"previous_slate": current_slate, "new_slate": self.stateManager.gloss_name_cleaned},
        )

    def load_replay_animations(self, replay_gloss):
        for replay_actor in self.replayActors:
            replay_actor.load_expected_animation(self.tk, replay_gloss)

    def replay_animations_ready(self):
        return bool(self.replayActors) and all(
            replay_actor.has_expected_animation_ready()
            for replay_actor in self.replayActors
        )

    def replay_locations_for_diagnostics(self, replay_gloss):
        extra = {
            "replay_gloss": replay_gloss,
            "last_stopped_take_root": self._last_stopped_take_root,
        }
        for replay_actor in self.replayActors:
            extra[replay_actor.actor_shorthand] = replay_actor.last_location
            extra[f"{replay_actor.actor_shorthand}_expected_gloss"] = replay_actor.expected_gloss
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
                "expected_gloss": replay_actor.expected_gloss,
                "location": replay_actor.last_location,
            }
            self.diagnostics.sample("before_replay_actor", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra=replay_extra)
            replay_actor.set_loaded_anim()
            self.diagnostics.sample("after_replay_actor", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra=replay_extra)

    def retry_or_timeout_export(self, export_gloss, locations):
        self._export_retry_count += 1
        if self._export_retry_count < self._export_retry_max:
            return False

        self._export_retry_count = 0
        self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
        self.diagnostics.sample(
            "export_timed_out",
            state=self.stateManager.get_recording_status(),
            gloss=self.stateManager.get_gloss_name(),
            extra={"export_gloss": export_gloss, **locations},
        )
        return True

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

    def spin_down(self) -> None:
        """
        Stop the Python-side recorder services and unregister the editor tick hook.
        """
        unreal.TraceUtilLibrary.trace_bookmark("MocapPython.SpinDown")
        try:
            self.stateManager.set_recording_status(stateManagerScript.Status.DIE)
        except Exception as e:
            unreal.log_warning(f"[recorder.py] Could not set DIE state while spinning down: {e}")
        self.stop()
        unreal.TraceUtilLibrary.trace_bookmark("MocapPython.SpinDown.Complete")

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

            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.TakeRecorderReadyAfterStop")
            self._last_stopped_take_root = self.tk.fetch_last_recording_root_path()
            for replay_actor in self.replayActors:
                replay_actor.last_anim = None
            gc.collect()
            unreal.SystemLibrary.collect_garbage()
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.PostTakeCleanupComplete")
            self.tk.log_source_count("after recording cleanup")
            self.diagnostics.sample("resetting_ready", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            self.sync_slate_name()
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
            self.sync_slate_name()
            print(f"[recorder.py] Starting recording with slate name: {self.stateManager.get_gloss_name()}")
            self.diagnostics.sample("before_start_recording", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.ReleasePreviousReplay.Begin")
            for replay_actor in self.replayActors:
                replay_actor.clear_anim()
            gc.collect()
            unreal.SystemLibrary.collect_garbage()
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.ReleasePreviousReplay.Complete")
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.BeginRecording")
            self.tk.log_source_count("before recording")

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
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.BeginRecording.Complete")
            return

        if self.stateManager.get_recording_status() == stateManagerScript.Status.STOP:
            self.diagnostics.sample("before_stop_recording", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.StopRecording")
            self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            stopped_gloss = self.stateManager.gloss_name_of_stopped_recording or self.stateManager.get_gloss_name()
            self.tk.stop_recording()
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.StopRecording.Complete")
            self.diagnostics.sample("after_stop_recording", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            if self.CSVWriter:
                unreal.TraceUtilLibrary.trace_bookmark("MocapPython.CSVExport")
                ok = self.CSVWriter.stop_and_export(stopped_gloss)
                unreal.TraceUtilLibrary.trace_bookmark("MocapPython.CSVExport.Complete")
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
            replay_gloss = self.get_replay_gloss()
            self.load_replay_animations(replay_gloss)

            self.diagnostics.sample(
                "after_replay_fetch",
                state=self.stateManager.get_recording_status(),
                gloss=self.stateManager.get_gloss_name(),
                extra=self.replay_locations_for_diagnostics(replay_gloss),
            )

            if not self.replay_animations_ready():
                self.retry_or_timeout_replay()
                return

            self._replay_retry_count = 0
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.Replay")
            self.set_replay_actor_animations()
            self.stateManager.set_last_location(self.replayActors[0].last_location)
            self.diagnostics.sample("after_replay", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.Replay.Complete")
            self.stateManager.set_recording_status(stateManagerScript.Status.RESETTING)
            return

        # Exporting needs to be done through the main thread since UE5.5, the subthread communicating with the websocket therefore
        # communicates with this main thread loop
        if self.stateManager.get_recording_status() in (stateManagerScript.Status.FBX_EXPORT, stateManagerScript.Status.EXPORT_FBX):
            # don’t start the export until the panel is ready
            if not self.tk.take_recorder_ready():
                return

            export_gloss = self.get_export_gloss()

            location = self.tk.fetch_animation_path_by_slate(self.actorNameShorthand, export_gloss)
            location2 = self.tk.fetch_animation_path_by_slate(self.actorName2Shorthand, export_gloss) if self.actorName2Shorthand else None
            location3 = self.tk.fetch_animation_path_by_slate(self.actorName3Shorthand, export_gloss) if self.actorName3Shorthand else None
            export_locations = {self.actorNameShorthand: location}
            if self.actorName2Shorthand:
                export_locations[self.actorName2Shorthand] = location2
            if self.actorName3Shorthand:
                export_locations[self.actorName3Shorthand] = location3

            if location is None or (self.actorName2Shorthand and location2 is None) or (self.actorName3Shorthand and location3 is None):
                self.retry_or_timeout_export(export_gloss, export_locations)
                return

            self._export_retry_count = 0
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.Export")
            self.stateManager.set_last_location(location)
            self.diagnostics.sample("before_export_actor1", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location})
            if not self.tk.export_animation(location, self.stateManager.folder, export_gloss, actor_name=self.actorNameShorthand, avatar=self.actorNameShorthand):
                self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
            else:
                self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)
            self.diagnostics.sample("after_export_actor1", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location})

            if self.actorName2Shorthand:
                self.diagnostics.sample("before_export_actor2", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location2})
                if not self.tk.export_animation(location2, self.stateManager.folder, export_gloss, actor_name=self.actorName2Shorthand, subfolder="CC", avatar=self.actorName2Shorthand, preview_mesh=False):
                    self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
                elif self.stateManager.get_recording_status() != stateManagerScript.Status.EXPORT_FAIL:  # only set to success if the first export didn’t fail
                    self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)
                self.diagnostics.sample("after_export_actor2", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location2})

            if self.actorName3Shorthand:
                self.diagnostics.sample("before_export_actor3", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location3})
                if not self.tk.export_animation(location3, self.stateManager.folder, export_gloss, actor_name=self.actorName3Shorthand, subfolder="Vicon", avatar=self.actorName3Shorthand, preview_mesh=False):
                    self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_FAIL)
                elif self.stateManager.get_recording_status() != stateManagerScript.Status.EXPORT_FAIL:  # only set to success if the first export didn’t fail
                    self.stateManager.set_recording_status(stateManagerScript.Status.EXPORT_SUCCESS)
                self.diagnostics.sample("after_export_actor3", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name(), extra={"location": location3})

            location = None
            location2 = None
            location3 = None
            self.cleanup_loaded_assets()
            self.diagnostics.sample("after_export_branch", state=self.stateManager.get_recording_status(), gloss=self.stateManager.get_gloss_name())
            unreal.TraceUtilLibrary.trace_bookmark("MocapPython.Export.Complete")

        # If the recording status is idle, we check if the gloss name is different from the last one
        if self.stateManager.get_recording_status() == stateManagerScript.Status.IDLE:
            self.sync_slate_name()

        return

def add_configured_take_recorder_sources(tk):
    # First actor
    tk.add_actor_to_take_recorder(editorFuncs.get_actor_by_shorthand(params.actor_name_shorthand))

    if params.get('actor2_name_shorthand'):
        # Second actor
        tk.add_actor_to_take_recorder(editorFuncs.get_actor_by_shorthand(params.get('actor2_name_shorthand')))
    if params.get('actor3_name_shorthand'):
        # Third actor
        tk.add_actor_to_take_recorder(editorFuncs.get_actor_by_shorthand(params.get('actor3_name_shorthand')))

def main():
    global _take_recorder_started
    global _active_take_recorder
    global _active_keep_running_take_recorder
    global _active_websocket_communication
    global _active_state_manager

    if _take_recorder_started:
        popUp.show_popup_message("Take Recorder", "Take Recorder is already running.\nUse Stop Take Recorder to spin it down first.")
        return

    _take_recorder_started = True

    unreal.TraceUtilLibrary.trace_bookmark("MocapPython.Setup")
    print("[recorder`.py] Starting recorder...")
    stateManager = stateManagerScript.StateManager(params.record_path)
    stateManager.set_folder(params.record_path)
    stateManager.set_endpoint_file(params.export_endpoint)
    stateManager.set_recording_status(stateManagerScript.Status.IDLE)
    _active_state_manager = stateManager
    tk = takeRecorder.TakeRecorder(stateManager)
    _active_take_recorder = tk
    add_configured_take_recorder_sources(tk)

    ktk = KeepRunningTakeRecorder(tk, stateManager, "")
    ktk.start()
    _active_keep_running_take_recorder = ktk

    host = params.ws_url
    if len(sys.argv) > 1:
        host = sys.argv[1]
    wsCom = wsCommunicationScript.websocketCommunication(host, tk, ktk, params.actor_name, params.replay_actor_name)
    _active_websocket_communication = wsCom
    unreal.TraceUtilLibrary.trace_bookmark("MocapPython.Setup.Complete")
    # wsCom.keep_running_take_recorder = tk

def spin_down_take_recorder(show_popup=True):
    global _take_recorder_started
    global _active_take_recorder
    global _active_keep_running_take_recorder
    global _active_websocket_communication
    global _active_state_manager

    if not _take_recorder_started and _active_keep_running_take_recorder is None and _active_websocket_communication is None:
        if show_popup:
            popUp.show_popup_message("Take Recorder", "Python Take Recorder is not running.")
        return

    unreal.TraceUtilLibrary.trace_bookmark("MocapPython.StopPythonTakeRecorder")

    if _active_keep_running_take_recorder is not None:
        _active_keep_running_take_recorder.spin_down()

    if _active_websocket_communication is not None:
        try:
            _active_websocket_communication.close_connection()
        except Exception as e:
            unreal.log_warning(f"[recorder.py] Failed to close websocket while spinning down: {e}")

    if _active_state_manager is not None:
        try:
            _active_state_manager.set_recording_status(stateManagerScript.Status.IDLE)
        except Exception as e:
            unreal.log_warning(f"[recorder.py] Failed to restore idle state after spin down: {e}")

    _active_take_recorder = None
    _active_keep_running_take_recorder = None
    _active_websocket_communication = None
    _active_state_manager = None
    _take_recorder_started = False
    wsCommunicationScript.websocketCommunication._instance = None

    unreal.TraceUtilLibrary.trace_bookmark("MocapPython.StopPythonTakeRecorder.Complete")
    if show_popup:
        popUp.show_popup_message("Take Recorder", "Python Take Recorder spun down. You can start it again from ToucanTools.")

def restart_take_recorder_panel():
    global _active_take_recorder
    global _active_state_manager

    if _active_state_manager is not None and _active_state_manager.get_recording_status() == stateManagerScript.Status.RECORDING:
        popUp.show_popup_message("Take Recorder", "Cannot restart the Take Recorder panel while recording.")
        return

    if _active_take_recorder is None:
        if _active_state_manager is None:
            _active_state_manager = stateManagerScript.StateManager()
        _active_take_recorder = takeRecorder.TakeRecorder(_active_state_manager)

    restarted = _active_take_recorder.restart_take_recorder_panel()
    source_count = _active_take_recorder.log_source_count("after panel restart source restore check")
    if source_count == 0:
        add_configured_take_recorder_sources(_active_take_recorder)
        _active_take_recorder.log_source_count("after panel restart source restore")

    if restarted:
        popUp.show_popup_message("Take Recorder", "Take Recorder panel restarted.")
    else:
        popUp.show_popup_message("Take Recorder", "Take Recorder panel restart was partial. Check the Unreal log for exposed close-method details.")

def spin_down_take_recorder_on_shutdown(*args, **kwargs):
    try:
        spin_down_take_recorder(show_popup=False)
    except Exception as e:
        try:
            unreal.log_warning(f"[recorder.py] Shutdown spin-down failed: {e}")
        except Exception:
            pass

def register_shutdown_spin_down():
    global _shutdown_callback_handle

    if _shutdown_callback_handle is not None:
        return

    for method_name in ("register_python_shutdown_callback", "register_editor_exit_callback"):
        if not hasattr(unreal, method_name):
            continue
        try:
            _shutdown_callback_handle = getattr(unreal, method_name)(spin_down_take_recorder_on_shutdown)
            unreal.log(f"[recorder.py] Registered shutdown spin-down callback with unreal.{method_name}.")
            return
        except Exception as e:
            unreal.log_warning(f"[recorder.py] Failed to register unreal.{method_name}: {e}")

    unreal.log_warning("[recorder.py] No Unreal Python shutdown callback API was exposed; use Stop Take Recorder before closing the editor.")

register_shutdown_spin_down()

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

Button(
    menu_path="LevelEditor.MainMenu.ToucanTools",
    section_name="TakeRecorderSection",
    label="Stop Take Recorder",
    callback=spin_down_take_recorder,
    tooltip="Stops the Python Take Recorder tick hook and websocket connection.",
    overwrite=True
)

Button(
    menu_path="LevelEditor.MainMenu.ToucanTools",
    section_name="TakeRecorderSection",
    label="Restart Take Recorder Panel",
    callback=restart_take_recorder_panel,
    tooltip="Experimental: closes and reopens the Take Recorder panel, then restores sources if needed.",
    overwrite=True
)
