"""Tests for SQLAlchemy ORM persistence models.

These tests verify that the ORM table definitions are structurally correct
and that column names, types, and constraints match what is expected.
No database connection is required — SQLAlchemy's in-memory metadata
inspection is sufficient.
"""

from __future__ import annotations

import sqlalchemy as sa

from src.storage.models import AnalysisJobRow, Base, ChatSettingsRow, ListingRow, RawPayloadRow, UserRow


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

    def test_users_table_registered(self):
        assert "users" in Base.metadata.tables

    def test_chat_settings_table_registered(self):
        assert "chat_settings" in Base.metadata.tables

    def test_raw_payloads_table_registered(self):
        assert "raw_payloads" in Base.metadata.tables


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

    def test_telegram_ids_use_biginteger(self):
        """Telegram supergroup/channel IDs are 64-bit; must not use 32-bit Integer."""
        assert issubclass(type(_col(self._table, "telegram_chat_id").type), sa.BigInteger)
        assert issubclass(type(_col(self._table, "telegram_message_id").type), sa.BigInteger)


# ---------------------------------------------------------------------------
# ListingRow uniqueness constraint
# ---------------------------------------------------------------------------


class TestListingRowConstraints:
    _table: sa.Table = ListingRow.__table__  # type: ignore[attr-defined]

    def test_provider_source_id_unique_constraint_exists(self):
        """get_by_source() assumes at most one row per (provider, source_id)."""
        matching = [
            c for c in self._table.constraints
            if isinstance(c, sa.UniqueConstraint)
            and {col.name for col in c.columns} == {"provider", "source_id"}
        ]
        assert matching, "Missing UniqueConstraint on (provider, source_id) in listings table"


# ---------------------------------------------------------------------------
# UserRow columns
# ---------------------------------------------------------------------------


class TestUserRowColumns:
    _table: sa.Table = UserRow.__table__  # type: ignore[attr-defined]

    def test_primary_key_is_id(self):
        pk_cols = {c.name for c in self._table.primary_key}
        assert pk_cols == {"id"}

    def test_telegram_user_id_exists_and_not_nullable(self):
        col = _col(self._table, "telegram_user_id")
        assert not col.nullable

    def test_telegram_user_id_is_biginteger(self):
        assert issubclass(type(_col(self._table, "telegram_user_id").type), sa.BigInteger)

    def test_telegram_user_id_unique_constraint_exists(self):
        """get_by_telegram_id() requires at most one row per telegram_user_id."""
        # Unique constraint can be declared as a UniqueConstraint or an inline
        # column-level unique=True (which SQLAlchemy also surfaces as a constraint).
        col = _col(self._table, "telegram_user_id")
        has_unique_col = col.unique
        has_unique_constraint = any(
            isinstance(c, sa.UniqueConstraint)
            and {col_.name for col_ in c.columns} == {"telegram_user_id"}
            for c in self._table.constraints
        )
        assert has_unique_col or has_unique_constraint

    def test_optional_profile_columns_are_nullable(self):
        for col_name in ("telegram_username", "first_name", "last_name"):
            col = _col(self._table, col_name)
            assert col.nullable, f"Expected {col_name} to be nullable"

    def test_timestamp_columns_exist_and_not_nullable(self):
        assert not _col(self._table, "created_at").nullable
        assert not _col(self._table, "updated_at").nullable


# ---------------------------------------------------------------------------
# ChatSettingsRow columns
# ---------------------------------------------------------------------------


class TestChatSettingsRowColumns:
    _table: sa.Table = ChatSettingsRow.__table__  # type: ignore[attr-defined]

    def test_primary_key_is_chat_id(self):
        pk_cols = {c.name for c in self._table.primary_key}
        assert pk_cols == {"chat_id"}

    def test_chat_id_is_biginteger(self):
        assert issubclass(type(_col(self._table, "chat_id").type), sa.BigInteger)

    def test_language_column_not_nullable(self):
        assert not _col(self._table, "language").nullable

    def test_language_default_is_ru(self):
        col = _col(self._table, "language")
        assert col.default is not None
        assert col.default.arg == "ru"

    def test_timestamp_columns_exist_and_not_nullable(self):
        assert not _col(self._table, "created_at").nullable
        assert not _col(self._table, "updated_at").nullable


# ---------------------------------------------------------------------------
# RawPayloadRow columns
# ---------------------------------------------------------------------------


class TestRawPayloadRowColumns:
    _table: sa.Table = RawPayloadRow.__table__  # type: ignore[attr-defined]

    def test_primary_key_is_id(self):
        pk_cols = {c.name for c in self._table.primary_key}
        assert pk_cols == {"id"}

    def test_required_columns_exist(self):
        for col_name in ("provider", "source_url", "payload", "captured_at"):
            assert col_name in self._table.c, f"Missing column: {col_name}"

    def test_source_id_is_nullable(self):
        assert _col(self._table, "source_id").nullable

    def test_provider_not_nullable(self):
        assert not _col(self._table, "provider").nullable

    def test_source_url_not_nullable(self):
        assert not _col(self._table, "source_url").nullable

    def test_payload_is_json_and_not_nullable(self):
        col = _col(self._table, "payload")
        assert issubclass(type(col.type), sa.JSON)
        assert not col.nullable

    def test_captured_at_not_nullable(self):
        assert not _col(self._table, "captured_at").nullable

    def test_no_updated_at_column(self):
        """raw_payloads rows are write-once; no updated_at column is needed."""
        assert "updated_at" not in self._table.c
