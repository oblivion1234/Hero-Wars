# ======================================================================
# >> CUSTOM EVENTS
# ======================================================================

# Source.Python
from events.custom import CustomEvent

from events.resource import ResourceFile
from events.variable import StringVariable
from events.variable import ShortVariable
from events.variable import LongVariable
from events.variable import ByteVariable


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'Hero_Pre_Level_Up',
    'Hero_Level_Up',
    'Player_Ultimate',
    'Player_Pre_Hurt'
)


# ======================================================================
# >> EVENT CLASSES
# ======================================================================

class Hero_Pre_Level_Up(CustomEvent):
    cls_id = StringVariable("Hero's class' id")
    id = LongVariable("Hero's unique Python id")


class Hero_Level_Up(CustomEvent):
    cls_id = StringVariable("Hero's class' id")
    id = LongVariable("Hero's unique Python id")
    player_index = ShortVariable("Player's index")
    player_userid = ShortVariable("Player's userid")


class Player_Ultimate(CustomEvent):
    index = ShortVariable("Player's index")
    userid = ShortVariable("Player's userid")


class Player_Pre_Hurt(CustomEvent):
    armor = ByteVariable(
        'The remaining amount of armor the victim has after the damage.')
    attacker = ShortVariable('The userid of the attacking player.')
    dmg_armor = ByteVariable(
        'The amount of damage sustained by the victim\'s armor.')
    dmg_health = ShortVariable(
        'The amount of health the victim lost in the attack.')
    health = ByteVariable(
        'The remaining amount of health the victim has after the damage.')
    hitgroup = ByteVariable('The hitgroup that was damaged in the attack.')
    userid = ShortVariable('The userid of the victim.')
    weapon = StringVariable('The type of weapon used in the attack.')


# ======================================================================
# >> CREATE RESOURCE FILES
# ======================================================================

for event_cls in (
        Hero_Pre_Level_Up,
        Hero_Level_Up,
        Player_Ultimate,
        Player_Pre_Hurt):
    resource_file = ResourceFile(
        'hw/{0}'.format(event_cls.__name__.lower()),
        event_cls
    )
    resource_file.write()
    resource_file.load_events()
