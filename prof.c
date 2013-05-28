#include <stdio.h>
#include <stdlib.h>


#define IN 1// 'I'
#define OUT 2 // 'O'

#define STACK_SIZE         (0xFFFF + 32) //what? flushing is done using the marker below on a pow of 2 boundary for cheap testing
#define STACK_FULL_MARKER  (0x10000)

static FILE *fp_trace = NULL; //trace file
static void *stack = NULL;
static int stack_index = 0;
unsigned long last_time = 0;

#define STACK_ADD_UINT16( val )     ((uint16_t *)stack)[stack_index] = (uint16_t)(val); stack_index += sizeof(uint16_t); // This only works on certain CPUs as it causes the 32bit data to be written on 16bit boundaries
#define STACK_ADD_UINT32( val )     ((uint32_t *)stack)[stack_index] = (uint32_t)(val); stack_index += sizeof(uint32_t);
#define STACK_FULL()                (stack_index & STACK_FULL_MARKER)

#define FLUSH()                     fwrite( stack, stack_index, 1 * 4, fp_trace); stack_index = 0;


void __attribute__((no_instrument_function)) __cyg_profile_func_enter(void *this_fn, void *call_site)
{
   if( !stack || !fp_trace)
      return;

   STACK_ADD_UINT32( IN );
   STACK_ADD_UINT32( this_fn );
   STACK_ADD_UINT32( call_site );
   STACK_ADD_UINT32( time(NULL) );

   if ( STACK_FULL() )
      FLUSH();
}

void __attribute__((no_instrument_function)) __cyg_profile_func_exit(void *this_fn, void *call_site)
{
   if( !stack || !fp_trace)
      return;

   STACK_ADD_UINT32( OUT );
   STACK_ADD_UINT32( this_fn );
   STACK_ADD_UINT32( call_site );
   STACK_ADD_UINT32( time(NULL) );

   if ( STACK_FULL() )
      FLUSH();
}



void __attribute__((no_instrument_function)) __attribute__ ((constructor)) trace_begin (void)
{
   fp_trace = fopen("./trace.out", "w");
   stack = calloc( 1, sizeof( unsigned int ) * STACK_SIZE );
}


void __attribute__((no_instrument_function)) __attribute__ ((destructor)) trace_end (void)
{
   if(fp_trace != NULL)
   {
      FLUSH();

      fclose(fp_trace);
      fp_trace = NULL;

      if( !stack )
         free(stack);
         stack = NULL;
   }
}