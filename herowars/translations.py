# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.configs import default_language


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'get_translation',
    'default_language'
)


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def get_translation(language, sub_dict, key):
    """Gets a translation for a string.

    Finds the proper translated string from translations dict
    using the provided language, sub dict and a key.

    Args:
        language: Language used for the translation
        sub_dict: Key of the sub dict
        key: Key of the actual string

    Raises:
        KeyError: If sub_dict is not found

    Returns:
        Translated string (if found)
    """

    # Get the language dictionary
    if language in _translations:
        lang_dict = _translations[language]
    else:
        lang_dict = _translations.get(default_language, {})

    # Make sure the sub dict exists
    if sub_dict in lang_dict:

        # Return the proper translation
        return '{tr}'.format(tr=lang_dict[sub_dict].get(key, '#null_str'))

    # Else raise an error of the sub dict
    raise KeyError('Invalid sub dict key: {key}'.format(key=sub_dict))


# ======================================================================
# >> TRANSLATIONS
# ======================================================================

_translations = {

    # English
    'en': {

        # Exp values
        'exp': dict(

            # Kill values
            kill = '+{exp} exp for a kill.',
            headshot = '+{exp} exp for a headshot.',
            assist = '+{exp} exp for an assist.',

            # Weapon values
            weapon_knife = '+{exp} exp for a knife kill.',

            # Round values
            round_win = '+{exp} exp for winning a round.',
            round_lose = '+{exp} exp for losing a round.',

            # Bomb values
            bomb_plant = '+{exp} exp for plating the bomb.',
            bomb_plant_team = '+{exp} exp for bomb being planted.',
            bomb_explode = '+{exp} exp for bomb exploding.',
            bomb_explode_team = '+{exp} exp for bomb exploding.',
            bomb_defuse = '+{exp} exp for defusing the bomb.',
            bomb_defuse_team = '+{exp} exp for bomb being defused.',

            # Hostage values
            hostage_pickup = '+{exp} exp for picking up a hostage.',
            hostage_pickup_team = '+{exp} exp for a hostage being picked up.',
            hostage_rescue = '+{exp} exp for rescuing a hostage.',
            hostage_rescue_team = '+{exp} exp for a hostage being rescued.'
        ),

        # Menu messages
        'menu_messages': dict(

            # Item values
            no_items_to_buy = 'There are no items to buy.',
            no_owned_items = "You don't have any items",
            not_enough_cash = "You don't have enough cash (${cash}/${cost}).",

            bought_item = 'You bought item {name} for ${cost}.',
            sold_item = 'You bought item {name} for ${cost}.',

            # Hero values
            no_heroes_to_buy = 'There are no heroes to buy.',
            no_owned_heroes = "You don't have any heroes.",
            not_enough_gold = "You don't have enough gold ({gold}/{cost}).",

            bought_hero = 'You bought hero {name} for {cost} gold.',
            changed_hero = 'You changed hero to {name}.',

            # Skill values
            skill_leveled = 'Skill {name} is now level {level}.',
            skill_points_reset = 'Skill points have been reset.'
            
        ),

        # Menu options
        'menu' : dict(

            # Mainmenu
            buy_heroes = 'Buy Heroes',
            owned_heroes = 'Owned Heroes',
            current_hero = 'Current Hero',

            # Headers
            buy_items = 'Buy Items',
            item_categories = 'Item Categories',
            sell_items = 'Sell Items',

            # Info
            available_skill_points = 'Skill Points: {skill_points}',

            # Options
            reset_skill_points = 'Reset Skill Points',
            option_buy = 'Buy',
            option_change = 'Change'
        )
    }
}