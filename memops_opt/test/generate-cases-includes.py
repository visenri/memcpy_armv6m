# Test case extra files generator, it generates:
# - C file: arrays including implementation details.
# - H file: declaration of ASM functions and declaration of C file arrays.
# - CMAKE file to add all generated files to the target.

import sys, os, glob, re

targetSourcesStart = """
target_sources(@targetName INTERFACE
"""

targetSourcesEnd = """)
"""

headerStart = """
#ifndef @headerName_H
#define @headerName_H
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif
"""

headerEnd = """
#ifdef __cplusplus
}
#endif
#endif
"""

headerFunctionPrototype = "extern void * @function(void *dst, const void *src, size_t length);\n"
headerFunctionArrayPrototype = "void * (* const @name_IMP_FUNCTIONS[@name_IMP_COUNT])(void *, const void *, size_t)"
headerFunctionNameArrayPrototype = "const char * const @name_IMP_NAMES[@name_IMP_COUNT]"
headerFunctionArrayCount = "#define @name_IMP_COUNT @value" #"const int @name_IMP_COUNT = @value;\n"

def openFile(fileName, mode):
    if sys.version_info[0]<3:
        return open(fileName, mode)
    else:
        return open(fileName, mode, encoding="latin-1")

def generateElement(baseName, template, list, definition, prefix, suffix):

    result = "\n"
    
    if not definition:
        result += "extern "
    result += template.replace("@name", baseName)

    result += (";", " =")[definition] + "\n"

    if definition:
        result += "{\n"
        for element in list:
            result += prefix + element + suffix + ",\n"
        result += "};\n"
    return result

def generate(target, filesPattern):
    baseFile = re.sub('\*.*', '', os.path.basename(filesPattern))
    #print (baseFile)

    files = []
    functions = []
    for filename in glob.glob(filesPattern):
        basename = os.path.basename(filename)
        files.append(filename)
        functions.append(os.path.splitext(basename)[0])
        
    print("\n %d files found.\n" % len(files))

    #print(files)
    #print(functions)

    # GENERATE MAKEFILE
    cmakeFile = target + ".cmake"
    cFile = target + ".c"
    hFile = target + ".h"

    with openFile(cmakeFile, 'w') as fout:
        fout.write(targetSourcesStart.replace("@targetName", target))
        for filename in files:
            #print (filename)
            fout.write((os.path.join("${CMAKE_CURRENT_LIST_DIR}", filename).replace('\\', '/')) + "\n")

        fout.write((os.path.join("${CMAKE_CURRENT_LIST_DIR}", cFile).replace('\\', '/')) + "\n")
        fout.write(targetSourcesEnd)


    # GENERATE HEADER AND C FILE
    baseName = baseFile.upper()
    for definition in False, True:
        fileName = (hFile, cFile)[definition]
        with openFile(fileName, 'w') as fout:
            if definition:
                fout.write('#include "' + hFile + '"\n')
            else:
                fout.write(headerStart.replace("@headerName", os.path.splitext(fileName)[0].upper()))
                for functionName in functions:
                    fout.write(headerFunctionPrototype.replace("@function", functionName))
                fout.write("\n")
                fout.write(headerFunctionArrayCount.replace("@name", baseName).replace("@value", str(len(functions))) + "\n")        
            
            # Generate arrays
            fout.write(generateElement(baseName, headerFunctionArrayPrototype, functions, definition, "&", ""))
            fout.write(generateElement(baseName, headerFunctionNameArrayPrototype, functions, definition, '"', '"'))

            if not definition:
                fout.write(headerEnd)


def main():
    # Check and parse the command line arguments
    if len(sys.argv) < 3:
        print("usage: " + os.path.basename(__file__) + " target_name out_dir")
        sys.exit(-1)
        
    outdir = sys.argv[2]
    target =  sys.argv[1]    
    
    generate(target, outdir)

if __name__ == '__main__':
    main()
