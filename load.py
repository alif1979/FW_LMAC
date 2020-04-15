
try:
	from general import *
	from db import XL_READ
	from addressing import Routes
	from acg import ObjDict
	from acl import AclDict
	from common import InitGroups, DictMethods
	# from general import text_to_List, blank_line, hostname_line, get_mgmt_ip
except:
	raise ImportError("Unable to import necessary Modules, Please contact al202t@att.com")

# ----------------------------------------------------------------------------------------
def split_file(file):
	'''reads capture file and keep outputs in dictionary of lists. 
	--> dictionary with items
	'''
	dic = {}
	for cmds in OUTPUT_CMDS:
		for k, v in cmds.items():
			for each_cmd in v:
				dic[each_cmd] = k

	idx_dic, ndic = {}, {}
	test_list = text_to_List(file)
	size = len(test_list)
	for idx, val in enumerate(test_list):
		try:
			if dic[val.split("#")[-1].strip()]:
				idx_dic[idx + 1] = dic[val.split("#")[-1].strip()]
		except:
			pass
	idx_dic[size] = ''
	old_i = 0
	for i, v in idx_dic.items():
		if old_i > 0:
			ndic[old_v] = test_list[old_i:i]
		old_i, old_v = i, v
	ndic[old_v] = test_list[old_i:i]
	return ndic

# ----------------------------------------------------------------------------------------
def int_to_acl(hostname, acg_list=None, acl_file=None):
	'''access list v/s interface entries in dictionary
	--> dict
	'''
	if acl_file != None: acg_list = text_to_List(acl_file)
	acl = {}
	for line in acg_list:
		if blank_line(line): continue
		if hostname_line(line, hostname): continue
		lst = line.split()
		acl[lst[-1]] = lst[1]
	return acl

# ----------------------------------------------------------------------------------------
selSCol = lambda x: x.src_ip if not USE_SOURCE_NAT_IP or x.src_nat in ("N/A", "",) else x.src_nat
selDCol = lambda x: x.dst_ip if not USE_DESTINATION_NAT_IP or x.dst_nat in ("N/A", "",) else x.dst_nat
def get_request_data(req_file):
	"""for provided request file give data frame, for src and dst ip addresss 
	column separate ips using space/enter and put it in list.

	:return: Pandas DF
	:rtype: DataFrame
	"""
	# READ REQUEST EXCEL
	xl = XL_READ(req_file, fields_list=CUSTOM_COLUMN_NAMES_FILTERED, header=0)
	xl.df.src_ip = xl.df.apply(selSCol, axis=1)
	xl.df.dst_ip = xl.df.apply(selDCol, axis=1)
	xl.df.src_ip = xl.df.src_ip.str.replace(" ","\n").str.split("\n")
	xl.df.dst_ip = xl.df.dst_ip.str.replace(" ","\n").str.split("\n")
	return xl.df

def read_xl(req_file):
	"""Read original Excel Request file and convert to required format..
	concerns : Header row on number 9, 
	records will be trunked starting from "特記事項：" value in first column.
	There should be no blank rows in beween header and above last remark row.
	...customer column missing in original request. need to add manually...
	"""
	dic = {}
	xl = XL_READ(req_file, shtName=REQUEST_ORG_SHEET_NAME, header=REQUEST_ORG_SHEET_HEADER_ROW)
	for x, y in zip(xl.df.keys(), CUSTOM_COLUMN_NAMES_ALL): dic[x] = y
	xl.df = xl.df.rename(columns=dic)
	ddsr = xl.df.index[xl.df.req_type.str.contains(ROWS_TOBE_TRIM_FROM_VALUE) == True].tolist()[0]
	for x in xl.df.index: 
		if x >= ddsr: xl.df = xl.df.drop(x)
	return xl

# ----------------------------------------------------------------------------------------
def load_conf_n_request(req_file):
	"""Kick"""
	try:
		lgmain.save(f"Reading Excel Request File {REQUEST_FILE}...", INFO)
		df = get_request_data(req_file)
		lgmain.save(f"...Reading Excel Request File {REQUEST_FILE} complete", INFO)
	except FileNotFoundError as e:
		lgmain.save(f"File Not Found {REQUEST_FILE}", CRITICAL)
		lgmain.save(e, CRITICAL)
		popup('Execution Halted',
		f"File Not Found {REQUEST_FILE}",
		auto_close=True, auto_close_duration=5)
		quit()
	except:
		lgmain.save(f"!!!Reading Excel Request File {REQUEST_FILE} failed!!!", ERR)
	fws = LoadDict(lgmain, confList=df)
	return (df, fws)

# ----------------------------------------------------------------------------------------
class LoadDict(InitGroups, DictMethods):
	"""configurations of firewalls"""
	def __str__(self):
		if len(self.dic.keys()) > 7:
			return f"[O]: Configuration for Devices: {tuple(self.dic.keys())[:7]} ...and more"
		else:
			return f"[O]: Configuration for Devices: {self.dic.keys()}"

	def get_groups(self, confList, object_group_dict):
		"""set configuration load"""
		df = confList
		for x in range(len(df)):
			row = df.iloc[x]
			for fwcol in FW_COL_NAMES:
				fw = row[fwcol]
				if not fw: continue
				##
				fw_file = CAPTURE_FOLDER+"/"+fw+LOG_EXTN
				##
				if not self.dic.get(fw):
					try:
						lgmain.save(f"Reading Capture file: {fw_file}...", INFO)
						splfile = split_file(fw_file)
						lgmain.save(f"...Configuration {fw} Loaded to Memory", INFO)
					except:
						lgmain.save(f"!!!Error Reading {fw} data!!!", ERR)
					self[fw] = Load(fw, splfile)
				##

# ----------------------------------------------------------------------------------------
class Load(DictMethods):
	"""class which depicts existing configuration of firewall in various format
	"""
	def __str__(self):
		return "[O]: Configurations for Device: " + super().__str__()

	def __init__(self, fw, file_list):
		self.name = ""#tbd
		self.file_list = file_list
		self.dic = get_load(fw, file_list)
		try: self.ip = get_mgmt_ip(file_list['run_list'])
		except:	lgmain.save(f"!!!Configuration Reading 'SHOW RUN for MGMT IP' for {fw} failed!!!", ERR)


def get_load(fw, file_list):
	"""generate dic of the given firewall file list"""
	RT, intvsAcl, acldict, objgrps = None, None, None, None
	#
	try: RT = Routes(fw, route_list=file_list['route_list'])
	except:	lgmain.save(f"!!!Reading 'ROUTING TABLE' for {fw} failed!!!", ERR)
	try: intvsAcl = int_to_acl(fw, acg_list=file_list['int2acl_list'])
	except: lgmain.save(f"!!!Reading 'SHOW ACCESS-GROUP' for {fw} failed!!!", ERR)
	try: objgrps = ObjDict(fw, confList=file_list['run_list'], object_group_dict=None)
	except: lgmain.save(f"!!!Reading 'RUNNING CONFIG' for {fw} failed!!!", ERR)
	try: acldict = AclDict(fw, confList=file_list['acl_list'], object_group_dict=objgrps)
	except : 
		lgmain.save(f"!!!Reading 'SHOW ACCESS-LIST' for {fw} failed!!!", ERR)
		raise Exception(f"!!!Reading 'SHOW ACCESS-LIST' for {fw} failed!!!")

	return {
		"RT": RT,
		"intvsAcl": intvsAcl,
		"objgrps": objgrps,
		"acldict": acldict,
	}
# ----------------------------------------------------------------------------------------
