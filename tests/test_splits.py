import re

from tests.base import IntegrationTest
from tasklib.task import local_zone
from datetime import datetime


def current_year():
    return local_zone.localize(datetime.now()).year


def current_month():
    current_month_number = local_zone.localize(datetime.now()).month
    months = ["January", "February", "March", "April",
              "May", "June", "July", "August",
              "September", "October", "November", "December"]

    return months[current_month_number - 1]


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

        assert str(current_year()) in '\n'.join(output)


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


        assert str(current_year()) in '\n'.join(output)
        assert current_month() in '\n'.join(output)


class TestHistoryAnnualSimple(IntegrationTest):

    tasks = [
        dict(description="test task"),
        dict(description="completed task 1", status="completed", end="now"),
        dict(description="completed task 2", status="completed", end="now"),
        dict(description="deleted task", status="deleted"),
    ]

    def execute(self):
        self.command("TaskWikiHistoryAnnual")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer history.annual")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Year', 'Added', 'Completed', 'Deleted', 'Net'])
        year = r'\s*'.join(map(str, [current_year(), 4, 2, 1, 1]))

        assert re.search(header, output, re.MULTILINE)
        assert re.search(year, output, re.MULTILINE)


class TestHistoryMonthlySimple(IntegrationTest):

    tasks = [
        dict(description="test task"),
        dict(description="completed task 1", status="completed", end="now"),
        dict(description="completed task 2", status="completed", end="now"),
        dict(description="deleted task", status="deleted"),
    ]

    def execute(self):
        self.command("TaskWikiHistoryMonthly")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer history.monthly")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Year', 'Month', 'Added', 'Completed', 'Deleted', 'Net'])
        year = r'\s*'.join(map(str, [current_year(), current_month(), 4, 2, 1, 1]))

        assert re.search(header, output, re.MULTILINE)
        assert re.search(year, output, re.MULTILINE)
