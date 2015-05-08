# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.database import save_hero_data
from hw.database import load_player_data

from hw.entities import Hero

from hw.tools import find_element

from hw.configs import starting_heroes
from hw.configs import player_entity_class

# Source.Python
from players.helpers import playerinfo_from_userid

from messages import SayText2


# ======================================================================
# >> GLOBALS
# ======================================================================

_player_data = {}


# ======================================================================
# >> CLASSES
# ======================================================================

class Player(player_entity_class):
    """Player class for Hero-Wars related activity and data.

    Attributes:
        gold: Player's Hero-Wars gold, used to purchase heroes and items
        hero: Player's hero currently in use
        heroes: List of owned heroes
    """

    def __init__(self, index):
        """Initializes a new player instance.

        Args:
            index: Index of the player
        """

        if self.userid not in _player_data:
            _player_data[self.userid] = {
                'gold': 0,
                'hero': None,
                'heroes': []
            }

            # Load player's data
            load_player_data(self)

            # Make sure the player gets his starting heroes
            heroes = Hero.get_subclasses()
            for cid in starting_heroes:
                hero_cls = find_element(heroes, 'cid', cid)
                if hero_cls and not find_element(self.heroes, 'cid', cid):
                    self.heroes.append(hero_cls())

            # Make sure the player has a hero
            if not self.hero:
                self.hero = self.heroes[0]

    @property
    def gold(self):
        """Getter for player's Hero-Wars gold.

        Returns:
            Player's gold
        """

        return _player_data[self.userid]['gold']

    @gold.setter
    def gold(self, gold):
        """Setter for player's Hero-Wars gold.

        Raises:
            ValueError: If gold is set to a negative value
        """

        if gold < 0:
            raise ValueError('Attempt to set negative gold for a player.')
        _player_data[self.userid]['gold'] = gold

    @property
    def hero(self):
        """Getter for player's current hero.

        Returns:
            Player's hero
        """

        return _player_data[self.userid]['hero']

    @hero.setter
    def hero(self, hero):
        """Setter for player's current hero.

        Makes sure player owns the hero and saves his current hero to
        the database before switching to the new one.

        Args:
            hero: Hero to switch to

        Raises:
            ValueError: Hero not owned by the player
        """

        # Make sure player owns the hero
        if hero not in self.heroes:
            raise ValueError('Hero {cid} not owned by {steamid}.'.format(
                cid=hero.cid, steamid=self.steamid
            ))

        # If player has a current hero
        if self.hero:

            # Save current hero's data
            save_hero_data(self.steamid, self.hero)

            # Destroy current hero's items
            for item in self.hero.items:
                if not item.permanent:
                    self.hero.items.remove(item)

        # Change to the new hero
        _player_data[self.userid]['hero'] = hero

    @property
    def heroes(self):
        """Getter for plaeyr's heroes.

        Returns:
            A list of player's heroes.
        """

        return _player_data[self.userid]['heroes']
