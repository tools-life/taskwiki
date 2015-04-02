import sys

# Mock vim to test vim-nonrelated functions
class MockVim(object):

    def eval(*args, **kwargs):
        return 42

sys.modules['vim'] = MockVim()

from taskwiki import util

class TestParsingModstrings(object):
    def test_modstring_to_args(self):
        assert util.tw_modstring_to_args("") == []
        assert util.tw_modstring_to_args("project:Random") == ["project:Random"]
        assert util.tw_modstring_to_args("project:Random area:admin") == ["project:Random", "area:admin"]
        assert util.tw_modstring_to_args("project:Random +test") == ["project:Random", "+test"]
        assert util.tw_modstring_to_args("project:'Random +test'") == ["project:Random +test"]

    def test_modstring_to_args_with_spaces(self):
        assert util.tw_modstring_to_args("project:Random  +test") == ["project:Random", "+test"]
        assert util.tw_modstring_to_args("project:Random    due:now") == ["project:Random", "due:now"]

    def test_modstring_to_args_with_quotes(self):
        assert util.tw_modstring_to_args('project:"Random test" +test') == ["project:Random test", "+test"]
        assert util.tw_modstring_to_args("project:'Random test' +test") == ["project:Random test", "+test"]

    def test_modstring_to_args_with_nested_quotes(self):
        assert util.tw_modstring_to_args('project:"Random\'test" +test') == ["project:Random'test", "+test"]
        assert util.tw_modstring_to_args("project:'Random\"test' +test") == ["project:Random\"test", "+test"]

    def test_modstring_to_args_with_esacpe(self):
        assert util.tw_modstring_to_args(r'project:Random\ test +test') == ["project:Random test", "+test"]
        assert util.tw_modstring_to_args(r"project:Random\ test +test") == ["project:Random test", "+test"]

    def test_modstring_to_args_with_esacped_escape(self):
        assert util.tw_modstring_to_args(r'project:Random\\ +test') == ['project:Random\\', "+test"]

    def test_modstring_to_args_overriding(self):
        assert util.tw_modstring_to_args("project:Random project:Home") == ["project:Random", "project:Home"]
        assert util.tw_modstring_to_args("project:Random due:now due:today") == ["project:Random", "due:now", "due:today"]

    def test_modstring_to_kwargs(self):
        assert util.tw_modstring_to_kwargs("")[0] == {}
        assert util.tw_modstring_to_kwargs("project:Random")[0]  == {"project":"Random"}
        assert util.tw_modstring_to_kwargs("project:Random area:admin")[0]  == {"project":"Random", "area":"admin"}
        assert util.tw_modstring_to_kwargs("project:Random +test")[0]  == {"project":"Random", "tags":["test"]}
        assert util.tw_modstring_to_kwargs("project:Random +test +home")[0]  == {"project":"Random", "tags":["test", "home"]}
        assert util.tw_modstring_to_kwargs("project:'Random +test'")[0]  == {"project":"Random +test"}

    def test_modstring_to_kwargs_with_simple_tag(self):
        assert util.tw_modstring_to_kwargs("+test ")[0] == {"tags":["test"]}

    def test_modstring_to_kwargs_with_removal(self):
        assert util.tw_modstring_to_kwargs("project: +work")[0] == {"tags":["work"], "project":None}

    def test_modstring_to_kwargs_with_spaces(self):
        assert util.tw_modstring_to_kwargs("project:Random area:admin")[0] == {"project":"Random", "area":"admin"}
        assert util.tw_modstring_to_kwargs("project:Random +test")[0] == {"project":"Random", "tags":["test"]}

    def test_modstring_to_kwargs_overriding(self):
        assert util.tw_modstring_to_kwargs("project:Random project:Home")[0] == {"project":"Home"}
        assert util.tw_modstring_to_kwargs("project:Random area:admin area:school")[0] == {"project":"Random", "area":"school"}

    def test_modstring_to_kwargs_ignore_modifiers(self):
        assert util.tw_modstring_to_kwargs("project.is:Random due:now")[0] == {"due":"now"}
        assert util.tw_modstring_to_kwargs("project:Random due.before:now area:admin")[0] == {"project":"Random", "area":"admin"}

    def test_modstring_to_kwargs_ignore_virtual_tags(self):
        assert util.tw_modstring_to_kwargs("project:Random +PENDING")[0] == {"project":"Random"}
        assert util.tw_modstring_to_kwargs("project:Random -DELETED area:admin")[0] == {"project":"Random", "area":"admin"}
