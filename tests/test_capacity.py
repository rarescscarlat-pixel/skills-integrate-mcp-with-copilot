import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi import HTTPException

from src.app import activities, signup_for_activity


class SignupCapacityTests(unittest.TestCase):
    activity_name = "Capacity Test Activity"

    def setUp(self):
        activities[self.activity_name] = {
            "description": "Test activity",
            "schedule": "Test schedule",
            "max_participants": 2,
            "participants": ["first@example.com", "second@example.com"],
        }

    def tearDown(self):
        del activities[self.activity_name]

    def test_rejects_signup_when_activity_is_full(self):
        with self.assertRaises(HTTPException) as raised:
            signup_for_activity(self.activity_name, "third@example.com")

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail, "Activity is full")
        self.assertEqual(
            len(activities[self.activity_name]["participants"]),
            activities[self.activity_name]["max_participants"],
        )

    def test_only_one_concurrent_signup_gets_the_last_spot(self):
        activity = activities[self.activity_name]
        activity["max_participants"] = 1
        activity["participants"] = []
        barrier = Barrier(2)

        def attempt_signup(email):
            barrier.wait()
            try:
                signup_for_activity(self.activity_name, email)
                return "signed up"
            except HTTPException as error:
                return error.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(
                attempt_signup,
                ["first@example.com", "second@example.com"],
            ))

        self.assertCountEqual(results, ["signed up", 409])
        self.assertEqual(len(activity["participants"]), 1)


if __name__ == "__main__":
    unittest.main()