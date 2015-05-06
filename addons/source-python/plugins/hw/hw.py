# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.users import User
from hw.users import users

import hw.database

from hw.entities import Hero

from hw.events import Hero_Level_Up
from hw.events import Player_Ultimate

from hw.tools import get_messages
from hw.tools import find_element

from hw.menus import menus

from hw.heroes import *
from hw.items import *

import hw.configs as cfg

# Source.Python
from events import Event

from players.helpers import userid_from_playerinfo
from players.helpers import index_from_playerinfo
from players.helpers import index_from_userid

from engines.server import engine_server

from cvars.public import PublicConVar

from plugins.info import PluginInfo

from translations.strings import LangStrings

from commands.client import ClientCommand


# ======================================================================
# >> GLOBALS
# ======================================================================

# Plugin info
info = PluginInfo()
info.name = 'Hero-Wars'
info.author = 'Mahi'
info.version = '0.6.0'
info.basename = 'hw'
info.variable = "{0}_version".format(info.basename)

# Public variable for plugin info
info.convar = PublicConVar(
    info.variable,
    info.version,
    0,
    "{0} Version".format(info.name)
)

# Translation messages
exp_messages = get_messages(LangStrings('hw/exp'))
gold_messages = get_messages(LangStrings('hw/gold'))
other_messages = get_messages(LangStrings('hw/other'))


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def load():
    """Setups the database upon Hero-Wars loading.

    Makes sure there are heroes on the server, restarts the game
    and setups the database file.

    Raises:
        NotImplementedError: When there are no heroes
    """

    heroes = Hero.get_subclasses()
    if not heroes:
        raise NotImplementedError('No heroes on the server.')
    if not cfg.starting_heroes:
        raise NotImplementedError('No starting heroes set.')
    for cls_id in cfg.starting_heroes:
        if not find_element(heroes, 'cls_id', cls_id):
            raise ValueError('Invalid starting hero: {0}'.format(cls_id))

    # Setup database
    hw.database.setup()

    # Restart the game
    engine_server.server_command('mp_restartgame 1\n')

    # Send a message to everyone
    other_messages['Plugin Loaded'].send()


def unload():
    """Save all unsaved data into database."""

    # Save each user's data into the database
    for user in users.values():
        hw.database.save_user_data(user)

    # Send a message to everyone
    other_messages['Plugin Unloaded'].send()


def give_gold(user, gold_key):
    """Gives user gold and sends him a message about it.

    Args:
        user: User who to give gold to
        gold_key: Key used for finding the gold value and translation
    """

    if not cfg.show_gold_messages:
        return
    gold = cfg.gold_values.get(gold_key, 0)
    if gold > 0:
        user.gold += gold
        gold_messages[gold_key].send(index_from_userid(user.userid), gold=gold)


def give_exp(user, exp_key):
    """Gives user exp and sends him a message about it.

    Args:
        user: User who to give exp to
        exp_key: Key used for finding the exp value and translation
    """

    exp = cfg.exp_values.get(exp_key, 0)
    if exp > 0:
        user.hero.exp += exp
        exp_messages[exp_key].send(index_from_userid(user.userid), exp=exp)


def give_team_exp(user, exp_key):
    """Gives exp for user's teammates.

    Args:
        user: User whose teammates to give exp to
        exp_key: Key used for finding the exp value and translation
    """

    # Give all his teammates exp
    team = user.get_entity().team == 2 and 't' or 'ct'
    for userid in users:
        if userid != user.userid:
            player = users[userid].get_entity()
            if player.team == team:
                give_exp(users[userid], exp_key)


# ======================================================================
# >> CLIENT COMMANDS
# ======================================================================

@ClientCommand('hw_ultimate')
def client_command_ultimate(playerinfo, command):
    """Raises ultimate event with player's information."""

    Player_Ultimate(
        index=index_from_playerinfo(playerinfo),
        userid=userid_from_playerinfo(playerinfo)
    ).fire()


@ClientCommand('hw_menu')
def client_command_menu(playerinfo, command):
    """Opens a menu."""

    index = index_from_playerinfo(playerinfo)
    if command == 'hw_menu':
        menus['main'].send(index)
    else:
        _, menu = command.split(maxsplit=1)
        if menu in menus:
            menus[menu].send(index)


# ======================================================================
# >> GAME EVENTS
# ======================================================================

@Event
def player_disconnect(game_event):
    """Saves user's data upon disconnect."""

    userid = game_event.get_int('userid')
    user = users.get(userid)
    if user:
        hw.database.save_user_data(user)
        del users[userid]


@Event
def player_spawn(game_event):
    """Saves user's data.

    Also executes spawn skills and shows current exp/level progress.
    """

    # Get the user
    userid = game_event.get_int('userid')
    user = users.get(userid)

    # Create a new user if one doesn't exist already, and load his data
    if not user:
        user = User(userid)
        users[userid] = user
        hw.database.load_user_data(user)

    # Save user's data
    hw.database.save_user_data(user)

    # Get user's hero and entity
    hero = user.hero
    entity = user.get_entity()

    # Show current exp and level
    other_messages['Hero Status'].send(
        entity.index,
        name=hero.name,
        level=hero.level,
        current=hero.exp,
        required=hero.required_exp
    )

    # Execute spawn skills if the user's on a valid team
    if entity.team > 1:
        hero.execute_skills('player_spawn', user=user)


@Event
def player_death(game_event):
    """Executes kill, assist and death skills.

    Also gives exp from kill and assist.
    """

    # Get the users
    defender = users[game_event.get_int('userid')]
    attacker = users.get(game_event.get_int('attacker'))
    assister = users.get(game_event.get_int('assister'))

    # Create the event arguments dict
    eargs = {
        'attacker': attacker,
        'defender': defender,
        'assister': assister,
        'headshot': game_event.get_bool('headshot'),
        'weapon': game_event.get_string('weapon')
    }

    # If it was a suicide
    if (not attacker or
            defender.get_entity().index == attacker.get_entity().index):

        # Execute suicide skills
        defender.hero.execute_skills(
            'player_suicide', user=defender, **eargs)

    # If it wasn't...
    else:

        # Execute kill and death skills
        attacker.hero.execute_skills('player_kill', user=attacker, **eargs)
        defender.hero.execute_skills('player_death', user=defender, **eargs)

        # Give attacker exp from kill and headshot
        give_exp(attacker, 'Kill')
        if eargs['headshot']:
            give_exp(attacker, 'Headshot')

        # Give attacker gold from kill
        give_gold(attacker, 'Kill')

    # If the assister exists
    if assister:

        # Execute assist skills
        assister.hero.execute_skills('player_assist', user=assister, **eargs)

        # Give assister exp and gold
        give_exp(assister, 'Assist')
        give_gold(assister, 'Assist')

    # Finally, remove defender's items
    for item in defender.hero.items:
        if not item.permanent:
            defender.hero.items.remove(item)


@Event
def player_hurt(game_event):
    """Executes attack and defend skills."""

    # Get attacker and defender
    defender = users[game_event.get_int('userid')]
    attacker = users.get(game_event.get_int('attacker'))

    # Create event arguments dict
    eargs = {
        'attacker': attacker,
        'defender': defender,
        'damage': game_event.get_int('dmg_health'),
        'damage_armor': game_event.get_int('dmg_armor'),
        'weapon': game_event.get_string('weapon')
    }

    # Execute attack and defend skills
    if attacker:
        attacker.hero.execute_skills('player_attack', user=attacker, **eargs)
    defender.hero.execute_skills('player_defend', user=defender, **eargs)


@Event
def player_jump(game_event):
    """Executes jump skills."""

    user = users[game_event.get_int('userid')]
    user.hero.execute_skills('player_jump', user=user)


@Event
def player_say(game_event):
    """Executes ultimate skills and opens the menu."""

    # Get the user, index and the text
    user = users[game_event.get_int('userid')]
    index = index_from_userid(userid)
    text = game_event.get_string('text')

    # If text doesn't begin with the prefix, it's useless for us
    if text[:len(cfg.chat_command_prefix)] != cfg.chat_command_prefix:
        return

    # Get the ACTUAL text without the prefix
    text2 = text[len(cfg.chat_command_prefix):]

    # If the text was '!ultimate', execute ultimate skills
    if text2 == 'ultimate':
        Player_Ultimate(
            index=index,
            userid=user.userid
        ).fire()

    # If the text was '!hw' or '!hw', open Main menu
    elif text2 in ('hw', 'hw'):
        menus['Main'].send(index)

    elif text2 == 'admin':
        menus['Admin'].send(index)

    # Finally, execute hero's player_say skills
    user.hero.execute_skills('player_say', user=user, text=text)


@Event
def round_end(game_event):
    """Give exp from round win and loss.

    Also executes round_end skills.
    """

    # Get the winning team
    winner = game_event.get_int('winner')

    # Loop through all the users
    for userid, user in users.items():

        # Give user win exp and gold
        if user.get_entity().team == winner:
            give_exp(user, 'Round Win')
            give_gold(user, 'Round Win')

        # Or loss exp and gold
        else:
            give_exp(user, 'Round Loss')
            give_gold(user, 'Round Loss')

        # Execute hero's round_end skills
        user.hero.execute_skills('round_end', user=user, winner=winner)


@Event
def round_start(game_event):
    """Executes round_start skills."""

    for userid, user in users.items():
        user.hero.execute_skills(
            'round_start', user=user, winner=game_event.get_int('winner'))


@Event
def bomb_planted(game_event):
    """Give exp from bomb planting.

    Also executes bomb_planted skills.
    """

    user = users.get(game_event.get_int('userid'))
    if user:
        give_exp(user, 'Bomb Plant')
        give_team_exp(user, 'Bomb Plant Team')
        user.hero.execute_skills('bomb_planted', user=user)


@Event
def bomb_exploded(game_event):
    """Give exp from bomb explosion.

    Also executes bomb_exploded skills.
    """

    user = users.get(game_event.get_int('userid'))
    if user:
        give_exp(user, 'Bomb Explode')
        give_team_exp(user, 'Bomb Explode Team')
        user.hero.execute_skills('bomb_exploded', user=user)


@Event
def bomb_defused(game_event):
    """Give exp from bomb defusion.

    Also executes bomb_defused skills.
    """

    user = users.get(game_event.get_int('userid'))
    if user:
        give_exp(user, 'Bomb Defuse')
        give_team_exp(user, 'Bomb Defuse Team')
        user.hero.execute_skills('bomb_defused', user=user)


@Event
def hostage_follows(game_event):
    """Give exp from hostage pick up.

    Also executes hostage_follows skills.
    """

    user = users.get(game_event.get_int('userid'))
    if user:
        give_exp(user, 'Hostage Pick Up')
        give_team_exp(user, 'Hostage Pick Up Team')
        user.hero.execute_skills('hostage_follows', user=user)


@Event
def hostage_rescued(game_event):
    """Give exp from hostage rescue.

    Also executes hostage_rescued skills.
    """

    user = users.get(game_event.get_int('userid'))
    if user:
        give_exp(user, 'Hostage Rescue')
        give_team_exp(user, 'Hostage Rescue Team')
        user.hero.execute_skills('hostage_rescued', user=user)


@Event
def hero_pre_level_up(game_event):
    """Fetches the player and raises the Hero_Level_Up event."""

    # Raise hero_level_up event
    hero_id = game_event.get_int('id')
    owner = None
    for user in users.values():
        if id(user.hero) == hero_id:
            owner = user
            break
    if owner:
        Hero_Level_Up(
            cls_id=game_event.get_string('cls_id'),
            id=hero_id,
            player_index=owner.get_entity().index,
            player_userid=owner.userid
        ).fire()


@Event
def hero_level_up(game_event):
    """Sends hero's status to player and opens current hero menu.

    Also executes hero_level_up skills.
    """

    # Get the user's index and his hero
    index = index_from_userid(game_event.get_int('userid'))
    hero = player.hero

    # Send hero's status via chat
    other_messages['Hero Status'].send(
        index,
        name=hero.name,
        level=hero.level,
        current=hero.exp,
        required=hero.required_exp
    )

    # Open current hero info menu (Kamiqawa, what?) to let the player
    # spend skill points
    menus['Current Hero'].send(index)

    # Execute user's skills
    user = users.get(game_event.get_int('userid'))
    user.hero.execute_skills('hero_level_up', user=user, hero=hero)


@Event
def player_ultimate(game_event):
    """Executes ultimate skills."""

    user = users.get(game_event.get_int('userid'))
    if user:
        user.hero.execute_skills('player_ultimate', user=user)
