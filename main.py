from src.model.runbook import Runbook, Step
import uuid
from faker import Faker
from src.storage.vector import VectorDB

from src.core.executor import RunBookExecutor


fake = Faker()

db = VectorDB()
rbe = RunBookExecutor()

rbs = []

descs = [
    "print out 'hell world' successfully",
    "print out 'Hello World!' successfully",
    "print out 'go kys' successfully"
]

cmds = [
    "echo \"hell world\"",
    "echo \"Hello World!\"",
    "echo \"go kys\""
]

# Generate fake runbooks
def generate_fake_runbooks():
    for desc in descs:
        done_step = Step(sid=uuid.uuid4(), description=fake.sentence(), allowed_cmds=[])
        fake_step = Step(sid=uuid.uuid4(), description=desc, allowed_cmds=cmds, next=done_step.sid)
        runbook = Runbook(
            rid=uuid.uuid4(), description="a runbook to help someone" + desc, steps=[fake_step]
        )
        print(runbook.description)
        # db.add_runbook(runbook)
        rbs.append(runbook)

    for rb in rbs:
        rbe.run_book(rb)

generate_fake_runbooks()
