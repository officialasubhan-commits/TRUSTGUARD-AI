"""
Threat Intelligence repository operations.
Interacts with public.threat_reports table in Supabase PostgreSQL.
Handles machine-generated threat intelligence records (VirusTotal, URLhaus, ML findings).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.exceptions import DatabaseError
from app.database import connection
from app.schemas.threat_intel import ThreatIntelCreate, ThreatIntelResponse

logger = logging.getLogger("trustguard.repo.threat")

_mock_threats_store: Dict[uuid.UUID, Dict[str, Any]] = {}


class ThreatRepository:
    def __init__(self, client=None):
        self._client = client or connection.supabase_client

    async def save_threat_record(
        self,
        intel_in: ThreatIntelCreate,
    ) -> ThreatIntelResponse:
        """
        Saves a verified threat intelligence record.
        Only executed by backend service role during URL analysis.
        """
        record_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        record = {
            "id": str(record_id),
            "scan_id": str(intel_in.scan_id) if intel_in.scan_id else None,
            "normalized_url": intel_in.normalized_url,
            "domain": intel_in.domain,
            "threat_source": intel_in.threat_source,
            "threat_category": intel_in.threat_category,
            "severity": intel_in.severity,
            "verification_status": intel_in.verification_status,
            "first_seen_at": intel_in.first_seen_at.isoformat()
            if intel_in.first_seen_at
            else now.isoformat(),
            "last_seen_at": intel_in.last_seen_at.isoformat()
            if intel_in.last_seen_at
            else now.isoformat(),
            "raw_data": intel_in.raw_data,
            "created_at": now.isoformat(),
        }

        if self._client is not None:
            try:
                res = self._client.table("threat_reports").insert(record).execute()
                if res.data:
                    return ThreatIntelResponse.model_validate(res.data[0])
                raise DatabaseError("Database insert into threat_reports returned empty response.")
            except Exception as e:
                logger.error("Supabase insert threat_reports failed: %s", e)
                raise DatabaseError(
                    f"Failed to persist threat record to database: {e}. "
                    "If using Supabase, ensure migration 000_full_schema.sql has been executed."
                ) from e

        # Local fallback (only when Supabase client is unconfigured)
        _mock_threats_store[record_id] = {
            **record,
            "id": record_id,
            "scan_id": intel_in.scan_id,
            "first_seen_at": intel_in.first_seen_at or now,
            "last_seen_at": intel_in.last_seen_at or now,
            "created_at": now,
        }
        return ThreatIntelResponse.model_validate(_mock_threats_store[record_id])

    async def get_threat_records_by_url(self, normalized_url: str) -> List[ThreatIntelResponse]:
        """
        Retrieves threat intelligence records matching a normalized URL.
        """
        if self._client is not None:
            try:
                res = (
                    self._client.table("threat_reports")
                    .select("*")
                    .eq("normalized_url", normalized_url)
                    .order("created_at", desc=True)
                    .execute()
                )
                return [ThreatIntelResponse.model_validate(r) for r in res.data]
            except Exception as e:
                logger.error("Supabase select threat_reports by url error: %s", e)
                raise DatabaseError(f"Database error fetching threat records: {e}")

        records = [
            r for r in _mock_threats_store.values() if r.get("normalized_url") == normalized_url
        ]
        return [ThreatIntelResponse.model_validate(r) for r in records]

    async def get_threat_records_by_domain(self, domain: str) -> List[ThreatIntelResponse]:
        """
        Retrieves threat intelligence records matching a domain name.
        """
        if self._client is not None:
            try:
                res = (
                    self._client.table("threat_reports")
                    .select("*")
                    .eq("domain", domain)
                    .order("created_at", desc=True)
                    .execute()
                )
                return [ThreatIntelResponse.model_validate(r) for r in res.data]
            except Exception as e:
                logger.error("Supabase select threat_reports by domain error: %s", e)
                raise DatabaseError(f"Database error fetching domain threats: {e}")

        records = [r for r in _mock_threats_store.values() if r.get("domain") == domain]
        return [ThreatIntelResponse.model_validate(r) for r in records]
