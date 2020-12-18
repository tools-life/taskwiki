if exists('g:loaded_taskwiki_auto') | finish | endif
let g:loaded_taskwiki_auto = 1

" Altered version of the VimwikiFoldText, strips viewport params
function! taskwiki#FoldText()
  let line = getline(v:foldstart)
  let main_text = substitute(line, '^\s*', repeat(' ',indent(v:foldstart)), '')
  let short_text = substitute(main_text, '|[^=]* =', '=', '')
  let short_text = substitute(short_text, '@[^=]* =', '=', '')
  let short_text = substitute(short_text, ' @[A-Za-z0-9]\+', '', '')
  let fold_len = v:foldend - v:foldstart + 1
  let len_text = ' ['.fold_len.'] '
  return short_text.len_text.repeat(' ', 500)
endfunction
