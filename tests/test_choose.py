# -*- coding: utf-8 -*-
from tests.base import IntegrationTest


class TestChooseProject(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", project="Home"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('2gg')
        self.command("TaskWikiChooseProject")
        self.client.normal('5gg')
        self.client.feedkeys("\\<CR>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['project'] == "Home"
        assert self.tasks[1]['project'] == "Home"


class TestChooseProjectUnset(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", project="Home"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.command("TaskWikiChooseProject")
        self.client.normal('4gg')
        self.client.feedkeys("\\<CR>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['project'] == None
        assert self.tasks[1]['project'] == None


class TestChooseProjectCanceled(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", project="Home"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.command("TaskWikiChooseProject")
        self.client.normal('4gg')
        self.client.feedkeys("q")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['project'] == "Home"
        assert self.tasks[1]['project'] == None


class TestChooseTag(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", tags=["home"]),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('2gg')
        self.command("TaskWikiChooseTag")
        self.client.normal('4gg')
        self.client.feedkeys("\\<CR>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['tags'] == set(["home"])
        assert self.tasks[1]['tags'] == set(["home"])


class TestChooseTagCancelled(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", tags=["home"]),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.command("TaskWikiChooseTag")
        self.client.normal('4gg')
        self.client.feedkeys("q")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['tags'] == set(["home"])
        assert self.tasks[1]['tags'] == set()


class TestChooseTagNoSelected(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", tags=["home"]),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        self.command("TaskWikiChooseTag")
        self.client.normal('5gg')  # No task on the 5th row
        self.client.feedkeys("\\<CR>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['tags'] == set(["home"])
        assert self.tasks[1]['tags'] == set()


class TestChooseProjectUnicode(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", project=u"Hôme"),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('2gg')
        self.command("TaskWikiChooseProject")
        self.client.normal('5gg')
        self.client.feedkeys("\\<CR>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['project'] == u"Hôme"
        assert self.tasks[1]['project'] == u"Hôme"


class TestChooseTagUnicode(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", tags=[u"hôme"]),
        dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('2gg')
        self.command("TaskWikiChooseTag")
        self.client.normal('4gg')
        self.client.feedkeys("\\<CR>")
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['tags'] == set([u"hôme"])
        assert self.tasks[1]['tags'] == set([u"hôme"])
