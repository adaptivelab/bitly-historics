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


class TestLinkClicks(unittest.TestCase):
    """"""
    def setUp(self):
        config.mongo_bitly_links_raw.drop()
        config.mongo_bitly_clicks.drop()

    def test_empty_response(self):
        empty_response = historics.process_link_clicks_response([])
        self.assertTrue(len(empty_response) == 0)

    def test_proper_response(self):
        link_clicks = historics.process_link_clicks_response(fixtures.link_clicks0)
        self.assertTrue(len(link_clicks) == len(fixtures.link_clicks0))
        last_dt = link_clicks[0][0]
        for dt, clicks in link_clicks[1:]:
            self.assertTrue(dt > last_dt)
            last_dt = dt
            self.assertTrue(clicks >= 0)

    def test_get_existing_bitly_clicks_for_norecord(self):
        hsh = "nothing"
        document = historics.get_existing_bitly_clicks_for(hsh)
        self.assertTrue(document['clicks'] == [])

        # we have a new document, updated_at is only added on a save
        self.assertTrue('updated_at' not in dir(document))
        dt_now = datetime.datetime.utcnow()
        historics.store_bitly_clicks_for(document)
        self.assertTrue(document['updated_at'] >= dt_now)

        # test that we get back the populated document (not a fresh one)
        document2 = historics.get_existing_bitly_clicks_for(hsh)
        self.assertTrue('updated_at' in document2)
        self.assertTrue(document['_id'] == document2['_id'])

        # get a second document, store, check they're distinct from each other
        hsh = "nothingelse"
        document3 = historics.get_existing_bitly_clicks_for(hsh)
        historics.store_bitly_clicks_for(document3)
        self.assertTrue(document['_id'] != document3['_id'])

    def test_add_new_clicks_to_document(self):
        hsh = "nothing"
        document = historics.get_existing_bitly_clicks_for(hsh)
        self.assertTrue(document['clicks'] == [])

        response = fixtures.link_clicks0
        historics.add_response_to_document(response, document)
        self.assertTrue(len(document['clicks']) == len(response))

        # test we don't double-add
        historics.add_response_to_document(response, document)
        self.assertTrue(len(document['clicks']) == len(response))

        # we have a new document, updated_at is only added on a save
        self.assertTrue('updated_at' not in dir(document))
        dt_now = datetime.datetime.utcnow()
        historics.store_bitly_clicks_for(document)
        self.assertTrue(document['updated_at'] >= dt_now)

        # test that we get back the populated document (not a fresh one)
        document2 = historics.get_existing_bitly_clicks_for(hsh)
        self.assertTrue('updated_at' in document2)
        self.assertTrue(document['_id'] == document2['_id'])

        response2 = fixtures.link_clicks1
        historics.add_response_to_document(response2, document)
        self.assertTrue(len(document['clicks']) == 6, len(document['clicks']))  # we want a merge of the two fixtures

        # iterate through clicks and check they're in sorted datetime order
        last_dt = document['clicks'][0][0]
        for dt, clicks in document['clicks'][1:]:
            self.assertTrue(dt > last_dt)
            last_dt = dt
            self.assertTrue(clicks >= 0)

        self.assertTrue(document['clicks'][0] == (datetime.datetime(2012, 12, 14, 4, 0), 2))
        self.assertTrue(document['clicks'][1] == (datetime.datetime(2012, 12, 16, 4, 0), 1))
        self.assertTrue(document['clicks'][5] == (datetime.datetime(2013, 3, 5, 4, 0), 1))

    def test_hash_is_active(self):
        """Check that a small time between update and most recent result mean this link is still active"""
        # check that updated_at that matches latest result means this hash is
        # considered to be still active
        response = fixtures.link_clicks0
        sorted_link_clicks = historics.process_link_clicks_response(response)
        updated_at = datetime.datetime.fromtimestamp(response[0]['dt'])
        hash_is_active = historics._hash_is_active(updated_at, sorted_link_clicks)
        self.assertTrue(hash_is_active)

        # now confirm that an older click with a recent updated_at is
        # considered as inactive
        updated_at = updated_at + config.TIMEDELTA_FOR_HASH_TO_BE_CONSIDERED_INACTIVE
        hash_is_active = historics._hash_is_active(updated_at, sorted_link_clicks)
        self.assertFalse(hash_is_active)

    def test_add_new_hourly_clicks_to_document(self):
        """Use hourly click data to update a new document"""
        hsh = "nothing"
        document = historics.get_existing_bitly_clicks_for(hsh)
        self.assertTrue(document['clicks'] == [])

        response = fixtures.link_clicks2
        historics.add_response_to_document(response, document)
        self.assertTrue(len(document['clicks']) == len(response))

        res0 = response[0]
        self.assertIsInstance(res0['clicks'], int)
        self.assertIsInstance(res0['dt'], int)
        dt = datetime.datetime.fromtimestamp(res0['dt'])
        self.assertTrue(dt.year > 2010, dt)

        # force a bit.ly record to be attached to our click history
        # and confirm that it doesn't need updating, as updated_at
        # is too recent
        canonical_url = "http://bcd.com"
        title = "some Title"
        bitly_url = "http://bit.ly/nothing"
        domain = "bcd.com"
        historics.add_entries_to_mongodb(bitly_url, title, canonical_url, domain)
        self.assertEqual(config.mongo_bitly_links_raw.count(), 1)

        historics.store_bitly_clicks_for(document)
        links_to_update = historics.get_bitly_links_to_update()
        self.assertTrue(len(links_to_update) == 0)

        # force the updated_at time to be a long while ago
        document['updated_at'] = datetime.datetime(2010, 1, 1, 1, 1)
        config.mongo_bitly_clicks.save(document)
        hash_is_active = historics._hash_is_active(document['updated_at'], document['clicks'])
        self.assertTrue(hash_is_active)
        # confirm that we need to update 1 record
        links_to_update = historics.get_bitly_links_to_update()
        self.assertTrue(len(links_to_update) == 1)

        # check that we're only tracking this one domain
        domains_we_track = historics.list_domains_we_track()
        self.assertEqual(domains_we_track, ['bcd.com'])


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

    #def test_clicks_by_day_popularity(self):
        #"""Get clicks popularity result, confirm the timestamps and activity"""
        #popularity = historics.get_popularity_per_day(fixtures.clicks0)
        #self.assertTrue(len(popularity) == 5, "Fixture has 5 days of results")

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

        # check that we're only tracking the two domains that we've added
        domains_we_track = historics.list_domains_we_track()
        self.assertEqual(domains_we_track, ['asos.com', 'guardian.co.uk'])

    #def test_add_clicks_to_mongo(self):
        #"""Can we add processed clicks to mongo?"""
        #historics.add_clicks_to_mongodb(fixtures.clicks0)
        #nbr_click_records = config.mongo_bitly_clicks.count()
        #self.assertTrue(nbr_click_records == 1, "Expected 1 click record, not {}".format(nbr_click_records))
        #clicks = config.mongo_bitly_clicks.find()[0]
        #nbr_clicks = len(clicks['clicks'])
        #self.assertTrue(nbr_clicks == 5)
        #most_recent = clicks['clicks'][-1]
        #self.assertTrue(clicks['updated_at'] <= datetime.datetime.utcnow(), "Update must have been recently")
        #recent_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        #self.assertTrue(clicks['updated_at'] > recent_time, "Update must have been recently, after " + str(recent_time))
        #assert most_recent[1] == 113

        ## add the same clicks, confirm list length doesn't change
        #historics.add_clicks_to_mongodb(fixtures.clicks0)
        #clicks = config.mongo_bitly_clicks.find()[0]
        #nbr_clicks = len(clicks['clicks'])
        #self.assertTrue(nbr_clicks == 5, "Expected 5 click events, not {}".format(nbr_clicks))

        ## add some new and existing clicks, check we add the new ones and
        ## update the existing one
        #historics.add_clicks_to_mongodb(fixtures.clicks1)
        #clicks = config.mongo_bitly_clicks.find()[0]
        #nbr_clicks = len(clicks['clicks'])
        #self.assertTrue(nbr_clicks == 7, "Expected 7 click events, not {}".format(nbr_clicks))
        #most_recent = clicks['clicks'][-1]
        #self.assertTrue(clicks['updated_at'] <= datetime.datetime.utcnow(), "Update must have been recently")
        #self.assertTrue(clicks['updated_at'] > recent_time, "Update must have been recently, after" + str(recent_time))
        #assert most_recent[1] == 115

    #def test_we_find_links_to_update(self):
        #bitly_links_to_update = historics.get_bitly_links_to_update()
        #self.assertTrue(len(bitly_links_to_update) == 0, "Should not have anything to update yet")

        ## add a new link, we haven't fetched any clicks for it yet
        #historics.add_links_raw_to_mongodb([fixtures.links0])
        #bitly_links_to_update = historics.get_bitly_links_to_update()
        #self.assertTrue(len(bitly_links_to_update) == 1)

        ## add clicks for the link, confirm we don't need to update again
        #historics.add_clicks_to_mongodb(fixtures.clicks0)
        #bitly_links_to_update = historics.get_bitly_links_to_update()
        #self.assertTrue(len(bitly_links_to_update) == 0, "We've just updated so we don't need to update again but we have {} links to update".format(len(bitly_links_to_update)))

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
