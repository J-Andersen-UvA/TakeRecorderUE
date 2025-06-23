import unreal

# Function to get the name of the skeletal mesh from the animation
def get_skeletal_mesh_name_from_animation(animation_path):
    print(f"Loading animation asset from path: {animation_path}")
    # Load the animation asset
    animation_asset = unreal.load_asset(animation_path)
    
    # Check if the asset was successfully loaded
    if not animation_asset:
        print("Failed to load asset. Please check the asset path.")
        return None
    
    # Check if the asset is a valid animation asset
    if not isinstance(animation_asset, unreal.AnimSequence):
        print(f"Loaded asset is not an AnimSequence. It is a {type(animation_asset).__name__}.")
        return None

    print(f"Successfully loaded animation asset: {animation_asset.get_name()}")

    # Get the skeleton from the animation asset
    skeleton = animation_asset.get_editor_property('skeleton')
    if not skeleton:
        print("Failed to get skeleton from the animation asset.")
        return None
    
    print(f"Skeleton: {skeleton.get_name()}")

    if "_Skeleton" in skeleton.get_name():
        return skeleton.get_name().replace("_Skeleton", "")
    
    # Get all skeletal mesh references associated with the skeleton
    skeletal_meshes = skeleton.get_referencers(unreal.SkeletalMesh)
    if not skeletal_meshes:
        print("No skeletal meshes found for this animation.")
        return None
    
    # Get the name of the first skeletal mesh found (assuming there's at least one)
    skeletal_mesh_name = skeletal_meshes[0].get_name()
    return skeletal_mesh_name


# Example usage
animation_path = '/Game/Cinematics/Takes/2024-07-08/test_01_Subscenes/Animation/GlassesGuyRecord_test_01'
skeletal_mesh_name = get_skeletal_mesh_name_from_animation(animation_path)
print(f"Skeletal mesh name: {skeletal_mesh_name}")
