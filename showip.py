from jinja2 import Environment, FileSystemLoader, select_autoescape


def handler(event, context):
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html']))

    headers = event["headers"]
    country = headers["CloudFront-Viewer-Country"]
    ip = headers["X-Forwarded-For"].split(",")[0]

    template = env.get_template('showip.html')

    return {"statusCode": 200,
            "body": template.render(IP=ip, COUNTRY=country),
            "headers": {"Content-Type": "text/html"}}
