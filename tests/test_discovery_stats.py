"""The discovery figures can be regenerated, and the headline numbers stay what the data says."""
from scripts import discovery_stats


def test_discovery_stats_regenerates_the_tables(tmp_path):
    output = tmp_path / "ticket_stats.md"
    assert discovery_stats.main(output) == 0
    report = output.read_text(encoding="utf-8")
    assert "| Total tickets in sample | 500 " in report
    assert "| Historical first contact resolution | 43.8% |" in report
    assert "| Proportion answerable from existing docs | 71.4% |" in report
    for heading in ["## 3. Where the time goes", "## 5. Checks for claims", "## 7. What the labels allow"]:
        assert heading in report


def test_mann_whitney_detects_a_clear_difference():
    assert discovery_stats.mann_whitney_p([1, 2, 3, 4, 5] * 4, [6, 7, 8, 9, 10] * 4) < 0.001
    assert discovery_stats.mann_whitney_p([1, 2, 3] * 5, [1, 2, 3] * 5) > 0.9
