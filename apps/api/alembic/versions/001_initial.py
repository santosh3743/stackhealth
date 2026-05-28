"""initial schema — repos, scans, scan_findings, formula_versions, rate_limits

Revision ID: 001
Revises:
Create Date: 2026-05-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # enums (explicit create + pass create_type=False below to avoid the
    # double-create that SQLAlchemy's column DDL would otherwise emit).
    scan_status = postgresql.ENUM(
        "queued", "cloning", "analyzing", "scoring", "complete", "failed",
        name="scan_status",
        create_type=False,
    )
    letter_grade = postgresql.ENUM(
        "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F",
        name="letter_grade",
        create_type=False,
    )
    finding_severity = postgresql.ENUM(
        "critical", "high", "medium", "low", "info",
        name="finding_severity",
        create_type=False,
    )
    finding_engine = postgresql.ENUM(
        "semgrep", "trivy", "scorecard", "lint", "complexity", "duplication", "hygiene",
        name="finding_engine",
        create_type=False,
    )
    bind = op.get_bind()
    for t in (scan_status, letter_grade, finding_severity, finding_engine):
        # Use raw SQL with IF NOT EXISTS via DO block for true idempotence.
        labels = ", ".join(f"'{v}'" for v in t.enums)
        bind.exec_driver_sql(
            f"""
            DO $$ BEGIN
                CREATE TYPE {t.name} AS ENUM ({labels});
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
            """
        )

    # repos
    op.create_table(
        "repos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("default_branch", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("homepage", sa.Text),
        sa.Column("language", sa.Text),
        sa.Column("stars", sa.Integer),
        sa.Column("forks", sa.Integer),
        sa.Column("license_spdx", sa.Text),
        sa.Column("is_archived", sa.Boolean, server_default=sa.text("false")),
        sa.Column("is_fork", sa.Boolean, server_default=sa.text("false")),
        sa.Column("pushed_at", sa.DateTime(timezone=True)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("owner", "name", name="uq_repos_owner_name"),
    )
    op.create_index("idx_repos_language", "repos", ["language"])
    op.create_index("idx_repos_stars", "repos", [sa.text("stars DESC")])

    # scans
    op.create_table(
        "scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("repos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", scan_status, nullable=False, server_default="queued"),
        sa.Column("formula_version", sa.Text, nullable=False),
        sa.Column("commit_sha", sa.Text),
        sa.Column("overall_score", sa.Integer),
        sa.Column("grade", letter_grade),
        sa.Column("security_score", sa.Integer),
        sa.Column("quality_score", sa.Integer),
        sa.Column("hygiene_score", sa.Integer),
        sa.Column("community_score", sa.Integer),
        sa.Column("score_breakdown", postgresql.JSONB),
        sa.Column("partial", sa.Boolean, server_default=sa.text("false")),
        sa.Column("failure_reason", sa.Text),
        sa.Column("artifacts_url", sa.Text),
        sa.Column("tool_versions", postgresql.JSONB),
        sa.Column("requested_by_ip", postgresql.INET),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "idx_scans_repo_complete", "scans",
        ["repo_id", sa.text("completed_at DESC")],
        postgresql_where=sa.text("status = 'complete'"),
    )
    op.create_index(
        "idx_scans_status", "scans", ["status"],
        postgresql_where=sa.text("status != 'complete'"),
    )
    op.create_index("idx_scans_created", "scans", [sa.text("created_at DESC")])

    # scan_findings
    op.create_table(
        "scan_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engine", finding_engine, nullable=False),
        sa.Column("severity", finding_severity, nullable=False),
        sa.Column("rule_id", sa.Text),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("file_path", sa.Text),
        sa.Column("line_number", sa.Integer),
        sa.Column("code_snippet", sa.Text),
        sa.Column("raw_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_findings_scan", "scan_findings", ["scan_id"])
    op.create_index("idx_findings_severity", "scan_findings", ["scan_id", "severity"])

    # formula_versions
    op.create_table(
        "formula_versions",
        sa.Column("version", sa.Text, primary_key=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("spec_url", sa.Text, nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("false")),
    )
    op.execute(
        "INSERT INTO formula_versions (version, published_at, spec_url, summary, is_active) "
        "VALUES ('v1.0', NOW(), "
        "'https://github.com/stackhealth-dev/formula/tree/v1.0', "
        "'Initial formula. Security 30, Quality 25, Hygiene 25, Community 20.', "
        "true)"
    )

    # rate_limits
    op.create_table(
        "rate_limits",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("window_start", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("rate_limits")
    op.drop_table("formula_versions")
    op.drop_index("idx_findings_severity", table_name="scan_findings")
    op.drop_index("idx_findings_scan", table_name="scan_findings")
    op.drop_table("scan_findings")
    op.drop_index("idx_scans_created", table_name="scans")
    op.drop_index("idx_scans_status", table_name="scans")
    op.drop_index("idx_scans_repo_complete", table_name="scans")
    op.drop_table("scans")
    op.drop_index("idx_repos_stars", table_name="repos")
    op.drop_index("idx_repos_language", table_name="repos")
    op.drop_table("repos")
    for enum_name in ("finding_engine", "finding_severity", "letter_grade", "scan_status"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
