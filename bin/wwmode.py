import time
import re
import threading
import shelve
from queue import Queue
from pysnmp.hlapi import SnmpEngine
from utils.snmpget import snmp_run, process_output, get_with_send
from utils.load_settings import Settings
from utils.load_cards import retrive


IFALIAS_OID = '1.3.6.1.2.1.31.1.1.1.18'


class Device:
    def __init__(self, ip):
        self.ip = ip
        self.vlans = []
        self.uplinks = []

    def identify(self, descr):
        for card in device_cards:
            if re.search(card['info_pattern'], descr):
                self.vlan_oid = card['vlan_tree']
                self.vtree = True if 'vlan_tree_by_oid' in card else False
                self.firmware_oid = card['firmware_oid']
                return card['model_oid']


def worker():
    engine = SnmpEngine()
    while True:
        host = q.get()
        if host is None:
            break
        snmp_get = snmp_run(engine, run_set.ro_community, host.exploded,
                            'sysDescr', mib='SNMPv2-MIB')
        error_indication, error_status, error_index, var_binds = next(snmp_get)
        oid, value = process_output(error_indication, error_status, error_index,
                                    var_binds, host.exploded)
        if value:
            device = Device(host.exploded)
            with threading.Lock():
                available_devices.append(device)
            oid, device.location = get_with_send('sysLocation', host.exploded,
                                                 snmp_get, mib='SNMPv2-MIB')
            oid, device.contact = get_with_send('sysContact', host.exploded,
                                                snmp_get, mib='SNMPv2-MIB')
            model_oid = device.identify(value)
            if model_oid:
                oid, device.model = get_with_send(model_oid, host.exploded,
                                                  snmp_get)
                oid, device.firmware = get_with_send(device.firmware_oid,
                                                     host.exploded, snmp_get)
                snmp_next = snmp_run(engine, run_set.ro_community,
                                     host.exploded, device.vlan_oid,
                                     action="next")
                for (error_indication, error_status, error_index,
                     var_binds) in snmp_next:
                    oid, vlan = process_output(
                        error_indication, error_status, error_index, var_binds,
                        host.exploded)
                    if device.vlan_oid not in oid:
                        break
                    if device.vtree:
                        vlan = oid.split('.')[-1]
                    if vlan not in run_set.unneded_vlans:
                        device.vlans.append(vlan)
                snmp_next = snmp_run(engine, run_set.ro_community,
                                     host.exploded, 'ifAlias', mib='IF-MIB',
                                     action="next")
                for (error_indication, error_status, error_index,
                     var_binds) in snmp_next:
                    oid, if_descr = process_output(
                        error_indication, error_status, error_index, var_binds,
                        host.exploded)
                    if IFALIAS_OID not in oid:
                        break
                    if re.match(run_set.uplink_pattern,
                                if_descr):
                        if_index = oid.split('.')[-1]
                        oid, if_speed = get_with_send(
                            'ifHighSpeed', host.exploded, snmp_get,
                            mib='IF-MIB', index=if_index)
                        if_speed = if_speed + ' Mb/s'
                        device.uplinks.append((if_descr, if_speed))
                print('{} ----> {}'.format(host, device.model))
                print('{} ----> {}'.format(host, device.firmware))
                print('{} ----> {}'.format(host, device.uplinks))
                print('{} ----> {}'.format(host, device.vlans))
            else:
                print('{} unrecognized...'.format(host))
        q.task_done()

start_time = time.time()
device_cards = retrive()
available_devices = []
q = Queue()
threads = []
run_set = Settings()
run_set.load_conf()
run_set.num_threads = int(run_set.num_threads)
total_hosts = [x for subnet in run_set.subnets for x in subnet.hosts()]
if run_set.num_threads > len(total_hosts):
    run_set.num_threads = len(total_hosts)
for i in range(run_set.num_threads):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

for item in total_hosts:
    q.put(item)
q.join()

for i in range(run_set.num_threads):
    q.put(None)
for t in threads:
    t.join()
shfile = shelve.open('devdb')
for device in available_devices:
    shfile[device.ip] = device
shfile.close()
print('Total execution time: {:.2f} sec.'.format(time.time() - start_time))
print('Total hosts founded: {}'.format(len(available_devices)))
