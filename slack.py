import sublime, sublime_plugin
import functools
import json
exec_mod = __import__("exec")

plugin_name = 'Slack'
base_url = 'https://slack.com/api/{method}?token={token}'
url_param = '&{key}={value}'
message = '[{user}]\n\t{text}\n\n'

class SlackCommand(exec_mod.ExecCommand):
	def run(self, method = 'auth.test', **kwargs):
		if not hasattr(self, 'settings'):
			self.settings = sublime.load_settings(plugin_name + '.sublime-settings')
		if not hasattr(self, 'preferences'):
			self.preferences = sublime.load_settings("Preferences.sublime-settings")
		self.token = self.settings.get('token', None)
		self.http_proxy = self.settings.get('http_proxy', None)
		self.show_panel_on_build = self.settings.get('show_panel_on_build', False)
		self.show_panel_on_build_pref = self.preferences.get("show_panel_on_build", True)

		self.on_http_result = self.http_result
		self.on_http_finish = self.http_finish

		if method == 'users.list':
			self.on_http_result = self.get_members
		elif method == 'channels.list':
			self.on_http_result = self.select_channel
		elif method == 'channels.history':
			self.on_http_result = self.open_channel

		self.http_request(method, **kwargs)

	def http_request(self, method, **kwargs):
		url = base_url.format(method=method, token=self.token)
		for key in kwargs:
			url += url_param.format(key=key, value=kwargs[key])

		#url += '&pretty=1'
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
		try:
			self.result = json.loads(data.decode('utf-8'))
		except ValueError:
			print "Error json load data"
		self.isOk = self.result["ok"]
		self.error = self.result.get('error')

	def http_finish(self, proc):
		if self.isOk:
			sublime.status_message("Slack request success")
		else:
			sublime.status_message("Slack request error: " + self.error)

	def on_data(self, proc, data):
		super(SlackCommand, self).on_data(proc, data)
		sublime.set_timeout(functools.partial(self.on_http_result, proc, data), 0)

	def on_finished(self, proc):
		super(SlackCommand, self).on_finished(proc)
		sublime.set_timeout(functools.partial(self.on_http_finish, proc), 0)

	def get_members(self, proc, data):
		self.http_result(proc, data)
		members = self.result["members"]
		self.users = {}
		for member in members:
			self.users[member.get('id')] = member.get('name')

	def select_channel(self, proc, data):
		self.http_result(proc, data)
		self.channels = self.result["channels"]
		menu_items = ['#' + channel.get('name') for channel in self.channels]
		def on_done(index):
			if index == -1:
				return
			self.open_channel_name = '#' + self.channels[index].get('name')
			self.window.run_command("slack", {"method": "channels.history", "channel": self.channels[index].get('id')})
		self.window.show_quick_panel(menu_items, on_done)

	def open_channel(self, proc, data):
		self.http_result(proc, data)
		print 'open_channel'
		for view in self.window.views():
			if view.name() is None:
				continue
			if view.name() == self.open_channel_name:
				self.window.focus_view(view)
				return

		scratch = self.window.new_file()
		scratch.set_scratch(True)
		scratch.set_name(self.open_channel_name)

		messages = self.result["messages"]
		content = ""
		for m in reversed(messages):
			text = m.get("text")
			if text is None:
				continue
			user_id = m.get("user")
			user_name = self.users[user_id]
			content += message.format(user=user_name, text=text)

		scratch.run_command("slack_dummy", {"content": content})


class SlackDummyCommand(sublime_plugin.TextCommand):
	def run(self, edit, content):
		self.view.insert(edit, 0, content)
