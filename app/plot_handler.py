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

"""
CMAP for state responding to values:
    grey -- -1 -> No data

    darkred - dargreen -- 1-5 -> State values

CMAP for habit responding ti values:
    grey -- -1 -> No data
    red -- 0 -> Habit broke
    green -- 1 -> Habit done
"""
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
    """
    Class load data objects. Calculate statistics basing on particular object's
    entries. Statistics are attached as attributes to data objects.
    """
    def __init__(
            self, 
            date: datetime.date
        ) -> None:
        """
        Initialize attributes of object:
            - self.end_date - with date passed by user
            - self.start_date - with date one year prior to date passed by user.

        Arguments:
            date -- date object passed by user
        """
        self.end_date = date
        self.start_date = date - datetime.timedelta(days=365)
        
    def prepare_habit_data(self,
            habits: list[Habit],
            does_today_entry_exists: int
        ) -> None:
        """
        Calculate statistics for Habit object.

        Arguments:
            habits -- collection containing Habit objects
            does_today_entry_exists -- number indicating if today's entry were
                already entered by user
        """

        for habit in habits:
            habit.n_days = StatsUtils.get_tracking_days_count(habit, self.end_date, does_today_entry_exists)
            habit.percentage = StatsUtils.get_habit_fulfillment_percentage(habit, habit.n_days)
            habit.streak = StatsUtils.get_current_streak(habit)

    def prepare_state_data(
            self,
            states: list[State],
            does_today_entry_exists: int
        ) -> None:
        """
        Calculate statistics for State object.

        Arguments:
            states -- collection containing State objects
            does_today_entry_exists -- number indicating if today's entry were
                already entered by user
        """
        for state in states:
            state.n_days = StatsUtils.get_tracking_days_count(state, self.end_date, does_today_entry_exists)
            state.avg_value = StatsUtils.get_avg_state_value(state)

class StatsUtils():
    """
    Util class containing methods that calculate particular statistics.
    """
    @classmethod
    def get_avg_state_value(cls, state: State) -> float:
        """
        Calculate average state value among all entries. If there are no entries
        then return 0.
        Returned value is rounded to 2 decimal point.
        
        Argument:
            state -- State object
        """
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
        """
        Calculate and return count of days that passed since the start
        of tracking specified Habit or State to today (if today's entries were
        already entered) or to previous day (otherwise).

        Arguments:
            object -- Habit or State object
            today -- today's date
            does_today_entry_exists -- number indicating if today's entry were
                already entered by user
        """
        
        return (today - object.start_date).days + does_today_entry_exists

    @classmethod
    def get_habit_fulfillment_percentage(
            cls, 
            habit: Habit, 
            days_of_tracking: int
        ) -> int:
        """
        Calculate and return percentage of days with Habit done.
        Returned value is rounded to int.

        Arguments:
            habit -- Habit object
            days_of_tracking -- count of days that passed since the start of 
            tracking specified Habit to today
        """
        days_with_habit_done = sum(entry.value for entry in habit.habit_entries)
        ratio = days_with_habit_done/(days_of_tracking) if days_of_tracking else 0
        percentage = round(ratio * 100)

        return percentage
    
    @classmethod
    def get_current_streak(
            cls,
            habit: Habit
        ):
        """
        Calculate and return a consecutive count of days, that specified Habit
        was done at, starting at the newest entry.

        Arguments:
            habit -- Habit object
        """
        streak = 0
        for entry in habit.habit_entries[::-1]:
            if entry.value == False:
                break
            streak += 1
        return streak

class PlotManager:
    """
    Manages the plotting of calendar-like heatmaps.
    """
    def __init__(
        self,
        today_date: datetime.date,
        today_entry_exists: int
        ) -> None:
        """
        Initialize attributes of object.

        Arguments:
            -- today_date - date object passed by user
            -- today_entry_exists - number indicating if today's entry were
                already entered by user
        """
        self.today = today_date
        self.data_handler = DashboardStatsHandler(self.today)
        self.dates = self.get_dates()
        self.today_entry_exists = today_entry_exists
    
    def specify_data_preparation_method(
            self, 
            data_type: str
        ) -> None:
        """
        Choose appropriate method for handling particular type of data.
        Raise ValueError if there is no method for chosen data_type

        Arguments:
            -- data_type - data type's name
        """
        if data_type == "Habit":
            self.prepare_data = self.data_handler.prepare_habit_data
        elif data_type == "State":
            self.prepare_data = self.data_handler.prepare_state_data
        else:
            raise(ValueError)

    def make_plots(
            self, 
            data: list[Habit | State], 
            data_type: Literal["Habit", "State"]
        ) -> None:
        """
        Create plots for all objects in passed collection. Attach them
        to responding objects.

        Arguments:
            date -- collection with Habit or State objects
            data_type -- string indicating type of data user wants to plot
        """
        self.specify_data_preparation_method(data_type)
        self.prepare_data(data, self.today_entry_exists)
        for obj in data:
            data = self.get_data_for_plot(obj, data_type)
            plotter = Plotter(self.dates, data, data_type)
            obj.plot = plotter.plot()

    def get_dates(self) -> list[datetime.date]:
        """
        Create list of all dates in given range. Range is took from class'
        attributes. 
        """
        end_date = self.today
        start_date = self.today - datetime.timedelta(days=365)
        dates = date_range(
            start_date, end_date
        )
        return dates
    
    def get_data_for_plot(
            self, 
            obj : Habit | State, 
            data_type: Literal["Habit", "State"]
        ) -> list[int]:
        """
        Get neccesary values for plot and put them in a list.

        List is prefilled with -1 values, that indicate that 
        entry on that day doesn't exist.

        Arguments:
            obj -- Habit or State object
            data_type -- string indicating type of given data

        """
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
    """
    Class plotting calendar-like diagram from given data. Then plot is encoded
    in base64 and saved as a string. 
    """
    def __init__(
            self,
            dates: list[datetime.date],
            data: list[int],
            data_type: Literal["Habit", "State"]
        ) -> None:
        """
        Initializes class attributes. Sets plot params responding to given
        data_type.

        Arguments:
            dates -- list containing all dates to include in calendar
            data -- list containing all data values to plot
            data_type -- string indicating type of given data 
        """
        if len(dates != data):
            raise ValueError(
                "Length mismatch - dates and data list should have equal length"
            )
        self.dates = dates
        self.data = data
        self.params = self.get_params(data_type)
        mpl.use('agg') # turn off matplotlib gui
        
    def plot(self) -> str:
        """
        Create calendar-like heatmap. Return it as a base64 encoded string.
        """
        july.heatmap(self.dates, self.data, **self.params)
        self._fig = plt.gcf()
        encoded_image = self.plot_to_base64()

        return encoded_image
    
    def plot_to_base64(self) -> str:
        """
        Convert mpl figure to string encoded in base64. Return encoded plot.
        """
        s = io.BytesIO()
        self._fig.savefig(s, format='png', transparent=True, bbox_inches="tight")
        s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")

        return f'data:image/png;base64,{s}'

    def get_params(
            self,
            data_type: str
        ) -> dict:
        """
        Return dictionary with params for matplotlib, regarding to type
        of plotted data.

        Arguments:
            data_type -- string indicating type of given data
        """
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
            raise ValueError("Incorrect data type!")
        
        return params