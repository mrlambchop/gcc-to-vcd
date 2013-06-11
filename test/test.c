//#   Licensed under the Apache License, Version 2.0 (the "License");
//#   you may not use this file except in compliance with the License.
//#   You may obtain a copy of the License at
//#
//#       http://www.apache.org/licenses/LICENSE-2.0
//#
//#   Unless required by applicable law or agreed to in writing, software
//#   distributed under the License is distributed on an "AS IS" BASIS,
//#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//#   See the License for the specific language governing permissions and
//#   limitations under the License.

#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <unistd.h>

void FISH3( int i )
{
   if (i)
   {
      FISH3(i - 1);
      usleep( i * 1000 );
   }
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
