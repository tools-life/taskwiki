## Taskwiki

_Use [taskwarrior](http://taskwarrior.org) task-management in [vimwiki](https://github.com/vimwiki/vimwiki/tree/dev)_

This is a vim plugin, which aims to provide a integration between vim and taskwarrior. It extends vimwiki plugin, replacing the rudimentary Todo lists, and provides bidirecitonal synchronization between TaskWarrior and Vimwiki files.

This allows you to define your tasks in your vimwiki files and still have processing power of TaskWarrior at your disposal. If you use taskwarrior, and you use vimwiki, you want this plugin.

### Requirements

* vim v7.4+
   (with python bindings) (see :version, within vim, to see what version you are using)
* [vimwiki](https://github.com/vimwiki/vimwiki/tree/dev)
   (the dev version)
* [taskwarrior](http://taskwarrior.org)
   version (2.2.0 or newer)
* tasklib
   (the "develop" version)

### Install

Install this plugin like any other; using pathogen or copying the files and folders to your vim directories.

### Features

* ViewPorts
  * Create a header that contains a taskwarrior filter, and after saving the file, TaskWiki generates a full list of matching tasks.
  * Define defaults, so that any tasks created under this header will automatically be assigned these defaults
* Bidirecitonal updates:
  * TW -> Vimwiki (upon file loading)
  * Vimwiki -> TW (upon saving)
* Updated information
  * Description
  * Task status (completion)
  * Dependency sets (sets subtasks as dependencies of parent tasks)
  * Due dates
  * Priority

### Planned features
* Updating
  * Task deletion (when removed from the Vimwiki file, if it was there previously)
  * Removals from dependency sets

### Credits

Inspired by vimwiki-tasks plugin.
