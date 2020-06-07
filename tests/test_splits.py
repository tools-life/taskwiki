import re

from tests.base import IntegrationTest
from tasklib import local_zone
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
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer burndown.daily")
        assert "Daily Burndown" in self.read_buffer()[0]


class TestBurndownMonthlySimple(IntegrationTest):

    def execute(self):
        self.command("TaskWikiBurndownMonthly")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer burndown.monthly")
        assert "Monthly Burndown" in self.read_buffer()[0]


class TestBurndownWeeklySimple(IntegrationTest):

    def execute(self):
        self.command("TaskWikiBurndownWeekly")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer burndown.weekly")
        assert "Weekly Burndown" in self.read_buffer()[0]


class TestCalendarSimple(IntegrationTest):

    def execute(self):
        self.command("TaskWikiCalendar")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer calendar")

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
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer ghistory.annual")
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
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer ghistory.monthly")
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
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer history.annual")
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
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer history.monthly")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Year', 'Month', 'Added', 'Completed', 'Deleted', 'Net'])
        year = r'\s*'.join(map(str, [current_year(), current_month(), 4, 2, 1, 1]))

        assert re.search(header, output, re.MULTILINE)
        assert re.search(year, output, re.MULTILINE)


class TestProjectsSimple(IntegrationTest):

    tasks = [
        dict(description="home task", project="Home"),
        dict(description="home chore task 1", project="Home.Chores"),
        dict(description="home chore task 2", project="Home.Chores"),
        dict(description="work task 1", project="Work"),
        dict(description="work task 2", project="Work"),
    ]

    def execute(self):
        self.command("TaskWikiProjects")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer projects")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Project', 'Tasks'])
        home = r'\s*'.join(['Home', '3' if self.tw.version >= '2.4.2' else '1'])
        chores = r'\s*'.join(['Chores', '2'])
        work = r'\s*'.join(['Work', '2'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(home, output, re.MULTILINE)
        assert re.search(chores, output, re.MULTILINE)
        assert re.search(work, output, re.MULTILINE)


class TestSummarySimple(IntegrationTest):

    tasks = [
        dict(description="home task", project="Home"),
        dict(description="home chore task 1", project="Home.Chores"),
        dict(description="home chore task 2", project="Home.Chores"),
        dict(description="work task 1", project="Work"),
        dict(description="work task 2", project="Work"),
    ]

    def execute(self):
        self.command("TaskWikiProjectsSummary")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer summary")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Project', 'Remaining', 'Avg age', 'Complete'])
        home = r'\s*'.join(['Home', '3' if self.tw.version >= '2.4.2' else '1'])
        chores = r'\s*'.join(['Chores', '2'])
        work = r'\s*'.join(['Work', '2'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(home, output, re.MULTILINE)
        assert re.search(chores, output, re.MULTILINE)
        assert re.search(work, output, re.MULTILINE)


class TestStatsSimple(IntegrationTest):

    tasks = [
        dict(description="home task"),
        dict(description="home chore task 1", tags=['chore']),
        dict(description="home chore task 2", tags=['chore']),
        dict(description="work task 1", tags=['work']),
        dict(description="work task 2", tags=['work']),
    ]

    def execute(self):
        self.command("TaskWikiStats")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer stats")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Category', 'Data'])
        data = r'\s*'.join(['Pending', '5'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(data, output, re.MULTILINE)


class TestTagsSimple(IntegrationTest):

    tasks = [
        dict(description="home task"),
        dict(description="home chore task 1", tags=['chore']),
        dict(description="home chore task 2", tags=['chore']),
        dict(description="work task 1", tags=['work']),
        dict(description="work task 2", tags=['work']),
    ]

    def execute(self):
        self.command("TaskWikiTags")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer tags")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Tag', 'Count'])
        chores = r'\s*'.join(['chore', '2'])
        work = r'\s*'.join(['work', '2'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(chores, output, re.MULTILINE)
        assert re.search(work, output, re.MULTILINE)


class TestTagsSimpleFiltered(IntegrationTest):

    tasks = [
        dict(description="home task"),
        dict(description="home chore task 1", tags=['chore']),
        dict(description="home chore task 2", tags=['chore']),
        dict(description="work task 1", tags=['work']),
        dict(description="work task 2", tags=['work']),
    ]

    def execute(self):
        self.command("TaskWikiTags +chore")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer tags")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Tag', 'Count'])
        chores = r'\s*'.join(['chore', '2'])
        work = r'\s*'.join(['work', '2'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(chores, output, re.MULTILINE)
        assert not re.search(work, output, re.MULTILINE)


class TestSplitReplacement(IntegrationTest):

    def execute(self):
        self.command("TaskWikiBurndownDaily")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer burndown.daily")
        assert "Daily Burndown" in self.read_buffer()[0]

        # switch back to taskwiki buffer
        self.client.feedkeys("\\<C-W>p")

        self.command("TaskWikiBurndownDaily")
        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer burndown.daily")
        assert "Daily Burndown" in self.read_buffer()[0]

        # Assert that there are only two buffers in the window
        self.py("print(len(vim.buffers))", regex='2$', lines=1)
