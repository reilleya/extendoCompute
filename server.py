import sys, os, threading, time, threadManager
from multiprocessing.connection import Listener, Client

bindIP = "192.168.3.162"

def controllerClientHandler(conn, addr):
	global exiting
	while not exiting:
		req = conn.recv()
		if req[0] == "stop":
			manager.logEvent("[Controller] Shutting server down now!")
			exiting = True
		if req[0] == "info":
			cl = []
			for k,c in manager.activeThreads.items():
				cl.append(c.generateStatusString())
			conn.send([cl, manager.log])
		if req[0] == "program":
			manager.logEvent("[Controller] Sent new program "+req[1]+" from "+addr+", distributing...")
			manager.distribNewProgram(req[1], req[2])
		if req[0] == "run":
			manager.logEvent("[Controller] Controller ordered program to run")
			manager.run()
		if req[0] == "close":
			break
		if req[0] == "disc":
			if req[1] in manager.activeThreads: #Move this logic into the function itself?
				manager.endThread(req[1])
				conn.send(req[1])
			else:
				manager.logEvent("[Controller] Attempted to end non-existent connection #"+str(req[1]))
				conn.send(-1)
		if req[0] == "results":
			conn.send(manager.results)
		if req[0] == "iterations":
			manager.setIterations(req[1])
		if req[0] == "saveresults":
			manager.saveResults(req[1])
		if req[0] == "batchsize":
			manager.setBatchSize(req[1])
			
	manager.logEvent("[Controller] Closed controller connection with "+addr)
	conn.send("exit")
	conn.close()

def controllerListener():
	while not exiting: 
		conn = listener.accept()
		if not exiting:
			threading.Thread(target=controllerClientHandler, args=(conn,listener.last_accepted[0],)).start()
			manager.logEvent("[Controller] Accepted a controller connection from "+listener.last_accepted[0])

exiting = False

listener = Listener((bindIP, 7777), authkey="password")
threading.Thread(target=controllerListener).start()

manager = threadManager.threadManager()

while not exiting:
	buff = ""
	buff += ("="*40)+"extendoCompute"+("="*40)+"\n"
	buff +=  ("="*94)+"\n"
	buff +=  "Recent Events:\n"
	events = manager.log[-10:]
	if events!=None:
		events.reverse()
		while len(events)<10:
			events.append("-")
		for event in events:
			buff += "\t"+event+"\n"
	buff += ("-"*94)+"\n"
	buff += str(len(manager.activeThreads))+" active connection"+("s"*(len(manager.activeThreads)!=1))+(":"*(len(manager.activeThreads)!=0))+"\n"
	for id,ct in manager.activeThreads.items():
		buff += "\t"+ct.generateStatusString()+"\n"
	buff += ("="*94)+"\n"
	buff += ("="*94)+"\n"
	os.system("cls")
	print buff
	time.sleep(0.1)

print
print "Shutting down..."
print "Ordering thread manager to close..."
manager.exit()
print "Done."
print "Closing controller listener..."
conn = Client((bindIP,7777), authkey="password")
print "Done."
print "Exiting..."
