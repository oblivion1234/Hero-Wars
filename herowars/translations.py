# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.configs import default_lang_key
from herowars.configs import chat_message_prefix
from herowars.configs import chat_message_colors as colors

# Source Python
from basetypes import Color

# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'get_translation',
    'default_lang_key'
)


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def get_translation(lang_key, sub_dict, key):
    """Gets a translation for a string.

    Finds the proper translated string from translations dict
    using the provided language, sub dict and a key.

    Args:
        lang_key: Language key used for the translation
        sub_dict: Key of the sub dict
        key: Key of the actual string

    Raises:
        KeyError: If sub_dict is not found

    Returns:
        Translated string (if found)
    """

    # Get the language dictionary
    if lang_key in _translations:
        lang_dict = _translations[lang_key]
    elif default_lang_key in _translations:
        lang_dict = _translations[default_lang_key]
    else:
        raise KeyError('Unable to get language dict ({lang_key}, {default}.'
            .format(lang_key=lang_key, default=default_lang_key))

    # Make sure the sub dict exists
    if sub_dict in lang_dict:

        # Return the proper translation
        return lang_dict[sub_dict].get(key, '#null_str')

    # Else raise an error of the sub dict
    raise KeyError('Invalid sub dict key: {key}'.format(key=sub_dict))


def get_prefixed_translation(*args, **kwargs):
    """Gets a translation for a string and adds prefix

    Finds the translated string and modifies it to 
    Hero Wars standard format with prefix and default colors.

    Args:
        lang_key: Language key used for the translation
        sub_dict: Key of the sub dict
        key: Key of the actual string

    Raises:
        KeyError: If sub_dict is not found

    Returns:
        Translated string (if found)
    """

    return '{prefix_color}{prefix} {text_color}{text}'.format(
        prefix_color=colors['prefix'],
        prefix=chat_message_prefix,
        text_color=colors['text'],
        text=get_translation(*args, **kwargs)
    )


# ======================================================================
# >> TRANSLATIONS
# ======================================================================

_translations = {

    # English
    'en': {

        # Exp values
        'exp': dict(

            # Kill values
            kill = "{0}+{{exp}}{1} exp for a kill.".format(colors['highlight'], colors['text']),
            headshot = "{0}+{{exp}}{1} exp for a headshot.".format(colors['highlight'], colors['text']),
            assist = "{0}+{{exp}}{1} exp for an assist.".format(colors['highlight'], colors['text']),

            # Weapon values
            weapon_knife = "{0}+{{exp}}{1} exp for a knife kill.".format(colors['highlight'], colors['text']),

            # Round values
            round_win = "{0}+{{exp}}{1} exp for winning a round.".format(colors['highlight'], colors['text']),
            round_lose = "{0}+{{exp}}{1} exp for losing a round.".format(colors['highlight'], colors['text']),

            # Bomb values
            bomb_plant = "{0}+{{exp}}{1} exp for planting the bomb.".format(colors['highlight'], colors['text']),
            bomb_plant_team = "{0}+{{exp}}{1} exp for bomb being planted.".format(colors['highlight'], colors['text']),
            bomb_explode = "{0}+{{exp}}{1} exp for bomb exploding.".format(colors['highlight'], colors['text']),
            bomb_explode_team = "{0}+{{exp}}{1} exp for bomb exploding.".format(colors['highlight'], colors['text']),
            bomb_defuse = "{0}+{{exp}}{1} exp for defusing the bomb.".format(colors['highlight'], colors['text']),
            bomb_defuse_team = "{0}+{{exp}}{1} exp for bomb being defused.".format(colors['highlight'], colors['text']),

            # Hostage values
            hostage_pickup = "{0}+{{exp}}{1} exp for picking up a hostage.".format(colors['highlight'], colors['text']),
            hostage_pickup_team = "{0}+{{exp}}{1} exp for a hostage being picked up.".format(colors['highlight'], colors['text']),
            hostage_rescue = "{0}+{{exp}}{1} exp for rescuing a hostage.".format(colors['highlight'], colors['text']),
            hostage_rescue_team = "{0}+{{exp}}{1} exp for a hostage being rescued".format(colors['highlight'], colors['text'])
        ),

        # Gold values
        'gold': dict(
            
            # Kill values
            kill = "{0}+{{gold}}{1} gold for a kill.".format(colors['highlight'], colors['text']),
            assist = "{0}+{{gold}}{1} gold for an assist.".format(colors['highlight'], colors['text']),

            # Round values
            round_win = "{0}+{{gold}}{1} gold for winning a round.".format(colors['highlight'], colors['text']),
            round_lose = "{0}+{{gold}}{1} gold for losing a round.".format(colors['highlight'], colors['text'])
        ),

        # Menu messages
        'menu_messages': dict(

            # Item values
            no_items_to_buy = "There are no items to buy.",
            no_owned_items = "You don't have any items.",
            not_enough_cash = "You don't have enough cash: {0}${{cash}}{1}/{0}${{cost}}{1}.".format(colors['highlight'], colors['text']),

            bought_item = "You bought item {0}{{name}}{1} for {0}${{cost}}{1}.".format(colors['highlight'], colors['text']),
            sold_item = "You sold item {0}{{name}}{1} for {0}${{cost}}{1}.".format(colors['highlight'], colors['text']),

            # Hero values
            no_heroes_to_buy = "There are no heroes to buy.",
            no_owned_heroes = "You don't have any heroes.",
            not_enough_gold = "You don't have enough gold {0}{{gold}}{1}/{0}{{cost}}{1}.".format(colors['highlight'], colors['text']),

            bought_hero = "You bought hero {0}{{name}}{1} for {0}{{cost}}{1} gold.".format(colors['highlight'], colors['text']),
            changed_hero = "You changed your hero to {0}{{name}}{1}.".format(colors['highlight'], colors['text']),

            # Skill values
            skill_leveled = "Skill {0}{{name}}{1} is now on level {0}{{level}}{1}.".format(colors['highlight'], colors['text']),
            skill_points_reset = "Skill points have been reset.",

            not_required_level = "Hero hasn't reached required level {0}{{current_level}}{1}/{0}{{required_level}}{1}.".format(colors['highlight'], colors['text']),
            not_enough_skill_points = "You don't have enough skill points {0}{{skill_points}}{1}/{0}{{cost}}{1}.".format(colors['highlight'], colors['text']),
            skill_maxed_out = "Skill has already been maxed out."
        ),

        # Menu options
        'menus' : dict(

            # Mainmenu
            buy_heroes = "Buy Heroes",
            owned_heroes = "Owned Heroes",
            current_hero = "Current Hero",

            # Headers
            buy_items = "Buy Items",
            item_categories = "Item Categories",
            sell_items = "Sell Items",

            # Info
            available_skill_points = "Skill Points: {{skill_points}}",

            # Options
            reset_skill_points = "Reset Skill Points",
            option_buy = "Buy",
            option_change = "Change"
        ),

        # Other translations
        'other': dict(

            # Plugin setup
            plugin_loaded = 'Hero Wars loaded.',
            plugin_unloaded = 'Hero Wars unloaded.',

            # Hero's status
            hero_status = "{0}{{name}}{1} - lvl {0}{{level}}{1} - {0}{{exp}}{1}/{0}{{max_exp}}{1} exp".format(colors['highlight'], colors['text']),

            # Level up
            level_up = "{0}{{name}}{1} - lvl {0}{{level}}{1} - {0}{{exp}}{1}/{0}{{max_exp}}{1} exp.".format(colors['highlight'], colors['text'])
        )
    }
}
