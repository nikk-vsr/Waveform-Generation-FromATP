import matplotlib
import warnings
# Make sure that we are using QT5
matplotlib.use('Qt5Agg')                    # backend for matplotlib
from PyQt5 import QtWidgets                 # to get the GUI components widget is imported
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib import colors as mcolors
import numpy as np
import math
import Datamanipulation 
import GlobalVar as G

def Initialization():

 
    G.Signal_Values= [0 for i in range(G.No_Signals)]             # To store the dictionary values from Signal data dictionary G.Signal_Values[i][0]--> gives the Signal data to plot for the first signal

    G.Signals_Segments=  [0 for i in range(G.No_Signals)]         #intializing Signal Segments list

    for i in range(0,G.No_Signals):
        G.Signal_Values[i]= list(G.Signals[i].values())                                              # Signal values list eg [[3,1],[3,1]...]
        G.Signals_Segments[i]= [ [[0,0],[0,0]] for k in range(len(G.Signal_Values[i][0])) ]          # intializing the segments for each signal waveform

    G.Xticks_Wait=[0 for i in range(len(G.Wait)+1) ]              # Eg:- G.Xticks_Wait--> [0,3,3,6,1,1,1,1....] 0 is appended to include Time=0 instant  

    for i in range(1,len(G.Xticks_Wait)):
        G.Xticks_Wait[i]= G.Xticks_Wait[i-1]+ G.Wait[i-1]                     

    G.Signal_Wait=[[] for i in range(G.No_Signals)]                  # Each signal wait times are appended in to this list
    G.Rev_CumSum= [0 for i in range(G.No_Signals)]                   # reverse cummulative sum of wait for each signal is stored in this list
    G.Concetanated_Segments= [0 for i in range(G.No_Signals)]        # plotable coordinates are generated and stored in this list
    G.SignalAction=[ 0 for i in range(G.No_Signals)]                 # stores the indices of first find of Signal in Action data
    G.SignalPendingWait=[0 for i in range(G.No_Signals)]             # finds the wait time wrt action for the next actions after the first finding of signal,

    G.Color_Index=[[] for i in range(G.No_Signals)]
    
def CumSumWait():

    for k in range(G.No_Signals):
        for i in range(0,len(G.Signal_Values[k][0])):
              G.Signal_Wait[k].append(G.Signal_Values[k][0][i][0])

        G.Rev_CumSum[k]= np.cumsum(G.Signal_Wait[k][::-1])[::-1]            
        G.Rev_CumSum[k]= np.append(G.Rev_CumSum[k],0)     

def SegmentConvFun(a,b):                  #b--> represents Signal here

    for i in range(0,len(a)):             #len(a) represents no of cordinate pairs of signal values in Signal dictionary     
        
        G.Signals_Segments[b][i][0][0]= sum(G.Wait)-G.Rev_CumSum[b][i]
        G.Signals_Segments[b][i][0][1]= a[i][1]
        G.Signals_Segments[b][i][1][0]= sum(G.Wait)-G.Rev_CumSum[b][i+1]
        G.Signals_Segments[b][i][1][1]= a[i][1]

def ConcetanatedConvFun():
    
    for k in range(0,G.No_Signals):
        SegmentConvFun(G.Signal_Values[k][0],k)                                 #K- varies with Signal
     
        for p in range(0,len(G.Signals_Segments[k])):
            G.Signals_Segments[k][p]=G.Signals_Segments[k][p][::-1]
        
        G.Signals_Segments[k]=G.Signals_Segments[k][::-1]                         # reversed because signal data is plotted reversely           
        last_element=G.Signals_Segments[k][-1]                                  # Last element is appended again as it is needed to get the last action color
        G.Signals_Segments[k].append(last_element)                    

        #concatenates the segments to form continous line
        if len(G.Signals_Segments[k]) > 1 :     
            G.Concetanated_Segments[k] = np.concatenate([G.Signals_Segments[k][:-1], G.Signals_Segments[k][1:]], axis=1)
        else:
            G.Concetanated_Segments[k]=G.Signals_Segments[k]

#-------------------------------------------------------------------------------------------------------------------------
''' Finds the total number of elements in a nested list-Wait'''
def LenofNestedList(ListofElem):
    count = 0
    if type(ListofElem) is list:
    # Iterate over the list
        for elem in ListofElem:
        # Check if type of element is list
            if type(elem) == list:  
            # Again call this function to get the size of this element
                count += LenofNestedList(elem)
            else:
                count += 1
    else:
        count=1
    return count
#-------------------------------------------------------------------------------------------------------------------------


def Signal_PendingWait():

    for i in range(0,G.No_Signals):
 
        G.SignalAction[i]= list(G.Signal_Indices[i].values())[0][:1]
        temp_var= G.No_Actions-G.SignalAction[i][0][0]-1
        if temp_var !=0 :
            G.SignalPendingWait[i]=G.list_Wait[-temp_var:]                  # latest update

   

#--------------------------------------------------------------------------------------------------------------------------
'''stores wait time leftover in the same action'''          
def list_WaitSignals(a,b):                                
    tempo=[]
    tempo_ramp=[]

    for n in range(b,len(G.Actions[a])):
        if G.Actions[a][n][0]== "Wait":
 
            tempo.append(G.Actions[a][n][2])
        if G.Actions[a][n][0]=="Ramp":
            if (G.Actions[a][n][2][0] <G.Actions[a][n][2][1]):                       # for ramp up 
                for j in range(G.Actions[a][n][2][0],G.Actions[a][n][2][1],G.Actions[a][n][2][2]):
                   tempo_ramp.append(G.Actions[a][n][5])
                tempo.append(tempo_ramp)
            else:                                                                    #for ramp down
                for k in range(G.Actions[a][n][2][0],G.Actions[a][n][2][1],-G.Actions[a][n][2][2]):
                    tempo_ramp.append(G.Actions[a][n][5])
                tempo.append(tempo_ramp)
   
    if len(tempo)>1:
        return tempo
    else:
        return(tempo[0])
    
def Same_ActionWait():
    '''append same action wait time as first element of signal pending wait'''
    ''' if Signal_PendingWait is [3,1],[[3,1],[3,1]] '''
    for k in range(0,G.No_Signals):
        if (G.No_Actions- 1-G.SignalAction[k][0][0]) == 0 :
            G.SignalPendingWait[k]= [list_WaitSignals(G.SignalAction[k][0][0],G.SignalAction[k][0][1])]                   # if same action wait is [[3,1],[3,1],[3,1]]'''
        else:
            G.SignalPendingWait[k].insert(0, list_WaitSignals(G.SignalAction[k][0][0],G.SignalAction[k][0][1]))           #inserts pending wait in the same action
                                                                                                                #net wait would be [[[3,1],[3,1],[3,1]],[3,1],[3,1],[3,1]]  
#-----------------------------------------------------------------------------------------------------------------------------------    
 
def Color_Indexing():

    global Colors_List
    
    Colors_List=['gold','r','lawngreen','b','c','fuchsia','k','g','coral','lightslategray', 'gold','r','lawngreen','b','c','fuchsia','k','g','coral','lightslategray','gold','r','lawngreen','b','c','fuchsia','k','g','coral','lightslategray']
 
    for m in range(G.No_Signals):
        firstindex=0
        for n in range(len(G.SignalPendingWait[m])-1,-1,-1):         #reverse step
            
            if LenofNestedList(G.SignalPendingWait[m][n])==1:
                G.Color_Index[m].append(Colors_List[firstindex])
                     
            else:
                for p in range(LenofNestedList(G.SignalPendingWait[m][n])):
                    G.Color_Index[m].append(Colors_List[firstindex])
                    
            firstindex=firstindex+1
   
#-----------------------------------------------------------------------------------------------------------------------------------
                               

class ScrollableWindow(QtWidgets.QMainWindow):
    def __init__(self, fig):
        self.qapp = QtWidgets.QApplication([])

        QtWidgets.QMainWindow.__init__(self)
        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.widget.layout().setContentsMargins(0,0,0,0)
        self.widget.layout().setSpacing(0)
        self.windowSize = (1200, 800)
        self.fig = fig
        self.canvas = FigureCanvas(self.fig)
        self.canvas.draw()
        self.scroll = QtWidgets.QScrollArea(self.widget)
        self.scroll.setWidget(self.canvas)

        self.setWindowTitle("Waveform") 
        self.nav = NavigationToolbar(self.canvas, self.widget)
        self.widget.layout().addWidget(self.nav)
        self.widget.layout().addWidget(self.scroll)

        self.show()
        exit(self.qapp.exec_()) 

'''delete the unused subplots in the figure'''

def Del_Subplots(a):
    global fig
    global ax
    for j in range(a,G.No_Signals):
        fig.delaxes(ax[j])

            
'''plotting the 2D suplots figure'''
def Waveform_Gen():
    
    global Colors_List

    G.LC= [0 for j in range(G.No_Signals)]
    global fig
    global ax
    figsize_Value= G.No_Signals+5
    if G.No_Signals>4:
        fig,ax= plt.subplots(G.No_Signals,1,constrained_layout=True,figsize= (13.5,figsize_Value))   # constrainedlayout  ensures no overlappnig in the plot
    else:
        fig,ax= plt.subplots(G.No_Signals,1,constrained_layout=True,figsize= (13.5,6))
    warnings.simplefilter("ignore")    
    fig.suptitle(ATPname+ "_"+ TestCaseNo, fontsize=8,fontweight="bold")       # remove this line 

    for j in range(0,G.No_Signals):
            
        if G.No_Signals==1:

            G.LC[j] = LineCollection(G.Concetanated_Segments[0], linewidth=2,colors=G.Color_Index[0])
            ax.add_collection(G.LC[j])
            ax.autoscale()
            ax.set_xlabel('time(s)',fontsize=8)
            ax.set_ylabel(G.Signal_Names[j]+ "  "+ (G.Signal_Units[j]),fontsize=8)
            plt.sca(ax)
        else:
            G.LC[j]= LineCollection(G.Concetanated_Segments[j], linewidth=2,colors=G.Color_Index[j])
            ax[j].add_collection(G.LC[j])
            ax[j].autoscale()
            ax[j].margins(x=0)
            ax[j].set_xlabel('time(s)',fontsize=8)
            ax[j].set_ylabel(G.Signal_Names[j]+ "  "+ (G.Signal_Units[j]),fontsize=8)
            plt.sca(ax[j])                                                        #setting current axes

        ''' to add yticks of ramp '''                                           # can add text over ramp value as well using plt.text()
        justify= G.Signal_Names[j] not in list(G.Ramp_Signal_yticks.keys())

        if justify ==False:
            ExtraTicks=G.Ramp_Signal_yticks[G.Signal_Names[j]]
            plt.yticks(list(plt.yticks()[0])+ ExtraTicks)
                
        plt.xticks(G.Xticks_Wait)
        plt.tick_params(axis='both', labelsize=6)
           
    '''Create colorbar to map colors with action number'''
        
    Colr=(Colors_List[:(G.No_Actions)][::-1])                                         # Stores the list of colors for each action 
    c=np.arange(G.No_Actions+1)
    Action_Names=[ "Action" + str(i) for i in range(0,G.No_Actions)]     
    cmap = ListedColormap(Colr)                                     
    norm = BoundaryNorm(c,len(c)-1)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])                                                                # this line may be ommitted for matplotlib >= 3.1
    cbar=fig.colorbar(sm, ax=ax, ticks=c, orientation='horizontal',aspect=100)
    cbar.set_ticklabels(Action_Names)
    cbar.ax.tick_params(labelsize=8) 
    a = ScrollableWindow(fig) 
    
def Plot_Data(ATPName,TestCaseNum,InputData):                       

    global ATPname
    global TestCaseNo
    
    received_data= Datamanipulation.Generate_Data(InputData)    
   
    G.Plot_Init()

    ATPname= ATPName                                       
    TestCaseNo=TestCaseNum                           
    
    Initialization()
    CumSumWait()
    ConcetanatedConvFun()
    Signal_PendingWait()
    Same_ActionWait()
    Color_Indexing()
    Waveform_Gen()                                                  
  
