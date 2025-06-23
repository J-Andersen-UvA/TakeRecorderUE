import unreal
import scripts.editorFuncs as editorFuncs

def torchToggle(actor):
    """Toggles the torch that the actor is holding."""
    # Get the actor by name
    if actor is None:
        unreal.log_warning("Torch bearing actor not found in the current world.")
        return False
    
    # From the actor get the components called: torch & torchFire
    torch = None
    torchFire = None
    for component in actor.get_components_by_tag(tag="torch"):
        if component.get_name() == "torch":
            torch = component
        elif component.get_name() == "torchFire":
            torchFire = component
    
    if torch is None or torchFire is None:
        unreal.log_warning("Torch bearing actor does not have the required components.")
        return False
    
    # Toggle the visibility of the torch and torchFire
    torch.set_visibility(not torch.is_visible())
    torchFire.set_visibility(not torchFire.is_visible())

    # Do something to toggle the torch
    return True

# example usage
torchToggle(editorFuncs.get_actor_by_name("mageGuyRecord_C_2"))
