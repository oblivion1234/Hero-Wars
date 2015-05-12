# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.database import save_player_data
from hw.database import load_player_data
from hw.database import save_hero_data

from hw.entities import Hero

from hw.tools import find_element

from hw.configs import starting_heroes
from hw.configs import player_entity_class

# Source.Python
from players.helpers import index_from_userid

from memory import make_object
from memory.hooks import HookType

from entities import TakeDamageInfo
from entities.helpers import index_from_pointer

from events import Event

from weapons.entity import WeaponEntity


# ======================================================================
# >> GLOBALS
# ======================================================================

_player_data = {}
_is_hooked = False

# ======================================================================
# >> GAME EVENTS
# ======================================================================

@Event
def player_disconnect(game_event):
    """Saves player's data upon disconnect."""

    userid = game_event.get_int('userid')
    player = Player.from_userid(userid)
    save_player_data(player)
    del _player_data[userid]


@Event
def player_spawn(game_event):
    """Saves player's data upon spawning."""

    player = Player.from_userid(game_event.get_int('userid'))
    save_player_data(player)

# ======================================================================
# >> HOOKS
# ======================================================================

def weapon_bump(args):
    """
    Hooked to a function that is fired any time a weapon is
    requested to be picked up in game.
    """

    player_index = index_from_pointer(args[0])
    weapon_index = index_from_pointer(args[1])
    weapon = WeaponEntity(weapon_index)
    player = Player(player_index)
    eargs = {'weapon': weapon}
    if weapon.classname in player.restrictions:
        player.hero.execute_skills('weapon_pickup_failed', player=player, **eargs)
        return False
    else:
        player.hero.execute_skills('weapon_pickup', player=player, **eargs)

def take_damage(args):
    """
    Hooked to a function that is fired any time an
    entity takes damage.
    """

    player_index = index_from_pointer(args[0])
    info = make_object(TakeDamageInfo, args[1])
    defender = Player(player_index)
    attacker = Player(info.attacker)
    eargs = {
        'attacker': attacker,
        'defender': defender,
        'info': info
    }
    if not player_index == info.attacker:
        defender.hero.execute_skills('player_pre_defend', **eargs)
        attacker.hero.execute_skills('player_pre_attack', **eargs)

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

    @classmethod
    def from_userid(cls, userid):
        """Returns a Player instance from an userid.

        Args:
            userid: Userid of the player
        """

        return cls(index_from_userid(userid))

    def __init__(self, index):
        """Initializes a new player instance.

        Args:
            index: Index of the player
        """

        if _is_hooked is False:
            self.bump_weapon.add_hook(HookType.PRE, weapon_bump)
            self.take_damage.add_hook(HookType.PRE, take_damage)

            global _is_hooked
            _is_hooked = True

        if self.userid not in _player_data:
            _player_data[self.userid] = {
                'gold': 0,
                'hero': None,
                'heroes': [],
                'weapons': set()
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

    @property
    def restrictions(self):
        return _player_data[self.userid]['weapons']
