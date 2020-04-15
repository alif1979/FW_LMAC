
from general import *
from common import InitGroups, DictMethods
from collections import OrderedDict
# ----------------------------------------------------------------------------------------
class Outputs(InitGroups, DictMethods):
	"""Configuration Output of firewalls"""	
	def get_groups(self, fw_name, dummylist):
		self[fw_name] = FWOutput()

# ----------------------------------------------------------------------------------------
class FWOutput(DictMethods):
	"""Configuration Output of firewall"""
	def __init__(self):
		self.dic = OrderedDict()
		self.ip = ''

	def rem_on_del_req_op(self, aclname, line_no, customer, f, xl_row, rem):
		request_type = DR
		request_rollback_type = DRR
		_myrule = f.rem_rule(aclname, line_no, rem)
		_rollbackrule = f.rem_rollback_rule(aclname, line_no, rem)
		self.add_output(customer, xl_row, request_type, request_rollback_type, 
			_myrule, _rollbackrule)

	def add_del_req_op(self, acl, aclname, line_no, srObj, f, xl_row):
		"""Delete Request OUTPUT ACL Rule change/rollback"""
		sr = srObj.sr
		customer = srObj.customer
		if sr != 'del':
			self.append(EXC, f'Invalid Request', xl_row)
		request_type = DR
		request_rollback_type = DRR
		attr = acl[line_no]
		org_logwarn = acl[line_no]['log_warning']
		_myrule = f.rule(aclname, line_no, org_logwarn, **attr)
		_rollbackrule = f.rollback_rule(aclname, line_no, org_logwarn, **attr)
		self.add_output(customer, xl_row, request_type, request_rollback_type, 
			_myrule, _rollbackrule)

	def add_add_req_op(self, aclname, line_no, srObj, f, xl_row, attr):
		"""Add Request OUTPUT ACL Rule change/rollback"""
		sr = srObj.sr
		customer = srObj.customer
		if sr != 'add':
			self.append(EXC, f'Invalid Request', xl_row)
		request_type = AR
		request_rollback_type = ARR
		_myrule = f.rule(aclname, line_no, **attr)
		_rollbackrule = f.rollback_rule(aclname, line_no, **attr)
		self.add_output(customer, xl_row, request_type, request_rollback_type, 
			_myrule, _rollbackrule)

	def add_object_group(self, grpObj, newmembers, srObj, f, xl_row):
		"""Add/Delete Request OUTPUT Object group change/rollback"""
		sr = srObj.sr
		customer = srObj.customer
		request_type = OBJ_GRP_CHG_BANNER
		request_rollback_type = OBJ_GRP_RBK_BANNER
		if sr not in ('del', 'add'):
			self.append(EXC, f'Invalid Request', xl_row)
		invsr = "add" if sr == "del" else "del"
		_myrule = f.objgrp(grpObj, newmembers, invsr)
		_rollbackrule = f.objgrp(grpObj, newmembers, sr)
		self.add_output(customer, xl_row, request_type, request_rollback_type, 
			_myrule, _rollbackrule)

	def add_output(self, customer, xl_row, request_type, request_rollback_type, 
		_myrule, _rollbackrule):
		"""output append helper"""
		for x, y in self:
			if request_type in CHANGE_BANNERS: 
				for z in y:
					if _myrule in z[0]: return None
		self.append(request_type, (_myrule, customer, xl_row))
		self.append(request_rollback_type, (_rollbackrule, customer, xl_row))

	def add_exception(self, desc, xl_row):
		"""exception append helper"""
		self.append(EXC, desc)
		self.append('xl_row', xl_row)

# ----------------------------------------------------------------------------------------


class TextOutput(object):
	"""class to generate text output"""

	def __init__(self, op, club=True, max_row=0):
		self.op = op
		self.club = club
		self.max_row = max_row
		self.getOut

	@property
	def getOut(self):
		"""Caller: Save clubbed outputs"""
		opl = self.output_lists
		if self.club:
			if SAVE_TO_FILE:
				writeTofile((opl, GREET), OUTPUT_FOLDER + '/clubbed_delta' + OUTPUT_FILE_EXTENSION)
			if ONSCREEN_DISPLAY:
				print(opl)

	# Pullers ---------------------------------
	@property
	def output_lists(self):
		"""--> clubbed output to tuple"""
		s = ""
		for fw, fwop in self.op:
			if self.club:
				s+=self.firewall_header(fw)
				s+=self.output_list(fwop)
			else:
				for row in range(2, self.max_row+1):
					chglist = self.output_list(fwop, row, CHANGE_BANNERS)
					rbklist = self.output_list(fwop, row, ROLLBACK_BANNERS)
					if SAVE_TO_FILE:
						writeTofile(chglist, "tmp/" + fw + '-change.tmp')
						writeTofile(rbklist, "tmp/" + fw + '-rollback.tmp')
					if ONSCREEN_DISPLAY:
						print(chglist)
						print(rbklist)
				self.club_scripts(fw)
		return s

	def output_list(self, fwop, row=None, banner_type=ALL_BANNERS):
		"""--> individual output list"""
		s = ""
		test = False
		for fwk, fwv in fwop:
			if row and fwk not in banner_type: continue  # can be removed? TB-Check
			subheader = self.req_row_header(fwk, row)
			headerapplied = False
			ssfwv = sorted(set(fwv), key=sort_seq_012)
			if fwk in (DEL_ROLLBACK_BANNER, ADD_REQUEST_BANNER):
				intlinenumbers = [(int(line.split()[3]), line.split()[1])  
									for line, customer, rw in ssfwv]
				num_acl_grp = acl_group_members(intlinenumbers)
				for acl, num_grp in num_acl_grp.items():
					for k, v in reversed(sorted(num_grp.items())):
						for n in range(int(k), int(v)+1):
							for line, customer, rw in ssfwv:
								if acl not in line: continue
								if row and int(rw) != row: continue
								if not headerapplied: 
									s+=subheader
									headerapplied = True
								if "line " + str(n) + " " in line: 
									s+="\n"+line
									break
			else:
				for line, customer, rw in ssfwv:
					if row and int(rw) != row: continue
					if not headerapplied: 
						s+=subheader
						headerapplied = True
					s+="\n"+line
		return s

	# Headers --------------------------------------------
	def main_header(self, fw):
		"""main header for firewall"""
		return ["\n\n", LINE_80,
		"\n!\n", FIREWALL_NAME_BANNER_PREFIX, fw, FIREWALL_NAME_BANNER_SUFFIX,
		"\n!\t\t\t\tGenerated on: ", ctime(),
		"\n!\t\tThankx For using - Please validate output before apply.\n", LINE_80, "\n\n"]

	def firewall_header(self, fw):
		"""firewall header """
		return f"\n\n{HASH_80}\n{FIREWALL_NAME_BANNER_PREFIX}{fw}{FIREWALL_NAME_BANNER_SUFFIX}\n{HASH_80}\n"

	def req_row_header(self, fw, row):
		"""request row number header"""
		if row is None:
			return f"\n{DOUBLELINE_80}\n{fw}\n{DOUBLELINE_80}"
		else:
			return f"\n{PUNCTUATION_80}\n{fw}{EXCEL_ROW_BANNER_PREFIX1}{str(row)}{EXCEL_ROW_BANNER_SUFFIX}\n{PUNCTUATION_80}"


	# Writers -----------------------------------------
	def club_scripts(self, fw):
		"""all clubbed scripts"""
		if not SAVE_TO_FILE: return None
		with open("tmp/" + fw + '-change.tmp', 'r') as f:
			changes = f.read()		
		with open("tmp/" + fw + '-rollback.tmp', 'r') as f:
			rollbacks = f.read()
		remove("tmp/" + fw + '-change.tmp')
		remove("tmp/" + fw + '-rollback.tmp')
		writeTofile(self.main_header(fw), OUTPUT_FOLDER + "/" + fw + OUTPUT_FILE_EXTENSION)
		writeTofile(changes + "\n"*3 + rollbacks, OUTPUT_FOLDER + "/" + fw + OUTPUT_FILE_EXTENSION)

