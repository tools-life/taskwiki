import re

from datetime import datetime
from tasklib import local_zone
from tests.base import IntegrationTest


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


class TestAnnotateActionManually(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.feedkeys(":TaskWikiAnnotate\\<Enter>")
        self.client.feedkeys("This is typed annotation.\\<Enter>")
        self.client.eval('0')  # wait for command completion

        self.tasks[0].refresh()
        annotation = self.tasks[0]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == "This is typed annotation."


class TestAnnotateActionManuallyAbort(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        # Start entering the annotation but bail out
        self.client.feedkeys(":TaskWikiAnnotate\\<Enter>")
        self.client.type("<Esc>")
        self.client.eval('0')  # wait for command completion

        # Refresh and check no annotation has been added
        self.tasks[0].refresh()
        annotation = self.tasks[0]['annotations']
        assert annotation == []

        # Assert that proper feedback has been shown
        self.command('messages', regex="Input must be provided.")


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
        self.client.feedkeys(":TaskWikiAnnotate This is annotation.\\<Enter>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        annotation = self.tasks[0]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == "This is annotation."

        annotation = self.tasks[1]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == "This is annotation."


class TestAnnotateActionRedo(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        # Annotate the first task
        self.command(
            "TaskWikiAnnotate This is annotation.",
            regex="Task \"test task 1\" annotated.$",
            lines=1)

        self.tasks[0].refresh()
        annotation = self.tasks[0]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == "This is annotation."

        # Now also annotate the second task
        self.client.type('j')
        self.command("TaskWikiRedo", regex="Task \"test task 2\" annotated.$",
                     lines=1)


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
        self.client.normal('VG')
        self.client.feedkeys(":TaskWikiDelete\\<Enter>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[1]['status'] == "deleted"
        assert self.tasks[0]['status'] == "deleted"


class TestDeleteActionRedo(IntegrationTest):

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
        # Delete the first task
        self.command(
            "TaskWikiDelete",
            regex="Task \"test task 1\" deleted.$",
            lines=1
        )

        # Now also delete the second task
        self.command(
            "TaskWikiRedo",
            regex="Task \"test task 2\" deleted.$",
            lines=1
        )

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['status'] == "deleted"
        assert self.tasks[1]['status'] == "deleted"


class TestInfoAction(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.command("TaskWikiInfo")

        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer info")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Name', 'Value'])
        data = r'\s*'.join(['Description', 'test task 1'])
        data2 = r'\s*'.join(['Status', 'Pending'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(data, output, re.MULTILINE)
        assert re.search(data2, output, re.MULTILINE)


class TestInfoActionTriggeredByEnter(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('1gg')
        self.client.feedkeys("\\<CR>")
        self.client.eval('0')  # wait for command completion

        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer info")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Name', 'Value'])
        data = r'\s*'.join(['Description', 'test task 1'])
        data2 = r'\s*'.join(['Status', 'Pending'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(data, output, re.MULTILINE)
        assert re.search(data2, output, re.MULTILINE)


class TestInfoActionNotTriggeredByEnterOnLink(IntegrationTest):

    viminput = """
    * [ ] [[link task]] 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="[[link task]] 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('1gg')
        self.client.type('10l')
        self.client.feedkeys("\\<CR>")
        self.client.eval('0')  # wait for command completion

        # Make sure we have been sent to a new buffer
        output = '\n'.join(self.read_buffer())

        assert not self.py("print(vim.current.buffer)", silent=False).startswith("<buffer info")
        assert not output


class TestInfoActionMoved(IntegrationTest):

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
        self.command("TaskWikiInfo")

        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer info")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Name', 'Value'])
        data = r'\s*'.join(['Description', 'test task 2'])
        data2 = r'\s*'.join(['Status', 'Pending'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(data, output, re.MULTILINE)
        assert re.search(data2, output, re.MULTILINE)


class TestInfoActionRange(IntegrationTest):

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
        self.client.feedkeys(":TaskWikiInfo\\<Enter>")
        self.client.eval('0')  # wait for command completion

        assert self.py("print(vim.current.buffer)", silent=False).startswith("<buffer info")
        output = '\n'.join(self.read_buffer())

        header = r'\s*'.join(['Name', 'Value'])
        data = r'\s*'.join(['Description', 'test task 1'])
        data2 = r'\s*'.join(['Status', 'Pending'])

        assert re.search(header, output, re.MULTILINE)
        assert re.search(data, output, re.MULTILINE)
        assert re.search(data2, output, re.MULTILINE)


class TestLinkAction(IntegrationTest):

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
            "TaskWikiLink",
            regex="Task \"test task 1\" linked.$",
            lines=1)

        backlink = "wiki: {0}".format(self.filepath)

        self.tasks[0].refresh()
        annotation = self.tasks[0]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == backlink


class TestLinkActionMoved(IntegrationTest):

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
            "TaskWikiLink",
            regex="Task \"test task 2\" linked.$",
            lines=1)

        backlink = "wiki: {0}".format(self.filepath)

        self.tasks[1].refresh()
        annotation = self.tasks[1]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == backlink


class TestLinkActionRange(IntegrationTest):

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
        self.client.feedkeys(":TaskWikiLink\\<Enter>")
        self.client.eval('0')  # wait for command completion

        backlink = "wiki: {0}".format(self.filepath)

        for task in self.tasks:
            task.refresh()

        annotation = self.tasks[0]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == backlink

        annotation = self.tasks[1]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == backlink


class TestLinkActionRedo(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        # Link the first task
        self.command(
            "TaskWikiLink",
            regex="Task \"test task 1\" linked.$",
            lines=1
        )

        # Now also link the second task
        self.client.type('j')
        self.command(
            "TaskWikiRedo",
            regex="Task \"test task 2\" linked.$",
            lines=1
        )

        backlink = "wiki: {0}".format(self.filepath)

        # Assert the backlink on the first task
        self.tasks[0].refresh()
        annotation = self.tasks[0]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == backlink

        # Assert the backlink on the second task
        self.tasks[1].refresh()
        annotation = self.tasks[1]['annotations']
        assert annotation != []
        assert annotation[0]['description'] == backlink


class TestStartAction(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [S] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.command(
            "TaskWikiStart",
            regex="Task \"test task 1\" started.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert (now - self.tasks[0]['start']).total_seconds() < 5
        assert (self.tasks[0]['start'] - now).total_seconds() < 5

        assert self.tasks[1]['start'] == None


class TestStartActionMoved(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [S] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('2gg')
        self.command(
            "TaskWikiStart",
            regex="Task \"test task 2\" started.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert (now - self.tasks[1]['start']).total_seconds() < 5
        assert (self.tasks[1]['start'] - now).total_seconds() < 5

        assert self.tasks[0]['start'] == None


class TestStartActionRange(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [S] test task 1  #{uuid}
    * [S] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.client.normal('VG')
        self.client.feedkeys(":TaskWikiStart\\<Enter>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert (now - self.tasks[0]['start']).total_seconds() < 5
        assert (self.tasks[0]['start'] - now).total_seconds() < 5

        assert (now - self.tasks[1]['start']).total_seconds() < 5
        assert (self.tasks[1]['start'] - now).total_seconds() < 5


class TestStartActionRedo(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [S] test task 1  #{uuid}
    * [S] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        # Start the first task
        self.command(
            "TaskWikiStart",
            regex="Task \"test task 1\" started.$",
            lines=1
        )

        # Now also start the second task
        self.client.type('j')
        self.command(
            "TaskWikiRedo",
            regex="Task \"test task 2\" started.$",
            lines=1
        )

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert (now - self.tasks[0]['start']).total_seconds() < 5
        assert (self.tasks[0]['start'] - now).total_seconds() < 5

        assert (now - self.tasks[1]['start']).total_seconds() < 5
        assert (self.tasks[1]['start'] - now).total_seconds() < 5


class TestStopAction(IntegrationTest):

    viminput = """
    * [S] test task 1  #{uuid}
    * [S] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [S] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", start="now"),
        dict(description="test task 2", start="now"),
    ]

    def execute(self):
        self.command(
            "TaskWikiStop",
            regex="Task \"test task 1\" stopped.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert (now - self.tasks[1]['start']).total_seconds() < 30
        assert (self.tasks[1]['start'] - now).total_seconds() < 30

        assert self.tasks[0]['start'] == None


class TestStopActionMoved(IntegrationTest):

    viminput = """
    * [S] test task 1  #{uuid}
    * [S] test task 2  #{uuid}
    """

    vimoutput = """
    * [S] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", start="now"),
        dict(description="test task 2", start="now"),
    ]

    def execute(self):
        self.client.type('2gg')
        self.command(
            "TaskWikiStop",
            regex="Task \"test task 2\" stopped.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert (now - self.tasks[0]['start']).total_seconds() < 30
        assert (self.tasks[0]['start'] - now).total_seconds() < 30

        assert self.tasks[1]['start'] == None


class TestStopActionRange(IntegrationTest):

    viminput = """
    * [S] test task 1  #{uuid}
    * [S] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", start="now"),
        dict(description="test task 2", start="now"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.client.normal('VG')
        self.client.feedkeys(":TaskWikiStop\\<Enter>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert self.tasks[0]['start'] == None
        assert self.tasks[1]['start'] == None


class TestStopActionRedo(IntegrationTest):

    viminput = """
    * [S] test task 1  #{uuid}
    * [S] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", start="now"),
        dict(description="test task 2", start="now"),
    ]

    def execute(self):
        self.command(
            "TaskWikiStop",
            regex="Task \"test task 1\" stopped.$",
            lines=1
        )

        # Now also stop the second task
        self.client.type('j')
        self.command(
            "TaskWikiRedo",
            regex="Task \"test task 2\" stopped.$",
            lines=1
        )

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert self.tasks[0]['start'] == None
        assert self.tasks[1]['start'] == None


class TestModAction(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.command(
            "TaskWikiMod project:Home",
            regex="Modified 1 task.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['project'] == "Home"
        assert self.tasks[1]['project'] == None


class TestModActionRedo(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.command(
            "TaskWikiMod project:Home",
            regex="Modified 1 task.$",
            lines=1
        )

        # Now also modify the second task
        self.client.type('j')
        self.command(
            "TaskWikiRedo",
            regex="Modified 1 task.$",
            lines=1
        )

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['project'] == "Home"
        assert self.tasks[1]['project'] == "Home"


class TestModInteractiveAction(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.feedkeys(":TaskWikiMod\\<Enter>")
        self.client.feedkeys("+work\\<Enter>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['tags'] == set(["work"])
        assert self.tasks[1]['tags'] == set()


class TestModInteractiveActionRedo(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.feedkeys(":TaskWikiMod\\<Enter>")
        self.client.feedkeys("+work\\<Enter>")
        self.client.eval('0')  # wait for command completion

        # Now also modify the second task
        self.client.type('j')
        self.command(
            "TaskWikiRedo",
            regex="Modified 1 task.$",
            lines=1
        )

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['tags'] == set(["work"])
        assert self.tasks[1]['tags'] == set(["work"])


class TestModVisibleAction(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        today = local_zone.localize(
            datetime.now().replace(hour=0,minute=0,second=0,microsecond=0))

        self.command(
            "TaskWikiMod due:today",
            regex="Modified 1 task.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['due'] == today
        assert self.tasks[1]['due'] == None

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"


class TestModActionMoved(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('2gg')
        self.command(
            "TaskWikiMod project:Home",
            regex="Modified 1 task.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['project'] == None
        assert self.tasks[1]['project'] == "Home"


class TestModActionRange(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.client.normal('VG')
        self.client.feedkeys(":TaskWikiMod project:Home\\<Enter>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"

        assert self.tasks[0]['project'] == "Home"
        assert self.tasks[1]['project'] == "Home"


class TestDoneAction(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [X] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.command(
            "TaskWikiDone",
            regex="Task \"test task 1\" completed.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "completed"
        assert self.tasks[1]['status'] == "pending"

        assert (now - self.tasks[0]['end']).total_seconds() < 5
        assert (self.tasks[0]['end'] - now).total_seconds() < 5

        assert self.tasks[1]['end'] == None

class TestDoneNoSelected(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}

    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}

    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('2gg')
        self.command(
            "TaskWikiDone",
            regex="No tasks selected.",
            lines=1)

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "pending"


class TestDoneActionMoved(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [X] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.type('2gg')
        self.command(
            "TaskWikiDone",
            regex="Task \"test task 2\" completed.$",
            lines=1)

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "pending"
        assert self.tasks[1]['status'] == "completed"

        assert (now - self.tasks[1]['end']).total_seconds() < 5
        assert (self.tasks[1]['end'] - now).total_seconds() < 5

        assert self.tasks[0]['end'] == None


class TestDoneActionRange(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [X] test task 1  #{uuid}
    * [X] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.client.normal('VG')
        self.client.feedkeys(":TaskWikiDone\\<Enter>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "completed"
        assert self.tasks[1]['status'] == "completed"

        assert (now - self.tasks[0]['end']).total_seconds() < 5
        assert (self.tasks[0]['end'] - now).total_seconds() < 5

        assert (now - self.tasks[1]['end']).total_seconds() < 5
        assert (self.tasks[1]['end'] - now).total_seconds() < 5


class TestDoneActionRedo(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [X] test task 1  #{uuid}
    * [X] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.command(
            "TaskWikiDone",
            regex="Task \"test task 1\" completed.$",
            lines=1
        )

        # Now also finish the second task
        self.client.type('j')
        self.command(
            "TaskWikiRedo",
            regex="Task \"test task 2\" completed.$",
            lines=1
        )

        for task in self.tasks:
            task.refresh()

        now = local_zone.localize(datetime.now())

        assert self.tasks[0]['status'] == "completed"
        assert self.tasks[1]['status'] == "completed"

        assert (now - self.tasks[0]['end']).total_seconds() < 5
        assert (self.tasks[0]['end'] - now).total_seconds() < 5

        assert (now - self.tasks[1]['end']).total_seconds() < 5
        assert (self.tasks[1]['end'] - now).total_seconds() < 5


class TestSortManually(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 2  #{uuid}
    * [ ] test task 1  #{uuid}
    """

    tasks = [
        dict(description="test task 1"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.client.normal('VG')
        self.client.feedkeys(":TaskWikiSort description-\\<Enter>")

class TestSelectAfterBufferSwitch(IntegrationTest):

    viminput = """
    * [ ] test task  #{uuid}
    """

    vimoutput = """
    * [ ] test task  #{uuid}
    """

    tasks = [
        dict(description="test task"),
    ]

    def execute(self):
        self.command('w', silent=False)
        self.command('split testwiki2.txt', silent=False)
        self.command('q!')
        self.client.normal('1gg')
        self.command("TaskWikiMod project:Home", regex="Modified 1 task.")

        self.tasks[0].refresh()
        assert self.tasks[0]['project'] == "Home"
