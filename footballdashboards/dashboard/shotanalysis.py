import pandas as pd
from typing import Dict
from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards._types._data_accessor import _DataAccessor
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer.scatterutils import scatter_football

class ShotLollipopDashboard(Dashboard):

    
    def _required_data_columns(self) -> Dict[str, str]:
        return {
            'squad':'Team Name',

        }
    
    @property
    def datasource_name(self) -> str:
        return 'ShotData'
    
    def _setup_plot(self) -> PlotReturnType:
        fig = Figure(figsize=(10,6), facecolor=self.facecolor)
        ax = fig.add_subplot(1, 1, 1)
        ax.hlines(0, 0, 90, color='black', linewidth=1,zorder=10)
        ax.set_facecolor(self.facecolor)
        return fig, ax
        
    def _apply_minute_function(self, data: pd.DataFrame) -> pd.DataFrame:
        data['minute_int'] = data['minute'].astype(str).apply(lambda x: int(x.split('+')[0])+int(x.split('+')[1]) if len(x.split('+'))>1 else int(x))
        return data

    def _plot_lollipops(self, ax: Axes, data: pd.DataFrame):
        data = data.copy()
        data['xg']= data['xg'] * (data['home']-0.5)*2
        op_goals = data[(data['outcome']=='Goal') &(data['is_open_play']==1)]
        op_shots = data[(data['outcome']!='Goal') &(data['is_open_play']==1)]
        deadball_goals = data[(data['outcome']=='Goal') &(data['is_open_play']==0)]
        deadball_shots = data[(data['outcome']!='Goal') &(data['is_open_play']==0)]

        
        ax.vlines(op_goals['minute_int'], 0, op_goals['xg'], color='green', linewidth=2)
        ax.vlines(op_shots['minute_int'], 0, op_shots['xg'], color='grey', linewidth=2)
        ax.vlines(deadball_goals['minute_int'], 0, deadball_goals['xg'], color='green', linewidth=2, linestyle='dashed')
        ax.vlines(deadball_shots['minute_int'], 0, deadball_shots['xg'], color='grey', linewidth=2, linestyle='dashed')
        ax.scatter(op_goals['minute_int'], op_goals['xg'], s=50, c='green', ec='black', lw=0.5, zorder=2)
        ax.scatter(op_shots['minute_int'], op_shots['xg'], s=50, c='grey', ec='black', lw=0.5, zorder=2)
        ax.scatter(deadball_goals['minute_int'], deadball_goals['xg'], s=50, c='green', ec='black', lw=0.5, zorder=2, linestyle='dashed')
        ax.scatter(deadball_shots['minute_int'], deadball_shots['xg'], s=50, c='grey', ec='black', lw=0.5, zorder=2, linestyle='dashed')
    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        
        data = self._apply_minute_function(data)
        fig, ax = self._setup_plot()
        self._plot_lollipops(ax, data)
        return fig, ax
    

class EventsShotLollipopDashboard(ShotLollipopDashboard):

    @property
    def datasource_name(self) -> str:
        return 'ShotDataEvents' 