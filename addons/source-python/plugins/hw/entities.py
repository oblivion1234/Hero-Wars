# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.tools import get_subclasses
from hw.tools import classproperty

from hw.configs import default_hero_category
from hw.configs import default_item_category
from hw.configs import item_sell_value_multiplier
from hw.configs import exp_algorithm

from hw.events import Hero_Pre_Level_Up

# Source.Python
from messages import SayText2


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all___ = (
    'Entity',
    'Hero',
    'Skill',
    'Item'
)


# ======================================================================
# >> CLASSES
# ======================================================================

class Entity(object):
    """The base element of Hero-Wars.

    Entity is a base class for most of the Hero-Wars classes.
    It implements common properties like name and description, as well
    as common behavior and methods for most objects in Hero-Wars.

    Attributes:
        level: Entity's Hero-Wars level

    Class Attributes:
        name: Entity's name
        description: Short description of the entity
        authors: Creators/Designers of the entity
        cost: How much does the entity cost
        max_level: Maximum level the entity can be leveled to
        required_level: Required level before the entity can be used
        allowed_users: List of steamids of those who can use the entity
    """

    # Defaults
    name = str()
    description = str()
    authors = list()
    cost = int()
    max_level = None
    allowed_players = list()

    @classproperty
    def cid(cls):
        """Gets the class' id.

        Returns the name of the class or instance's class.
        Can be called from the class or one of its instances.

        Returns:
            The class id
        """

        return cls.__name__

    def __init__(self, level=0):
        """Initializes a new Hero-Wars entity.

        Args:
            level: Entity's starting level
        """

        self._level = level

    @property
    def level(self):
        """Getter for entity's level.

        Returns:
            Entity's level
        """

        return self._level

    @level.setter
    def level(self, level):
        """Setter for entity's level.

        Raises:
            ValueError: If the level is set to a negative value or
                to a value higher than max_level
        """

        if level < 0:
            raise ValueError('Attempt to set a negative level for an entity.')
        elif self.max_level is not None and level > self.max_level:
            raise ValueError(
                'Attempt to set an entity\'s level over it\'s maximum level.')
        self._level = level

    @classmethod
    def get_subclasses(cls):
        """Gets a list of entity class's subclasses.

        Returns:
            List of entity class's subclasses
        """

        return sorted(
            (subcls for subcls in get_subclasses(cls)),
            key=lambda subcls: subcls.cid
        )

    def get_message_prefix(self):
        """Getter for entity's message prefix.

        Returns:
            Entity's message prefix
        """

        return '[{}] '.format(self.name)

    def message(self, player_index, message):
        """Sends a message from an entity to a player using SayText2.

        Args:
            player_index: Index of the player who to send the message to
            message: Message to send
        """

        SayText2(message='{prefix}{msg}'.format(
            prefix=self.get_message_prefix(),
            msg=message
        )).send((player_index,))


class Hero(Entity):
    """Heroes strenghten players, giving them a set of powerful skills.

    Each hero has its own unique skill set (see hw.core.Skill) to
    spice up the game.
    Clients attempt to level up their heroes by gaining enough
    experience points (exp) until the hero levels up.
    Experience points are gained from in-game tasks, such as killing
    enemies and planting bombs.
    After leveling up, player can upgrade the hero's skills.

    Attributes:
        skills: List of hero object's skills
        exp: Hero's experience points for gradually leveling up
        required_exp: Experience points required for hero to level up

    Class Attributes:
        skill_set (cls var): List of skill classes the hero will use
    """

    # Defaults
    skill_set = tuple()
    passive_set = tuple()
    category = default_hero_category

    def __init__(self, level=0, exp=0):
        """Initializes a new Hero-Wars hero.

        Args:
            level: Hero's current level
            exp: Hero's experience points
        """

        super().__init__(level)
        self._exp = exp
        self.skills = [skill() for skill in self.skill_set]
        self.passives = [passive() for passive in self.passive_set]
        self.items = []

    @property
    def required_exp(self):
        """Calculate required experience points for a hero to level up.

        Returns:
            Required experience points for leveling up
        """

        if self.max_level is not None and self.level >= self.max_level:
            return 0
        return exp_algorithm(self.level)

    @Entity.level.setter
    def level(self, level):
        """Level setter for hero.

        Sets hero's level to an absolute value, and manages setting
        his experience points to zero in case the level was decreased.
        This is mostly used only by admins.

        Args:
            level: Level to set the hero to
        """

        self._exp = 0
        Entity.level.fset(self, level)  # Call to Entity's level setter
        Hero_Pre_Level_Up(cid=self.cid, id=str(id(self))).fire()

    @property
    def exp(self):
        """Getter for hero's experience points.

        Returns:
            Hero's experience points
        """

        return self._exp

    @exp.setter
    def exp(self, exp):
        """Setter for hero's experience points.

        Sets hero's exp, increases hero's level as his experience points
        reach their maximum.

        Raises:
            ValueError: If attempting to set exp to a negative value
        """

        # Make sure exp is positive
        if exp < 0:
            raise ValueError('Attempt to set negative exp for a hero.')

        # If exp differs from current exp
        if exp != self._exp:

            # Set the new exp and get old level
            self._exp = exp
            old_level = self.level

            # Increase levels while necessary
            while (self.exp >= self.required_exp and
                    (self.max_level is None or self.level < self.max_level)):
                self._exp -= self.required_exp
                self._level += 1

            # Make sure the hero's level is not over the maximum level
            if self.max_level is not None and self.level >= self.max_level:
                self.level = self.max_level

            # Fire the level up event
            if self.level > old_level:
                Hero_Pre_Level_Up(cid=self.cid, id=str(id(self))).fire()

    @property
    def skill_points(self):
        """Gets the amount of hero's unused skill points.

        Returns:
            Unused skill points
        """

        used_points = sum(skill.level * skill.cost for skill in self.skills)
        return self._level - used_points

    def execute_skills(self, method_name, **eargs):
        """Executes hero's skills and passives.

        Calls each of hero's skills' and passives' execute() method with
        the given eargs.

        Args:
            method_name: Name of the method to execute
            eargs: Additional information of the event
        """

        for passive in self.passives:
            passive.execute_method(method_name, **eargs)
        for skill in self.skills:
            if skill.level:
                skill.execute_method(method_name, **eargs)
        for item in self.items:
            item.execute_method(method_name, **eargs)

    @classmethod
    def skill(cls, skill_class):
        """Decorator for adding skills to a hero's skill set.

        Decorator that allows easily adding skills into hero's skill set
        upon the definition of the skill class. The decorated skill
        class will get appended to the end of the skill set.

        Args:
            skill_class: Skill class to add into hero's skill set

        Returns:
            The skill without any modifications, simply appended to
            the hero's skill set.
        """

        cls.skill_set += (skill_class, )
        return skill_class

    @classmethod
    def passive(cls, skill_class):
        """Decorator for adding passive skills to a hero's skill set.

        Read Hero.skill for more info.

        Args:
            skill_class: Skill class to add into hero's skill set

        Returns:
            The passive skill without any modifications, simply appended
            to the hero's passive skill set.
        """

        cls.passive_set += (skill_class, )
        return skill_class


class Skill(Entity):
    """Skills give custom powers and effects for heroes.

    Skills are what heroes use to become strong an dunique; they allow
    more versatile gameplay for Hero-Wars. Each hero has a certain skill
    set, and each skill gets used during a certain event or action to
    create a bonus effect, such as damaging the enemy.
    """

    # Defaults
    cost = int(1)
    max_level = int(6)
    required_level = int(0)

    def execute_method(self, method_name, **eargs):
        """Executes skill's method.

        Executes the skill's method with matching name to the
        method_name with provided event arguments.

        Args:
            method_name: Name of the method to execute
            eargs: Additional information of the event
        """

        method = getattr(self.__class__, method_name, None)
        if method:
            method(self, **eargs)


class Item(Skill):
    """Items are kind of temporary skills that can be bought on heroes.

    Each hero can equip 6 items at once, they can be bought and sold
    and some can be upgraded.

    Class Attributes:
        permanent: Does the item stay when the hero dies
    """

    # Defaults
    name = 'Unnamed Item'
    description = 'This is an item.'
    cost = 10
    permanent = False  # Does the item stay after death
    limit = 0
    category = default_item_category

    @property
    def sell_value(self):
        """Getter for item's sell value.

        Returns:
            Item's sell value
        """

        return int(self.cost * item_sell_value_multiplier)
