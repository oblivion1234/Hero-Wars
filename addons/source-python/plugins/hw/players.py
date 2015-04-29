# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.database import load_player_data
from hw.database import save_hero_data

from hw.entities import Hero

from hw.configs import database_path
from hw.configs import starting_heroes

# Xtend
from xtend.players import PlayerEntity

from xtend.tools import CachedAttr
from xtend.tools import find_element


# ======================================================================
# >> CLASSES
# ======================================================================

class Player(PlayerEntity):
    """Player class for Hero-Wars related activity.

    Player extends Source.Python's PlayerEntity, implementing player
    sided properties for Hero-Wars related information.
    Adds methods such as burn, freeze and push.

    Attributes:
        gold: Player's Hero-Wars gold, used to purchase heroes and items
        hero: Player's hero currently in use
        heroes: List of owned heroes
        lang_key: Language key used to display messages and menus
    """

    _db_loaded = CachedAttr(bool)
    _gold = CachedAttr(int)
    _hero = CachedAttr(type(None))
    heroes = CachedAttr(list)

    def __init__(self, index, *args, **kwargs):
        """Initializes a new PlayerEntity instance.

        Args:
            index: Index of the player's entity
        """

        # Do nothing if the player's data has already been loaded
        if self._db_loaded:
            return

        # Load player's data from the database
        load_player_data(database_path, self)
        self._db_loaded = True

        # Make sure the player gets his starting heroes
        heroes = Hero.get_subclasses()
        for cls_id in starting_heroes:
            hero_cls = find_element(heroes, 'cls_id', cls_id)
            if hero_cls and not find_element(self.heroes, 'cls_id', cls_id):
                self.heroes.append(hero_cls())

        # Make sure the player has a current hero
        if not self.hero and self.heroes:
            self.hero = self.heroes[0]

    @property
    def gold(self):
        """Getter for player's Hero-Wars gold.

        Returns:
            Player's gold
        """

        return self._gold

    @gold.setter
    def gold(self, gold):
        """Setter for player's Hero-Wars gold.

        Raises:
            ValueError: If gold is set to a negative value
        """

        if gold < 0:
            raise ValueError('Attempt to set negative gold for a player.')
        self._gold = gold

    @property
    def hero(self):
        """Getter for player's current hero.

        Returns:
            Player's hero
        """

        return self._hero

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
            raise ValueError('Hero {cls_id} not owned by {steamid}.'.format(
                cls_id=hero.cls_id, steamid=self.steamid
            ))

        # If player has a current hero
        if self.hero:

            # Save current hero's data
            save_hero_data(database_path, self.steamid, self.hero)

            # Destroy current hero's items
            for item in self.hero.items:
                if not item.permanent:
                    self.hero.items.remove(item)

        # Change to the new hero
        self._hero = hero

    @property
    def cs_team(self):
        """Returns player's Counter-Strike team."""

        return ['un', 'spec', 't', 'ct'][self.team]

    @cs_team.setter
    def cs_team(self, value):
        """Sets player's Counter-Strike team."""

        self.team = ['un', 'spec', 't', 'ct'].index(value)
