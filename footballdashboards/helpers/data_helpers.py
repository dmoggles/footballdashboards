from footmav.data_definitions.whoscored.constants import EventType
from footballdashboards.helpers import formatters


def lineup_card(data):
    lineup_card = (
        data[["shirt_number", "player_name", "position"]]
        .groupby(["shirt_number"])
        .first()
        .reset_index()
    )
    lineup_card["position"] = lineup_card["position"].apply(
        lambda x: x if x not in ["RCDM", "LCDM", "RCAM", "LCAM"] else x.replace("C", "")
    )
    lineup_card = lineup_card.loc[lineup_card["shirt_number"] != -1]
    subs = (
        data.loc[data["event_type"] == EventType.SubstitutionOn][
            ["player_name", "minute", "second"]
        ]
        .set_index("player_name")
        .to_dict()["minute"]
    )
    subs_off = (
        data.loc[data["event_type"] == EventType.SubstitutionOff][
            ["player_name", "minute", "second"]
        ]
        .set_index("player_name")
        .to_dict()["minute"]
    )
    lineup_card["on"] = lineup_card["player_name"].map(subs).fillna(0).astype(int)
    lineup_card["is_position"] = lineup_card["position"].apply(lambda x: 1 if x != "GK" else 0)
    lineup_card["off"] = lineup_card["player_name"].map(subs_off).fillna(0).astype(int).astype(str)
    lineup_card["off"] = lineup_card["off"].apply(lambda x: x if x != "0" else "--")
    lineup_card["player_name"] = lineup_card["player_name"].apply(formatters.smart_name_formatter)
    lineup_card = lineup_card.sort_values(["is_position", "on", "shirt_number"])
    lineup_card = lineup_card.rename(
        columns={
            "player_name": "Player",
            "position": "Pos",
            "shirt_number": "No.",
            "on": "On",
            "off": "Off",
        }
    )
    starters = lineup_card.loc[lineup_card["On"] == 0]
    subs = lineup_card.loc[lineup_card["On"] != 0]
    subs = subs.sort_values("On")
    subs["On"] = subs["On"].astype(str)
    return starters, subs


def extract_names_sorted_by_position(data, exclude_positions=None):
    exclude_positions = exclude_positions or []
    data = data.loc[data["event_type"] != EventType.Carry]
    subs = data.loc[data["event_type"] == EventType.SubstitutionOn, "player_name"]

    list_of_names = (
        data.loc[
            (~data["player_name"].isna())
            & (data["isTouch"] == 1)
            & (~data["player_name"].isin(subs))
            & (~data["position"].isin(exclude_positions))
        ]
        .groupby("player_name")
        .first()
        .reset_index()
        .sort_values("sort_id")["player_name"]
        .tolist()
        + subs.tolist()
    )
    if len(list_of_names) > 15:
        list_of_names = list_of_names[:16]
    return list_of_names
