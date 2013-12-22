# coding=utf8

import sublime
from .Base import Base

class Error(Base):

	points = None
	ts_view = None

	def __init__(self,name,view):
		super(Error, self).__init__(name,view)

	def setup(self,ts_view,files,points):
		self.ts_view = ts_view
		self.window = self.ts_view.window()
		self.files =  files
		self.points = points

	def on_click(self,line):
		if not self.points:
			if self.ts_view: 
				if self.ts_view.window():
					self.ts_view.window().focus_view(self.ts_view)
			return

		if line in self.points:
			(group,index) = self.window.get_view_index(self.ts_view)
			self.window.focus_group(group)
			view = self.window.open_file(self.files[line])
			self.open_view(view,*self.points[line])

		self.ts_view.window().focus_view(self.ts_view)
		

	def open_view(self,view,begin,end):
		if view.is_loading():
			sublime.set_timeout(lambda: self.open_view(view,begin,end), 100)
			return
		else:
			a = view.text_point(*begin)
			b = view.text_point(*end) 
			region = sublime.Region(a,b)
			
			self.ts_view.window().focus_view(view)
			view.show(region)