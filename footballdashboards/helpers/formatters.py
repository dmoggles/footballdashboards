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


def smartest_name_formatter_yet(name, length_limit=20):
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

    tokens = [t.capitalize() if t not in particles else t for t in tokens]
    if tokens[-1].startswith("Mc"):
        tokens[-1] = tokens[-1][:2] + tokens[-1][2].upper() + tokens[-1][3:]

    name = " ".join(tokens)
    if len(name) > length_limit and set(particles).intersection(set(tokens)):
        particle_index = [i for i, x in enumerate(tokens) if x in particles][0]
        name = (
            f"{tokens[0][0].upper()}. "
            + tokens[particle_index]
            + " "
            + " ".join(tokens[particle_index + 1 :]).title()
        )
    if len(name) > length_limit and len(name.split(" ")) >= 4:
        tokens = name.split(" ")
        name = f"{tokens[0].title()} {tokens[-1].title()}"
    if (
        len(name) > length_limit
        and len(name.split(" ")) == 3
        and name.split(" ")[1] not in particles
    ):
        tokens = name.split(" ")
        name = f"{tokens[0].capitalize()} {tokens[1][0].upper()}. {tokens[-1].capitalize()}"

    if (
        len(name) > length_limit
        and len(name.split(" ")) == 3
        and name.split(" ")[1] not in particles
    ):
        tokens = name.split(" ")
        name = f"{tokens[0].capitalize()} {tokens[-1].capitalize()}"

    if len(name) > length_limit:
        name = length_based_name_formatter(name, length_limit=length_limit)
    tokens = name.split(" ")
    tokens = [t if not t.startswith("Mc") else t[:2] + t[2].upper() + t[3:] for t in tokens]
    name = " ".join(tokens)
    return name


def simplified_opta_position(position: str):
    if position in ["CB", "RCB", "LCB"]:
        return "CB"
    if position in ["LB", "RB", "LWB", "RWB"]:
        return "FB"
    if position in ["CDM", "LCDM", "RCDM"]:
        return "DM"
    if position in ["CM", "LCM", "RCM"]:
        return "CM"
    if position in ["CAM", "LCAM", "RCAM", "SS"]:
        return "AM"
    if position in ["LWF", "RWF", "LM", "RM"]:
        return "W"
    if position in ["CF", "LF", "RF"]:
        return "ST"
    return position
