# ======================================================================
# >> CUSTOM EVENTS
# ======================================================================

# Source.Python
from events import Event

from events.custom import CustomEvent

from events.resource import ResourceFile
from events.variable import StringVariable
from events.variable import ShortVariable
from events.variable import LongVariable

# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'Pre_Hero_Level_Up',
    'Hero_Level_Up'
)


# ======================================================================
# >> PRE HERO LEVEL UP EVENT
# ======================================================================

class Pre_Hero_Level_Up(CustomEvent):
    cls_id = StringVariable("Hero's class' id")
    id = LongVariable("Hero's unique Python id")


event_file = ResourceFile('herowars/pre_hero_level_up', Pre_Hero_Level_Up)
event_file.write()
event_file.load_events()


# ======================================================================
# >> HERO LEVEL UP EVENT
# ======================================================================

class Hero_Level_Up(CustomEvent):
    cls_id = StringVariable("Hero's class' id")
    id = LongVariable("Hero's unique Python id")
    player_index = ShortVariable("Player's index")
    player_userid = ShortVariable("Player's userid")


event_file = ResourceFile('herowars/hero_level_up', Hero_Level_Up)
event_file.write()
event_file.load_events()
