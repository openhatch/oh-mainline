#include <stdio.h>
#include <stdlib.h>

/* Find the nth Fibonacci number. */
static int fib(int n)
{
  if (n <= 0)
    return 0;
  if (n == 1)
    return 1;
  return fib(n - 1) + fib(n - 2);
}

int main(int argc, char** argv)
{
  if (argc < 2) {
    fprintf(stderr, "Need an argument.\n");
    return 1;
  }

  printf("%d\n", fib(atoi(argv[1])));
  return 0;
}
