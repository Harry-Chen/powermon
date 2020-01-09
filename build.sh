#!/bin/bash
gcc -I /home/harry/.local/include read_485.c -L /home/harry/.local/lib -lmodbus -lm -static -o read_485
