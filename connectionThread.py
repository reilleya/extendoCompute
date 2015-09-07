import sys, os, threading, time
from multiprocessing.connection import Listener

class connectionThread():
	def __init__(self, threadMan, ID, connection, tasks=[]):
		self.threadMan = threadMan
		self.address = self.threadMan.listener.last_accepted
		self.threadID = ID
		self.programName = None
		self.program = ""
		self.state = "idle"
		self.ctask = 0
		self.batchnum = -1
		self.tasks = tasks
		self.results = []
		self.conn = connection
		self.exiting = False
		self.handshake()
		self.listenThread = threading.Thread(target = self.handleClient, args=())
		self.listenThread.start()
		self.updateThread = threading.Thread(target = self.update, args=())
		self.updateThread.start()
		self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Thread started")
	
	def reconnect(self, newConnection):
		self.conn = newConnection
		self.handshake()
		self.state = "idle"
		
	def handshake(self):
		packet = {}
		packet["threadID"] = self.threadID
		packet["progName"] = self.programName
		packet["prog"] = self.program
		packet["tasks"] = self.tasks
		self.conn.send(packet)
	
	def handleClient(self):
		while not self.exiting:
			try:
				d = self.conn.recv()
			except:
				if not self.exiting:
					if self.state != "connerror":
						self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Connection receive error!")
						self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Waiting "+str(self.threadMan.config.timeout)+" seconds before closing")
						#self.threadMan.reportDisconnect(self.threadID)
						self.state = "connerror"
						self.disconnectTime = time.time()
				
			if d[0] == "close":
				self.exit()
			
			if d[0] == "state":
				self.state = d[1]
				self.ctask = d[2]
				
			if d[0] == "results":
				self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Received results from "+str(len(d[1]))+" tasks from client")
				self.results+=d[1]
				self.threadMan.recvRes += len(d[1])
				if len(self.results) == len(self.tasks):
					self.threadMan.reportResults(self.results, self.threadID)
					self.results = []
			
		self.conn.close()
				
	def update(self):
		while not self.exiting:
			if self.state == "connerror":
				if time.time() - self.disconnectTime > self.threadMan.config.timeout:
					self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Unable to regain connection. Closing.")
					self.exiting = True
					self.threadMan.deleteThread(self.threadID)
				
	def generateStatusString(self):
		ss = "#"+str(self.threadID)+": Addr="+self.address[0]+", Prog="+str(self.programName)+","
		if self.state == "idle":
			ss += " Idle"
		elif self.state == "running":
			ss += " Running, task " + str(self.ctask) + " of " + str(len(self.tasks))
		elif self.state == "done":
			ss += "Done"
		elif self.state == "connerror":
			ss += "Connection problem, waiting "+str(self.threadMan.config.timeout-(time.time()-self.disconnectTime))+" more seconds before disconnecting"
		elif self.state == "paused":
			ss += "Paused"
		return ss
	
	def exit(self):
		self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Closing")
		self.exiting = True
		self.conn.send(["exit", "server ordered it"])
		time.sleep(0.5) #Fix the problems with clients trying to reconnect?
		self.conn.close()
		self.threadMan.deleteThread(self.threadID)
		
	def newProgram(self, name, prog):
		self.programName = name
		self.program = prog
		self.conn.send(["program", name, prog])
		
	def run(self):
		if self.programName != None:
			self.conn.send(["run"])
			self.state = "running" #ugly hack to make sure we don't get too many tasks at once
			self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Program started")
		else:
			self.threadMan.logEvent("[Connection"+str(self.threadID)+"] No program to start")
			
	def assignTasks(self, batchnum, tasks):
		self.batchnum = batchnum
		self.tasks = tasks
		self.conn.send(["tasks", tasks, "r"])
	
	def addTasks(self, tasks):
		self.tasks += tasks
		self.conn.send(["tasks", tasks, "a"])
		
	def pause(self):
		self.conn.send(["pause"])
		self.state = "paused"
		
	def resume(self):
		self.conn.send(["resume"])
		self.state = "running"
		
	def cancel(self):
		self.conn.send(["cancel"])
		self.state = "idle"