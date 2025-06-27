# server.py

import json
import os

import tornado.web
import tornado.template
import tornado.ioloop

import project
import auth


class homepage(tornado.web.RequestHandler):
    """This will eventually serve the tracker homepage"""

    def get(self, x='testing.'):
        self.write(f'Hello World, {x}')


class start_item(tornado.web.RequestHandler):
    """API endpoint for requesting an item"""

    def get(self, project):
        username = self.get_argument('username')

        try:
            item = projects[project].getitem(username, self.request.remote_ip)  # ← call matches leaderboard.getitem
            if item == 'NoItemsLeft':
                self.set_status(404)
            self.write(item)
        except KeyError:
            self.set_status(404)
            self.write('InvalidProject')


class heartbeat(tornado.web.RequestHandler):
    """API endpoint for heartbeat"""

    def get(self, project):
        id = self.get_argument('id')

        try:
            heartbeat_stat = projects[project].heartbeat(id, self.request.remote_ip)
            if heartbeat_stat in ['IpDoesNotMatch', 'InvalidID']:
                self.set_status(403)
            self.write(str(heartbeat_stat))
        except KeyError:
            self.set_status(404)
            self.write('InvalidProject')


class finish_item(tornado.web.RequestHandler):
    """API endpoint for finishing an item"""

    def get(self, project):
        id = self.get_argument('id')
        size = int(self.get_argument('size'))  # ← renamed from itemsize to size

        try:
            done_stat = projects[project].finishitem(id, size, self.request.remote_ip)  # ← modified call
            if done_stat in ['IpDoesNotMatch', 'InvalidID']:
                self.set_status(403)
            self.write(str(done_stat))
        except KeyError:
            self.set_status(404)
            self.write('InvalidProject')


class get_leaderboard(tornado.web.RequestHandler):
    """API endpoint for getting the leaderboard"""

    def get(self, project):
        try:
            self.write(projects[project].get_leaderboard())
        except KeyError:
            self.set_status(404)
            self.write('InvalidProject')


class get_user_stats(tornado.web.RequestHandler):  # ← added
    """API endpoint for per-user stats lookup"""

    def get(self, project):
        username = self.get_argument('username')
        try:
            resp = projects[project].get_user_stats(username)
            self.write(resp)
        except KeyError:
            self.set_status(404)
            self.write('InvalidProject')


class AdminHandler(tornado.web.RequestHandler):
    """Base class for any admin page except login"""

    def get_current_user(self):
        return self.get_secure_cookie("user")


class admin_login(tornado.web.RequestHandler):
    """Account login function"""

    def get(self):
        msg = self.get_query_argument('msg', default=False)
        self.write(html_loader.load(
            'admin/login.html').generate(msg=msg))

    def post(self):
        username = self.get_body_argument('username')
        password = self.get_body_argument('password')
        if auth.verify(username, password):
            self.set_secure_cookie('user', username)
            self.redirect('/admin')
        else:
            self.redirect("/admin/login?msg=Invalid%20username%20or%20password")


class admin_logout(AdminHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_all_cookies()
        self.redirect("/admin/login?msg=Logout%20success")


class admin(AdminHandler):
    @tornado.web.authenticated
    def get(self):
        self.write(html_loader.load(
            'admin/manage.html').generate(projects=projects))


class manage_project(AdminHandler):
    @tornado.web.authenticated
    def get(self, project):
        try:
            self.write(html_loader.load(
                'admin/project.html').generate(project=projects[project]))
        except KeyError:
            self.set_status(404)
            self.write('InvalidProject')


# Template loader object
html_loader = tornado.template.Loader('templates')

projects = {}
auth = auth.Auth()

for p in os.listdir('projects'):
    if p.endswith('.json') and not p.endswith('leaderboard.json'):
        with open(os.path.join('projects', p), 'r') as jf:
            project_name = json.loads(jf.read())['project-meta']['name']
        projects[project_name] = project.Project(os.path.join('projects', p))


if __name__ == "__main__":
    PORT = 80
    settings = {
        'compiled_template_cache': False,
        'login_url': '/admin/login',
        'cookie_secret': 'CHANGEME',
    }
    app = tornado.web.Application([
        (r'/', homepage),

        # API urls
        (r'/(.*?)/item/get', start_item),
        (r'/(.*?)/item/heartbeat', heartbeat),
        (r'/(.*?)/item/done', finish_item),
        (r'/(.*?)/api/leaderboard', get_leaderboard),
        (r'/(.*?)/api/user_stats', get_user_stats),  # ← new route

        # Admin
        (r'/admin', admin),
        (r'/admin/login', admin_login),
        (r'/admin/logout', admin_logout),
        (r'/admin/project/(.*?)', manage_project),
    ], **settings)

    app.listen(PORT)
    print(f'Listening on {PORT}')
    tornado.ioloop.IOLoop.current().start()
