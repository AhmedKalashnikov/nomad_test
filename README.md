# nomad_test
Test automation framework for Nomad Games - an interactive tourist guide mobile app(which is actually a wrapped web app). 
Coded in Python using Playwright Pytest with some JavaScript injections. All tests are executed in parallel with pytest-xdist.

Unfortunately for me, I got used to the mysql.connector library, which sucks for many reasons I wouldn't want to bother you with, therefore you need to create a venv with Python 3.12, because as of today, Python 3.13 isn't supported yet.

- clearlogs.py is a script for quick deletion of old test logs and screenshots.
- conftest.py is for configuring various functions like automatic screenshotting, browser context, default timeout etc.
- creds and dbCreds.csv are storages for credentials
- getObjCoordinates.py is a script for launching chromium and injecting some JavaScript that returns x and y coordinates of click position. Useful for dealing with externally generated elements.
- loginUtils.py is for automatic authentication whenever i use getObjCoordinates.py, runCodegen.py whenever I run a test which is unrelated to authentication
- pytest.ini adds various parameters to test runs e. g. '-q' for less verbose tracebacks(opposite of '-v') or 'log_cli_level=CRITICAL' for displaying only critical-level logging(so that my terminal isn't cluttered with irrelevant information - only care about details when the test fails).
- nomadTests.py is where all tests are set up and their execution flows are defined.
- runCodegen.py runs playwright codegen in an authenticated state
- test_nomad_main.py is the script where test functions are initially called from.
- requirements.txt for quick and easy installation of all required libraries('pip install -r requirements.txt')

All I have to do to run my tests is type 'pytest', and thanks to parallel execution, I'll know the results in circa 15 seconds(used to be about a minute before implementing parallelism). All tests clean up after themselves.

Libraries and frameworks used: sys, os, shutil, logging, pytest, playwright.sync_api, pytest-xdist, pytest-playwright, mysql.connector, datetime, pathlib, traceback, csv, random, re
