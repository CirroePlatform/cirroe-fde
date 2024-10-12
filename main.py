from src.model.runbook import Runbook, Step
from datetime import datetime, timedelta
import uuid
from faker import Faker
from src.storage.vector import VectorDB

from src.core.executor import RunBookExecutor
from src.core.metrics import SpikeDetector

from src.model.issue import OpenIssueRequest, Issue

from src.server.handle_actions import handle_new_issue

fake = Faker()

db = VectorDB()
rbe = RunBookExecutor()

sd = SpikeDetector()

rbs = []

descs = [
    "print out 'hell world' successfully",
    "print out 'Hello World!' successfully",
    "print out 'go kys' successfully",
]

cmds = ['echo "hell world"', 'echo "Hello World!"', 'echo "go kys"']


# Generate fake runbooks
def generate_fake_runbooks():
    for desc in descs:
        done_step = Step(sid=uuid.uuid4(), description=fake.sentence(), allowed_cmds=[])
        fake_step = Step(
            sid=uuid.uuid4(), description=desc, allowed_cmds=cmds, next=done_step.sid
        )
        runbook = Runbook(
            rid=uuid.uuid4(),
            description="a runbook to help someone" + desc,
            steps=[fake_step],
        )
        print(runbook.description)
        db.add_runbook(runbook)
        rbs.append(runbook)

    # for rb in rbs:
    #     rbe.run_book(rb)

# generate_fake_runbooks()

# end_time = datetime.utcnow()
# start_time = end_time - timedelta(hours=24)  # Last 24 hours
# Generate and print the report
# sd.generate_report(start_time, end_time, threshold=2.5, sort_key="DBInstanceIdentifier", sort_val="hatch-prod")

handle_new_issue(OpenIssueRequest(requestor="james", issue=Issue(tid=uuid.uuid4(), problem_description="Hello, I am trying to print out go kys, but every time I run the command \"ech go kys\" it just does not print what I want. Can you help?", comments=[])))
