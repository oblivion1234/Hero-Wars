# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.database import load_player_data
from herowars.database import save_player_data
from herowars.database import load_hero_data
from herowars.database import save_hero_data

from herowars.entities import Hero

from herowars.tools import find_element

from herowars.configs import database_path
from herowars.configs import starting_heroes
from herowars.configs import default_lang_key

# Source.Python
from players.entity import PlayerEntity

from players.helpers import index_from_userid

from messages import SayText2


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all___ = (
    'player',
    'get_player',
    'create_player',
    'remove_player'
)


# ======================================================================
# >> GLOBALS
# ======================================================================

players = []


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def get_player(userid):
    """Gets a player with matching userid.

    Loops through the players list and returns a player with matching
    userid to the provided parameter value.

    Args:
        userid: Userid of the player to find

    Returns:
        Player with matching userid
    """

    return find_element(players, 'userid', userid)


def create_player(userid):
    """Creates a new player, fetching his data from the database.

    Creates a new player object, loads any saved data from the database
    based on SteamID, makes sure the player gets the starting heroes
    and has a current hero set. Finally returns the player after adding
    him to the global players list.

    Args:
        userid: Userid of the player to create

    Returns:
        New player who's been added to the players list
    """

    # Create a new player and load his data from the database (if any)
    player = _Player(index_from_userid(userid))
    load_player_data(database_path, player)

    # Make sure player gets the starting hero(es)
    heroes = Hero.get_subclasses()
    for cls_id in starting_heroes:
        hero_cls = find_element(heroes, 'cls_id', cls_id)
        if hero_cls and not find_element(player.heroes, 'cls_id', cls_id):
            player.heroes.append(hero_cls())

    # Make sure the player has a current hero
    if not player.hero and player.heroes:
        player._hero = player.heroes[0]

    # Add the player to the global list and return the player
    players.append(player)
    return player


def remove_player(userid):
    """Removes a player, inserting his data into the database.

    Finds a player with given userid, saving his data into the database
    and removing him from the global players list.

    Args:
        userid: Userid of the player to remove
    """

    # Attempt to get the player
    player = get_player(userid)
    if player:

        # Save player's data and remove him
        save_player_data(database_path, player)
        players.remove(player)


# ======================================================================
# >> CLASSES
# ======================================================================

class _Player(PlayerEntity):
    """Player class for Hero Wars related activity.

    Player extends Source.Python's PlayerEntity, implementing player
    sided properties for Hero Wars related information.
    Adds methods such as burn, freeze and push.

    Attributes:
        gold: Player's Hero Wars gold, used to purchase heroes and items
        hero: Player's hero currently in use
        heroes: List of owned heroes
        lang_key: Language key used to display messages and menus
    """

    def __new__(cls, index, gold=0, lang_key=default_lang_key):
        """Creates a new Hero Wars player.

        Args:
            index: Player's index
            gold: Player's Hero Wars gold
            lang_key: Language key used for messages and menus
        """

        self = super().__new__(cls, index)
        self._gold = gold
        self._hero = None
        self.heroes = []
        self.lang_key = lang_key
        return self

    @property
    def gold(self):
        """Getter for player's Hero Wars gold.

        Returns:
            Player's gold
        """

        return self._gold

    @gold.setter
    def gold(self, gold):
        """Setter for player's Hero Wars gold.

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

        # Destroy current hero's items
        for item in self.hero.items:
            if not item.permanent:
                self.hero.items.remove(item)

        # Save his current hero and change to the new one
        save_hero_data(database_path, self.steamid, self.hero)
        self._hero = hero

    def signal(self, message):
        """Sends a message to a player using SayText2.

        Args:
            message: Text to display to the player
        """

        SayText2(message=message).send(self.index)
