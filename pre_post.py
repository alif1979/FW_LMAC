
from general import *
from collections import OrderedDict
# ----------------------------------------------------------------------------------------
class PrePost():
	"""Pre-Post configuration comparision"""
	startchar = RUN_CONF_START_CHAR
	endchar = RUN_CONF_END_CHAR

	def __init__(self, configdeltadict, load, runningconfig=None, runningfile=None):
		if runningfile is not None:
			with open(runningfile, 'r') as f:
				runningfilestr = f.read()
			s = runningfilestr.find(self.startchar)
			e = runningfilestr.find(self.endchar)
			runningconfig = runningfilestr[s:e]			
		self.runningconfig = runningconfig
		self.postconfig = runningconfig
		self.load = load
		self.configdeltadict = configdeltadict
		############################################
		self.match_sequence

	@property
	def match_sequence(self):
		"""sequences of action"""
		self.remove_rule_deletion
		self.insert_rule_addition
		self.update_object_group_modification
		#.. to be add more, when need...#

	def getnextremarkpositionfromrunningconfig(self, line):
		"""Next Remark Position in running config starting from line"""
		s = self.runningconfig.find(line)
		s = self.runningconfig.find("remark", s+75)		## Approximation
		s = self.runningconfig.rfind("\n", s-50, s)		## Approximation
		return s

	def segregation_of_line_numbers(self):
		"""Segregate line numbers into various dictionary for further use"""
		newdeltalineslist, newdeltalinesdesclist = [], []
		for line, customer, rw in self.configdeltadict.dic.get(ADD_REQUEST_BANNER):
			l = line.split()
			newdeltalineslist.append(int(l[3]))
			newdeltalinesdesclist.append(l[1])
		self.deltalinelist = sorted(newdeltalineslist)
		return get_range_of_numbers(newdeltalineslist, newdeltalinesdesclist)

	def position_vs_linenumber_dict(self, newdeltalinesrange, descdic):
		"""--> dict:: linenumber:pos in running config"""
		dic = {}
		for linenumber, numberoflines in newdeltalinesrange.items():
			remark = self.load['acldict'][descdic[linenumber]][str(linenumber-1)]['remark']
			for l in self.load.file_list['run_list']:
				if found(l, "access-list "+descdic[linenumber]+" remark ") and found(l, remark):
					line = l
					break
			pos = self.getnextremarkpositionfromrunningconfig(line)
			dic[pos] = linenumber
		return dic

	@property
	def insert_rule_addition(self):
		"""ADD Request - ACL Rule"""
		if self.configdeltadict.dic.get(ADD_REQUEST_BANNER):
			newdeltalinesrange, descdic, listdic = self.segregation_of_line_numbers()
			# blanklinesdic = self.linenumber_vs_position_dict(newdeltalinesrange, descdic)
			blanklinesdic = self.position_vs_linenumber_dict(newdeltalinesrange, descdic)
			for linenumber in reversed(sorted(blanklinesdic.keys())):
				for eachnumber in reversed(listdic[blanklinesdic[linenumber]]):
					for line, customer, rw in self.configdeltadict.dic.get(ADD_REQUEST_BANNER):
						if descdic[eachnumber] + " line "+str(eachnumber)+" " in line:
							lwl = line_without_linenumber(line)
							self.runningconfig = edit_str(self.runningconfig, linenumber, "\n"+(" "*len(lwl)))
							self.postconfig = edit_str(self.postconfig, linenumber, "\n"+lwl)

	@property
	def remove_rule_deletion(self):
		"""DEL Request - ACL Rule"""
		if self.configdeltadict.dic.get(DEL_REQUEST_BANNER):
			for line, customer, rw in self.configdeltadict.dic.get(DEL_REQUEST_BANNER):
				line = line[3:]
				self.postconfig = self.postconfig.replace(line.rstrip(), " "*len(line))

	@property
	def update_object_group_modification(self):
		"""ADD/DEL Request - Object-Group change"""
		if self.configdeltadict.dic.get(OBJ_GRP_CHG_BANNER):
			for lines_tuple in set(self.configdeltadict.dic.get(OBJ_GRP_CHG_BANNER)):
				for i, line in enumerate(lines_tuple[0].split("\n")):
					nonnegatedline = line.strip()[3:]
					if i == 0:
						# delete full object group
						if line[:3] == "no ":
							gs = self.postconfig.find(nonnegatedline)
							ge = self.postconfig.find("\nobject-group ", gs)
							count = self.postconfig[gs:ge].count("\n")
							self.postconfig = self.postconfig.replace(self.postconfig[gs:ge], "\n"*count)
							continue
						else:
							gs = self.postconfig.find(line)
							ge = self.postconfig.find("\nobject-group ", gs)
							if gs > -1: continue # for member update
							#####new group add#####
							# find similar matching group and its ending position (sep)
							desc = lines_tuple[2]
							newname, newcordinate = last_group_ordinates(desc, self.postconfig)
							# insert
							line = " ".join(line.split()[:2])+newname
							self.postconfig = edit_str(self.postconfig, newcordinate, line)
							gs = self.postconfig.find(line)
							ge = self.postconfig.find("\nobject-group ", gs)
							newgrpst = self.postconfig[ge:ge+70]			## approximation
							self.runningconfig = edit_str(self.runningconfig, newgrpst, "\n")
					else:
						postconfig1 = self.postconfig[:gs]
						postconfig2 = self.postconfig[gs:ge]
						postconfig3 = self.postconfig[ge:]
						# delete old member from post config
						if postconfig2.find(nonnegatedline) > -1:
							postconfig2 = postconfig2.replace(nonnegatedline, "")
						# add new member in post config
						else:
							if line.strip().startswith("!"): continue
							preconfig1 = self.runningconfig[:gs]
							preconfig2 = self.runningconfig[gs:ge]
							preconfig3 = self.runningconfig[ge:]
							preconfig2 += "\n"
							postconfig2 += "\n" + line
							self.runningconfig = preconfig1 + preconfig2 + preconfig3
						self.postconfig = postconfig1 + postconfig2 + postconfig3


# ----------------------------------------------------------------------------------------

def last_group_ordinates(desc, postconfig):
	"""-->new group name, string co-ordinate from where it should insert"""
	grpdic = similargroups(desc, postconfig)
	n = 0
	lastcoo = None
	for k, v in grpdic.items():
		# print(">>k>", k)
		# print(">>v>", k)
		s = k.split(desc)[-1].split("-")[-1]
		if s.isdigit():
			s = int(s)
			if n > s: continue
			n = s
			lastcoo = v
		elif lastcoo is None:
			lastcoo = v
	return (desc+"-"+str(n+1), lastcoo[-1])

def similargroups(desc, postconfig):
	"""find similar matching group and its ending position (sep)"""
	lstofmatchinggrpnames = {}
	fromline = 0
	while True:
		fromlinegp = postconfig.find("\nobject-group ", fromline)
		if fromlinegp == -1: break
		fromline = postconfig.find(desc, fromlinegp)
		if fromline == -1: 
			fromline -= 25
			break
		if fromline < fromlinegp + 25:
			nxtenter = postconfig.find("\n", fromline)
			existingdesc = postconfig[fromline:nxtenter]
			nextgrp = postconfig.find("\nobject-group ", fromline)
			lstofmatchinggrpnames.update({existingdesc:(fromline, nextgrp)})
			fromline = nxtenter
		else:
			fromline -= 25
	return lstofmatchinggrpnames

def line_without_linenumber(line):
	"""--> remove line number from acl line"""
	l = line.split()
	return " ".join(l[:2]) + " " + " ".join(l[4:])

def edit_str(string, where, what):
	"""insert 'what' into 'string' at 'where' index"""
	string1 = string[:where]
	string3 = string[where:]
	return string1 + what + string3

# ----------------------------------------------------------------------------------------
