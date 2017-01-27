# -*- coding: utf-8 -*-

from datetime import datetime
from tasklib import local_zone
from tests.base import IntegrationTest, MultipleSourceTest


class TestSimpleTaskCreation(IntegrationTest):

    viminput = """
    * [ ] This is a test task
    """

    vimoutput = """
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'


class TestInvalidUUIDTask(IntegrationTest):

    viminput = """
    * [ ] This is a test task  #abc123ef
    """

    vimoutput = """
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command("w", regex="on line 1 will be re-created")

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'


class TestSimpleTaskModification(IntegrationTest):

    viminput = """
    * [ ] This is a test task  #{uuid}
    """

    vimoutput = """
    * [ ] This is a modified task  #{uuid}
    """

    tasks = [
        dict(description="This is a test task")
    ]

    def execute(self):
        # Change the current line's due date
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('test', 'modified')
        self.write_buffer(current_data)

        self.command("w", regex="written$", lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a modified task'
        assert task['status'] == 'pending'


class TestBufferTaskCompletion(IntegrationTest):

    viminput = """
    * [ ] This is a test task  #{uuid}
    """

    vimoutput = """
    * [X] This is a test task  #{uuid}
    """

    tasks = [
        dict(description="This is a test task")
    ]

    def execute(self):
        # Change the current line's due date
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('[ ]', '[X]')
        self.write_buffer(current_data)

        self.command("w", regex="written$", lines=1)

        # Check that the task was completed
        assert len(self.tw.tasks.pending()) == 0
        assert len(self.tw.tasks.completed()) == 1

        task = self.tw.tasks.completed()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'completed'
        assert task['end'] is not None


class TestBufferTaskUncompletion(IntegrationTest):

    viminput = """
    * [X] This is a test task  #{uuid}
    """

    vimoutput = """
    * [ ] This is a test task  #{uuid}
    """

    tasks = [
        dict(description="This is a test task", status="completed")
    ]

    def execute(self):
        # Change the current line's due date
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('[X]', '[ ]')
        self.write_buffer(current_data)

        self.command("w", regex="written$", lines=1)

        # Check that the task was completed
        assert len(self.tw.tasks.pending()) == 1
        assert len(self.tw.tasks.completed()) == 0

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['end'] is None


class TestBufferTaskDeletion(IntegrationTest):

    viminput = """
    * [ ] This is a test task  #{uuid}
    """

    vimoutput = """
    * [D] This is a test task  #{uuid}
    """

    tasks = [
        dict(description="This is a test task")
    ]

    def execute(self):
        # Change the current line's due date
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('[ ]', '[D]')
        self.write_buffer(current_data)

        self.command("w", regex="written$", lines=1)

        # Check that the task was completed
        assert len(self.tw.tasks.pending()) == 0
        assert len(self.tw.tasks.deleted()) == 1

        task = self.tw.tasks.deleted()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'deleted'
        assert task['end'] is not None


class TestBufferTaskUndeletion(IntegrationTest):

    viminput = """
    * [D] This is a test task  #{uuid}
    """

    vimoutput = """
    * [ ] This is a test task  #{uuid}
    """

    tasks = [
        dict(description="This is a test task", status="deleted", end="now")
    ]

    def execute(self):
        # Change the current line's due date
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('[D]', '[ ]')
        self.write_buffer(current_data)

        self.command("w", regex="written$", lines=1)

        # Check that the task was completed
        assert len(self.tw.tasks.pending()) == 1
        assert len(self.tw.tasks.deleted()) == 0

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['end'] is None


class TestBufferTaskActivation(IntegrationTest):

    viminput = """
    * [ ] This is a test task  #{uuid}
    """

    vimoutput = """
    * [S] This is a test task  #{uuid}
    """

    tasks = [
        dict(description="This is a test task")
    ]

    def execute(self):
        # Change the current line's due date
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('[ ]', '[S]')
        self.write_buffer(current_data)

        self.command("w", regex="written$", lines=1)

        # Check that the task was completed
        assert len(self.tw.tasks.pending()) == 1
        assert len(self.tw.tasks.filter(start__any=None)) == 1

        task = self.tw.tasks.get(start__any=None)
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['start'] is not None
        assert task['end'] is None


class TestBufferTaskDeactivation(IntegrationTest):

    viminput = """
    * [S] This is a test task  #{uuid}
    """

    vimoutput = """
    * [ ] This is a test task  #{uuid}
    """

    tasks = [
        dict(description="This is a test task", status="pending", start="now")
    ]

    def execute(self):
        # Change the current line's due date
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('[S]', '[ ]')
        self.write_buffer(current_data)

        self.command("w", regex="written$", lines=1)

        # Check that the task was completed
        assert len(self.tw.tasks.pending()) == 1
        assert len(self.tw.tasks.completed()) == 0

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['start'] is None
        assert task['end'] is None


class TestSimpleTaskWithDueDatetimeCreation(IntegrationTest):

    viminput = """
    * [ ] This is a test task (2015-03-03 12:00)
    """

    vimoutput = """
    * [ ] This is a test task (2015-03-03 12:00)  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        due = datetime(2015, 3, 3, 12, 0)

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['due'] == local_zone.localize(due)


class TestSimpleTaskWithFlawedDueDatetimeCreation(IntegrationTest):

    viminput = """
    * [ ] This is a test task (2015-94-53 12:00)
    """

    vimoutput = """
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command("w", regex="Invalid timestamp", lines=2)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['due'] == None


class TestSimpleTaskWithDueDateCreation(IntegrationTest):

    viminput = """
    * [ ] This is a test task (2015-03-03)
    """

    vimoutput = """
    * [ ] This is a test task (2015-03-03)  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        due = datetime(2015, 3, 3, 0, 0)

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['due'] == local_zone.localize(due)


class TestSimpleTaskWithDueDatetimeModification(IntegrationTest):

    viminput = """
    * [ ] This is a test task (2015-03-03 12:00)  #{uuid}
    """

    vimoutput = """
    * [ ] This is a test task (2015-03-04 13:00)  #{uuid}
    """

    tasks = [
        dict(description="This is a test task", due=datetime(2015, 3, 3, 12, 0))
    ]

    def execute(self):
        # Change the current line's due date
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('2015-03-03 12:00',
                                                  '2015-03-04 13:00')
        self.write_buffer(current_data)

        # Save the changes
        self.command("w", regex="written$", lines=1)

        # Check that only one tasks with exists
        assert len(self.tw.tasks.pending()) == 1

        due = datetime(2015, 3, 4, 13, 0)

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['due'] == local_zone.localize(due)


class TestSimpleTaskWithPriorityCreation(IntegrationTest):

    viminput = """
    * [ ] This is a test task !!
    """

    vimoutput = """
    * [ ] This is a test task !!  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        # Check that only one task matches
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['priority'] == "M"


class TestSimpleTaskWithPriorityModification(IntegrationTest):

    viminput = """
    * [ ] This is a test task !!!  #{uuid}
    """

    vimoutput = """
    * [ ] This is a test task !  #{uuid}
    """

    tasks = [
        dict(description="This is a test task", priority="H")
    ]

    def execute(self):
        # Change the current line's priority
        current_data = self.read_buffer()
        current_data[0] = current_data[0].replace('!!!', '!')
        self.write_buffer(current_data)

        # Save the changes
        self.command("w", regex="written$", lines=1)

        # Check that only one task exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'This is a test task'
        assert task['status'] == 'pending'
        assert task['priority'] == "L"


class TestChildTaskCreation(IntegrationTest):

    viminput = """
    * [ ] This is parent task
      * [ ] This is child task
    """

    vimoutput = """
    * [ ] This is parent task  #{uuid}
      * [ ] This is child task  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 2

        parent = self.tw.tasks.filter(description="This is parent task")[0]
        child = self.tw.tasks.filter(description="This is child task")[0]

        assert child['description'] == 'This is child task'
        assert parent['description'] == 'This is parent task'
        assert parent['depends'] == set([child])


class TestChildTaskCreationLimit(IntegrationTest):

    viminput = """
    * [ ] This is not a parent task
    * This is the parent entry
      * [ ] This is not a child task
    """

    vimoutput = """
    * [ ] This is not a parent task  #{uuid}
    * This is the parent entry
      * [ ] This is not a child task  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        parent = self.tw.tasks.filter(description="This is not a parent task")[0]
        child = self.tw.tasks.filter(description="This is not a child task")[0]

        assert parent['depends'] == set()


class TestChildTaskModification(IntegrationTest):

    viminput = """
    * [ ] This is parent task  #{uuid}
    * [ ] This is child task  #{uuid}
    """

    vimoutput = """
    * [ ] This is parent task  #{uuid}
      * [ ] This is child task  #{uuid}
    """

    tasks = [
        dict(description="This is parent task"),
        dict(description="This is child task"),
    ]

    def execute(self):
        # Check that only two tasks are in the data files
        assert len(self.tw.tasks.pending()) == 2

        parent = self.tw.tasks.filter(description="This is parent task")[0]
        child = self.tw.tasks.filter(description="This is child task")[0]

        assert parent['depends'] == set()

        # Indent the task in the buffer
        buffer_content = self.read_buffer()
        self.write_buffer(["  " + buffer_content[1]], 1)

        self.command("w", regex="written$", lines=1)

        # Check that only two tasks are in the data files
        assert len(self.tw.tasks.pending()) == 2

        parent = self.tw.tasks.filter(description="This is parent task")[0]
        child = self.tw.tasks.filter(description="This is child task")[0]

        assert parent['depends'] == set([child])


class TestCreationDifferentTaskSource(MultipleSourceTest):

    viminput = """
    * [ ] This is first data source task  #H:
    """

    def execute(self):
        self.command('w', regex='written')

        # Check that corect data store has been used
        assert len(self.tw.tasks.all()) == 0
        assert len(self.extra_tw.tasks.all()) == 1


class TestSimpleUnicodeTaskCreation(IntegrationTest):

    viminput = u"""
    * [ ] This is a test täsk
    """

    vimoutput = u"""
    * [ ] This is a test täsk  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['description'] == u'This is a test täsk'
        assert task['status'] == 'pending'


class TestLineNumberPreservation(IntegrationTest):

    viminput = """
    My tasks for today:
    * [ ] Wake up
    * [ ] Sieze the day
    * [ ] Go to sleep in time
    """

    vimoutput = """
    My tasks for today:
    * [ ] Wake up  #{uuid}
    * [ ] Go to sleep in time  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        # Delete Sieze the day task
        self.client.normal('3gg')
        self.command('TaskWikiDelete', regex="deleted", lines=1)

        # Check cursor position
        assert self.client.eval("line('.')") == '3'
