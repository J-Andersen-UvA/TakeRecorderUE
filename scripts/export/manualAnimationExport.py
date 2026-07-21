import os
from datetime import datetime

import unreal

from scripts.config.params import Config
import scripts.export.exportAndSend as exportAndSend


@unreal.uclass()
class AnimationExportSelection(unreal.Object):
    animation = unreal.uproperty(unreal.AnimSequence)


def select_and_export_animation():
    selection = unreal.new_object(AnimationExportSelection)
    options = unreal.EditorDialogLibraryObjectDetailsViewOptions(
        show_object_name=False,
        allow_search=False,
        allow_resizing=True,
        min_width=600,
        min_height=220,
    )

    if not unreal.EditorDialog.show_object_details_view("Test Animation Export", selection, options):
        return

    animation = selection.get_editor_property("animation")
    if animation is None:
        unreal.EditorDialog.show_message(
            "Test Animation Export",
            "Select an animation asset before exporting.",
            unreal.AppMsgType.OK,
        )
        return

    params = Config()
    export_folder = os.path.join(
        params.record_path,
        datetime.now().strftime("%Y-%m-%d"),
        "ManualExportTest",
    )
    os.makedirs(export_folder, exist_ok=True)

    success, export_path = exportAndSend.export_animation(
        animation.get_path_name(),
        export_folder,
        animation.get_name(),
        preview_mesh=False,
    )

    if success:
        unreal.EditorDialog.show_message(
            "Test Animation Export",
            f"Exported to:\n{export_path}",
            unreal.AppMsgType.OK,
        )
