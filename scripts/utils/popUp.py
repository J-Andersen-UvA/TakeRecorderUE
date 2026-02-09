import unreal
import time

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

def show_timed_popup(title, message, seconds=5):
    with unreal.ScopedSlowTask(seconds, title) as task:
        task.make_dialog(True)  # True = allow cancel
        for i in range(seconds):
            if task.should_cancel():
                break
            task.enter_progress_frame(1, f"{message} ({seconds - i}s)")
            time.sleep(1)

# # Example usage
# show_popup_message("Information", "This is a pop-up message from Unreal Python!")
# show_timed_popup("Please Re-record!", "Neem opnieuw op!", seconds=5)