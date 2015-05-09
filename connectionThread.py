import sys, os, threading, time
from multiprocessing.connection import Listener

class connectionThread():
	def __init__(self, threadMan, ID, connection):
		self.threadMan = threadMan
		self.address = self.threadMan.listener.last_accepted
		self.threadID = ID
		self.programName = None
		self.state = "idle"
		self.ctask = 0
		self.tasks = []
		self.conn = connection
		self.exiting = False
		self.thread = threading.Thread(target=self.handleClient, args=())
		self.thread.start()
		self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Thread started")
		
	def handleClient(self):
		while not self.exiting:
			try:
				d = self.conn.recv()
			except:
				if not self.exiting:
					self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Connection receive error!")
					self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Closing")
					self.exiting = True
					self.threadMan.deleteThread(self.threadID)
				break
			if d[0] == "close":
				self.exit()
			
			if d[0] == "state":
				self.state = d[1]
				self.ctask = d[2]
				
			if d[0] == "results":
				self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Received results from "+str(len(d[1]))+" tasks from client")
				self.threadMan.reportResults(d[1], self.threadID)
			
		self.conn.close()
				
	def generateStatusString(self):
		ss = "#"+str(self.threadID)+": Addr="+self.address[0]+", Prog="+str(self.programName)+","
		if self.state == "idle":
			ss += " Idle"
		elif self.state == "running":
			ss += " Running, task " + str(self.ctask) + " of " + str(len(self.tasks))
		elif self.state == "done":
			ss += "Done"
		return ss
	
	def exit(self):
		self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Closing")
		self.exiting = True
		self.conn.send(["exit"])
		time.sleep(0.5) #Fix the problems with clients trying to reconnect?
		self.conn.close()
		self.threadMan.deleteThread(self.threadID)
		
	def newProgram(self, name, prog):
		self.programName = name
		self.conn.send(["program", name, prog])
		
	def run(self):
		if self.programName != None:
			self.conn.send(["run"])
			self.state = "running" #ugly hack to make sure we don't get too many tasks at once
			self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Program started")
		else:
			self.threadMan.logEvent("[Connection"+str(self.threadID)+"] No program to start")
			
	def assignTasks(self, tasks):
		self.tasks = tasks
		self.conn.send(["tasks", tasks, "r"])
	
	def addTasks(self, tasks):
		self.tasks += tasks
		self.conn.send(["tasks", tasks, "a"])