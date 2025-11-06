import logging
from typing import Any, override

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

from sregym.conductor.oracles.localization_oracle import LocalizationOracle

local_logger = logging.getLogger("all.sregym.otel_localization_oracle")
local_logger.propagate = True
local_logger.setLevel(logging.DEBUG)


class OtelLocalizationOracle(LocalizationOracle):

    def __init__(self, problem, namespace: str, expected_deployment_name: str):
        super().__init__(problem, namespace, expected_deployment_name)
        self.expected_deployment_name = expected_deployment_name

    @override
    def expect(self):
        uid, name = self.only_pod_of_deployment_uid(self.expected_deployment_name, self.namespace)
        return [uid]  # Return only the UID as expected

    @override
    def compare_truth(self, expectation, reality):
        if type(expectation) == str and type(reality) == str:
            return expectation == reality  # both string, just compare the string
        elif type(expectation) == list and type(reality) == list:
            return all(e in reality for e in expectation)
        else:
            local_logger.warning(
                f"Expectation and reality are not both string or list, can not compare. Expectation: {expectation}, Reality: {reality}"
            )
            return False
