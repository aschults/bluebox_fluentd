import unittest
import url_fwd
import mock
import requests

class UrlFwdTest(unittest.TestCase):

    def test_parse(self):
        lp = url_fwd.LineParser(parse_message_json=True)
        d1 = lp.parse_line('{"a":1,"message":"{\\"x\\":2}"}')
        self.assertEqual(1, d1["a"])
        self.assertEqual(2, d1["message"]["x"])

        self.assertRaises(Exception, lp.parse_line, "xxxxxxxxxx")
        self.assertRaises(Exception, lp.parse_line, '{"message":"xxxxx"}')

    @mock.patch('requests.request')
    @mock.patch('url_fwd.open')
    def test_request(selfi,open_mock, req_mock):
        rh = url_fwd.RequestHandler("a({a})/b({b})", content_format="C:a({a})", method="WHATEVER", content_type="xxx")
        rh.do_request(a=1)
        req_mock.assert_called_once_with("WHATEVER","a(1)/b()",headers={"Content-Type":"xxx"}, data="C:a(1)")
        open_mock.assert_not_called()

        req_mock.reset_mock()
        open_mock.return_value.__enter__.return_value.read.return_value = "C:a({a})"
        rh = url_fwd.RequestHandler("xxx", content_format="@f1", method="WHATEVER", content_type="xxx")
        rh.do_request(a=1)
        req_mock.assert_called_once_with("WHATEVER","xxx",headers={"Content-Type":"xxx"}, data="C:a(1)")


if __name__ == '__main__':
    unittest.main()
