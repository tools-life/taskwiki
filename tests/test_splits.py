import re

from tests.base import IntegrationTest
from tasklib.task import local_zone
from datetime import datetime


class TestBurndownDailySimple(IntegrationTest):

    def execute(self):
        self.command("TaskWikiBurndownDaily")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer burndown.daily")
        assert "Daily Burndown" in self.read_buffer()[0]


class TestBurndownMonthlySimple(IntegrationTest):

    def execute(self):
        self.command("TaskWikiBurndownMonthly")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer burndown.monthly")
        assert "Monthly Burndown" in self.read_buffer()[0]


class TestBurndownWeeklySimple(IntegrationTest):

    def execute(self):
        self.command("TaskWikiBurndownWeekly")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer burndown.weekly")
        assert "Weekly Burndown" in self.read_buffer()[0]


class TestCalendarSimple(IntegrationTest):

    def execute(self):
        self.command("TaskWikiCalendar")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer calendar")

        # Assert each day is displayed at least once.
        output = self.read_buffer()
        for day in map(str, range(1, 29)):
            assert any(day in line for line in output)


class TestGhistoryAnnualSimple(IntegrationTest):

    tasks = [
        dict(description="test task"),
        dict(description="completed task 1", status="completed", end="now"),
        dict(description="completed task 2", status="completed", end="now"),
        dict(description="deleted task", status="deleted"),
    ]

    def execute(self):
        self.command("TaskWikiGhistoryAnnual")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer ghistory.annual")
        output = self.read_buffer()

        header_words = ("Year", "Number", "Added", "Completed", "Deleted")
        for word in header_words:
            assert word in output[0]

        legend_words = ("Legend", "Added", "Completed", "Deleted")
        for word in legend_words:
            assert re.search(word, output[-1], re.IGNORECASE)

        current_year = local_zone.localize(datetime.now()).year
        assert str(current_year) in '\n'.join(output)


class TestGhistoryMonthlySimple(IntegrationTest):

    tasks = [
        dict(description="test task"),
        dict(description="completed task 1", status="completed", end="now"),
        dict(description="completed task 2", status="completed", end="now"),
        dict(description="deleted task", status="deleted"),
    ]

    def execute(self):
        self.command("TaskWikiGhistoryMonthly")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer ghistory.monthly")
        output = self.read_buffer()

        header_words = ("Year", "Month", "Number", "Added", "Completed", "Deleted")
        for word in header_words:
            assert word in output[0]

        legend_words = ("Legend", "Added", "Completed", "Deleted")
        for word in legend_words:
            assert re.search(word, output[-1], re.IGNORECASE)

        current_year = local_zone.localize(datetime.now()).year
        current_month_number = local_zone.localize(datetime.now()).month
        months = ["January", "February", "March", "April",
                  "May", "June", "July", "August",
                  "September", "October", "November", "December"]

        assert str(current_year) in '\n'.join(output)
        assert str(months[current_month_number - 1]) in '\n'.join(output)
