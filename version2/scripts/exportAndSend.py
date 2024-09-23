import unreal
import scripts.levelSequence as levelSequence
import asyncio
import httpx

#########################################################################################################
#                                               FBX EXPORT AND SENDER                                   #
#########################################################################################################


class ExportandSend:
    """
    Utility class for exporting and sending files asynchronously.

    This class provides methods to execute export operations and send files
    asynchronously to a specified URL.

    Attributes:
    - glossName (str): Name used for the file export.
    - file (str): File path for the export operation.

    Methods:
    - execExport(): Execute the export operation.
    - done(future): Callback function executed when the operation is done.
    - send_file_to_url(file_path, url): Asynchronously send a file to a URL.
    """
    def __init__(self, glossName, unreal_take):
        self.glossName = glossName
        self.unreal_take = unreal_take
        self.file = "D:\\RecordingsUE\\" + self.glossName + ".fbx"
        self.sequencerTools = levelSequence.SequencerTools()
        self.execExport()

    def execExport(self) -> None:
        print(self.unreal_take)

        self.sequencerTools.set_root_sequence(self.unreal_take)
        self.sequencerTools.set_level_sequence(self.unreal_take)
        self.sequencerTools.set_file(self.file)
        self.sequencerTools.execute_export()

        asyncio.run(
            self.send_file_to_url(
                self.file, "https://leffe.science.uva.nl:8043/fbx2glb/upload/"
            )
        )

    def execExportLast(self) -> None:
        """
        Execute the export operation.

        Creates a SequencerTools instance to fetch the last recording and
        export it using asyncio to send the file to a specified URL.
        """
        last_recording = tk.fetch_last_recording()
        self.sequencerTools.set_root_sequence(last_recording)
        self.sequencerTools.set_level_sequence(last_recording)
        self.sequencerTools.set_file(self.file)
        self.sequencerTools.execute_export()

        asyncio.run(
            self.send_file_to_url(
                self.file, "https://leffe.science.uva.nl:8043/fbx2glb/upload/"
            )
        )

    def done(self, future):
        print(future.result())

    async def send_file_to_url(self, file_path, url):
        """
        Asynchronously send a file to a URL.

        Parameters:
        - file_path (str): File path of the file to send.
        - url (str): URL to send the file to.

        Prints the response from the server after sending the file.
        """
        print("Sending file...")
        async with httpx.AsyncClient(verify=False) as client:
            # Open the file and prepare it for sending. No need to use aiohttp.FormData with httpx.
            with open(file_path, "rb") as file:
                files = {"file": (file_path, file, "multipart/form-data")}
                response = await client.post(
                    url,
                    files=files,
                )  # 'verify=False' skips SSL verification.

                # No need to check _is_multipart or to explicitly close the file; it's managed by the context manager.
                print(response.text)

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
    return True, full_export_path
