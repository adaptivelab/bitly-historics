"""Tests for start_here"""
#!/usr/bin/python
# -*- coding: utf-8 -*-
# http://www.python.org/dev/peps/pep-0263/
import unittest
import datetime
import historics
import tools
import config
import fixtures

# Usage:
# $ BITLY_HISTORICS_CONFIG=testing python test_historics.py.py
# $ BITLY_HISTORICS_CONFIG=testing python -m unittest discover


class Test(unittest.TestCase):
    def setUp(self):
        config.mongo_bitly_links_raw.drop()
        config.mongo_bitly_clicks.drop()

    def test_get_hash(self):
        """Test we can extract bitly hashes from a bitly URL"""
        url_hashes = [("http://bit.ly/Wozuff", "Wozuff"),
                      ("http://bit.ly/Wozuff/", "Wozuff")]
        for url, hsh in url_hashes:
            returned_hsh = tools.get_hash(url)
            self.assertEqual(hsh, returned_hsh)

    def test_get_hash2(self):
        """From a search result check we can get a URL hash"""
        returned_hsh = tools.get_hash(fixtures.links0["aggregate_link"])
        self.assertEqual("Wozuff", returned_hsh)

    def test_clicks_by_day_popularity(self):
        """Get clicks popularity result, confirm the timestamps and activity"""
        popularity = historics.get_popularity_per_day(fixtures.clicks0)
        self.assertTrue(len(popularity) == 5, "Fixture has 5 days of results")

    def test_add_links_raw_to_mongo(self):
        """Can we add a raw links response directly into mongodb?"""
        historics.add_links_raw_to_mongodb([fixtures.links0])
        nbr_links = config.mongo_bitly_links_raw.count()
        self.assertTrue(nbr_links == 1, "Expected 1 link, not {}".format(nbr_links))
        # confirm that we don't re-add the same item
        historics.add_links_raw_to_mongodb([fixtures.links0])
        nbr_links = config.mongo_bitly_links_raw.count()
        self.assertTrue(nbr_links == 1, "Expected 1 link, not {}".format(nbr_links))
        # confirm that we add new items
        historics.add_links_raw_to_mongodb([fixtures.links1])
        nbr_links = config.mongo_bitly_links_raw.count()
        self.assertTrue(nbr_links == 2, "Expected 1 link, not {}".format(nbr_links))
        # confirm that we don't re-add the same items
        historics.add_links_raw_to_mongodb([fixtures.links0, fixtures.links1])
        nbr_links = config.mongo_bitly_links_raw.count()
        self.assertTrue(nbr_links == 2, "Expected 1 link, not {}".format(nbr_links))

    def test_add_clicks_to_mongo(self):
        """Can we add processed clicks to mongo?"""
        historics.add_clicks_to_mongodb(fixtures.clicks0)
        nbr_click_records = config.mongo_bitly_clicks.count()
        self.assertTrue(nbr_click_records == 1, "Expected 1 click record, not {}".format(nbr_click_records))
        clicks = config.mongo_bitly_clicks.find()[0]
        nbr_clicks = len(clicks['clicks'])
        self.assertTrue(nbr_clicks == 5)
        most_recent = clicks['clicks'][-1]
        self.assertTrue(clicks['updated_at'] <= datetime.datetime.utcnow(), "Update must have been recently")
        recent_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        self.assertTrue(clicks['updated_at'] > recent_time, "Update must have been recently, after " + str(recent_time))
        assert most_recent[1] == 113

        # add the same clicks, confirm list length doesn't change
        historics.add_clicks_to_mongodb(fixtures.clicks0)
        clicks = config.mongo_bitly_clicks.find()[0]
        nbr_clicks = len(clicks['clicks'])
        self.assertTrue(nbr_clicks == 5, "Expected 5 click events, not {}".format(nbr_clicks))

        # add some new and existing clicks, check we add the new ones and
        # update the existing one
        historics.add_clicks_to_mongodb(fixtures.clicks1)
        clicks = config.mongo_bitly_clicks.find()[0]
        nbr_clicks = len(clicks['clicks'])
        self.assertTrue(nbr_clicks == 7, "Expected 7 click events, not {}".format(nbr_clicks))
        most_recent = clicks['clicks'][-1]
        self.assertTrue(clicks['updated_at'] <= datetime.datetime.utcnow(), "Update must have been recently")
        self.assertTrue(clicks['updated_at'] > recent_time, "Update must have been recently, after" + str(recent_time))
        assert most_recent[1] == 115

    def test_we_find_links_to_update(self):
        bitly_links_to_update = historics.get_bitly_links_to_update()
        self.assertTrue(len(bitly_links_to_update) == 0, "Should not have anything to update yet")

        # add a new link, we haven't fetched any clicks for it yet
        historics.add_links_raw_to_mongodb([fixtures.links0])
        bitly_links_to_update = historics.get_bitly_links_to_update()
        self.assertTrue(len(bitly_links_to_update) == 1)

        # add clicks for the link, confirm we don't need to update again
        historics.add_clicks_to_mongodb(fixtures.clicks0)
        bitly_links_to_update = historics.get_bitly_links_to_update()
        self.assertTrue(len(bitly_links_to_update) == 0, "We've just updated so we don't need to update again but we have {} links to update".format(len(bitly_links_to_update)))

    def test_we_can_add_new_bitly_links_raw(self):
        canonical_url = "http://bcd.com"
        title = "some Title"
        bitly_url = "http://bit.ly/abcdEF"
        domain = "bcd.com"
        historics.add_entries_to_mongodb(bitly_url, title, canonical_url, domain)
        self.assertEqual(config.mongo_bitly_links_raw.count(), 1)
        new_links_raw = config.mongo_bitly_links_raw.find()[0]
        self.assertEqual(new_links_raw['title'], title)
        self.assertEqual(new_links_raw['aggregate_link'], bitly_url)
        self.assertEqual(new_links_raw['url'], canonical_url)

if __name__ == "__main__":
    unittest.main()
