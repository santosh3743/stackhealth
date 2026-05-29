"""Tests for the email templates — pure string rendering, no network."""

import pytest

from stackhealth import notify_templates


def _render_args(**overrides):
    base = dict(
        owner="pallets",
        name="click",
        overall=82,
        grade="B+",
        partial=False,
        scores={"security": 84, "quality": 79, "hygiene": 96, "community": 75},
        language="Python",
        stars=17_500,
        report_link="https://stackhealth.dev/r/pallets/click/abc",
        methodology_link="https://stackhealth.dev/methodology",
    )
    base.update(overrides)
    return base


# ─────────────────────────── subject ───────────────────────────


def test_subject_signal_first() -> None:
    """Grade + score must appear early so Gmail's truncation keeps it."""
    subj = notify_templates.scan_complete_subject(
        owner="pallets", name="click", grade="B+", overall=82
    )
    assert subj.startswith("pallets/click scored B+ (82/100)")


# ─────────────────────────── plain text ───────────────────────────


def test_text_includes_meta_and_subscores() -> None:
    text = notify_templates.scan_complete_text(**_render_args())
    assert "pallets/click" in text
    assert "B+" in text and "82/100" in text
    assert "Python" in text and "17,500 ★" in text
    assert "Security:   84" in text
    assert "Quality:    79" in text
    assert "Hygiene:    96" in text
    assert "Community:  75" in text
    assert "https://stackhealth.dev/r/pallets/click/abc" in text
    assert "stackhealth.dev/methodology" in text


def test_text_partial_label() -> None:
    text = notify_templates.scan_complete_text(**_render_args(partial=True))
    assert "partial" in text


def test_text_works_without_optional_fields() -> None:
    text = notify_templates.scan_complete_text(
        **_render_args(scores=None, language=None, stars=None)
    )
    assert "B+" in text
    # No KeyError, no formatting errors, no leftover {placeholders}.
    assert "{" not in text or "{" in text.split("Grade")[0]  # only allow in template artifact


# ─────────────────────────── HTML ───────────────────────────


def test_html_contains_repo_grade_and_report_link() -> None:
    html = notify_templates.scan_complete_html(**_render_args())
    assert "<title>pallets/click — B+</title>" in html
    assert "82" in html  # score in hero (whitespace-tolerant)
    assert "B+" in html
    assert 'href="https://stackhealth.dev/r/pallets/click/abc"' in html
    assert 'href="https://stackhealth.dev/methodology"' in html


def test_html_grade_color_matches_grade() -> None:
    """Letter-grade colour must match what GradeBadge uses in the web app."""
    html_b = notify_templates.scan_complete_html(**_render_args(grade="B"))
    html_a = notify_templates.scan_complete_html(**_render_args(grade="A+"))
    assert "#84cc16" in html_b  # B colour
    assert "#10b981" in html_a  # A+ colour


def test_html_partial_banner_shown_only_when_partial() -> None:
    html_clean = notify_templates.scan_complete_html(**_render_args(partial=False))
    html_partial = notify_templates.scan_complete_html(**_render_args(partial=True))
    assert "Partial scan" not in html_clean
    assert "Partial scan" in html_partial


def test_html_subscores_grid_renders_with_weights() -> None:
    html = notify_templates.scan_complete_html(**_render_args())
    # Each weight label appears in the grid.
    for w in ("weight 30%", "weight 25%", "weight 20%"):
        assert w in html


def test_html_no_template_brace_leaks() -> None:
    """Catch a class of bugs where an f-string `{var}` ends up rendered literally."""
    html = notify_templates.scan_complete_html(**_render_args())
    # The only legitimate `{` in the rendered HTML is in CSS @media. We have
    # none. Anything else is a leaked template.
    assert "{owner}" not in html and "{name}" not in html and "{grade}" not in html
    assert "{report_link}" not in html


@pytest.mark.parametrize(
    ("score", "label"),
    [
        (95, "Excellent"),
        (80, "Good"),
        (65, "Fair"),
        (45, "Weak"),
        (20, "Poor"),
    ],
)
def test_qualitative_label_bands(score: int, label: str) -> None:
    assert notify_templates.qualitative_label(score) == label
