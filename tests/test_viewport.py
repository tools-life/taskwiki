# -*- coding: utf-8 -*-
from datetime import datetime
from tests.base import IntegrationTest
from time import sleep


class TestViewportsTaskGeneration(IntegrationTest):

    viminput = """
    === Work tasks | +work ===
    """

    vimoutput = """
    === Work tasks | +work ===
    * [ ] tag work task  #{uuid}
    """

    tasks = [
        dict(description="tag work task", tags=['work']),
    ]

    def execute(self):
        self.command("w", regex="written$", lines=1)


class TestViewportsTaskRemoval(IntegrationTest):

    viminput = """
    === Work tasks | -work ===
    * [ ] tag work task  #{uuid}
    """

    vimoutput = """
    === Work tasks | -work ===
    """

    tasks = [
        dict(description="tag work task", tags=['work']),
    ]

    def execute(self):
        self.command("w", regex="written$", lines=1)


class TestViewportDefaultsAssigment(IntegrationTest):

    viminput = """
    === Work tasks | +work ===
    * [ ] tag work task
    """

    vimoutput = """
    === Work tasks | +work ===
    * [ ] tag work task  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'tag work task'
        assert task['status'] == 'pending'
        assert task['tags'] == ['work']


class TestViewportDefaultsOverriding(IntegrationTest):

    viminput = """
    === Work tasks | project:Home +home | project:Chores  ===
    * [ ] home task
    """

    vimoutput = """
    === Work tasks | project:Home +home | project:Chores  ===
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'home task'
        assert task['status'] == 'pending'
        assert task['project'] == 'Chores'
        assert task['tags'] == ['home']


class TestViewportDefaultsRemoval(IntegrationTest):

    viminput = """
    === Work tasks | project:Home +home | project:  ===
    * [ ] home task
    """

    vimoutput = """
    === Work tasks | project:Home +home | project:  ===
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'home task'
        assert task['status'] == 'pending'
        assert task['project'] == None
        assert task['tags'] == ['home']


class TestViewportInspection(IntegrationTest):

    viminput = """
    === Work tasks | +work ===
    * [ ] tag work task  #{uuid}
    """

    vimoutput = """
    ViewPort inspection:
    --------------------
    Name: Work tasks
    Filter used: -DELETED -PARENT +work
    Defaults used: tags:['work']
    Matching taskwarrior tasks: 1
    Displayed tasks: 1
    Tasks to be added:
    Tasks to be deleted:
    """

    tasks = [
        dict(description="tag work task", tags=['work']),
    ]

    def execute(self):
        self.command("w", regex="written$", lines=1)
        self.client.feedkeys('1gg')
        self.client.feedkeys(r'\<CR>')
        sleep(0.5)

        assert self.command(":py print vim.current.buffer", regex="<buffer taskwiki.")


class TestViewportsUnicodeTaskGeneration(IntegrationTest):

    viminput = """
    === Work tasks | +work ===
    """

    vimoutput = u"""
    === Work tasks | +work ===
    * [ ] tag work täsk  #{uuid}
    """

    tasks = [
        dict(description=u"tag work täsk", tags=['work']),
    ]

    def execute(self):
        self.command("w", regex="written$", lines=1)


class TestViewportsTaskSortedGeneration(IntegrationTest):

    viminput = """
    === Work tasks | +work ===
    """

    vimoutput = """
    === Work tasks | +work ===
    * [ ] main task 1 (2015-08-07 00:00)  #{uuid}
        * [ ] sub task 1a (2015-08-01 00:00)  #{uuid}
            * [ ] sub task 1aa  #{uuid}
        * [ ] sub task 1b  #{uuid}
    * [ ] main task 2 (2015-08-08 00:00)  #{uuid}
    * [ ] main task 3 (2015-08-09 00:00)  #{uuid}
        * [ ] sub task 3a (2015-08-03 00:00)  #{uuid}
        * [ ] sub task 3b  #{uuid}
    * [ ] main task 4  #{uuid}
    """

    tasks = [
        dict(description="main task 3", tags=['work'], due=datetime(2015,8,9)),
        dict(description="main task 2", tags=['work'], due=datetime(2015,8,8)),
        dict(description="main task 1", tags=['work'], due=datetime(2015,8,7)),
        dict(description="main task 4", tags=['work']),
        dict(description="sub task 1b", tags=['work']),
        dict(description="sub task 1a", tags=['work'], due=datetime(2015,8,1)),
        dict(description="sub task 1aa", tags=['work']),
        dict(description="sub task 3b", tags=['work']),
        dict(description="sub task 3a", tags=['work'], due=datetime(2015,8,3)),
    ]

    def execute(self):
        # Mark the dependencies
        self.tasks[2]['depends'].add(self.tasks[4])
        self.tasks[2]['depends'].add(self.tasks[5])
        self.tasks[0]['depends'].add(self.tasks[7])
        self.tasks[0]['depends'].add(self.tasks[8])
        self.tasks[5]['depends'].add(self.tasks[6])

        for task in self.tasks:
            task.save()

        self.command("w", regex="written$", lines=1)
