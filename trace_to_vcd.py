#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import sys
import struct


def usage( failure ):
    print >>sys.stderr, "trace_to_vcd.py"
    print >>sys.stderr, "Nick Lambourne 2013, after a good cocktail with James McCombe"
    print >>sys.stderr
    print >>sys.stderr, "Usage: trace_to_vcd.py [options]"
    print >>sys.stderr
    print >>sys.stderr, "    -t, --tracefile       Pointer to the trace file"
    print >>sys.stderr, "    -o, --output          Output VCD file"
    print >>sys.stderr, "    -v, --verbose         Verbose mode"
    print >>sys.stderr, "    -vv, --veryverbose    Very Verbose mode"
    print >>sys.stderr, ""
    print >>sys.stderr, "Exiting with status: ", failure
    sys.exit(1)


class Logging:
    quiet = 0
    verbose = 1
    very_verbose = 2

def get_options(): 
    class Options:
        def __init__(self):           
            
            self.tracefile = None
            self.output = None
            self.program = None
            self.logging = Logging.quiet

    options = Options()
    a = 1
    while a < len(sys.argv):
        if sys.argv[a].startswith("-"):
            if sys.argv[a] in ("-t", "--tracefile"):
                a += 1
                options.tracefile = sys.argv[a]
            elif sys.argv[a] in ("-o", "--output"):
                a += 1
                options.output  = sys.argv[a]
            elif sys.argv[a] in ("-p", "--program"):
                a += 1
                options.program  = sys.argv[a]                      
            elif sys.argv[a] in ("-v", "--verbose"):
                options.logging = Logging.verbose
            elif sys.argv[a] in ("-vv", "--veryverbose"):
                options.logging = Logging.very_verbose                
            else:
                usage("Unknown option:" + sys.argv[a])
        else:
            usage("Invalid option formatting" + sys.argv[a])
        a += 1
        
    if options.tracefile == None or options.output == None or options.program == None:
       usage( "not enough arguments" )
        
    if options.logging == Logging.very_verbose:
        print "Trace file =", options.tracefile
        print "Output =", options.output
        print "Program =", options.program

    return options



###################################################
## Function to build up a dict of address vs function name
###################################################
func_names = {}

def load_func_names( file, logging ):
   tup_list = []

   cmd = "nm --demangle -n " + file    

   if logging:
      print "Running cmd: ", cmd

   stream = os.popen(cmd)
   while True:
      s = stream.readline()
      if len(s) == 0:
         break
      t = s.split(" ")

      if logging == Logging.very_verbose:
         print "Read tuple", t

      if len(t) == 3:
         tup_list.append(t)

   if logging:
      print "Parsing output of nm"

   #parse the list of tuples in reverse order, building up a full address map to the symbols store the last address seen (as we as nm to output sorted) and use this to determine the 
   #range
   prev_address = -1
   for x in reversed(tup_list):
      if x[1] == 'T' or x[1] == 't':
         name = x[2].rstrip('\r\n')
         if name[0] != '.': #strip out internal gcc symbols
            for addr in range( int(x[0], base=16), int( prev_address, base=16 ) ):
               a_ = "%08X" % addr
               func_names[a_] = name
               if logging == Logging.very_verbose:
                  print "Adding func:", name, "at address", a_
      prev_address = x[0]


###################################################
## Helper func to get a name from an address - needed to handle the exception case where no name exists
###################################################
def get_func_name( addr ):
   a_ = "%08X" % addr
   if func_names.has_key(a_):
       return func_names[a_]
   else:
      return "UNKNOWN_" + a_



def draw_progress_bar( percentage, cur_bar_pos ):
   toolbar_width = 50 #half of the percent to make things easy

   if percentage == 0:
      # setup toolbar
      sys.stdout.write("[%s]" % (" " * toolbar_width))
      sys.stdout.flush()
      sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['

   new_pos = percentage / 2
   if percentage > 0 and cur_bar_pos != new_pos:
       new_bar_chars = new_pos - cur_bar_pos

       # update the bar
       for x in range(0, new_bar_chars):
          sys.stdout.write("-")
       sys.stdout.flush()
       cur_bar_pos = new_pos

   if percentage == 100:
      sys.stdout.write("\n")

   return cur_bar_pos


###################################################
## Parse Trace! Returns a tuple of:
##    - function names used (list of strs)
##    - list of function calls (list of tuples being DIRECTION, FUNC, CALLER, TIME)
###################################################
def parse_trace( filename, logging ):
   func_names_used = []
   calls = []

   file_size = os.path.getsize(filename)
   total_data_read = 0
   progress_percentage = 0
   cur_bar_pos = 0

   f = open( filename, "rb" )

   IN = 1
   OUT = 2

   size_of_item = 8 #bytes
   buffer_size_to_read = size_of_item * 16384

   if logging:
      print "Parsing trace file:", filename

   cur_bar_pos = draw_progress_bar( 0, cur_bar_pos )

   while True:
      data = f.read( buffer_size_to_read )
      total_data_read += len(data)

      if len(data) != 0:
         for x in range( 0, len(data), 8 ):
            t = struct.unpack("II", data[x:x+8] )
            op_time = t[0]
            func = t[1]

            op = (op_time >> 24) & 0xFF
            time = op_time & 0xFFFFFF

            if op == IN or op == OUT:
               dir = "IN" if (op == IN) else "OUT"
              
               item = dir, get_func_name(func), time
 
               func_names_used.append( get_func_name(func) )
            
               calls.append( item )
            else:
               print "Bad op", op
               sys.exit(-1)

            new_percentage = (total_data_read * 100) / file_size
            if progress_percentage != new_percentage:
               cur_bar_pos = draw_progress_bar( new_percentage, cur_bar_pos )
               progress_percentage = new_percentage

      else:
         break
   f.close()

   cur_bar_pos = draw_progress_bar( 100, cur_bar_pos )
   
   #remove the duplices from the function names
   func_names_used = list(set(func_names_used))
   
   return func_names_used, calls


###################################################
## Dump the VCD file
###################################################
def dump_waveform( outfile, funcs, calls, logging ):
   f = open( outfile, "w" )

   if logging:
      print "Dumping VCD"
   
   #first, print all the functions
   f.write( "$date May 20 2013 12:00:05 $end\n" )
   f.write( "$version GCC func to vcd V0.1 $end\n" )
   f.write( "$timescale 1 ns $end\n" )
   f.write( "$scope module top $end\n" )

   func_char_map = {}

   char_index = ord('!')    
   for func in sorted(funcs):
      f.write( "$var wire 1 " + chr(char_index) + " " + func + " $end\n"  )
      func_char_map[func] = chr(char_index)
      char_index += 1
      if chr(char_index) == '\"' or chr(char_index) == '\'':
         char_index += 1

   f.write( "$upscope $end\n" )
   f.write( "$enddefinitions $end\n" )
   
   
   #initial settings
   f.write( "#0\n" )
   for func in funcs:
      f.write( "0" + func_char_map[func] + "\n" )
   
   #dump out all the stack changes
   for t, c in enumerate(calls):
      new_time = t + c[2]
      if new_time == t:
         new_time += 1
      else:
         print "actual ", new_time, t, c[2]

      f.write( "#" + str(new_time) + "\n" )
      if c[0] == "IN":
         f.write( "1" + func_char_map[c[1]] + "\n" )
         
      if c[0] == "OUT":
         f.write( "0" + func_char_map[c[1]] + "\n" )

      t = new_time
         
   #all to zero at the end please
   f.write( "#" + str(t + 2) + "\n" )
   for func in funcs:
      f.write( "0" + func_char_map[func] + "\n" )     
   
   f.close()

###################################################
## Main!
###################################################
if __name__ == '__main__':
    
    #parse options
    options = get_options()

    load_func_names( options.program, options.logging )
    
    #parse the trace file
    funcs, calls = parse_trace( options.tracefile, options.logging )

    if options.logging:
       print "There are", len(funcs), "functions logged and", len(calls), "total function calls"
    
    #dump the wave form
    dump_waveform( options.output, funcs, calls, options.logging )    

    sys.exit(0)
