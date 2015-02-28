# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.entities import Hero
from herowars.entities import Skill
from herowars.entities import Item

from herowars.tools import find_element
from herowars.tools import find_elements

from herowars.translations import get_translation
from herowars.translations import get_prefixed_translation

# Python
from functools import wraps

# Source.Python
from menus import PagedMenu
from menus import SimpleMenu
from menus import Option
from menus import Text

from menus.base import _translate_text

from messages import SayText2

from players.helpers import userid_from_index


# ======================================================================
# >> CLASSES
# ======================================================================

class HwPagedMenu(PagedMenu):
    """Overrides certain methods of the SourcePython's 
    PagedMenu class. 

    Additional Attributes:
        option7: Option-instance to show always at slot 7
                 uses select_callback function as value
        option8: Option-instance to show always at slot 8
                 uses menu instance as value
        page_info: Determines if page number should be visible or not
    """

    @wraps(PagedMenu.__init__)
    def __init__(
            self, data=None, select_callback=None,
            build_callback=None, description=None,
            title=None, top_seperator='-'*30, bottom_seperator='-'*30):
        super().__init__(
            data, select_callback, build_callback, description, title,
            top_seperator, bottom_seperator
        )
        self.option7 = None  # Custom slot 7
        self.option8 = None  # Custom slot 8 (back)
        self.player = None  # The player the menu is built for
        self.page_info = True  # True: shows pagenumber


    @wraps(PagedMenu._format_header)
    def _format_header(self, ply_index, page, slots):
        info = ''
        if self.page_info == True:  # Check to show pagenumber
            # Create the page info string
            info = '[{0}/{1}]\n'.format(page.index + 1, self.page_count)
        buffer = (_translate_text(self.title or '', ply_index)).ljust(
            len(self.top_seperator) - len(info)) + info

        # Set description if present
        if self.description is not None:
            buffer += _translate_text(self.description, ply_index) + '\n'

        # Set the top seperator if present
        if self.top_seperator is not None:
            buffer += self.top_seperator + '\n'

        return buffer


    @wraps(PagedMenu._format_body)
    def _format_body(self, ply_index, page, slots):
        buffer = ''

        # Get the maximum number of items for each page
        n = 6 if self.option7 else 7  # Enable special slot 7

        # Get all options for the current page
        options = page.options = self[page.index * n: (page.index + 1) * n]

        # Loop through all options of the current page
        for index, option in enumerate(options, 1):
            if not isinstance(option, Option):
                raise TypeError('Expected a RadioOption instance.')

            buffer += option._render(ply_index, index)
            if option.selectable:
                slots.add(index)

        # Fill the rest of the menu
        buffer += ' \n' * (n - len(options))

        return buffer

    @wraps(PagedMenu._format_footer)
    def _format_footer(self, ply_index, page, slots):
        buffer = ''

        # Set the bottom seperator if present
        if self.bottom_seperator is not None:
            buffer += self.bottom_seperator + '\n'

        # Add option 7
        if self.option7:
            buffer += self.option7._render(ply_index, 7)
            slots.add(7)

        # Add "Back" option
        # Enable it on first page if option8 is set
        back_selectable = True if self.option8 else page.index > 0
        buffer += Option(
            'Back', highlight=back_selectable)._render(ply_index, 8)
        if back_selectable:
            slots.add(8)

        # Add "Next" option
        next_selectable = page.index < self.last_page_index
        buffer += Option(
            'Next', highlight=next_selectable)._render(ply_index, 9)
        if next_selectable:
            slots.add(9)

        # Add "Close" option
        buffer += Option('Close', highlight=False)._render(ply_index, 0)

        # Return the buffer
        return buffer

    @wraps(PagedMenu._select)
    def _select(self, ply_index, choice):
        """Callbacks for custom option7 and option8"""

        if choice == 7 and self.option7:
            # Call option7's value function
            return self.option7.value(self, self.player.index, choice)

        elif (choice == 8 and self.option8 and 
                self._player_pages[self.player.index].index == 0):
            # Call option8's value function (menu-returning function)
            return self.option8.value(self.player)

        return super()._select(self.player.index, choice)


# ======================================================================
# >> MAINMENU
# ======================================================================

def main_menu(player):
    """Main menu for navigating between other Hero Wars menus."""
    menu = SimpleMenu()
    menu.player = player
    menu.select_callback = _main_menu_callback
    menu.extend([
        Text('Hero Wars'),
        Text('Gold: {gold}'.format(gold=player.gold)),
        Option(get_translation(player.lang_key, 'menus', 'buy_heroes'), 1),
        Option(get_translation(player.lang_key, 'menus', 'owned_heroes'), 2),
        Option(get_translation(player.lang_key, 'menus', 'current_hero'), 3),
        Option(get_translation(player.lang_key, 'menus', 'buy_items'), 4),
        Option(get_translation(player.lang_key, 'menus', 'sell_items'), 5),
        Text('0. Close')
    ])
    return menu


def _main_menu_callback(menu, _, choice):
    """Main menu callback."""

    if choice.value == 1:
        buy_hero_menu(menu.player).send(menu.player.index)
    elif choice.value == 2:
        owned_heroes_menu(menu.player).send(menu.player.index)
    elif choice.value == 3:
        current_hero_info_menu(
            menu.player, 
            return_to_main_menu=True
        ).send(menu.player.index)
    elif choice.value == 4:
        item_categories_menu(menu.player).send(menu.player.index)
    elif choice.value == 5:
        sell_items_menu(menu.player).send(menu.player.index)


# ======================================================================
# >> BUY HEROES -MENU
# ======================================================================

def buy_hero_menu(player):
    """Menu to display all non-owned heroes.

    Displays all heroes usable by player which he hasn't yet bought.
    Choosing a hero opens new Hero Info -menu with information
    about the skills and a buy option.
    """

    menu = HwPagedMenu(
        title=get_translation(player.lang_key, 'menus', 'buy_heroes'), 
        select_callback=_buy_hero_menu_callback
    )
    menu.player = player
    menu.option8 = Option('Back', main_menu)

    # Get all heroes not owned by player
    heroes = (
        hero_cls for hero_cls in Hero.get_subclasses()
        if not find_element(player.heroes, 'cls_id', hero_cls.cls_id)
    )

    for hero_cls in heroes:
        # Check if player can use the hero
        if (hero_cls.allowed_users 
                and player.steamid not in hero_cls.allowed_users):
            continue
        menu.append(Option('{name} ({cost})'.format(
            name=hero_cls.name, 
            cost=hero_cls.cost), 
            hero_cls
        ))

    if not menu:
        SayText2(message=get_prefixed_translation(
            player.lang_key, 
            'menu_messages', 
            'no_heroes_to_buy'
        )).send(player.index)

        menu = menu.option8.value(player)  # Refresh

    return menu


def _buy_hero_menu_callback(menu, _, choice):
    """Buy Heroes -menu callback.

    Sends the Hero Info -menu instance to the player.
    """

    hero_info_menu(menu.player, choice.value).send(menu.player.index)
        

# ======================================================================
# >> BUY ITEMS -MENU
# ======================================================================

def item_categories_menu(player):
    """Menu to display all item categories.

    Choosing a category will open a new menu
    with items of chosen category in it.
    """
    menu = HwPagedMenu(
        title=get_translation(player.lang_key, 'menus', 'item_categories'), 
        select_callback=_item_categories_menu_callback
    )
    menu.player = player
    menu.option8 = Option('Back', main_menu)

    items = (
        item for item in Item.get_subclasses()
        if (len(tuple(find_elements(player.hero.items, 'cls_id', item.cls_id))) 
            < item.limit) or item.limit <= 0
    )
    categories = set()
    for item in items:
        # Check if player can use the item
        if item.allowed_users and player.steamid not in item.allowed_users:
            continue
        if item.category not in categories:
            categories.add(item.category)

    for category in categories:
        menu.append(Option(category, category))

    if not menu:
        SayText2(message=get_prefixed_translation(
            player.lang_key,
            'menu_messages', 
            'no_items_to_buy'
        )).send(player.index)
        menu = menu.option8.value(player)  # Refresh

    return menu

def _item_categories_menu_callback(menu, _, choice):
    """Item Categories Menu callback

    Sends player a menu of items in chosen category
    """
    buy_items_menu(menu.player, choice.value).send(menu.player.index)


def buy_items_menu(player, chosen_category='Default'):
    """Menu to display items in certain category that can be bought.

    Displays all items that player doesn't own too many 
    of already and that can be bought by the player in
    certain category. Also displays item descriptions 
    below the item name and cost. Selecting an item 
    will immediately buy it.
    """

    menu = HwPagedMenu(
        title=get_translation(player.lang_key, 'menus', 'buy_items'), 
        select_callback=_buy_items_menu_callback
    )
    menu.player = player
    menu.option8 = Option('Back', item_categories_menu)
    menu.chosen_category = chosen_category

    items = (
        item for item in Item.get_subclasses()
        if (len(tuple(find_elements(player.hero.items, 'cls_id', item.cls_id))) 
            < item.limit) or item.limit <= 0
    )

    for item in items:
        # Check if player can use the item
        if item.allowed_users and player.steamid not in item.allowed_users:
            continue
        if item.category == chosen_category:
            menu.append(Option('{name} (buy ${cost})\n{description})'.format(
                name=item.name, 
                cost=item.cost, 
                description=item.description), 
                item
            ))

    if not menu:
        SayText2(message=get_prefixed_translation(
            player.lang_key, 
            'menu_messages', 
            'no_items_to_buy'
        )).send(player.index)
        menu = menu.option8.value(player)  # Refresh
    
    return menu


def _buy_items_menu_callback(menu, _, choice):
    """Buy Items -menu callback.

    Buys the selected item and adds it to player's hero's inventory.
    """

    item_cls = choice.value
    chosen_category = menu.chosen_category

    # Check if player can buy the item
    if menu.player.cash < item_cls.cost:
        translation = get_prefixed_translation(
            menu.player.lang_key, 'menu_messages', 'not_enough_cash')

        SayText2(message=translation.format(
            cash=menu.player.cash, 
            cost=item_cls.cost
        )).send(menu.player.index)

        # Refresh
        menu.close()
        buy_items_menu(menu.player, chosen_category).send(menu.player.index)

    # Buy the item
    menu.player.cash -= item_cls.cost
    menu.player.hero.items.append(item_cls())
    translation = get_prefixed_translation(
        menu.player.lang_key, 'menu_messages', 'bought_item')

    SayText2(message=translation.format(
        name=item_cls.name, 
        cost=item_cls.cost
    )).send(menu.player.index)

    # Refresh
    menu.close()
    buy_items_menu(menu.player, chosen_category).send(menu.player.index)


# ======================================================================
# >> OWNED HEROES -MENU
# ======================================================================

def owned_heroes_menu(player):
    """Owned Heroes menu.

    Displays all heroes owned by the player. Choosing a hero opens it
    in new Hero Info -menu with option to change the hero as active one.
    """

    menu = HwPagedMenu(
        title=get_translation(player.lang_key, 'menus', 'owned_heroes'), 
        select_callback=_owned_heroes_menu_callback
    )
    menu.player = player
    menu.option8 = Option('Back', main_menu)

    # Add all player's heroes to the menu
    for hero in player.heroes:
        menu.append(
            Option('{name} ({current_level}/{max_level})'.format(
                    name=hero.name, 
                    current_level=hero.level,
                    max_level=hero.max_level
                ), 
                hero
            )
        )

    if not menu:
        SayText2(message=get_prefixed_translation(
            player.lang_key, 
            'menu_messages', 
            'no_owned_heroes'
        )).send(player.index)
        menu = menu.option8.value(player.index)  # Refresh

    return menu


def _owned_heroes_menu_callback(menu, _, choice):
    """Owned Heroes -menu callback.

    Sends the Hero Info -menu instance of selected hero to the player.
    """

    owned_hero_info_menu(menu.player, choice.value).send(menu.player.index)


# ======================================================================
# >> SELL ITEMS -MENU
# ======================================================================

def sell_items_menu(player):
    """Sell Items menu.

    Displays all items owned by the players current hero.
    Choosing an item will immediately sell it.
    """

    menu = HwPagedMenu(
        title=get_translation(player.lang_key, 'menus', 'sell_items'), 
        select_callback=_sell_items_menu_callback
    )
    menu.player = player
    menu.option8 = Option('Back', main_menu)

    # Add all hero's items into the menu
    for item in player.hero.items:
        menu.append(Option('{name} (sell ${sell_value})'.format(
            name=item.name,
            sell_value=item.sell_value
            ), 
            item
        ))

    if not menu:
        SayText2(message=get_prefixed_translation(
            player.lang_key, 
            'menu_messages', 
            'no_owned_items'
        )).send(player.index)
        menu = menu.option8.value(player)  # Refresh
    
    return menu


def _sell_items_menu_callback(menu, _, choice):
    """Sell Items -menu callback.

    Sells the selected item.
    """

    item = choice.value
    menu.player.hero.items.remove(item)
    menu.player.cash += item.sell_value

    translation = get_prefixed_translation(
        menu.player.lang_key, 'menu_messages', 'sold_item')

    SayText2(message=translation.format(
        name=item.name, 
        cost=item.cost
    )).send(menu.player.index)

    # Refresh
    menu.close()
    sell_items_menu(menu.player).send(menu.player.index)


# ======================================================================
# >> HERO INFO -MENU
# ======================================================================

def hero_info_menu(player, hero_cls=None):
    """Hero Info menu.

    Menu to display hero info such as description and skills and
    their descriptions. Selecting option 7 will buy and set the selected
    hero active for the player.
    """

    menu = HwPagedMenu(select_callback=_hero_info_menu_callback)
    menu.player = player
    menu.title = '{name}\n{description}\n{seperator}Price: {price}\n'.format(
        name=hero_cls.name, 
        description=hero_cls.description,
        seperator=menu.top_seperator + '\n' if menu.top_seperator else '',
        price=hero_cls.cost
    )
    menu.page_info = False
    menu.selected_hero = hero_cls  # Callback needs to know the hero
    menu.option7 = Option(get_translation(
        player.lang_key, 'menus', 'option_buy'), _buy_hero)
    menu.option8 = Option('Back', buy_hero_menu)

    # Add all hero's skills and descriptions to the menu
    for skill in hero_cls.skill_set:
        menu.append(Option('{name}\n{description}'.format(
            name=skill.name, 
            description=skill.description
            ),
            None  # No value needed for now
        ))

    # Add all hero's passive skills and descriptions to the menu
    for passive in hero_cls.passive_set:
        menu.append(Option('{name} (passive)\n{description}'.format(
            name=passive.name,
            description=passive.description
            ), 
            None,  # No value needed for now
            highlight=False
        ))
    
    return menu


def _buy_hero(menu, _, choice):
    """Hero Info menu's callback for option 7.

    If option 7 (slot 7) was selected then buy and change to the hero.
    """

    hero = menu.selected_hero()

    # Check if player cannot buy the hero
    if menu.player.gold < hero.cost:
            translation = get_prefixed_translation(
                menu.player.lang_key, 'menu_messages', 'not_enough_gold')
            SayText2(message=translation.format(
                name=hero.name, 
                cost=hero.cost
            )).send(menu.player.index)
            
            # Refresh
            menu.close()
            hero_info_menu(menu.player).send(menu.player.index)
            return

    # Buy the hero
    menu.player.gold -= hero.cost
    menu.player.heroes.append(hero)

    # Change the hero automatically
    menu.player.hero = hero
    translation = get_prefixed_translation(
        menu.player.lang_key, 'menu_messages', 'bought_hero')
    SayText2(message=translation.format(
        name=hero.name, 
        cost=hero.cost
    )).send(menu.player.index)


def _hero_info_menu_callback(menu, _, choice):
    """Hero Info menu callback.

    Pressing the skills does nothing at the moment.
    """

    pass


# ======================================================================
# >> OWNED HEROINFO -MENU
# ======================================================================

def owned_hero_info_menu(player, hero=None):
    """Owned Hero Info menu.

    Menu to display hero info for owned heroes. Hero info includes
    hero's description, skills and their levels and descriptions.
    Selecting option 7 will set the selected hero active for the player.
    """

    menu = HwPagedMenu(select_callback=_owned_hero_info_menu_callback)
    menu.player = player
    menu.title = '{name}\n{description}\n{seperator}Level: {level}\n'.format(
        name=hero.name, 
        description=hero.description,
        seperator=menu.top_seperator + '\n' if menu.top_seperator else '',
        level=hero.level
    )
    menu.page_info = False
    menu.selected_hero = hero  # Callback needs to know the hero
    menu.option7 = Option(get_translation(
        player.lang_key, 'menus', 'option_change'), _change_hero)
    menu.option8 = Option('Back', owned_heroes_menu)

    # Add all the hero's skills, their levels and descriptions to the menu
    for skill in hero.skills:
        menu.append(
            Option('{name} {level}/{max}{required}\n{description}'.format(
                name=skill.name,
                level=skill.level,
                required=(' (req {0})'.format(skill.required_level)
                    if skill.required_level > 0 
                    and hero.level < skill.required_level else ''),
                max=skill.max_level,
                description=skill.description
            ), 
            None  # No value needed for now
        ))

    for passive in hero.passives:
        menu.append(Option('{name} (passive)\n{description}'.format(
            name=passive.name,
            description=passive.description
            ), 
            None,  # No value needed for now))
            highlight=False
        ))
    
    return menu


def _change_hero(menu, _, choice):
    """Owned Hero Info menu's callback for option 7.

    If option 7 was selected, then change to the hero.
    """ 
    hero = menu.selected_hero
    menu.player.hero = hero
    translation = get_prefixed_translation(
        menu.player.lang_key, 'menu_messages', 'changed_hero')
    SayText2(message=translation.format(name=hero.name)).send(menu.player.index)


def _owned_hero_info_menu_callback(menu, _, choice):
    """Owned Hero Info menu callback.

    Pressing the skills does nothing at the moment.
    """

    pass


# ======================================================================
# >> OWNED HEROINFO -MENU
# ======================================================================

def current_hero_info_menu(player, return_to_main_menu=False):
    """Current Hero Info menu.

    Menu to display skills and their levels for the active hero of
    the player.
    Allows leveling up of the skills by selecting any of the skills
    when skill points are available.
    Selecting option 7 resets the skill points.
    """

    menu = HwPagedMenu(select_callback=_current_hero_info_menu_callback)
    menu.player = player
    menu.return_to_main_menu = return_to_main_menu
    menu.title = '{name}\n{seperator}Level: {level}\n'.format(
        name=player.hero.name, 
        seperator=menu.top_seperator + '\n' if menu.top_seperator else '',
        level=player.hero.level
    )
    menu.page_info = False

    menu.option7 = Option(get_translation(
        player.lang_key, 'menus', 'reset_skill_points'), _reset_skill_points)

    if return_to_main_menu: 
        menu.option8 = Option('Back', main_menu)

    # Override the bottom seperator to display available skill points
    translation = get_translation(
        player.lang_key, 'menus', 'available_skill_points')
    menu.bottom_seperator = (
        menu.bottom_seperator + '\n' +
        translation.format(skill_points=player.hero.skill_points)
        + '\n' + menu.bottom_seperator
    )

    # Add all hero's skills and their levels to the menu
    for skill in player.hero.skills:
        menu.append(Option('{name} {level}/{max_level}{required}'.format(
            name=skill.name,
            level=skill.level,
            max_level=skill.max_level,
            required=(' (req {0})'.format(skill.required_level)
                if skill.required_level > 0 
                and player.hero.level < skill.required_level else ''),
            highlight=False if skill.max_level == 0 or
                skill.level >= skill.max_level else True
            ),
            skill,
        ))
    
    return menu


def _reset_skill_points(menu, _, choice):
    """Current Hero Info menu's callback for option 7.

    If option 7 was selected, reset skill points and refresh the menu.
    """

    SayText2(message=get_prefixed_translation(
        menu.player.lang_key, 
        'menu_messages', 
        'skill_points_reset'
    )).send(menu.player.index)

    for skill in menu.player.hero.skills:
        skill.level = 0

    # Refresh
    menu.close()
    current_hero_info_menu(
        menu.player, 
        menu.return_to_main_menu
    ).send(menu.player.index)


def _current_hero_info_menu_callback(menu, _, choice):
    """Current Hero Info menu's callback.

    If there are available skill points, level up the 
    selected skill and refresh the menu.
    """

    skill = choice.value

    if menu.player.hero.level < skill.required_level:
        translation = get_prefixed_translation(
            menu.player.lang_key, 
            'menu_messages', 
            'not_required_level'
        ).format(
            current_level=menu.player.hero.level,
            required_level=skill.required_level
        )

    elif skill.level >= skill.max_level:
        translation = get_translation(
            menu.player.lang_key, 
            'menu_messages', 
            'skill_maxed_out'
        )

    elif menu.player.hero.skill_points < skill.cost:
        translation = get_prefixed_translation(
            menu.player.lang_key, 
            'menu_messages', 
            'not_enough_skill_points'
        ).format(
            skill_points=menu.player.hero.skill_points,
            cost=skill.cost
        )

    else:  # Everything went good
        skill.level += 1
        translation = get_prefixed_translation(
            menu.player.lang_key, 
            'menu_messages', 
            'skill_leveled'
        ).format(
            name=skill.name, 
            level=skill.level
        )

    SayText2(message=translation).send(menu.player.index)

    refresh = False
    # Calculate if player can still use skill points
    for skill in menu.player.hero.skills:
        if (menu.player.hero.skill_points > skill.cost 
                and skill.level < skill.max_level 
                and menu.player.hero.level >= skill.required_level):
            refresh = True
            break

    menu.close()

    # Refresh
    if refresh:
        current_hero_info_menu(
            menu.player, 
            menu.return_to_main_menu
        ).send(menu.player.index)


