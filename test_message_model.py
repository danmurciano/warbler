"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message

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


class MessageModelTestCase(TestCase):

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        u1 = User.signup("testuser1", "test1@test.com", "password", "")
        u1.id = 101

        db.session.commit()

        u1 = User.query.get(101)

        self.u1 = u1

        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_message_model(self):
        """Does basic model work?"""

        msg = Message(text="This is a test message", user_id=101)

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(self.u1.messages[0].text, "This is a test message")
