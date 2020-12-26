if exists('b:did_ftplugin_taskwiki_after') | finish | endif
let b:did_ftplugin_taskwiki_after = 1

let b:taskwiki_omnifunc_fallback = len(&omnifunc) ? function(&omnifunc) : ''
setlocal omnifunc=taskwiki#CompleteOmni
