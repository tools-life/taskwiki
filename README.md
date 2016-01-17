## Taskwiki

_Proper project management in vim.
Standing on the shoulders of vimwiki and Taskwarrior_

[![Travis build status](https://travis-ci.org/tbabej/taskwiki.svg?branch=master)](https://travis-ci.org/tbabej/taskwiki)
[![Coverage Status](https://coveralls.io/repos/tbabej/taskwiki/badge.svg?branch=master)](https://coveralls.io/r/tbabej/taskwiki?branch=master)
[![Code Health](https://landscape.io/github/tbabej/taskwiki/master/landscape.svg?style=flat)](https://landscape.io/github/tbabej/taskwiki/master)
[![Chat with developers](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/tbabej/taskwiki)

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

To access documentation, run :helptags and then :help taskwiki.

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

#### Individual tasks

    * [ ] Install Taskwiki

Such tasks get synced to TaskWarrior when the file is saved. Additional
metadata, as project, tags, priority, can be stored with this task.

Some of that metadata gets visually represented in vim, and is updated
if the representation changes in vim.

    * [ ] Install Taskwiki !!! (2015-08-23 19:00)

#### Task lists

Tasks can be grouped - simply written in one block. This has the advantage
of any child tasks being marked as dependencies of the parent tasks.

    * [ ] Get married
        * [X] Find a girlfriend
        * [ ] Buy a ring
        * [ ] Propose

#### Viewports

Viewport is a header with a task query (filter) embedded, generating
the corresponding task list. These tasks can be modified and changes
will be synced back to task data.  A simple viewport can look as follows:

    == Home tasks | project:Home ==

Filter query is concealed.

Upon saving, this will generate the list of matching tasks, in a tree-like
fashion (respecting dependencies).

    == Home tasks | project:Home ==
    * [ ] Feed the dog (2015-08-08)
    * [ ] Tidy up the house !!
      * [ ] Wash the dishes
      * [ ] Declare war on the cobwebs

Tasks added (written) to the task list under the viewport inherit the defaults
from its filter.

    == Home tasks | project:Home ==
    * [ ] Feed the dog
    * [ ] Tidy up the house !!
      * [ ] Wash the dishes
      * [ ] Declare war on the cobwebs
    * [ ] Call the landlord about rent payment (2015-08-23)
          ^ the task above will have project:Home set automatically

For some more complex filters, defaults cannot be automatically derived.
In such case, you can specify the defaults explicitly:

    == Urgent tasks | +OVERDUE or +urgent | +urgent ==
                                             ^ defaults definition

Viewports can be inspected by hitting [CR] with cursor above them.

#### Report splits

Taskwiki can provide additional information reports on a task list (selected,
or part of a viewport) and on individial tasks as well. These reports are shown
in dynamic temporary splits.

    * [ ] Tidy up the house !! (2015-08-23 00:00)

For example, hitting [CR] on the above task runs :TaskWikiInfo and displays:

    Name          Value
    ------------- ---------------------------------------------------------
    ID            6
    Description   Tidy up the house
                    2015-08-22 21:29:35 Tip: Use roomba for vacuum-cleaning
    Status        Pending
    Project       Home
    Entered       2015-08-22 21:27:26 (2 minutes)
    Due           2015-08-23 00:00:00
    Last modified 2015-08-22 21:30:21 (1 second)
    Virtual tags  ANNOTATED MONTH PENDING READY UNBLOCKED YEAR
    UUID          448c2fa9-6a06-454e-a2bc-b0c8ae91994f
    Urgency       9.895
    Priority      H

    Date                Modification
    ------------------- ------------------------------------------------------------
    2015-08-14 21:29:35 Annotation of 'Tip: Use roomba for vacuum-cleaning' added.
    2015-08-14 21:30:11 Due set to '2015-08-23 00:00:00'.

Running the :TaskWikiSummary can produce side-split like this:

    Project            Remaining Avg age  Complete 0%                        100%
    ------------------ --------- -------- -------- ------------------------------
    Work                      18  4 weeks      74% ======================
      Designs
        Feature X              3  4 weeks      89% ==========================
        Feature Y              7  2 weeks      47% =========
      Tickets                  5  3 weeks      79% ======================
      Blog                     1 4 months      50% ===============


There are many more reports (burndown, calendar, history, projects, stats,
summary, tags,..), but for the sake of brevity, they will not be described here.
They work in a similiar fashion.


#### Task modification commands

Taskwiki provides commands for the all the traditional operation on tasks, such as
starting, stopping, completing, deletion, annotation, generic modification, etc.

    * [ ] Tidy up the house !! (2015-08-23 00:00)

Say we want to postpone this task to tomorrow. This can be achieved by hitting
[Leader]tm (:TaskWikiMod) a prompt will show up, where we enter our desired
modification:

    Enter modifications: due:tomorrow

Task is instantly updated:

    * [ ] Tidy up the house !! (2015-08-24 00:00)

Task modification commands can be performed on a task currently below the
cursor, or on a visually selected group of tasks.


#### Advanced

- Viewport flags: Custom data sources / sort orders can be defined for
individual viewports.

- Grid view: If vim-taskwarrior is available, it can be used to display
a grid view of available tasks.

- Tagbar: Can be shown to display a overview of a Taskwiki file

- Interactive splits: Assign project/tags by picking a option from a split
that lists all the already used projects/tags.


### Credits

Created by: Tomas Babej.

Design suggestions contributed by: David J Patrick.

Inspired by: [vimwiki-tasks plugin](https://github.com/teranex/vimwiki-tasks).

Taskwiki wouldn't be possible without all the work and support from the
Taskwarrior community. Come hang out at #taskwarrior on Freenode.

### Contributing

Code and issue tracker is hosted at: https://github.com/tbabej/taskwiki

Feel free to submit pull requests and/or file issues for bugs and suggestions.
