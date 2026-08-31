from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_required_repository_files_exist():
    required = [
        "README.md",
        "ROADMAP.md",
        "LICENSE",
        "CITATION.cff",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        ".github/workflows/ci.yml",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    assert not missing, f"Missing required repository files: {missing}"


def test_documentation_links_target_existing_local_files():
    expected = [
        "docs/architecture_overview.md",
        "docs/decisions/ADR-001-portfolio-platform.md",
        "docs/decisions/ADR-002-duckdb-warehouse.md",
        "docs/source_to_staging_mapping.md",
        "docs/staging_failure_runbook.md",
        "docs/da1_evidence.md",
        "docs/dimensional_model.md",
        "docs/da2_evidence.md",
        "contracts/sources/customers.yml",
        "src/data_architecture/contracts.py",
        "src/data_architecture/synthetic_data.py",
        "src/data_architecture/staging.py",
        "src/data_architecture/warehouse.py",
        "warehouse/sql/00_staging_views.sql",
        "warehouse/sql/10_dimensions.sql",
        "warehouse/sql/20_facts.sql",
        "warehouse/quality_checks.yml",
        "tests",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert not missing, f"README-linked local paths do not exist: {missing}"
