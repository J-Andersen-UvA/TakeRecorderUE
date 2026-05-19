import unreal


class PlayLastActor:
    """
    Small wrapper for the replay actor blueprint.

    The actor blueprint is expected to expose an AnimSequence variable named
    CurrentAnim.
    """

    def __init__(self, actor: unreal.Actor, actor_name: str = None, actor_shorthand: str = None):
        self.actor = actor
        self.actor_name = actor_name
        self.actor_shorthand = actor_shorthand
        self.expected_gloss = None
        self.last_location = None
        self.last_anim = None
        self.last_replayed_location = None

    @property
    def is_valid(self) -> bool:
        return self.actor is not None

    def set_anim(self, anim: unreal.AnimSequence) -> bool:
        if not self.actor or not anim:
            return False

        for property_name in ("CurrentAnim", "current_anim"):
            try:
                self.actor.set_editor_property(property_name, anim)
                unreal.log(f"[PlayLastActor] Set {self.actor.get_name()}.{property_name} = {anim.get_name()}")
                return True
            except Exception:
                pass

        unreal.log_warning(
            f"[PlayLastActor] Could not set CurrentAnim on {self.actor.get_name()}. "
            "Make sure the blueprint variable is exposed as CurrentAnim."
        )
        return False

    def begin_waiting_for(self, gloss_name):
        if self.expected_gloss == gloss_name:
            return

        self.expected_gloss = gloss_name
        self.last_location = None
        self.last_anim = None

    def fetch_expected_animation_path(self, take_recorder, gloss_name):
        self.begin_waiting_for(gloss_name)
        location = take_recorder.fetch_animation_path_by_slate(self.actor_shorthand, gloss_name)
        self.last_location = location
        return location

    def load_expected_animation(self, take_recorder, gloss_name):
        location = self.fetch_expected_animation_path(take_recorder, gloss_name)
        self.last_anim = unreal.load_asset(location) if location else None
        return self.last_anim

    def has_expected_animation_ready(self) -> bool:
        return (
            self.last_location is not None
            and self.last_location != self.last_replayed_location
            and self.last_anim is not None
        )

    def set_loaded_anim(self) -> bool:
        if not self.set_anim(self.last_anim):
            return False

        self.last_replayed_location = self.last_location
        return True
