# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.tools import apply_tokens
from hw.tools import find_element

from hw.entities import Hero

from hw.menulib import HwPagedMenu

from hw.players import get_player

# Source.Python
from menus import SimpleMenu
from menus import SimpleOption
from menus import PagedOption
from menus import Text

from menus.base import _translate_text

from translations.strings import LangStrings


# ======================================================================
# >> GLOBALS
# ======================================================================

_TR = {
    'menulib': LangStrings('hw/menulib'),
    'menus': LangStrings('hw/menus')
}

menus = {}


# ======================================================================
# >> CURRENT HERO MENU
# ======================================================================

def _current_hero_select_callback(menu, player_index, choice):
    """Current Hero menu's select_callback function."""

    player = get_player(player_index, key='index')
    if choice.value == 7:
        for skill in player.hero.skills:
            skill.level = 0
    else:
        skill = choice.value
        if (skill.cost <= player.hero.skill_points
                and skill.required_level <= player.hero.level
                and skill.level < skill.max_level):
            skill.level += 1
    return menu


def _current_hero_build_callback(menu, player_index):
    """Current Hero menu's build_callback function."""

    # Get player and hero
    player = get_player(player_index, key='index')
    hero = player.hero

    # Set menu's base attributes
    menu.title = hero.name
    menu.description = apply_tokens(
        _TR['menus']['Description'],
        level=hero.level,
        skill_points=hero.skill_points
    )

    # Clear the menu
    menu.clear()

    # Loop through hero's passives
    for passive in hero.passives:

        # Get the additional info for passive
        info = ''
        if passive.level > 0:
            if passive.max_level > 0:
                info = ' ({0}/{1})'.format(passive.level, passive.max_level)
            else:
                info = ' ({0})'.format(passive.level)

        # Add the option to the menu
        menu.append(Text('P. {0}{1}'.format(passive.name, info)))

    # Loop through hero's skills
    for skill in hero.skills:

        # Set the default arguments for the PagedOption
        info = '{0}/{1}'.format(skill.level, skill.max_level)
        selectable = True

        # If skill is already maxed out
        if skill.level >= skill.max_level:
            info = ' ({0})'.format(_translate_text(
                _TR['menus']['Maxed'],
                player_index
            ))
            selectable = False

        # If the hero hasn't reached skill's required level
        elif skill.required_level > hero.level:
            info += ' ({0})'.format(_translate_text(
                apply_tokens(
                    _TR['menus']['Required'],
                    required=skill.required_level
                ),
                player_index
            ))
            selectable = False

        # If skill costs more than one, show the cost
        elif skill.cost > 1:
            info += ' ({0})'.format(_translate_text(
                apply_tokens(_TR['menus']['Cost'], cost=skill.cost),
                player_index
            ))

        # And if hero doesn't have enough skill points, disable skill
        if skill.cost > hero.skill_points:
            selectable = False

        # Add the PagedOption to the menu
        menu.append(PagedOption(
            '{0} {1}'.format(skill.name, info),
            skill,
            selectable=selectable,
            highlight=selectable
        ))


menus['Current Hero'] = HwPagedMenu(
    select_callback=_current_hero_select_callback,
    build_callback=_current_hero_build_callback,
    constants={7: PagedOption(_TR['menus']['Reset Skills'], 7)},
    display_page_info=False
)


# ======================================================================
# >> OWNED HEROES MENU
# ======================================================================

def _owned_heroes_select_callback(menu, player_index, choice):
    """Owned Heroes menu's select_callback function."""

    player = get_player(player_index, key='index')
    player.hero = choice.value


def _owned_heroes_build_callback(menu, player_index):
    """Owned Heroes menu's build_callback function."""

    player = get_player(player_index, key='index')
    menu.clear()
    for hero in player.heroes:
        option = PagedOption(
            '{0} {1}/{2}'.format(
                hero.name, hero.level, hero.max_level
            ),
            hero
        )
        if hero.cls_id == player.hero.cls_id:
            option.selectable = option.highlight = False
        menu.append(option)


menus['Owned Heroes'] = HwPagedMenu(
    title=_TR['menus']['Owned Heroes'],
    select_callback=_owned_heroes_select_callback,
    build_callback=_owned_heroes_build_callback
)


# ======================================================================
# >> BUY HEROES MENU
# ======================================================================

def _buy_heroes_select_callback(menu, player_index, choice):
    """Buy Heroes menu's select_callback function."""

    player = get_player(player_index, key='index')
    hero_cls = choice.value
    if player.gold > hero_cls.cost:
        hero = hero_cls()
        player.gold -= hero.cost
        player.heroes.append(hero)
        player.hero = hero


def _buy_heroes_build_callback(menu, player_index):
    """Buy Heroes menu's build_callback function."""

    player = get_player(player_index, key='index')
    menu.clear()
    for hero_cls in Hero.get_subclasses():
        if find_element(player.heroes, 'cls_id', hero_cls.cls_id):
            continue
        option = PagedOption(
            '{0} ({1})'.format(
                hero_cls.name,
                _translate_text(
                    apply_tokens(
                        _TR['menus']['Cost'], cost=hero_cls.cost
                    ),
                    player_index
                )
            ),
            hero_cls
        )
        if hero_cls.cost > player.gold:
            option.selectable = option.highlight = False
        menu.append(option)

menus['Buy Heroes'] = HwPagedMenu(
    title=_TR['menus']['Buy Heroes'],
    description=_TR['menus']['Gold'],
    select_callback=_buy_heroes_select_callback,
    build_callback=_buy_heroes_build_callback
)


# ======================================================================
# >> MAIN MENU
# ======================================================================

def _main_select_callback(menu, player_index, choice):
    """Main menu's select_callback function."""

    choice.value.previous_menu = menu
    return choice.value


def _main_build_callback(menu, player_index):
    """Main menu's build_callback function."""

    player = get_player(player_index, key='index')
    apply_tokens(menu[1].text, gold=player.gold)


menus['Main'] = SimpleMenu(
    data=[
        Text('Hero-Wars'),
        Text(_TR['menus']['Gold']),
        SimpleOption(1, _TR['menus']['Current Hero'], menus['Current Hero']),
        SimpleOption(2, _TR['menus']['Owned Heroes'], menus['Owned Heroes']),
        SimpleOption(3, _TR['menus']['Buy Heroes'], menus['Buy Heroes']),
        SimpleOption(0, _TR['menulib']['Close'])
    ],
    select_callback=_main_select_callback,
    build_callback=_main_build_callback
)
