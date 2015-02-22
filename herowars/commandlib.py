# ======================================================================
# >> IMPORTS
# ======================================================================

# Python 3
from collections import defaultdict

# Source.Python
from messages import SayText2

from listeners.tick import tick_delays

from filters.players import PlayerIter

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


def players_near_coord(vector, radius, player_filter='alive'):
    """Gets list of players near given vector-coordinate

    Returns a generator of playerentities that are within given radius
    from given vector (x,y,z). Uses Source.Python's default
    player filter syntax as optional player_filter setting
    """

    return (player for player in PlayerInter(player_filter) if vector.get_distance(player.location) <= radius)

def player_nearest_coord(vector, max_radius=0, player_filter='alive'):
    """Gets the player nearest to the given point

    Returns a playerentity with smallest distance to the
    given vector (x,y,z) location. Returns None if no 
    players were found. Max radius limits the search into
    a given range. Player filter is Source.Python's default
    method for filtering objects with PlayerIter.
    """

    player_distances = {player:vector.get_distance(player.location) for player in PlayerInter(player_filter)} or {None:0}
    nearest_player = sorted(player_distances.items(), key=lambda x:x[1])[0]
    return nearest_player[0] if nearest_player[1] <= max_radius else None

def push(player, vector):
    """Pushes player along given vector

    Pushes player along given vector (x,y,z).
    """

    player.set_property_string('CBasePlayer.localdata.m_vecBaseVelocity', ','.join(vector))

def push_to(player, vector, force):
    """Pushes player towards given point

    Pushes player towards given vector point (x,y,z)
    with given force.
    """

    push(player, (vector-player.location)*force)
