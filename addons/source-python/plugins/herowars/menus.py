# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.entities import Hero
from herowars.entities import Skill
from herowars.entities import Item

from herowars.player import players

from herowars.tools import find_element
from herowars.tools import find_elements
from herowars.tools import get_messages

# Python
from functools import wraps

# Source.Python
from menus import PagedMenu
from menus import SimpleMenu
from menus import PagedOption as Option
from menus import SimpleOption
from menus import Text

from menus.base import _translate_text

from translations.strings import LangStrings
from translations.strings import TranslationStrings

from players.helpers import get_client_language
from players.helpers import userid_from_index



# ======================================================================
# >> TRANSLATIONS
# ======================================================================

menu_options = LangStrings('herowars/menu_options')
menu_messages = get_messages(LangStrings('herowars/menu_messages'))


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
        self.option8  = None  # Custom slot 8 (back)
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


    """@wraps(PagedMenu._format_body)
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

        return buffer"""

    """@wraps(PagedMenu._format_body)
    def _format_body(self, player_index, page, slots):
        buffer = super()._format_body(player_index, page, slots)
        if self.option7:
            buffer += self.option7._render(player_index, 7)
        return buffer"""

    def _get_max_item_count(self):
        return 6 if self.option7 else 7

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
    def _select(self, player_index, choice_index):
        """Callbacks for custom option7 and option8"""

        if choice_index == 7 and self.option7:
            # Call option7's value function
            return self.option7.value(self, self.player.index, choice_index)

        elif (choice_index == 8 and self.option8 and 
                self._player_pages[self.player.index].index == 0):
            # Call option8's value function (menu-returning function)
            return self.option8.value(**self.option8.kwargs)

        return super()._select(self.player.index, choice_index)

    """def _select(self, player_index, choice_index):

        # Do nothing if the menu is being closed
        if choice_index == 0:
            del self._player_pages[player_index]
            return None

        # Get the player's current page
        page = self._player_pages[player_index]

        # Display previous page?
        if choice_index == 8:
            self.set_player_page(player_index, page.index - 1)
            return self

        # Display next page?
        if choice_index == 9:
            self.set_player_page(player_index, page.index + 1)
            return self

        return super(PagedRadioMenu, self)._select(player_index, choice_index)"""

class HwText(Text):

    @wraps(Text.__init__)
    def __init__(self, text, **kwargs):
        super().__init__(text)
        self.kwargs = kwargs

    @wraps(Text._render)
    def _render(self, player_index, choice_index=None):
        """Render the data.

        @param <player_index>:
        A player index.

        @param <choice_index>:
        The number should be required to select this item. It depends on the
        menu type if this parameter gets passed.
        """
        return str(_hw_translate_text(
            self.text, 
            player_index,
            **self.kwargs
        )) + '\n'


class HwOption(Option):

    @wraps(Option.__init__)
    def __init__(self, text, value=None, highlight=True, 
            selectable=True, translate_kwargs=dict(), **kwargs):
    
        super().__init__(text, value, highlight, selectable)
        self.translate_kwargs = translate_kwargs
        self.kwargs = kwargs

    @wraps(Option._render)  
    def _render(self, player_index, choice_index):
        """Render the data.

        @param <player_index>:
        A player index.

        @param <choice_index>:
        The number should be required to select this item. It depends on the
        menu type if this parameter gets passed.
        """
        return '{0}{1}. {2}\n'.format(
            self._get_highlight_prefix(),
            choice_index,
            _hw_translate_text(
                self.text, 
                player_index, 
                **self.translate_kwargs
            )
        )


def _hw_translate_text(text, player_index, **kwargs):
    """Translate <text> if it is an instance of TranslationStrings.

    Otherwise the original text will be returned.
    """
    if isinstance(text, TranslationStrings):
        return text.get_string(get_client_language(player_index), **kwargs)

    return text

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
        HwText(menu_options['Gold'], gold=player.gold),
        SimpleOption(1, menu_options['Buy Heroes']),
        SimpleOption(2, menu_options['Owned Heroes']),
        SimpleOption(3, menu_options['Current Hero']),
        SimpleOption(4, menu_options['Buy Items']),
        SimpleOption(5, menu_options['Sell Items']),
        SimpleOption(0, menu_options['Close'], highlight=False)
    ])

    return menu

def _main_menu_callback(menu, _, choice):
    """Main menu callback."""

    if choice.choice_index == 1:
        buy_hero_menu(menu.player).send(menu.player.index)
    elif choice.choice_index == 2:
        owned_heroes_menu(menu.player).send(menu.player.index)
    elif choice.choice_index == 3:
        current_hero_info_menu(
            menu.player, 
            return_to_main_menu=True
        ).send(menu.player.index)
    elif choice.choice_index == 4:
        item_categories_menu(menu.player).send(menu.player.index)
    elif choice.choice_index == 5:
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
        title=menu_options['Buy Heroes'], 
        select_callback=_buy_hero_menu_callback
    )
    menu.player = player
    menu.option8 = HwOption(menu_options['Back'], main_menu, player=player)

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
        menu_messages['No Heroes To Buy'].send(player.index)
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
        title=menu_options['Item Categories'], 
        select_callback=_item_categories_menu_callback
    )
    menu.player = player
    menu.option8 = HwOption(menu_options['Back'], main_menu, player=player)

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
        menu_messages['No Items To Buy'].send(player.index)
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
        title=menu_options['Buy Items'], 
        select_callback=_buy_items_menu_callback
    )
    menu.player = player
    menu.option8 = HwOption(menu_options['Back'], item_categories_menu, player=player)
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
        menu_messages['No Items To Buy'].send(player.index)
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
        menu_messages['Not Enough Cash'].send(
            menu.player.index, 
            cash=menu.player.cash, 
            cost=item_cls.cost
        )

        # Refresh
        menu.close()
        buy_items_menu(menu.player, chosen_category).send(menu.player.index)

    # Buy the item
    menu.player.cash -= item_cls.cost
    menu.player.hero.items.append(item_cls())

    menu_messages['Bought Item'].send(
        menu.player.index,
        name=item_cls.name,
        cost=item_cls.cost
    )

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
        title=menu_options['Owned Heroes'], 
        select_callback=_owned_heroes_menu_callback
    )
    menu.player = player
    menu.option8 = HwOption(menu_options['Back'], main_menu, player=player)

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
        menu_messages['No Owned Heroes'].send(player.index)
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
        title=menu_options['Sell Items'], 
        select_callback=_sell_items_menu_callback
    )
    menu.player = player
    menu.option8 = HwOption(menu_options['Back'], main_menu, player=player)

    # Add all hero's items into the menu
    for item in player.hero.items:
        menu.append(Option('{name} (sell ${sell_value})'.format(
            name=item.name,
            sell_value=item.sell_value
            ), 
            item
        ))

    if not menu:
        menu_messages['No Owned Items'].send(player.index)
        menu = menu.option8.value(player)  # Refresh
    
    return menu


def _sell_items_menu_callback(menu, _, choice):
    """Sell Items -menu callback.

    Sells the selected item.
    """

    item = choice.value
    menu.player.hero.items.remove(item)
    menu.player.cash += item.sell_value

    menu_messages['Sold Item'].send(
        menu.player.index,
        name=item.name,
        cost=item.cost
    )

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
    menu.option7 = Option(menu_options['Buy'], _buy_hero)
    menu.option8 = HwOption(menu_options['Back'], buy_hero_menu, player=player)

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
            menu_messages['Not Enough Gold'].send(
                menu.player.index,
                name=hero.name,
                cost=hero.cost
            )
            
            # Refresh
            menu.close()
            hero_info_menu(menu.player).send(menu.player.index)
            return

    # Buy the hero
    menu.player.gold -= hero.cost
    menu.player.heroes.append(hero)

    # Change the hero automatically
    menu.player.hero = hero

    menu_messages['Bough Hero'].send(
        menu.player.index,
        name=hero.name,
        cost=hero.cost
    )


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
    menu.option7 = Option(menu_options['Change'], _change_hero)
    menu.option8 = HwOption(menu_options['Back'], owned_heroes_menu, player=player)

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
    menu_messages['Changed Hero'].send(menu.player.index, name=hero.name)


def _owned_hero_info_menu_callback(menu, _, choice):
    """Owned Hero Info menu callback.

    Pressing the skills does nothing at the moment.
    """

    pass


# ======================================================================
# >> CURRENT HEROINFO -MENU
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

    menu.option7 = Option(
        menu_options['Reset Skill Points'], 
        _reset_skill_points
    )

    if return_to_main_menu: 
        menu.option8 = HwOption(menu_options['Back'], main_menu, player=player)

    # Override the bottom seperator to display available skill points
    menu.bottom_seperator = (
        menu.bottom_seperator + '\n' +
        'SP: {0}'.format(player.hero.skill_points)
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
    menu_messages['Skill Points Reset'].send(menu.player.index)

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
        menu_messages['Not Required Level'].send(
            menu.player.index,
            current=menu.player.hero.level,
            required=skill.required_level
        )

    elif skill.level >= skill.max_level:
        menu_messages['Skill Maxed Out'].send(menu.player.index)

    elif menu.player.hero.skill_points < skill.cost:
        menu_messages['Not Enough Skill Points'].send(
            menu.player.index,
            skill_points=menu.player.hero.skill_points,
            cost=skill.cost
        )

    else:  # Everything went good
        skill.level += 1
        menu_messages['Skill Leveled'].send(
            menu.player.index,
            name=skill.name, 
            level=skill.level
        )

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


# ======================================================================
# >> ADMIN MAIN MENU
# ======================================================================

def admin_menu(player):
    """Main admin menu.

    Privately accessed menu for specified steamid's only.
    Includes Hero Wars admin functions.
    """

    menu = SimpleMenu()
    menu.player = player
    menu.select_callback = _admin_callback

    menu.extend([
        Text('Hero Wars - Admin'),
        SimpleOption(1, 'Manage players'),
        Text('0. Close')
    ])

    return menu


def _admin_callback(menu, _, choice):
    """Admin menu callback.

    Sends the correct sub-menu depending on chosen
    admin function.
    """

    if choice.choice_index == 1:
        player_pick_menu(
            menu.player,
            _admin_player_pick_callback, 
            admin_menu
        ).send(menu.player.index)


def _admin_player_pick_callback(menu, _, choice):
    """Callback function for admin player management.

    Sends the settings page for chosen player
    """
    admin_player_settings_menu(menu.player, choice.value).send(
        menu.player.index
    )


# ======================================================================
# >> GENERAL PLAYER PICK MENU
# ======================================================================

def player_pick_menu(player, callback_function, previous_menu=None):
    """Menu for picking a player.

    Menu with all the server's players as options.
    Choosing a player will execute the callback_function.
    """

    menu = HwPagedMenu(select_callback=callback_function)
    menu.player = player
    menu.title = 'Choose a player'

    # If previous menu was set, use the custom back button
    if previous_menu:
        menu.option8 = HwOption(menu_options['Back'], previous_menu, player=player)

    # Add all players into the menu
    for player in players:
        menu.append(Option(player.name, player))
    
    return menu


# ======================================================================
# >> ADMIN PLAYER SETTINGS MENU
# ======================================================================

def admin_player_settings_menu(player, chosen_player):
    """Player specific options for admins.

    Provides options for controlling the chosen player.
    Allows giving of different attributes.
    In future may include resetting attributes,
    changing hero etc.
    """

    menu = HwPagedMenu(select_callback=_admin_player_settings_callback)
    menu.player = player
    menu.chosen_player = chosen_player
    menu.title = '{name}\n{hero_name} ({hero_level}) \n'.format(
        name=chosen_player.name,
        hero_name=chosen_player.hero.name,
        hero_level=chosen_player.hero.level
    )
    menu.page_info = False
    menu.top_seperator = '-'*30

    menu.option8 = HwOption(
        'Back', 
        player_pick_menu, 
        player=player, 
        callback_function=_admin_player_pick_callback, 
        previous_menu=admin_menu
    )
    
    menu.extend([
        Option('Give Exp', 'exp'),
        Option('Give Level', 'level'),
        Option('Give Cash', 'cash'),
        Option('Give Gold', 'gold')
    ])
    return menu


def _admin_player_settings_callback(menu, _, choice):
    """Admin player settings menu callback.

    Executes the chosens function on the player.
    """

    admin_give_amount_menu(
        menu.player, 
        menu.chosen_player, 
        choice.value
    ).send(menu.player.index)
 

# ======================================================================
# >> ADMIN GIVE AMOUNT MENU
# ======================================================================

def admin_give_amount_menu(player, chosen_player, chosen_attr):
    """Choose the amount of chosen attribute to give to chosen player.

    Chosen_values is a tuple (object, attribute) that will
    get boosted by the amount chosen in this menu.
    """

    menu = HwPagedMenu(select_callback=_admin_give_amount_callback)
    menu.player = player
    menu.chosen_player = chosen_player
    menu.chosen_attr = chosen_attr

    # Pick the right object
    if (not hasattr(chosen_player, chosen_attr) and 
            hasattr(chosen_player.hero, chosen_attr)):
        menu.chosen_object = chosen_player.hero
    else:
        menu.chosen_object = chosen_player

    menu.option8 = HwOption(
        'Back', 
        admin_player_settings_menu, 
        player=player, 
        chosen_player=menu.chosen_player
    )

    menu.title = 'Pick an amount'

    menu.extend([
        Option('1', 1),
        Option('5', 5),
        Option('10', 10),
        Option('50', 50),
        Option('100', 100),
        Option('500', 500),
        Option('1 000', 1000),
        Option('5 000', 5000),
        Option('10 000', 10000)
    ])

    return menu

def _admin_give_amount_callback(menu, _, choice):
    """Admin give amount menu callback.

    Gives the chosen amount of chosen attribute to the
    chosen player.
    """

    setattr(menu.chosen_object, menu.chosen_attr, 
        getattr(
            menu.chosen_object, 
            menu.chosen_attr
        )+choice.value
    )

    menu.close()
    admin_give_amount_menu(
        menu.player, 
        menu.chosen_player, 
        menu.chosen_attr
    ).send(menu.player.index)



