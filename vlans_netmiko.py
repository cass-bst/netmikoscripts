#!/usr/bin/env python3
"""
Seção 4 - Automação da criação de VLANs com Netmiko.

Cria as VLANs 2 (Alunos), 3 (Professores) e 4 (Tecnicos) em S1, S2 e S3,
verifica com 'show vlan brief' e salva a config em cada switch.

Ajuste host/username/password de acordo com o seu cenário no GNS3.
"""

from netmiko import ConnectHandler

# --- Switch(es) a serem configurados -------------------------------------
# A topologia do PNETLab tem só o SW1. Se precisar dos três switches do
# roteiro, é só descomentar S2/S3 e adicioná-los na lista 'switches'.
SW1 = {
    "device_type": "cisco_ios",
    "host": "192.168.10.2",
    "username": "ruan",
    "password": "gomes",
    "secret": "gomes",
    "fast_cli": False,
    "global_delay_factor": 2,
}
# S2 = {"device_type": "cisco_ios", "host": "192.168.2.102",
#       "username": "ruan", "password": "gomes"}
# S3 = {"device_type": "cisco_ios", "host": "192.168.3.103",
#       "username": "ruan", "password": "gomes"}

switches = [SW1]  # ex.: [SW1, S2, S3]

# --- VLANs: (id, nome) ----------------------------------------------------
# Obs.: o IOS aceita só ASCII em nome de VLAN, então uso "Tecnicos" sem acento.
vlans = [
    (2, "Alunos"),
    (3, "Professores"),
    (4, "Tecnicos"),
]

# Monta a lista de comandos a partir das tuplas de VLAN.
# O 'enable' e o 'conf t' são abstraídos pelo send_config_set.
cfg_list = []
for vlan_id, vlan_name in vlans:
    cfg_list += [
        f"vlan {vlan_id}",
        f"name {vlan_name}",
        "exit",
    ]

# --- Configura cada switch ------------------------------------------------
for sw in switches:
    connect = ConnectHandler(**sw)
    connect.enable()  # garante modo privilegiado antes de configurar
    print(f"\n===== Configurando {sw['host']} =====")

    # Cria as VLANs
    output = connect.send_config_set(cfg_list, read_timeout=30)
    print(output)

    # Verifica se as VLANs foram criadas
    print(connect.send_command("show vlan brief"))

    # Persiste running-config -> startup-config
    connect.save_config()
    connect.disconnect()

print("\nScript finalizado")
