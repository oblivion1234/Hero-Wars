# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.entities import Hero, Skill

from hw.tools import chance, chancef
from hw.tools import cooldown, cooldownf

from hw.players import Player

# Xtend
import xtend.effects

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
    beam_ents = xtend.effects.BeamEnts(
        model='sprites/lgtning.vmt',
        start_width=2, end_width=1, speed=1, red=255, green=255, life=2
    )

    def player_spawn(self, player, **eargs):
        player.set_property_float('m_flLaggedMovementValue', 1.3)
        player.message('+30% speed from Passive.')

    @chance(33)
    def player_attack(self, attacker, defender, **eargs):
        attacker.health += 5
        self.beam_ents(
            start_ent_index=attacker.index,
            end_ent_index=defender.index
        )
        attacker.message('+5 health from Passive.')


@TestHero1.skill
class Damage(Skill):
    name = 'Damage'
    description = 'Deal 2x damage with attacks.'
    max_level = 1

    def player_attack(self, attacker, defender, **eargs):
        # Not implemented attacker.damage(defender.index, eargs['damage'])
        attacker.message('You dealt 2x damage!')


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
            target.message('You were burned!')
        player.message('You burned your enemies!')


@TestHero1.skill
class Noclip(Skill):
    name = 'Noclip'
    description = 'Ultimate: Get noclip for 2-4 seconds'
    max_level = 3
    cost = 2
    required_level = 5
    beam_follow = xtend.effects.BeamFollow(
        blue=255, start_width=10, model='sprites/lgtning.vmt'
    )

    @cooldownf(lambda self, **eargs: 20 - self.level * 2)
    def player_ultimate(self, player, **eargs):
        duration = 1 + self.level
        player.noclip(duration)
        self.beam_follow(ent_index=player.index)
        player.message('You got noclip for {0} seconds!'.format(duration))
