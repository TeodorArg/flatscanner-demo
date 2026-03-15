"""Tests for SQLAlchemy ORM persistence models.

These tests verify that the ORM table definitions are structurally correct
and that column names, types, and constraints match what is expected.
No database connection is required — SQLAlchemy's in-memory metadata
inspection is sufficient.
"""

from __future__ import annotations

import sqlalchemy as sa

from src.storage.models import AnalysisJobRow, Base, ListingRow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _col(table: sa.Table, name: str) -> sa.Column:
    return table.c[name]


# ---------------------------------------------------------------------------
# Base metadata
# ---------------------------------------------------------------------------


class TestBaseMetadata:
    def test_listings_table_registered(self):
        assert "listings" in Base.metadata.tables

    def test_analysis_jobs_table_registered(self):
        assert "analysis_jobs" in Base.metadata.tables


# ---------------------------------------------------------------------------
# ListingRow columns
# ---------------------------------------------------------------------------


class TestListingRowColumns:
    _table: sa.Table = ListingRow.__table__  # type: ignore[attr-defined]

    def test_primary_key_is_id(self):
        pk_cols = {c.name for c in self._table.primary_key}
        assert pk_cols == {"id"}

    def test_required_text_columns_exist(self):
        for col_name in ("source_url", "title", "provider", "source_id"):
            assert col_name in self._table.c, f"Missing column: {col_name}"

    def test_nullable_location_columns(self):
        for col_name in ("latitude", "longitude", "address", "city", "country", "neighbourhood"):
            col = _col(self._table, col_name)
            assert col.nullable, f"Expected {col_name} to be nullable"

    def test_nullable_price_columns(self):
        for col_name in ("price_amount", "price_currency", "price_period", "cleaning_fee", "service_fee"):
            col = _col(self._table, col_name)
            assert col.nullable, f"Expected {col_name} to be nullable"

    def test_nullable_property_columns(self):
        for col_name in ("bedrooms", "bathrooms", "max_guests", "rating", "review_count"):
            col = _col(self._table, col_name)
            assert col.nullable, f"Expected {col_name} to be nullable"

    def test_nullable_host_columns(self):
        assert _col(self._table, "host_name").nullable
        assert _col(self._table, "host_is_superhost").nullable

    def test_amenities_and_raw_payload_are_json(self):
        amenities_type = type(_col(self._table, "amenities").type)
        raw_type = type(_col(self._table, "raw_payload").type)
        assert issubclass(amenities_type, sa.JSON)
        assert issubclass(raw_type, sa.JSON)

    def test_timestamp_columns_exist(self):
        assert "created_at" in self._table.c
        assert "updated_at" in self._table.c

    def test_timestamp_columns_not_nullable(self):
        assert not _col(self._table, "created_at").nullable
        assert not _col(self._table, "updated_at").nullable


# ---------------------------------------------------------------------------
# AnalysisJobRow columns
# ---------------------------------------------------------------------------


class TestAnalysisJobRowColumns:
    _table: sa.Table = AnalysisJobRow.__table__  # type: ignore[attr-defined]

    def test_primary_key_is_id(self):
        pk_cols = {c.name for c in self._table.primary_key}
        assert pk_cols == {"id"}

    def test_required_columns_exist(self):
        for col_name in ("source_url", "provider", "status", "telegram_chat_id", "telegram_message_id"):
            assert col_name in self._table.c, f"Missing column: {col_name}"

    def test_listing_id_is_nullable_foreign_key(self):
        col = _col(self._table, "listing_id")
        assert col.nullable
        fk_tables = {fk.column.table.name for fk in col.foreign_keys}
        assert "listings" in fk_tables

    def test_error_message_is_nullable(self):
        assert _col(self._table, "error_message").nullable

    def test_timestamp_columns_exist_and_not_nullable(self):
        assert not _col(self._table, "created_at").nullable
        assert not _col(self._table, "updated_at").nullable

    def test_status_default_is_pending(self):
        col = _col(self._table, "status")
        assert col.default is not None
        assert col.default.arg == "pending"
