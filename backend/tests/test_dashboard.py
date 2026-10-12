import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import UserRole
from app.services.dashboard import build_dashboard
from app.services.runs import create_research_run
from app.services.users import create_user


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_researcher_scope_only_contains_own_runs(self):
        with Session(self.engine, expire_on_commit=False) as session:
            first = create_user(session, username="first", display_name="甲", password="password-123", role=UserRole.RESEARCHER)
            second = create_user(session, username="second", display_name="乙", password="password-456", role=UserRole.RESEARCHER)
            create_research_run(session, {"factor": "momentum_20d", "groups": 5}, created_by_id=first.id)
            create_research_run(session, {"factor": "momentum_20d", "groups": 5}, created_by_id=second.id)
            result = build_dashboard(session, first)
            self.assertEqual(result["scope"], "personal")
            self.assertEqual(result["tasks"]["total"], 1)
            self.assertEqual(result["tasks"]["by_status"]["pending"], 1)
            self.assertEqual(result["factors"]["builtin"], 6)

    def test_viewer_scope_is_global(self):
        with Session(self.engine, expire_on_commit=False) as session:
            viewer = create_user(session, username="viewer2", display_name="访客", password="password-789", role=UserRole.VIEWER)
            create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            result = build_dashboard(session, viewer)
            self.assertEqual(result["scope"], "global")
            self.assertEqual(result["tasks"]["total"], 1)
            self.assertIsNone(result["tasks"]["success_rate"])


if __name__ == "__main__":
    unittest.main()
