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
        self.driver.get("http://localhost:8000/")

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
            print("Error setting Sentry selenium-id tag")

    def teardown_method(self, test_method):
        time.sleep(5) # sleep for short time to make sure Sentry event goes out

        has_errors = False
        try:
            has_errors = self.driver.execute_script("return Sentry.lastEventId()") != None
        except:
            print("No application errors detected")

        self.driver.quit()
        if (has_errors):
            time.sleep(5)

            print("\n\n-------- JS Errors (powered by Sentry) --------")
            total_errors = 0

            url = "https://sentry.io/api/0/organizations/testorg-az/discover/query/"

            payload = "{\"orderby\":\"-time\",\"fields\":[\"id\",\"issue.id\",\"message\",\"error.type\",\"stack.filename\",\"stack.abs_path\",\"stack.lineno\",\"stack.function\",\"stack.colno\"],\"aggregations\":[[\"uniq\",\"id\",\"uniq_id\"]],\"range\":\"14d\",\"limit\":5000,\"conditions\":[[\"selenium-session-id\",\"=\",\"%s\"]],\"projects\":[261820,269722,1261841,1309317,208111,1367923,1316401,265601,288413,1319181,297017,1213077,1241612,1284466,234931,1318230,1235156,302369,1407826,228369,228436,228429,228037,1366275,1316515,1445069,1356467,1364701,300067,1257489,1366201,1241611,1313442,1314943,1267200,280125,1313446,1445070,262853,280389,1399858,1232459,1434630,1233912,1232461,1241613,1248558,272622,272646,261718,1313427,1317411,232874,1190123,1192562,272623,1410711,258421,259091,1326318,1271980,1197098,229477,252389,279552,1364567,240874,1226692,797920,298739,230024,227943,258917,1324056,1277950,226673,260278,1231280,228490,225677,304007,226985,1388365,1336446,1255106,252393,1298448,1201524,1385152],\"groupby\":[\"time\"],\"rollup\":86400}" % self.session_id
            headers = {
                'authorization': "Bearer %s" % os.environ.get('SENTRY_AUTH_TOKEN'),
                'content-type': "application/json"
            }

            response = requests.request("POST", url, data=payload, headers=headers)
            json_data = json.loads(response.text)

            for data in json_data['data']:
                if 'message' in data:
                    message = data['message']
                    print("\t%s" % message)

                    stack_indexes = range(len(data['stack.function']))
                    stack_indexes.reverse()
                    for i in stack_indexes:
                        print("\t\tat %s (%s:%s:%s)" % (data['stack.function'][i] or '?', data['stack.filename'][i], data['stack.lineno'][i], data['stack.colno'][i]))
                    print(('\tLink to Sentry Issue/Error: '
                           'https://sentry.io/testorg-az/sentry-in-selenium/issues/%s/events/%s/\n' %
                           (data['issue.id'], data['id'])))  # todo, link to event?


    def test_sampletest(self):
        # Test actions
        time.sleep(5)
        self.driver.find_element_by_id("button-1").click() # clicking will cause error
        self.driver.find_element_by_id("button-2").click() # clicking will cause error
        assert 3 == 4 # fail on purpose
