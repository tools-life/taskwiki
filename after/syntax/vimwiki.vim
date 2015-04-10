" Detect if conceal feature is available
let s:conceal = exists("+conceallevel") ? ' conceal': ''

syntax match TaskWikiTask contains=VimwikiListTodo /\s*\* \[.\]\s.*$/

" Conceal the UUID
execute 'syn match TaskWikiTaskUuid containedin=TaskWikiTask /\v#([A-Z]:)?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/'.s:conceal
execute 'syn match TaskWikiTaskUuid containedin=TaskWikiTask /\v#([A-Z]:)?[0-9a-fA-F]{8}$/'.s:conceal
highlight link TaskWikiTaskUuid Comment

" Conceal header definitions
for s:i in range(1,6)
  execute 'syn match TaskWikiHeaderDef containedin=VimwikiHeader'.s:i.' /|[^=]*/'.s:conceal
endfor

" Define active and deleted task regions
" Will be colored dynamically by Meta().source_tw_colors()
syntax match TaskWikiTaskActive containedin=TaskWikiTask /\s*\*\s\[S\]\s[^#]*/
syntax match TaskWikiTaskCompleted containedin=TaskWikiTask /\s*\*\s\[X\]\s[^#]*/
syntax match TaskWikiTaskDeleted containedin=TaskWikiTask /\s*\*\s*\[D\]\s[^#]*/
syntax match TaskWikiTaskPriority containedin=TaskWikiTask /\( !\| !!\| !!!\)/

" Set concealed parts as really concealed in normal mode, and with cursor over
setlocal conceallevel=3
setlocal concealcursor=nc
