from tests.base import IntegrationTest
from time import sleep


class TestAnnotateAction(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.command(
            "TaskWikiAnnotate This is annotation.",
            regex="Task \"test task 1\" annotated.$",
            lines=1)

        self.tasks[0].refresh()
        annotation = self.tasks[0]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == "This is annotation."


class TestAnnotateActionMoved(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('2gg')  # Go to the second line
        self.command(
            "TaskWikiAnnotate This is annotation.",
            regex="Task \"test task 2\" annotated.$",
            lines=1)

        self.tasks[1].refresh()
        annotation = self.tasks[1]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == "This is annotation."


class TestAnnotateActionRange(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('V2gg')  # Go to the second line
        self.client.feedkeys(":TaskWikiAnnotate This is annotation.")
        self.client.type('<Enter>')

        sleep(2)

        for task in self.tasks:
            task.refresh()

        annotation = self.tasks[0]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == "This is annotation."

        annotation = self.tasks[1]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == "This is annotation."


class TestDeleteAction(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.command(
            "TaskWikiDelete",
            regex="Task \"test task 1\" deleted.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['status'] == "deleted"
        assert self.tasks[1]['status'] == "pending"


class TestDeleteActionMoved(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('2gg')
        self.command(
            "TaskWikiDelete",
            regex="Task \"test task 2\" deleted.$",
            lines=1)
        sleep(1)

        for task in self.tasks:
            task.refresh()

        assert self.tasks[1]['status'] == "deleted"
        assert self.tasks[0]['status'] == "pending"


class TestDeleteActionRange(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        sleep(1)
        self.client.normal('VG')
        sleep(1)
        self.client.feedkeys(":TaskWikiDelete")
        self.client.type('<Enter>')
        sleep(1)

        for task in self.tasks:
            task.refresh()

        assert self.tasks[1]['status'] == "deleted"
        assert self.tasks[0]['status'] == "deleted"
