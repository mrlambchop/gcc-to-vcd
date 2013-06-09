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
    print >>sys.stderr, "    -p, --program         Pointer to the program/exe"
    print >>sys.stderr, "    -l, --limit           Limit the trace file parsing to N records"
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
            self.limit = 0
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
            elif sys.argv[a] in ("-l", "--limit"):
                a += 1
                options.limit  = int(sys.argv[a])
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



VCD_LOW_ASCII = 'a' #'!'
VCD_HIGH_ASCII = 'f' #'~'

tmp_ascii_dict = {}

#We get in an ASCII ID in the form 'xyz' where each character is the range 33-126
def translate_ascii_id( name, i ):

   #quick lookup for the key
   if tmp_ascii_dict.has_key( name ):
      return tmp_ascii_dict[name]
  
   range = ord(VCD_HIGH_ASCII) - ord(VCD_LOW_ASCII) + 1

   #always add iniial report
   s = chr( (i % range) + ord(VCD_LOW_ASCII) )

   i /= (range ** 1)

   while i:
      d = (i % range)
      s = chr( d + ord(VCD_LOW_ASCII) ) + s
     
      i /= (range ** 1)      

   #store the new key
   tmp_ascii_dict[name] = s

   return s


###################################################
## Function to build up a dict of address vs function name
###################################################
func_names = {}

def load_func_names( file, logging ):
   class Func():
      def __init__(self, name, ascii_id ):
         self.name = name
         self.ascii_id = ascii_id

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

   #parse the list of tuples in reverse order, building up a full address map to the symbols store the last address seen (as we asked nm to output in addr sorted order) and use this 
   #to determine the range of each function (i.e. start / end address)
   prev_address = -1
   ascii_id = 0
   for x in reversed(tup_list):
      if x[1] == 'T' or x[1] == 't':
         name = x[2].rstrip('\r\n')
         if name[0] != '.': #strip out internal gcc symbols
            for addr in range( int(x[0], base=16), int( prev_address, base=16 ) ):
               a_ = "%08X" % addr
               func_names[a_] = Func( name, translate_ascii_id( name, ascii_id ) )
               if logging == Logging.very_verbose:
                  print "Adding func:", name, "at address", a_, "with ASCII ID:", translate_ascii_id( name, ascii_id )
               ascii_id += 1
      prev_address = x[0]


###################################################
## Helper func to get a name OR ascii id from an address - needed to handle the exception case where no name exists
###################################################
def get_func_name( addr ):
   a_ = "%08X" % addr
   if func_names.has_key(a_):
       return func_names[a_].name
   else:
      return "UNKNOWN_" + a_

def get_ascii_id_from_addr( addr ):
   a_ = "%08X" % addr   
   if func_names.has_key(a_):
       return func_names[a_].ascii_id
   else:
      return "!FAIL!" + a_
      
def get_ascii_id_from_name( name ):
   if tmp_ascii_dict.has_key(name):
       return tmp_ascii_dict[name]
   else:
      return "!FAIL!" + name  


###################################################
## Draw a progress bar on the console
###################################################
def draw_progress_bar( percentage, cur_bar_pos ):
   toolbar_width = 50 #half of the percent to make things easy

   if percentage == 0:
      # setup toolbar
      sys.stdout.write("[%s]" % (" " * toolbar_width))
      sys.stdout.flush()
      sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['

   new_pos = percentage / 2 #div by 2 to match the toolbar_width
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
## Parse Trace and dump the wave form. Returns:
##    - function names used (list of strs)
###################################################
def parse_trace_and_dump_waveform( trace_file, vcd_file, max_records, logging ):
   func_names_used = []
   calls = []

   file_size = os.path.getsize(trace_file)
   total_data_read = 0
   progress_percentage = 0
   cur_bar_pos = 0

   trace = open( trace_file, "rb" )
   vcd = open( vcd_file, "w" )

   #markers in the trace file
   IN = 1
   OUT = 2

   size_of_item = 8 #bytes
   buffer_size_to_read = size_of_item * 16384

   if max_records == 0:
      max_records = file_size / size_of_item   

   if logging:
      print "Parsing trace file:", trace_file

   cur_bar_pos = draw_progress_bar( 0, cur_bar_pos )

   #time pos zero is generated in the header (all signals set to zero to improve the visualization)
   time_in_vcd = 1

   #max data to read
   data_to_read = max_records * size_of_item
   
   if logging == Logging.very_verbose:
      print "Max records:", max_records
      print "Reading data:", data_to_read

   while data_to_read != 0:
      max_data_to_read = buffer_size_to_read if buffer_size_to_read < data_to_read else data_to_read
      data = trace.read( max_data_to_read )
      total_data_read += len(data)
      data_to_read -= len(data)

      if logging == Logging.very_verbose:
         print "Read data:", len(data)

      if len(data) != 0:
         for x in range( 0, len(data), 8 ):
            t = struct.unpack("II", data[x:x+8] )
            op_time = t[0]
            func = t[1]

            op = (op_time >> 24) & 0xFF
            time = op_time & 0xFFFFFF

            if op == IN or op == OUT: 
               func_names_used.append( get_func_name(func) )
               
               new_time = time_in_vcd + time
               if new_time == time_in_vcd:
                  new_time += 1

               vcd.write( "#" + str(new_time) + "\n" )
               if op == IN:
                  vcd.write( "1 " + get_ascii_id_from_addr(func) + "\n" )

               if op == OUT:
                  vcd.write( "0 " + get_ascii_id_from_addr(func) + "\n" )

               time_in_vcd = new_time
            else:
               print "Bad op", op
               sys.exit(-1)

            new_percentage = (total_data_read * 100) / (max_records * size_of_item)
            if progress_percentage != new_percentage:
               cur_bar_pos = draw_progress_bar( new_percentage, cur_bar_pos )
               progress_percentage = new_percentage

      else:
         break

   trace.close()
   vcd.close()

   cur_bar_pos = draw_progress_bar( 100, cur_bar_pos )
   
   #remove the duplices from the function names
   func_names_used = list(set(func_names_used))
   
   return func_names_used



###################################################
## Dump the VCD file
###################################################
def dump_waveform_header( outfile, funcs_used, logging ):
   f = open( outfile, "w" )

   if logging:
      print "Dumping VCD Header"
   
   #first, print all the functions
   f.write( "$date May 20 2013 12:00:05 $end\n" )
   f.write( "$version GCC func to vcd V0.1 $end\n" )
   f.write( "$timescale 1 ns $end\n" )
   f.write( "$scope module top $end\n" )

   for func in sorted(funcs_used):
      f.write( "$var wire 1 " + get_ascii_id_from_name(func) + " " + func + " $end\n"  )

   f.write( "$upscope $end\n" )
   f.write( "$enddefinitions $end\n" )
   
   #initial settings
   f.write( "#0\n" )
   for func in funcs_used:
      f.write( "0 " + get_ascii_id_from_name(func) + "\n" )
   
   f.close()

###################################################
## Main!
###################################################
if __name__ == '__main__':
    
    #parse options
    options = get_options()

    #parse the executable for the symbol map
    load_func_names( options.program, options.logging )
    
    #dump the wave form and get back the func list of things used
    funcs_used = parse_trace_and_dump_waveform( options.tracefile, options.output + "_payload", options.limit, options.logging )    
    
    if options.logging:
       print "There are", len(funcs_used), "functions logged"
    
    dump_waveform_header( options.output + "_header", funcs_used, options.logging )

    #concat the 2 files together

    cmd = "cat " + options.output + "_header " + options.output + "_payload" + " > " + options.output
    if options.logging:
       print "Running cmd: ", cmd
    stream = os.popen(cmd)
    stream.close()

    sys.exit(0)
