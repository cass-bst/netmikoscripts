#!/usr/bin/env python3
"""
Seção 5 - Habilitação do SNMP nos roteadores + monitoramento de octetos.

1) Habilita o SNMP (community string própria) em R1, R2 e R3 via Netmiko.
2) A cada 10s, consulta via SNMPv2c os octetos de entrada/saida da e0/0
   (Ethernet0/0) de cada roteador e imprime no formato pedido.

Ajuste host/username/password e as community strings ao seu cenário.

Dependências:
    pip install netmiko pysnmp
"""

import time

from netmiko import ConnectHandler
from pysnmp.hlapi import (
    getCmd,
    nextCmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
)

# --- Roteadores -----------------------------------------------------------
R1 = {
    "device_type": "cisco_ios",
    "host": "10.0.12.1",
    "username": "ruan",
    "password": "gomes",
    "secret": "gomes",
    "fast_cli": False,
    "global_delay_factor": 2,
}
R2 = {
    "device_type": "cisco_ios",
    "host": "10.0.12.2",
    "username": "ruan",
    "password": "gomes",
    "secret": "gomes",
    "fast_cli": False,
    "global_delay_factor": 2,
}
R3 = {
    "device_type": "cisco_ios",
    "host": "10.0.23.2",
    "username": "ruan",
    "password": "gomes",
    "secret": "gomes",
    "fast_cli": False,
    "global_delay_factor": 2,
}

routers = [R1, R2, R3]
# Uma community string por roteador (mesma ordem da lista de roteadores).
communities = ["comunidade1", "comunidade2", "comunidade3"]

# OIDs da IF-MIB
OID_IF_DESCR = "1.3.6.1.2.1.2.2.1.2"   # ifDescr
OID_IN_OCT = "1.3.6.1.2.1.2.2.1.10"    # ifInOctets
OID_OUT_OCT = "1.3.6.1.2.1.2.2.1.16"   # ifOutOctets

INTERFACE = "Ethernet0/0"  # IOL no PNETLab usa Ethernet0/X (e0/0), nao Gigabit


# --- Funções auxiliares de SNMP ------------------------------------------
def snmp_get(host, community, oid):
    """Faz um GET SNMPv2c de um OID e retorna o valor como int (ou None)."""
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),  # mpModel=1 => SNMPv2c
        UdpTransportTarget((host, 161), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    error_indication, error_status, _, var_binds = next(iterator)
    if error_indication or error_status:
        return None
    for var_bind in var_binds:
        return int(var_bind[1])
    return None


def find_ifindex(host, community, iface_name):
    """Descobre o ifIndex de uma interface pelo nome (faz walk em ifDescr)."""
    for (err_ind, err_stat, _, var_binds) in nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        UdpTransportTarget((host, 161), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(OID_IF_DESCR)),
        lexicographicMode=False,
    ):
        if err_ind or err_stat:
            break
        for oid, value in var_binds:
            if str(value) == iface_name:
                # o ifIndex é o último número do OID
                return int(str(oid).split(".")[-1])
    return None


# --- 1) Habilita o SNMP em cada roteador ----------------------------------
for router, community in zip(routers, communities):
    connect = ConnectHandler(**router)
    connect.enable()  # garante modo privilegiado
    print(f"Habilitando SNMP em {router['host']} (community: {community})")
    connect.send_config_set(
        [f"snmp-server community {community} RO"], read_timeout=30
    )
    connect.save_config()
    connect.disconnect()

# --- Descobre o ifIndex da G0/0 em cada roteador (uma vez) ----------------
ifindex = {}
for router, community in zip(routers, communities):
    idx = find_ifindex(router["host"], community, INTERFACE)
    ifindex[router["host"]] = idx
    if idx is None:
        print(f"[AVISO] Nao achei {INTERFACE} em {router['host']}")

# --- 2) Loop de monitoramento ---------------------------------------------
try:
    while True:
        print("============")
        for i, (router, community) in enumerate(zip(routers, communities), start=1):
            host = router["host"]
            idx = ifindex[host]
            if idx is None:
                print(f"R{i} = in: N/A out: N/A")
                continue
            in_oct = snmp_get(host, community, f"{OID_IN_OCT}.{idx}")
            out_oct = snmp_get(host, community, f"{OID_OUT_OCT}.{idx}")
            print(f"R{i} = in: {in_oct} out: {out_oct}")
        print("============")
        time.sleep(10)
except KeyboardInterrupt:
    print("\nMonitoramento encerrado")
