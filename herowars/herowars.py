# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.player import get_player
from herowars.player import create_player
from herowars.player import remove_player

from herowars.database import setup_database
from herowars.database import save_player_data

from herowars.entities import Hero

from herowars.configs import database_path
from herowars.configs import exp_values
from herowars.configs import chat_command_prefix

from herowars.translations import get_translation

from herowars.menus import main_menu

from herowars.heroes import *
from herowars.items import *

# Source.Python 
from events import Event

from filters.players import PlayerIter

from engines.server import engine_server


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

    if not Hero.get_subclasses():
        raise NotImplementedError('No heroes on the server.')
    setup_database(database_path)
    engine_server.server_command('mp_restartgame 3\n')


def give_exp(player, exp_key):
    """Gives player exp and sends him a message about it.

    Args:
        player: Player who to give exp to
        exp_key: Key used for finding the exp value and translation
    """

    if player and player.hero:
        exp = exp_values.get(exp_key, 0)
        if exp > 0:
            player.exp += exp
            translation = get_translation(player.lang_key, 'exp', exp_key)
            player.signal(translation.format(exp=exp))


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

    Also executes spawn skills.
    """

    # Get the player
    userid = game_event.get_int('userid')
    player = get_player(userid)

    # If the player was found
    if player:

        # Save his data
        save_player_data(database_path, player)

    # If the player wasn't found
    else:

        # Create a new player
        player = create_player(userid)

    # Execute spawn skills if the player's on a valid team
    if game_event.get_int('teamnum') > 1:
        player.hero.execute_skills('on_spawn', game_event)


@Event
def player_death(game_event):
    """Executes kill, assist and death skills.

    Also gives exp from kill and assist."""

    # Set 'defender' key and remove 'userid' key
    game_event.set_int('defender', game_event.get_int('userid'))
    game_event.set_int('userid', 0)

    # Get the players
    defender = get_player(game_event.get_int('defender'))
    attacker = get_player(game_event.get_int('attacker'))
    assister = get_player(game_event.get_int('assister'))

    # If defender exists
    if defender:

        # And if attacker exists
        if attacker:

            # Execute kill and death skills
            attacker.hero.execute_skills('on_kill', game_event)
            defender.hero.execute_skills('on_death', game_event)

            # Give attacker exp from kill, headshot and weapon
            give_exp(attacker, 'kill')
            if game_event.get_bool('headshot'):
                give_exp(attacker, 'headshot')
            give_exp(attacker, game_event.get_string('weapon'))

        # If there was no attacker, execute defender's suicide skills
        elif not game_event.get_int('attacker'):
            defender.hero.execute_skills('on_suicide', game_event)

        # Execute assister's skills and give him exp
        if assister:
            assister.hero.execute_skills('on_assist', game_event)
            give_exp(assister, 'assist')

        # Finally, remove items that are not "permanent"
        for item in defender.hero.items:
            if not item.permanent:
                defender.hero.items.remove(item)


@Event
def player_hurt(game_event):
    """Executes attack and defend skills."""

    # Set 'defender' key and remove 'userid' key
    game_event.set_int('defender', game_event.get_int('userid'))
    game_event.set_int('userid', 0)

    # Get the players
    defender = get_player(game_event.get_int('defender'))
    attacker = get_player(game_event.get_int('attacker'))

    # If both defender and attacker exist
    if defender and attacker:

        # Execute attack and defend skills
        attacker.hero.execute_skills('on_attack', game_event)
        defender.hero.execute_skills('on_defend', game_event)


@Event
def player_jump(game_event):
    """Executes jump skills."""

    player = get_player(game_event.get_int('userid'))
    if player:
        player.hero.execute_skills('on_jump', game_event)


@Event
def player_say(game_event):
    """Executes ultimate skills."""

    # Get the player and the text
    player = get_player(game_event.get_int('userid'))
    if player:
        text = game_event.get_string('text')

        # If text doesn't begin with the prefix, it's useless for us
        if text[:len(chat_command_prefix)] != chat_command_prefix:
            return

        # Get the ACTUAL text without the prefix
        text = text[len(chat_command_prefix):]

        # If the text was '!ultimate', execute ultimate skills
        if text == 'ultimate':
            player.hero.execute_skills('on_ultimate', game_event)

        # If the text was '!hw' or '!herowars', open main menu
        elif text in ('hw', 'herowars'):
            main_menu(player.index).send(player.index)
        

@Event
def round_end(game_event):
    """Give exp from round win and loss."""

    # Get the winning team
    winner = game_event.get_int('winner')

    # Loop through all the players' userids
    for userid in PlayerIter(is_filters=('ct', 't'), return_types='userid'):

        # Get the player
        player = get_player(userid)

        # Give player win exp
        if player.get_team() == winner:
            give_exp(player, 'round_win')

        # Or loss exp
        else:
            give_exp(player, 'round_loss')


@Event
def bomb_planted(game_event):
    """Give exp from bomb planting."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'bomb_plant')
    give_team_exp(player, 'bomb_plant_team')


@Event
def bomb_exploded(game_event):
    """Give exp from bomb explosion."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'bomb_explode')
    give_team_exp(player, 'bomb_explode_team')


@Event
def bomb_defused(game_event):
    """Give exp from bomb defusion."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'bomb_defuse')
    give_team_exp(player, 'bomb_defuse_team')


@Event
def hostage_follows(game_event):
    """Give exp from hostage pick up."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'hostage_pick_up')
    give_team_exp(player, 'hostage_pick_up_team')


@Event
def hostage_rescued(game_event):
    """Give exp from hostage rescue."""

    player = get_player(game_event.get_int('userid'))
    give_exp(player, 'hostage_rescue')
    give_team_exp(player, 'hostage_rescue_team')
