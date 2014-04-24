import sublime, sublime_plugin
exec_mod = __import__("exec")

plugin_name = 'Slack'
base_url = 'https://slack.com/api/{method}?token={token}'


class SlackCommand(exec_mod.ExecCommand):
	def run(self):
		s = sublime.load_settings(plugin_name + '.sublime-settings')
		self.token = s.get('token', None)
		self.http_proxy = s.get('http_proxy', None)

		self.http_request('auth.test')
		sublime.status_message("slack done")

	def http_request(self, method):
		url = base_url.format(method=method, token=self.token)
		command = ['curl', url]
		command.append('-s')
		if self.http_proxy is not None:
			command.append('-x')
			command.append(self.http_proxy)
		#sublime.load_settings("Preferences.sublime-settings").set("show_panel_on_build", True)
		super(SlackCommand, self).run(cmd = command)

	def on_data(self, proc, data):
		super(SlackCommand, self).on_data(proc, data)
		print data
