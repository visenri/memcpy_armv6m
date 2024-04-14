# Fast memcpy for ARMv6M

This new memcpy is between 1.5x and 3.5x faster than the default ROM version of Raspberry Pi Pico (RP2040).

The following graph shows the average throughput compared to the default ROM version (in dashed lines):
![](./images/memcpy_comparison_ram.png)

 - Green lines: data aligned at word (4 byte) boundary (both source & destination).
 - Red lines: not aligned data.
 
There are 3 versions (mivo0, miwo1 & miwo2) with increasing speed.

## Ho to use it:
Copy the memops_opt folder to your project.

Add it in your makefile:
~~~~
add_subdirectory(memops_opt)
~~~~

Enable it at runtime calling:
~~~~
memcpy_wrapper_replace(NULL);
~~~~

See more details in my blog: 
https://visenri.users.sourceforge.net/blog/2024/mempy_replacement_for_armv6-Part1
