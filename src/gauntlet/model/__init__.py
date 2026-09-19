"""Kronos lineage, inference, and adaptation contracts."""

from .inference import INFERENCE_SCHEMA, ContextObservation, FrozenContext, InferenceArtifact, ModelError, ModelProfile, run_inference
from .registry import MODEL_SCHEMA, ModelRegistration, ModelRegistryEntry, register_model

MODEL_REGISTRY_SCHEMA = MODEL_SCHEMA
MODEL_INFERENCE_SCHEMA = INFERENCE_SCHEMA
MODEL_REGISTRATION_EVENT = "model-registration"
MODEL_INFERENCE_EVENT = "model-inference"
MODEL_OUTPUT_BASIS = "MODELED"
MODEL_REPLAY_READY = "READY"
MODEL_REPLAY_BLOCKED = "BLOCKED"
MODEL_CALIBRATION_STATUS = "PENDING"
__all__ = ["ContextObservation", "FrozenContext", "InferenceArtifact", "ModelError", "ModelProfile", "ModelRegistration", "ModelRegistryEntry", "register_model", "run_inference"]
