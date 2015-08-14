## Taskwiki

_Proper project management in vim.
Standing on the shoulders of vimwiki and Taskwarrior_

[![Travis build status](https://travis-ci.org/tbabej/taskwiki.svg?branch=master)](https://travis-ci.org/tbabej/taskwiki)
[![Coverage Status](https://coveralls.io/repos/tbabej/taskwiki/badge.svg?branch=master)](https://coveralls.io/r/tbabej/taskwiki?branch=master)
[![Code Health](https://landscape.io/github/tbabej/taskwiki/master/landscape.svg?style=flat)](https://landscape.io/github/tbabej/taskwiki/master)

         a         |_   _|_ _ ___| | _\ \      / (_) | _(_)         a         ~
    command-line     | |/ _` / __| |/ /\ \ /\ / /| | |/ / |   personal wiki   ~
     todo list       | | (_| \__ \   <  \ V  V / | |   <| |      for vim      ~
                     |_|\__,_|___/_|\_\  \_/\_/  |_|_|\_\_|                   ~

### Installation

#### Make sure you satisfy the requirements

* Vim 7.4 or newer, compiled with +python
* [Vimwiki](https://github.com/vimwiki/vimwiki/tree/dev) (the dev branch)

        git clone https://github.com/vimwiki/vimwiki ~/.vim/bundle/ --branch dev

* [Taskwarrior](http://taskwarrior.org) (version 2.4.0 or newer)
- install either from [sources](http://taskwarrior.org/download/)
or using your [package manager](http://taskwarrior.org/download/#dist)

        sudo dnf install task

* [tasklib](https://github.com/tbabej/tasklib/tree/develop) (the develop branch)
- Python library for Taskwarrior.

        sudo pip install --upgrade git+git://github.com/tbabej/tasklib@develop

#### Install taskwiki

Using pathogen (or similiar vim plugin manager), the taskwiki install is
as simple as:

    git clone https://github.com/tbabej/taskwiki ~/.vim/bundle/taskwiki

However, make sure your box satisfies the requirements stated above.

#### Optional enhancements

The following optional plugins enhance and integrate with TaskWiki.
At very least,I'd recommend the AnsiEsc plugin - Taskwarrior
charts are much more fun when they're colorful!

* [vim-plugin-AnsiEsc](https://github.com/powerman/vim-plugin-AnsiEsc)
adds color support in charts.

        git clone https://github.com/powerman/vim-plugin-AnsiEsc ~/.vim/bundle/

* [tagbar](https://github.com/majutsushi/tagbar)
provides taskwiki file navigation.

        git clone https://github.com/majutsushi/tagbar ~/.vim/bundle/

* [vim-taskwarrior](https://github.com/farseer90718/vim-taskwarrior)
enables grid view.

        git clone https://github.com/farseer90718/vim-taskwarrior ~/.vim/bundle/

### How it works

Taskwiki enhances simple vimwiki task lists by storing the task metadata in
Taskwarrior. Taskwarrior uses plaintext data files as a backend, and taskwiki
uses Taskwarrior as a backend. This allows taskwiki to leverage its powerful
features, such as filtering, recurrent tasks, user defined attributes or hooks.

### Features

- ViewPorts: a vimwiki header with a task query (filter) embedded, generate
a corresponding list of tasks. These tasks can be modified and changes
will be synced back to task data.  A ViewPort heading looks like this:

<pre>
    == Project Foo Tasks | +PENDING project:foo | +bar pri:H ==
         title ^^^            filter ^^^             ^^^ user defaults
</pre>
title can be any text, and the filter elements are concealed in normal mode.

- Individual Todos: tasks can be used anywhere in a vimwiki, looking like:

<pre>
* [ ] Install TaskWiki plugin
</pre>

and when adding a new task, any other metadata can be added after "--" like

<pre>
* [ ] test taskwiki todos and viewports -- proj:tw.wiki +foo due:tomorrow
</pre>

and the task will be synced with the task data on saving. After syncing,
all tasks end with a concealed uuid (eg.  #541c5b57) don't edit this!

- Task Info: hitting <CR> with the cursor over a task shows all task info.

- Reports: burndown, calendar, history, projects, summary, stats and tags
reports can all be invoked, opening in a split window.

- Grid view: the TaskWikiGrid command will open a new buffer with a grid
view of task details, of the nearest ViewPort (using vim-taskwarrior)

- Back-links: The command TaskWikiLink will add an annotation to the selected
task(s) with the ~/path/to/file.wiki

- Tests: TaskWiki is well tested in development to ensure data integrity.
    **DISCLAIMER** This is free software, it comes with absolutely NO
    warranty and no promise of fitness for any purpose! (back up your data!)

### Commands
* TaskWikiBurndown(Daily, Monthly, Weekly)
* TaskWikiCalendar
* TaskWikiChooseProject
* TaskWikiChooseTag
* TaskWikiDelete
* TaskWikiGhistory(Annual, Monthly)
* TaskWikiHistory(Annual, Monthly)
* TaskWikiInfo
* TaskWikiInspect
* TaskWikiLink
* TaskWikiMod
* TaskWikiProjects
* TaskWikiProjectsSummary
* TaskWikiStart
* TaskWikiStats
* TaskWikiStop
* TaskWikiTags

see more in doc/taskwiki.txt. After installing, run :helptags and then :he taskwiki

### Credits

Authored by Tomas Babej

Inspired by [vimwiki-tasks plugin](https://github.com/teranex/vimwiki-tasks).

### Contributing

Clone, fork, contribute and learn more at https://github.com/tbabej/taskwiki

Good ideas, well formed bug reports and thoughtful pull-requests welcome.


