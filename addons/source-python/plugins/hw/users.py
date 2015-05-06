# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.database import save_hero_data

from hw.entities import Hero

from hw.tools import find_element

from hw.configs import starting_heroes
from hw.configs import player_entity_class

# Source.Python
from players.helpers import playerinfo_from_userid
from players.helpers import index_from_userid

from messages import SayText2


# ======================================================================
# >> GLOBALS
# ======================================================================

users = {
    # userid: User
}


# ======================================================================
# >> CLASSES
# ======================================================================

class User(object):
    """User class for Hero-Wars related activity and data.

    Attributes:
        gold: Player's Hero-Wars gold, used to purchase heroes and items
        hero: Player's hero currently in use
        heroes: List of owned heroes
    """

    def __init__(self, userid):
        """Initializes a new User instance.

        Args:
            userid: Userid of the user
        """

        self.userid = userid
        self._gold = 0
        self._hero = None
        self.heroes = []

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
    def steamid(self):
        """Returns user's steamid."""

        return playerinfo_from_userid(self.userid).get_networkid_string()

    def get_entity(self):
        """Returns a PlayerEntity instance from user."""

        return player_entity_class(index_from_userid(self.userid))

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
            save_hero_data(self.steamid, self.hero)

            # Destroy current hero's items
            for item in self.hero.items:
                if not item.permanent:
                    self.hero.items.remove(item)

        # Change to the new hero
        self._hero = hero

    def message(self, text):
        """Sends a message to an user through SayText2.

        Args:
            text: Text to send
        """

        SayText2(message=text).send(index_from_userid(self.userid))
