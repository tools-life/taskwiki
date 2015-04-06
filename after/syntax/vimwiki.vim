" Detect if conceal feature is available
let s:conceal = exists("+conceallevel") ? ' conceal': ''

" Conceal the UUID
execute 'syn match VimwikiTaskUuid containedin=VimwikiCheckBoxDone,VimwikiCheckBoxActive,VimwikiCheckBoxDeleted /\v#([A-Z]:)?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/'.s:conceal
execute 'syn match VimwikiTaskUuid containedin=VimwikiCheckBoxDone,VimwikiCheckBoxActive,VimwikiCheckBoxDeleted /\v#([A-Z]:)?[0-9a-fA-F]{8}$/'.s:conceal

" Conceal header definitions
for s:i in range(1,6)
  execute 'syn match TaskWikiHeaderDef containedin=VimwikiHeader'.s:i.' /|[^=]*/'.s:conceal
endfor

" Highlight active tasks
syntax match VimwikiCheckBoxActive /\s*\*\s*\[S\]\s.*$/
hi def link VimwikiCheckBoxActive Type

" Highlight deleted tasks
syntax match VimwikiCheckBoxDeleted /\s*\*\s*\[D\]\s.*$/
hi def link VimwikiCheckBoxDeleted Error

" Highlight the UUID as comment
hi link VimwikiTaskUuid Comment

" Set concealed parts as really concealed in normal mode, and with cursor over
setlocal conceallevel=3
setlocal concealcursor=nc
