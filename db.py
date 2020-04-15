
from general import *
from css import *
import copy
try:
	import pandas as pd
except:
	lgmain.save("DEPENDANCY NOT MET, Library missing - pandas!!!", CRITICAL)
	raise Exception("DEPENDANCY_ERROR, Library missing - pandas")
if MOP_EXCEL_OUTPUT:
	try:
		from openpyxl import load_workbook
	except:
		lgmain.save("DEPENDANCY NOT MET, Library missing - openpyxl!!!", CRITICAL)
		raise Exception("DEPENDANCY_ERROR, Library missing - openpyxl")
# ----------------------------------------------------------------------------------------

class XL_WRITE():
	'''EXEL FILE CREATE, 
	hostname  - excel file name
	**sht_df    - sht_name=dataframe
		df        - dataframe which data to be copied to Excel.
		sht_name  - Sheet Name of Excel where data to be copied
	'''

	# Object Initializer
	def __init__(self, mopObj, headers_col, **sht_df):
		self.i = 0
		self.hostname = mopObj.hostname
		hn = mopObj.hostname
		self.ip = mopObj.ipObj+0
		while True:
			try:
				op_file = self.getnewmop(hn)
				break
			except PermissionError:
				hn = self.next_file
			except:
				break
		self.write_to_excel(op_file, headers_col, **sht_df)

	@property
	def next_file(self):
		self.i += 1
		hn = self.hostname+" ("+str(self.i)+")"
		return hn

	@staticmethod
	def getnewmop(hn):
		filecopy(MOP_EXCEL_TEMPLATE, MOP_OUTPUT_FOLDER + "/" + hn + ".xlsx")
		return MOP_OUTPUT_FOLDER + "/" + hn + ".xlsx"

	def write_to_excel(self, op_file, headers_col, **sht_df):
		for sht_name, df in sht_df.items():
			sdf = df.style.\
						apply(v_bg_color_schema(sht_name), axis=1).\
						apply(h_font_bg_color_schema(sht_name), axis=1)
			try:
				append_df_to_excel(op_file, 
					sdf,
					sheet_name=sht_name, 
					index=False, startrow=headers_col[sht_name], 
					header=True, 
					)
			except PermissionError:
				op_file = self.getnewmop(self.next_file)
				self.write_to_excel(op_file, headers_col, **sht_df)

# ----------------------------------------------------------------------------------------
class XL_READ(object):
	'''EXCEL FILE READING,
	df      - DataFrame object (iterable, lenth, etc. available )
	'''

	# Object Initializer
	def __init__(self, xl, shtName='Sheet1', fields_list=None, header=0):
		self.df = pd.read_excel(xl, sheet_name=shtName, usecols=fields_list, 
			header=header).fillna('')
		
	# Length of Object
	def __len__(self):
		return self.df.last_valid_index()+1

	# Object Iterator
	def __iter__(self):
		for header, value in self.df.items():
			yield (header, value)		

	# Get a specific Item/Record from Object
	def __getitem__(self, key):
		'''get an item from parameters'''
		return self.df[key]
		
	def __get__(self, column, row):
		return self[column][row]

	# Object Data Filter
	def filter(self, df=None, **kwarg):
		'''Filter Records
		df    - external data frame ( default object dataframe )
		kwarg - filters to be applied on df.
		'''
		if df is None:
			tmpdf = self.df
		else:
			tmpdf = df
		for k, v in kwarg.items():
			try:
				tmpdf = tmpdf[tmpdf[k]==v]
			except:
				pass
		return tmpdf

	def column_values(self, column, **kwarg):
		'''selected column output, after filters applied
		column - a single column name or , list of column names
		kwarg  - filters to be applied
		'''
		return self.filter(**kwarg)[column]

	def update(self, row, col_name, value):
		"""update specific position value in df"""
		self.df.iloc[row, self.df.columns.get_loc(col_name)] = value
		
	def update_list_col(self, row, col_list, col_name, value):
		for colname in col_list:
			if colname != col_name: continue
			try:
				self.df.iloc[row, self.df.columns.get_loc(col_name)] = value
			except:
				self.df = self.df.append({}, True).fillna("")
				self.df.iloc[row, self.df.columns.get_loc(col_name)] = value

	def insert_row(self, atrow, n=1):
		"""Inserts blank row(s) before given atrow position"""
		df1 = self.df[0:atrow]
		df2 = self.df[atrow:]
		for x in range(n): df1 = df1.append({}, True).fillna("")
		df_result = pd.concat([df1, df2])
		df_result.index = [*range(df_result.shape[0])] 
		self.df = df_result

	def get_row_number(self, column, value):
		return self[self[column] == value].index
# ----------------------------------------------------------------------------------------

def append_df_to_excel(filename, df, sheet_name, startrow, **to_excel_kwargs):
	"""Append a DataFrame [df] to existing Excel file [filename] """
	############# SLOW FUNCTION #########
	if 'engine' in to_excel_kwargs: to_excel_kwargs.pop('engine')
	writer = pd.ExcelWriter(filename, engine='openpyxl')
	writer.book = load_workbook(filename)
	writer.sheets = {ws.title:ws for ws in writer.book.worksheets}
	if startrow is None: startrow = 0
	df.to_excel(writer, sheet_name, startrow=startrow, **to_excel_kwargs)
	writer.save()
# ----------------------------------------------------------------------------------------

def getstartcol(sht_name): return CONTENT_START_FROM_COL[sht_name]
def getcols(sht_name): return VALUE_COLS[sht_name]

# ----------------------------------------------------------------------------------------
