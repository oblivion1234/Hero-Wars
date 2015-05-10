# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.player import Player

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

from filters.players import PlayerIter


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
    for cid in cfg.starting_heroes:
        if not find_element(heroes, 'cid', cid):
            raise ValueError('Invalid starting hero: {0}'.format(cid))

    # Setup database
    hw.database.setup()

    # Restart the game
    engine_server.server_command('mp_restartgame 1\n')

    # Send a message to everyone
    other_messages['Plugin Loaded'].send()


def unload():
    """Save all unsaved data into database."""

    # Save each player's data into the database
    for index in PlayerIter():
        player = Player(index)
        hw.database.save_player_data(player)

    # COmmit and close
    hw.database.database.commit()
    hw.database.database.close()

    # Send a message to everyone
    other_messages['Plugin Unloaded'].send()


def give_gold(player, gold_key):
    """Gives player gold and sends him a message about it.

    Args:
        player: Player who to give gold to
        gold_key: Key used for finding the gold value and translation
    """

    if not cfg.show_gold_messages:
        return
    gold = cfg.gold_values.get(gold_key, 0)
    if gold > 0:
        player.gold += gold
        gold_messages[gold_key].send(player.index, gold=gold)


def give_exp(player, exp_key):
    """Gives player exp and sends him a message about it.

    Args:
        player: Player who to give exp to
        exp_key: Key used for finding the exp value and translation
    """

    exp = cfg.exp_values.get(exp_key, 0)
    if exp > 0:
        player.hero.exp += exp
        exp_messages[exp_key].send(player.index, exp=exp)


def give_team_exp(player, exp_key):
    """Gives exp for player's teammates.

    Args:
        player: Player whose teammates to give exp to
        exp_key: Key used for finding the exp value and translation
    """

    # Give all his teammates exp
    team = player.team == 2 and 't' or 'ct'
    for index in PlayerIter(is_filters=team):
        if index != player.index:
            teammate = Player(index)
            give_exp(teammate, exp_key)


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
    """Saves player's data upon disconnect."""

    userid = game_event.get_int('userid')
    player = Player(index_from_userid(userid))
    hw.database.save_player_data(player)


@Event
def player_spawn(game_event):
    """Saves player's data.

    Also executes spawn skills and shows current exp/level progress.
    """

    # Get the player
    userid = game_event.get_int('userid')
    player = Player(index_from_userid(userid))

    # Save player's data
    hw.database.save_player_data(player)

    # Get player's hero
    hero = player.hero

    # Show current exp and level
    other_messages['Hero Status'].send(
        player.index,
        name=hero.name,
        level=hero.level,
        current=hero.exp,
        required=hero.required_exp
    )

    # Execute spawn skills if the player's on a valid team
    if player.team > 1:
        hero.execute_skills('player_spawn', player=player)


@Event
def player_death(game_event):
    """Executes kill, assist and death skills.

    Also gives exp from kill and assist.
    """

    # Get the defender
    defender = Player(index_from_userid(game_event.get_int('userid')))

    # Create the event arguments dict
    eargs = {
        'defender': defender,
        'headshot': game_event.get_bool('headshot'),
        'weapon': game_event.get_string('weapon')
    }

    # Get the attacker
    attacker_id = game_event.get_int('attacker')
    if attacker_id:
        attacker = Player(index_from_userid(attacker_id))
        eargs['attacker'] = attacker

    # If it was a suicide
    if not attacker_id or defender.userid == attacker.userid:

        # Execute suicide skills
        defender.hero.execute_skills(
            'player_suicide', **eargs)

    # If it wasn't...
    else:

        # Execute kill and death skills
        attacker.hero.execute_skills('player_kill', **eargs)
        defender.hero.execute_skills('player_death', **eargs)

        # Give attacker exp from kill and headshot
        give_exp(attacker, 'Kill')
        if eargs['headshot']:
            give_exp(attacker, 'Headshot')

        # Give attacker gold from kill
        give_gold(attacker, 'Kill')

    # Finally, remove defender's items
    for item in defender.hero.items:
        if not item.permanent:
            defender.hero.items.remove(item)


@Event
def player_hurt(game_event):
    """Executes attack and defend skills."""

    # Get the defender
    defender = Player(index_from_userid(game_event.get_int('userid')))

    # Create event arguments dict
    eargs = {
        'defender': defender,
        'damage': game_event.get_int('dmg_health'),
        'damage_armor': game_event.get_int('dmg_armor'),
        'weapon': game_event.get_string('weapon')
    }

    # Get the attacker and execute his skills
    attacker_id = game_event.get_int('attacker')
    if attacker_id:
        attacker = Player(index_from_userid(attacker_id))
        eargs['attacker'] = attacker
        attacker.hero.execute_skills('player_attack', **eargs)

    # Execute defend skills
    defender.hero.execute_skills('player_defend', **eargs)


@Event
def player_jump(game_event):
    """Executes jump skills."""

    player = Player(index_from_userid(game_event.get_int('userid')))
    player.hero.execute_skills('player_jump', player=player)


@Event
def player_say(game_event):
    """Executes ultimate skills and opens the menu."""

    # Get the player and the text
    player = Player(index_from_userid(game_event.get_int('userid')))
    text = game_event.get_string('text')

    # If text doesn't begin with the prefix, it's useless for us
    if text[:len(cfg.chat_command_prefix)] != cfg.chat_command_prefix:
        return

    # Get the ACTUAL text without the prefix
    text2 = text[len(cfg.chat_command_prefix):]

    # If the text was '!ultimate', execute ultimate skills
    if text2 == 'ultimate':
        Player_Ultimate(
            index=player.index,
            userid=player.userid
        ).fire()

    # If the text was '!hw' or '!hw', open Main menu
    elif text2 in ('hw', 'hw'):
        menus['Main'].send(player.index)

    elif text2 == 'admin':
        menus['Admin'].send(player.index)

    # Finally, execute hero's player_say skills
    player.hero.execute_skills('player_say', player=player, text=text)


@Event
def round_end(game_event):
    """Give exp from round win and loss.

    Also executes round_end skills.
    """

    # Get the winning team
    winner = game_event.get_int('winner')

    # Loop through all the players
    for index in PlayerIter():

        # Get player
        player = Player(index)

        # Give player win exp and gold
        if player.team == winner:
            give_exp(player, 'Round Win')
            give_gold(player, 'Round Win')

        # Or loss exp and gold
        else:
            give_exp(player, 'Round Loss')
            give_gold(player, 'Round Loss')

        # Execute hero's round_end skills
        player.hero.execute_skills('round_end', player=player, winner=winner)


@Event
def round_start(game_event):
    """Executes round_start skills."""

    for index in PlayerIter():
        player = Player(index)
        player.hero.execute_skills(
            'round_start', player=player, winner=game_event.get_int('winner'))


@Event
def bomb_planted(game_event):
    """Give exp from bomb planting.

    Also executes bomb_planted skills.
    """

    player = Player(index_from_userid(game_event.get_int('userid')))
    give_exp(player, 'Bomb Plant')
    give_team_exp(player, 'Bomb Plant Team')
    player.hero.execute_skills('bomb_planted', player=player)


@Event
def bomb_exploded(game_event):
    """Give exp from bomb explosion.

    Also executes bomb_exploded skills.
    """

    player = Player(index_from_userid(game_event.get_int('userid')))
    give_exp(player, 'Bomb Explode')
    give_team_exp(player, 'Bomb Explode Team')
    player.hero.execute_skills('bomb_exploded', player=player)


@Event
def bomb_defused(game_event):
    """Give exp from bomb defusion.

    Also executes bomb_defused skills.
    """

    player = Player(index_from_userid(game_event.get_int('userid')))
    give_exp(player, 'Bomb Defuse')
    give_team_exp(player, 'Bomb Defuse Team')
    player.hero.execute_skills('bomb_defused', player=player)


@Event
def hostage_follows(game_event):
    """Give exp from hostage pick up.

    Also executes hostage_follows skills.
    """

    player = Player(index_from_userid(game_event.get_int('userid')))
    give_exp(player, 'Hostage Pick Up')
    give_team_exp(player, 'Hostage Pick Up Team')
    player.hero.execute_skills('hostage_follows', player=player)


@Event
def hostage_rescued(game_event):
    """Give exp from hostage rescue.

    Also executes hostage_rescued skills.
    """

    player = Player(index_from_userid(game_event.get_int('userid')))
    give_exp(player, 'Hostage Rescue')
    give_team_exp(player, 'Hostage Rescue Team')
    player.hero.execute_skills('hostage_rescued', player=player)


@Event
def hero_pre_level_up(game_event):
    """Fetches the player and raises the Hero_Level_Up event."""

    # Raise hero_level_up event
    hero_id = game_event.get_int('id')
    owner = None
    for index in PlayerIter():
        player = Player(index)
        if id(player.hero) == hero_id:
            owner = player
            break
    if owner:
        Hero_Level_Up(
            cid=game_event.get_string('cid'),
            id=hero_id,
            player_index=player.index,
            player_userid=player.userid
        ).fire()


@Event
def hero_level_up(game_event):
    """Sends hero's status to player and opens current hero menu.

    Also executes hero_level_up skills.
    """

    # Get the player and his hero
    index = game_event.get_int('player_index')
    player = Player(index)
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

    # Execute player's skills
    player.hero.execute_skills('hero_level_up', player=player, hero=hero)


@Event
def player_ultimate(game_event):
    """Executes ultimate skills."""

    player = Player(index_from_userid(game_event.get_int('userid')))
    player.hero.execute_skills('player_ultimate', player=player)
