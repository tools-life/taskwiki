from tests.base import IntegrationTest


class TestSimpleTask(IntegrationTest):

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
