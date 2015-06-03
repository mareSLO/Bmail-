#!/usr/bin/env python
import os
import jinja2
import webapp2
from google.appengine.api import users
from models import Bmail
from google.appengine.api import urlfetch
import json


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}

        user = users.get_current_user()
        if user:
            logged_in = True
            logout_url = users.create_logout_url("/")
            params["logged_in"] = logged_in
            params["user"] = user
            params["logout_url"] = logout_url
        else:
            logged_in = False
            login_url = users.create_login_url("/")
            params["logged_in"] = logged_in
            params["user"] = user
            params["login_url"] = login_url

        template = jinja_env.get_template(view_filename)
        self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        current_user = str(users.get_current_user())
        bmail = Bmail.query(Bmail.to == current_user).order(-Bmail.created).fetch()

        params = {"bmail": bmail}

        self.render_template("hello.html", params)

class SendMail(BaseHandler):
    def get(self):
        self.render_template("send_mail.html")


class MailSent(BaseHandler):
    def post(self):
        to = self.request.get("to")
        subject = self.request.get("subject")
        msg = self.request.get("msg")
        from_user = str(users.get_current_user())

        mail = Bmail(to=to, subject=subject, msg=msg, from_user=from_user)
        mail.put()

        self.render_template("mail_sent.html")

class SentHandler(BaseHandler):
    def get(self):
        current_user = str(users.get_current_user())
        bmail = Bmail.query(Bmail.from_user == current_user).order(-Bmail.created).fetch()

        params = {"bmail": bmail}

        self.render_template("sent.html", params)

class MailHandler(BaseHandler):
    def get(self, mail_id):
        mail = Bmail.get_by_id(int(mail_id))

        params = {"mail": mail}

        self.render_template("mail.html", params)

class WeatherHandler(BaseHandler):
    def get(self):
        url = "http://api.openweathermap.org/data/2.5/weather?zip=1351,si&units=metric"

        url_content = urlfetch.fetch(url).content
        weather = json.loads(url_content)

        params = {"weather": weather}

        self.render_template("weather.html", params)


app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/send', SendMail),
    webapp2.Route('/mailsent', MailSent),
    webapp2.Route('/sent', SentHandler),
    webapp2.Route('/mail/<mail_id:\d+>', MailHandler),
    webapp2.Route('/weather', WeatherHandler),
], debug=True)
