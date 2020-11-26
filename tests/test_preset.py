from tests.base import MultiSyntaxIntegrationTest


class TestPresetDefaults(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER3(Work tasks || +work)
    * [ ] This is a test task
    """

    vimoutput = """
    HEADER3(Work tasks || +work)
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one task with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['work'])


class TestPresetHierarchy(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || +work)
    HEADER3(Hard work tasks || +hard)
    HEADER3(Easy work tasks || +easy)
    * [ ] This is a test task
    """

    vimoutput = """
    HEADER2(Work tasks || +work)
    HEADER3(Hard work tasks || +hard)
    HEADER3(Easy work tasks || +easy)
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['work', 'easy'])


class TestPresetSeparateDefaults(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER1(Work tasks || +work or +play || +work)
    * [ ] This is a test task
    """

    vimoutput = """
    HEADER1(Work tasks || +work or +play || +work)
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['work'])


class TestPresetNestedDefaults(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || +work)
    HEADER3(Hard work || +hard)
    * [ ] This is a test task
    """

    vimoutput = """
    HEADER2(Work tasks || +work)
    HEADER3(Hard work || +hard)
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['work', 'hard'])


class TestPresetViewport(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || +work)
    HEADER3(Hard work | +hard)
    """

    vimoutput = """
    HEADER2(Work tasks || +work)
    HEADER3(Hard work | +hard)
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


class TestPresetIgnoreViewport(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks | +work)
    HEADER3(Hard work || +hard)
    * [ ] This is a test task
    """

    vimoutput = """
    HEADER2(Work tasks | +work)
    HEADER3(Hard work || +hard)
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['hard'])


class TestPresetViewportDefaultsYesNo(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || project:Work or project:Play || project:Work)
    HEADER3(Hard work | +hard)
    * [ ] This is a test task
    """

    vimoutput = """
    HEADER2(Work tasks || project:Work or project:Play || project:Work)
    HEADER3(Hard work | +hard)
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['hard'])
        assert task['project'] == 'Work'


class TestPresetViewportDefaultsNoYes(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || project:Work)
    HEADER3(Hard work | +hard or +easy | +hard)
    * [ ] This is a test task
    """

    vimoutput = """
    HEADER2(Work tasks || project:Work)
    HEADER3(Hard work | +hard or +easy | +hard)
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['hard'])
        assert task['project'] == 'Work'


class TestPresetViewportDefaultsYesYes(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || project:Work or project:Play || project:Work)
    HEADER3(Hard work | +hard or +easy | +hard)
    * [ ] This is a test task
    """

    vimoutput = """
    HEADER2(Work tasks || project:Work or project:Play || project:Work)
    HEADER3(Hard work | +hard or +easy | +hard)
    * [ ] This is a test task  #{uuid}
    """

    def execute(self):
        self.command('w', regex='written$', lines=1)

        # Check that only one tasks with this description exists
        assert len(self.tw.tasks.pending()) == 1

        task = self.tw.tasks.pending()[0]
        assert task['tags'] == set(['hard'])
        assert task['project'] == 'Work'


class TestPresetDefaultPreservesTags(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || +work)
    HEADER3(Work tasks | +hard)
    * [ ] hard task
    """

    vimoutput = """
    HEADER2(Work tasks || +work)
    HEADER3(Work tasks | +hard)
    * [ ] hard task  #{uuid}
    """

    def execute(self):
        self.command("w", regex="written$", lines=1)

        # Make sure both tags were preserved
        task = self.tw.tasks.pending()[0]
        assert task['description'] == 'hard task'
        assert task['status'] == 'pending'
        assert task['tags'] == set(['work', 'hard'])


class TestPresetExpires(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || !2020-01-01)
    HEADER3(Work tasks |)
    * [ ] old task
    """

    vimoutput = """
    HEADER2(Work tasks || !2020-01-01)
    HEADER3(Work tasks |)
    * [ ] old task
    """

    tasks = [
        dict(description="task 1"),
        dict(description="task 2"),
        dict(description="task 3"),
        dict(description="task 4"),
    ]

    def execute(self):
        # Generate the tasks
        self.command("w", regex="written$", lines=1)


class TestPresetExpiresWithOverridingViewport(MultiSyntaxIntegrationTest):

    viminput = """
    HEADER2(Work tasks || !2020-01-01)
    HEADER3(Work tasks | $T !2500-01-01)
    * [ ] old task
    """

    vimoutput = """
    HEADER2(Work tasks || !2020-01-01)
    HEADER3(Work tasks | $T !2500-01-01)
    * [ ] old task  #{uuid}
    * [ ] task 1  #{uuid}
    * [ ] task 2  #{uuid}
    * [ ] task 3  #{uuid}
    * [ ] task 4  #{uuid}
    """

    tasks = [
        dict(description="task 1"),
        dict(description="task 2"),
        dict(description="task 3"),
        dict(description="task 4"),
    ]

    def execute(self):
        # Define the ordering T
        self.command('let g:taskwiki_sort_orders={"T": "description"}')

        # Generate the tasks
        self.command("w", regex="written$", lines=1)
