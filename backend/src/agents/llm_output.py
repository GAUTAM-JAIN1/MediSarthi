from typing import Optional


def first_pydantic_dict(result) -> Optional[dict]:
    """
    Returns pyd.dict() for the first task output of a CrewAI result that
    carries a Pydantic model, or None if none does.

    Replaces the loop previously copy-pasted in route handlers:
        for task_output in getattr(result, "tasks_output", []):
            pyd = getattr(task_output, "pydantic", None)
            if pyd is not None:
                x = pyd.dict()
                break
    Callers keep their own fallback logic.
    """
    for task_output in getattr(result, "tasks_output", []):
        pyd = getattr(task_output, "pydantic", None)
        if pyd is not None:
            return pyd.dict()
    return None

