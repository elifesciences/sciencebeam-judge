from unittest.mock import MagicMock

from sciencebeam_judge.evaluation.custom.registry import (
    create_custom_evaluation
)


class TestCreateCustomEvaluation:
    def test_should_call_custom_evaluation_factory(self):
        custom_evaluation_factory = MagicMock(name='custom_evaluation_factory')
        create_custom_evaluation(custom_evaluation_factory)
        custom_evaluation_factory.assert_called_with()

    def test_should_pass_in_config_to_evaluation_factory(self):
        config = {'scoring_type': 'test'}
        custom_evaluation_factory = MagicMock(name='custom_evaluation_factory')
        create_custom_evaluation(custom_evaluation_factory, config)
        custom_evaluation_factory.assert_called_with(config=config)
