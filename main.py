from src.model.runbook import Runbook, Step
import uuid
from faker import Faker
from src.storage.vector import VectorDB

fake = Faker()

db = VectorDB()

# Generate 10 fake runbooks
def generate_fake_runbooks(n=10):
    for _ in range(n):
        done_step = Step(sid=uuid.uuid4(), description=fake.sentence(), allowed_cmds=[])
        fake_step = Step(sid=uuid.uuid4(), description=fake.sentence(), allowed_cmds=["echo \"Hello World!\""], alt_condition=("Hello world fails", done_step.sid))

        runbook = Runbook(
            rid=uuid.uuid4(), description=fake.sentence(), steps=[fake_step]
        )
        print(runbook.description)
        db.add_runbook(runbook)


generate_fake_runbooks()


