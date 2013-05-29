#include <stdio.h>
#include <stdlib.h>


void FISH3( int i )
{
   if (i)
      FISH3(i - 1);
}


void FISH2( void )
{
   FISH3(4);
}

void FISH( void )
{
   printf("Starting to fish...");
   FISH2();
   printf("Done!\n");
}


int main( void )
{
   printf("Main\n");
   FISH();

   return 0;
}
