"""Offline checks for safe HTML output and digest MIME structure."""

import tempfile
import unittest
from email import policy
from email.parser import BytesParser
from pathlib import Path

from notify_modules.email_sender import _build_digest_message, build_html_body
from output_modules.html_builder import write_html_dashboard


class OutputSafetyTests(unittest.TestCase):
    def test_email_html_escapes_untrusted_paper_fields_and_rejects_unsafe_links(self):
        paper = {
            "Title": '<img src=x onerror="alert(1)">',
            "Link": 'javascript:alert(1)',
            "Authors": ['<svg onload="alert(2)">'],
            "Journal": '<script>alert(3)</script>',
            "Date": "2025/01/01",
            "Source": "fixture",
            "MatchedKeywords": ["<b>term</b>"],
        }

        body = build_html_body([paper], ("2025/01/01", "2025/01/07"))

        self.assertNotIn('<img src=x', body)
        self.assertNotIn('<svg onload=', body)
        self.assertNotIn('<script>alert(3)</script>', body)
        self.assertNotIn('href="javascript:', body)
        self.assertIn("&lt;img", body)

    def test_dashboard_escapes_api_and_configuration_values(self):
        with tempfile.TemporaryDirectory() as directory:
            html_path = Path(directory) / "dashboard.html"
            json_path = Path(directory) / "results.json"
            write_html_dashboard(
                start_end_date=("2025/01/01", "2025/01/07"),
                config_file_dict={"email": '<script>alert("email")</script>'},
                components=[{
                    "Source": "keyword",
                    "Title": '<img src=x onerror="alert(1)">',
                    "Abstract": '<script>alert("abstract")</script>',
                    "Journal": "Journal <b>name</b>",
                    "Authors": ["Author <svg onload=x>"],
                    "Institution": ["Lab <iframe src=x>"] ,
                    "Date": "2025/01/01",
                    "Link": "javascript:alert(1)",
                }],
                keyword_frequency_dict={},
                html_name=str(html_path),
                json_dump_path=str(json_path),
                auto_mode=True,
            )
            html = html_path.read_text(encoding="utf-8")

        self.assertNotIn('<img src=x', html)
        self.assertNotIn('<script>alert("email")</script>', html)
        self.assertNotIn('<script>alert("abstract")</script>', html)
        self.assertNotIn('href="javascript:', html)
        self.assertIn("&lt;iframe", html)

    def test_html_attachment_is_nested_beside_alternative_body(self):
        with tempfile.TemporaryDirectory() as directory:
            attachment_path = Path(directory) / "dashboard.html"
            attachment_path.write_text("<html>demo</html>", encoding="utf-8")
            message = _build_digest_message(
                [], ("2025/01/01", "2025/01/07"),
                "sender@example.invalid", "recipient@example.invalid",
                str(attachment_path),
            )

        parsed = BytesParser(policy=policy.default).parsebytes(message.as_bytes())
        self.assertEqual(parsed.get_content_type(), "multipart/mixed")
        parts = list(parsed.iter_parts())
        self.assertEqual(parts[0].get_content_type(), "multipart/alternative")
        self.assertEqual(
            [part.get_content_type() for part in parts[0].iter_parts()],
            ["text/plain", "text/html"],
        )
        self.assertEqual(parts[1].get_content_type(), "application/html")
        self.assertEqual(parts[1].get_filename(), "publications.html")


if __name__ == "__main__":
    unittest.main()
