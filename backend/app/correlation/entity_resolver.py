import re
import uuid
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.correlation import Entity
from app.correlation.contracts import ResolvedEntity


class EntityResolver:
    """Extracts, normalizes, and reconciles security entities across telemetry and findings (Phase 6)."""

    def __init__(self):
        self._cache: Dict[Tuple[str, str], ResolvedEntity] = {}

    @staticmethod
    def normalize_ip(ip_str: Optional[str]) -> Optional[str]:
        """Normalizes IP address, stripping ports and whitespace."""
        if not ip_str:
            return None
        cleaned = ip_str.strip()
        # Handle IP:Port like 192.168.1.1:8080
        if ":" in cleaned and not cleaned.startswith("[") and cleaned.count(":") == 1:
            cleaned = cleaned.split(":")[0]
        return cleaned.lower()

    @staticmethod
    def normalize_host(host_str: Optional[str]) -> Optional[str]:
        """Normalizes hostname into uppercase base hostname."""
        if not host_str:
            return None
        cleaned = host_str.strip().upper()
        # Strip domain if FQDN (e.g. WORKSTATION-01.CORP.LOCAL -> WORKSTATION-01)
        if "." in cleaned and not re.match(r"^\d+\.\d+\.\d+\.\d+$", cleaned):
            cleaned = cleaned.split(".")[0]
        return cleaned

    @staticmethod
    def normalize_user(user_str: Optional[str]) -> Optional[str]:
        """Normalizes user account name, stripping domain prefix."""
        if not user_str:
            return None
        cleaned = user_str.strip()
        # Strip DOMAIN\username or username@domain
        if "\\" in cleaned:
            cleaned = cleaned.split("\\")[-1]
        elif "@" in cleaned:
            cleaned = cleaned.split("@")[0]
        return cleaned.lower()

    @staticmethod
    def normalize_process(proc_str: Optional[str]) -> Optional[str]:
        """Normalizes process executable path to executable basename."""
        if not proc_str:
            return None
        cleaned = proc_str.strip()
        # Extract filename from path (e.g., C:\Windows\System32\cmd.exe -> cmd.exe)
        cleaned = cleaned.replace("/", "\\")
        base = cleaned.split("\\")[-1]
        return base.lower()

    def resolve_entity(
        self,
        entity_type: str,
        raw_identifier: str,
        db: Optional[Session] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ResolvedEntity]:
        """Normalizes identifier, retrieves or creates the entity in-memory and in DB."""
        if not raw_identifier:
            return None

        etype = entity_type.lower()
        if etype == "ip":
            norm_id = self.normalize_ip(raw_identifier)
        elif etype in ["host", "hostname"]:
            norm_id = self.normalize_host(raw_identifier)
            etype = "host"
        elif etype in ["user", "username"]:
            norm_id = self.normalize_user(raw_identifier)
            etype = "user"
        elif etype in ["process", "proc"]:
            norm_id = self.normalize_process(raw_identifier)
            etype = "process"
        else:
            norm_id = raw_identifier.strip().lower()

        if not norm_id:
            return None

        cache_key = (etype, norm_id)
        now = datetime.utcnow()

        if cache_key in self._cache:
            cached = self._cache[cache_key]
            cached.last_seen_at = now
            return cached

        # Check DB if provided
        entity_id = uuid.uuid4()
        if db is not None:
            existing_db = (
                db.query(Entity)
                .filter(Entity.entity_type == etype, Entity.identifier == norm_id)
                .first()
            )
            if existing_db:
                existing_db.last_seen_at = now
                entity_id = existing_db.id
            else:
                new_db = Entity(
                    id=entity_id,
                    entity_type=etype,
                    identifier=norm_id,
                    display_name=f"{etype.title()}: {norm_id}",
                    entity_metadata=metadata or {},
                    first_seen_at=now,
                    last_seen_at=now,
                    created_at=now,
                )
                db.add(new_db)
                try:
                    db.commit()
                except Exception:
                    db.rollback()

        resolved = ResolvedEntity(
            id=entity_id,
            entity_type=etype,
            identifier=norm_id,
            display_name=f"{etype.title()}: {norm_id}",
            metadata=metadata or {},
            first_seen_at=now,
            last_seen_at=now,
        )
        self._cache[cache_key] = resolved
        return resolved

    def extract_and_resolve_from_event(
        self,
        event: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> List[ResolvedEntity]:
        """Extracts and resolves all entities present in a single security event."""
        resolved: List[ResolvedEntity] = []

        # Hosts
        host = event.get("host") or event.get("source_identifier") or event.get("hostname")
        if host:
            h_ent = self.resolve_entity("host", str(host), db=db)
            if h_ent:
                resolved.append(h_ent)

        # Users
        user = event.get("user") or event.get("username")
        if user:
            u_ent = self.resolve_entity("user", str(user), db=db)
            if u_ent:
                resolved.append(u_ent)

        # IPs
        for ip_field in ["src_ip", "dest_ip", "source_ip", "destination_ip"]:
            ip_val = event.get(ip_field)
            if ip_val:
                ip_ent = self.resolve_entity("ip", str(ip_val), db=db)
                if ip_ent and ip_ent not in resolved:
                    resolved.append(ip_ent)

        # Processes
        proc = event.get("process_name") or event.get("image")
        if proc:
            p_ent = self.resolve_entity("process", str(proc), db=db)
            if p_ent:
                resolved.append(p_ent)

        return resolved


entity_resolver_instance = EntityResolver()
