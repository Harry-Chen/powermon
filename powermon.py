#!/usr/bin/env python3

import json
import os
import sys
import time
from subprocess import check_output

from influxdb import InfluxDBClient

dir = os.path.dirname(os.path.realpath(__file__))

config = json.load(open(os.path.join(dir, 'config.json')))
db = InfluxDBClient(
        host=config['host'],
        port=config['port'], 
        database=config['database'],
        username=config['username'],
        password=config['password']
        )

device = config['device']
amc_id = config['amc_id']
adf_id = config['adf_id']
program = os.path.join(dir, config['read_program'])


def read_485(slave_id, start, count):
    command = [program, device, str(slave_id), str(start), str(count)]
    out = check_output(command)
    return out


def generate_body(table, tags, fields):
    json_body = {
            "measurement": table,
            "tags": tags,
            "fields": fields
    }
    return json_body


def parse_amc_value(a, b):
    return a * pow(10, b - 3)


def generate_amc_point(phase, current):
    tags = {
            "device": "amc",
            "metric": "current",
            "phase": phase
    }
    fields = {
            "value": current
    }
    return generate_body('power', tags, fields)


def generate_adf_point(location, metric, value, phase=None):
    tags = {
        "device": "adf",
        "metric": metric,
        "location": location
    }

    if phase is not None:
        tags["phase"] = phase

    fields = {
        "value": float(value)
    }
    return generate_body('power', tags, fields)


def get_from_amc():
    values = [int(x, 16) for x in read_485(amc_id, 0x06, 0x06).strip().split()]
    
    points = []
    points.append(generate_amc_point('A', parse_amc_value(values[0], values[1])))
    points.append(generate_amc_point('B', parse_amc_value(values[2], values[3])))
    points.append(generate_amc_point('C', parse_amc_value(values[4], values[5])))
    
    db.write_points(points)


def read_adf_part(location, offset):
    values = [int(x, 16) for x in read_485(adf_id + offset, 0x033F, 35).strip().split()]

    points = []

    concat = lambda x: (x[0] << 16) + x[1]

    # voltage (V)
    points.append(generate_adf_point(location, 'voltage', values[0] * 0.1, 'A'))
    points.append(generate_adf_point(location, 'voltage', values[1] * 0.1, 'B'))
    points.append(generate_adf_point(location, 'voltage', values[2] * 0.1, 'C'))
    # current (A)
    points.append(generate_adf_point(location, 'current', values[3] * 0.01, 'A'))
    points.append(generate_adf_point(location, 'current', values[4] * 0.01, 'B'))
    points.append(generate_adf_point(location, 'current', values[5] * 0.01, 'C'))
    # active power (W)
    points.append(generate_adf_point(location, 'active_power', values[7] + values[8] + values[9], 'total')) # workaround for overflow
    points.append(generate_adf_point(location, 'active_power', values[7], 'A'))
    points.append(generate_adf_point(location, 'active_power', values[8], 'B'))
    points.append(generate_adf_point(location, 'active_power', values[9], 'C'))
    # reactive power (Var)
    points.append(generate_adf_point(location, 'reactive_power', values[10], 'total'))
    points.append(generate_adf_point(location, 'reactive_power', values[11], 'A'))
    points.append(generate_adf_point(location, 'reactive_power', values[12], 'B'))
    points.append(generate_adf_point(location, 'reactive_power', values[13], 'C'))
    # power factor
    points.append(generate_adf_point(location, 'power_factor', values[14] * 0.001, 'total'))
    points.append(generate_adf_point(location, 'power_factor', values[15] * 0.001, 'A'))
    points.append(generate_adf_point(location, 'power_factor', values[16] * 0.001, 'B'))
    points.append(generate_adf_point(location, 'power_factor', values[17] * 0.001, 'C'))
    # frequency (Hz)
    points.append(generate_adf_point(location, 'frequency', values[18] * 0.01))
    # active energy (kWh)
    points.append(generate_adf_point(location, 'active_energy', concat(values[31:33]) * 0.01, 'total'))
    points.append(generate_adf_point(location, 'active_energy', concat(values[19:21]) * 0.01, 'A'))
    points.append(generate_adf_point(location, 'active_energy', concat(values[21:23]) * 0.01, 'B'))
    points.append(generate_adf_point(location, 'active_energy', concat(values[23:25]) * 0.01, 'C'))
    # reactive energy (kVarh)
    points.append(generate_adf_point(location, 'reactive_energy', concat(values[33:35]) * 0.01, 'total'))
    points.append(generate_adf_point(location, 'reactive_energy', concat(values[25:27]) * 0.01, 'A'))
    points.append(generate_adf_point(location, 'reactive_energy', concat(values[27:29]) * 0.01, 'B'))
    points.append(generate_adf_point(location, 'reactive_energy', concat(values[29:31]) * 0.01, 'C'))

    db.write_points(points)
    

def get_from_adf():
    read_adf_part("north", 0)
    read_adf_part("middle", 3)
    read_adf_part("south", 6)


if __name__ == '__main__':
    
    print(json.dumps(config), file=sys.stderr)
    
    while True:
        try:
            print('====')
            get_from_amc()
            get_from_adf()
            time.sleep(0.5)
        except Exception as e:
            print(e, file=sys.stderr)
            time.sleep(0.5)

