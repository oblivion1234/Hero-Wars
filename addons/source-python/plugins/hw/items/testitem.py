# ======================================================================
# >> IMPORTS
# ======================================================================

# Python
from random import randint

# Hero Wars
from herowars.entities import Item

import herowars.commandlib as cmdlib


# ======================================================================
# >> Exp Boost
# ======================================================================

class ExpBoost(Item):
    name = 'Exp Boost'
    description = 'Grants extra xp on spawn.'
    category = 'Test Items'
    cost = 10
    limit = 3

    def on_spawn(self, player, **eargs):
        amount = randint(1, 15)
        player.hero.exp += amount
        cmdlib.tell(
            player, 
            'ExpBoost granted you {amount} extra experience.'.format(
                amount=amount
            ))
