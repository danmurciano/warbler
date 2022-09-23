"""User views tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

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

        follow1 = Follows(user_being_followed_id=101, user_following_id=102)
        like1 = Likes(user_id=102, message_id=11)

        db.session.add_all([follow1, like1])
        db.session.commit()

        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_list_users(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser1", str(resp.data))
            self.assertIn("test2@test.com", str(resp.data))


    def test_show_users(self):
        with self.client as c:
            resp = c.get("/users/101")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser1", str(resp.data))


    def test_show_following(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 102

            resp = c.get("/users/102/following")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser1", str(resp.data))


    def test_show_following_unauthorized(self):
        with self.client as c:
            resp = c.get("/users/102/following", follow_redirects=True)

            self.assertIn("Access unauthorized.", str(resp.data))


    def test_show_followers(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 101

            resp = c.get("/users/101/followers")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", str(resp.data))


    def test_show_followers_unauthorized(self):
        with self.client as c:
            resp = c.get("/users/101/followers", follow_redirects=True)

            self.assertIn("Access unauthorized.", str(resp.data))


    def test_add_follow(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 101

            resp = c.post("/users/follow/102")

            self.assertEqual(resp.status_code, 302)

            follows = Follows.query.filter(Follows.user_following_id==101).all()
            self.assertEqual(len(follows), 1)
            self.assertEqual(follows[0].user_being_followed_id, 102)


    def test_stop_follow(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 102

            resp = c.post("/users/stop-following/101")

            self.assertEqual(resp.status_code, 302)

            follows = Follows.query.filter(Follows.user_following_id==102).all()
            self.assertEqual(len(follows), 0)


    def test_show_likes(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 102

            resp = c.get("/users/102/likes")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("This is a test message", str(resp.data))


    def test_show_likes_unauthorized(self):
        with self.client as c:
            resp = c.get("/users/102/likes", follow_redirects=True)

            self.assertIn("Access unauthorized.", str(resp.data))
