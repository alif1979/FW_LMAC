
from time import ctime
from collections import OrderedDict
import logging as lg

VERSION = "4.6.7"
# ----------------------------------------------------------------------------------------
# REQUESTS --------------------------------------------
REQUEST_HEADER_ROW = 1
FW_COL_NAMES = ('src_fw', 'dst_fw')
IP_COL_NAMES = ('src_ip', 'dst_ip')
CUSTOM_COLUMN_NAMES_FILTERED = ["req_type", "src_name", "src_type", "src_ip", "src_nat",
	"dst_name", "customer_prefix", "dst_type", "dst_ip", "dst_nat", "dst_port",
	"src_fw", "dst_fw", "customer"]

CUSTOM_COLUMN_NAMES_ALL = ["req_type", "src_name", "extra3", "src_type", "src_ip", "src_nat",
	"dst_name", "customer_prefix", "dst_type", "dst_ip", "dst_nat", "dst_port", "extra1", "extra2", 
	"src_fw", "dst_fw"]
REQUEST_ORG_SHEET_NAME = 'GSNI Firewall Filter申請書'
REQUEST_ORG_SHEET_HEADER_ROW = 8
ROWS_TOBE_TRIM_FROM_VALUE = "特記事項："
NINJA = False
# ----------------------------------------------------------------------------------------
# LOAD TEXT --------------------------------------------
line_continueators = ("{", ":")
line_split = False
s = ""
try:
	with open("settings.txt", 'r') as f:
		lst = f.readlines()
	for line in lst: 
		if len(line) > 1 and line.rstrip()[-1] in line_continueators:
			line_split = True
			s += "\n" + line
			continue
		if line.lstrip() == line: line_split = False
		s += line
		if not line_split:
			exec(s)
			s = ""
except:
	with open("log/activity.log", 'w') as f:
		e = "CRITICAL: Either {settings.txt} missing or having content error, please resolve and re-run"
		f.write(e)
	raise Exception(e)

# ----------------------------------------------------------------------------------------
# LOGGING CLASS
class Log():
	"""Activity Logging Class"""

	log_level = LOG_LEVEL_MIN

	def __init__(self, name=None, outputfile='activity.log' ):
		self.name = name
		self.opfile = outputfile
		self.enable_file_handle

	@property
	def enable_file_handle(self):
		"""File handler"""
		import logging as lgf
		if self.name == None:
			self.f_format = lgf.Formatter('%(asctime)s - %(levelname)s - %(message)s')
		else:
			name = self.name
			self.f_format = lgf.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
		self.f_handle = lgf.FileHandler(self.opfile)
		self.f_handle.setFormatter(self.f_format)
		self.f_logger = lgf.getLogger(self.name)
		self.f_logger.addHandler(self.f_handle)
		self.f_logger.setLevel(self.log_level)

	def save(self, msg, msgtype='warning'):
		if not NINJA or (msgtype in (ERR, CRITICAL)):
			exec("self.f_logger."+msgtype+"(msg)")
			print(f"{msgtype}\t|{msg}")

# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# LOAD REST --------------------------------------------
lgmain = Log('main', LOG_FOLDER + '/activity.log')
try:
	import PySimpleGUI as sg	
	sg.SetOptions(icon='sample/ali.ico')
	print = sg.EasyPrint
	sgLOAD = True
except:
	sgLOAD = False
	lgmain.save("INSTALL PySimpleGUI TO HAVE BENIFIT OF GUI OPTION SET", 'warning')
try:
	import xlrd
except:
	raise Exception("Critical: Missing Mandatory Module - xlrd")
	lgmain.save("Missing Mandatory Module - xlrd", 'critical')

# shortends
AR = ADD_REQUEST_BANNER
DR = DEL_REQUEST_BANNER
ARR = ADD_ROLLBACK_BANNER
DRR = DEL_ROLLBACK_BANNER
EXC = EXCEPTIONS_BANNER
CHANGE_BANNERS = {AR, DR, OBJ_GRP_CHG_BANNER }
ROLLBACK_BANNERS = { ARR, DRR, OBJ_GRP_RBK_BANNER }
ALL_BANNERS = CHANGE_BANNERS.union(ROLLBACK_BANNERS)
ADD_BANNERS = {AR, ARR}
DEL_BANNERS = {DR, DRR}
# ----------------------------------------------------------------------------------------
# FIXED CONS --------------------------------------------
GROUP_CANDIDATES = ('object-group_candidate', 'object_candidate')
INDIVIDUAL_CANDIDATES = ('host_candidate', 'prefix_candidate', 'eq_candidate', 'range_candidate')
SH_RTE_CMDS = {'route_list': CMDS_SHOW_RTE}
SH_RUN_CMDS = {'run_list': CMDS_SHOW_RUN}
SH_ACL_CMDS = {'acl_list': CMDS_SHOW_ACL}
SH_ACG_CMDS = {'int2acl_list': CMDS_SHOW_ACG}
OUTPUT_CMDS = (SH_RTE_CMDS, SH_RUN_CMDS, SH_ACL_CMDS, SH_ACG_CMDS)
DEBUG = 'debug'
INFO = 'info'
WARN = 'warning'
ERR = 'error'
CRITICAL = 'critical'
LOG_LEVELS = {DEBUG:10, INFO:20, WARN:30, ERR:40, CRITICAL:50}
FORTEEN_STARS = "*"*14
GREET = ["\n\n", EXCLAMATION_80, "\n\n\t\t\t\tGenerated on: ", ctime(),
	"\n\t\tThankx For using - Please validate output before apply.\n\n", EXCLAMATION_80, "\n\n"]
RUN_CONF_START_CHAR = ": Serial"
RUN_CONF_END_CHAR = ": end"

# ----------------------------------------------------------------------------------------
# DICT MAPS --------------------------------------------
ACL_DICT_KEYS = {
	0: "source_candidate",
	1: "destination_candidate",
	2: "port",
	3: "protocol",
	# 4: "remark"
	}
T = tuple(ACL_DICT_KEYS)

# ----------------------------------------------------------------------------------------
# MOP FILE CONSTANTS -------------------------------
MOP_OUTPUT_FOLDER = OUTPUT_FOLDER
DOT = "."
ITEM = '項目'
CONTENT = '内容'
REMARKS = '備考'
CHANGE = '変更'
CHANGE_PROCEDURE = '変更手順'
FALLBACK_PROCEDURE = 'fallback手順 '
SH_RUN = 'sh run'
HEADERS_COL = {CHANGE_PROCEDURE:3, FALLBACK_PROCEDURE:3, SH_RUN:0 }
VALUE_COLS = {CHANGE_PROCEDURE: (CONTENT, REMARKS, DOT), FALLBACK_PROCEDURE: (CONTENT, REMARKS, DOT), SH_RUN: ('Pre', 'Post', 'FORMULAE') }
CONTENT_START_FROM_COL = {CHANGE_PROCEDURE: 4, FALLBACK_PROCEDURE: 4, SH_RUN: 0}
VALUE_BEGIN_FROM_ROW = {CHANGE_PROCEDURE:10, FALLBACK_PROCEDURE:10, SH_RUN:1 }
CHANGE_ACL_ROWS = {'min':23, 'max':25}
FALLBACK_ACL_ROWS = {'min':23, 'max':25}
CHANGE_OBJGRP_ROWS = {'min':27, 'max':54}
FALLBACK_OBJGRP_ROWS = {'min':27, 'max':54}
DELETE = "削除"
ADD_TO = "追加"
def get_request(x):
	return "del" if x['req_type'] == DELETE else "add"
# ----------------------------------------------------------------------------------------

def userform():
	"""GUI USERFORM TO SET OPTIONS:
	Add new variable at 3 places, Lookup ADD [n]"""
	global CAPTURE_FOLDER               
	global LOG_EXTN                     
	global REQUEST_FILE                 
	global LOG_FOLDER                   
	global OUTPUT_FOLDER                
	global OUTPUT_FILE_EXTENSION        
	global LOG_WARNING                  
	global LINENO_ON_DEL                
	global ONSCREEN_DISPLAY             
	global SAVE_TO_FILE                 
	global CLUB_OUTPUT_FOR_ALL_DEVICE
	global MOP_EXCEL_TEMPLATE
	global MOP_OUTPUT_FOLDER
	global MOP_EXCEL_OUTPUT
	global LOG_LEVEL_MIN
	global TASK_COMPLETE_NOTICE
	global ACL_BASE
	global USE_SOURCE_NAT_IP
	global USE_DESTINATION_NAT_IP
	global NINJA
	#### ADD 1
	#
	boot = None
	version = VERSION
	header = f'FW LMAC REQUEST - {version}'
	
	tab1 = [[sg.Frame(title='Parameters', title_color='red', size=(600, 4), relief=sg.RELIEF_RIDGE, 
		layout=[
		[sg.Text('', font=("TimesBold", 5))],
		[sg.Text('Configuration backup parameters :'+' '*40, font=('TimesBold',14))],
		[sg.Text('-'*200, font=("TimesBold", 5))],
		[sg.Text("Configuration captured folder :"), sg.InputText(key='CAPTURE_FOLDER', size=(20, 1), default_text=CAPTURE_FOLDER), sg.FolderBrowse()],
		[sg.Text("Configuration captured files extension :"), sg.InputText(key='LOG_EXTN', size=(20, 1), default_text=LOG_EXTN)],
		[sg.Text('', font=("TimesBold", 5))],
		[sg.Text('Input/Request File Parameters :', font=('TimesBold',14))],
		[sg.Text('-'*200, font=("TimesBold", 5))],
		[sg.Text("Rule change request file (Excel) :"), sg.InputText(key='REQUEST_FILE', size=(20, 1), default_text=REQUEST_FILE), sg.FileBrowse()],
		[sg.Text("MOP Template file (Excel) :"), sg.InputText(key='MOP_EXCEL_TEMPLATE', size=(30, 1), default_text=MOP_EXCEL_TEMPLATE), sg.FileBrowse(key='MOP1')],
		[sg.Text('', font=("TimesBold", 5))],
		[sg.Text('Output Parameters :', font=('TimesBold',14))],
		[sg.Text('-'*200, font=("TimesBold", 5))],
		[sg.Text("Activity Log folder :"), sg.InputText(key='LOG_FOLDER', size=(20, 1), default_text=LOG_FOLDER), sg.FolderBrowse()],
		[sg.Text("Configuration Output folder :"), sg.InputText(key='OUTPUT_FOLDER', size=(20, 1), default_text=OUTPUT_FOLDER), sg.FolderBrowse()],
		[sg.Text("Configuration Output file extension :"), sg.InputText(key='OUTPUT_FILE_EXTENSION', size=(20, 1), default_text=OUTPUT_FILE_EXTENSION)],
		[sg.Text("MOP Excel Output folder :"), sg.InputText(key='MOP_OUTPUT_FOLDER', size=(20, 1), default_text=OUTPUT_FOLDER), sg.FolderBrowse(key='MOP2')],
		[sg.Text('', font=("TimesBold", 5))],
		]),
	]]

	tab2 = [[sg.Frame(title='Options', title_color='red', size=(600, 4), relief=sg.RELIEF_RIDGE, 
		layout=[
		[sg.Text('-'*200, font=("TimesBold", 5))],
		[sg.Checkbox('Task Complete Notice', default=TASK_COMPLETE_NOTICE, key='TASK_COMPLETE_NOTICE') ],
		[sg.Checkbox('"log warning" suffix in rules output', default=LOG_WARNING, key='LOG_WARNING' ) ],
		[sg.Checkbox('Line numbers on Negating rules', default=LINENO_ON_DEL, key='LINENO_ON_DEL' ) ],
		[sg.Text('-'*200, font=("TimesBold", 5))],
		[sg.Checkbox('Delta Changes on debug window', default=ONSCREEN_DISPLAY, key='ONSCREEN_DISPLAY' ) ],
		[sg.Checkbox('Delta Changes in text file', default=SAVE_TO_FILE, key='SAVE_TO_FILE', change_submits=True  ) ],
		[sg.Checkbox('Club Delta output(s)', default=CLUB_OUTPUT_FOR_ALL_DEVICE, key='CLUB_OUTPUT_FOR_ALL_DEVICE' ) ],
		[sg.Checkbox('MOP Excel Output', default=MOP_EXCEL_OUTPUT, key='MOP_EXCEL_OUTPUT', change_submits=True ) ],
		[sg.Text('-'*200, font=("TimesBold", 5))],
		[sg.Checkbox('Use NAT IP for Source(s)', default=USE_SOURCE_NAT_IP, key='USE_SOURCE_NAT_IP') ],
		[sg.Checkbox('Use NAT IP for Destinations(s)', default=USE_DESTINATION_NAT_IP, key='USE_DESTINATION_NAT_IP') ],
		[sg.Text('-'*200, font=("TimesBold", 5))],
		[sg.Text("ACL Base"), sg.InputCombo(['SOURCE', 'DESTINATION'], default_value='SOURCE', key='ACL_BASE' ) ],
		[sg.Text("Minimum Logging Level: "), sg.InputCombo(['debug', 'info', 'warning', 'error', 'critical'], default_value='info', key='LOG_LEVEL_MIN' ) ],
		#### ADD 2
		[sg.Text('', font=("TimesBold", 5))],
		]),
	]]

	layout = [
		[sg.Text("AT&T", font='arial', justification='center', size=(500,1))],
		[sg.Text(header, font='arial', justification='center', size=(500,1))],
		[sg.Frame(title='Button Pallete', size=(600, 4), title_color='blue', relief=sg.RELIEF_RIDGE, layout=[
			[sg.OK('Go', size=(10,1), bind_return_key=True), sg.Cancel('Cancel', size=(10,1), bind_return_key=True), sg.Text(' '*80), sg.Button('Ninja', key='ninja', size=(10,1), bind_return_key=True)],
			]),
		],
		[sg.TabGroup([[sg.Tab('    Request    ', tab1), sg.Tab('    Power    ', tab2)]])],
		[sg.Text("Note: Executing menu from any module except 'main' will result nothing...", font=('TimesBold',12), text_color='red')],
	]

	w = sg.Window(header, layout, 
		resizable=True, 
		size=(768, 768),
		button_color = ("black", "lightgray") ,
		alpha_channel=.92,
		grab_anywhere=True,
		)

	while True:
		event, (i) = w.Read(timeout=1000)

		NINJA = event == 'ninja'
		if event == 'Cancel':
			boot = False
			break

		if event == 'MOP_EXCEL_OUTPUT':
			w.Element('MOP_OUTPUT_FOLDER').Update(disabled=not i['MOP_EXCEL_OUTPUT'])
			w.Element('MOP_EXCEL_TEMPLATE').Update(disabled=not i['MOP_EXCEL_OUTPUT'])
			w.Element('MOP1').Update(disabled=not i['MOP_EXCEL_OUTPUT'])
			w.Element('MOP2').Update(disabled=not i['MOP_EXCEL_OUTPUT'])

		if event == 'SAVE_TO_FILE':
			w.Element('OUTPUT_FILE_EXTENSION').Update(disabled=not i['SAVE_TO_FILE'])
			w.Element('CLUB_OUTPUT_FOR_ALL_DEVICE').Update(disabled=not i['SAVE_TO_FILE'])

		if event in ('Go', 'ninja'):
			boot = True
			CAPTURE_FOLDER = i['CAPTURE_FOLDER']
			LOG_EXTN = i['LOG_EXTN']
			REQUEST_FILE = i['REQUEST_FILE']
			LOG_FOLDER = i['LOG_FOLDER']
			OUTPUT_FOLDER = i['OUTPUT_FOLDER']
			OUTPUT_FILE_EXTENSION = i['OUTPUT_FILE_EXTENSION']
			LOG_WARNING = i['LOG_WARNING']
			LINENO_ON_DEL = i['LINENO_ON_DEL']
			CLUB_OUTPUT_FOR_ALL_DEVICE = i['CLUB_OUTPUT_FOR_ALL_DEVICE']
			MOP_EXCEL_TEMPLATE = i['MOP_EXCEL_TEMPLATE']
			MOP_OUTPUT_FOLDER = i['MOP_OUTPUT_FOLDER']
			MOP_EXCEL_OUTPUT = i['MOP_EXCEL_OUTPUT']
			ONSCREEN_DISPLAY = i['ONSCREEN_DISPLAY']
			SAVE_TO_FILE = i['SAVE_TO_FILE']
			TASK_COMPLETE_NOTICE = i['TASK_COMPLETE_NOTICE']
			USE_SOURCE_NAT_IP = i['USE_SOURCE_NAT_IP']
			USE_DESTINATION_NAT_IP = i['USE_DESTINATION_NAT_IP']
			ACL_BASE = i['ACL_BASE']
			LOG_LEVEL_MIN = LOG_LEVELS[i['LOG_LEVEL_MIN']]
			#### ADD 3

		if boot:
			w.Element('Go').Update(disabled=True)
			break
	w.Close()
	return boot

try:
	if BOOT: pass
except: BOOT = userform() if sgLOAD and SHOW_MENU else True



# # ----------------------------------------------------------------------------------------
