
from std_vars import *
from os import remove
# ----------------------------------------------------------------------------------------
def text_to_List(fileX):
	'''convert file to list
	--> list
	'''
	try:
		with open(fileX, 'r') as f:
			lines = f.readlines()
		return lines
	except:
		lgmain.save(f"file {fileX} read failed", CRITICAL)
		raise Exception(f"file {fileX} read failed")

def blank_line(line):
	'''check if provided line is blank or not
	--> boolean
	'''
	try: return True if len(line.strip()) == 0 else False
	except Exception: pass

def found(line, searchitem):
	'''Search for item in line and return Boolean result'''
	try:
		return True if line.find(searchitem) > -1 else False
	except:
		return False

def find_multi(s, sub, start=0, count=None, index=True, beginwith=False):
	'''Find multiple items from string
	--> boolean
	'''
	count = len(s) if count is None else count+start
	if isinstance(sub, str):
		i = s.find(sub, start, count) 
		if index:
			if beginwith:
				return i if i == 0 else -1
			else:
				return i
		else:
			if beginwith:
				return True if i == 0 else False
			else:
				return False if i == -1 else True
	elif isinstance(sub, (tuple, list)):
		sl = []
		for x in sub:
			sl.append(find_multi(s, x, start, count, index, beginwith))
		return sl
	else:
		return None

def find_any(s, sub, start=0, count=None, beginwith=False):
	'''Find multiple items from string, Return True if any one available
	--> boolean
	'''
	sl = find_multi(s, sub, start, count, False, beginwith)
	try:
		return True if True in sl else False
	except:
		return sl

def finddualnreplacesingle(line, item=' '):
	'''Finds two subsequent item string from line and replace it with single
	--> str
	'''
	try:
		while line.find(item+item) > -1:
			line = line.replace(item+item, item)
		return line
	except:
		lgmain.save(f"Err! finddualnreplacesingle()", WARN)
		raise Exception

def replace_dual_and_split(line, item=' '):
	'''Finds two subsequent item string from line and replace it with single, &
	splits line with provided item
	--> list
	'''
	line = finddualnreplacesingle(line, item)
	return line.split(item)

def split_multi(line, item=None):       # NIU
	'''Splits line with multiple items, provide item in tuple/list.
	--> list
	'''
	repl = None
	for x in item:
		if repl:
			line = line.replace(x, repl)
		else:
			repl=x
	return line.split(repl)

def hostname_line(line, hostname):
	'''Search hostname in line and returns boolean value
	'''
	try:
		return line.startswith(hostname)
	except:
		lgmain.save(f"Err! hostname_line()", WARN)
		raise Exception


def get_mgmt_ip(spl):
	"""Management ip of device"""
	try:
		for line in spl:
			if line.startswith(" ip address"):
				return line[12:].split()[0]
	except:
		lgmain.save(f"Err! get_mgmt_ip()", WARN)
		raise Exception

# ----------------------------------------------------------------------------------------
def writeTofile(treelistX, output=''):
	'''
	Writes List/text to output file
	---> None

	:param treelistX: data to be written in output text file
	:type str, tuple, list:

	:param output: output text filename
	:type str:

	'''
	if output != '':
		if isinstance(treelistX, (list, tuple)):
			for x in treelistX:
				writeTofile(x, output)
		elif isinstance(treelistX, str):
			with open(output, 'a') as f:
				f.write(treelistX)

def filecopy(source, destination):
	"""Binary File copy"""
	with open(source, 'rb') as fr:
		s = fr.read()
		with open(destination, 'wb') as fw:
			fw.write(s)

# ----------------------------------------------------------------------------------------
def combinations(*i):
	"""combination of items"""
	if len(i) > 2 :
		for a in combinations(*i[:-1]):
			for z in i[-1]:
				c = list(a)
				c.append(z)
				yield tuple(c)
	elif len(i) == 2:
		for x in i[0]:
			for y in i[1]:
				yield (x, y)
	else:
		print("Two or more argument needed.")

# ----------------------------------------------------------------------------------------
def sort_seq_210(x):
	"""sort sequence by index 2-1-0 for three items"""
	return (x[2],x[1],x[0])
def sort_seq_012(x):
	"""sort sequence by index 0-1-2 for three items"""
	return (x[0],x[1],x[2])
# ----------------------------------------------------------------------------------------
def port_alias(port):
	"""--> Port alias value"""
	return WELL_KNOWN_PORTS.get(port, port)


def get_range_of_numbers(listofnumbers, listofaclnames):
	"""List of Numbers - various operations, add to dictionary of range, acl name etc"""
	dic = {}
	namedic = {x:y for x, y in zip(listofnumbers, listofaclnames)}
	listdic = {}
	for i, x in enumerate(sorted(set(listofnumbers))):
		if i == 0:
			k = x
			dic[k] = 1
			listdic[k] =[]
		else:
			if prevx+1 == x:
				dic[k] += 1
			else:
				k = x
				dic[k] = 1
				listdic[k] =[]
		listdic[k].append(x)
		prevx = x	
	return (dic, namedic, listdic)
# ---------------------------------------------------------------------------------------

def popup(*args, **kwargs):
	sg.Popup(*args, **kwargs)
# ---------------------------------------------------------------------------------------

def appp(row, port_line):
	"""Generate and yield -> ports attributes 'APPP' (a row from Excel column)"""
	pls = port_line.split(",")
	pdic = {}
	for ipl in pls:
		pl = ipl.strip().split(" ", 1)
		if pl[0].lower() in PROTOCOLS:
			protocol = pl[0]
		if pl[0][:4] in ICMP:
			ipl = "icmp "+ipl
			pl = ipl.split(" ", 1)
			protocol = pl[0]
		ports = []
		while found(pl[-1], " ,") or found(pl[-1], ", ") or found(pl[-1], ";"):
			pl[-1] = pl[-1].replace(";", ",")
			pl[-1] = pl[-1].replace(" ,", ",")
			pl[-1] = pl[-1].replace(", ", ",")
		ports.extend(pl[-1].split(","))
		protocol = protocol.lower()
		if not pdic.get(protocol): pdic[protocol] = {'action': row.action}
		pdicp = pdic[protocol]
		for port in ports:
			port_type = 'eq_candidate'
			if port in ICMP: port_type = ''
			elif found(port, " ") or found(port, "-"): 
				port_type = 'range_candidate'
				port = port.replace("-", " ")
				port = port.replace("range", "").strip()
			if not pdicp.get(port_type):
				pdicp[port_type] = set()
			port = port_alias(port)
			pdicp[port_type].add(port)
	return pdic
# ---------------------------------------------------------------------------------------

def acl_group_members(int_n):
	"""--> dictionary of acl: range/group of numbers"""
	dic, dicx, dic_key, prev_n = {}, {}, None, -2
	acls = {aclname for ln, aclname in int_n}
	for acl in acls:
		lst = []
		for ln, aclname in int_n:
			if aclname != acl: continue
			lst.append(ln)
		dicx[acl] = sorted(lst)
	for acl in acls:
		for aclname, lns in dicx.items():
			for ln in lns:
				if ln == prev_n + 1:
					dic[aclname][dic_key] = str(ln)
				else:
					if not dic.get(aclname): dic[aclname] = {}
					dic[aclname][str(ln)] = str(ln)
					dic_key = str(ln)
				prev_n = ln  
	return dic
