from datetime import datetime
from tasklib.task import local_zone
from tests.base import IntegrationTest


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


class TestSimpleTaskWithDueDateCreation(IntegrationTest):

    viminput = """
    * [ ] This is a test task (2015-03-03)
    """

    vimoutput = """
    * [ ] This is a test task (2015-03-03 00:00)  #{uuid}
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
