#include <omp.h>
#include <stdio.h>
int main(void) {
    int count = 0;
    #pragma omp parallel reduction(+:count)
    count += 1;
    printf("THREADS=%d\n", count);
    return count == 38 ? 0 : 1;
}
