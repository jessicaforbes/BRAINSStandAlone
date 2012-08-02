import film
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util

def filmWF():
    filmWF = pe.Workflow(name= 'filmWF')

    inputSpec = pe.Node(interface=util.IdentityInterface(fields=['images']), name='InputSpec')
    inputSpec.iterables = ('images', subjects_list)
    outputSpec = pe.Node(interface=util.IdentityInterface(fields=['output_image']), name='OutputSpec')

    film = pe.Node(interface=film.Film(), name ='film')
    film.inputs.input_image = "/nopoulos/structural/peg_MR/8720323/11088905/ANONRAW/8720323_11088905_T2_COR.nii.gz"
    film.inputs.output_image = "film_output.nii.gz"
    film.inputs.passes = 2
    film.inputs.injection_kernel_sigma = 1
    film.inputs.injection_kernel_radius = 1
    film.inputs.num_iterations = 30
    film.inputs.verbose = True
    film.inputs.inverse_interpolation_kernel ="cubic"

    filmWF.connect(inputSpec, 'images', film, 'input_image')
    filmWF.connect(film, 'output_image', outputSpec, 'output_image')

    return filmWF