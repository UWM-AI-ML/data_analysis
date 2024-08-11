# importing libraries
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui 
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys 
import os
import numpy as np
cxfel_root = os.environ['CXFEL_ROOT']
startup_file = cxfel_root+'/misc_tools/startup.py'
exec(open(startup_file).read())
from misc_tools import read_h5

class Stream(QObject):
	newtext = pyqtSignal(str)

	def write(self,text):
		self.newtext.emit(str(text))

# The Overall Window
class Window(QMainWindow): 
	
	def __init__(self): 
		super().__init__() 

		# setting title 
		self.setWindowTitle("Diffusion Map") 

		# setting geometry 
		self.setGeometry(200, 200, 900, 550) 
		self.tab_widget = MyTabWidget(self) 
		self.setCentralWidget(self.tab_widget) 
		
		self.show()
	
	def closeEvent(self, event):
		"""Shuts down application on close."""
		# Return stdout to defaults.
		sys.stdout = sys.__stdout__
		super().closeEvent(event)


# Tabs 
class MyTabWidget(QWidget):
	def __init__(self, parent):
		super(QWidget, self).__init__(parent)
		self.layout = QVBoxLayout(self)
		self.tabs = QTabWidget(self,tabShape=QTabWidget.Rounded)
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.close_current_tab)
		self.tabs.setMovable(True)
		# First tab : main
		self.tab1 = QWidget()
		self.file_path = None

		
		# Put parameter box
		self.parameter_box("Transpose",10,130,100,30)
		self.parameter_box("Nearest Neighbour:",10,170,140,30)
		self.parameter_box("Sigma Factor:",10,210,110,30)
		self.parameter_box("nEigs:",10,250,60,30)
		self.parameter_box("Concatenation:",10,290,120,30)
		self.parameter_box("Data Chunk Size:",10,330,120,30)
		self.parameter_box("MPI Workers:",10,370,120,30)
		self.checkbox_transpose_true = QCheckBox(self.tab1)
		self.checkbox_transpose_true.setGeometry(160,130,60,30)
		self.checkbox_transpose_true.setText("DxN")
		self.checkbox_transpose_false = QCheckBox(self.tab1)
		self.checkbox_transpose_false.setGeometry(250,130,60,30)
		self.checkbox_transpose_false.setText("NxD")
		self.checkbox_transpose_true.stateChanged.connect(self.transpose_uncheck)
		self.checkbox_transpose_false.stateChanged.connect(self.transpose_uncheck)

		self.line4 = QLineEdit("",self.tab1)
		self.line4.setGeometry(160,170,60,30)
		self.line5 = QLineEdit("",self.tab1)
		self.line5.setGeometry(160,210,60,30)
		self.line6 = QLineEdit("",self.tab1)
		self.line6.setGeometry(160,250,60,30)
		self.line_c = QLineEdit("",self.tab1)
		self.line_c.setGeometry(160,290,60,30)
		self.line_n = QLineEdit("",self.tab1)
		self.line_n.setGeometry(160,330,60,30)
		self.line_mpi = QLineEdit("",self.tab1)
		self.line_mpi.setGeometry(160,370,60,30)

		self.LoadFile()
	   
		# Claiming parameters
		self.v_name,self.nN,self.sigfac,self.h5,self.nEigs,self.transpose,self.concat_num,self.n,self.mpi \
			= None,None,None,None,None,None,None,None,None
		self.run_button()

		self.process = QTextEdit(self.tab1, readOnly=True)
		self.process.ensureCursorVisible()
		self.process.setLineWrapColumnOrWidth(500)
		self.process.setLineWrapMode(QTextEdit.FixedPixelWidth)
		self.process.setFixedWidth(360)
		self.process.setFixedHeight(200)
		self.process.move(500, 30)		

		sys.stdout = Stream(newtext=self.onUpdateText)
		self.tabs.addTab(self.tab1, "Main")
		self.layout.addWidget(self.tabs) 
		self.setLayout(self.layout) 

	def onUpdateText(self, text):
		"""Write console output to text widget."""
		cursor = self.process.textCursor()
		cursor.movePosition(QTextCursor.End)
		cursor.insertText(text)
		self.process.setTextCursor(cursor)
		self.process.ensureCursorVisible()

	# Open File Function
	def open_dialog(self):
		options = QFileDialog.Options()
		runPath = "/home/hui/Git-test/gui_test/"
		fileName, _ = QFileDialog.getOpenFileName(self.tab1,"Open Dialogue", runPath, "All Files (*);;Python Files (*.py);;Image Files (*jpeg, *.png)", options=options)
		if fileName:
			print('Data file ' + fileName + ' is selected')
			self.popup_text(fileName,170,10,300,30)
			self.file_path = fileName
			self.parameter_box("h5",10,50,40,30)
			button_variable=QPushButton("Variable Name:",self.tab1)
			button_variable.setGeometry(10,90,110,30)
			button_variable.clicked.connect(self.pulldown_v)
			button_variable.show()
			self.checkbox_h5_true = QCheckBox(self.tab1)
			self.checkbox_h5_false = QCheckBox(self.tab1)
			self.checkbox_h5_true.setGeometry(160,50,60,30)
			self.checkbox_h5_false.setGeometry(250,50,60,30)
			self.checkbox_h5_true.setText("True")
			self.checkbox_h5_false.setText("False")
			self.checkbox_h5_true.show()
			self.checkbox_h5_false.show()
			self.checkbox_h5_true.stateChanged.connect(self.h5_uncheck)
			self.checkbox_h5_false.stateChanged.connect(self.h5_uncheck)

	def h5_uncheck(self,state):
		if state == Qt.Checked:
			if self.sender() == self.checkbox_h5_true:
				self.checkbox_h5_false.setChecked(False)
			elif self.sender() == self.checkbox_h5_false:
				self.checkbox_h5_true.setChecked(False)

	def transpose_uncheck(self,state):
		if state == Qt.Checked:
			if self.sender() == self.checkbox_transpose_true:
				self.checkbox_transpose_false.setChecked(False)
			elif self.sender() == self.checkbox_transpose_false:
				self.checkbox_transpose_true.setChecked(False)
	
	def pulldown_v(self):
		if self.checkbox_h5_true.isChecked():
			import h5py
			f = h5py.File(self.file_path,'r')
			self.v_list = list(f.keys())
		elif self.checkbox_h5_false.isChecked():
			from scipy.io import loadmat
			f = loadmat(str(self.file_path))
			self.v_list = list(f.keys())
		else:
			print("Please select 'True' or 'False' for the h5 field.")
			return  # Return without further processing
		self.line1 = QComboBox(self.tab1)
		self.line1.setGeometry(160,90,120,30)
		self.line1.addItems(self.v_list[::-1])
		self.line1.show()

	def LoadFile(self):
		button_load= QPushButton("Open Data File", self.tab1)
		button_load.setGeometry(10,10,150,30)
		button_load.clicked.connect(self.open_dialog)
	   
	def popup_text(self,a,x,y,w,h):
		line_file = QLineEdit(a,self.tab1)
		line_file.setGeometry(x,y,w,h)
		line_file.show()

	def parameter_box(self,a,x,y,w,h):
		label = QLabel(a, self.tab1)
		label.setGeometry(x,y,w,h)
		label.setFrameStyle(QFrame.Panel | QFrame.Raised)
		label.setLineWidth(2)
		label.setMidLineWidth(2)
		label.show()
		
	def click_save(self):
		self.h5 = self.checkbox_h5_true.isChecked()
		self.v_name = self.line1.currentText()
		self.transpose = self.checkbox_transpose_true.isChecked()
		self.nN = int(self.line4.text())
		self.sigfac = float(self.line5.text())
		self.nEigs = int(self.line6.text())
		self.concat_num = int(self.line_c.text())
		self.n = int(self.line_n.text())
		self.mpi = int(self.line_mpi.text())
		text = " Data = {} \n Variable Name = {} \n h5 = {} \n Transpose = {} \n nN = {} \n Sigma Factor = {} \n nEigs = {}".format(self.file_path,self.v_name,self.h5,self.transpose,self.nN,self.sigfac,self.nEigs)
		print(text)

	def run_button(self):
		button = QPushButton("Run",self.tab1)
		button.setGeometry(700,240,150,30) 
		button.clicked.connect(self.click_save)
		button.clicked.connect(self.click_run)

	def click_run(self):
		from misc_tools import write_h5
		import os
		import subprocess
		
		xyz = read_h5(self.file_path,self.v_name,self.h5,self.transpose)
		
		sq_code = cxfel_root+"/misc_tools/prepare_squared_distance_file_.py"
		num_worker = self.mpi
		
		data_file = 'data_file_for_sna.h5'
		variable_name = self.v_name
		N,D = xyz.shape
		c = self.concat_num
		h5 = 'True'
		if (not self.h5): h5 = 'False'
		transpose = 'False'
		if (self.transpose): transpose = 'True'
		n = self.n
		nN = self.nN
		sqDist_file = 'sqDist.h5'
		cleanup = 'True'
		no_block = 'True'
		run_mpi = 'True'
		if (num_worker<2): run_mpi = 'False'
		
		os.link(self.file_path,data_file)
		
		subprocess.run(["mpiexec","-N",str(num_worker),"python",sq_code,data_file,variable_name,str(N),str(D),'dSq',str(c),h5,transpose,str(n),str(nN),sqDist_file,cleanup,no_block,run_mpi])
		print("sqDist Done")
		
		ferguson_code = cxfel_root+"/ferguson/run_ferguson_.py"
		subprocess.run(["python",ferguson_code,sqDist_file])
		print("Ferguson Analysis Done")
		plot_button_ferg= QPushButton("Ferguson Result",self.tab1)
		plot_button_ferg.setGeometry(700,280,150,30)
		plot_button_ferg.clicked.connect(self.plot_ferguson)
		plot_button_ferg.show()
		
		sigma_factor = self.sigfac
		nEigs = self.nEigs
		alpha = 1.0
		diffmap_code = cxfel_root+"/diffmap/run_diffmap_.py"
		subprocess.run(["python",diffmap_code,sqDist_file,str(sigma_factor),str(nEigs),str(alpha)])
		print("Diffusion Map Done")

		self.eigVal = read_h5("eigVec_eigVal.h5",'eigVal')
		self.eigVec = read_h5('eigVec_eigVal.h5','eigVec')
		mu = (self.eigVec[:,0])*(self.eigVec[:,0])
		psi = self.eigVec[:,1:].T/self.eigVec[:,0]
		write_h5("mu_psi.h5",mu,'mu')
		write_h5("mu_psi.h5",psi,'psi')
		plot_button_eigVal = QPushButton("Eigenvalue",self.tab1)
		plot_button_eigVal.setGeometry(700,320,150,30)
		plot_button_eigVal.clicked.connect(self.plot_eigVal)
		plot_button_eigVal.show()	

		self.line_eigv1 = QLineEdit("",self.tab1)
		self.line_eigv1.setGeometry(500,325,40,25)
		self.line_eigv1.show()
		self.parameter_box("Eigenvector Index 1: ",360,320,130,30)
		self.line_eigv2 = QLineEdit("",self.tab1)
		self.line_eigv2.setGeometry(500,365,40,25)
		self.line_eigv2.show()
		self.parameter_box("Eigenvector Index 2: ",360,360,130,30)
		self.line_eigv3 = QLineEdit("",self.tab1)
		self.line_eigv3.setGeometry(500,405,40,25)
		self.line_eigv3.show()
		self.parameter_box("Eigenvector Index 3: ",360,400,130,30)

		plot_button_1d = QPushButton("Display 1D",self.tab1)
		plot_button_1d.setGeometry(700,360,150,30)
		plot_button_1d.clicked.connect(self.plot_1d)
		plot_button_1d.show()

		plot_button_2d = QPushButton("Display 2D",self.tab1)
		plot_button_2d.setGeometry(700,400,150,30)
		plot_button_2d.clicked.connect(self.plot_2d)
		plot_button_2d.show()

		plot_button_3d = QPushButton("Display 3D",self.tab1)
		plot_button_3d.setGeometry(700,440,150,30)
		plot_button_3d.clicked.connect(self.plot_3d)
		plot_button_3d.show()
		
	def plot_eigVal(self):
		from diffmap import plot_eigVal
		import matplotlib.pyplot as plt
		
		figure_name = plot_eigVal('eigVec_eigVal.h5')
		plt.close()
		
		self.tab2 = QWidget()
		label = QLabel(self.tab2)
		label.setGeometry(100,0,900,550)
		pixmap = QPixmap(figure_name).scaledToWidth(600)
		
		label.setPixmap(pixmap)
		label.move(0,0)
		label.show()
		
		self.tabs.addTab(self.tab2, "eigVal")

	def plot_1d(self):
		from diffmap import plot1D
		import matplotlib.pyplot as plt
		from misc_tools import write_h5
		import os
		
		ev1 = int(self.line_eigv1.text())
		ev2 = int(self.line_eigv2.text())
		ev3 = int(self.line_eigv3.text())
		figure_name = plot1D('eigVec_eigVal.h5',[ev1,ev2,ev3])
		plt.close()
		
		self.tab2 = QWidget()
		label = QLabel(self.tab2)
		label.setGeometry(100,0,900,550)
		pixmap = QPixmap(figure_name).scaledToWidth(900)
		
		label.setPixmap(pixmap)
		label.move(0,0)
		label.show()
		
		self.tabs.addTab(self.tab2, "1D Eigenvectors")		

	def plot_2d(self):
		from diffmap import plot2D
		import matplotlib.pyplot as plt
		from misc_tools import write_h5
		import os
		
		eigVec = self.eigVec
		ev1 = int(self.line_eigv1.text())
		ev2 = int(self.line_eigv2.text())
		ev3 = int(self.line_eigv3.text())
		write_h5('colorcode.h5',eigVec[:,1]/eigVec[:,0],'colorcode')
		figure_name = plot2D('eigVec_eigVal.h5',[ev1,ev2,ev3],s=20)
		plt.close()
		os.remove('colorcode.h5')
		
		self.tab2 = QWidget()
		label = QLabel(self.tab2)
		label.setGeometry(100,0,900,550)
		pixmap = QPixmap(figure_name).scaledToWidth(900)
		
		label.setPixmap(pixmap)
		label.move(0,0)
		label.show()
		
		self.tabs.addTab(self.tab2, "2D Manifold")
		
	def plot_3d(self):
		from diffmap import plot3D
		import matplotlib.pyplot as plt
		from misc_tools import write_h5
		import os
		
		eigVec = self.eigVec
		ev1 = int(self.line_eigv1.text())
		ev2 = int(self.line_eigv2.text())
		ev3 = int(self.line_eigv3.text())
		write_h5('colorcode.h5',eigVec[:,1]/eigVec[:,0],'colorcode')
		figure_name = plot3D('eigVec_eigVal.h5',[ev1,ev2,ev3],s=20)
		plt.close()
		os.remove('colorcode.h5')
		
		self.tab2 = QWidget()
		label = QLabel(self.tab2)
		label.setGeometry(100,0,900,550)
		pixmap = QPixmap(figure_name).scaledToHeight(400)
		
		label.setPixmap(pixmap)
		label.move(0,0)
		label.show()
		
		self.tabs.addTab(self.tab2, "3D Manifold")
		
	def plot_ferguson(self):
		self.tab2 = QWidget()
		label = QLabel(self.tab2)
		label.setGeometry(100,0,900,550)
		pixmap = QPixmap('ferguson.jpg').scaled(700,480)
		
		label.setPixmap(pixmap)
		label.move(0,0)
		label.show()
		
		self.tabs.addTab(self.tab2, "Ferguson Result")
		
	def close_current_tab(self, i):

		# if there is only one tab
		if self.tabs.count() < 2:
			# do nothing
			super(QWidget).close()
			return

		# else remove the tab
		self.tabs.removeTab(i)



# create pyqt5 app 
App = QApplication(sys.argv) 

# create the instance of our Window 
window = Window() 
# start the app 
sys.exit(App.exec())
