import film
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
from glob import glob

def getSubjList():
    subjList = glob('/paulsen/MRx/*/*/*/ANONRAW/*T2-15*.nii.gz')
    subjList.extend(glob('/paulsen/MRx/*/*/*/ANONRAW/*PD-15*.nii.gz'))
    subjListCopy = list()
    subjListCopy.extend(subjList)
    for item in subjList:
        if 'HD_BAD_DATA' in item:
            subjListCopy.remove(item)
    #subjListCopy = ['/paulsen/MRx/PHD_029/0144/48370/ANONRAW/0144_48370_T2-15_4.nii.gz', '/paulsen/MRx/PHD_159/0332/20705/ANONRAW/0332_20705_T2-15_4.nii.gz']
    return subjListCopy

def get_global_sge_script():
    """This is a wrapper script for running commands on an SGE cluster
so that all the python modules and commands are pathed properly"""

    PYTHONPATH = '/paulsen/Experiments/20120813_FILM'
    BASE_BUILDS = '/ipldev/sharedopt/20120722/Darwin_i386/cmtk/bin'
    GLOBAL_SGE_SCRIPT = """#!/bin/bash
echo "STARTED at: $(date +'%F-%T')"
echo "Ran on: $(hostname)"
export PATH=$PATH:{BINPATH}
export PYTHONPATH=$PYTHONPATH:{PYTHONPATH}

echo "========= CUSTOM ENVIORNMENT SETTINGS =========="
echo "export PYTHONPATH=$PYTHONPATH:{PYTHONPATH}"
echo "export PATH=$PATH:{BINPATH}"
echo "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"

## NOTE:  nipype inserts the actual commands that need running below this section.
""".format(PYTHONPATH=PYTHONPATH,BINPATH=BASE_BUILDS)
    return GLOBAL_SGE_SCRIPT

def filmWF():
    filmWF = pe.Workflow(name= 'filmWF')

    ExperimentBaseDirectoryCache = '/paulsen/Experiments/20120813_FILM/FILM_CACHE'
    filmWF.config['execution'] = {
                                         'plugin':'Linear',
                                         #'stop_on_first_crash':'true',
                                         #'stop_on_first_rerun': 'true',
                                         'stop_on_first_crash':'true',
                                         'stop_on_first_rerun': 'false',      ## This stops at first attempt to rerun, before running, and before deleting previous results.
                                         'hash_method': 'timestamp',
                                         'single_thread_matlab':'true',       ## Multi-core 2011a  multi-core for matrix multiplication.
                                         'remove_unnecessary_outputs':'false',
                                         'use_relative_paths':'false',         ## relative paths should be on, require hash update when changed.
                                         'remove_node_directories':'false',   ## Experimental
                                         'local_hash_check':'true',           ##
                                         'job_finished_timeout':15            ##
                                         }
    filmWF.config['logging'] = {
          'workflow_level':'DEBUG',
          'filemanip_level':'DEBUG',
          'interface_level':'DEBUG',
          'log_directory': ExperimentBaseDirectoryCache
        }
    filmWF.base_dir = ExperimentBaseDirectoryCache

    subjList = getSubjList()
    inputSpec = pe.Node(interface=util.IdentityInterface(fields=['images']), name='InputSpec')
    inputSpec.iterables = ('images', subjList)
    outputSpec = pe.Node(interface=util.IdentityInterface(fields=['output_image']), name='OutputSpec')

    Film = pe.Node(interface=film.Film(), name ='Film')
    Film.inputs.passes = 3
    Film.inputs.output_prefix = 'film3pC'
    Film.inputs.injection_kernel_sigma = 1
    Film.inputs.injection_kernel_radius = 1
    Film.inputs.num_iterations = 30
    Film.inputs.verbose = True
    Film.inputs.inverse_interpolation_kernel ="cubic"
    Film.inputs.interleaving_axis = "coronal"

    filmWF.connect(inputSpec, 'images', Film, 'input_image')
    filmWF.connect(Film, 'image', outputSpec, 'output_image')

    filmWF.write_graph()

    JOB_SCRIPT=get_global_sge_script()
    SGEFlavor='SGE'
    filmWF.run(plugin='Linear')
    #print "Running On ipl_OSX"    
    #filmWF.run(plugin=SGEFlavor,
    #    plugin_args=dict(template=JOB_SCRIPT,qsub_args="-S /bin/bash -pe smp1 1-300 -l mem_free=4000M -o /dev/null -e /dev/null -q OSX"))

filmWF()
