"""Offline Telegram public preview ingestion safety tests."""
import unittest
from scripts.discover_news import harvest_telegram

SOURCE = {"id": "simorghdata369", "handle": "simorghdata369", "endpoint": "https://t.me/s/simorghdata369"}
PAGE = """
<section>
<div class="tgme_widget_message_wrap">
  <div class="tgme_widget_message js-widget_message" data-post="simorghdata369/123">
    <div class="tgme_widget_message_text js-message_text">
      <b>گزارش تازه درباره ایران و تنگه هرمز</b><br/>
      مقام‌های رسمی درباره وضعیت تجاری منطقه گفته‌اند که بررسی‌ها همچنان ادامه دارد و نتیجه مستقلی منتشر نشده است.
    </div>
    <a class="tgme_widget_message_date" href="https://t.me/simorghdata369/123"><time datetime="2026-11-01T11:00:00+00:00">11:00</time></a>
  </div>
</div>
<div class="tgme_widget_message" data-post="simorghdata369/124">
  <div class="tgme_widget_message_text">گزارش درباره وضعیت انتخاباتی یک کشور اروپایی و برنامه‌های محلی آن است که ارتباط مستقیمی با موضوع ما ندارد.</div>
  <time datetime="2026-11-01T12:00:00+00:00"></time>
</div>
<div class="tgme_widget_message" data-post="other/125">
  <div class="tgme_widget_message_text">ایران ایران ایران؛ این پست متعلق به کانال دیگری است و باید حذف شود.</div>
  <time datetime="2026-11-01T12:00:00+00:00"></time>
</div>
</section>
"""

class TelegramPreviewTests(unittest.TestCase):
    def test_candidate_is_attributed_not_verified(self):
        rows = list(harvest_telegram(SOURCE, payload=PAGE))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://t.me/simorghdata369/123")
        self.assertEqual(rows[0]["published"], "2026-11-01T11:00:00+00:00")
        self.assertEqual(rows[0]["status"], "unverified_candidate")
        self.assertIsNone(rows[0]["score_effect"])
        self.assertIn("تنگه هرمز", rows[0]["excerpt"])

    def test_stable_ids_and_no_date_rejected(self):
        a = list(harvest_telegram(SOURCE, payload=PAGE))
        b = list(harvest_telegram(SOURCE, payload=PAGE))
        self.assertEqual(a, b)
        self.assertEqual(list(harvest_telegram(SOURCE, payload='<div data-post="simorghdata369/4"><div class="tgme_widget_message_text">ایران ' + 'خبر ' * 30 + '</div></div>')), [])

if __name__ == "__main__":
    unittest.main()
