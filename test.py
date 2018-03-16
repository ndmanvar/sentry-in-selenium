from selenium import webdriver
import time
import requests
import json
import os



class Test:
    def setup_method(self, test_method):
        global driver
        driver = webdriver.Chrome()

        # set session id as tag
        driver.get("file:///Users/neilmanvar/PycharmProjects/sentry-in-selenium/app/app.html")

        # set session_id as Raven tag
        global session_id
        session_id= driver.session_id
        print("Selenium session id is : %s" % session_id)
        set_session_id_str = "Raven.setTagsContext({'selenium-session-id': '%s'})" % session_id  # need to clean up
        try:
            driver.execute_script(set_session_id_str) # error being thrown by selenium even though tag is succesfully set
        except:
            print("Sentry selenium session-id tag set")


    def teardown_method(self, test_method):
        time.sleep(5) # sleep for short time to make sure Sentry event goes out
        has_errors = driver.execute_script("return Raven.lastEventId()") != None

        driver.close()
        if (has_errors):
            # TODO: hit Sentry issues rest api (using selenium session-id as param) to obtain issues/errors and mssage into test result report
            time.sleep(180) # sleep for X seconds due to event ingestion
            url = "https://sentry.io/api/0/projects/testorg-az/sentry-in-selenium/issues/"
            querystring = {
                "query": "selenium-session-id:%s" % session_id,
                "limit": 25
                }
            headers = {
                'authorization': "Bearer %s" % os.environ.get('SENTRY_AUTH_TOKEN') # TODO: use env var
            }
            response = requests.request("GET", url, headers=headers, params=querystring)
            json_data = json.loads(response.text)
            print("-------- %s JS Errors (courtesy of Sentry) --------" % len(json_data))
            for issue in json_data:
                print("%s - %s" % (issue['title'], issue['permalink']))

    def test_sampletest(self):
        # Test actions
        driver.find_element_by_id("button-1").click()
        driver.find_element_by_id("button-2").click()
        assert 3 == 4 # fail on purpose
