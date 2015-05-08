# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.entities import Hero, Skill

from hw.tools import chance, chancef
from hw.tools import cooldown, cooldownf

from hw.player import Player

# Source.Python
from filters.players import PlayerIter


# ======================================================================
# >> Test Hero #1
# ======================================================================

class TestHero1(Hero):
    name = 'Test Hero #1'
    description = 'First testing hero, limited alpha release edition.'
    authors = ('Mahi', 'Kamiqawa')


@TestHero1.passive
class HealthSpeed(Skill):
    name = 'Speed&Health Passive'
    description = 'Gain speed on spawn and health on attack.'

    def player_spawn(self, player, **eargs):
        player.set_property_float('m_flLaggedMovementValue', 1.3)
    @chance(33)
    def player_attack(self, attacker, defender, **eargs):
        attacker.health += 5


@TestHero1.skill
class Damage(Skill):
    name = 'Damage'
    description = 'Deal 2x damage with attacks.'
    max_level = 1

    def player_attack(self, attacker, defender, **eargs):
        pass
        # Not implemented attacker.damage(defender.index, eargs['damage'])


@TestHero1.skill
class Ignite(Skill):
    name = 'Ignite'
    description = 'Ignite all enemies for 3-4 seconds when you spawn.'
    max_level = 2

    def player_spawn(self, player, **eargs):
        target_team = player.team == 2 and 'ct' or 't'
        for index in PlayerIter(is_filters=('alive', target_team)):
            target = Player(index)
            target.burn(2 + self.level)


@TestHero1.skill
class Noclip(Skill):
    name = 'Noclip'
    description = 'Ultimate: Get noclip for 2-4 seconds'
    max_level = 3
    cost = 2
    required_level = 5

    @cooldownf(lambda self, **eargs: 20 - self.level * 2)
    def player_ultimate(self, player, **eargs):
        duration = 1 + self.level
        player.noclip(duration)


# ======================================================================
# >> Test Hero #1
# ======================================================================

class TestHero2(Hero):
    name = 'Test Hero #2'


@TestHero2.skill
class Gravity(Skill):
    name = 'Gravity'

    def player_spawn(self, player, **eargs):
        player.gravity -= 0.1
