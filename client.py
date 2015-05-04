from multiprocessing.connection import Client
import threading
	
ip = raw_input("IP>")
if ip=="":
	ip = "192.168.3.162"
		
running = True
conn = Client((ip,2424), authkey="password")

state = "idle"

progname = ""
prog = ""

ntasks = 0
ctask = 1
tasks = []
cres = None
results = []

def runProg():
	global state, cstask
	while running:
		if state == "running":
			for task in tasks:
				print "Running task "+str(ctask)+"/"+str(ntasks)
				print "\t Task inputs: "+str(task)
				exec prog
				results.append(result)
				tasks.remove(task)
				ctask+=1
			if len(tasks) == 0:
				state = "idle"
				print "All done with tasks"
				print "Results: "+str(results)

threading.Thread(target = runProg).start()

while running:
	try:
		d = conn.recv()

	except:
		print "Connection error! Retrying..." 
		conn = Client((ip,2424), authkey="password")
		print "Connection regained!"
		continue
		
	if d[0] == "exit":
		print "Exiting"
		running = False
		
	if d[0] == "program":
		print "Received a new program ("+d[1]+")"
		progname = d[1]
		prog = d[2]
		
	if d[0] == "tasks":
		print "Received "+str(len(d[1]))+" new tasks, "+("appending to list of tasks"*(d[2]=="a"))+("replacing current list of tasks"*(d[2]=="r"))
		if d[2] == "a":
			tasks+=d[1]
		if d[2] == "r":
			tasks=d[1] #Probably need to alert the other thread about this somehow
		ntasks = len(tasks)
		
	if d[0] == "run":
		print "Setting state to run"
		state = "running"