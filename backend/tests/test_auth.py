import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import authenticate, create_access_token, hash_password, verify_password
from app.db import Base
from app.models import UserRole
from app.services.users import create_user, ensure_bootstrap_users, list_users, update_user


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_password_hash_is_salted_and_verifiable(self):
        first = hash_password("correct-password")
        second = hash_password("correct-password")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("correct-password", first))
        self.assertFalse(verify_password("wrong-password", first))

    def test_bootstrap_users_and_authentication(self):
        with Session(self.engine) as session:
            ensure_bootstrap_users(session)
            self.assertEqual({user.role for user in list_users(session)}, {UserRole.ADMIN, UserRole.RESEARCHER, UserRole.VIEWER})
            admin = authenticate(session, "admin", "admin12345")
            self.assertIsNotNone(admin)
            self.assertTrue(create_access_token(admin))
            self.assertIsNone(authenticate(session, "admin", "wrong-password"))

    def test_duplicate_username_is_rejected(self):
        with Session(self.engine) as session:
            create_user(session, username="member", display_name="成员", password="member-pass1", role=UserRole.VIEWER)
            with self.assertRaisesRegex(ValueError, "用户名已存在"):
                create_user(session, username="member", display_name="成员二", password="member-pass2", role=UserRole.RESEARCHER)

    def test_admin_can_disable_user_but_not_self(self):
        with Session(self.engine) as session:
            admin = create_user(session, username="adminx", display_name="管理员", password="admin-password", role=UserRole.ADMIN)
            member = create_user(session, username="memberx", display_name="成员", password="member-password", role=UserRole.RESEARCHER)
            disabled = update_user(session, member, actor_id=admin.id, is_active=False)
            self.assertFalse(disabled.is_active)
            self.assertIsNone(authenticate(session, "memberx", "member-password"))
            with self.assertRaisesRegex(ValueError, "不能停用自己"):
                update_user(session, admin, actor_id=admin.id, is_active=False)

    def test_last_active_admin_cannot_be_removed(self):
        with Session(self.engine) as session:
            admin = create_user(session, username="adminx", display_name="管理员", password="admin-password", role=UserRole.ADMIN)
            actor = create_user(session, username="adminy", display_name="管理员二", password="admin-password2", role=UserRole.ADMIN)
            update_user(session, admin, actor_id=actor.id, is_active=False)
            with self.assertRaisesRegex(ValueError, "至少一个"):
                update_user(session, actor, actor_id="external-admin", role=UserRole.VIEWER)


if __name__ == "__main__":
    unittest.main()
