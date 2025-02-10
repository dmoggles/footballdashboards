import pandas as pd
from typing import List, Dict, Any, Tuple
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer.pitch import Pitch
from footmav.data_definitions.whoscored.constants import EventType as EventTypeOld
from footmav.utils import whoscored_funcs as WF

def fwd_passes(data:pd.DataFrame, _)->pd.DataFrame:
    return data[data['endX']>=data['x']]


def __pass_type_mask(data:pd.DataFrame, pass_type:int)->pd.Series:
    data=data.copy()    
    data["event_type"] = EventTypeOld.Pass
    data["passtypes"] = WF.classify_passes(data)
    if pass_type == 0:
        return data['passtypes']==0
    return data['passtypes'].apply(lambda x: x&pass_type).astype(bool)

def progressive_passes(data:pd.DataFrame, _)->pd.DataFrame:
    return data[__pass_type_mask(data, 2)]

def regular_passes(data:pd.DataFrame, _)->pd.DataFrame:
    return data[__pass_type_mask(data, 0)]

def cutback_passes(data:pd.DataFrame, _)->pd.DataFrame:
    return data[__pass_type_mask(data, 1)]

def opponents(data:pd.DataFrame, teams:List[str])->pd.DataFrame:
    return data[data['team'].isin(teams)]


def applied_filters_text(
   config: Dict[str, Any], 
   data: pd.DataFrame, 
   figure: Figure, 
   ax: Axes, 
   pitch: Pitch, 
   filters: List[Tuple[str, Any]]
):     
    
    filter_str = ""
    for f_name, params in filters:
        if params:
            filter_str += f"{f_name}: {params} | "
        else:
            filter_str += f"{f_name} | "
    if 'opponents' in config:
        filter_str += f"Opponents: {','.join(config['opponents'])} | "
    filter_str = filter_str[:-3] if filter_str else filter_str
    if not filter_str:
        return
    filter_str = "Filters applied: " + filter_str
    #if text is longer than 100 characters, split it into two lines on a space
    if len(filter_str) > 100:
        split_index = filter_str[:100].rfind(" ")
        filter_str = filter_str[:split_index] + "\n" + filter_str[split_index + 1:]
    ax.text(
        0.0, 
        1.0, 
        filter_str,
        fontsize=9, 
        ha='left',
        va='top',
        color='grey'
    )





