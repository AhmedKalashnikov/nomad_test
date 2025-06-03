from nomadTests import NomadEnd2EndTest, NomadTestEnv, NomadAuthTest
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from playwright.sync_api import Page
import pytest

@pytest.mark.order(1)
def test_manualLogin(page: Page, browser_name: str) -> None:
    tester = NomadAuthTest()
    tester.manualLogin(page=page)
    
@pytest.mark.order(2)
def test_registration(page: Page, browser_name: str) -> None:
    tester = NomadAuthTest()
    tester.registration(page=page)

@pytest.mark.order(3)
def test_end2end(page: Page, browser_name: str) -> None:
    tester = NomadEnd2EndTest()
    tester.playthroughFromMap(page=page)
