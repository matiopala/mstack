import unittest
from unittest.mock import MagicMock, patch

from sender import send


class SenderTests(unittest.TestCase):
    @patch("sender.urlopen")
    def test_sends_json_post(self, urlopen):
        response = MagicMock()
        response.__enter__.return_value.status = 202
        urlopen.return_value = response
        self.assertEqual(send("https://staging.invalid/events", {"kind": "ping"}), 202)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.data, b'{"kind": "ping"}')


if __name__ == "__main__":
    unittest.main()
