import os

# Perform initialization &
#   add cxfel code to system path.
cxfel_root = os.environ['CXFEL_ROOT']
startup_file = cxfel_root+'/misc_tools/startup.py'
exec(open(startup_file).read())

from diffmap import analyze as diffmap_analyze,plot2D
from ferguson import analyze as ferguson_analyze
from misc_tools import prepare_squared_distance_file,read_h5,write_h5

# Read demo data, & set algorithmic parameters.
data_file='DM_Spiral.mat';variable_name='Y';N=2000;D=3;
h5=False;transpose=True;
os.link(cxfel_root+'/data/'+data_file,'./'+data_file)

yRow_yCol_yVal_file = 'sqDist.h5'
nN = 100
sigma_factor = 2.0
nEigs = 20
alpha = 1.0

# Calculate symmetrized, truncated, pairwise squared Euclidean distances using
# the Shift-and-Add library.
c=1;n=500;cleanup=True;no_block=True;run_mpi=False;
prepare_squared_distance_file(data_file,variable_name,N,D,measure_type='dSq',c=c,\
  h5=h5,transpose=transpose,n=n,nN=nN,sqDist_file=yRow_yCol_yVal_file,cleanup=cleanup,\
  no_block=no_block,run_mpi=run_mpi)
os.remove(data_file)

# Calculate characteristic length scale of the data.
sigma_opt,_ = ferguson_analyze(yRow_yCol_yVal_file)

# Calculate Diffusion Map embedding.
sigma = sigma_factor*sigma_opt
h5_eigVec_eigVal = diffmap_analyze(yRow_yCol_yVal_file,sigma,nEigs,alpha)

# Visualize the manifold.
eigVec = read_h5(h5_eigVec_eigVal,'eigVec')

# tau-fit the open 1d manifold
write_h5('fit_open_1d_manifold_3d_input.mat',
  (eigVec[:,1:4]/eigVec[:,0:1]).T,'psi')

library_path = cxfel_root + r'/open_1d_manifold'
with open('run_me.m', 'w') as f:
  f.write(f'addpath("{library_path}");\n')
  f.write('fit_open_1d_manifold_3d;\n')
os.system('octave run_me.m > NUL')

import platform
is_window = platform.system()=='Windows'
if not is_window: os.remove('NUL')

tau = read_h5('a_b_tau_result.mat','tau',h5=False,transpose=True)
os.remove('fit_open_1d_manifold_3d_input.mat')
os.remove('run_me.m')
os.remove('a_b_tau_result.mat')

# colored based on parametric fit
write_h5('colorcode.h5',tau,'colorcode')
figure_name = plot2D(h5_eigVec_eigVal,[1,2,3],s=20)
os.rename(figure_name,'diffmap_2D_tau_colored.jpg')
