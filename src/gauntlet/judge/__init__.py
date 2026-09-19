"""Local walk-forward evaluation contracts."""

from .splits import SplitError, SplitFold, SplitManifest, SplitPolicy, build_split_manifest
from .synthetic import BarRow, EventRow, FrozenPopulation, SyntheticPopulationError, build_synthetic_population
from .walk_forward import CandidateVariant, FactoryRankingEntry, Prediction, Trade, WalkForwardError, WalkForwardFold, WalkForwardRequest, WalkForwardRun, evaluate_walk_forward
from .prospective import ProspectiveDependency, ProspectiveDependencySnapshot, ProspectiveError, ProspectiveOutcome, ProspectiveRecord, ProspectiveSignal, ProspectiveVerification, append_signal, resolve_outcome, verify_prospective

SPLIT_SCHEMA = "gauntlet.walk-forward-split.v1"
SYNTHETIC_POPULATION_SCHEMA = "gauntlet.synthetic-population.v1"
WALK_FORWARD_RUN_SCHEMA = "gauntlet.walk-forward-run.v1"
JUDGE_MODULE_VERSION = "1"
JUDGE_ENTRY_POLICY = "next_bar"

__all__ = ["BarRow", "CandidateVariant", "EventRow", "FactoryRankingEntry", "FrozenPopulation", "Prediction", "ProspectiveDependency", "ProspectiveDependencySnapshot", "ProspectiveError", "ProspectiveOutcome", "ProspectiveRecord", "ProspectiveSignal", "ProspectiveVerification", "SplitError", "SplitFold", "SplitManifest", "SplitPolicy", "SyntheticPopulationError", "Trade", "WalkForwardError", "WalkForwardFold", "WalkForwardRequest", "WalkForwardRun", "append_signal", "build_split_manifest", "build_synthetic_population", "evaluate_walk_forward", "resolve_outcome", "verify_prospective"]
