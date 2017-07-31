from tests.base import IntegrationTest
from time import sleep


class TestPresetDefaults(IntegrationTest):

    viminput = """
    === Work tasks || +work ===
    * [ ] This is a test task
    """

    vimoutput = """
    === Work tasks || +work ===
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['work'])


class TestPresetHierarchy(IntegrationTest):

    viminput = """
    == Work tasks || +work ==
    === Hard work tasks || +hard ===
    === Easy work tasks || +easy ===
    * [ ] This is a test task
    """

    vimoutput = """
    == Work tasks || +work ==
    === Hard work tasks || +hard ===
    === Easy work tasks || +easy ===
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['work', 'easy'])


class TestPresetSeparateDefaults(IntegrationTest):

    viminput = """
    = Work tasks || +work or +play || +work =
    * [ ] This is a test task
    """

    vimoutput = """
    = Work tasks || +work or +play || +work =
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['work'])


class TestPresetNestedDefaults(IntegrationTest):

    viminput = """
    == Work tasks || +work ==
    === Hard work || +hard ===
    * [ ] This is a test task
    """

    vimoutput = """
    == Work tasks || +work ==
    === Hard work || +hard ===
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['work', 'hard'])


class TestPresetViewport(IntegrationTest):

    viminput = """
    == Work tasks || +work ==
    === Hard work | +hard ===
    """

    vimoutput = """
    == Work tasks || +work ==
    === Hard work | +hard ===
    * [ ] tag hard work task  #{uuid}
    """

    tasks = [
        dict(description="tag hard work task", tags=['work', 'hard']),
        dict(description="tag easy work task", tags=['work', 'easy']),
        dict(description="tag any work task", tags=['work']),
        dict(description="tag no work task", tags=['play', 'hard'])
    ]

    def execute(self):
        self.command("w", regex="written$", lines=1)


class TestPresetIgnoreViewport(IntegrationTest):

    viminput = """
    == Work tasks | +work ==
    === Hard work || +hard ===
    * [ ] This is a test task
    """

    vimoutput = """
    == Work tasks | +work ==
    === Hard work || +hard ===
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['hard'])


class TestPresetViewportDefaultsYesNo(IntegrationTest):

    viminput = """
    == Work tasks || project:Work or project:Play || project:Work ==
    === Hard work | +hard ===
    * [ ] This is a test task
    """

    vimoutput = """
    == Work tasks || project:Work or project:Play || project:Work ==
    === Hard work | +hard ===
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['hard'])
        assert task['project'] == 'Work'


class TestPresetViewportDefaultsNoYes(IntegrationTest):

    viminput = """
    == Work tasks || project:Work ==
    === Hard work | +hard or +easy | +hard ===
    * [ ] This is a test task
    """

    vimoutput = """
    == Work tasks || project:Work ==
    === Hard work | +hard or +easy | +hard ===
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['hard'])
        assert task['project'] == 'Work'


class TestPresetViewportDefaultsYesYes(IntegrationTest):

    viminput = """
    == Work tasks || project:Work or project:Play || project:Work ==
    === Hard work | +hard or +easy | +hard ===
    * [ ] This is a test task
    """

    vimoutput = """
    == Work tasks || project:Work or project:Play || project:Work ==
    === Hard work | +hard or +easy | +hard ===
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['hard'])
        assert task['project'] == 'Work'


class TestPresetDefaultPreservesTags(IntegrationTest):

    viminput = """
    == Work tasks || +work ==
    === Work tasks | +hard ===
    * [ ] hard task
    """

    vimoutput = """
    == Work tasks || +work ==
    === Work tasks | +hard ===
    * [ ] hard task  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)
        sleep(0.5)

        # Make sure both tags were preserved
        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'hard task'
        assert task['status'] == 'pending'
        assert task['tags'] == set(['work', 'hard'])
