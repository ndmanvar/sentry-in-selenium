from selenium import webdriver
import time
import requests
import json
import os

class Test:
    def setup_method(self, test_method):
        username = os.environ.get('SAUCE_USERNAME')
        access_key = os.environ.get('SAUCE_ACCESS_KEY')
        self.driver = webdriver.Remote(
            command_executor='https://%s:%s@ondemand.saucelabs.com:443/wd/hub' % (username, access_key),
            desired_capabilities={
                'platform': "Windows 7",
                'browserName': "chrome",
                'version': "latest",
                'name': 'test-name',
                'extendedDebugging': True,
            })

        self.driver.get("http://localhost:8080/app.html")

        # set session_id as Raven tag
        self.session_id = self.driver.session_id
        print('\nSauceOnDemandSessionID=%s job-name=test-name' % self.session_id)
        set_session_id_str = "Raven && Raven.setTagsContext({'selenium-session-id': '%s'}) && \
                        Raven.setTagsContext({'build-name': '%s'})" % (self.session_id, os.environ.get('BUILD_TAG'))
        try:
            # error being thrown by selenium even though tag is succesfully set
            self.driver.execute_script(set_session_id_str)
        except:
            print("Sentry selenium session-id tag set")


    def teardown_method(self, test_method):
        time.sleep(5) # sleep for short time to make sure Sentry event goes out
        has_errors = self.driver.execute_script("return Raven.lastEventId()") != None

        self.driver.quit()
        if (has_errors):
            time.sleep(5)
            url = "https://sentry.io/api/0/projects/testorg-az/sentry-in-selenium/events/"
            querystring = {
                # "query": "selenium-session-id:%s" % self.session_id,
                "limit": 25
                }
            headers = {
                'authorization': "Bearer %s" % os.environ.get('SENTRY_AUTH_TOKEN')
            }
            response = requests.request("GET", url, headers=headers, params=querystring)
            json_data = json.loads(response.text)

            print("-------- JS Errors (courtesy of Sentry) --------")
            total_errors = 0
            for event in json_data:
                for tag in event['tags']:
                    if tag['key'] == 'selenium-session-id' and tag['value'] == self.session_id:
                        total_errors += 1
                        print("Error #%s:" % total_errors)
                        print("\tError Message: %s" % event['message'])
                        print(('\tLink to Sentry Issue: '
                            'https://sentry.io/testorg-az/sentry-in-selenium/issues/%s/' % event['groupID']))

    def test_sampletest(self):
        # Test actions
        time.sleep(5)
        self.driver.find_element_by_id("button-1").click() # clicking will cause error
        self.driver.find_element_by_id("button-2").click() # clicking will cause error
        assert 3 == 4 # fail on purpose
