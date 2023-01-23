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
