import unreal
import threading
import requests  # or whatever you use
import os
from datetime import datetime
from scripts.utils.logger import RecordingLog, RecordingLogSingleAnim, guess_gloss_from_filename_csv
import shutil
_log = RecordingLog()

def export_animation(animation_asset_path : str, export_path : str, name : str = "animation", ascii : bool = False, force_front_x_axis : bool = False):
    if not export_path.endswith("/"):
        export_path += "/"

    # Full export filename including .fbx extension
    full_export_path = f"{export_path}{name}.fbx"

    FbxExportOptions = unreal.FbxExportOption()
    FbxExportOptions.ascii = ascii
    FbxExportOptions.export_local_time = True
    FbxExportOptions.export_morph_targets = True
    FbxExportOptions.export_preview_mesh = True
    FbxExportOptions.force_front_x_axis = force_front_x_axis

    task = unreal.AssetExportTask()
    task.set_editor_property("exporter", unreal.AnimSequenceExporterFBX())
    task.options = FbxExportOptions
    task.automated = True
    task.filename = full_export_path
    task.object = unreal.load_asset(animation_asset_path)
    task.write_empty_files = False
    task.replace_identical = True
    task.prompt = False

    # Export the animation
    if not unreal.Exporter.run_asset_export_task(task):
        raise ValueError(f"Failed to export animation at path {animation_asset_path}")

    _log.add_asset(name, "retargeted_animation_fbx", full_export_path, machine="UE", status="ready")
    return True, full_export_path # success, path

def _copy_file_in_background(source: str, destination: str):
    try:
        shutil.copyfile(source, destination)
        print(f"[Exporter] Copied {source} -> {destination}")
        machine_name = None
        if destination.startswith("//") or destination.startswith("\\\\"):
            machine_name = destination.split("\\")[2] if destination.startswith("\\\\") else destination[2:].split("/")[0]
        RecordingLogSingleAnim._update_metadata(destination, machine=machine_name)
    except Exception as e:
        print(f"[Exporter] Failed to copy {source} -> {destination}\nError: {e}")

def copy_paste_file_to_vicon_pc(source: str, destination_root: str = "//VICON-SB001869/Recordings"):
    # Validate source
    if not os.path.exists(source):
        return False, f"Source file does not exist: {source}"

    date_str = datetime.now().strftime("%Y-%m-%d")
    destination_dated_folder = os.path.join(destination_root, date_str)

    # Determine gloss name from filename
    if source.endswith(".csv"):
        anim_name = guess_gloss_from_filename_csv(source)
    else:
        anim_name = os.path.splitext(os.path.basename(source))[0]

    destination_folder = os.path.join(destination_dated_folder, anim_name, "unreal")

    try:
        # Ensure remote folder exists (UNC paths are supported if permissions allow)
        os.makedirs(destination_folder, exist_ok=True)
    except Exception as e:
        return False, f"Failed to create remote folder: {destination_folder}\nError: {e}"

    destination = os.path.join(destination_folder, os.path.basename(source))

    # Copy file in a background thread
    thread = threading.Thread(
        target=_copy_file_in_background,
        args=(source, destination),
        daemon=True
    )
    thread.start()

    return True, destination

def _upload_in_background(file_path: str, endpoint: str, avatar_name: str, gloss_name: str):
    try:
        print(f"[Uploader] POST → {endpoint}")
        print(f"[Uploader] data: avatarName={avatar_name}, glosName={gloss_name}")
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f)}
            data = {
                "avatarName": avatar_name,
                "glosName":    gloss_name,
            }
            resp = requests.post(endpoint, files=files, data=data, verify=False, timeout=60)
        print(f"[Uploader] Response {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        print("[Uploader] Upload successful")
    except Exception as e:
        print(f"[Uploader] Background upload failed: {e}")


def send_fbx_to_url_async(
    file_path: str,
    endpoint: str,
    avatar_name: str,
    gloss_name: str
):
    thread = threading.Thread(
        target=_upload_in_background,
        args=(file_path, endpoint, avatar_name, gloss_name),
        daemon=True
    )
    thread.start()
