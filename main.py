from src.model.runbook import Runbook
import uuid
from faker import Faker
from src.storage.vector import VectorDB

fake = Faker()

db = VectorDB()

# Generate 10 fake runbooks
def generate_fake_runbooks(n=10):
    for _ in range(n):
        runbook = Runbook(
            rid=uuid.uuid4(),
            description=fake.sentence(),
            first_step_id=uuid.uuid4()
        )
        print(runbook.description)    
        db.add_runbook(runbook)

generate_fake_runbooks()