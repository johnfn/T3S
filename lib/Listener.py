# coding=utf8

import sublime
import sublime_plugin

from .display.Views import VIEWS
from .display.Completion import COMPLETION
from .display.Errors import ERRORS
from .system.Files import FILES
from .system.Liste import LISTE
from .system.Processes import PROCESSES
from .system.Settings import SETTINGS
from .Tss import TSS
from .Utils import debounce, is_ts, is_dts, is_member_completion, get_data, get_file_infos, ST3


# ------------------------------------------- INIT ------------------------------------------ #

def init(view):
	if VIEWS.is_open_view(view.name()): VIEWS.on_view(view)
	if not is_ts(view): return
	if is_dts(view): return
	if get_data(view.file_name()) == None: return

	root = SETTINGS.get_root(view)
	if root == 'no_ts' or root == None: return

	process = PROCESSES.get(root)
	filename = view.file_name()
	if process != None:
		if not process.is_alive():
			args = get_file_infos(view)
			if LISTE.has(filename):
				TSS.update(*args)
			else:
				args = (root,)+args
				FILES.add(root,filename)
				TSS.add(*args)

			VIEWS.update()
			debounce(TSS.errors, 0.3, 'errors' + str(id(TSS)), view.file_name())
	else:
		FILES.add(root,filename)
		if filename != root: FILES.add(root,root)
		TSS.addEventListener('init',root,on_init)
		TSS.addEventListener('kill',root,on_kill)
		TSS.init(root)
		view.settings().set('auto_complete',SETTINGS.get("auto_complete"))
		view.settings().set('extensions',['ts'])

def on_init(process):
	TSS.removeEventListener('init',process.root,on_init)
	FILES.init(process.root)
	ERRORS.init(process.root,process.r_async)
	VIEWS.init()

def on_kill(process):
	TSS.removeEventListener('kill',process.root,on_kill)
	FILES.remove_by(process.root)
	ERRORS.remove(process.root)


# ----------------------------------------- LISTENERS ---------------------------------------- #

class TypescriptEventListener(sublime_plugin.EventListener):

	error_delay = 0.3


	# CLOSE FILE
	def on_close(self,view):
		if VIEWS.is_view(view.name()):
			VIEWS.delete_view(view.name())

		if is_ts(view) and not is_dts(view):
			filename = view.file_name()
			if ST3: TSS.kill(filename)
			else: sublime.set_timeout(lambda:TSS.kill(filename),300)


	# FILE ACTIVATED
	def on_activated(self,view):
		init(view)

		
	# ON CLONED FILE
	def on_clone(self,view):
		init(view)


	# ON SAVE
	def on_post_save(self,view):
		if not is_ts(view):
			return

		args = get_file_infos(view)
		TSS.update(*args)
		VIEWS.update()
		FILES.update(view,True)
		debounce(TSS.errors, self.error_delay, 'errors' + str(id(TSS)), view.file_name())


		if SETTINGS.get('build_on_save'):
			sublime.active_window().run_command('typescript_build',{"characters":False})


	# ON CLICK
	def on_selection_modified(self,view):
		if not is_ts(view):
			if VIEWS.is_open_view(view.name()): VIEWS.on_view(view)
			return

		filename = view.file_name()
		if not LISTE.has(filename) and get_data(filename) != None and not is_dts(view):
			root = SETTINGS.get_root(view)
			if root == None or root == 'no_ts': return
			args = (root,)+get_file_infos(view)
			FILES.add(root,filename)
			TSS.add(*args)

		view.erase_regions('typescript-definition')
		ERRORS.set_status(view)


	# ON VIEW MODIFIED
	def on_modified(self,view):
		if view.is_loading(): return
		if not is_ts(view):
			return

		args = get_file_infos(view)
		TSS.update(*args)
		FILES.update(view)
		VIEWS.update()

		if not SETTINGS.get('error_on_save_only'):
			debounce(TSS.errors, self.error_delay, 'errors' + str(id(TSS)), view.file_name())


	# ON QUERY COMPLETION
	def on_query_completions(self,view,prefix,locations):
		if is_ts(view):
			if COMPLETION.enabled:
				TSS.update(*get_file_infos(view))
				pos = view.sel()[0].begin()
				(line, col) = view.rowcol(pos)
				is_member = str(is_member_completion(view.substr(sublime.Region(view.line(pos-1).a, pos)))).lower()
				TSS.complete(view.file_name(),line,col,is_member)

				COMPLETION.enabled = False
				return (COMPLETION.get_list(), sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)


	# ON QUERY CONTEXT
	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "T3S":
			view = sublime.active_window().active_view()
			return is_ts(view)