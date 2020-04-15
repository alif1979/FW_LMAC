

try:
	from general import *
	from group import addaction
	from load import load_conf_n_request
	from firewall import request_type_object
	from output import Outputs, FWOutput, TextOutput
	from mop_calls import create_mop_excels
	from process_request import process_del_request, process_add_request, desc_remove_per_row
except:
	raise ImportError("Unable to import necessary Modules, Please contact al202t@att.com")
# ----------------------------------------------------------------------------------------
def step1_prepare():
	"""Readiness before starting"""
	lgmain.save('~~~ Activity Begin / Preparing ~~~', INFO )
	df, load = load_conf_n_request(REQUEST_FILE)
	df = addaction(df)
	op = Outputs()
	return (df, load, op)

# ----------------------------------------------------------------------------------------
def step2_iterate_over(df, load, op):
	"""Start"""
	lgmain.save('Starting with Config Generation ...', INFO)
	for x in range(len(df)):
		row = df.iloc[x]
		fw_cols = (row[fcn] for fcn in FW_COL_NAMES)
		customer = row.customer
		for fw in fw_cols:
			err_occ = False
			if not fw or fw == "N/A": continue
			lgmain.save(f'Working on Excel Row {x+2}: {fw}', INFO)
			lg = Log(fw, LOG_FOLDER + "/" + fw + LOG_EXTN)
			if not op[fw]: op[fw] = FWOutput()
			fwop = op[fw]
			f = request_type_object(fw, load, row)
			if not f:
				lg.save(f'No valid Request found for Excel row {x+2}', ERR)
				fwop.append(EXC, (f'No valid Request found for Excel row {x+2}', customer, x+2))
				continue
			#
			req_type = get_request(row)
			ipaddress = load[fw].ip
			src_candid = set(row.src_ip)
			dst_candid = set(row.dst_ip)
			lastline = 0
			prev_emls = set()
			#
			lg.save('//iterating over items// ', INFO)
			for protocol, attrib in f.ports:
				action = attrib['action']
				for k, v in attrib.items():					
					if k == 'action': continue
					basecheck = dst_candid if ACL_BASE == "DESTINATION" else src_candid
					try:
						aclname = f.get_acl(basecheck, base=ACL_BASE)
					except:
						err_occ = True
						popup('Execution Jumped',
						f'Verify data for Firewall {fw} on Excel Row {x+2} for NAT/non-NAT IP requirement',
						'This firewall is skipped from execution',
						auto_close=True, auto_close_duration=5)
						break

					lg.save('Matching Access-List: {' + aclname + '}', INFO)
					acl = load[fw]['acldict'][aclname]
					acg = load[fw]['objgrps']

					if req_type == 'del':
						emls = process_del_request(req_type, fwop, acl, aclname, f,
							src_candid, dst_candid, v, protocol, row, str(x+2), lg)
						prev_emls.update(emls)

					if req_type == 'add':
						lastline = process_add_request(req_type, fwop, acl, aclname, acg, f,
							src_candid, dst_candid, k, v, protocol, row, str(x+2), lg, lastline)
				if err_occ: break
			desc_remove_per_row(prev_emls, acl, aclname, fwop, row, f, str(x+2))

			op.ip = ipaddress
	TextOutput(op, CLUB_OUTPUT_FOR_ALL_DEVICE, x+2)
	lgmain.save('... Completed Config Generation', INFO)

	return None

# ----------------------------------------------------------------------------------------
def step3_mop_generate(op, load):
	"""EXCEL MOP GENERATION"""
	lgmain.save(f'Starting MOP File(s) Generation...', INFO)
	create_mop_excels(op, load)
	lgmain.save(f'...Finished MOP File(s) Generation', INFO)
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def main():
	"""BOOT FROM HERE"""
	lgmain.f_logger.setLevel(LOG_LEVEL_MIN)
	(df, load, op) = step1_prepare()
	lgmain.save('', INFO)
	lgmain.save('~~~ Going thru Request ~~~', INFO)
	step2_iterate_over(df, load, op)
	if MOP_EXCEL_OUTPUT: step3_mop_generate(op, load)
	if TASK_COMPLETE_NOTICE and not NINJA:
		popup('Execution Finished',
		'Look for Configurations inside "config" folder\nLook for activity log files inside "log" folder',
		auto_close=True, auto_close_duration=10)

# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
	if BOOT: main()
	quit() 
# ----------------------------------------------------------------------------------------

