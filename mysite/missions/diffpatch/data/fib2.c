#include <stdio.h>
#include <stdlib.h>

/* Find the nth Fibonacci number. */
static int fib(int n)
{
  int prev = 1;
  int current = 0;
  int i;

  for (i = 0; i < n; i++) {
    int next = current + prev;
    prev = current;
    current = next;
  }

  return current;
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
