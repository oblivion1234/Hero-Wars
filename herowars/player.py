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

from herowars.translations import get_translation

from herowars.menus import current_hero_info_menu

# Source.Python
from players.entity import PlayerEntity

from players.helpers import index_from_userid

from messages import SayText2


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
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

def get_player(value, key='userid'):
    """Gets a player with matching key.

    Loops through the players list and returns a player with matching
    key to the provided parameter value.

    Args:
        value: Value of the player's key to look for
        key: Key to compare the value to

    Returns:
        Player with matching key or None
    """

    return find_element(players, key, value)


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
        player.hero = player.heroes[0]

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

        # If player has a current hero
        if self.hero:

            # Save current hero's data
            save_hero_data(database_path, self.steamid, self.hero)

            # Destroy current hero's items
            for item in self.hero.items:
                if not item.permanent:
                    self.hero.items.remove(item)

            # Stop listening to current hero's level up event
            self.hero.e_level_up -= self._send_level_up_message

        # Change to the new hero and listen to its level up event
        self._hero = hero
        hero.e_level_up += self._send_level_up_message

    @property
    def cs_team(self):
        """Returns player's Counter-Strike team."""

        return ['un', 'spec', 't', 'ct'][self.team]

    @cs_team.setter
    def cs_team(self, value):
        """Sets player's Counter-Strike team."""

        self.team = ['un', 'spec', 't', 'ct'].index(value)

    def _send_level_up_message(self, sender, *args):
        """Event listener for hero's level up event."""

        translation = get_translation(self.lang_key, 'other', 'level_up')
        SayText2(message=translation.format(
            name=sender.name, level=sender.level,
            exp=sender.exp, max_exp=sender.required_exp
        )).send(self.index)

        # Check if player can use skill points
        for skill in self.hero.skills:
            if (self.hero.skill_points >= skill.cost 
                    and skill.level < skill.max_level 
                    and self.hero.level >= skill.required_level):

                # If there are usable skill points, send the menu
                current_hero_info_menu(self).send(self.index)
                break
            
