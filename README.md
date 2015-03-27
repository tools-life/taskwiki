## Taskwiki

_Use [taskwarrior](http://taskwarrior.org) task-management in [vimwiki](https://github.com/vimwiki/vimwiki/tree/dev) files_

[![Travis build status](https://travis-ci.org/tbabej/taskwiki.svg?branch=master)](https://travis-ci.org/tbabej/taskwiki)
[![Coverage Status](https://coveralls.io/repos/tbabej/taskwiki/badge.svg?branch=master)](https://coveralls.io/r/tbabej/taskwiki?branch=master)
[![Code Health](https://landscape.io/github/tbabej/taskwiki/master/landscape.svg?style=flat)](https://landscape.io/github/tbabej/taskwiki/master)

This is a vim plugin, which aims to provide integration between vimwiki and taskwarrior. It extends vimwiki by replacing the rudimentary Todo lists, and provides bidirecitonal synchronization between TaskWarrior and Vimwiki files.

This allows you to define your tasks in your vimwiki files and still have processing power of TaskWarrior at your disposal. If you use taskwarrior, and you use vimwiki, you want this plugin.

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

### Install

Install this plugin like any other; using pathogen or copying the files and folders to your vim directories.

### Features

#### ViewPorts
  * Create a heading that contains a taskwarrior filter, that looks like this;
<pre>
== Foo task list | project:foo ==
</pre>
and after saving the file, TaskWiki generates a full list of matching tasks.

#### Define defaults, by extending that heading like this;
<pre>
== Foo task list | project:foo | project:foo +bar ==
</pre>
so that any tasks created under this heading will automatically be assigned "project:foo +bar"

#### Bidirecitonal updates:
  * TW -> Vimwiki (upon file loading)
  * Vimwiki -> TW (upon saving)

#### Updated information
  * Description
  * Task status (completion)
  * Dependency sets (sets subtasks as dependencies of parent tasks)
  * Due dates
  * Priority

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

### Planned features
* Updating
  * Removals from dependency sets

### Credits

Inspired by vimwiki-tasks plugin.
