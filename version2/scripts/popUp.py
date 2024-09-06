import unreal

def show_popup_message(title, message):
    """
    Display a pop-up message in the Unreal Engine editor.

    Args:
        title (str): The title of the pop-up window.
        message (str): The text to display in the pop-up.
    """
    unreal.EditorDialog.show_message(
        title=title,
        message=message,
        message_type=unreal.AppMsgType.OK
    )

# # Example usage
# show_popup_message("Information", "This is a pop-up message from Unreal Python!")
