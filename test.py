from selenium import webdriver
import time
import requests
import json
import os

class Test:
    def setup_method(self, test_method):
        # launch browser (on saucelabs)
        self.driver = webdriver.Remote(
            command_executor='https://%s:%s@ondemand.saucelabs.com:443/wd/hub' %
                             (os.environ.get('SAUCE_USERNAME'), os.environ.get('SAUCE_ACCESS_KEY')),
            desired_capabilities={
                'platform': "Windows 7",
                'browserName': "chrome",
                'version': "latest",
                'name': 'test-name',
                'extendedDebugging': True,
                'commandTimeout': 300
            })

        # go to test application (via sauce-connect)
        self.driver.get("http://localhost:8000/app.html")

        # set session_id as Sentry tag
        self.session_id = self.driver.session_id
        print('\nSauceOnDemandSessionID=%s job-name=test-name' % self.session_id)
        set_session_id_str = "Sentry && \
            Sentry.configureScope(function (scope) { \
                scope.setTag('selenium-session-id', '%s'); \
                scope.setTag('build-name', '%s'); \
            })" % (self.session_id, os.environ.get('BUILD_TAG'))
        try:
            # error being thrown by selenium even though tag is successfully set
            self.driver.execute_script(set_session_id_str)
        except:
            print("Sentry selenium session-id tag set")

    def teardown_method(self, test_method):
        time.sleep(5) # sleep for short time to make sure Sentry event goes out
        has_errors = self.driver.execute_script("return Sentry.lastEventId()") != None

        self.driver.quit()
        if (has_errors):
            time.sleep(5)
            url = "https://sentry.io/api/0/organizations/testorg-az/events/?statsPeriod=14d&query=selenium-session-id%%3A%%22%s%%22" % self.session_id
            headers = {
                'authorization': "Bearer %s" % os.environ.get('SENTRY_AUTH_TOKEN')
            }
            response = requests.get(url, headers=headers)
            json_data = json.loads(response.text)

            print("-------- JS Errors (courtesy of Sentry) --------")
            total_errors = 0
            for event in json_data:
                        total_errors += 1
                        print("Error #%s:" % total_errors)
                        print("\tError Message: %s" % event['message'])
                        for frame in reversed(event['entries'][0]['data']['values'][0]['stacktrace']['frames']):
                            print("\t\tat %s (%s:%s:%s)" %
                                  (frame['function'] or '?', frame['filename'], frame['lineNo'], frame['colNo']))
                        print(('\n\tLink to Sentry Issue/Error: '
                               'https://sentry.io/testorg-az/sentry-in-selenium/issues/%s/events/%s/\n' %
                               (event['groupID'], event['eventID'])))  # todo, link to event?

    def test_sampletest(self):
        # Test actions
        time.sleep(5)
        self.driver.find_element_by_id("button-1").click() # clicking will cause error
        self.driver.find_element_by_id("button-2").click() # clicking will cause error
        assert 3 == 4 # fail on purpose
