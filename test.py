from selenium import webdriver
import time
import requests
import json
import os

class Test:
    def setup_method(self, test_method):
        self.driver = webdriver.Chrome()

        # set session id as tag
        self.driver.get("file:///Users/neilmanvar/PycharmProjects/sentry-in-selenium/app/app.html")

        # set session_id as Raven tag
        self.session_id = self.driver.session_id
        print("Selenium session id is : %s" % self.session_id)
        set_session_id_str = "Raven.setTagsContext({'selenium-session-id': '%s'})" % self.session_id  # need to clean up
        try:
            self.driver.execute_script(set_session_id_str) # error being thrown by selenium even though tag is succesfully set
        except:
            print("Sentry selenium session-id tag set")


    def teardown_method(self, test_method):
        time.sleep(1) # sleep for short time to make sure Sentry event goes out
        has_errors = self.driver.execute_script("return Raven.lastEventId()") != None

        self.driver.close()
        if (has_errors):
            time.sleep(3) # sleep for 180 seconds due to event ingestion
            url = "https://sentry.io/api/0/projects/testorg-az/sentry-in-selenium/events/"
            querystring = {
                # "query": "selenium-session-id:%s" % self.session_id,
                "limit": 25
                }
            headers = {
                'authorization': "Bearer %s" % os.environ.get('SENTRY_AUTH_TOKEN') # TODO: use env var
            }
            response = requests.request("GET", url, headers=headers, params=querystring)
            json_data = json.loads(response.text)

            print("-------- JS Errors (courtesy of Sentry) --------")
            for event in json_data:
                for tag in event['tags']:
                    if tag['key'] == 'selenium-session-id' and tag['value'] == self.session_id:
                        print("https://sentry.io/testorg-az/sentry-in-selenium/issues/%s/" % event['groupID'])


    def test_sampletest(self):
        # Test actions
        self.driver.find_element_by_id("button-1").click()
        self.driver.find_element_by_id("button-2").click()
        assert 3 == 4 # fail on purpose
