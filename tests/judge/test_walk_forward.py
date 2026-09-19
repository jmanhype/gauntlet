from __future__ import annotations

import ast, json, pytest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType

from gauntlet.config.resolver import ArtifactVersions, ResolvedConfig, resolve_config
from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.data.descriptors import descriptor_mapping, register_descriptor
from gauntlet.judge import CandidateVariant, FactoryRankingEntry, SplitError, SplitPolicy, WalkForwardError, WalkForwardRequest, build_split_manifest, build_synthetic_population, evaluate_walk_forward
from gauntlet.judge.synthetic import _content, _descriptor
from gauntlet.ledger import Actor, verify_chains


OWNER = Actor("human", "walk-forward-owner"); POLICY = SplitPolicy(datetime(2026, 1, 1, tzinfo=timezone.utc), 60, 10, 5, 5, 2, 2, 3, 2, 1, 1, True)
PROVENANCE = {"normalization": {"window_bars": 3, "uses_future": False, "available_at": "prediction_time"}, "source": "synthetic.bars"}


def config(tmp_path: Path) -> ResolvedConfig:
    profile = tmp_path / "profile.toml"; profile.write_text('schema_version = "1"\nprofile_id = "walk-forward"\nprofile_version = 1\n[values]\nvenue_track = "solana_dex"\ndata_start = "2026-01-01"\ndata_end = "2026-01-03"\nseed = 7\nlookback = 2\nhorizon = 2\nthreshold = 0.5\nfee_bps = 10\n', encoding="utf-8")
    return resolve_config(profile, {}, ArtifactVersions(*(["1"] * 6), sha256_digest(b"schemas"), sha256_digest(b"environment")))


def candidates() -> tuple[CandidateVariant, CandidateVariant]:
    return (CandidateVariant("", PROVENANCE, {"lookback": 2, "momentum_weight": 0.0, "volume_weight": 0.0, "threshold": -1.0}), CandidateVariant("", PROVENANCE, {"lookback": 2, "momentum_weight": 0.0, "volume_weight": 0.0, "threshold": 2.0}))


def request(population, resolved, split=None, variant=None) -> WalkForwardRequest:
    buy, _ = candidates(); return WalkForwardRequest(population, resolved, (variant or buy,), OWNER, PROVENANCE, (), split)


@pytest.fixture
def scene(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "gauntlet-data"; monkeypatch.setenv("GAUNTLET_DATA_ROOT", str(root)); population = build_synthetic_population(7, POLICY); return root, population, build_split_manifest(POLICY, population), config(tmp_path)


def test_synthetic_population_is_deterministic_registered_and_local(scene) -> None:
    root, population, _, _ = scene
    repeated, different = build_synthetic_population(7, POLICY), build_synthetic_population(8, POLICY); assert repeated.mapping() == population.mapping() and repeated.population_hash == population.population_hash and different.population_hash != population.population_hash
    assert population.mapping()["promotable_venue_evidence"] is False and population.mapping()["evidence_class"] == "SYNTHETIC_FIXTURE" and [row.row_id for row in population.bars] == sorted(row.row_id for row in population.bars)
    assert all(row.venue == "solana_dex" and row.token for row in population.bars) and population.events
    bars, events = json.loads(Path(str(population.bars_content_path)).read_bytes()), json.loads(Path(str(population.events_content_path)).read_bytes())
    assert bars["rows"] == [row.mapping() for row in population.bars] and events["rows"] == [row.mapping() for row in population.events]
    assert (root / "ledger" / "trials.jsonl").read_bytes().count(b"\n") == 4 and verify_chains(root).valid
    for module in ((Path(__file__).parents[2] / "src" / "gauntlet" / "judge" / name) for name in ("synthetic.py", "walk_forward.py")):
        tree = ast.parse(module.read_text(encoding="utf-8")); assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) and any(alias.name.split(".")[0] in {"socket", "http", "urllib", "requests"} for alias in node.names) for node in ast.walk(tree)); assert "bitquery" not in module.read_text(encoding="utf-8").casefold()


def test_split_manifest_records_strict_boundaries_labels_and_locks(scene) -> None:
    _, population, manifest, _ = scene
    value = manifest.mapping()
    assert value["fold_order"] == [1, 2] and len(value["folds"]) == 2 and value["policy"]["horizon_bars"] == value["policy"]["target_horizon_bars"] == POLICY.target_horizon_bars
    assert value["policy"]["lookback_bars"] == POLICY.lookback_bars and value["policy"]["normalization_window_bars"] == POLICY.normalization_window_bars and value["policy"]["embargo_bars"] == POLICY.embargo_bars and value["policy"]["purge_bars"] == POLICY.purge_bars
    rows = {row.row_id: row for row in population.bars}
    prior_tests: set[str] = set()
    for fold in manifest.folds:
        assert fold.selection_lock == {"fold_id": fold.fold_id, "state": "PENDING", "candidate_fingerprint": None, "locked_at_boundary": fold.validation_end_utc, "selection_input": "validation_only"}
        train_end = datetime.fromisoformat(fold.train_end_utc.replace("Z", "+00:00")); validation_start = datetime.fromisoformat(fold.validation_start_utc.replace("Z", "+00:00")); validation_end = datetime.fromisoformat(fold.validation_end_utc.replace("Z", "+00:00")); test_start = datetime.fromisoformat(fold.test_start_utc.replace("Z", "+00:00"))
        assert train_end < validation_start < validation_end < test_start
        assert not set(fold.train_membership) & set(fold.validation_membership) and not set(fold.train_membership) & set(fold.test_membership) and not set(fold.validation_membership) & set(fold.test_membership)
        assert not prior_tests & set(fold.test_membership); prior_tests.update(fold.test_membership)
        for membership, boundary in ((fold.train_membership, fold.train_end_utc), (fold.validation_membership, fold.validation_end_utc), (fold.test_membership, fold.test_end_utc)):
            assert all(datetime.fromisoformat(rows[row_id].target_completed_at_utc.replace("Z", "+00:00")) < datetime.fromisoformat(boundary.replace("Z", "+00:00")) for row_id in membership)
    bad = replace(population, bars=(*population.bars[:-1], replace(population.bars[-1], close=population.bars[-1].close + 1)))
    with pytest.raises(SplitError) as rejection:
        build_split_manifest(POLICY, bad)
    assert rejection.value.code == "POPULATION_MUTATED"


def test_real_multi_fold_evaluation_selects_on_validation_and_replays_rows(scene) -> None:
    root, population, split, resolved = scene
    buy, flat = candidates(); ranking = (FactoryRankingEntry(flat.fingerprint, 999.0), FactoryRankingEntry(buy.fingerprint, -999.0))
    arguments = (population, resolved, (buy, flat), OWNER, PROVENANCE, ranking, split)
    result = evaluate_walk_forward(WalkForwardRequest(*arguments))
    assert result.status == "OK" and result.run_report["dependency_evaluation"]["status"] == "OK" and result.run_report["selected_fingerprints"] == [buy.fingerprint, buy.fingerprint] and result.run_report["factory_ranking"] == {"admissible": False, "ranking_score_is_judge_evidence": False, "entry_condition": "selected_fingerprint_locked"}
    assert result.run_report["config_hash"] == resolved.config_hash and result.run_report["population_hash"] == population.population_hash and set(result.run_report["source_descriptor_hashes"]) == {population.bars_descriptor["descriptor_hash"], population.events_descriptor["descriptor_hash"]}
    assert len(result.predictions) == 10 and len(result.trades) == 10
    for prediction in result.predictions:
        assert prediction.venue == "solana_dex" and prediction.token and prediction.intended_action in {"BUY", "FLAT"} and prediction.prediction_basis == prediction.label_basis == "MODELED" and prediction.selected_fingerprint == buy.fingerprint
        assert (datetime.fromisoformat(prediction.entry_timestamp_utc.replace("Z", "+00:00")) - datetime.fromisoformat(prediction.timestamp_utc.replace("Z", "+00:00"))).total_seconds() == POLICY.bar_interval_seconds
    for trade in result.trades:
        assert trade.label_completed_at_utc and trade.execution_basis == trade.outcome_basis == "MODELED" and trade.selection_lock_hash and datetime.fromisoformat(trade.entry_timestamp_utc.replace("Z", "+00:00")) < datetime.fromisoformat(trade.exit_timestamp_utc.replace("Z", "+00:00"))
    for fold in result.folds:
        assert fold.selection_lock["test_membership_digest_before_selection"] == sha256_digest(canonical_json(list(fold.test_membership)))
    for name in ("fold_manifest.json", "predictions.json", "trades.json", "run_report.json"): assert result.artifact_paths[name].is_file() and not (result.artifact_paths[name].stat().st_mode & 0o222)
    assert json.loads(result.artifact_paths["run_report.json"].read_bytes())["evaluation_hash"] == result.run_report["evaluation_hash"] and (root / "ledger" / "events.jsonl").read_bytes().count(b"\n") == 1 and verify_chains(root).valid
    replay = evaluate_walk_forward(WalkForwardRequest(*arguments)); assert replay.run_hash == result.run_hash and replay.replayed and (root / "ledger" / "events.jsonl").read_bytes().count(b"\n") == 1


def test_fail_closed_rejections_and_missing_dependency_blocks(scene) -> None:
    root, population, split, resolved = scene; future = CandidateVariant("", {"normalization": {"uses_future": True}}, {"lookback": 2})
    with pytest.raises(WalkForwardError) as future_rejection:
        evaluate_walk_forward(request(population, resolved, split, future))
    assert future_rejection.value.code == "FUTURE_NORMALIZATION_REJECTED"
    with pytest.raises(WalkForwardError) as unknown_rejection:
        evaluate_walk_forward(request(population, resolved, split, CandidateVariant("", PROVENANCE, {"lookback": 2, "surprise": 1})))
    assert unknown_rejection.value.code == "PARAMETER_UNKNOWN"
    mutated = replace(population, bars=(*population.bars[:-1], replace(population.bars[-1], close=population.bars[-1].close + 1)))
    with pytest.raises(WalkForwardError) as mutation_rejection:
        evaluate_walk_forward(request(mutated, resolved, split))
    assert mutation_rejection.value.code == "POPULATION_MUTATED"
    ghost = dict(population.events_descriptor) | {"descriptor_hash": sha256_digest(b"missing-event-descriptor")}; missing = replace(population, events_descriptor=MappingProxyType(ghost))
    object.__setattr__(missing, "population_hash", missing.digest())
    blocked = evaluate_walk_forward(request(missing, resolved, build_split_manifest(POLICY, missing)))
    assert blocked.status == "BLOCKED" and blocked.run_report["blocked_reason"] == "BLOCKED" and blocked.predictions == () and blocked.trades == () and blocked.run_report["execution"]["imputed_fill"] is False
    assert any(finding["code"] == "DEPENDENCY_MISSING" for finding in blocked.run_report["dependency_evaluation"]["findings"]) and verify_chains(root).valid


def test_absent_target_timestamp_with_flat_variant_blocks_without_label(scene) -> None:
    root, population, _, resolved = scene; _, flat = candidates(); absent = "2026-01-01T00:23:30Z"; index = 23
    bad_row = replace(population.bars[index], target_completed_at_utc=absent); bad_rows = (*population.bars[:index], bad_row, *population.bars[index + 1:])
    content = _content("bars", 901, POLICY, [row.mapping() for row in bad_rows]); descriptor = _descriptor("bars", 901, POLICY, content, ()); registration = register_descriptor(descriptor)
    malformed = replace(population, seed=901, bars=bad_rows, bars_descriptor=MappingProxyType(descriptor_mapping(descriptor)), bars_content_path=registration.content_path, bars_content_hash=sha256_digest(content), population_hash=""); object.__setattr__(malformed, "population_hash", malformed.digest())
    with pytest.raises(SplitError) as rejection: build_split_manifest(POLICY, malformed)
    assert rejection.value.code == "TARGET_BAR_MISSING" and rejection.value.path == "$.bars.bar-000023"
    blocked = evaluate_walk_forward(WalkForwardRequest(malformed, resolved, (flat,), OWNER, PROVENANCE))
    assert blocked.status == "BLOCKED" and blocked.run_report["blocked_reason"] == "TARGET_BAR_MISSING" and blocked.predictions == () and blocked.trades == () and json.loads(blocked.artifact_paths["predictions.json"].read_bytes()) == [] and absent not in blocked.artifact_paths["predictions.json"].read_text()
    assert blocked.run_report["dependency_evaluation"]["status"] == "OK" and blocked.run_report["execution"]["imputed_fill"] is False and verify_chains(root).valid
