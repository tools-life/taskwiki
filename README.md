## Taskwiki

_Use [taskwarrior](http://taskwarrior.org) task-management in [vimwiki](https://github.com/vimwiki/vimwiki/tree/dev) files_

![taskwiki demo](http://picpaste.com/pics/wz8U2Qq9.1430094451.gif)

[![Travis build status](https://travis-ci.org/tbabej/taskwiki.svg?branch=master)](https://travis-ci.org/tbabej/taskwiki)
[![Coverage Status](https://coveralls.io/repos/tbabej/taskwiki/badge.svg?branch=master)](https://coveralls.io/r/tbabej/taskwiki?branch=master)
[![Code Health](https://landscape.io/github/tbabej/taskwiki/master/landscape.svg?style=flat)](https://landscape.io/github/tbabej/taskwiki/master)

<pre>
                   _____         _   __        ___ _    _                    ~
        a         |_   _|_ _ ___| | _\ \      / (_) | _(_)         a         ~
   command-line     | |/ _` / __| |/ /\ \ /\ / /| | |/ / |   personal wiki   ~
    todo list       | | (_| \__ \   <  \ V  V / | |   <| |      for vim      ~
     manager        |_|\__,_|___/_|\_\  \_/\_/  |_|_|\_\_|                   ~
                                                                             ~
==============================================================================
QUICK-REFERENCE   --   use  "leader" + t and one of:                          

| a  annotate         | C  calendar       | Ga ghistory annual | p  projects |
| bd burndown daily   | d  done           | hm history month   | s  summary  |
| bw burndown weekly  | D  delete         | ha history annual  | S  stats    |
| bm burndown monthly | e  edit           | i  (or  CR ) info  | t  tags     |
| cp choose project   | g  grid           | l  back-link       | +  start    |
| cp choose tag       | Gm ghistory month | m  modify          | -  stop     |

</pre>

### Requirements

* vim v7.4+
   (with python bindings) (see :version, within vim, to see what version you are using)
* [vimwiki](https://github.com/vimwiki/vimwiki/tree/dev)
   (the dev branch)
* [taskwarrior](http://taskwarrior.org) 
   (version 2.4.3 or newer)
* [tasklib](https://github.com/tbabej/tasklib/tree/develop)
   (the develop branch) taskwarrior python bindings

### Enhancements
* [vim-plugin-AnsiEsc](https://github.com/powerman/vim-plugin-AnsiEsc) for color support
* [tagbar](https://github.com/majutsushi/tagbar) for taskwiki file navigation
* [vim-taskwarrior](https://github.com/farseer90718/vim-taskwarrior) for grid view

### Install

- plugins the vim way: http://vimdoc.sourceforge.net/htmldoc/usr_05.html#05.4
- plugins the easy way: https://github.com/tpope/vim-pathogen. Other "vim plugin managers" will probably work, but have not been tested

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
* TaskWikiDelete
* TaskWikiGhistory(Annual, Monthly)
* TaskWikiHistory(Annual, Monthly)
* TaskWikiInfo
* TaskWikiLink
* TaskWikiMod
* TaskWikiProjects
* TaskWikiProjectsSummary
* TaskWikiStart
* TaskWikiStats
* TaskWikiStop
* TaskWikiTags

### Credits

Inspired by vimwiki-tasks plugin.

see more in doc/taskwiki.txt

