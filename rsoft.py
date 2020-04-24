import send2trash

# calculate mode index, mode field, and bend loss using Rsoft Beamprop
# tested with Rsoft v6.0.5
# defaults assume bsimw32.exe is in 'c:/rsoft/bin/' and working folder 'c:/temp/pyrsoft/'

def writeipf(nn,res,limits,folder):
    xmin,xmax,ymin,ymax = limits
    nx,ny = nn.shape
    with open(folder+'pyindex.ipf','w') as f:
        f.write(f'/rn,a,b/nx0/ls1\n/r,qa,qb\n')
        f.write(f'{nx} {xmin} {xmax} 0 OUTPUT_REAL_3D\n')
        f.write(f'{ny} {ymin} {ymax}\n')
        for i,ni in enumerate(nn):
            for j,nij in enumerate(ni):
                f.write(f' {nij-1:.6f}  ') # note: index minus one
            f.write(f'\n')
def writeind(wavelengthinmicrons,nktp,dns,res,limits,folder,lossradius=None):
    calcloss = bool(lossradius)
    if calcloss:
        writeind(wavelengthinmicrons,nktp,dns,res,limits,folder,None)
    xmin,xmax,ymin,ymax = limits
    with open(folder+f"pyindex{'bendloss' if calcloss else ''}.ind",'w') as f:
        f.write(f'alpha = 0\n')
        f.write(f'background_index = 1\n')
        f.write(f'boundary_max = {xmax}\nboundary_max_y = {ymax}\nboundary_min = {xmin}\nboundary_min_y = {ymin}\n')
        f.write(f'char_nmax = {nktp+dns}\nchar_nmin = {nktp}\n')
        f.write(f'cover_index = 1\n')
        f.write(f'delta = 1\n')
        f.write(f'dimension = 3\n')
        f.write(f'eim = 0\n')
        f.write(f'free_space_wavelength = {wavelengthinmicrons}\n')
        f.write(f'grid_size = {res}\ngrid_size_y = {res}\n')
        f.write(f'height = 2\n')
        f.write(f'width = 2\n')
        f.write(f'idbpm_convergence_warning = 0\n')
        f.write(f'index_min = {nktp}\n')
        f.write(f'k0 = (2*pi)/free_space_wavelength\n')
        if calcloss:
          f.write(f'launch_file = tmp.m00\nlaunch_type = LAUNCH_FILE\n')
        else:
          f.write(f'launch_position = .5\nlaunch_position_y = -.5\nlaunch_type = LAUNCH_GAUSSIAN\nlaunch_width = .5\n')
        f.write(f'monitor_step_size = 10\n')
        f.write(f'neff_tol = 1e-008\n')
        f.write(f'profile_type = PROF_USER_1\n')
        f.write(f'sim_tool = ST_BEAMPROP\n')
        f.write(f'slice_display_mode = DISPLAY_CONTOURMAPXY\n')
        f.write(f'slice_step_size = 100\n')
        f.write(f'step_size = 1\n')
        f.write(f'step_size_idbpm = 1\n')
        f.write(f'structure = STRUCT_CHANNEL\n')
        f.write(f'\n\n')
        f.write(f'user_profile 1\n')
        f.write(f'   type = UF_DATAFILE\n')
        f.write(f'   filename = pyindex.ipf\n')
        f.write(f'end user_profile\n')
        f.write(f'\n\n')
        f.write(f'segment 1\n')
        if calcloss:
            f.write(f'   simulated_bend = 1\n')
            f.write(f'   simulated_bend_radius = {lossradius}\n')
        f.write(f'   begin.x = 0\n begin.z = 0\n')
        f.write(f'   end.x = 0 rel begin segment 1\n   end.z = 10000 rel begin segment 1\n')
        f.write(f'end segment\n\n\n')
        if calcloss:
            f.write(f'pathway 1\n  1\nend pathway\n\n\n')
            f.write(f'monitor 1\n  pathway = 1\n monitor_type = MONITOR_FILE_POWER\n   monitor_tilt = 0\n    monitor_mode = 0\n    monitor_file = tmp.m00\nend monitor\n\n\n')
            f.write(f'launch_field 1\n launch_pathway = 1\n  launch_type = LAUNCH_FILE\n   launch_tilt = 0\n launch_mode = 0\n launch_mode_radial = 1\n  launch_file = tmp.m00\nend launch_field\n\n\n')
def runrsoft(nummodes=1,indexprofile=False,bendloss=False,workingfolder='c:/temp/pyrsoft/',rsoftfolder='c:/rsoft/bin/',logfile='bsimw32pylog.txt'):
    import subprocess
    def run(command,logfile):
        log = open(logfile, 'w')
        # print('    running:',command)
        process = subprocess.Popen(command.split(), cwd=workingfolder, stdout=log, stderr=subprocess.PIPE)
        out,err = process.communicate()
        if err: print('rsoft.py error:',err)
    if bendloss:
        runrsoft(bendloss=False,workingfolder=workingfolder,rsoftfolder=rsoftfolder,logfile=logfile) # need to generate mode.m00 for input to 
        run( rsoftfolder+'bsimw32 pyindexbendloss.ind prefix=tmp wait=0', workingfolder+logfile )
    else:
        if indexprofile:
            run( rsoftfolder+'bsimw32 pyindex.ind prefix=tmp index_profile=1 wait=0', workingfolder+logfile )
        run( rsoftfolder+f'bsimw32 pyindex.ind prefix=tmp mode_set=0-{nummodes-1} mode_method=1 wait=0', workingfolder+logfile )
def modecalc(nn,wl,n0,dn0,res,limits,nummodes=1,lossradius=None,folder = 'c:/temp/pyrsoft/'):
    import os
    deletefolder(folder)
    writeipf(nn,res,limits,folder=folder)               # create pyindex.ipf
    writeind(wl,n0,dn0,res,limits,folder,lossradius)    # create pyindex.ind (and pyindexbendloss.ind if needed)
    if os.path.isdir('c:/rsoft/bin/'):
        runrsoft(nummodes=nummodes,bendloss=bool(lossradius),workingfolder=folder)
        if bool(lossradius):
            return loadmon(folder)
        ns,ees = loadmodes(folder)
        return ns,ees
    else:
        print('rsoft not found')
        return None,None
def loadmon(folder,file='tmp.mon'):
    return np.loadtxt(folder+file,delimiter=' ',skiprows=5)
    # print(a.shape,a[0],a[-1])
def loadmodes(folder,name='tmp'):
    import os
    def file(i):
        return folder+name+f'.m{i:02d}'
    def header(n,file):
        with open(file,'r') as f:
            return [f.readline() for i in range(n)]
    ns,ees,i = [],[],0
    while os.path.isfile(file(i)):
        aa = header(4,file(i))
        nx,xmin,xmax,z,outputtype,n,nimag = aa[-2].split() # last one is imaginary index?
        ny,ymin,ymax = aa[-1].split()
        ee = np.loadtxt(file(i),skiprows=4)
        ns,ees,i = ns+[float(n)],ees+[ee],i+1
    return ns,ees
def deletefolder(folder): # remove old files before running in order to catch bsimw32.exe failures
    import os
    path = os.path.abspath(folder)
    if not os.path.exists(path): print(path,'not found')
    send2trash.send2trash(path)
    os.mkdir(path)
if __name__ == '__main__':

    # define wavelength, bulk index, index step, grid resolution, grid size (x0,x1,y0,y1)
    wavelength,n0,dn0,gridresolution,gridlimits = 1.550,1.8,0.02,1.0,(-10,10,-20,10)

    # create index disribution
    import numpy as np
    nn = n0*np.ones((21,31))
    nn[8:13,10:] += dn0
    nn[:,20:] = 1
    # from wave import Wave2D
    # Wave2D(nn,xs=np.linspace(-1,1,21),ys=np.linspace(-2,1,31)).plot()

    # calculate single mode
    ns,ees = modecalc(nn,wavelength,n0,dn0,gridresolution,gridlimits)
    # from wave import Wave2D
    # Wave2D(ees[0],xs=np.linspace(-1,1,21),ys=np.linspace(-2,1,31)).plot()

    # calculate multimode modes
    ns,ees = modecalc(nn,wavelength,n0,dn0,gridresolution,gridlimits,nummodes=3)
    # from wave import Wave2D
    # Wave2D(ees[-1],xs=np.linspace(-1,1,21),ys=np.linspace(-2,1,31)).plot()
    
    # calculate bend loss, returns 2xn array of transmission vs distance
    a = modecalc(nn,wavelength,n0,dn0,gridresolution,gridlimits,lossradius=800)
    # from wave import Wave
    # Wave(*a.T[::-1]).plot(x='distance (um)',y='transmission')
