from dataclasses import dataclass
from footmav.data_definitions.whoscored.constants import EventType
from footmav.utils import whoscored_funcs as WF



@dataclass
class EventDefinition:
    label: str
    event_type: EventType
    outcome_type: int
    marker: str
    color: str = None
    edge_color: str = None
    size_mult: float = 1

def get_touch_events(data):
    touch_events = [
        2,
        3,
        7,
        8,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        41,
        42,
        44,
        45,
        49,
        50,
        54,
        61,
        74,
    ]
    touch_events = [EventType(e) for e in touch_events]

    total_touches = data.loc[
        (data["event_type"].isin(touch_events))
        | ((data["event_type"] == EventType.Foul) & (data["outcomeType"] == 1))
        | (
            (
                (data["event_type"] == EventType.Pass)
                | (data["event_type"] == EventType.OffsidePass)
            )
            & ~(
                WF.col_has_qualifier(data, qualifier_code=6)
                | WF.col_has_qualifier(data, display_name="ThrowIn")
            )
        )  # excludes corners and throw-ins
    ].copy()
    return total_touches

defensive_events = [
    EventDefinition("Recovery", EventType.BallRecovery, 1, "o"),
    EventDefinition("Interception", EventType.Interception, 1, "X", size_mult=1.5),
    EventDefinition("Interception", EventType.BlockedPass, 1, "X", size_mult=1.5),
    EventDefinition(
        "Tackle Won (won ball)", EventType.Tackle, 1, "D", "green", "lightgreen"
    ),
    EventDefinition(
        "Tackle Won (other team kept ball)",
        EventType.Tackle,
        0,
        "D",
        "olive",
        "lightgreen",
    ),
    EventDefinition("Tackle Lost", EventType.Challenge, 0, "D", "red", "orangered"),
    EventDefinition(
        "Foul",
        EventType.Foul,
        0,
        "P",
        size_mult=1.5,
        color="red",
        edge_color="orangered",
    ),
    EventDefinition("Clearance", EventType.Clearance, 1, "*", size_mult=2),
    EventDefinition("Header Won", EventType.Aerial, 1, "^", "green", "lightgreen", 1.5),
    EventDefinition("Header Lost", EventType.Aerial, 0, "^", "red", "orangered", 1.5),
    EventDefinition("Block", EventType.Save, 1, "s", size_mult=1),
]
