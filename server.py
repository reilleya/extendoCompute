import sys, os, threading, time, threadManager
from multiprocessing.connection import Listener, Client
import configLoader

config = configLoader.cfgLoader("serverConfig.cfg")

sys.stderr = open('errors.txt','w')

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
			conn.send([cl, manager.log, manager.inputs])
			
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
				manager.logEvent("[Controller] Ending connection #"+str(req[1]))
				manager.endThread(req[1])
				conn.send(req[1])
			else:
				manager.logEvent("[Controller] Attempted to end non-existent connection #"+str(req[1]))
				conn.send(-1)
				
		if req[0] == "results":
			manager.logEvent("[Controller] Sending results to controller")
			conn.send(manager.results)
			
		if req[0] == "iterations":
			manager.logEvent("[Controller] Setting iteration count to "+str(req[1]))
			manager.setIterations(req[1])
			
		if req[0] == "saveresults":
			manager.logEvent("[Controller] Saving results locally as "+str(req[1]))
			manager.saveResults(req[1])
			
		if req[0] == "batchsize":
			manager.logEvent("[Controller] Setting batch size to "+str(req[1]))
			manager.setBatchSize(req[1])
			
		if req[0] == "newInput":
			manager.logEvent("[Controller] Adding a new input called "+req[1]+ " with "+str(len(req[2]))+" different values")
			manager.addInput(req[1], req[2])
			
		if req[0] == "delInput":
			manager.logEvent("[Controller] Deleting input named "+req[1])
			manager.deleteInput(req[1])
			
		if req[0] == "inputs":
			conn.send(manager.inputs)
			
		if req[0] == "genTasks":
			manager.generateTasks()
		
		if req[0] == "genBatches":
			manager.generateBatches()
			
		if req[0] == "batches":
			conn.send(manager.batches)
			
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

listener = Listener((config.bindIP, config.controllerPort), authkey="password")
threading.Thread(target=controllerListener).start()

print "in"
manager = threadManager.threadManager(config)
print "out"

while not exiting:
	buff = ""
	buff += ("="*50)+"extendoCompute"+("="*50)+"\n"
	buff +=  ("="*114)+"\n"
	buff +=  "Recent Events:\n"
	events = manager.log[-10:]
	if events!=None:
		events.reverse()
		while len(events)<10:
			events.append("-")
		for event in events:
			buff += "\t"+event+"\n"
	buff += ("-"*114)+"\n"
	buff += str(len(manager.activeThreads))+" active connection"+("s"*(len(manager.activeThreads)!=1))+(":"*(len(manager.activeThreads)!=0))+"\n"
	for id,ct in manager.activeThreads.items():
		buff += "\t"+ct.generateStatusString()+"\n"
	buff += ("-"*114)+"\n"
	buff += "Program Info:\n"
	buff += "\tName: "+(manager.progName*(manager.progName!=""))+("N/A"*(manager.progName==""))+"\n"
	if manager.running:
		buff += "\tRunning:\n"
		buff += "\tResults: "+str(len(manager.results))+"/"+str(len(manager.tasks))+"\n"
		#buff += "\tBatch States: "+str(manager.batchStates)+"\n"
	else:
		buff += "\tNot running\n"
	buff += ("="*114)+"\n"
	buff += ("="*114)+"\n"
	os.system("cls")
	print buff
	time.sleep(0.1)

print
print "Shutting down..."
print "Ordering thread manager to close..."
manager.exit()
print "Done."
print "Closing controller listener..."
conn = Client((config.bindIP,config.controllerPort), authkey="password")
print "Done."
sys.stderr.close()
sys.stderr = sys.__stderr__
print "Exiting..."
