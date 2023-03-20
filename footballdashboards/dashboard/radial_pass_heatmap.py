from typing import Dict
import numpy as np
import pandas as pd
from footballdashboards.dashboard.dashboard import Dashboard
from footmav.utils.mplsoccer.standardizer import Standardizer
from footmav.utils import whoscored_funcs as WF
from footballdashboards._types._dashboard_fields import FloatListField, PositiveNumField, ColorMapField, ColorField, FigSizeField
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.helpers.colours import is_light_or_dark, ColourShade
from matplotlib.cm import get_cmap
from matplotlib.figure import Figure
from matplotlib.axes import Axes

class RadialPassHeatmapDashboard(Dashboard):

    length_bin_edges = FloatListField("edges of the three length bins",  [15, 30])
    num_angle_bins = PositiveNumField("number of slices on the radar to group passes into", 8)
    main_cmap = ColorMapField('colormap for the main heatmap', 'Blues')
    main_cmap_max_value = PositiveNumField('maximum value for the highest main heatmap saturation color', 0.2)
    dark_text_color = ColorField('Dark text colour for light background', '#000000')
    light_text_color = ColorField('Light text colour for dark background', '#FFFFFF')
    fig_size = FigSizeField('Figure size', (6, 7))
    def datasource_name(self) -> str:
        return 'RadialPassHeatmap'
    
    def _required_data_columns(self) -> Dict[str, str]:
        return {
         
        'x':'x location of the start of the pass',
        'y':'y location of the start of the pass',
        'endX':'x location of the end of the pass',
        'endY':'y location of the end of the pass',
        'outcome':'outcome of the pass (1 for success, 0 for failure)',
        #"Player" : "Player Name",
        #"Team" : "Team Name",
        #"Season": "Season",
        #"Competition": "Competition Name",
        #"All Leagues": "All leagues in the comparison",
        #"Decorated League": "Decorated League for display purposes",
        #"Decorated Team": "Decorated Team for display purposes",

     }
    
    @staticmethod
    def _degrees(x0:float, y0:float, x1:float, y1:float)->float:
        standardizer = Standardizer(pitch_from="opta", pitch_to="uefa")
        x0, y0 = standardizer.transform(np.array([x0]), np.array([y0]))
        x1, y1 = standardizer.transform(np.array([x1]), np.array([y1]))
        return (np.arctan2(y1-y0, x1-x0) * 180 / np.pi)[0]
    
    
    def pass_aggregator(self, data:pd.DataFrame)->pd.DataFrame:
        data['pass_length']=data.apply(lambda r: WF.distance(r['x'], r['y'], r['endX'], r['endY']), axis=1)
        data['pass_angle']=data.apply(lambda r: -self._degrees(r['x'], r['y'], r['endX'], r['endY']), axis=1)
        data['pass_angle_360']= data['pass_angle'].apply(lambda x: x if x>=0 else x+360)

        data['length_bin']=data['pass_length'].apply(lambda x: 0 if x < self.length_bin_edges[0] else 1 if x < self.length_bin_edges[1] else 2)
        data['angle_bin']=pd.cut(
            data['pass_angle_360'],bins = [0] + [i * 360 / self.num_angle_bins + 360 / self.num_angle_bins / 2 for i in range(self.num_angle_bins)] + [360], labels=range(self.num_angle_bins+1)
        )
        data['angle_bin']=data['angle_bin'].apply(lambda x: x if x != self.num_angle_bins else 0)

        aggregated_data = data.groupby(['player_name','length_bin', 'angle_bin'])['outcome'].agg(['sum', 'count']).reset_index().rename(columns={'sum':'pass_successes', 'count':'pass_attempts'})
        aggregated_data['pass_success_rate']=aggregated_data['pass_successes']/aggregated_data['pass_attempts']
        aggregated_data['pct_of_total_passes']=aggregated_data.apply(lambda r: r['pass_attempts']/aggregated_data[aggregated_data['player_name']==r['player_name']]['pass_attempts'].sum(), axis=1)

        return aggregated_data
    
    def _attach_color_data(self, data: pd.DataFrame) -> pd.DataFrame:
        data['color'] = data['pct_of_total_passes'].apply(lambda x: get_cmap(self.main_cmap)(x/self.main_cmap_max_value))
        data['text_shading'] = data['color'].apply(lambda x: self.light_text_color if is_light_or_dark(x) == ColourShade.DARK else self.dark_text_color)
        return data
    

        
    def _setup_figure(self):
        fig = Figure(figsize=self.fig_size, facecolor=self.facecolor)
        axes = {
            'title': fig.add_axes([0, 0.90, 1, 0.1], facecolor=self.facecolor),
            'radar': fig.add_axes([0, 0.05, 1, 0.85], projection='polar', facecolor=self.facecolor),
            'endnote': fig.add_axes([0, 0, 1, 0.05], facecolor=self.facecolor)
        }
        for ax_title in ['title', 'endnote']:
            axes[ax_title].axis('off')
        
        axes['radar'].set_rorigin(-0.2)
        axes['radar'].set_theta_zero_location('N')
        axes['radar'].set_theta_direction(-1)
        axes['radar'].set_yticklabels([])
        axes['radar'].set_xticklabels([])
        axes['radar'].yaxis.grid(False)

        theta, width = np.linspace(
              0.0, 2 * np.pi, self.num_angle_bins, endpoint=False, retstep=True
          )
        
        axes['radar'].set_thetagrids((theta+width/2) * 180 / np.pi)
        return fig, axes
    
    def _plot_radar(self, pass_summary: pd.DataFrame, ax:Axes):
        theta, width = np.linspace(
              0.0, 2 * np.pi, self.num_angle_bins, endpoint=False, retstep=True
        )
        
        for _, r in pass_summary.iterrows():
            theta = r['angle_bin']*360/self.num_angle_bins*np.pi / 180
            ax.bar(theta, bottom = r['length_bin']*0.55, height=.5, width=width, color=r['color'])
            ax.text(theta, r['length_bin']*0.55+0.25, f"{r['pct_of_total_passes']*100:0.1f}%",ha='center',va='center',color=r['text_shading'])
        ax.text(0, -0.2, pass_summary['pass_attempts'].sum(), ha='center',va='center')

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._setup_figure()
        pass_summary = self.pass_aggregator(data)
        self._attach_color_data(pass_summary)
        self._plot_radar(pass_summary, axes['radar'])
        return fig, axes
    

class ComparisonRadialPassHeatmapDashboard(RadialPassHeatmapDashboard):

    def __init__(self, data_accessor):
        super().__init__(data_accessor)
        self.main_cmap = 'coolwarm'

    def _attach_color_data(self, data: pd.DataFrame) -> pd.DataFrame:
        data['color'] = data['pct_of_total_passes'].apply(lambda x: get_cmap(self.main_cmap)(x/(self.main_cmap_max_value / 2) + 0.5))
        data['text_shading'] = data['color'].apply(lambda x: self.light_text_color if is_light_or_dark(x) == ColourShade.DARK else self.dark_text_color)
        return data
    

    def pass_aggregator(self, data: pd.DataFrame) -> pd.DataFrame:
        aggregated_data =  super().pass_aggregator(data)
        target_player = aggregated_data[aggregated_data['player_name']==data['Player'].values[0]] 
        other_players = aggregated_data[aggregated_data['player_name']!=data['Player'].values[0]]
        other_players = other_players.groupby(['length_bin','angle_bin']).agg({'pass_successes':'sum', 'pass_attempts':'sum'}).reset_index()
        other_players['pass_success_rate']=other_players['pass_successes']/other_players['pass_attempts']
        other_players['pct_of_total_passes']=other_players['pass_attempts']/other_players['pass_attempts'].sum()

        combined_data = pd.merge(target_player, other_players, on=['length_bin', 'angle_bin'], suffixes=('_player', '_other'))
        combined_data['pct_of_total_passes']=combined_data['pct_of_total_passes_player']-combined_data['pct_of_total_passes_other']
        combined_data['pass_attempts']=combined_data['pass_attempts_player']
        return combined_data