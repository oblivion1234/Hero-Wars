# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.player import get_player
from herowars.player import create_player
from herowars.player import remove_player
from herowars.player import players

from herowars.database import setup_database
from herowars.database import save_player_data

from herowars.entities import Hero

from herowars.tools import find_element

from herowars.menus import main_menu

from herowars.translation import get_messages

from herowars.heroes import *
from herowars.items import *

import herowars.configs as cfg

# Source.Python 
from events import Event

from filters.players import PlayerIter

from engines.server import engine_server

from cvars.public import PublicConVar

from plugins.info import PluginInfo

from messages import SayText2


# ======================================================================
# >> PLUGIN INFO
# ======================================================================

info = PluginInfo()
info.name = 'Hero Wars'
info.author = 'Mahi, Kamiqawa'
info.version = '0.4.5'
info.basename = 'herowars'
info.variable = "{0}_version".format(info.basename)

# Public variable
info.convar = PublicConVar(
    info.variable, 
    info.version, 
    0, 
    "{0} Version".format(info.name)
)


# ======================================================================
# >> TRANSLATIONS
# ======================================================================

exp_messages = get_messages('exp_messages')
gold_messages = get_messages('gold_messages')
other_messages = get_messages('other_messages')


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def load():
    """Setups the database upon Hero Wars loading.

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
    setup_database(cfg.database_path)

    # Restart the game
    engine_server.server_command('mp_restartgame 1\n')

    # Send a message to everyone
    other_messages['Plugin Loaded'].send()


def unload():
    """Save all unsaved data into database."""

    # Save each player's data into the database
    for player in players:
        save_player_data(cfg.database_path, player)

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
    for userid in PlayerIter(is_filters=team, return_types='userid'):
        if userid != player.userid:
            teammate = get_player(userid)
            give_exp(teammate, exp_key)


# ======================================================================
# >> GAME EVENTS
# ======================================================================

@Event
def player_disconnect(game_event):
    """Removes a player and saves his data upon disconnection."""

    userid = game_event.get_int('userid')
    remove_player(userid)


@Event
def player_spawn(game_event):
    """Creates new players and saves existing players' data.

    Also executes spawn skills and shows current exp/level progress.
    """

    # Get the player
    userid = game_event.get_int('userid')
    player = get_player(userid)

    # If the player was found
    if player:

        # Save his data
        save_player_data(cfg.database_path, player)

    # If the player wasn't found
    else:

        # Create a new player
        player = create_player(userid)

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
        hero.execute_skills('on_spawn', player=player)


@Event
def player_death(game_event):
    """Executes kill, assist and death skills.

    Also gives exp from kill and assist."""

    # Get the attacker, defender and assister
    defender = get_player(game_event.get_int('userid'))
    attacker = get_player(game_event.get_int('attacker'))
    assister = get_player(game_event.get_int('assister'))

    # Create the event arguments dict
    eargs = {
        'attacker': attacker,
        'defender': defender,
        'assister': assister,
        'headshot': game_event.get_bool('headshot'),
        'weapon': game_event.get_string('weapon')
    }

    # If it was a suicide
    if defender == attacker:

        # Execute suicide skills
        defender.hero.execute_skills(
            'on_suicide', player=defender, **eargs)

    # If it wasn't...
    else:

        # Execute kill and death skills
        attacker.hero.execute_skills('on_kill', player=attacker, **eargs)
        defender.hero.execute_skills('on_death', player=defender, **eargs)

        # Give attacker exp from kill and headshot
        give_exp(attacker, 'Kill')
        if eargs['headshot']:
            give_exp(attacker, 'Headshot')

        # Give attacker gold from kill
        give_gold(attacker, 'Kill')

    # If the assister exists
    if assister:

        # Execute assist skills
        assister.hero.execute_skills('on_assist', player=assister, **eargs)

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

    # Get defender and attacker
    defender = get_player(game_event.get_int('userid'))
    attacker = get_player(game_event.get_int('attacker'))

    # Create event arguments dict
    eargs = {
        'attacker': attacker,
        'defender': defender,
        'damage': game_event.get_int('dmg_health'),
        'damage_armor': game_event.get_int('dmg_armor'),
        'weapon': game_event.get_string('weapon')
    }

    # Execute attack and defend skills
    attacker.hero.execute_skills('on_attack', player=attacker, **eargs)
    defender.hero.execute_skills('on_defend', player=defender, **eargs)


@Event
def player_jump(game_event):
    """Executes jump skills."""

    player = get_player(game_event.get_int('userid'))
    player.hero.execute_skills('on_jump', player=player)


@Event
def player_say(game_event):
    """Executes ultimate skills and opens the menu."""

    # Get the player and the text
    player = get_player(game_event.get_int('userid'))
    text = game_event.get_string('text')

    # If text doesn't begin with the prefix, it's useless for us
    if text[:len(cfg.chat_command_prefix)] != cfg.chat_command_prefix:
        return

    # Get the ACTUAL text without the prefix
    text2 = text[len(cfg.chat_command_prefix):]

    # If the text was '!ultimate', execute ultimate skills
    if text2 == 'ultimate':
        player.hero.execute_skills('on_ultimate', player=player)

    # If the text was '!hw' or '!herowars', open main menu
    elif text2 in ('hw', 'herowars'):
        main_menu(player).send(player.index)

    # Finally, execute hero's on_say skills
    player.hero.execute_skills('on_say', player=player, text=text)
        

@Event
def round_end(game_event):
    """Give exp from round win and loss."""

    # Get the winning team
    winner = game_event.get_int('winner')

    # Loop through all the players' userids
    for userid in PlayerIter(is_filters=('ct', 't'), return_types='userid'):

        # Get the player
        player = get_player(userid)

        # Give player win exp and gold
        if player.get_team() == winner:
            give_exp(player, 'Round Win')
            give_gold(player, 'Round Win')

        # Or loss exp and gold
        else:
            give_exp(player, 'Round Loss')
            give_gold(player, 'Round Loss')


@Event
def bomb_planted(game_event):
    """Give exp from bomb planting."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'Bomb Plant')
    give_team_exp(player, 'Bomb Plant Team')


@Event
def bomb_exploded(game_event):
    """Give exp from bomb explosion."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'Bomb Explode')
    give_team_exp(player, 'Bomb Explode Team')


@Event
def bomb_defused(game_event):
    """Give exp from bomb defusion."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'Bomb Defuse')
    give_team_exp(player, 'Bomb Defuse Team')


@Event
def hostage_follows(game_event):
    """Give exp from hostage pick up."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'Hostage Pick Up')
    give_team_exp(player, 'Hostage Pick Up Team')


@Event
def hostage_rescued(game_event):
    """Give exp from hostage rescue."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'Hostage Rescue')
    give_team_exp(player, 'Hostage Rescue Team')
