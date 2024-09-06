import unreal
import csv
import httpx


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

	return


#we want to get csv file and then convert te rows, pass them on to execute the export_fbx function
def get_csv_rows(csv_file):
	with open(csv_file, mode='r') as file:
		reader = csv.DictReader(file)
		for row in reader:
			unrealTake = row['unreal_take']
			#LevelSequence /Game/Cinematics/Takes/2024-04-03/Scene_1_303.Scene_1_303
			#replace levelSequence fwith empty string
			unrealTake = unrealTake.replace("LevelSequence ", "")
			unrealScene = unrealTake.split(".")[1]
			unrealTake = unrealTake.split(".")[0]
			#add _Subscenes/GlassesGuyRecord
			unrealTake = unrealTake + "_Subscenes/GlassesGuyRecord" + "_" +unrealScene

			print(unrealTake)
   
			# Accessing by column header name	
			export_fbx('/Game/mainlevel', unrealTake, unrealTake, "C:\\RecordingsUE\\"+row['glos']+".fbx")
   
			send_file_to_url("C:\\RecordingsUE\\"+row['glos']+".fbx")
   
   
   
		
async def send_file_to_url(file_path):
        """
        Asynchronously send a file to a URL.

        Parameters:
        - file_path (str): File path of the file to send.
        - url (str): URL to send the file to.

        Prints the response from the server after sending the file.
        """
        print("Sending file...")
        with httpx.AsyncClient(verify=False) as client:
            # Open the file and prepare it for sending. No need to use aiohttp.FormData with httpx.
            with open(file_path, "rb") as file:
                files = {"file": (file_path, file, "multipart/form-data")}
                response = await client.post(
                    "https://leffe.science.uva.nl:8043/fbx2glb/upload/",
                    files=files,
                )  # 'verify=False' skips SSL verification.

                # No need to check _is_multipart or to explicitly close the file; it's managed by the context manager.
                print(response.text)
		
#/Game/Cinematics/Takes/2024-04-03/Scene_1_303_Subscenes/GlassesGuyRecord_Scene_1_303
# export_fbx("/Game/mainlevel", "/Game/Cinematics/Takes/2024-04-03/Scene_1_294_Subscenes/GlassesGuyRecord_Scene_1_294", "/Game/Cinematics/Takes/2024-04-03/Scene_1_294_Subscenes/GlassesGuyRecord_Scene_1_294", "C:\\RecordingsUE\\testPY.fbx")

get_csv_rows(r"C:\\Users\\gotters\\Documents\\Unreal Projects\\MyProject4\\Plugins\\casper_ue.csv")