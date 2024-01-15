import pytest
import datetime
from app import app

from app.utils import CalendarUtils, DatetimeUtils

class TestCalendarUtils:
    @pytest.mark.parametrize(
            'year,month,expected_previous,expected_next',
            [("2022", "05", "202204", "202206"),
             ("2024", "03", "202402", "202404"),
             ("2023", "12", "202311", "202401"),
             ("2024", "01", "202312", "202402"),]
    )
    def test_get_next_and_previous_months(
            self,
            year,
            month,
            expected_previous,
            expected_next
        ):
        previous, next = CalendarUtils.get_next_and_previous_months(month, year)
        assert previous == expected_previous
        assert next == expected_next

class TestDatetimeUtils:

    @pytest.mark.parametrize(
            'entered_date,oldest_date,expected,',
            [(datetime.date(2024,1,10), datetime.date(2024,1,1), "None"),]
    )
    def test_handle_requested_date_out_of_range(
            self,
            entered_date, 
            oldest_date, 
            expected
        ):
        val = DatetimeUtils.handle_requested_date_out_of_range(entered_date, oldest_date)
        assert str(val) == expected
    