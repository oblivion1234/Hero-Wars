# ======================================================================
# >> IMPORTS
# ======================================================================

# Python
from random import randint

from functools import wraps, WRAPPER_ASSIGNMENTS

# Source.Python
from listeners.tick.repeat import TickRepeat

from messages import SayText2


# ======================================================================
# >> CLASSES
# ======================================================================

class classproperty(object):
    """Decorator to create a property for a class.

    http://stackoverflow.com/a/3203659/2505645
    """

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def find_element(iterable, attr_name, attr_value):
    """Finds an element from an iterable by an attribute.

    Takes an iterable and looks for the first element that has
    an attribute with matching name and value to the provided arguments.

    Args:
        iterable: Iterable where to seek for the element
        attr_name: Name of the attribute to compare to
        attr_value: Desired value of the attribute

    Returns:
        First element with matching attribute
    """

    for x in iterable:
        if getattr(x, attr_name) == attr_value:
            return x


def find_elements(iterable, attr_name, attr_value):
    """Finds all elements from an iterable by an attribute.

    Takes an iterable and looks for all the elements that have
    an attribute with matching name and value to the provided arguments.

    Args:
        iterable: Iterable where to seek for the elements
        attr_name: Name of the attribute to compare to
        attr_value: Desired value of the attribute 

    Returns:
        A generator of elements with matching attribute
    """

    return (x for x in iterable if getattr(x, attr_name) == attr_value)


def get_subclasses(cls):
    """Returns a set of class' subclasses."""

    subclasses = set()
    for subcls in cls.__subclasses__():
        subclasses.add(subcls)
        subclasses.update(get_subclasses(subcls))
    return subclasses


def shiftattr(obj, attr_name, shift):
    """Shifts an attribute's value.

    Similar to getattr() and setattr(), shiftattr() shifts
    (increments or decrements) attributes value by the given shift.

    Args:
        obj: Object whose attribute to shift
        attr_name: Name of the attribute to shift
        shift: Shift to make, can be negative
    """

    setattr(obj, attr_name, getattr(obj, attr_name) + shift)


def chance(percentage):
    """Decorates a function to be executed at a static chance.

    Takes a percentage as a parameter, returns an other decorator
    that wraps the original function so that it only gets executed
    at a chance of the given percentage.

    Args:
        percentage: Chance of execution in percentage (0-100)

    Returns:
        New function that doesn't always get executed when called
    """

    return chancef(lambda self, **eargs: percentage)


def chancef(fn):
    """Decorates a function to be executed at a dynamic chance.

    Takes a percentage as a parameter, returns an other decorator
    that wraps the original function so that it only gets executed
    at a chance of the percentage calculated by given function.

    Args:
        fn: Function to determine the chance of the method's execution

    Returns:
        New function that doesn't always get executed when called
    """

    # Create a decorator using the function provided
    def method_decorator(method):

        # Create a wrapper method
        @wraps(method, assigned=WRAPPER_ASSIGNMENTS+('__dict__',), updated=())
        def method_wrapper(self, **eargs):

            # If the randomization passes
            if randint(0, 100) <= fn(self, **eargs):

                # Call the method
                return method(self, **eargs)

            # Else exit with code 2
            return 2

        # Return the wrapper
        return method_wrapper

    # Return the decorator
    return method_decorator


def cooldown(time, message=None):
    """Decorates a function to have a static cooldown.

    Decorator function for easily adding cooldown as
    a static time (integer) into skill's methods.

    Args:
        time: Cooldown of the method
        message: Optional message sent if there's still cooldown left

    Returns:
        Decorated method with a static cooldown
    """

    return cooldownf(lambda self, **eargs: time, message)


def cooldownf(fn, message=None):
    """Decorates a method to have a dynamic cooldown.

    Decorator function for easily adding cooldown as a dynamic time
    (function) into skill's methods. The function gets called when the
    cooldown is needed, and the skill is passed to the function.

    Args:
        fn: Function to determine the cooldown of the method
        message: Optional message sent if there's still cooldown left
    
    Returns:
        Decorated method with a dynamic cooldown
    """

    # Create a decorator using the function and message provided
    def method_decorator(method):

        # Create a wrapper method
        @wraps(method, assigned=WRAPPER_ASSIGNMENTS+('__dict__',), updated=())
        def method_wrapper(self, **eargs):

            # If the method's cooldown is over
            if method_wrapper.cooldown.remaining <= 0:

                # Restart the cooldown
                method_wrapper.cooldown.start(1, fn(self, **eargs))

                # And call the function
                return method(self, **eargs)

            # If there was cooldown remaining and a message is provided
            if message:

                # Format the provided message
                formatted_message = message.format(
                    name=self.name,
                    cd=method_wrapper.cooldown.remaining,
                    max_cd=method_wrapper.cooldown.limit
                )

                # And send it to the player
                SayText2(message=formatted_message).send(eargs['player'].index)

                # And exit with code 3
                return 3

        # Create the cooldown object for the wrapper
        method_wrapper.cooldown = TickRepeat(lambda: None)

        # And return the wrapper
        return method_wrapper

    # Return the decorator
    return method_decorator
