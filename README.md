### To compile the profiling / test application:

$ gcc prof.c test/test.c -finstrument-functions -g

### then run:

$ ./a.exe 

### To parse the trace.out file (generated when running a.exe)

$ python ./trace_to_vcd.py -t ./trace.out -o ./o.vcd -p ./a.exe

### this generates o.vcd which can then be loaded in your friendly waveform view (gtkwave is recommended)
