# Test case generator from SDCC compiler (https://sdcc.sourceforge.net/)
# Modifications by Visenri:
#   - Added /ns modifier to avoid generaration or "__runSuite" code.
#   - New template format to allow grouped or skipped cases.
#  
from HTMLgen import TemplateDocument
import sys, re, tempfile, os

"""See InstanceGenerator for a description of this file"""

# Globals
# Directory that the generated files should be placed into
outdir = ''

# Start of the test function table definition
testfuntableheader = """
void
__runSuite(void)
{
"""

# End of the test function table definition
testfuntablefooter = """}
"""

# Code to generate the suite function
testfunsuite = """
__code const char *
__getSuiteName(void)
{
  return "{testcase}";
}
""" 

# Utility functions
def createdir(path):
    """Creates a directory if it doesn't exist"""
    if not os.path.isdir(path):
        os.mkdir(path)

class InstanceGenerator:
    """Test case iteration generator.
    Takes the template given as the first argument, pulls out all the meta
    iteration information, and generates an instance for each combination
    of the names and types.

    See doc/test_suite_spec.tex for more information on the template file
    format."""

    def __init__(self, inname):
        self.inname = inname
        # Initalise the replacements hash.
        # Map of name to values.
        self.replacements = { }
        self.groups = []
        # Initalise the function list hash.
        self.functions = []
        # Emit the suite wrapper into a temporary file
        self.tmpname = tempfile.mktemp()
        (self.dirname, self.filename) = os.path.split(self.inname)
        (self.basename, self.ext) = os.path.splitext(self.filename)
        self.genCount = 0

    def permute(self, basepath, keys, trans = {}):
        """Permutes across all of the names.  For each value, recursivly creates
        a mangled form of the name, this value, and all the combinations of
        the remaining values.  At the tail of the recursion when one full
        combination is built, generates an instance of the test case from
        the template."""
        if len(keys) == 0:
            # End of the recursion.
            # Set the runtime substitutions.
            trans['testcase'] = re.sub(r'\\', r'\\\\', basepath)
            trans['testcaseFilename'] = re.sub(r'\\', r'\\\\', os.path.basename(basepath))

            match = {}
            for group in self.groups:
                #print(group)
                found = True
                for key in group.keys():
                    if (not (key in trans) or not trans[key] in group[key]) and (key != '_Done_'):
                        found = False
                        break
                if (found):
                    match = group
                    break

            #print(self.groups)

            alreadyDone = False
            if len(match):
                alreadyDone = not ('_Done_' in match) or match['_Done_']
                if not alreadyDone:
                    match['_Done_'] = True


            if not alreadyDone:
                # Create the instance from the template
                T = TemplateDocument(self.tmpname)
                T.substitutions = trans
                #print(trans)
                T.write(basepath + self.ext)
                self.genCount += 1
        else:
            # Pull off this key, then recursivly iterate through the rest.
            key = keys[0]
            for part in self.replacements[key]:
                trans[key] = part
                # Turn a empty string into something decent for a filename
                if not part:
                    part = 'none'
                # Remove any bad characters from the filename.
                part = re.sub(r'\s+', r'_', part)
                # The slice operator (keys[1:]) creates a copy of the list missing the
                # first element.
                # Can't use '-' as a seperator due to the mcs51 assembler.
                self.permute(basepath + '_' + key + '_' + part, keys[1:], trans) 

    def writetemplate(self, generateSuiteTable):
        """Given a template file and a temporary name writes out a verbatim copy
        of the source file and adds the suite table and functions."""
        if sys.version_info[0]<3:
            fout = open(self.tmpname, 'w')
        else:
            fout = open(self.tmpname, 'w', encoding="latin-1")

        for line in self.lines:
            fout.write(line)

        if generateSuiteTable:
            # Emmit the suite table
            fout.write(testfuntableheader)

            n = 0;
            for fun in self.functions:
                # Turn the function definition into a function call
                fout.write("  __prints(\"Running " + fun + "\\n\");\n");
                fout.write('  ' + fun + "();\n")
                n += 1;

            fout.write(testfuntablefooter)
            fout.write("\nconst int __numCases = " + str(n) + ";\n")
            fout.write(testfunsuite);
        else:
            n = -1;
        fout.close()
        return n

    def readfile(self):
        """Read in all of the input file."""
        if sys.version_info[0]<3:
            fin = open(self.inname)
        else:
            fin = open(self.inname, encoding="latin-1")
        self.lines = fin.readlines()
        fin.close()

    def parse(self):
        # Start off in the header.
        inheader = 1;

        # Iterate over the source file and pull out the meta data.
        for line in self.lines:
            line = line.strip()

            # If we are still in the header, see if this is a substitution line
            if inheader:
                # A substitution line has a ':' in it
                if re.search(r'=[ \t]*:', line) != None or re.search(r'-[ \t]*:', line) != None:
                    kv = {}
                    if re.search(r'=[ \t]*:', line) != None:
                        kv['_Done_'] = False

                    line = re.split(r':', line)[1]
                    keyValuesText = re.split(r';', line)
                    
                    for text in keyValuesText:
                        #print(text)
                        (name, values) = re.split(r' ', text.strip(), 1)
                        name = name.strip()
                        values = re.split(r',', values.strip()) 
                        values = [value.strip() for value in values]
                        kv[name] = values

                    self.groups.append(kv)   
                    #print(self.groups)
                elif re.search(r':', line) != None:
                    # Split out the name from the values
                    (name, rawvalues) = re.split(r':', line)
                    # Split the values at the commas
                    values = re.split(r',', rawvalues)
                    
                    # Trim the name
                    name = name.strip()
                    # Trim all the values
                    values = [value.strip() for value in values]
                    
                    self.replacements[name] = values
                elif re.search(r'\*/', line) != None:
                    # Hit the end of the comments
                    inheader = 0;
                else:
                    # Do nothing.
                    None
            else:
                # Pull out any test function names
                m = re.match(r'^(?:\W*void\W+)?\W*(test\w*)\W*\(\W*void\W*\)', line)
                if m != None:
                    self.functions.append(m.group(1))

    def generate(self, generateSuiteTable):
        """Main function.  Generates all of the instances."""
        self.readfile()
        self.parse()
        if self.writetemplate(generateSuiteTable) == 0:
            sys.stderr.write("Empty function list in " + self.inname + "!\n")

        # Create the output directory if it doesn't exist
        createdir(outdir)

        # Generate
        self.permute(os.path.join(outdir, self.basename), list(self.replacements.keys()))
        
        print("\n %d files generated." % self.genCount)

        # Remove the temporary file
        os.remove(self.tmpname)

def main():
    # Check and parse the command line arguments
    if len(sys.argv) < 3:
        print("usage: " + os.path.basename(__file__) + " template.c out_dir")
        sys.exit(-1)
        
    global outdir
    outdir = sys.argv[2]
    
    # Input name is the first arg.
    s = InstanceGenerator(sys.argv[1])
    genSuiteTable = True
    if len(sys.argv) >= 4:
        genSuiteTable = sys.argv[3] != '/ns'
    s.generate(genSuiteTable)

if __name__ == '__main__':
    main()
