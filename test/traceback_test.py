from src.integrations.cleaners.traceback_cleaner import TracebackCleaner, TracebackStep
from src.storage.vector import VectorDB
from pydantic import BaseModel
from typing import List

from include.constants import MEM0AI_ORG_ID

vector_db = VectorDB(user_id=MEM0AI_ORG_ID)
cleaner = TracebackCleaner(vector_db)


class CleanTracebackCase(BaseModel):
    traceback: str
    expected_steps: List[TracebackStep]


def test_clean_traceback():
    cases = [
        CleanTracebackCase(
            traceback="""
                Welcome to your personal Travel Agent Planner! How can I assist you with your travel plans today?
                You: milan
                Traceback (most recent call last):
                File "c:\...\memo_base.py", line 129, in <module>
                    response = chat_turn(user_input, user_id)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                File "c:\...\memo_base.py", line 110, in chat_turn
                    context = retrieve_context(user_input, user_id)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                File "c:\...\memo_base.py", line 49, in retrieve_context
                    seralized_memories = ' '.join([mem["memory"] for mem in memories])
                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                File "c:\...\memo_base.py", line 49, in <listcomp>
                    seralized_memories = ' '.join([mem["memory"] for mem in memories])
                                                ~~~^^^^^^^^^^
                TypeError: string indices must be integers, not 'str'```
            """,
            expected_steps=[
                TracebackStep(
                    file="memo_base.py",
                    code="response = chat_turn(user_input, user_id)",
                ),
                TracebackStep(
                    file="memo_base.py",
                    code="context = retrieve_context(user_input, user_id)",
                ),
                TracebackStep(
                    file="memo_base.py",
                    code="seralized_memories = ' '.join([mem['memory'] for mem in memories])",
                ),
            ],
        )
    ]

    for case in cases:
        steps = cleaner.clean(case.traceback)

        assert len(steps) == len(case.expected_steps)
        for i in range(len(steps)):
            assert steps[i].file == case.expected_steps[i].file
            assert steps[i].code == case.expected_steps[i].code
