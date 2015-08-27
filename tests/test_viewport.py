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


class TestViewportsContextTaskGeneration(IntegrationTest):

    viminput = """
    === Work tasks | @work ===
    """

    vimoutput = """
    === Work tasks | @work ===
    * [ ] tag work task  #{uuid}
    """

    tasks = [
        dict(description="tag work task", tags=['work']),
    ]

    def execute(self):
        with open(self.taskrc_path, 'a') as f:
            f.write('context.work=+work\n')

        self.command("w", regex="written$", lines=1)


class TestViewportsContextComplexFilterTaskGeneration(IntegrationTest):

    viminput = """
    === Work tasks | @work or project:Home ===
    """

    vimoutput = """
    === Work tasks | @work or project:Home ===
    * [ ] home project task  #{uuid}
    * [ ] tag work task  #{uuid}
    """

    tasks = [
        dict(description="tag work task", tags=['work']),
        dict(description="home project task", project='Home'),
    ]

    def execute(self):
        with open(self.taskrc_path, 'a') as f:
            f.write('context.work=+work\n')

        self.command("w", regex="written$", lines=1)


class TestViewportsTwoContextTaskGeneration(IntegrationTest):

    viminput = """
    === Work tasks | @work or @home ===
    """

    vimoutput = """
    === Work tasks | @work or @home ===
    * [ ] home project task  #{uuid}
    * [ ] tag work task  #{uuid}
    """

    tasks = [
        dict(description="tag work task", tags=['work']),
        dict(description="home project task", project='Home'),
    ]

    def execute(self):
        with open(self.taskrc_path, 'a') as f:
            f.write('context.work=+work\n')
            f.write('context.home=project:Home\n')

        self.command("w", regex="written$", lines=1)


class TestViewportsContextInvalid(IntegrationTest):

    viminput = """
    === Work tasks | @doesnotexist ===
    """

    vimoutput = """
    === Work tasks | @doesnotexist ===
    """

    def execute(self):
        self.command("w", regex="Context definition for 'doesnotexist' "
                                "could not be found.", lines=3)


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


class TestViewportDefaultsExplicit(IntegrationTest):

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
        assert task['tags'] == []


class TestViewportDefaultsExplicitEmpty(IntegrationTest):

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
        assert task['tags'] == []


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
    Ordering used: due+,pri-,project+
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


class TestViewportsSortedGeneration(IntegrationTest):

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


class TestViewportsSortedGenerationReverse(TestViewportsSortedGeneration):

    vimoutput = """
    === Work tasks | +work ===
    * [ ] main task 3 (2015-08-09 00:00)  #{uuid}
        * [ ] sub task 3a (2015-08-03 00:00)  #{uuid}
        * [ ] sub task 3b  #{uuid}
    * [ ] main task 2 (2015-08-08 00:00)  #{uuid}
    * [ ] main task 1 (2015-08-07 00:00)  #{uuid}
        * [ ] sub task 1a (2015-08-01 00:00)  #{uuid}
            * [ ] sub task 1aa  #{uuid}
        * [ ] sub task 1b  #{uuid}
    * [ ] main task 4  #{uuid}
    """

    def execute(self):
        # Change the ordering
        self.command('let g:taskwiki_sort_order="due-"')

        # Otherwise everything from previous test should be preserved
        super(TestViewportsSortedGenerationReverse, self).execute()


class TestViewportsMultilevelSortedGeneration(IntegrationTest):

    viminput = """
    === Work tasks | project:Work or project:Home ===
    """

    vimoutput = """
    === Work tasks | project:Work or project:Home ===
    * [ ] home task 1 (2015-08-01 00:00)  #{uuid}
    * [ ] home task 2 (2015-08-02 00:00)  #{uuid}
    * [ ] home task 3 (2015-08-03 00:00)  #{uuid}
    * [ ] work task 1 (2015-08-01 00:00)  #{uuid}
    * [ ] work task 2 (2015-08-02 00:00)  #{uuid}
    * [ ] work task 3 (2015-08-03 00:00)  #{uuid}
    """

    tasks = [
        dict(description="home task 1", project="Home", due=datetime(2015,8,1)),
        dict(description="home task 2", project="Home", due=datetime(2015,8,2)),
        dict(description="home task 3", project="Home", due=datetime(2015,8,3)),
        dict(description="work task 1", project="Work", due=datetime(2015,8,1)),
        dict(description="work task 2", project="Work", due=datetime(2015,8,2)),
        dict(description="work task 3", project="Work", due=datetime(2015,8,3)),
    ]

    def execute(self):
        # Change the ordering
        self.command('let g:taskwiki_sort_order="project,due"')

        # Generate the tasks
        self.command("w", regex="written$", lines=1)


class TestViewportsSpecificSorting(IntegrationTest):

    viminput = """
    === Work tasks | project:Work or project:Home $T ===
    """

    vimoutput = """
    === Work tasks | project:Work or project:Home $T ===
    * [ ] home task 1 (2015-08-01 00:00)  #{uuid}
    * [ ] home task 2 (2015-08-02 00:00)  #{uuid}
    * [ ] work task 1 (2015-08-01 00:00)  #{uuid}
    * [ ] work task 2 (2015-08-02 00:00)  #{uuid}
    """

    tasks = [
        dict(description="home task 1", project="Home", due=datetime(2015,8,1)),
        dict(description="home task 2", project="Home", due=datetime(2015,8,2)),
        dict(description="work task 1", project="Work", due=datetime(2015,8,1)),
        dict(description="work task 2", project="Work", due=datetime(2015,8,2)),
    ]

    def execute(self):
        # Define the ordering T
        self.command('let g:taskwiki_sort_orders={"T": "project,due"}')

        # Generate the tasks
        self.command("w", regex="written$", lines=1)


class TestViewportsSpecificSortingCombined(TestViewportsSpecificSorting):

    viminput = """
    === Work tasks | project:Work or project:Home $T ===

    === Work tasks | project:Work or project:Home ===
    """

    vimoutput = """
    === Work tasks | project:Work or project:Home $T ===
    * [ ] home task 1 (2015-08-01 00:00)  #{uuid}
    * [ ] home task 2 (2015-08-02 00:00)  #{uuid}
    * [ ] work task 1 (2015-08-01 00:00)  #{uuid}
    * [ ] work task 2 (2015-08-02 00:00)  #{uuid}

    === Work tasks | project:Work or project:Home ===
    * [ ] home task 1 (2015-08-01 00:00)  #{uuid}
    * [ ] work task 1 (2015-08-01 00:00)  #{uuid}
    * [ ] home task 2 (2015-08-02 00:00)  #{uuid}
    * [ ] work task 2 (2015-08-02 00:00)  #{uuid}
    """


class TestViewportsSortedInvalidOrder(IntegrationTest):

    viminput = """
    === Work tasks | +work $X ===
    """

    vimoutput = """
    === Work tasks | +work $X ===
    """

    def execute(self):
        # Check that proper error message is raised
        self.command("w", regex="Sort indicator 'X' for viewport "
            "'Work tasks' is not defined, using default.", lines=2)


class TestViewportsVisibleMetaTag(IntegrationTest):

    viminput = """
    === Home tasks | project:Home -VISIBLE ===

    === Chores | project:Home.Chores ===
    """

    vimoutput = """
    === Home tasks | project:Home -VISIBLE ===
    * [ ] home task  #{uuid}

    === Chores | project:Home.Chores ===
    * [ ] chore task  #{uuid}
    """

    tasks = [
        dict(description="home task", project='Home.Random'),
        dict(description="chore task", project='Home.Chores'),
    ]

    def execute(self):
        # Currently, two saves are necessary for VISIBLE to take effect
        self.command("w", regex="written$", lines=1)
        self.command("w", regex="written$", lines=1)
