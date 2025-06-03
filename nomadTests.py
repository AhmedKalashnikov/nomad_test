import csv, pytest, logging, random, re, pyautogui
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from playwright.sync_api import Page
from loginUtils import get_user_credentials, nomadLogin


class NomadTestEnv:
    '''Class for setting up the test environment.'''

    def __init__(self):
            
        def get_db_credentials(dbCredsDir) -> list:
            '''Reads and returns database credentials from a csv.'''

            with open(dbCredsDir) as dbCredsFile:
                dbCredsReader = csv.reader(dbCredsFile)
                dbCreds = list(dbCredsReader)
                flat_creds = [item for sublist in dbCreds for item in sublist]
                if len(flat_creds) >= 4:
                    return flat_creds[:4]
                else:
                    raise ValueError("Missing credentials in CSV file")

        def connectToDb() -> tuple[MySQLConnection, MySQLCursor]:
            '''Connects to the Nomad databse with fetched credentials. \n
            Returns cursor and connection objects for database manipulation.'''

            dbHost, dbUser, dbPwd, dbName = get_db_credentials('dbCreds.csv')
            primary_app_db = MySQLConnection(
            host = dbHost, user = dbUser,
            password = dbPwd, database = dbName,
            buffered = True)
            cursor = primary_app_db.cursor()
            return cursor, primary_app_db
        
        try:
            self.testUsername = 'tester' + str(random.randint(100_000, 999_999))
            self.creds = get_user_credentials('creds.csv')
            self.email1, self.pwd1, self.email2, self.pwd2 = self.creds
            self.cursor, self.db = connectToDb()
            self.homepage = 'https://app.nomad-games.eu'
            self.bypassAutomationDetectionJS = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                delete window.chrome.runtime.onConnect;
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['cs-CZ', 'cs'],
                });
                
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """
            logging.info('Test environment set up successfully.')
        
        except Exception as E:
            logging.error(f'Error setting up test environment: {E}')

    
    def __repr__(self):
        return f'Test environment: {self.testUsername}, {self.homepage}'
    
    

class NomadAuthTest(NomadTestEnv):
    '''Class for testing authentication functionality.'''
    def __init__(self):
        super().__init__()

    def manualLogin(self, page: Page, withLogOut: bool = True):
        '''Test manual login with fetched credentials.'''
        try:
            logging.debug('MANUAL LOGIN: Open app.')
            page.goto(self.homepage)
            logging.debug('MANUAL LOGIN: Press manual log in option button.')
            page.get_by_role("button", name="Log in (manually)").click()
            logging.debug('MANUAL LOGIN: Select e-mail form.')
            page.get_by_role("textbox", name="Email (username)").click()
            logging.debug('MANUAL LOGIN: Type e-mail.')
            page.get_by_role("textbox", name="Email (username)").fill(self.email1)
            logging.debug('MANUAL LOGIN: Select password form.')
            page.get_by_role("textbox", name="Password").click()
            logging.debug('MANUAL LOGIN: Type password.')
            page.get_by_role("textbox", name="Password").fill(str(self.pwd1))
            logging.debug('MANUAL LOGIN: Check "remember credentials".')
            page.locator(".mat-checkbox-inner-container").click()
            logging.debug('MANUAL LOGIN: Click log in button.')
            page.get_by_role("button", name="Log in").click()

        except Exception as E:
            logging.error(E)
            pytest.fail(pytrace=False)

        # log out if requested
        try:
            if withLogOut: 
                logging.debug('MANUAL LOGIN: Click log out button.')
                page.locator("#sn_logout").click()
                page.wait_for_url(self.homepage, timeout=10000)
                assert page.url.startswith(self.homepage)

        # check if url is correct post-logout
        except AssertionError as A:
            actual_url = page.url
            logging.debug(f'MANUAL LOGIN: Expected URL: {self.homepage}')
            logging.debug(f'MANUAL LOGIN: Actual URL: {actual_url}')


    def googleLogin(self, page: Page, withLogOut: bool = True):
        '''NOT IN USE : Test Google login.'''
        try:
            logging.debug('GOOGLE LOGIN: Run script for bypassing automation detection.')
            page.add_init_script(self.bypassAutomationDetectionJS)
            logging.debug('GOOGLE LOGIN: Open app.')
            page.goto(self.homepage)
            logging.debug('GOOGLE LOGIN: Press Google log in option button.')
            page.get_by_role("button", name="Log in (Google)").click()
            logging.debug('GOOGLE LOGIN: Click E-mail form.')
            page.locator("#identifierId").click()
            logging.debug('GOOGLE LOGIN: Fill E-mail form.')
            page.locator("#identifierId").fill(str(self.email1))
            logging.debug('GOOGLE LOGIN: Go to next section.')
            page.get_by_role("button", name="Další").locator("span").click()
            logging.debug('GOOGLE LOGIN: Click password form.')
            page.get_by_text("Zadejte heslo").click()
            logging.debug('GOOGLE LOGIN: Fill password form.')
            page.get_by_text("Zadejte heslo").fill(str(self.pwd1))
            logging.debug('GOOGLE LOGIN: Finish login by pressing [next] button.')
            page.get_by_role("button", name="Další").locator("span").click()          

        except Exception as E:
            logging.error(E)
            pytest.fail(pytrace=False)
        
        # log out if requested
        try:
            if withLogOut: 
                logging.debug('GOOGLE LOGIN: Click log out button.')
                page.locator("#sn_logout").click()
                page.wait_for_url(self.homepage, timeout=10000)
                assert page.url.startswith(self.homepage)

        # check if url is correct post-logout
        except AssertionError as A:
            actual_url = page.url
            logging.debug(f'GOOGLE LOGIN: Expected URL: {self.homepage}')
            logging.debug(f'GOOGLE LOGIN: Actual URL: {actual_url}')

        logging.info('GOOGLE LOGIN PASSED!')    


            
    def registration(self, page: Page) -> None:
        '''Test the registration with fetched credentials.'''
        cursor = self.cursor
        db = self.db

        try: # clean up from previous tests.
            logging.debug('REGISTRATION: Clean up from previous tests.')        
            cursor.execute('''
                        SELECT id
                        FROM tenant as t
                        WHERE email = %s;
                        ''', (self.email2,)) 
            
            accsToDelete = cursor.fetchall()
            if len(accsToDelete) > 0:

                accToDeleteIDs = [accID[0] for accID in accsToDelete]
                # generate placeholders for the in clause
                placeholders =' ,'.join(['%s'] * len(accToDeleteIDs))

                deleteFromTenantLangQuery = f'''DELETE FROM tenant_language
                                WHERE tenant IN {placeholders};'''
                deleteFromTenantQuery = f'''DELETE FROM tenant
                            WHERE id IN {placeholders};'''
                
                cursor.execute(deleteFromTenantLangQuery, accToDeleteIDs)
                cursor.execute(deleteFromTenantQuery, accToDeleteIDs)

                db.commit()

        except Exception as E:
            logging.error(f"Couldn't clean up : {E}")
            pytest.fail(pytrace=False)


        logging.info('REGISTRATION: ALL CLEAN!')

        try: # perform test
            logging.debug('REGISTRATION: Open app.')
            page.goto(self.homepage)
            logging.debug('REGISTRATION: Select registration menu option.')
            page.get_by_role("link", name="Registration").click()

            # fill registration form
            logging.debug('REGISTRATION: Select e-mail form.')
            page.get_by_role("textbox", name="Email (username)").click()
            logging.debug('REGISTRATION: Type e-mail')
            page.get_by_role("textbox", name="Email (username)").fill(str(self.email2))
            logging.debug('REGISTRATION: Select username form.')
            page.get_by_role("textbox", name="Username", exact=True).click()
            logging.debug('REGISTRATION: Type username.')
            page.get_by_role("textbox", name="Username", exact=True).fill(self.testUsername)
            logging.debug('REGISTRATION: Select password form.')
            page.get_by_role("textbox", name="New password", exact=True).click()
            logging.debug('REGISTRATION: Type password')
            page.get_by_role("textbox", name="New password", exact=True).fill(str(self.pwd2))
            logging.debug('REGISTRATION: Select password confirmation form.')
            page.get_by_role("textbox", name="New password confirmation").click()
            logging.debug('REGISTRATION: Type password confirmation.')
            page.get_by_role("textbox", name="New password confirmation").fill(str(self.pwd2))

            # select languages
            logging.debug('REGISTRATION: Click UI language form.')
            page.get_by_role("listbox", name="Language").locator("div").nth(1).click()
            logging.debug('REGISTRATION: Select english.')
            page.get_by_role("option", name="English").locator("span").click()
            logging.debug('REGISTRATION: Click spoken languages form.')
            page.get_by_role("textbox", name="Languages that you speak").click()
            logging.debug('REGISTRATION: Select Italian as second language(first language should be english).')
            page.locator("label").filter(has_text="Italiano").click()
            logging.debug('REGISTRATION: Apply chosen languages by clicking [Apply].')
            page.get_by_role("button", name="Apply").locator("span").click()
            logging.debug('REGISTRATION: Press [next] to go to next section.')
            page.get_by_role("button", name="Next").locator("span").click

            # accept terms and complete registration
            logging.debug('REGISTRATION: Check consent privacy agreements.')
            page.locator(".mat-checkbox-inner-container").first.click()
            logging.debug('REGISTRATION: Check consent user agreements.')
            page.get_by_label('I read and I agree with terms & conditions')
            logging.debug('REGISTRATION: Press [next] button.')
            page.get_by_role("button", name="Next").locator("span").click
            logging.debug('REGISTRATION: Finish registration by pressing [register].')
            page.get_by_text('REGISTRATION').locator("span").click()
            logging.debug('REGISTRATION: Press [OK] on e-mail confirmation alert.')
            page.get_by_text('OK').locator("span").click()
            
            # check if new user was actually created
            cursor.execute('''SELECT email 
                           FROM tenant 
                           WHERE email = %s;''', (self.email2,))
            new_user = cursor.fetchall()
            assert len(new_user) > 0, f"User {self.email2} should be created in database."

            logging.info('REGISTRATION PASSED!')
        
        except Exception as E:
            logging.error(E)
            pytest.fail(pytrace=False)

        finally: 
            db.close()
            cursor.close()


class NomadEnd2EndTest(NomadAuthTest):
    '''Class for end-to-end testing.'''
    def __init__(self):
        super().__init__()
        self.review = 'this is a rest teview hello world'
    
    def playthroughFromMap(self, page: Page) -> None:
        '''Plays a scenario from map and leaves a review.'''
        cursor = self.cursor
        db = self.db
        reviewTestSummary = 'this is a rest teview hello world'

        try: # clean up from previous tests
            logging.debug('PLAYTHROUGH FROM MAP: Clean up from previous tests.')
            cursor.execute('''SELECT id
                           FROM review
                           WHERE summary = %s''', (reviewTestSummary,))  
            reviewsToDelete = cursor.fetchall()

            if len(reviewsToDelete) > 0:
                reviewIDs = [review[0] for review in reviewsToDelete]

                # generate placeholders for the IN clause
                placeholders = ', '.join(['%s'] * len(reviewIDs))

                delete_coin_transaction_query = f'''DELETE FROM coin_transaction WHERE review IN ({placeholders})'''
                delete_review_score_query = f'''DELETE FROM review_score WHERE review IN ({placeholders})'''
                delete_review_query = f'''DELETE FROM review WHERE id IN ({placeholders})'''

                cursor.execute(delete_coin_transaction_query, reviewIDs)
                cursor.execute(delete_review_score_query, reviewIDs)
                cursor.execute(delete_review_query, reviewIDs)

                db.commit()
                logging.info('PLAYTHROUGH FROM MAP: ALL CLEAN!')

        except Exception as E:
            logging.error(f"Couldn't clean up :{E}")
            pytest.fail(pytrace=False)

        finally:
            db.close()
            cursor.close()
        
        
        try: # perform test
            nomadLogin(page=page)
            
            # choose and initialize scenario
            logging.debug('PLAYTHROUGH FROM MAP: Click scenario pin on map.')
            page.wait_for_load_state('networkidle')
            page.mouse.click(582, 292) # because the pin is hard to locate since it's generated by Angular Google Maps API
            logging.debug('PLAYTHROUGH FROM MAP: Click [Choose] to start scenario.')
            page.get_by_role("button", name="Choose").click()
            logging.debug('PLAYTHROUGH FROM MAP: After intro press [next] button.')
            page.get_by_text("Next").click()

            # answer questions
            logging.debug('PLAYTHROUGH FROM MAP -Q1: Choose an answer.')
            page.get_by_text("př. n. l.").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q1: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q1: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q1: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q2: Choose an answer.')
            page.get_by_text("Zeď politických vězňů").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q2: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q2: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q2: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q3: Choose an answer.')
            page.get_by_text("Huang Nguyen").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q3: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q3 Press [next] button 1.')
            page.get_by_text("Next").click()

            # check question image
            logging.debug('PLAYTHROUGH FROM MAP -Q3: Check image.')
            page.locator("#img_img").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q3: Go back from image.')
            page.get_by_text("Return").click()

            # continue playing
            logging.debug('PLAYTHROUGH FROM MAP -Q3: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q4: Choose an answer.')
            page.get_by_text("Nižší - Baroko, Vyšší - Gotika").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q4: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q4: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q4: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q5: Choose an answer.')
            page.get_by_text("Jeroným Kohl").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q5: Check explanation')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q5: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q5: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q6: Choose an answer.')
            page.get_by_text("První zemětřesení v česku.").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q6: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q6: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q6: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q7: Choose an answer.')
            page.get_by_text("Komplex Pražského hradu").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q7: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q7: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q7: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q8: Choose an answer.')
            page.get_by_text("3").first.click()
            logging.debug('PLAYTHROUGH FROM MAP -Q8: Check explanation. ')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q8: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q8: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q9: Choose an answer.')
            page.get_by_text("Na Náměstí Republiky").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q9: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q9: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q9: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q10: Choose an answer.')
            page.get_by_text("Říp").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q10: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q10: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q10: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q11: Choose an answer.')
            page.get_by_text("Kvůli sebevraždě jedné z").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q11: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q11: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q11: Press [next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q12: Choose an answer.')
            page.get_by_text("Hradčanský morový monument").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q12: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH FROM MAP -Q12: Press [next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH FROM MAP: Finish and leave a review by clicking [REVIEW].')
            page.get_by_text("REVIEW", exact=True).click()
            logging.debug('PLAYTHROUGH FROM MAP: Fill review description form.')
            page.get_by_role("textbox", name="Review description").fill(self.review) # to find it quicker in the database when cleaning up
            logging.debug('PLAYTHROUGH FROM MAP: Select positive aspects form.')
            page.get_by_role("textbox", name="Positive aspects").click()
            logging.debug('PLAYTHROUGH FROM MAP: Fill positive aspects form.')
            page.get_by_role("textbox", name="Positive aspects").fill("good")
            logging.debug('PLAYTHROUGH FROM MAP: Select negative aspects form.')
            page.get_by_role("textbox", name="Negative aspects").click()
            logging.debug('PLAYTHROUGH FROM MAP: Fill negative aspects form.')
            page.get_by_role("textbox", name="Negative aspects").fill("bad")
            logging.debug('PLAYTHROUGH FROM MAP: Leave star review 1.')
            page.locator("div").filter(has_text=re.compile(r"^Difficultystarstarstarstarstar$")).locator("mat-icon").first.click()
            logging.debug('PLAYTHROUGH FROM MAP: Leave star review 2.')
            page.locator("div").filter(has_text=re.compile(r"^Attractionstarstarstarstarstar$")).locator("mat-icon").nth(1).click()
            logging.debug('PLAYTHROUGH FROM MAP: Leave star review 3.')
            page.locator("div").filter(has_text=re.compile(r"^Relevancystarstarstarstarstar$")).locator("mat-icon").nth(2).click()
            logging.debug('PLAYTHROUGH FROM MAP: Leave star review 4.')
            page.locator("div").filter(has_text=re.compile(r"^Overviewstarstarstarstarstar$")).locator("mat-icon").nth(3).click()
            logging.debug('PLAYTHROUGH FROM MAP: Finish review by clicking [Apply].')
            page.get_by_role("button", name="Apply").click()
            logging.debug('PLAYTHROUGH FROM MAP: Finish scenario by clicking [OK]')
            page.get_by_role("button", name="OK").click()

            logging.info('PLAYTHROUGH FROM MAP PASSED!')

        except Exception as E:
            logging.error(E)
            pytest.fail(pytrace=False)
               
        
    def playthroughByArea(self, page: Page) -> None:
        '''Plays a scenario from selection by area.'''

        try: 
            nomadLogin(page)
            logging.debug('PLAYTHROUGH BY AREA : Switch to selection by area.')
            page.locator("#mat-radio-3 > .mat-radio-label > .mat-radio-container > .mat-radio-outer-circle").click()
            logging.debug('PLAYTHROUGH BY AREA: Click arrow in the state selection form.')
            page.locator("#mat-select-1 div").nth(2).click()
            logging.debug('PLAYTHROUGH BY AREA: Select Vietnam.')
            page.get_by_text("Vietnam").click()
            logging.debug('PLAYTHROUGH BY AREA: Choose scenario by clicking [choose].')
            page.get_by_role("button", name="Choose").click()
            logging.debug('PLAYTHROUGH BY AREA: After into press [Next] button.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q1: Choose an answer.')
            page.get_by_text("1454").click()
            logging.debug('PLAYTHROUGH BY AREA -Q1: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q1: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q1: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q2: Choose an answer.')
            page.get_by_text("Ho Chi Minh").click()
            logging.debug('PLAYTHROUGH BY AREA -Q2: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q2: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q2: Press [Next] button 1.')
            page.get_by_text("Next", exact=True).click()
            logging.debug('PLAYTHROUGH BY AREA -Q3: Choose an answer.')
            page.get_by_text("Modern dance performances").click()
            logging.debug('PLAYTHROUGH BY AREA -Q3: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q3: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q3: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q4: Choose an answer.')
            page.get_by_text("A floating stage in the Thu B").click()
            logging.debug('PLAYTHROUGH BY AREA -Q4: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q4: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q4: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q4: Check answer history.')
            page.locator("div").filter(has_text=re.compile(r"^menu$")).locator("#detailsBtn").click()
            logging.debug('PLAYTHROUGH BY AREA: Q4: Check own answer.')
            page.get_by_text("search").first.click()
            logging.debug('PLAYTHROUGH BY AREA -Q4: Go back from answer history by pressing [Back].')
            page.get_by_text("Back").click()
            logging.debug('PLAYTHROUGH BY AREA -Q4: Press [Next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q5: Choose an answer.')
            page.get_by_text("Bún Bò Huế").click()
            logging.debug('PLAYTHROUGH BY AREA -Q5: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q5: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q5: Press [Next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q6: Choose an answer.')
            page.get_by_text("20 years").click()
            logging.debug('PLAYTHROUGH BY AREA -Q6: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q6: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q6: Press [Next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q7: Choose an answer.')
            page.get_by_text("15th century").click()
            logging.debug('PLAYTHROUGH BY AREA -Q7: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q7: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q7: Press [Next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q8: Choose an answer.')
            page.get_by_text("Namazu").click()
            logging.debug('PLAYTHROUGH BY AREA -Q8: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q8: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q8: Press [Next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q9: Choose an answer.')
            page.get_by_text("Everything mentioned and more").click()
            logging.debug('PLAYTHROUGH BY AREA -Q9: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q9: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q9: Press [Next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q10: Choose an answer.')
            page.get_by_text("14th day of every lunar month").click()
            logging.debug('PLAYTHROUGH BY AREA -Q10: Check explanation.')
            page.get_by_text("Explanation").click()
            logging.debug('PLAYTHROUGH BY AREA -Q10: Press [Next] button 1.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA -Q10: Press [Next] button 2.')
            page.get_by_text("Next").click()
            logging.debug('PLAYTHROUGH BY AREA: Finish by pressing [THE END]')
            page.get_by_text("THE END").click()

        except Exception as E:
            logging.error(E)
            pytest.fail(pytrace=False)