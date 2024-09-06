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

def export_fbx(map_asset_path, sequencer_asset_path, root_sequencer_asset_path, output_file):
    # Load the map, get the world
    world = unreal.EditorLoadingAndSavingUtils.load_map(map_asset_path)
    # Load the sequence asset
    sequence = unreal.load_asset(sequencer_asset_path, unreal.LevelSequence)
    root_sequence = unreal.load_asset(root_sequencer_asset_path, unreal.LevelSequence)
    # Set Options
    export_options = unreal.FbxExportOption()
    export_options.ascii = False
    export_options.level_of_detail = True
    export_options.export_source_mesh = True
    export_options.map_skeletal_motion_to_root = True
    export_options.export_source_mesh = True
    export_options.vertex_color = True
    export_options.export_morph_targets = True
    export_options.export_preview_mesh = True
    export_options.force_front_x_axis = False
    # Get Bindings
    bindings = sequence.get_bindings()
    tracks = sequence.get_tracks()
    # Export
    export_fbx_params = unreal.SequencerExportFBXParams(world, sequence, root_sequence, bindings, tracks, export_options, output_file)
    unreal.SequencerTools.export_level_sequence_fbx(export_fbx_params)    
