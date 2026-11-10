"""User-facing validation boundary; strict schema lives with the scenario object."""
from app.scenarios import Scenario


def errors(scenario):
    try:
        scenario.to_case()
        return []
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        return [str(exc)]
