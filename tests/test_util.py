import sys
from tests.base import MockVim

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
        assert util.tw_modstring_to_kwargs("") == {}
        assert util.tw_modstring_to_kwargs("project:Random")  == {"project":"Random"}
        assert util.tw_modstring_to_kwargs("project:Random area:admin")  == {"project":"Random", "area":"admin"}
        assert util.tw_modstring_to_kwargs("project:Random +test")  == {"project":"Random", "tags":["test"]}
        assert util.tw_modstring_to_kwargs("project:Random +test +home")  == {"project":"Random", "tags":["test", "home"]}
        assert util.tw_modstring_to_kwargs("project:'Random +test'")  == {"project":"Random +test"}

    def test_modstring_to_kwargs_with_simple_tag(self):
        assert util.tw_modstring_to_kwargs("+test ") == {"tags":["test"]}

    def test_modstring_to_kwargs_with_removal(self):
        assert util.tw_modstring_to_kwargs("project: +work") == {"tags":["work"], "project":None}

    def test_modstring_to_kwargs_with_spaces(self):
        assert util.tw_modstring_to_kwargs("project:Random area:admin") == {"project":"Random", "area":"admin"}
        assert util.tw_modstring_to_kwargs("project:Random +test") == {"project":"Random", "tags":["test"]}

    def test_modstring_to_kwargs_overriding(self):
        assert util.tw_modstring_to_kwargs("project:Random project:Home") == {"project":"Home"}
        assert util.tw_modstring_to_kwargs("project:Random area:admin area:school") == {"project":"Random", "area":"school"}

    def test_modstring_to_kwargs_ignore_modifiers(self):
        assert util.tw_modstring_to_kwargs("project.is:Random due:now") == {"due":"now"}
        assert util.tw_modstring_to_kwargs("project:Random due.before:now area:admin") == {"project":"Random", "area":"admin"}

    def test_modstring_to_kwargs_ignore_virtual_tags(self):
        assert util.tw_modstring_to_kwargs("project:Random +PENDING") == {"project":"Random"}
        assert util.tw_modstring_to_kwargs("project:Random -DELETED area:admin") == {"project":"Random", "area":"admin"}
