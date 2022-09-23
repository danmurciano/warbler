"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        u1 = User.signup("testuser1", "test1@test.com", "password", "")
        u2 = User.signup("testuser2", "test2@test.com", "password", "")
        u1.id = 101
        u2.id = 102

        msg1 = Message(text="This is a test message", user_id=101)
        msg2 = Message(text="This too is a test message", user_id=101)
        msg1.id = 11
        msg2.id = 12

        db.session.add(msg1, msg2)
        db.session.commit()

        u1 = User.query.get(101)
        u2 = User.query.get(102)
        msg1 = Message.query.get(11)
        msg2 = Message.query.get(12)

        self.u1 = u1
        self.u2 = u2
        self.msg1 = msg1
        self.msg2 = msg2

        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_user_model(self):
        """Does basic model work?"""

        u3 = User(
            email="test3@test.com",
            username="testuser3",
            password="HASHED_PASSWORD"
        )

        db.session.add(u3)
        db.session.commit()

        # User should have no messages, no followers & no likes
        self.assertEqual(len(u3.messages), 0)
        self.assertEqual(len(u3.followers), 0)
        self.assertEqual(len(u3.likes), 0)


    def test_signup_valid(self):
        u3 = User.signup("testuser3", "test3@test.com", "password", "")
        u3.id = 103
        db.session.commit()

        u3 = User.query.get(103)
        self.assertEqual(u3.username, "testuser3")
        self.assertEqual(u3.email, "test3@test.com")
        self.assertNotEqual(u3.password, "password")

    def test_signup_non_unique_username(self):
        u3 = User.signup("testuser1", "test3@test.com", "password", "")
        u3.id = 103

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_signup_missing_username(self):
        u4 = User.signup(None, "test3@test.com", "password", "")
        u4.id = 103

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_signup_missing_email(self):
        u4 = User.signup("testuser3", None, "password", "")
        u4.id = 103

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_signup_missing_password(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testuser3", "test3@test.com", None, "")


    def test_authentication_valid(self):
        u1 = User.authenticate("testuser1", "password")
        self.assertEqual(u1.id, 101)

    def test_authentication_invalid_username(self):
        user = User.authenticate("no-such-user", "password")
        self.assertFalse(user)

    def test_authentication_invalid_password(self):
        u1 = User.authenticate("testuser1", "incorrect-password")
        self.assertFalse(u1)


    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_has_liked(self):
        self.u2.likes.append(self.msg1)
        db.session.commit()

        self.assertTrue(self.u2.has_liked(self.msg1))
        self.assertFalse(self.u2.has_liked(self.msg2))
