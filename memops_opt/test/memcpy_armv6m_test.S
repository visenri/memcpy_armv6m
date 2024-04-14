/*  Template for memcpy ARMv6M implementation cases
    // Test cases
    miwo:   0, 1, 2
    mssp:   0, 1, 2
    opxip:  0, 1
    opsz:   0, 1, 2
    msup:   0, 1

    // Grouped cases
    =: miwo 0; opsz 0
    =: miwo 0; opsz 1
    =: miwo 0; opsz 2

    // Skip cases
    // msup only used when mssp is 2
    -: mssp 0,1; msup 1 

    // opxip not used when mssp is 0
    -: mssp 0; opxip 1
*/

#define MEMCPY_ARMV6M_MISALIGNED_COPY_LOOP_WORDS      ({miwo})
#define MEMCPY_ARMV6M_MED_SIZE_SPEED                  ({mssp})
#define MEMCPY_ARMV6M_OPTIMIZE_XIP_MEMORY_READ        ({opxip})
#define MEMCPY_ARMV6M_OPTIMIZE_SIZE                   ({opsz})
#define MEMCPY_ARMV6M_MED_SIZE_UPWARDS                ({msup})

#define MEMCPY_ARMV6M_FUNCTION_NAME {testcaseFilename}
#define MEMCPY_ARMV6M_FUNCTION_END_SIGNATURE 1
#include "..\..\memcpy_armv6m.S"
