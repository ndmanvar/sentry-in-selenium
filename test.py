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
        self.driver.get("http://localhost:5000/")

        # set session_id as Sentry tag
        self.session_id = self.driver.session_id
        print('\nSauceOnDemandSessionID=%s job-name=test-name' % self.session_id)
        self.driver.execute_script("Sentry && \
            Sentry.configureScope(function (scope) { \
                scope.setTag('selenium-session-id', '%s'); \
                scope.setTag('build-name', '%s'); \
            })" % (self.session_id, os.environ.get('BUILD_TAG')))
        time.sleep(3)

    def teardown_method(self, test_method):
        time.sleep(3) # sleep for short time to make sure Sentry event goes out
        has_errors = self.driver.execute_script("return Sentry.lastEventId()") != None
        self.driver.quit()

        if (has_errors):
            time.sleep(3)
            print("\n\n-------------------------------- JS Errors (powered by Sentry) --------------------------------")

            payload = {
               "orderby": "-time",
               "fields": [
                  "id", "issue.id", "message", "error.type", "stack.filename", "stack.abs_path", "stack.lineno",
                  "stack.function", "stack.colno"
               ],
               "aggregations": [
                  [ "uniq", "id", "uniq_id" ]
               ],
               "range": "14d",
               "conditions": [[ "selenium-session-id", "=", self.session_id]],
               "projects": [ 304007, 1356467 ],
               "groupby": [ "time" ]
            }
            headers = {
                'authorization': "Bearer %s" % os.environ.get('SENTRY_AUTH_TOKEN'),
                'content-type': "application/json"
            }
            response = requests.request("POST", "https://sentry.io/api/0/organizations/testorg-az/discover/query/",
                                        data=json.dumps(payload), headers=headers)
            json_data = json.loads(response.text)

            for data in json_data['data']:
                if 'message' in data:
                    print("\t%s" % data['message'])

                    stack_indexes = range(len(data['stack.function']))
                    stack_indexes.reverse()
                    for i in stack_indexes:
                        print("\t\tat %s (%s:%s:%s)"
                              % (data['stack.function'][i] or '?', data['stack.filename'][i],
                                 data['stack.lineno'][i],
                                 data['stack.colno'][i]))
                    print(('\tLink to Sentry Issue/Error: '
                           'https://sentry.io/testorg-az/sentry-in-selenium/issues/%s/events/%s/\n' %
                           (data['issue.id'], data['id'])))

    def test_sampletest(self):
        # Test actions

        # add two items to cart
        self.driver.find_element_by_xpath("(//div[contains(@class,'inventory')]//button)[1]").click()
        self.driver.find_element_by_xpath("(//div[contains(@class,'inventory')]//button)[1]").click()

        # click on Checkout
        self.driver.find_element_by_css_selector(".sidebar button").click()

        # assert success message is present/displayed
        assert self.driver.find_element_by_class_name("cart-success").is_displayed()
