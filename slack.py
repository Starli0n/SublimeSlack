import sublime, sublime_plugin
import functools
import json
exec_mod = __import__("exec")

plugin_name = 'Slack'
base_url = 'https://slack.com/api/{method}?token={token}'


class SlackCommand(exec_mod.ExecCommand):
	def run(self):
		s = sublime.load_settings(plugin_name + '.sublime-settings')
		self.token = s.get('token', None)
		self.http_proxy = s.get('http_proxy', None)
		self.show_panel_on_build = s.get('show_panel_on_build', False)
		self.show_panel_on_build_pref = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)

		self.http_request('auth.test')

	def http_request(self, method):
		url = base_url.format(method=method, token=self.token)
		command = ['curl', url]
		command.append('-s')
		if self.http_proxy is not None:
			command.append('-x')
			command.append(self.http_proxy)
		sublime.load_settings("Preferences.sublime-settings").set("show_panel_on_build", self.show_panel_on_build)
		try:
			super(SlackCommand, self).run(cmd = command)
		finally:
			sublime.load_settings("Preferences.sublime-settings").set("show_panel_on_build", self.show_panel_on_build_pref)

	def http_result(self, proc, data):
		result = json.loads(data)
		self.isOk = result["ok"]
		self.error = result.get('error')

	def http_finish(self, proc):
		if self.isOk:
			sublime.status_message("Slack request success")
		else:
			sublime.status_message("Slack request error: " + self.error)

	def on_data(self, proc, data):
		super(SlackCommand, self).on_data(proc, data)
		sublime.set_timeout(functools.partial(self.http_result, proc, data), 0)

	def on_finished(self, proc):
		super(SlackCommand, self).on_finished(proc)
		sublime.set_timeout(functools.partial(self.http_finish, proc), 0)
