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

from herowars.heroes import *

# Source.Python 
from events import Event

from filters.players import PlayerIter


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def load():
    """Setups the database upon Hero Wars loading.

    Also makes sure there are heroes on the server.
    
    Raises:
        NotImplementedError: When there are no heroes
    """

    if not Hero.get_subclasses():
        raise NotImplementedError('No heroes on the server.')
    setup_database(database_path)


def _give_objective_exp(userid, team, exp_key):
    """Gives experience points from an objective.

    Gives the performing player exp based on the exp_key and all of 
    his teammates exp based on exp_key + '_team'.

    Args:
        userid: Userid of the player completing the objective
        team: Team who to give exp to ('t' or 'ct')
        exp_key: Key for the exp giving from herowars.configs.exp_values
    """

    # Get the player
    player = get_player(userid)

    # Give exp from the objective
    if player:
        player.hero.exp += exp_values[exp_key]

    # Give player's teammates exp
    for userid in PlayerIter(is_filters=team, return_types='userid'):
        teammate = get_player(userid)
        if teammate and teammate != player:
            teammate.hero.exp += exp_values[exp_key + '_team']


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

    # If defender exists (should always happen though)
    if defender:

        # If attacker exists
        if attacker:

            # Execute kill and death skills
            attacker.hero.execute_skills('on_kill', game_event)
            defender.hero.execute_skills('on_death', game_event)

            # Give attacker exp from kill
            attacker.hero.exp += exp_values['kill']

            # Give attacker exp from headshot
            if game_event.get_bool('headshot'):
                attacker.hero.exp += exp_values['headshot']

            # Give attacker exp from weapon
            weapon = game_event.get_string('weapon')
            if exp_values['weapons'][weapon]:
                attacker.hero.exp += exp_values['weapons'][weapon]

        # If there was no attacker, execute suicide skills
        else:
            defender.hero.execute_skills('on_suicide', game_event)

        # If there was an assister
        if assister:

            # Execute assist skills
            assister.hero.execute_skills('on_assist', game_event)

            # Give assister exp
            assister.hero.exp += exp_values['assist']


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

    player = get_player(game_event.get_int('userid'))
    if player:
        text = game_event.get_string('text')
        if text == '!ultimate':
            player.hero.execute_skills('on_ultimate', game_event)


@Event
def round_end(game_event):
    """Gives exp from round wins and losses."""

    # Get the winner and loser
    winner, loser = (game_event.get_int('winner') == 2
                    and ('t', 'ct') or ('ct', 't'))

    # Give winners exp
    for userid in PlayerIter(is_filters=winner, return_types='userid'):
        player = get_player(userid)
        if player:
            player.hero.exp += exp_values['round_win']

    # Give losers exp
    for userid in PlayerIter(is_filters=loser, return_types='userid'):
        player = get_player(userid)
        if player:
            player.hero.exp += exp_values['round_loss']


@Event
def bomb_planted(game_event):
    """Gives exp from bomb plant."""

    _give_objective_exp(game_event.get_int('userid'), 't', 'bomb_plant')


@Event
def bomb_exploded(game_event):
    """Gives exp from bomb explode."""

    _give_objective_exp(game_event.get_int('userid'), 't', 'bomb_explode')


@Event
def bomb_defused(game_event):
    """Gives exp from bomb defuse."""
    
    _give_objective_exp(game_event.get_int('userid'), 'ct', 'bomb_defuse')


@Event
def hostage_follows(game_event):
    """Gives exp from hostage pick up."""

    _give_objective_exp(game_event.get_int('userid'), 'ct', 'hostage_pickup')


@Event
def hostage_rescued(game_event):
    """Gives exp from hostage pick up."""

    _give_objective_exp(game_event.get_int('userid'), 'ct', 'hostage_rescue')
