class cfgLoader(object):
	def __init__(self, filename="config.cfg"):
		self.settings = {}
		f = open(filename, "r")
		contents = f.read()
		f.close()
		lines = contents.split("\n")
		for line in lines:
			if len(line)>3:
				print line
				name = line.split(" ")[0]
				print name
				exec "self.settings['"+name+"']="+line[len(name)+1:]
	
	def __getattribute__(self, key):
		if key in ("settings", "loadSettings"):
			return object.__getattribute__(self, key)
		else:
			if key in self.settings:
				return self.settings[key]
			else:
				raise Exception("Tried to access "+key+", a setting that does not exist!")