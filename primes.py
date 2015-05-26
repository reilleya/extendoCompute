result = True
for test in range(2, int(task["number"]/2)+1):
	if task["number"]%test == 0:
		result = False
		break