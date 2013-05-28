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
   FISH2();
}


int main( void )
{
   FISH();

   return 0;
}