from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Metadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    owner: str | None = None
    description: str | None = None


class Component(BaseModel):
    model_config = ConfigDict(extra="allow")

    kind: str

    @property
    def extra_fields(self) -> dict[str, Any]:
        return self.model_extra or {}


class Evaluation(BaseModel):
    model_config = ConfigDict(extra="allow")

    graders: dict[str, Any] = Field(default_factory=dict)
    suites: dict[str, Any] = Field(default_factory=dict)


class BehaviorKeys(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)


class Environment(BaseModel):
    model_config = ConfigDict(extra="allow")

    runtime: str | None = None
    sdk_versions: dict[str, str] = Field(default_factory=dict)
    lock_strategy: str | None = None


class IntelligenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: Literal["aigit.dev/v1"] = Field(alias="apiVersion")
    kind: Literal["IntelligenceSystem"]
    metadata: Metadata
    components: dict[str, Component]
    evaluation: Evaluation = Field(default_factory=Evaluation)
    behavior_keys: BehaviorKeys = Field(default_factory=BehaviorKeys)
    environment: Environment = Field(default_factory=Environment)

    @model_validator(mode="after")
    def require_components(self) -> "IntelligenceManifest":
        if not self.components:
            raise ValueError("components must be a non-empty mapping")
        return self


def json_schema() -> dict[str, Any]:
    return IntelligenceManifest.model_json_schema()
