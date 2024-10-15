from faker import Faker
from src.storage.vector import VectorDB

from src.core.executor import RunBookExecutor
from src.core.metrics import SpikeDetector

fake = Faker()

db = VectorDB()
rbe = RunBookExecutor()

sd = SpikeDetector()

# handle_new_issue(
#     OpenIssueRequest(
#         requestor="james",
#         issue=Issue(
#             tid=uuid.uuid4(),
#             problem_description="We noticed that there were some spikes in cpu utilization in some instances we are using. We cannot identify which one, and we also are having troble stopping it. Can you help here?",
#             comments=[],
#         ),
#     )
# )
