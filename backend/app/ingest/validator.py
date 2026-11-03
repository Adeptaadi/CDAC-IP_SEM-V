import os
import hashlib
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.ingest.downloader import RAW_DIR, NORMALIZED_DIR, ensure_directories
from app.ingest.scenarios import SCENARIO_REGISTRY
from app.repositories.dataset_repo import DatasetRepository


class DatasetValidationError(Exception):
    pass


class DatasetValidator:
    """Validates cybersecurity dataset files for integrity, schema consistency, and format compliance (Phase 3)."""

    REQUIRED_TELEMETRY_FIELDS = ["timestamp"]

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        """Computes deterministic SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha256.update(block)
        return sha256.hexdigest()

    @classmethod
    def inspect_and_validate_file(cls, file_path: str) -> Dict[str, Any]:
        """Inspects format, headers, missing values, encoding, and data quality."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        file_size_bytes = os.path.getsize(file_path)
        checksum = cls.compute_sha256(file_path)

        # Detect format: JSONL, JSON, or CSV
        file_format = "unknown"
        records_count = 0
        columns: List[str] = []
        missing_values_count = 0
        sample_records: List[Dict[str, Any]] = []
        validation_errors: List[str] = []

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            first_char = f.read(1)
            f.seek(0)

            if first_char == "[":
                # JSON array format
                file_format = "json"
                try:
                    data = json.load(f)
                    records_count = len(data)
                    if records_count > 0:
                        columns = list(data[0].keys())
                        sample_records = data[:3]
                        for row in data:
                            for k, v in row.items():
                                if v is None or v == "":
                                    missing_values_count += 1
                except Exception as e:
                    validation_errors.append(f"Invalid JSON format: {str(e)}")

            elif file_path.endswith(".jsonl"):
                # JSONL format
                file_format = "jsonl"
                for idx, line in enumerate(f):
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = json.loads(line_str)
                        records_count += 1
                        if records_count == 1:
                            columns = list(record.keys())
                        if records_count <= 3:
                            sample_records.append(record)
                        for k, v in record.items():
                            if v is None or v == "":
                                missing_values_count += 1
                    except Exception as e:
                        validation_errors.append(f"Invalid JSON line at index {idx}: {str(e)}")

            else:
                # CSV format
                file_format = "csv"
                try:
                    reader = csv.DictReader(f)
                    columns = reader.fieldnames or []
                    for row in reader:
                        records_count += 1
                        if records_count <= 3:
                            sample_records.append(dict(row))
                        for k, v in row.items():
                            if v is None or v.strip() == "":
                                missing_values_count += 1
                except Exception as e:
                    validation_errors.append(f"CSV parsing error: {str(e)}")

        # Validate required fields
        has_timestamp = any("time" in c.lower() or "timestamp" in c.lower() for c in columns)
        if not has_timestamp:
            validation_errors.append("Dataset file is missing required timestamp field.")

        status = "valid"
        if validation_errors:
            status = "invalid" if records_count == 0 else "warning"

        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "file_format": file_format,
            "file_size_bytes": file_size_bytes,
            "checksum": checksum,
            "record_count": records_count,
            "columns": columns,
            "missing_values_count": missing_values_count,
            "validation_status": status,
            "validation_errors": validation_errors,
            "sample_record": sample_records[0] if sample_records else None,
        }

    @classmethod
    def register_scenario_dataset(cls, scenario_id: str, db: Session) -> Dict[str, Any]:
        """Registers a scenario dataset and its associated files in PostgreSQL with validated metadata."""
        scenario = SCENARIO_REGISTRY.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        ensure_directories()
        raw_path = os.path.join(RAW_DIR, scenario.raw_filename)
        norm_path = os.path.join(NORMALIZED_DIR, scenario.normalized_filename)

        # Prepare if absent
        if not os.path.exists(raw_path):
            from app.ingest.downloader import prepare_scenario
            prepare_scenario(scenario_id)
        if not os.path.exists(norm_path):
            from app.ingest.normalizer import TelemetryNormalizer
            TelemetryNormalizer.normalize_scenario_file(scenario_id)

        raw_meta = cls.inspect_and_validate_file(raw_path)
        norm_meta = cls.inspect_and_validate_file(norm_path)

        repo = DatasetRepository(db)

        # Register or update dataset record
        ds = repo.register_dataset(
            name=f"{scenario.name} ({scenario.dataset_source})",
            dataset_type="network_flow" if "flow" in scenario.name.lower() else "mixed",
            version="1.0.0",
            description=scenario.description,
            source=scenario.dataset_source,
            checksum=raw_meta["checksum"],
            metadata={
                "scenario_id": scenario.scenario_id,
                "mitre_tactics": scenario.mitre_tactics,
                "mitre_techniques": scenario.mitre_techniques,
                "victim_hosts": scenario.victim_hosts,
                "attacker_ips": scenario.attacker_ips,
            },
        )

        # Register raw and normalized dataset files
        raw_file = repo.add_dataset_file(
            dataset_id=ds.id,
            filename=scenario.raw_filename,
            storage_uri=raw_path,
            file_format=raw_meta["file_format"],
            file_size_bytes=raw_meta["file_size_bytes"],
            record_count=raw_meta["record_count"],
            checksum=raw_meta["checksum"],
            schema_metadata={"columns": raw_meta["columns"], "missing_values": raw_meta["missing_values_count"]},
        )

        norm_file = repo.add_dataset_file(
            dataset_id=ds.id,
            filename=scenario.normalized_filename,
            storage_uri=norm_path,
            file_format=norm_meta["file_format"],
            file_size_bytes=norm_meta["file_size_bytes"],
            record_count=norm_meta["record_count"],
            checksum=norm_meta["checksum"],
            schema_metadata={"columns": norm_meta["columns"], "missing_values": norm_meta["missing_values_count"]},
        )

        db.commit()

        return {
            "dataset_id": str(ds.id),
            "name": ds.name,
            "raw_file": {
                "id": str(raw_file.id),
                "checksum": raw_meta["checksum"],
                "records": raw_meta["record_count"],
                "status": raw_meta["validation_status"],
            },
            "normalized_file": {
                "id": str(norm_file.id),
                "checksum": norm_meta["checksum"],
                "records": norm_meta["record_count"],
                "status": norm_meta["validation_status"],
            },
        }
