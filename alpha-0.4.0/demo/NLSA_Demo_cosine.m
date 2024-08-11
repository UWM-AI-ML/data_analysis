# Perform initialization &
#   add cxfel code to system path.
cxfel_root = getenv('CXFEL_ROOT')
addpath([cxfel_root '/wrappers'])
addpath([cxfel_root '/misc_tools'])
addpath([cxfel_root '/nlsa'])

##### System Specification #####
t_shift = 5800;
t_period = 500;
y_shift = 0;
y_scale = 1;
testFunc = @(t) (cos(2*pi*(t-t_shift)/t_period)+y_shift)*y_scale;
D = 1;

##### Simulation Specification #####
N = 11600;
delta_t = 50e-3; % fs

arg_list = argv();
command = sprintf('sigma_jitter = %s',arg_list{1});
eval(command)

##### samples #####
# k and jitter are in unit of timesteps:
k = ([1:N]'-1);
jitter = randn(N,1)*sigma_jitter/delta_t;
 
T_jitter_free = testFunc(k);
T_jittered = testFunc(k+jitter);
 
T_jittered_saved = T_jittered;

save('T_jittered_saved.mat','T_jittered_saved','-v7')

# Read demo data, & set algorithmic parameters.
data_file='T_jittered_saved.mat';
variable_name='T_jittered_saved',h5='False',transpose='False'


yRow_yCol_yVal_file = 'sqDist.h5'
nN = 1000
sigma_factor = 2.0
nEigs = 30
alpha = 1.0
c = 5800

# Calculate symmetrized, truncated, pairwise squared Euclidean distances using
# the Shift-and-Add library.
n=500,cleanup='True',no_block='True',run_mpi='False',num_worker=1
run_prepare_squared_distance_file_py(data_file,variable_name,N,D,'dSq',c,...
h5,transpose,n,nN,yRow_yCol_yVal_file,cleanup,no_block,run_mpi,num_worker)



# Calculate characteristic length scale of the data.
run_ferguson_py(yRow_yCol_yVal_file)
load('sigma_opt.h5','sigma_opt')


# Calculate Diffusion Map embedding.
run_diffmap_py(yRow_yCol_yVal_file,sigma_factor,nEigs,alpha)

load('eigVec_eigVal.h5','eigVec')
eigVec = eigVec';
mu = eigVec(:,1).^2;
psi = bsxfun(@rdivide,eigVec(:,2:end),eigVec(:,1));

# Calculate pairwise dot products using
# the Shift-and-Add library.

cleanup='False',no_block='True',run_mpi='False',num_worker=1
run_sna_py(data_file,variable_name,N,D,'dot',c,...
h5,transpose,n,nN,yRow_yCol_yVal_file,cleanup,no_block,run_mpi,num_worker)

delete('.sna_run_info')
[filepath,name,ext] = fileparts(data_file);
run_post_sna_cleanup_py('data_chunk',[name ext],n,c)
if (c>1), run_post_sna_cleanup_py('pipe','dummy',n,c), end

# nlsa.
ell = nEigs;
num_copy = 2;
if (mod(c+num_copy,2)==1), num_copy = 1; end

load(data_file,variable_name)
eval(sprintf('X1 = %s'';',variable_name))

################################################################################
# Treating nlsa as an external library
# [U_NLSA,S_NLSA,V_NLSA] = extract_topos_chronos(ell,X1,mu,psi,D,N,n,c,num_copy);
save('extract_topos_chronos_input.mat','ell','X1','mu','psi','D','N','n','c','num_copy')
system(['echo addpath\(\"' cxfel_root '/nlsa\"\) > run_me.m']);
system(['echo run extract_topos_chronos.m       >> run_me.m']);
system('octave run_me.m > /dev/null');
load('U_S_V.mat','U','S','V'); U_NLSA = U; S_NLSA = S; V_NLSA = V; clear U S V
delete('extract_topos_chronos_input.mat','run_me.m','U_S_V.mat')
################################################################################

run_post_sna_cleanup_py('square','dummy',n,c)

U_NLSA = real(U_NLSA);
S_NLSA = real(diag(S_NLSA));
V_NLSA = real(V_NLSA);

##### region of interest (both for display and for fitting) #####
x_time = [0:N-c+1-num_copy];
ROI = (c+num_copy)/2+x_time;
T_jittered = T_jittered(ROI,:);
T_jitter_free = T_jitter_free(ROI,:);

# Fourier analysis #
timeWindow = length(ROI);
nFFT = timeWindow;
[normalizedFreq,fourierOrder] = fourierPacking(nFFT);
freq = normalizedFreq*1000/(2*delta_t);
load([cxfel_root '/misc_tools/' 'hann200000.mat'],'myFilter');
mask = interp1([0:200000-1]/(200000-1),myFilter,[0:timeWindow-1]/(timeWindow-1));

y1 = T_jitter_free(:,1);
y2 = V_NLSA(1:timeWindow,1);
y1_masked = y1.*mask';
y2_masked = y2.*mask';

myFFT1 = fft(y1_masked,nFFT);
myFFT1 = abs(myFFT1(fourierOrder));
myFFT2 = fft(y2_masked,nFFT);
myFFT2 = abs(myFFT2(fourierOrder));

minFreq = 8;
maxFreq = 102;

##### graphics-related #####

hFigure = figure(1);
set(hFigure,'color','w')
set(hFigure,'resize','off')
Pix_SS = get(0,'screensize');
screenWidth = Pix_SS(3);
screenHeight = Pix_SS(4);
pos = [10 900 screenWidth/2 0.8*screenHeight];
try
  warning('off','Octave:abbreviated-property-match')
catch
end
set(hFigure,'pos',pos)

figure(hFigure)
 
hsp = subplot(2,2,1);
x = x_time;             my_xlabel = 'Time (\Deltat)';
y = T_jitter_free(:,1); my_ylabel = '';
y_min = min(y); y_max = max(y);
my_title = 'Jitter-free Signal';
plotRF(hsp,x,y,my_xlabel,my_ylabel,my_title,'b-')
set(hsp,'ylim',[y_min,y_max]+[-1,1]*0.1*(y_max-y_min))

hsp = subplot(2,2,2);
x = x_time;             my_xlabel = 'Time (\Deltat)';
y = T_jittered(:,1);    my_ylabel = '';
y_min = min(y); y_max = max(y);
my_title = 'Input Signal to NLSA';
plotRF(hsp,x,y,my_xlabel,my_ylabel,my_title,'b.')
hLine = get(hsp,'children');
set(hLine,'markerSize',4)
set(hsp,'ylim',[y_min,y_max]+[-1,1]*0.1*(y_max-y_min))

hsp = subplot(2,2,3);
num_S = min([nEigs c*D]);
x = [1:num_S];          my_xlabel = 'Singular Value #';
y = S_NLSA(1:num_S);    my_ylabel = 'Magnitude (A.U.)';
y = y/y(1);
y_min = 0.0; y_max = 1.0;
my_title = 'Singular Value Spectrum';
plotRF(hsp,x,y,my_xlabel,my_ylabel,my_title,'b-o')
set(hsp,'xlim',[0.8 num_S],'ylim',[y_min,y_max],'xTick',[5:5:num_S])

hsp = subplot(2,2,4);
ofInterest = (freq>minFreq)&(freq<maxFreq);
x = freq(ofInterest);
f1 = myFFT1(ofInterest).^2;
f2 = myFFT2(ofInterest).^2;
f1 = f1/max(f1);
f2 = f2/max(f2);
my_title = 'Power Spectrum';
my_xlabel = 'Frequency (THz)';
my_ylabel = '';
plotRF(hsp,x,f1,my_xlabel,my_ylabel,my_title,'b-o')
addplotRF(hsp,x,f2,'g-x')
set(hsp,'ylim',[0,1.2])
legend({'Jitter-free Signal','Chronogram'},'location','north','orientation','horizontal','box','off');

myJPEG = sprintf('NLSA_Demo_cosine_sigma_jitter_%.2f.jpg',sigma_jitter);
print(myJPEG)
