import pytest

from anicli_api import RandomAgent


@pytest.mark.parametrize(
    "agent1,agent2",
    [
        (RandomAgent.mobile(), RandomAgent.mobile()),
        (RandomAgent.desktop(), RandomAgent.desktop()),
        (RandomAgent.random(), RandomAgent.random()),
        (RandomAgent.desktop(), RandomAgent.mobile()),
        (RandomAgent.random(), RandomAgent.mobile()),
        (RandomAgent.random(), RandomAgent.desktop()),
    ],
)
def test_fake_agent(agent1: str, agent2: str):
    assert agent1 != agent2
