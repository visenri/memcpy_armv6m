pushd "%~dp0"

del .\gen\*.S /q
del memops_opt_test_imp.c /q
del memops_opt_test_imp.cmake /q
del memops_opt_test_imp.h /q

popd