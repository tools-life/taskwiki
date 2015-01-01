## vimwiki-pytasks

This is a vim plugin, which aims to provide a integration between vim and taskwarrior. It extends vimwiki plugin and provides bidirecitonal synchronization between TaskWarrior and Vimwiki file.

This allows you to define your tasks in your vimwiki files and still have processing power of TaskWarrior at your disposal.

It uses excellent tasklib library to communicate with TaskWarrior.

### Features

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
