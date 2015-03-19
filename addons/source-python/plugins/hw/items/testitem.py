# ======================================================================
# >> IMPORTS
# ======================================================================

# Python
from random import randint

# Hero-Wars
from hw.entities import Item


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
        player.tell('ExpBoost granted you {0} exp.'.format(amount))
