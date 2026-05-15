#include "fib.h"

int CFib(int n) {
    if (n <= 1) {
        return n;
    }
    return CFib(n - 1) + CFib(n - 2);
}
