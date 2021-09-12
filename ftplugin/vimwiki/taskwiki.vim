" Check VIM version
if version < 704
  echoerr "Taskwiki requires at least Vim 7.4. Please upgrade your environment."
  finish
endif

" Python version detection.
if has("python3") && ! exists("g:taskwiki_use_python2")
  let g:taskwiki_py='py3 '
  let g:taskwiki_pyfile='py3file '
elseif has("python")
  let g:taskwiki_py='py '
  let g:taskwiki_pyfile='pyfile '
else
  echoerr "Taskwiki requires Vim compiled with the Python support."
  finish
endif

" Disable taskwiki if taskwiki_disable variable set
if exists("g:taskwiki_disable")
  finish
endif

if !exists("g:did_python_taskwiki")
  " Determine the plugin path
  let s:plugin_path = escape(expand('<sfile>:p:h:h:h'), '\')

  " Execute the main body of taskwiki source
  execute g:taskwiki_pyfile . s:plugin_path . '/taskwiki/main.py'

  let g:did_python_taskwiki = 1
endif

" Global update commands
execute "command! -buffer -nargs=* TaskWikiBufferSave :"      . g:taskwiki_py . "WholeBuffer.update_to_tw()"
execute "command! -buffer -nargs=* TaskWikiBufferLoad :"      . g:taskwiki_py . "WholeBuffer.update_from_tw()"

augroup taskwiki
    autocmd! * <buffer>
    " Update to TW upon saving
    autocmd BufWrite <buffer> TaskWikiBufferSave
    " Save and load the view to preserve folding, if desired
    if !exists('g:taskwiki_dont_preserve_folds')
      autocmd BufWinLeave <buffer> call taskwiki#MkView()
      autocmd BufWinEnter <buffer> call taskwiki#LoadView()
    endif
    " Reset cache when switching buffers
    execute "autocmd BufEnter <buffer> :" . g:taskwiki_py . "cache.load_current().reset()"
    " Update window-local fold options
    autocmd BufWinEnter <buffer> call taskwiki#FoldInit()

    " Refresh on load (if possible, after loadview to preserve folds)
    if has('patch-8.1.1113') || has('nvim-0.4.0')
      autocmd BufWinEnter <buffer> ++once TaskWikiBufferLoad
    else
      TaskWikiBufferLoad
    endif
augroup END

" Split reports commands
execute "command! -buffer -nargs=* TaskWikiProjects :"        . g:taskwiki_py . "SplitProjects(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiProjectsSummary :" . g:taskwiki_py . "SplitSummary(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiBurndownDaily :"   . g:taskwiki_py . "SplitBurndownDaily(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiBurndownMonthly :" . g:taskwiki_py . "SplitBurndownMonthly(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiBurndownWeekly :"  . g:taskwiki_py . "SplitBurndownWeekly(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiCalendar :"        . g:taskwiki_py . "SplitCalendar(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiGhistoryAnnual :"  . g:taskwiki_py . "SplitGhistoryAnnual(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiGhistoryMonthly :" . g:taskwiki_py . "SplitGhistoryMonthly(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiHistoryAnnual :"   . g:taskwiki_py . "SplitHistoryAnnual(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiHistoryMonthly :"  . g:taskwiki_py . "SplitHistoryMonthly(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiStats :"           . g:taskwiki_py . "SplitStats(<q-args>).execute()"
execute "command! -buffer -nargs=* TaskWikiTags :"            . g:taskwiki_py . "SplitTags(<q-args>).execute()"

" Commands that operate on tasks in the buffer
execute "command! -buffer -range TaskWikiInfo :<line1>,<line2>"   . g:taskwiki_py . "SelectedTasks().info()"
execute "command! -buffer -range TaskWikiEdit :<line1>,<line2>"   . g:taskwiki_py . "SelectedTasks().edit()"
execute "command! -buffer -range TaskWikiLink :<line1>,<line2>"   . g:taskwiki_py . "SelectedTasks().link()"
execute "command! -buffer -range TaskWikiGrid :<line1>,<line2>"   . g:taskwiki_py . "SelectedTasks().grid()"
execute "command! -buffer -range TaskWikiDelete :<line1>,<line2>" . g:taskwiki_py . "SelectedTasks().delete()"
execute "command! -buffer -range TaskWikiStart :<line1>,<line2>"  . g:taskwiki_py . "SelectedTasks().start()"
execute "command! -buffer -range TaskWikiStop :<line1>,<line2>"   . g:taskwiki_py . "SelectedTasks().stop()"
execute "command! -buffer -range TaskWikiToggle :<line1>,<line2>" . g:taskwiki_py . "SelectedTasks().toggle()"
execute "command! -buffer -range TaskWikiDone :<line1>,<line2>"   . g:taskwiki_py . "SelectedTasks().done()"
execute "command! -buffer -range TaskWikiRedo :<line1>,<line2>"   . g:taskwiki_py . "SelectedTasks().redo()"

execute "command! -buffer -range -nargs=* TaskWikiSort :<line1>,<line2>"     . g:taskwiki_py . "SelectedTasks().sort(<q-args>)"
execute "command! -buffer -range -nargs=* TaskWikiAnnotate :<line1>,<line2>" . g:taskwiki_py . "SelectedTasks().annotate(<q-args>)"
execute "command! -buffer -range -nargs=* -complete=customlist,taskwiki#CompleteMod TaskWikiMod :<line1>,<line2>" . g:taskwiki_py . "SelectedTasks().modify(<q-args>)"

" Interactive commands
execute "command! -buffer -range TaskWikiChooseProject :<line1>,<line2>"     . g:taskwiki_py . "ChooseSplitProjects('global').execute()"
execute "command! -buffer -range TaskWikiChooseTag :<line1>,<line2>"         . g:taskwiki_py . "ChooseSplitTags('global').execute()"

" Meta commands
execute "command! -buffer TaskWikiInspect :" . g:taskwiki_py . "Meta().inspect_viewport()"

" Disable <CR> as VimwikiFollowLink
if !hasmapto('<Plug>VimwikiFollowLink')
  nmap <Plug>NoVimwikiFollowLink <Plug>VimwikiFollowLink
endif

execute "nnoremap <silent><buffer> <CR> :" . g:taskwiki_py . "Mappings.task_info_or_vimwiki_follow_link()<CR>"

" Leader-related mappings. Mostly <Leader>t + <first letter of the action>
if !exists('g:taskwiki_suppress_mappings')
        if exists('g:taskwiki_maplocalleader')
                let s:map_prefix = g:taskwiki_maplocalleader
        else
                if exists('g:mapleader')
                        let s:map_prefix = g:mapleader.'t'
                else
                        let s:map_prefix = '\t'
                endif
        endif
        execute "nnoremap <silent><buffer> ".s:map_prefix."a :TaskWikiAnnotate<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."bd :TaskWikiBurndownDaily<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."bw :TaskWikiBurndownWeekly<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."bm :TaskWikiBurndownMonthly<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."cp :TaskWikiChooseProject<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."ct :TaskWikiChooseTag<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."C :TaskWikiCalendar<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."d :TaskWikiDone<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."D :TaskWikiDelete<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."e :TaskWikiEdit<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."g :TaskWikiGrid<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."Gm :TaskWikiGhistoryMonthly<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."Ga :TaskWikiGhistoryAnnual<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."hm :TaskWikiHistoryMonthly<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."ha :TaskWikiHistoryAnnual<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."i :TaskWikiInfo<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."l :TaskWikiLink<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."m :TaskWikiMod<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."p :TaskWikiProjects<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."s :TaskWikiProjectsSummary<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."S :TaskWikiStats<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."t :TaskWikiTags<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix.". :TaskWikiRedo<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."+ :TaskWikiStart<CR>"
        execute "nnoremap <silent><buffer> ".s:map_prefix."- :TaskWikiStop<CR>"

        " Mappings for visual mode.
        execute "vnoremap <silent><buffer> ".s:map_prefix."a :TaskWikiAnnotate<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."cp :TaskWikiChooseProject<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."ct :TaskWikiChooseTag<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."d :TaskWikiDone<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."D :TaskWikiDelete<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."e :TaskWikiEdit<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."g :TaskWikiGrid<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."i :TaskWikiInfo<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."l :TaskWikiLink<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."m :TaskWikiMod<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix.". :TaskWikiRedo<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."+ :TaskWikiStart<CR>"
        execute "vnoremap <silent><buffer> ".s:map_prefix."- :TaskWikiStop<CR>"
endif
