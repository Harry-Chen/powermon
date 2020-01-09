#include <stdio.h>
#include <modbus/modbus.h>
#include <stdlib.h>
#include <errno.h>
#include <assert.h>

int main(int argc, char *argv[]) {
    modbus_t *mb;
    uint16_t tab_reg[128];

    if (argc != 5) {
        fprintf(stderr, "Usage: %s /dev/ttyUSB0 slave_id address count\n", argv[0]);
        exit(1);
    }

    char *device = argv[1];
    int slave_id, start_addr, count;

    int ret = sscanf(argv[2], "%d", &slave_id);
    assert(ret == 1);
    ret = sscanf(argv[3], "%d", &start_addr);
    assert(ret == 1);
    ret = sscanf(argv[4], "%d", &count);
    assert(ret == 1);
    assert(count <= 128);


    mb = modbus_new_rtu(argv[1], 9600, 'N', 8, 1);
    modbus_set_slave(mb, slave_id);
    modbus_connect(mb);

    ret = modbus_read_registers(mb, start_addr, count, tab_reg);

    if (ret == -1) {
        fprintf(stderr, "%s\n", modbus_strerror(errno));
        return -1;
    }


    for (int i = 0; i < ret; ++i) {
        printf("0x%x ", tab_reg[i]);
    }

    printf("\n");

    modbus_close(mb);
    modbus_free(mb);

    return 0;
}

