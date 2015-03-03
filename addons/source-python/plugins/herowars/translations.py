# ======================================================================
# >> IMPORTS
# ======================================================================

# Source.Python
from translations.strings import LangStrings

from messages import SayText2


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'lang_strings_dict',
    'get_translation',
    'get_messages'
)


# ======================================================================
# >> GLOBALS
# ======================================================================

lang_strings_dict = {
    'exp_messages': LangStrings('herowars/exp_messages'),
    'gold_messages': LangStrings('herowars/gold_messages'),
    'menu_messages': LangStrings('herowars/menu_messages'),
    'menu_options': LangStrings('herowars/menu_options'),
    'other_messages': LangStrings('herowars/other_messages')
}


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def get_translation(infile, key):
    """Gets a translation from a file based on the translation key.

    Args:
        infile: File to look for the translation for
        key: Key used to find the correct translation from the file

    Returns:
        The correct translation
    """

    return lang_strings_dict[infile][key]


def get_messages(infile):
    """Gets a dict of SayText2 messages from a LangStrings object.

    Args:
        infile: File to look for the messages for

    Returns:
        A dict of SayText2 messages
    """

    return {
        key: SayText2(message=lang_strings_dict[infile][key])
        for key in lang_strings_dict[infile]
    }
