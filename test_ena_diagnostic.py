
from ena_diagnostic import build_default_diagnostic, PhaseStatus


def test_default_totals():
    diag = build_default_diagnostic()
    assert diag.total_phases == 21
    assert diag.autonomy_percent == 89


def test_layers_present():
    diag = build_default_diagnostic()
    layers = {p.layer for p in diag.phases}
    assert layers == {1, 2, 3}


def test_phase_15_refusal_active():
    diag = build_default_diagnostic()
    phase_15 = next(p for p in diag.phases if p.id == 15)
    assert phase_15.status == PhaseStatus.ACTIVE
    assert "Refusal" in phase_15.name
