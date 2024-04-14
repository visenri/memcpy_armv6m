pushd "%~dp0"

call cleanresults
generate-cases.py memcpy_armv6m_test.S gen /ns
generate-cases-includes.py memops_opt_test_imp gen/memcpy_armv6m_test*.S

popd