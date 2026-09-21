from typing import Dict, List, Optional
from pydantic import BaseModel


class ScenarioMetadata(BaseModel):
    scenario_id: str
    name: str
    dataset_source: str
    day: str
    description: str
    mitre_tactics: List[str]
    mitre_techniques: List[str]
    gold_hypothesis: str
    victim_hosts: List[str]
    attacker_ips: List[str]
    raw_filename: str
    normalized_filename: str


SCENARIO_REGISTRY: Dict[str, ScenarioMetadata] = {
    "infiltration": ScenarioMetadata(
        scenario_id="infiltration",
        name="Infiltration & Lateral Movement",
        dataset_source="CSE-CIC-IDS2018",
        day="Thursday-01-03-2018",
        description="Victim workstation downloads malicious payload via web browser, executing a reverse shell followed by local privilege discovery and lateral port scanning against internal servers.",
        mitre_tactics=["Initial Access", "Execution", "Discovery", "Lateral Movement"],
        mitre_techniques=["T1566.001", "T1059.001", "T1046", "T1021.002"],
        gold_hypothesis="Malicious macro/payload executed powershell.exe establishing a reverse shell, subsequently scanning subnet 192.168.1.0/24 for lateral movement.",
        victim_hosts=["WORKSTATION-04", "FILESERVER-01"],
        attacker_ips=["13.58.225.34", "192.168.1.104"],
        raw_filename="Thurs-01-03-2018_Infiltration.csv",
        normalized_filename="infiltration_normalized.jsonl",
    ),
    "brute_force": ScenarioMetadata(
        scenario_id="brute_force",
        name="SSH & FTP Credential Brute Force",
        dataset_source="CSE-CIC-IDS2018",
        day="Wednesday-14-02-2018",
        description="High-velocity automated authentication attempts against SSH (port 22) and FTP (port 21) services, leading to successful password guessing and remote login session.",
        mitre_tactics=["Credential Access", "Initial Access"],
        mitre_techniques=["T1110.001", "T1078"],
        gold_hypothesis="External attacker executed dictionary attack against SSH/FTP, resulting in successful unauthorized authentication.",
        victim_hosts=["UBUNTU-SRV-01", "UBUNTU-SRV-02"],
        attacker_ips=["18.218.115.60", "18.219.9.1"],
        raw_filename="Wed-14-02-2018_BruteForce.csv",
        normalized_filename="brute_force_normalized.jsonl",
    ),
    "web_attacks": ScenarioMetadata(
        scenario_id="web_attacks",
        name="Web Application Exploitation (SQLi / XSS)",
        dataset_source="CSE-CIC-IDS2018",
        day="Thursday-22-02-2018",
        description="Targeted SQL injection queries and Cross-Site Scripting payloads delivered over HTTP port 80 against enterprise web applications, attempting database extraction.",
        mitre_tactics=["Initial Access", "Exfiltration"],
        mitre_techniques=["T1190", "T1041"],
        gold_hypothesis="Attacker exploited input validation vulnerabilities in web app, attempting SQL injection to extract backend records.",
        victim_hosts=["WEB-SRV-01"],
        attacker_ips=["18.218.115.60"],
        raw_filename="Thurs-22-02-2018_WebAttacks.csv",
        normalized_filename="web_attacks_normalized.jsonl",
    ),
    "botnet_c2": ScenarioMetadata(
        scenario_id="botnet_c2",
        name="Botnet Command & Control (Ares C2)",
        dataset_source="CSE-CIC-IDS2018",
        day="Friday-02-03-2018",
        description="Workstations infected with Ares Botnet initiating periodic encrypted beaconing to external C2 nodes and executing received instructions.",
        mitre_tactics=["Command and Control", "Exfiltration"],
        mitre_techniques=["T1071.001", "T1573.001"],
        gold_hypothesis="Internal nodes compromised by Ares botnet establishing periodic C2 beaconing connections to remote IP.",
        victim_hosts=["WORKSTATION-10", "WORKSTATION-12"],
        attacker_ips=["18.219.211.138"],
        raw_filename="Fri-02-03-2018_Botnet.csv",
        normalized_filename="botnet_c2_normalized.jsonl",
    ),
    "dos_goldeneye": ScenarioMetadata(
        scenario_id="dos_goldeneye",
        name="Denial of Service (GoldenEye & Slowloris)",
        dataset_source="CSE-CIC-IDS2018",
        day="Thursday-15-02-2018",
        description="Application-layer DoS keeping HTTP server sockets open indefinitely with incomplete headers, exhausting server connection pools.",
        mitre_tactics=["Impact"],
        mitre_techniques=["T1498.001", "T1499.003"],
        gold_hypothesis="Distributed nodes conducted Slowloris/GoldenEye HTTP starvation attack against port 80.",
        victim_hosts=["WEB-SRV-01"],
        attacker_ips=["18.218.115.60", "18.219.9.1"],
        raw_filename="Thurs-15-02-2018_DoS.csv",
        normalized_filename="dos_goldeneye_normalized.jsonl",
    ),
}


def get_scenario(scenario_id: str) -> Optional[ScenarioMetadata]:
    return SCENARIO_REGISTRY.get(scenario_id)


def list_scenarios() -> List[ScenarioMetadata]:
    return list(SCENARIO_REGISTRY.values())
