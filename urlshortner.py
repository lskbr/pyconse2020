import uuid

from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute

#
# Constants
#

DAYS_TO_LIVE = 2  # Days before the url is deleted from the database
SIZE = 6  # Size of the url shortned

#
#  Jinja Template Setup
#

env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html']))

#
# Database Model for PynamoDB
# Helps with DynamoDB handling
#


class URLModel(Model):
    class Meta:
        table_name = 'urlsTable'
        region = 'eu-west-1'

    short_key = UnicodeAttribute(hash_key=True)
    url = UnicodeAttribute()
    counter = NumberAttribute(default=0)
    ttl = NumberAttribute()


#
# Helper Functions
#

def compute_timestamp() -> int:
    """Computes the timestamp to delete de URL record"""
    return int((datetime.now() + timedelta(days=DAYS_TO_LIVE)).timestamp())


def create_short_id() -> str:
    """Tries to create a unique short prefix. Tries max_tries times."""
    max_tries = 10
    while True:
        candidate = uuid.uuid4().hex[:SIZE]
        if URLModel.count(hash_key=candidate) == 0:
            return candidate
        max_tries += 1
        if max_tries == 0:
            raise Exception("Failed to create a unique shortner")


def get_lambda_path_from_event(event) -> str:
    """Builds the lambda function url based on event data"""
    lambda_path = event["requestContext"]["path"]
    lambda_domain = event["requestContext"]["domainName"]
    return f"https://{lambda_domain}{lambda_path}"


def fix_url(url) -> str:
    url = url[0]  # It is returned as a list, make it a string
    parsed = urlparse(url)
    if not parsed.scheme:
        # The url has no scheme (http or https or other)
        # add http as default to avoid redirecting to the same page
        url = f"http://{url}"
    return url

#
# Forms
#


def show_create_form(event):
    """Returns the form to ask for new URL"""
    template = env.get_template('url_create_form.html')
    return {"statusCode": 200,
            "body": template.render(),
            "headers": {"Content-Type": "text/html"}}


def show_url_created_page(event):
    """Creates a record in the db when the form is posted.
       Returns a result page."""
    body = event.get("body", "")
    fields = parse_qs(body)
    url = fields.get("original_url")
    if not url:
        raise Exception("Original URL is a required field")
    url = fix_url(url)
    short_key = create_short_id()
    lambda_url = get_lambda_path_from_event(event)
    short_url = f"{lambda_url}/{short_key}"
    URLModel(short_key=short_key, url=url, ttl=compute_timestamp()).save()

    template = env.get_template('url_created_page.html')
    return {"statusCode": 200,
            "body": template.render(URL=url, SHORT_URL=short_url),
            "headers": {"Content-Type": "text/html"}}


def create(event, context):
    """Returns a html page.
       Depending on the http method, it can be a form to ask for
       a new url (GET);
       or a page to display the newly created url with
       the short code (POST)."""
    method = event["httpMethod"]

    try:
        if method == "GET":
            return show_create_form(event)
        elif method == "POST":
            return show_url_created_page(event)
        raise Exception(f"Unsupported http method {method}")

    except Exception as e:
        return {"statusCode": 500,
                "body": f"Error: {e}"}


def use(event, context):
    short_key = event["pathParameters"]["short_key"]
    try:
        # Try to find the short key in the database.
        # Query returns an iterator, calls next to get real data.
        udata = URLModel.query(hash_key=short_key).next()

        # Increment the usage counter in the database
        udata.update(actions=[URLModel.counter.set(URLModel.counter + 1)])
        return {"statusCode": 301,
                "headers": {"Location": udata.url}}

    except Exception as e:
        return {"statusCode": 500,
                "body": f"Error: {e}"}
