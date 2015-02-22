# ======================================================================
# >> IMPORTS
# ======================================================================

# Python 3
from collections import defaultdict

# Source.Python
from messages import SayText2


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'burn', 'freeze', 'noclip', 'set_property'
)


# ======================================================================
# >> GLOBALS
# ======================================================================

_effects = {key: defaultdict(set) for key in __all__ if key != 'set_property'}


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def tell(player, message):
    """Sends a message to a player through the chat."""

    SayText2(message=message).send(player.index)


def shiftprop(player, prop, shift, duration=0):
    """Shifts player's property's value for a duration.

    Args:
        player: Player whose property to shift
        prop: Name of the property to shift
        shift: Shift to make, can be negative
        duration: Duration until the effect is reverted, 0 for infinite
    """

    setattr(player, prop, getattr(player, prop) + shift)
    if duration:
        Delay(duration, shiftprop, player, prop, -shift)()


def burn(player, duration):
    """Sets a player on fire."""

    player.call_input('Ignite')
    delay, delay.args = Delay(duration, _unburn), (player, delay)
    _effects['burn'][player.index].add(delay)
    delay()


def _unburn(player, delay):
    """Extinguishes a player."""

    _effects['burn'][player.index].discard(delay)
    if not _effects['burn'][player.index]:
        player.call_input('IgniteLifetime', 0)


def freeze(player, duration):
    """Freezes a player."""

    player.freeze = True
    delay, delay.args = Delay(duration, _unfreeze), (player, delay)
    _effects['freeze'][player.index].add(delay)
    delay()


def _unfreeze(player, delay):
    """Unfreezes a player."""

    _effects['freeze'][player.index].discard(delay)
    if not _effects['freeze'][player.index]:
        player.freeze = False


def noclip(player, duration):
    """Noclips a player."""

    player.noclip = True
    delay, delay.args = Delay(duration, _unnoclip), (player, delay)
    _effects['noclip'][player.index].add(delay)
    delay()


def _unnoclip(player, delay):
    """Unnoclips a player."""

    _effects['noclip'][player.index].discard(delay)
    if not _effects['noclip'][player.index]:
        player.noclip = False
