#include <stdio.h>

int main(void) {
    char buffer[32];
    freopen("../root/a.dat", "r", stdin);
    size_t size = fread(buffer, 1, 32, stdin);
    fwrite(buffer, 1, size, stdout);
    return ferror(stdin);
}
