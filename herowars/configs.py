# ======================================================================
# >> CONFIGURATIONS
# ======================================================================


# Default language abbreviation
default_language = 'en'


# Chat command prefix, default is '!'
chat_command_prefix = '!'


# Dictionary for experience point values
exp_values = dict(

    # Kill values
    kill = 30,
    headshot = 15,
    assist = 15,
    weapon_knife = 30,

    # Round values
    round_win = 30,
    round_lose = 15,

    # Bomb values
    bomb_plant = 15,
    bomb_plant_team = 5,
    bomb_explode = 25,
    bomb_explode_team = 10,
    bomb_defuse = 30,
    bomb_defuse_team = 15,

    # Hostage values
    hostage_pick_up = 5,
    hostage_pick_up_team = 0,
    hostage_rescue = 25,
    hostage_rescue_team = 10,
)


# Database file used by Hero Wars
database_path = './herowars.db'


# Starting heroes given when a player joins for the first time
# Use class names for identifying the Hero classes
starting_heroes = (
    'UndeadMage',

)