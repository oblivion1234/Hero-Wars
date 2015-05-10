# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.entities import Hero

from hw.tools import find_element

from hw.configs import database_path

# Python
import sqlite3
from contextlib import closing


# ======================================================================
# >> GLOBALS
# ======================================================================

connection = None


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def setup():
    """Creates the Hero-Wwars tables into the database."""

    global connection
    connection = sqlite3.connect(database_path)
    with closing(connection.cursor()) as cursor:
        cursor.execute("""CREATE TABLE IF NOT EXISTS players (
            steamid TEXT PRIMARY KEY,
            gold INTEGER,
            hero_cid TEXT
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS heroes (
            steamid TEXT,
            cid TEXT,
            level INTEGER,
            exp INTEGER,
            PRIMARY KEY (steamid, cid)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS skills (
            steamid TEXT,
            hero_cid TEXT,
            cid TEXT,
            level INTEGER,
            PRIMARY KEY (steamid, hero_cid, cid)
        )""")


def save_player_data(player):
    """Saves player's data into the database.

    Args:
        player: player whose data to save
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT OR REPLACE INTO players VALUES (?, ?, ?)",
            (player.steamid, player.gold, player.hero.cid)
        )
    save_hero_data(player.steamid, player.hero)  # Calls database.commit()


def save_hero_data(steamid, hero):
    """Saves hero's data into the database.

    Args:
        steamid: Steamid of the hero's owner
        hero: Hero whose data to save
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT OR REPLACE INTO heroes VALUES (?, ?, ?, ?)",
            (steamid, hero.cid, hero.level, hero.exp)
        )
        for skill in hero.skills:
            cursor.execute(
                "INSERT OR REPLACE INTO skills VALUES (?, ?, ?, ?)",
                (steamid, hero.cid, skill.cid, skill.level)
            )
    connection.commit()


def load_player_data(player):
    """Loads player's data from the database.

    Args:
        player: player whose data to load
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT gold, hero_cid FROM players WHERE steamid=?",
            (player.steamid, )
        )
        gold, current_hero_cid = cursor.fetchone() or (0, None)
        player.gold = gold

        # Load player's heroes
        cursor.execute(
            "SELECT cid, level, exp FROM heroes WHERE steamid=?",
            (player.steamid, )
        )
        heroes = cursor.fetchall()

    # Load heroes data
    hero_classes = Hero.get_subclasses()
    for cid, level, exp in heroes:
        hero_cls = find_element(hero_classes, 'cid', cid)
        if hero_cls:
            hero = hero_cls(level, exp)
            load_hero_data(player.steamid, hero)
            player.heroes.append(hero)
            if cid == current_hero_cid:
                player.hero = hero


def load_hero_data(steamid, hero):
    """Loads hero's data from the database.

    Args:
        steamid: Steamid of the hero's owner
        hero: Hero whose data to load
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT level, exp FROM heroes WHERE steamid=? AND cid=?",
            (steamid, hero.cid)
        )
        level, exp = cursor.fetchone() or (0, 0)
        if level > hero.max_level:
            hero.level = hero.max._level
        else:
            hero.level = level
        hero.exp = exp

        # Load hero's skills
        for skill in hero.skills:
            cursor.execute(
                "SELECT level FROM skills "
                "WHERE steamid=? AND hero_cid=? AND cid=?",
                (steamid, hero.cid, skill.cid)
            )
            data = cursor.fetchone()
            if data:
                skill.level = data[0]
