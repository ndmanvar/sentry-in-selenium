REPORT_NAME=reports.xml

run_sc:
	./sc

run_app_server:
	cd app && python -m SimpleHTTPServer

run_tests:
	rm -rf $(REPORT_NAME) && pytest --junitxml=$(REPORT_NAME) test.py