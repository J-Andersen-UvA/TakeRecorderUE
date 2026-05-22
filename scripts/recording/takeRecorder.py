import unreal
import scripts.utils.UEFileManagerScript as UEFileManager
import scripts.utils.popUp as popUp
import scripts.state.stateManagerScript as stateManagerScript
import scripts.export.exportAndSend as exportAndSend
import re
from datetime import datetime

ANIMATION_RECORDER_KEYWORD = "animation"


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

    def __init__(self, stateManager):
        self.stateManager = stateManager

        unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
        self.take_recorder_panel = None
        self.metadata = None
        self.ensure_take_recorder_panel()
        self.levelSequence = unreal.LevelSequence
        self.metadata = self.take_recorder_panel.get_take_meta_data()
        self.UEFileFuncs = UEFileManager.UEFileFunctionalities()        

    # make it callable
    def __call__(self):
        return True

    @staticmethod
    def _sanitize_name(name: str, replacement: str = "_") -> str:
        if name is None:
            return ""

        # any character _not_ in A–Z a–z 0–9 space _ or -
        _SANITIZE_RE = re.compile(r'[^0-9A-Za-z _-]')
        return _SANITIZE_RE.sub(replacement, name)

    def ensure_take_recorder_panel(self) -> bool:
        panel = unreal.TakeRecorderBlueprintLibrary.get_take_recorder_panel()
        if panel is None:
            panel = unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()

        if panel is None:
            unreal.log_error("[TakeRecorder] Could not open Take Recorder panel.")
            return False

        # Optional: UE5.7 C++ API has IsPanelOpen; Python name may differ by build.
        # So only call if it exists.
        if hasattr(panel, "is_panel_open") and not panel.is_panel_open():
            panel = unreal.TakeRecorderBlueprintLibrary.open_take_recorder_panel()
            if panel is None:
                unreal.log_error("[TakeRecorder] Take Recorder panel exists but is not open and could not be reopened.")
                return False

        self.take_recorder_panel = panel
        self.metadata = self.take_recorder_panel.get_take_meta_data()
        return True

    def get_slate(self) -> str:
        """Retrieve the slate information from the take recorder panel."""
        self.metadata = self.take_recorder_panel.get_take_meta_data()
        return self.metadata.get_slate()

    def set_slate_name(self, name : str) -> None:
        """
        Sets the slate name for the Take Recorder panel.
        
        :param name: The name to set as the slate.
        """
        clean_name = self._sanitize_name(name)
        self.metadata = self.take_recorder_panel.get_take_meta_data()
        self.metadata.set_slate(clean_name)

    def get_sources(self):
        """Retrieve the sources from the take recorder panel."""
        lala = unreal.TakeRecorderBlueprintLibrary().get_take_recorder_panel()
        return lala.get_sources()

    def get_slate_from_take(self) -> str:
        """Retrieve the slate information from the current take."""
        lala = unreal.TakeRecorderBlueprintLibrary().get_take_recorder_panel()
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
        if self.take_recorder_ready():
            self.take_recorder_panel.start_recording()
            return

    def stop_recording(self):
        """
        Stop recording.

        This function stops the recording process using the take recorder panel.
        """
        try:
            self.take_recorder_panel.stop_recording()
        except Exception as e:
            print(f"Error stopping recording: {e}")
            popUp.show_popup_message("Error stopping recording", f"Error stopping recording: {e}")

    def fetch_last_recording(self):
        """
        Fetch last recording.

        Returns:
        - level_sequence (unreal.LevelSequence): The last recorded level sequence.
        """
        return self.take_recorder_panel.get_last_recorded_level_sequence()
        # return self.take_recorder_panel.get_level_sequence()

    def fetch_last_recording_root_path(self):
        """
        Fetch the package path for the last recorded root level sequence.
        """
        last_record = self.fetch_last_recording()
        if last_record is None:
            return None

        return last_record.get_path_name().split(".")[0]

    def _last_recording_path_parts(self):
        last_record = self.fetch_last_recording()
        if last_record is None:
            return None, None, None

        unreal_take = last_record.get_path_name().split(".")[0]
        unreal_scene = unreal_take.rsplit("/", 1)[-1]
        take_folder = unreal_take.rsplit("/", 1)[0]
        return unreal_take, unreal_scene, take_folder

    def _animation_path_candidates(self, unreal_take, unreal_scene, take_folder, actor_name):
        asset_name = f"{actor_name}_{unreal_scene}"
        return [
            f"{unreal_take}_Subscenes/Animation/{asset_name}",
            f"{take_folder}/Animation/{asset_name}",
        ]

    def fetch_animation_path_by_slate(self, actor_name="GlassesGuyRecord", slate_name=None):
        """
        Find a recorded animation by actor and slate in the shared Animation folder.
        This is useful when Take Recorder's last-recorded sequence lags behind the
        newest assets, especially with source subsequences disabled.
        """
        if not slate_name or not hasattr(unreal, "EditorAssetLibrary"):
            return None

        _, _, take_folder = self._last_recording_path_parts()
        if take_folder is None:
            take_folder = f"/Game/Cinematics/Takes/{datetime.now().strftime('%Y-%m-%d')}"

        clean_slate = self._sanitize_name(slate_name)
        anim_dir = f"{take_folder}/Animation"
        prefix = f"{actor_name}_{clean_slate}"

        try:
            if not unreal.EditorAssetLibrary.does_directory_exist(anim_dir):
                return None

            matches = []
            for path in unreal.EditorAssetLibrary.list_assets(anim_dir, recursive=False, include_folder=False):
                asset_path = path.split(".")[0]
                asset_name = asset_path.rsplit("/", 1)[-1]
                if asset_name.startswith(prefix):
                    matches.append(asset_path)

            if matches:
                matches.sort()
                return matches[-1]
        except Exception as e:
            unreal.log_warning(f"[TakeRecorder.py] Failed to find animation by slate in {anim_dir}: {e}")

        return None

    def animation_paths_for_recording_root(self, recording_root):
        """
        Return recorded animation asset paths for a take root in both Take Recorder layouts.
        """
        if not recording_root or not hasattr(unreal, "EditorAssetLibrary"):
            return []

        scene_name = recording_root.rsplit("/", 1)[-1]
        take_folder = recording_root.rsplit("/", 1)[0]
        anim_dirs = [
            f"{recording_root}_Subscenes/Animation",
            f"{take_folder}/Animation",
        ]

        paths = []
        seen = set()
        for anim_dir in anim_dirs:
            try:
                if not unreal.EditorAssetLibrary.does_directory_exist(anim_dir):
                    continue
                for path in unreal.EditorAssetLibrary.list_assets(anim_dir, recursive=False, include_folder=False):
                    asset_path = path.split(".")[0]
                    if asset_path.endswith("_" + scene_name) and asset_path not in seen:
                        seen.add(asset_path)
                        paths.append(asset_path)
            except Exception as e:
                unreal.log_warning(f"[TakeRecorder.py] Failed to list animation assets in {anim_dir}: {e}")

        return paths

    def fetch_animation_path_for_recording_root(self, recording_root, actor_name="GlassesGuyRecord"):
        """
        Fetch one actor animation path from a known take root.
        """
        if not recording_root:
            return None

        scene_name = recording_root.rsplit("/", 1)[-1]
        take_folder = recording_root.rsplit("/", 1)[0]
        candidates = self._animation_path_candidates(recording_root, scene_name, take_folder, actor_name)

        if hasattr(unreal, "EditorAssetLibrary"):
            for candidate in candidates:
                try:
                    if unreal.EditorAssetLibrary.does_asset_exist(candidate):
                        return candidate
                except Exception:
                    pass

            for path in self.animation_paths_for_recording_root(recording_root):
                asset_name = path.rsplit("/", 1)[-1]
                if asset_name.startswith(actor_name + "_"):
                    return path

        return candidates[0]

    def fetch_last_animation(self, actor_name="GlassesGuyRecord"):
        """
        Fetch last animation.

        Returns:
        - level_sequence (unreal.AnimSequence): The last recorded level sequence.
        """
        animLocation = self.fetch_last_animation_path(actor_name=actor_name)
        if animLocation is None:
            return None, None

        animation_asset = unreal.load_asset(animLocation)

        return animation_asset, animLocation

    def fetch_last_animation_path(self, actor_name="GlassesGuyRecord"):
        """
        Fetch the path for the last recorded animation without loading the asset.
        """
        unrealTake, unrealScene, takeFolder = self._last_recording_path_parts()
        if unrealTake is None:
            print("No last recording found, returning None")
            return None

        candidates = self._animation_path_candidates(unrealTake, unrealScene, takeFolder, actor_name)
        if hasattr(unreal, "EditorAssetLibrary"):
            for candidate in candidates:
                try:
                    if unreal.EditorAssetLibrary.does_asset_exist(candidate):
                        return candidate
                except Exception:
                    pass

        return candidates[0]

    def fetch_last_recording_assets(self):
        """
        Fetch last recording assets.

        This function fetches the assets recorded in the last recording session.

        Returns:
        - files_list (list): A list of file names of assets recorded in the last session.
        """
        root = self.fetch_last_recording_root_path()
        return self.animation_paths_for_recording_root(root)

    def take_recorder_ready(self):
        """
        Check if the take recorder is ready.

        This function checks if the take recorder panel is ready for recording.

        Returns:
        - ready (bool): True if the take recorder is ready, False otherwise.
        """
        err = self.take_recorder_panel.can_start_recording()
        err_str = "" if err is None else str(err).strip()
        if err_str:
            unreal.log_warning(f"Take Recorder is not ready to start recording because: {err_str}.")
        return not err or str(err).strip() == ""
    
    def error_test(self):
        """
        Check if the take recorder is ready.

        This function checks if the take recorder panel is ready for recording.

        Returns:
        - ready (bool): True if the take recorder is ready, False otherwise.
        """
        print("Error Test")
        popUp.show_popup_message("Error Test", "This is a pop-up message from Unreal Python!")
        return False

    def export_animation(self, location, folder, gloss_name, actor_name="GlassesGuyRecord", subfolder: str = "", avatar: str = None, preview_mesh: bool = True, force_front_x_axis: bool = False):
        if not gloss_name:
            gloss_name = self.stateManager.get_gloss_name()
        print(f"Exporting last recording: {gloss_name}...")

        if location is None:
            self.stateManager.flip_export_status()
            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            popUp.show_popup_message("Export Failed", f"[TakeRecorder.py] No animation found for {actor_name} / {gloss_name}")
            return False
        if hasattr(unreal, "EditorAssetLibrary") and not unreal.EditorAssetLibrary.does_asset_exist(location):
            self.stateManager.flip_export_status()
            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            popUp.show_popup_message("Export Failed", f"[TakeRecorder.py] Animation asset does not exist: {location}")
            return False

        success, full_export_path = exportAndSend.export_animation(location, self.stateManager.folder, gloss_name, subfolder=subfolder, avatar=avatar, preview_mesh=preview_mesh, force_front_x_axis=force_front_x_axis)

        if not success:
            self.stateManager.flip_export_status()
            self.stateManager.set_recording_status(stateManagerScript.Status.IDLE)
            popUp.show_popup_message("Export Failed", f"[TakeRecorder.py] Export failed for {gloss_name}")
            return False

        print(f"Exporting last recording done: {gloss_name}\tPath: {location}")

        exportAndSend.copy_paste_file_to_vicon_pc(
            source=full_export_path,
            subfolder=subfolder,
            avatar=avatar
        )

        return True

    def add_actor_to_take_recorder(self, actor: unreal.Actor):
        """
        Adds an actor to the Take Recorder as a source.
        """
        if not actor:
            unreal.log_error("No actor provided.")
            return

        # Grab source container
        sources = self.take_recorder_panel.get_sources()

        # Use the Actor-source helper
        new_source = unreal.TakeRecorderActorSource.add_source_for_actor(actor, sources)
        if new_source:
            self.keep_only_animation_recording(new_source)
            unreal.log(f"Added '{actor.get_name()}' to Take Recorder sources.")
        else:
            unreal.log_error(f"Failed to add '{actor.get_name()}' to Take Recorder sources.")

    def keep_only_animation_recording(self, actor_source) -> None:
        """
        Keep only skeletal mesh component recording on the actor source.
        """
        try:
            property_map = actor_source.get_editor_property("recorded_properties")
        except Exception as e:
            unreal.log_warning(f"[TakeRecorder.py] Could not read recorded properties: {e}")
            return

        detected = self._count_skeletal_mesh_maps(property_map)
        if detected <= 0:
            self._log_recorded_property_names(property_map)
            unreal.log_warning("[TakeRecorder.py] Found 0 skeletal mesh components; leaving Take Recorder source unchanged.")
            return

        kept = self._prune_property_map_to_skeletal_mesh(property_map)
        unreal.log(f"[TakeRecorder.py] Skeletal-mesh-only source setup kept {kept} skeletal mesh component map(s).")

    def _count_skeletal_mesh_maps(self, property_map) -> int:
        if not property_map:
            return 0

        count = 1 if self._property_map_records_skeletal_mesh(property_map) else 0

        for child in self._get_property_map_array(property_map, ("children", "Children")):
            count += self._count_skeletal_mesh_maps(child)

        return count

    def _prune_property_map_to_skeletal_mesh(self, property_map) -> int:
        if not property_map:
            return 0

        kept_here = 0
        if self._property_map_records_skeletal_mesh(property_map):
            kept_here += 1
            self._keep_animation_properties_if_visible(property_map)
        else:
            try:
                property_map.set_editor_property("properties", [])
            except Exception:
                for recorded_property in self._get_property_map_array(property_map, ("properties", "Properties")):
                    self._set_recorded_property_enabled(recorded_property, False)

        kept_children = []
        for child in self._get_property_map_array(property_map, ("children", "Children")):
            child_kept = self._prune_property_map_to_skeletal_mesh(child)
            if child_kept > 0:
                kept_here += child_kept
                kept_children.append(child)

        try:
            property_map.set_editor_property("children", kept_children)
        except Exception:
            pass

        return kept_here

    @staticmethod
    def _property_map_records_skeletal_mesh(property_map) -> bool:
        recorded_object = None
        for field in ("recorded_object", "RecordedObject"):
            try:
                recorded_object = property_map.get_editor_property(field)
                break
            except Exception:
                pass

        if not recorded_object:
            return False

        try:
            return isinstance(recorded_object, unreal.SkeletalMeshComponent)
        except Exception:
            pass

        try:
            class_name = recorded_object.get_class().get_name()
        except Exception:
            class_name = type(recorded_object).__name__

        return "SkeletalMeshComponent" in class_name

    def _keep_animation_properties_if_visible(self, property_map) -> None:
        properties = self._get_property_map_array(property_map, ("properties", "Properties"))
        animation_properties = [
            recorded_property
            for recorded_property in properties
            if self._is_animation_recorded_property(recorded_property)
        ]

        if not animation_properties:
            unreal.log_warning(
                "[TakeRecorder.py] Skeletal mesh component found, but no explicit animation recorder property was exposed to Python; keeping that skeletal mesh map intact."
            )
            return

        try:
            property_map.set_editor_property("properties", animation_properties)
        except Exception:
            for recorded_property in properties:
                self._set_recorded_property_enabled(recorded_property, self._is_animation_recorded_property(recorded_property))

    @staticmethod
    def _get_property_map_array(property_map, names):
        for name in names:
            try:
                value = property_map.get_editor_property(name)
                return list(value) if value else []
            except Exception:
                pass

        return []

    @staticmethod
    def _is_animation_recorded_property(recorded_property) -> bool:
        names = []
        for field in ("recorder_name", "RecorderName", "property_name", "PropertyName"):
            try:
                names.append(str(recorded_property.get_editor_property(field)).lower())
            except Exception:
                pass
            try:
                names.append(str(getattr(recorded_property, field)).lower())
            except Exception:
                pass

        return any(ANIMATION_RECORDER_KEYWORD in name for name in names)

    @staticmethod
    def _set_recorded_property_enabled(recorded_property, enabled: bool) -> None:
        for field in ("enabled", "b_enabled", "bEnabled", "BEnabled"):
            try:
                recorded_property.set_editor_property(field, enabled)
                return
            except Exception:
                pass
            try:
                setattr(recorded_property, field, enabled)
                return
            except Exception:
                pass

    def _log_recorded_property_names(self, property_map, depth=0) -> None:
        if not property_map or depth > 4:
            return

        try:
            recorded_object = property_map.get_editor_property("recorded_object")
        except Exception:
            recorded_object = None

        found_names = []
        for recorded_property in self._get_property_map_array(property_map, ("properties", "Properties")):
            values = []
            for field in ("recorder_name", "RecorderName", "property_name", "PropertyName"):
                try:
                    values.append(f"{field}={recorded_property.get_editor_property(field)}")
                except Exception:
                    pass
                try:
                    values.append(f"{field}={getattr(recorded_property, field)}")
                except Exception:
                    pass
            found_names.append("; ".join(values) if values else str(recorded_property))

        unreal.log_warning(
            f"[TakeRecorder.py] Recorded property map depth={depth} object={recorded_object} properties={found_names[:12]}"
        )

        for child in self._get_property_map_array(property_map, ("children", "Children")):
            self._log_recorded_property_names(child, depth + 1)
