# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.entities import Item

import herowars.commandlib as cmdlib


# ======================================================================
# >> Longjump Boots
# ======================================================================

class LongjumpBoots(Item):
    name = 'Longjump Boots'
    description = 'Grants you longjump'
    category = 'Test Items'
    cost = 10

    def on_jump(self, player, **eargs):
        cmdlib.boost_velocity(player, 1.2, 1.2)
