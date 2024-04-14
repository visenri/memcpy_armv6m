#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void * (*MemcpyFunction)(void *, const void *, size_t);

void test_memcpy(MemcpyFunction memcpyGood, MemcpyFunction memcpyTest);

#ifdef __cplusplus
}
#endif
