
if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/test-memcpy.c")
    add_library(memops_opt_test INTERFACE)
    target_sources(memops_opt_test INTERFACE
        ${CMAKE_CURRENT_LIST_DIR}/test-memcpy.c
    )
endif ()

if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/memops_opt_test_imp.cmake")
    add_library(memops_opt_test_imp INTERFACE)
    include(memops_opt_test_imp.cmake)
endif ()
