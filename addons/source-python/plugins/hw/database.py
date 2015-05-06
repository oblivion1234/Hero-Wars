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

database = None


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def setup():
    """Creates the Hero-Wwars tables into the database."""

    global database
    database = sqlite3.connect(database_path)
    with closing(database.cursor()) as cursor:
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            steamid TEXT PRIMARY KEY,
            gold INTEGER,
            hero_cls_id TEXT
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS heroes (
            steamid TEXT,
            cls_id TEXT,
            level INTEGER,
            exp INTEGER,
            PRIMARY KEY (steamid, cls_id)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS skills (
            steamid TEXT,
            hero_cls_id TEXT,
            cls_id TEXT,
            level INTEGER,
            PRIMARY KEY (steamid, hero_cls_id, cls_id)
        )""")


def save_user_data(user):
    """Saves user's data into the database.

    Args:
        user: User whose data to save
    """

    with closing(database.cursor()) as cursor:
        cursor.execute(
            "INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
            (user.steamid, user.gold, user.hero.cls_id)
        )
    save_hero_data(user.steamid, user.hero)  # Calls database.commit()


def save_hero_data(steamid, hero):
    """Saves hero's data into the database.

    Args:
        steamid: Steamid of the hero's owner
        hero: Hero whose data to save
    """

    with closing(database.cursor()) as cursor:
        cursor.execute(
            "INSERT OR REPLACE INTO heroes VALUES (?, ?, ?, ?)",
            (steamid, hero.cls_id, hero.level, hero.exp)
        )
        for skill in hero.skills:
            cursor.execute(
                "INSERT OR REPLACE INTO skills VALUES (?, ?, ?, ?)",
                (steamid, hero.cls_id, skill.cls_id, skill.level)
            )
    database.commit()


def load_user_data(user):
    """Loads user's data from the database.

    Args:
        user: user whose data to load
    """

    with closing(database.cursor()) as cursor:
        cursor.execute(
            "SELECT gold, hero_cls_id FROM users WHERE steamid=?",
            (user.steamid, )
        )
        gold, current_hero_cls_id = cursor.fetchone() or (0, None)
        user.gold = gold

        # Load user's heroes
        cursor.execute(
            "SELECT cls_id, level, exp FROM heroes WHERE steamid=?",
            (user.steamid, )
        )
        heroes = cursor.fetchall()

    # Load heroes data
    hero_classes = Hero.get_subclasses()
    for cls_id, level, exp in heroes:
        hero_cls = find_element(hero_classes, 'cls_id', cls_id)
        if hero_cls:
            hero = hero_cls(level, exp)
            load_hero_data(user.steamid, hero)
            user.heroes.append(hero)
            if cls_id == current_hero_cls_id:
                user.hero = hero


def load_hero_data(steamid, hero):
    """Loads hero's data from the database.

    Args:
        steamid: Steamid of the hero's owner
        hero: Hero whose data to load
    """

    with closing(database.cursor()) as cursor:
        cursor.execute(
            "SELECT level, exp FROM heroes WHERE steamid=? AND cls_id=?",
            (steamid, hero.cls_id)
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
                "WHERE steamid=? AND hero_cls_id=? AND cls_id=?",
                (steamid, hero.cls_id, skill.cls_id)
            )
            data = cursor.fetchone()
            if data:
                skill.level = data[0]
