import pandas as pd
from footballmodels.opta.event_type import EventType


def calc_minutes(data):
    max_minutes = data.groupby(["matchId", "period"])["max_minute"].max()
    sub_ons = data[data["event_type"] == EventType.SubstitutionOn].rename(
        columns={"minute": "sub_on_minute"}
    )
    sub_offs = data[data["event_type"] == EventType.SubstitutionOff].rename(
        columns={"minute": "sub_off_minute"}
    )
    combined = pd.merge(
        max_minutes,
        sub_ons[["matchId", "period", "sub_on_minute"]],
        on=["matchId", "period"],
        how="left",
    ).fillna(0)
    combined = pd.merge(
        combined,
        sub_offs[["matchId", "period", "sub_off_minute"]],
        on=["matchId", "period"],
        how="left",
    ).fillna(10000)
    combined["min_minute"] = combined["period"].apply(lambda x: (x - 1) * 45)
    combined["start_minute"] = combined[["sub_on_minute", "min_minute"]].max(axis=1)
    combined["end_minute"] = combined[["sub_off_minute", "max_minute"]].min(axis=1)
    combined["minutes"] = combined["end_minute"] - combined["start_minute"]
    return combined["minutes"].sum()
