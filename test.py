from selenium import webdriver
import time

class Test:
    def setup_method(self, test_method):
        global driver
        driver = webdriver.Chrome()

        # set session id as tag
        driver.get("file:///Users/neilmanvar/PycharmProjects/sentry-in-selenium/app/app.html")

        # set session_id as Raven tag
        session_id = driver.session_id
        set_session_id_str = "Raven.setTagsContext({'selenium-session-id': '%s'})" % session_id  # need to clean up
        try:
            driver.execute_script(set_session_id_str) # error being thrown by selenium even though tag is succesfully set
        except:
            print("Sentry selenium session-id tag set")

    def teardown_method(self, test_method):
        time.sleep(1) # sleep for short time to make sure Sentry event goes out
        has_errors = driver.execute_script("return Raven.lastEventId()") != None

        driver.close()
        if (has_errors):
            # TODO: hit Sentry issues rest api (using selenium session-id as param) to obtain issues/errors and mssage into test result report
            print("TODO")

    def test_sampletest(self):
        # Test actions
        driver.find_element_by_id("button-1").click()
        assert 3 == 4 # fail on purpose
