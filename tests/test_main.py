from main import detect, fixtures


def test_ten_seeded_drifts_detected_against_actual_app():
    clean, spec, traffic, bad = fixtures()
    assert len(detect(bad, spec, traffic)) == 10
    assert detect(clean, spec, traffic) == []


def test_proposed_documentation_is_a_clean_repair():
    clean, spec, traffic, _ = fixtures()
    assert all(row["response_status"] == 200 for row in clean)
    assert len({r["url"] for r in traffic}) == 10
