# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.tools import find_element
from hw.tools import find_elements
from hw.tools import shiftattr

from hw.configs import admins
from hw.entities import Hero
from hw.entities import Item
from hw.players import get_player
from hw.players import player_list

# Xtend
from xtend.menus import PagedMenu

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

_TR = LangStrings('hw/menus')

menus = {}


# ======================================================================
# >> CLASSES
# ======================================================================

class HeroMenu(PagedMenu):
    """
    Extends regular xtend's PagedMenu to accept hero argument.
    - hero: Hero class or instance
    - option7: shortcut property for binding constants[7]
    """

    def __init__(self, hero, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hero = hero

    @property
    def option7(self):
        return self.constants.get(7, None)

    @option7.setter
    def option7(self, value):
        self.constants[7] = value


class PlayerMenu(PagedMenu):
    """
    Extends regular xtend's PagedMenu to accept a player instance.
    - player: Player instance
    """

    def __init__(self, player=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = player


class ShiftAttrMenu(PagedMenu):
    """
    Extends regualr xtend's PagedMenu to accept an object
    and its attribute that will be altered.
    - obj: entity or player object
    - attr_name: name of entity's attribute that will be edited.
    """

    def __init__(self, obj=None, attr_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.obj = obj
        self.attr_name = attr_name


class EntitiesMenu(PagedMenu):
    """
    Extends regular xtend's PagedMenu to accept list of entities.
    - entities: List of entities with category attribute
    """

    def __init__(self, entities=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entities = entities or []


class CategoryMenu(EntitiesMenu):
    """
    Extends EntitiesMenu by adding callback menu for selected category.
    """

    def __init__(self, category_callback_menu, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_callback_menu = category_callback_menu

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
    menu.description = _TR['Description'].get_string(
        level=hero.level,
        skill_points=hero.skill_points
    )

    # Clear the menu
    menu.clear()

    # Loop through hero's skills
    for skill in hero.skills:

        # Set the default arguments for the PagedOption
        info = '{0}/{1}'.format(skill.level, skill.max_level)
        selectable = True

        # If skill is already maxed out
        if skill.level >= skill.max_level:
            info = ' ({0})'.format(_translate_text(
                _TR['Maxed'],
                player_index
            ))
            selectable = False

        # If the hero hasn't reached skill's required level
        elif skill.required_level > hero.level:
            info += ' ({0})'.format(_translate_text(
                _TR['Required'].get_string(
                    required=skill.required_level
                ),
                player_index
            ))
            selectable = False

        # If skill costs more than one, show the cost
        elif skill.cost > 1:
            info += ' ({0})'.format(_translate_text(
                _TR['Cost'].get_string(cost=skill.cost),
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


menus['Current Hero'] = PagedMenu(
    select_callback=_current_hero_select_callback,
    build_callback=_current_hero_build_callback,
    constants={7: PagedOption(_TR['Reset Skills'], 7)},
    display_page_info=False
)


# ======================================================================
# >> OWNED HEROES MENU
# ======================================================================

def _owned_heroes_select_callback(menu, player_index, choice):
    """Owned Heroes menu's select_callback function."""

    next_menu = HeroMenu(
        choice.value,
        select_callback=_hero_owned_info_select_callback,
        build_callback=_hero_owned_info_build_callback,
        constants={7: PagedOption(_TR['Change'], 7)},
        previous_menu=menu
    )

    return next_menu


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

        menu.append(option)


menus['Owned Heroes'] = PagedMenu(
    title=_TR['Owned Heroes'],
    select_callback=_owned_heroes_select_callback,
    build_callback=_owned_heroes_build_callback
)


# ======================================================================
# >> BUY HEROES MENU
# ======================================================================


def _buy_heroes_select_callback(menu, player_index, choice):
    """Buy Heroes menu's select_callback function."""

    next_menu = HeroMenu(
        choice.value,
        select_callback=_hero_owned_info_select_callback,
        build_callback=_hero_owned_info_build_callback,
        constants={7: PagedOption(_TR['Buy'], 7)},
    )
    next_menu.previous_menu = menu
    return next_menu


def _buy_heroes_build_callback(menu, player_index):
    """Buy Heroes menu's build_callback function."""

    player = get_player(player_index, key='index')
    menu.clear()
    for hero_cls in menu.entities:
        option = PagedOption(
            '{0} ({1})'.format(
                hero_cls.name,
                _translate_text(
                    _TR['Cost'].get_string(cost=hero_cls.cost),
                    player_index
                )
            ),
            hero_cls
        )
        if hero_cls.cost > player.gold:
            option.selectable = option.highlight = False
        menu.append(option)

menus['Buy Heroes'] = EntitiesMenu(
    title=_TR['Buy Heroes'],
    description=_TR['Gold'],
    select_callback=_buy_heroes_select_callback,
    build_callback=_buy_heroes_build_callback
)


# ======================================================================
# >> BUY ITEMS MENU
# ======================================================================


def _buy_items_select_callback(menu, player_index, choice):
    """Buy Items menu's select_callback function."""

    player = get_player(player_index, key='index')
    player.hero.items.append(choice.value())
    player.cash -= choice.value.cost


def _buy_items_build_callback(menu, player_index):
    """Buy Items menu's build_callback function."""

    player = get_player(player_index, key='index')
    menu.clear()
    for item in menu.entities:
        option = PagedOption(
            '{name} (${cost})\n{description}'.format(
                name=item.name,
                cost=_translate_text(
                    _TR['Cost'].get_string(cost=item.cost),
                    player_index
                ),
                description=item.description
            ),
            item
        )
        if item.cost > player.gold:
            option.selectable = option.highlight = False
        menu.append(option)

menus['Buy Items'] = EntitiesMenu(
    title=_TR['Buy Items'],
    select_callback=_buy_items_select_callback,
    build_callback=_buy_items_build_callback
)

# ======================================================================
# >> SELL ITEMS MENU
# ======================================================================


def _sell_items_select_callback(menu, player_index, choice):
    """Sell Items menu's select_callback function."""

    player = get_player(player_index, key='index')
    player.hero.items.remove(choice.value)
    player.cash += choice.value.sell_value


def _sell_items_build_callback(menu, player_index):
    """Sell Items menu's build_callback function."""

    player = get_player(player_index, key='index')
    menu.clear()
    for item in player.hero.items:
        menu.append(PagedOption('{name} (+${sell_value})'.format(
            name=item.name,
            sell_value=item.sell_value
            ), item
        ))

menus['Sell Items'] = EntitiesMenu(
    title=_TR['Sell Items'],
    select_callback=_sell_items_select_callback,
    build_callback=_sell_items_build_callback
)

# ======================================================================
# >> ENTITY CATEGORY MENU
# ======================================================================


def _entity_categories_select_callback(menu, player_index, choice):
    """Entity Categories menu's select_callback function."""

    next_menu = menu.category_callback_menu
    next_menu.previous_menu = menu
    next_menu.entities = choice.value
    return next_menu


def _buy_hero_categories_build_callback(menu, player_index):
    """Buy Hero Categories menu's build_callback function."""

    player = get_player(player_index, key='index')
    menu.entities = []

    for hero_cls in Hero.get_subclasses():
        if find_element(player.heroes, 'cls_id', hero_cls.cls_id):
            continue
        elif (hero_cls.allowed_users
                and player.steamid not in hero_cls.allowed_users):
            continue
        menu.entities.append(hero_cls)

    menu.clear()
    categories = dict()

    for entity in menu.entities:
        if entity.category not in categories:
            categories[entity.category] = [entity]
        else:
            categories[entity.category].append(entity)

    for category in categories:
        menu.append(PagedOption('{category} ({size})'.format(
            category=category,
            size=len(categories[category])
            ), categories[category]
        ))


def _buy_item_categories_build_callback(menu, player_index):
    """Buy Hero Categories menu's build_callback function."""

    player = get_player(player_index, key='index')
    menu.entities = []

    for item in Item.get_subclasses():
        if (len(tuple(find_elements(player.hero.items, 'cls_id', item.cls_id)))
                >= item.limit):
            continue
        elif (item.allowed_users and player.steamid not in item.allowed_users):
            continue
        menu.entities.append(item)

    menu.clear()
    categories = dict()

    for entity in menu.entities:
        if entity.category not in categories:
            categories[entity.category] = [entity]
        else:
            categories[entity.category].append(entity)

    for category in categories:
        menu.append(PagedOption('{category} ({size})'.format(
            category=category,
            size=len(categories[category])
            ), categories[category]
        ))

menus['Hero Buy Categories'] = CategoryMenu(
    category_callback_menu=menus['Buy Heroes'],
    title=_TR['Hero Categories'],
    select_callback=_entity_categories_select_callback,
    build_callback=_buy_hero_categories_build_callback
)

menus['Item Buy Categories'] = CategoryMenu(
    category_callback_menu=menus['Buy Items'],
    title=_TR['Item Categories'],
    select_callback=_entity_categories_select_callback,
    build_callback=_buy_item_categories_build_callback
)

# ======================================================================
# >> HERO BUY INFO MENU
# ======================================================================


def _hero_buy_info_select_callback(menu, player_index, choice):
    """Hero Buy Info menu's select_callback function."""

    if choice.value == 7:
        player = get_player(player_index, key='index')
        if player.gold > menu.hero.cost:
            hero = menu.hero()
            player.gold -= hero.cost
            player.heroes.append(hero)
            player.hero = hero
            print('changed hero to '+hero.name)  # TODO: Temporary


def _hero_buy_info_build_callback(menu, player_index):
    """Hero Buy Info menu's build_callback function."""

    menu.clear()
    menu.title = '{name} {cost}'.format(
        name=menu.hero.name,
        cost=menu.hero.cost
    )

    for passive in menu.hero.passive_set:
        menu.append(Text('P. {name}\n{description}'.format(
            name=passive.name,
            description=passive.description
        )))

    for skill in menu.hero.skill_set:
        menu.append(PagedOption(
            '{name}{max_level}{cost}{req}\n{description}'.format(
                name=skill.name,
                max_level=' '+_TR['Max'].get_string(max=skill.max_level),
                cost=(' '+_TR['Cost'].get_string(cost=skill.cost)
                    if skill.cost != 1 else ''),
                req=(' '+_TR['Required'].get_string(
                    required=skill.required_level)
                    if skill.required_level != 0 else ''),
                description=skill.description  # TODO: Split to lines
            )
        ))

# ======================================================================
# >> HERO OWNED INFO MENU
# ======================================================================


def _hero_owned_info_select_callback(menu, player_index, choice):
    """Hero Owned Info menu's select_callback function."""
    if choice.value == 7:
        player = get_player(player_index, key='index')
        player.hero = menu.hero
        print('changed hero to '+player.hero.name)


def _hero_owned_info_build_callback(menu, player_index):
    """Hero Owned Info menu's build_callback function."""

    menu.clear()
    menu.title = '{name} {level}/{max_level}'.format(
        name=menu.hero.name,
        level=menu.hero.level,
        max_level=menu.hero.max_level
    )

    for passive in menu.hero.passive_set:
        menu.append(Text('P. {name}\n{description}'.format(
            name=passive.name,
            description=passive.description
        )))

    for skill in menu.hero.skills:
        menu.append(PagedOption(
            '{name} {level}/{max_level}{cost}{req}\n{description}'.format(
                name=skill.name,
                level=skill.level,
                max_level=skill.max_level,
                cost=(' '+_TR['Cost'].get_string(cost=skill.cost)
                    if skill.cost != 1 else ''),
                req=(' '+_TR['Required'].get_string(
                    required=skill.required_level)
                    if skill.required_level != 0 else ''),
                description=skill.description  # TODO: Split to lines
            )
        ))


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
    menu[1].text.get_string(gold=player.gold)


menus['Main'] = SimpleMenu(
    data=[
        Text('Hero-Wars'),
        Text(_TR['Gold']),
        Text(' '),
        SimpleOption(1, _TR['Current Hero'], menus['Current Hero']),
        SimpleOption(2, _TR['Owned Heroes'], menus['Owned Heroes']),
        SimpleOption(3, _TR['Buy Heroes'], menus['Hero Buy Categories']),
        Text(' '),
        SimpleOption(4, _TR['Sell Items'], menus['Sell Items']),
        SimpleOption(5, _TR['Buy Items'], menus['Item Buy Categories']),
        Text(' '),
        SimpleOption(0, _TR['Close'])
    ],
    select_callback=_main_select_callback,
    build_callback=_main_build_callback
)

# ======================================================================
# >> PLAYERS MENU
# ======================================================================


def _admin_players_select_callback(menu, player_index, choice):
    """Admin Players menu's select_callback function."""

    next_menu = menus['Admin Player Management']
    next_menu.player = choice.value
    next_menu.previous_menu = menu
    return next_menu


def _players_build_callback(menu, player_index):
    """Players menu's build_callback function."""

    menu.clear()
    for player in player_list:
        menu.append(PagedOption(player.name, player))


menus['Admin Players Menu'] = PagedMenu(
    title=_TR['Pick Player'],
    select_callback=_admin_players_select_callback,
    build_callback=_players_build_callback
)


# ======================================================================
# >> PLAYER MANAGEMENT MENU
# ======================================================================


def _player_management_select_callback(menu, player_index, choice):
    """Player Management menu's select_callback function."""

    next_menu = menus['Shift Attr']
    next_menu.obj = choice.value[0]
    next_menu.attr_name = choice.value[1]
    next_menu.previous_menu = menu
    return next_menu


def _player_management_build_callback(menu, player_index):
    """Player Management menu's build_callback function."""

    menu.clear()
    menu.title = menu.player.name
    menu.description = '{0} ({1})'.format(
        menu.player.hero.name,
        menu.player.hero.level
    )
    menu.extend([
        PagedOption(_TR['Give Gold'], (menu.player, 'gold')),
        PagedOption(_TR['Give Cash'], (menu.player, 'cash')),
        PagedOption(_TR['Give Exp'], (menu.player.hero, 'exp')),
        PagedOption(_TR['Give Level'], (menu.player.hero, 'level'))
    ])

menus['Admin Player Management'] = PlayerMenu(
    select_callback=_player_management_select_callback,
    build_callback=_player_management_build_callback
)


# ======================================================================
# >> SHIFT ATTR MENU
# ======================================================================


def _shift_attr_select_callback(menu, player_index, choice):
    """Shift Attr menu's select_callback function."""

    shiftattr(menu.obj, menu.attr_name, choice.value)
    return menu


def _shift_attr_build_callback(menu, player_index):
    """Shift Attr menu's build_callback function."""

    menu.description = '{entity_name} - {attr_name}: {attr_value}'.format(
        entity_name=menu.obj.name,
        attr_name=menu.attr_name,
        attr_value=getattr(menu.obj, menu.attr_name)
    )

menus['Shift Attr'] = ShiftAttrMenu(
    data=[
        PagedOption('+1', 1),
        PagedOption('+10', 10),
        PagedOption('+25', 25),
        PagedOption('+50', 50),
        PagedOption('+100', 100),
        PagedOption('+1000', 1000),
        PagedOption('+10000', 10000),
        PagedOption('-1', -1),
        PagedOption('-10', -10),
        PagedOption('-25', -25),
        PagedOption('-50', -50),
        PagedOption('-100', -100),
        PagedOption('-1000', -1000),
        PagedOption('-10000', -10000)
    ],
    title=_TR['Pick Amount'],
    select_callback=_shift_attr_select_callback,
    build_callback=_shift_attr_build_callback
)


# ======================================================================
# >> ADMIN MENU
# ======================================================================

def _admin_select_callback(menu, player_index, choice):
    """Admin menu's select_callback function."""
    next_menu = choice.value
    next_menu.previous_menu = menu
    return next_menu


def _admin_build_callback(menu, player_index):
    """Admin menu's build_callback function."""

    player = get_player(player_index, key='index')

    menu.clear()

    if player.steamid in admins:
        menu.extend([
            Text('Admin'),
            SimpleOption(1, 'Player Management', menus['Admin Players Menu'])
        ])
    else:
        menu.append(Text('Not an admin!'))

menus['Admin'] = SimpleMenu(
    select_callback=_admin_select_callback,
    build_callback=_admin_build_callback
)
