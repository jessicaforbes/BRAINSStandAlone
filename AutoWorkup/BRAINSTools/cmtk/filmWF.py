import film
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util

def filmWF():
    filmWF = pe.Workflow(name= 'filmWF')

    ExperimentBaseDirectoryCache = '/scratch/film'
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

    subjects_list = ["/nopoulos/structural/peg_MR/8720323/11088905/ANONRAW/8720323_11088905_T2_COR.nii.gz",
                     "/nopoulos/structural/peg_MR/8720323/11088905/ANONRAW/8720323_11088905_T2_COR.nii.gz",
                     "/nopoulos/structural/peg_MR/8720323/11088905/ANONRAW/8720323_11088905_T2_COR.nii.gz"]

    inputSpec = pe.Node(interface=util.IdentityInterface(fields=['images']), name='InputSpec')
    inputSpec.iterables = ('images', subjects_list)
    outputSpec = pe.Node(interface=util.IdentityInterface(fields=['output_image']), name='OutputSpec')

    Film = pe.Node(interface=film.Film(), name ='Film')
    Film.inputs.output_image = "film_output.nii.gz"
    Film.inputs.passes = 2
    Film.inputs.injection_kernel_sigma = 1
    Film.inputs.injection_kernel_radius = 1
    Film.inputs.num_iterations = 30
    Film.inputs.verbose = True
    Film.inputs.inverse_interpolation_kernel ="cubic"

    filmWF.connect(inputSpec, 'images', Film, 'input_image')
    filmWF.connect(Film, 'image', outputSpec, 'output_image')

    filmWF.write_graph()


filmWF()
