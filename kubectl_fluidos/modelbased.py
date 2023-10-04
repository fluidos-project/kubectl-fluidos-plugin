from __future__ import annotations

from dataclasses import dataclass
from logging import Logger


logger = Logger(__name__)


@dataclass
class ModelBasedOrchestratorConfiguration:
    pass

    @staticmethod
    def build_configuration(args: list[str]) -> ModelBasedOrchestratorConfiguration:
        pass


class ModelBasedOrchestratorProcessor:
    def __init__(self, configuration: ModelBasedOrchestratorConfiguration = ModelBasedOrchestratorConfiguration()):
        self.configuration = configuration

    def __call__(self, data) -> int:
        raise NotImplementedError()
