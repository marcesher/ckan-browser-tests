import os
import ConfigParser
import logging
import httplib
import base64

from datetime import datetime
from selenium import webdriver

from pages.base import Base
from pages.home import Home
from pages.navigation import Navigation
from pages.datasets import Datasets
from pages.organizations import Organizations
from pages.groups import Groups
from pages.utils import Utils
from pages.screenshot import Screenshot


try:
    import json
except ImportError:
    import simplejson as json


def before_all(context):
    fast_fail = os.getenv('FAST_FAIL', False)

    setup_config(context)
    setup_logger(context)

    if(fast_fail):
        connection = httplib.HTTPConnection("fake.ghe.domain",
                                            timeout=10)
        connection.request("GET", "/")
        page_response = connection.getresponse()

        if page_response.status != 200:
            eMessage = str(page_response.status) + " " + page_response.reason
            raise Exception(eMessage)

    if context.browser == 'Sauce':
        context.logger.info("Using Sauce Labs")
        desired_capabilities = {
            'name': os.getenv('SELENIUM_NAME',
                              'CKAN browser tests') + str(datetime.now()),
            'platform': os.getenv('SELENIUM_PLATFORM', 'WINDOWS 7'),
            'browserName': os.getenv('SELENIUM_BROWSER', 'chrome'),
            'version': int(os.getenv('SELENIUM_VERSION', 33)),
            'max-duration': 7200,
            'record-video': os.getenv('SELENIUM_VIDEO', True),
            'video-upload-on-pass': os.getenv('SELENIUM_VIDEO_UPLOAD_ON_PASS',
                                              True),
            'record-screenshots': os.getenv('SELENIUM_SCREENSHOTS', False),
            'command-timeout': int(os.getenv('SELENIUM_CMD_TIMEOUT', 30)),
            'idle-timeout': int(os.getenv('SELENIUM_IDLE_TIMEOUT', 10)),
            'tunnel-identifier': os.getenv('SELENIUM_TUNNEL'),
            'selenium-version': os.getenv('SELENIUM_LIB', '2.45.0'),
            'screen-resolution': os.getenv('SELENIUM_RESOLUTION', '1024x768')
        }

        context.logger.info("Running Sauce with capabilities: %s" %
                            desired_capabilities)

        sauce_config = {"username": os.getenv('SAUCE_USER'),
                        "access-key": os.getenv("SAUCE_KEY")}
        context.sauce_config = sauce_config

        driver = webdriver.Remote(
            desired_capabilities=desired_capabilities,
            command_executor="http://%s:%s@ondemand.saucelabs.com:80/wd/hub" %
            (sauce_config['username'], sauce_config['access-key'])
        )

    else:
        driver = webdriver.Chrome(context.chromedriver_path)

    context.base = Base(context.logger, context.directory,
                        context.base_url, driver, 10, context.delay_secs)
    context.home = Home(context.logger, context.directory,
                        context.base_url, driver, 10, context.delay_secs)
    context.navigation = Navigation(context.logger, context.directory,
                                    context.base_url,
                                    driver, 10, context.delay_secs)
    context.datasets = Datasets(context.logger, context.directory,
                                context.base_url,
                                driver, 10, context.delay_secs)
    context.organizations = Organizations(context.logger, context.directory,
                                          context.base_url,
                                          driver, 10, context.delay_secs)
    context.groups = Groups(context.logger, context.directory,
                            context.base_url,
                            driver, 10, context.delay_secs)
    context.screenshot = Screenshot(context.base, context.take_screenshots)

    context.utils = Utils(context.base)


def before_feature(context, feature):
    context.logger.info('STARTING FEATURE %s' % feature)
    if context.browser == "Sauce":
        context.logger.info("Link to job: https://saucelabs.com/jobs/%s" %
                            context.base.driver.session_id)
        context.logger.info("SauceOnDemandSessionID=%s job-name=%s" %
                            (context.base.driver.session_id, feature.name))


def before_scenario(context, scenario):
    # Ensure each scenario starts with a full browser window.
    context.base.driver.maximize_window()
    context.logger.info('starting scenario %s with row %s' %
                        (scenario, scenario._row))
    context.logger.info('starting feature %s, scenario %s, with row %s' %
                        (scenario.feature.name, scenario.name, scenario._row))


def after_scenario(context, scenario):
    context.logger.info('Finished scenario %s with row %s' %
                        (scenario, scenario._row))


def after_feature(context, feature):
    context.logger.info("Total time spent sleeping is %s" %
                        context.base.utils.time_spent_sleeping)


def after_all(context):
    context.base.close_browser()
    if context.browser == 'Sauce':
        base64string = base64.encodestring('%s:%s' %
                                           (context.sauce_config['username'],
                                            context.sauce_config['access-key']
                                            ))[:-1]

        body_content = json.dumps({"passed": not context.failed})
        context.logger.info("Updating sauce job with %s" % body_content)
        
        # If a proxy is present then use it
        # Otherwise connect directly to saucelabs
        http_proxy = os.getenv('http_proxy', None)
        if http_proxy:
            if http_proxy.startswith("http://"):
                http_proxy = http_proxy[7:]
            connection = httplib.HTTPConnection(http_proxy)
        else:
            connection = httplib.HTTPConnection("saucelabs.com")

        connection.request('PUT', 'https://saucelabs.com/rest/v1/%s/jobs/%s' %
                           (context.sauce_config['username'],
                            context.base.driver.session_id),
                           body_content,
                           headers={"Authorization": "Basic %s" %
                                    base64string})

        result = connection.getresponse()
        context.logger.info(result.read())
        context.logger.info("Sauce update status: %s" % result.status)


def setup_logger(context):
    # create logger
    logger = logging.getLogger('ckan_browser_tests: ')
    logger.setLevel(context.log_level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        '[%(name)s] %(asctime)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    context.logger = logger

    context.logger.info('TEST ENVIRONMENT = %s' % context.base_url)


def setup_config(context):
    config = ConfigParser.ConfigParser()
    config.readfp(open('features/environment.cfg'))

    if config.has_option('logging', 'log_level'):
        context.log_level = int(config.get('logging', 'log_level'))
    else:
        context.log_level = logging.DEBUG

    if config.has_option('general', 'testing_output'):
        context.directory = config.get('general', 'testing_output')
    else:
        context.directory = 'test-results'

    if not os.path.exists(context.directory):
        os.makedirs(context.directory)

    if config.has_option('browser_testing', 'delay'):
        context.delay_secs = config.getint('browser_testing', 'delay')
    else:
        context.delay_secs = 5

    if config.has_option('browser_testing', 'base_url'):
        context.base_url = config.get('browser_testing', 'base_url')
    else:
        context.base_url = 'http://localhost'

    if config.has_option('browser_testing', 'browser'):
        context.browser = config.get('browser_testing', 'browser')
    else:
        context.browser = 'Chrome'

    if config.has_option('chrome_driver', 'chromedriver_path'):
        context.chromedriver_path = config.get('chrome_driver',
                                               'chromedriver_path')
    else:
        context.chromedriver_path = ''

    if config.has_option('browser_testing', 'take_screenshots'):
        context.take_screenshots = config.getboolean('browser_testing',
                                                     'take_screenshots')
    else:
        context.take_screenshots = False
