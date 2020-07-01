# -*- coding: utf-8 -*-
from tests.base import IntegrationTest


class TestDefaultMapping(IntegrationTest):

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
        self.client.feedkeys(r'\\td')
        self.client.normal('2gg')
        self.client.normal('V')
        self.client.feedkeys(r'\\td')
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()


class TestSuppressedMapping(IntegrationTest):

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

    def configure_global_variables(self):
        super(TestSuppressedMapping, self).configure_global_variables()
        self.command('let g:taskwiki_suppress_mappings="yes"')

    def execute(self):
        self.client.normal('1gg')
        self.client.feedkeys(r'\\td')
        self.client.normal('2gg')
        self.client.normal('V')
        self.client.feedkeys(r'\\td')
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()


class TestCustomMapping(IntegrationTest):

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

    def configure_global_variables(self):
        super(TestCustomMapping, self).configure_global_variables()
        self.command('let g:taskwiki_maplocalleader=",t"')

    def execute(self):
        self.client.normal('1gg')
        self.client.feedkeys(',td')
        self.client.normal('2gg')
        self.client.normal('V')
        self.client.feedkeys(',td')
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()


class TestColonRemap(IntegrationTest):

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
        self.command('nnoremap ; :')
        self.command('nnoremap : ;')
        self.command('vnoremap ; :')
        self.command('vnoremap : ;')

        self.client.normal('1gg')
        self.client.feedkeys(r'\\td')
        self.client.normal('2gg')
        self.client.normal('V')
        self.client.feedkeys(r'\\td')
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()


class TestColonRemapWithCustomMap(IntegrationTest):

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

    def configure_global_variables(self):
        super(TestColonRemapWithCustomMap, self).configure_global_variables()
        self.command('let g:taskwiki_maplocalleader=",t"')

    def execute(self):
        self.command('nnoremap ; :')
        self.command('nnoremap : ;')
        self.command('vnoremap ; :')
        self.command('vnoremap : ;')

        self.client.normal('1gg')
        self.client.feedkeys(',td')
        self.client.normal('2gg')
        self.client.normal('V')
        self.client.feedkeys(',td')
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()
