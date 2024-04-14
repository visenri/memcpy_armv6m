/*
 * Copyright (c) 2024 Visenri.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Tests for memcpy.
 * Some code is specific for RP2040 (rom address for romSrcMemoryBuffer & XIP stuff).
 */
#include "test-memcpy.h"
#include <string.h>
#include "stdio.h"
#include <inttypes.h>
#undef NDEBUG // Force assertions to work even in release mode
#include "assert.h"

#include "hardware/structs/xip_ctrl.h" // XIP macros

// Small function to generate sequences of numbers.
// It avoids the values used for out of buffer write detection.
static uint8_t rnd8()
{
    static uint8_t seed = 0;
    seed++;
    if (seed == 0xFF)
        seed++;
    if (seed == 0)
        seed++;
    return seed;
}

// This is the reference function to compare against the tested implementations.
static void * memcpy_known_good(void *dst, const void *src, size_t length)
{
  void *ret = dst;
  while (length--)
    *(uint8_t *)dst++ = *(uint8_t *)src++;
  return ret;
}

// Macros to fill a constant array with increasing numbers
#define REPEAT_UINT8_VALUES_INCREASING_2(x) (x) & 0xFF, (x + 1) & 0xFF
#define REPEAT_UINT8_VALUES_INCREASING_4(x)    REPEAT_UINT8_VALUES_INCREASING_2(x),   REPEAT_UINT8_VALUES_INCREASING_2(  x +   2)
#define REPEAT_UINT8_VALUES_INCREASING_8(x)    REPEAT_UINT8_VALUES_INCREASING_4(x),   REPEAT_UINT8_VALUES_INCREASING_4(  x +   4)
#define REPEAT_UINT8_VALUES_INCREASING_16(x)   REPEAT_UINT8_VALUES_INCREASING_8(x),   REPEAT_UINT8_VALUES_INCREASING_8(  x +   8)
#define REPEAT_UINT8_VALUES_INCREASING_32(x)   REPEAT_UINT8_VALUES_INCREASING_16(x),  REPEAT_UINT8_VALUES_INCREASING_16( x +  16)
#define REPEAT_UINT8_VALUES_INCREASING_64(x)   REPEAT_UINT8_VALUES_INCREASING_32(x),  REPEAT_UINT8_VALUES_INCREASING_32( x +  32)
#define REPEAT_UINT8_VALUES_INCREASING_128(x)  REPEAT_UINT8_VALUES_INCREASING_64(x),  REPEAT_UINT8_VALUES_INCREASING_64( x +  64)
#define REPEAT_UINT8_VALUES_INCREASING_256(x)  REPEAT_UINT8_VALUES_INCREASING_128(x), REPEAT_UINT8_VALUES_INCREASING_128(x + 128)
#define REPEAT_UINT8_VALUES_INCREASING_512(x)  REPEAT_UINT8_VALUES_INCREASING_256(x), REPEAT_UINT8_VALUES_INCREASING_256(x + 256)
#define REPEAT_UINT8_VALUES_INCREASING_1024(x) REPEAT_UINT8_VALUES_INCREASING_512(x), REPEAT_UINT8_VALUES_INCREASING_512(x + 512)


#define TEST_MEMCPY_MAX_TEST_SIZE 128
#define TEST_MEMCPY_MAX_TEST_OFFSET 7
#define TEST_MEMCPY_BUFFER_SIZE (256 * 1)

// Buffers needed for testing
static const uint8_t * const romSrcMemoryBuffer = (uint8_t * )0x4;
static const uint8_t flashSrcMemoryBuffer[] = {REPEAT_UINT8_VALUES_INCREASING_1024(0)};
static uint8_t ramSrcMemoryBuffer[TEST_MEMCPY_BUFFER_SIZE];

static uint8_t ramDstBufferGood[TEST_MEMCPY_BUFFER_SIZE];
static uint8_t ramDstBufferTest[TEST_MEMCPY_BUFFER_SIZE];

// Memory space types
typedef enum MemorySpaceType{
	MS_RAM,
	MS_ROM,
	MS_FLASH,
    MS_FLASH_NO_CACHE
}MemorySpaceType;

// Structure with the data for a memory space type
typedef struct MemorySpaceSourceInfo{
    MemorySpaceType memorySpace;
    const char * name;
    const uint8_t * memPointer;
}MemorySpaceSourceInfo;

// Define data to fill the list of memory spaces
#define MEMORY_SPACE_RAM            {MS_RAM, "RAM", ramSrcMemoryBuffer}
#define MEMORY_SPACE_ROM            {MS_ROM, "ROM", romSrcMemoryBuffer}
#define MEMORY_SPACE_FLASH          {MS_FLASH, "FLASH", flashSrcMemoryBuffer}
#define MEMORY_SPACE_FLASH_NO_CACHE {MS_FLASH_NO_CACHE, "FLASH - NO CACHE", (uint8_t *)((uint32_t)flashSrcMemoryBuffer + (XIP_NOCACHE_NOALLOC_BASE - XIP_MAIN_BASE))}

// List of memory spaces to test
static const MemorySpaceSourceInfo TEST_MEM_SPACES[] = {
    MEMORY_SPACE_RAM,
    MEMORY_SPACE_FLASH, 
    MEMORY_SPACE_FLASH_NO_CACHE, 
    MEMORY_SPACE_ROM};

static const int TEST_MEM_SPACES_COUNT = sizeof(TEST_MEM_SPACES) / sizeof(TEST_MEM_SPACES[0]);

void test_memcpy(MemcpyFunction memcpyGood, MemcpyFunction memcpyTest)
{    
    uint32_t testNumber = 0;

    if (memcpyGood == NULL) // Set default good implementation if none provided
        memcpyGood = &memcpy_known_good;

    for (int mem = 0; mem < TEST_MEM_SPACES_COUNT; mem++)
    {
        MemorySpaceSourceInfo ms = TEST_MEM_SPACES[mem];
        printf("Memory space: %s\n", ms.name);
        
        // Iterate all sizes, offsets & unused values
        for (size_t size = 0; size <= TEST_MEMCPY_MAX_TEST_SIZE; size++)
        {
            for (size_t srcOffset = 0; srcOffset <= TEST_MEMCPY_MAX_TEST_OFFSET; srcOffset++)
            {
                for (size_t dstOffset = 0; dstOffset <= TEST_MEMCPY_MAX_TEST_OFFSET; dstOffset++)
                {
                    for (uint8_t unusedValue = 0xFF; unusedValue != 1; unusedValue++)
                    {
                        // Fill destination buffers with unused value
                        memset(ramDstBufferGood, unusedValue, TEST_MEMCPY_BUFFER_SIZE);
                        memset(ramDstBufferTest, unusedValue, TEST_MEMCPY_BUFFER_SIZE);

                        const uint8_t * srcMemory = ms.memPointer; // Get pointer to source memory

                        if (srcMemory == ramSrcMemoryBuffer)
                        {
                            // Fill source buffer with the complement of unused value
                            memset(ramSrcMemoryBuffer, ~unusedValue, TEST_MEMCPY_BUFFER_SIZE);
                            // Fill memory with some data
                            uint8_t * src = &ramSrcMemoryBuffer[srcOffset];
                            for (size_t i = 0; i < size; i++)
                                src[i] = rnd8();
                        }
                        if (0 && ms.memorySpace == MS_FLASH_NO_CACHE ) // DEBUG specific case
                        {
                            if (size >= 9 && srcOffset != dstOffset)
                                asm("bkpt");
                        }

                        assert(srcMemory != NULL); // Source must be valid
                        
                        // Do copy with "good" memcpy & check results against source
                        const uint8_t * src = &srcMemory[srcOffset];
                        uint8_t * dst = &ramDstBufferGood[dstOffset];

                        uint8_t * dstRetGood = (uint8_t *)memcpyGood(dst, src, size);
                        assert(dstRetGood == dst);
                        assert(memcmp(dstRetGood, src, size) == 0);

                        // Do copy with tested memcpy & check results against source
                        dst = &ramDstBufferTest[dstOffset];
                        uint8_t * dstRetTest = (uint8_t *)memcpyTest(dst, src, size);
                        assert(dstRetTest == dst);
                        assert(memcmp(dstRetTest, src, size) == 0);

                        // Compare destination buffers using the whole size of buffer,
                        // this should detect out of buffer writes.
                        assert(memcmp(ramDstBufferGood, ramDstBufferTest, TEST_MEMCPY_BUFFER_SIZE) == 0);
                        testNumber++;
                    }
                }
            }
        }
        printf("%" PRIu32 " tests Ok\n", testNumber);
    }
}
