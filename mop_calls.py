
from general import *
from addressing import addressing
from db import XL_READ, XL_WRITE, pd
from pre_post import PrePost
# ----------------------------------------------------------------------------------------

def read_template_to_dfs():
	"""read mop template file and return dictionary of dataframe(s) objects"""
	template_obj = {CHANGE_PROCEDURE:None, FALLBACK_PROCEDURE:None, SH_RUN:None }
	for shtName, index_col in HEADERS_COL.items():
		template_obj[shtName] = XL_READ(MOP_EXCEL_TEMPLATE, shtName=shtName, header=index_col)
	return template_obj

# ----------------------------------------------------------------------------------------

class MOP(object):
	"""class for Method of Process Excel generation"""
	def __init__(self, hostname, ipObj, output, pre, post):
		self.hostname = hostname
		self.ipObj = ipObj
		self.output = output
		self.chgScript, self.fbkScript = get_chg_fbk_rule_scripts(self.output)
		self.grpchgScript, self.grpfbkScript = get_chg_fbk_object_group_scripts(self.output)
		self.template_obj = read_template_to_dfs()
		self.CHANGE_ACL_ROWS = CHANGE_ACL_ROWS.copy()
		self.FALLBACK_ACL_ROWS = FALLBACK_ACL_ROWS.copy()
		self.CHANGE_OBJGRP_ROWS = CHANGE_OBJGRP_ROWS.copy()
		self.FALLBACK_OBJGRP_ROWS = FALLBACK_OBJGRP_ROWS.copy()
		self.scriptlist = (self.chgScript, self.fbkScript, 
			self.grpchgScript, self.grpfbkScript)
		self.xl_row_list = (self.CHANGE_ACL_ROWS, self.FALLBACK_ACL_ROWS, 
			self.CHANGE_OBJGRP_ROWS, self.FALLBACK_OBJGRP_ROWS)
		for script, rowidentifier in zip(self.scriptlist, self.xl_row_list):
			self.update_general_script(script, rowidentifier)
		self.update_pre_post_config(pre, post)
		self.update_top_details
		self.write_dfs_to_excel

	def update_pre_post_config(self, pre, post):
		"""pre-post configuration comparision"""
		formulae = []
		prelst = pre.split("\n")
		postlst = post.split("\n")
		for n in range(2, len(prelst)+2):
			cell_formula = f"=EXACT(A{n},B{n})"
			formulae.append(cell_formula)
		dic = {"Pre": prelst, "Post":postlst, "FORMULAE":formulae}	
		self.template_obj[SH_RUN].df = self.template_obj[SH_RUN].df.append(pd.DataFrame(dic))

	def update_general_script(self, script, what):
		"""geneal script for change and fallback procedure tabs"""
		color = "w"
		if what is self.CHANGE_ACL_ROWS or what is self.FALLBACK_ACL_ROWS: color = "w"
		if what is self.CHANGE_OBJGRP_ROWS or what is self.FALLBACK_OBJGRP_ROWS: color = "a"
		if what is self.CHANGE_ACL_ROWS or what is self.CHANGE_OBJGRP_ROWS:
			where = CHANGE_PROCEDURE
		else:
			where = FALLBACK_PROCEDURE
		for k, v in VALUE_COLS.items():
			prevcustomer = ""
			if k == where:
				tok = self.template_obj[k]
				self.add_chgprocedure_row(script, what, tok)
				ss = sorted(set(script), key=sort_seq_012)
				try:
					intlinenumbers = [(int(l.split()[3]), l.split()[1])  for l, customer, rw in ss]
					num_acl_grp = acl_group_members(intlinenumbers)
					for acl, num_grp in num_acl_grp.items():						
						toggle = False
						for key, value in reversed(sorted(num_grp.items())):
							for n in range(key, value+1):
								for scriptline, customer, row in ss:
									if acl not in scriptline: continue
									if "line " + str(n) + " " in scriptline:
										if prevcustomer != "" and prevcustomer != customer:
											what['min'] += 1
										for line in scriptline.split("\n"):
											tok.update(what['min'], v[0], line)
											tok.update(what['min'], v[1], customer)
											tok.update(what['min'], v[2], color)
											prevcustomer = customer
											what['min'] += 1
										new_range += 1
				except:
					for scriptline, customer, row in ss:
						if prevcustomer != "" and prevcustomer != customer:
							what['min'] += 1
						for line in scriptline.split("\n"):
							tok.update(what['min'], v[0], line)
							tok.update(what['min'], v[1], customer)
							tok.update(what['min'], v[2], color)
							prevcustomer = customer
							what['min'] += 1

	def add_chgprocedure_row(self, script, what, tok):
		"""Insert chnge/rollback procedure tab rows if short"""
		n = len(script) 
		tok.insert_row(atrow=what['max']+1, n=n)
		what['max'] += n
		if what is self.CHANGE_ACL_ROWS or what is self.FALLBACK_ACL_ROWS:
			self.CHANGE_OBJGRP_ROWS['min'] += n
			self.CHANGE_OBJGRP_ROWS['max'] += n
			self.FALLBACK_OBJGRP_ROWS['min'] += n
			self.FALLBACK_OBJGRP_ROWS['max'] += n

	@property
	def update_top_details(self):
		"""Update TOP details , hostname / ip etc on change/fallback procedure tab"""
		for k, v in VALUE_COLS.items():
			if k == CHANGE_PROCEDURE or k == FALLBACK_PROCEDURE:
				tok = self.template_obj[k]
				tok.update(2, CONTENT, self.hostname + "/" + (self.ipObj+0))
				tok.update(0, ITEM, self.hostname+" "+CHANGE)
				rw = tok.get_row_number(ITEM, '2号機にLogin')
				tok.update(rw, CONTENT, self.hostname + "/" + (self.ipObj+1))

	@property
	def write_dfs_to_excel(self):
		"""write dictionary of dataframe(s) objects, to excel"""
		template_df = {CHANGE_PROCEDURE:None, FALLBACK_PROCEDURE:None, SH_RUN:None }
		for k, v in self.template_obj.items():
			template_df[k] =  v.df
		XL_WRITE(self, HEADERS_COL, **template_df)
		return None




# ----------------------------------------------------------------------------------------

def create_mop_excels(op, load):
	"""Method of process Excel generation"""
	ipObj = addressing(op.ip + "/29")
	for opk, opv in op:
		pp = PrePost(opv, load[opk], runningfile=CAPTURE_FOLDER+"/"+opk+LOG_EXTN)
		lgmain.save(f'Working on {opk}.xlsx', INFO)
		m = MOP(opk, ipObj, opv, pp.runningconfig, pp.postconfig)

# ----------------------------------------------------------------------------------------
def get_chg_fbk_rule_scripts(opv):
	"""get change and rollback rules from output object"""
	script, chgScript, fbkScript = None, [], []
	for fwk, fwv in opv:
		if fwk == EXCEPTIONS_BANNER: continue
		s = []
		if (fwk.startswith(ADD_REQUEST_BANNER) or 
			fwk.startswith(DEL_REQUEST_BANNER)):
			script = True
		elif (fwk.startswith(ADD_ROLLBACK_BANNER) or 
			fwk.startswith(DEL_ROLLBACK_BANNER)):
			script = False
		else:
			continue
		if isinstance(fwv, (list, tuple)):
			for v in set(fwv):
				s.append(v)
		else:
			s.append(v)
		if script:
			chgScript.extend(s)
		else:
			fbkScript.extend(s)
	return (chgScript, fbkScript)


def get_chg_fbk_object_group_scripts(opv):
	"""get change and rollback object group change details from output object"""
	script, chgScript, fbkScript = None, [], []
	for fwk, fwv in opv:
		if fwk == EXCEPTIONS_BANNER: continue
		s = []
		if fwk.startswith(OBJ_GRP_CHG_BANNER):
			script = True
		elif fwk.startswith(OBJ_GRP_RBK_BANNER):
			script = False
		else:
			continue
		if isinstance(fwv, (list, tuple)):
			for v in set(fwv):
				s.append(v)
		else:
			s.append(v)
		if script:
			chgScript = s
		else:
			fbkScript = s 
	return (chgScript, fbkScript)


# ----------------------------------------------------------------------------------------
