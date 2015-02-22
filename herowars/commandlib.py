# ======================================================================
# >> IMPORTS
# ======================================================================

# Python 3
from collections import defaultdict

# Source.Python
from messages import SayText2

from listeners.tick import tick_delays


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'burn', 'freeze', 'noclip', 'jetpack',
    'boost_velocity',
    'set_property'
)


# ======================================================================
# >> GLOBALS
# ======================================================================

_effects = {key: defaultdict(set) for key in __all__[:4]}


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
        tick_delays.delay(duration, shiftprop, player, prop, -shift)()


def burn(player, duration):
    """Sets a player on fire."""

    player.call_input('Ignite')
    delay = tick_delays.delay(duration, _unburn)
    delay.args = (player, delay)
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
    delay = tick_delays.delay(duration, _unfreeze)
    delay.args = (player, delay)
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
    delay = tick_delays.delay(duration, _unnoclip)
    delay.args = (player, delay)
    _effects['noclip'][player.index].add(delay)


def _unnoclip(player, delay):
    """Unnoclips a player."""

    _effects['noclip'][player.index].discard(delay)
    if not _effects['noclip'][player.index]:
        player.noclip = False


def jetpack(player, duration):
    """Jetpacks a player."""

    player.jetpack = True
    delay = tick_delays.delay(duration, _unjetpack)
    delay.args = (player, delay)
    _effects['jetpack'][player.index].add(delay)


def _unjetpack(player, delay):
    """Unjetpacks a player."""

    _effects['jetpack'][player.index].discard(delay)
    if not _effects['jetpack'][player.index]:
        player.jetpack = False


def boost_velocity(player, x_mul=1.0, y_mul=1.0, z_mul=1.0):
    """Boosts player's velocity."""

    base_str = 'CBasePlayer.localdata.m_vecBaseVelocity'
    new_values = (
        player.get_property_float('{0}[0]'.format(base_str)) * x_mul,
        player.get_property_float('{0}[1]'.format(base_str)) * y_mul,
        player.get_property_float('{0}[2]'.format(base_str)) * z_mul
    )
    player.set_property_float(
        base_str, ','.join(str(value) for value in new_values)
    )
