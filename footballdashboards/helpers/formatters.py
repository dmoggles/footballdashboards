"""
Various text formatters for displaying data
"""


def player_name_first_initial_surname_formatter(player_name: str) -> str:
    """
    Formats player name to first initial and surname

    Args:
        player_name (str): player name

    Returns:
        str: formatted player name

    """
    if player_name is None:
        return None
    if len(player_name.split()) == 1:
        return player_name.title()
    return f"{player_name.split()[0][0]} {player_name.split()[-1]}".title()


def full_name_formatter(player_name: str) -> str:
    """
    Formats the full player name

    Args:
        player_name (str): player name

    Returns:
        str: formatted player name
    """

    if player_name is None:
        return None
    return player_name.title()


def add_ordinal_suffix(day):
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def format_date(date):
    date_str = date.strftime("%A, %B ") + add_ordinal_suffix(date.day) + date.strftime(", %Y")

    return date_str


def smart_name_formatter(name):
    particles = [
        "de",
        "von",
        "van",
        "del",
        "della",
        "di",
        "du",
        "le",
        "la",
        "lo",
        "da",
        "das",
        "der",
        "den",
        "ten",
        "ter",
        "te",
        "af",
    ]
    tokens = name.split(" ")
    if len(tokens) == 1:
        return name.title()
    elif len(tokens) == 2:
        return f"{tokens[0][0].upper()}. {tokens[1].title()}"
    else:
        return "".join([t[0].upper() if t not in particles else t[0].lower() for t in tokens])


def length_based_name_formatter(name, length_limit=20):
    if len(name) > length_limit:
        return smart_name_formatter(name)
    return full_name_formatter(name)
