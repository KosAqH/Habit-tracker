import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import ListedColormap

import july
from july.utils import date_range

import io
import base64
import datetime
from typing import Literal

from app.models import Habit, State

DEFAULT_CMAPS = {
    "state": ListedColormap(
            ["grey", 
             "grey", 
             "darkred", 
             "red", 
             "orange", 
             "yellowgreen", 
             "darkgreen"]
        ),
    "habit": ListedColormap(["grey", "red", "green"])
}

class DashboardStatsHandler():
    def __init__(
            self, 
            date: datetime.date
        ) -> None:
        self.end_date = date
        self.start_date = date - datetime.timedelta(days=365)
        
    def prepare_habit_data(self,
            habits: list[Habit],
            does_today_entry_exists: int,
            today: datetime.date = datetime.date.today()
        ) -> None:

        for habit in habits:
            habit.n_days = StatsUtils.get_tracking_days_count(habit, today, does_today_entry_exists)
            habit.percentage = StatsUtils.get_habit_fulfillment_percentage(habit, habit.n_days)
            habit.streak = StatsUtils.get_current_streak(habit)

    def prepare_state_data(
            self,
            states: list[State],
            does_today_entry_exists: int,
            today: datetime.date = datetime.date.today()
        ) -> None:

        for state in states:
            state.n_days = StatsUtils.get_tracking_days_count(state, today, does_today_entry_exists)
            state.avg_value = StatsUtils.get_avg_state_value(state)

class StatsUtils():
    @classmethod
    def get_avg_state_value(cls, state: State) -> float:
        if state.state_entries:
            avg_value = sum((entry.value for entry in state.state_entries))/len(state.state_entries)
        else:
            avg_value = 0
        return round(avg_value, 2)
    
    @classmethod
    def get_tracking_days_count(
            cls,
            object: Habit | State,
            today: datetime.date,
            does_today_entry_exists: int
        ) -> int:
        
        return (today - object.start_date).days + does_today_entry_exists

    @classmethod
    def get_habit_fulfillment_percentage(
            cls, 
            habit: Habit, 
            days_of_tracking: int
        ) -> int:
        days_with_habit_done = sum(entry.value for entry in habit.habit_entries)
        ratio = days_with_habit_done/(days_of_tracking) if days_of_tracking else 0
        percentage = round(ratio * 100)

        return percentage
    
    @classmethod
    def get_current_streak(
            cls,
            habit: Habit
        ):
        streak = 0
        for entry in habit.habit_entries[::-1]:
            if entry.value == False:
                break
            streak += 1
        return streak

class PlotManager:
    def __init__(
        self,
        today_date: datetime.date,
        today_entry_exists: int
    ) -> None:
        self.today = today_date
        self.data_handler = DashboardStatsHandler(self.today)
        self.dates = self.get_dates()
        self.today_entry_exists = today_entry_exists
    
    def specify_data_preparation_method(self, data_type):
        if data_type == "Habit":
            self.prepare_data = self.data_handler.prepare_habit_data
        elif data_type == "State":
            self.prepare_data = self.data_handler.prepare_state_data
        else:
            raise(ValueError)

    def make_plots(self, data, data_type):
        self.specify_data_preparation_method(data_type)
        self.prepare_data(data, self.today_entry_exists)
        for obj in data:
            data = self.get_data_for_plot(obj, data_type)
            plotter = Plotter(self.dates, data, data_type)
            obj.plot = plotter.plot()

    def get_dates(self) -> list[datetime.date]:
        end_date = self.today
        start_date = self.today - datetime.timedelta(days=365)
        dates = date_range(
            start_date, end_date
        )
        return dates
    
    def get_data_for_plot(self, obj, data_type):
        if data_type == "Habit":
            entries = obj.habit_entries
        elif data_type == "State":
            entries = obj.state_entries
        else:
            raise(ValueError)
        
        data = [-1]*366
        for entry in entries:
            i = self.dates.index(entry.date)
            data[i] = entry.value
        return data

class Plotter:
    def __init__(
        self,
        dates: list[datetime.date],
        data: list[int],
        data_type: Literal["Habit", "State"]
    ) -> None:
        self.dates = dates
        self.data = data
        self.params = self.get_params(data_type)
        
    def plot(self) -> str:
        """
        doc to musi byc odpowiednik funkcji plot_habit i plot_state
        """
        mpl.use('agg') # turn off matplotlib gui
        july.heatmap(self.dates, self.data, **self.params)
        self._fig = plt.gcf()
        encoded_image = self.plot_to_base64()

        return encoded_image
    
    def plot_to_base64(self) -> str:
        s = io.BytesIO()
        self._fig.savefig(s, format='png', transparent=True, bbox_inches="tight")
        s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")

        return f'data:image/png;base64,{s}'

    def get_params(self, data_type):
        if data_type == "Habit":
            params = {
                "cmin": -1,
                "cmax": 1,
                "cmap": DEFAULT_CMAPS["habit"]
            }
        elif data_type == "State":
            params = {
                "cmin": -1,
                "cmax": 5,
                "cmap": DEFAULT_CMAPS["state"]
            }
        else:
            raise(ValueError)
        
        return params