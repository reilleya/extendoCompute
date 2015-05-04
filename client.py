from multiprocessing.connection import Client
import threading
	
def runProg():
	global state, ctask
	while running:
		if state == "running":
				print "Running task "+str(ctask)+"/"+str(ntasks)
				print "\t Task inputs: "+str(task)
				exec prog
				results.append([task, result])
				ctask+=1
		
			state = "idle"
			print "All done with tasks"
			print "Results: "+str(results)
			conn.send(["results", results])
	
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

threading.Thread(target = runProg).start()

while running:
	try:
		d = conn.recv()

	except:
		if running:
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