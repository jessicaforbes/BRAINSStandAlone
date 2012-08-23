"""



TITLE:

     Fix interleaved motion using inverse interpolation


DESCRIPTION:

     This tool splits an interleaved input image into the pass images, co-registers them, and reconstructs a motion-corrected image


SYNTAX:

     [options] InputImage OutputImage

  where

     InputImage =        Input image path

     OutputImage =       Output image path


LIST OF SUPPORTED OPTIONS:

Global Toolkit Options (these are shared by all CMTK tools)

  --help    Write list of basic command line options to standard output.

  --help-all
            Write complete list of basic and advanced command line options to standard output.

  --wiki    Write list of command line options to standard output in MediaWiki markup.

  --man     Write man page source in 'nroff' markup to standard output.

  --xml     Write command line syntax specification in XML markup (for Slicer integration).

  --version
            Write toolkit version to standard output.

  --echo    Write the current command line to standard output.

  --verbose-level <integer>
            Set verbosity level.

  --verbose, -v
            Increment verbosity level by 1 (deprecated; supported for backward compatibility).

  --threads <integer>
            Set maximum number of parallel threads (for POSIX threads and OpenMP).

Input Options

  --padding-value <double>
            Set padding value for input image. Pixels with this value will be ignored.
            [Default: disabled]

Interleaving Options

  --interleave-axis
            Define interleave axis: this is the through-slice direction of the acquisition.
            Supported values: "guess-from-input", "axial", "sagittal", "coronal", "interleave-x", "interleave-y", "interleave-z", where the default is "guess-from-input",
            or use one of the following

            --guess-from-input
                      Guess from input image
                      [This is the default]

            --axial, -a
                      Interleaved axial images

            --sagittal, -s
                      Interleaved sagittal images

            --coronal, -c
                      Interleaved coronal images

            --interleave-x, -x
                      Interleaved along x axis

            --interleave-y, -y
                      Interleaved along y axis

            --interleave-z, -z
                      Interleaved along z axis

  --passes <integer>, -p <integer>
            Number of interleaved passes
            [Default: 2]

  --pass-weight <string>, -W <string>
            Set contribution weight for a pass in the form 'pass:weight'

Motion Correction / Registration Options

  --reference-image <image-path>, -R <image-path>
            Use a separate high-resolution reference image for registration
            [Default: NONE]

  --registration-metric
            Registration metric for motion estimation by image-to-image registration.
            Supported values: "nmi", "mi", "cr", "msd", "cc", where the default is "msd", or use one of the following

            --nmi     Use Normalized Mutual Information for pass-to-refereence registration

            --mi      Use standard Mutual Information for pass-to-refereence registration

            --cr      Use Correlation Ratio for pass-to-refereence registration

            --msd     Use Mean Squared Differences for pass-to-refereence registration
                      [This is the default]

            --cc      Use Cross-Correlation for pass-to-refereence registration

  --import-xforms-path <path>
            Path of file from which to import transformations between passes.
            [Default: NONE]

  --export-xforms-path <path>
            Path of file to which to export transformations between passes.
            [Default: NONE]

Initial Volume Injection Options

  --injection-kernel-sigma <double>, -S <double>
            Standard deviation of Gaussian kernel for volume injection in multiples
            of pixel size in each direction.
            [Default: 0.5]

  --injection-kernel-radius <double>, -r <double>
            Truncation radius factor of injection kernel. The kernel is truncated at
            sigma*radius, where sigma is the kernel standard deviation.
            [Default: 2]

Inverse Interpolation Options

  --inverse-interpolation-kernel
            Kernel for the inverse interpolation reconstruction
            Supported values: "cubic", "linear", "hamming-sinc", "cosine-sinc", where the default is "cubic", or use one of the following

            --cubic, -C
                      Tricubic interpolation
                      [This is the default]

            --linear, -L
                      Trilinear interpolation (faster but less accurate)

            --hamming-sinc, -H
                      Hamming-windowed sinc interpolation

            --cosine-sinc, -O
                      Cosine-windowed sinc interpolation (most accurate but slowest)

  --fourth-order-error, -f
            Use fourth-order (rather than second-order) error for optimization.

  --num-iterations <integer>, -n <integer>
            Maximum number of inverse interpolation iterations
            [Default: 20]

Reconstruction Regularization Options

  --l-norm-weight <double>
            Set constraint weight for Tikhonov-type L-Norm regularization (0 disables constraint)
            [Default: 0]

  --no-truncation, -T
            Turn off regional intensity truncatrion

Output Options

  --write-injected-image <image-path>
            Write initial volume injection image to path
            [Default: NONE]

  --write-images-as-float, -F
            Write output images as floating point [default: same as input]

=======================================================================

How to run the test case:

Mouse:

/ipldev/scratch/johnsonhj/src/cmtk-build/bin/film \
    -v \
    -C \
    -p 2 \
    --injection-kernel-sigma 1 \
    --injection-kernel-radius 1 \
    --num-iterations 30 \
    /nopoulos/structural/Mouse_MR/davidson+lee/BacHD/Bac592/20110627/04/NEW_ANALYSIS/SIMPLECONVERSION_Bac592_04.nii.gz \
    film_output.nii.gz

//OPTIONAL INTERFACE FOR MULTI_MODAL_REGISTRATION:
#    -m 'CC[SUBJ_A_T2.nii.gz,SUBJ_B_T2.nii.gz,1,5]' \

=======================================================================
"""

# Standard library imports
import os

# Local imports
from nipype.interfaces.base import (TraitedSpec, File, traits, InputMultiPath, OutputMultiPath, isdefined)
from nipype.utils.filemanip import split_filename
from nipype.interfaces.ants.base import ANTSCommand, ANTSCommandInputSpec

class FilmInputSpec(ANTSCommandInputSpec):
    input_image = File(argstr='%s', mandatory=True, exists=True, position=-2, desc='input image')
    output_image = File(argstr='%s', usedefault=True, position=-1, desc='output image')
    output_prefix = traits.Str('film3pC', usedefault=True, desc=('Prefix that is prepended to all output files (default = film3pC)'))
    passes = traits.Int(2, argstr='--passes %s', usedefault=True, desc="Number of interleaved passes")
    injection_kernel_sigma = traits.Float(0.5, argstr='--injection-kernel-sigma %s', usedefault=True, desc="Standard deviation of Gaussian kernel for volume injection in multiples of pixel size in each direction.")
    injection_kernel_radius = traits.Float(2, argstr='--injection-kernel-radius %s', usedefault=True, desc="Truncation radius factor of injection kernel. The kernel is truncated at sigma*radius, where sigma is the kernel standard deviation.")
    num_iterations = traits.Int(20, argstr='--num-iterations %s', usedefault=True, desc="Maximum number of inverse interpolation iterations")
    verbose = traits.Bool(argstr="--verbose", desc='Increment verbosity level by 1 (deprecated; supported for backward compatibility).')
    inverse_interpolation_kernel = traits.Enum("cubic", "linear", "hamming-sinc", "cosine-sinc", argstr="--%s",
                                               default='--cubic', usedefault=True,
                                               desc='Kernel for the inverse interpolation reconstruction. Supported values: "cubic", "linear", "hamming-sinc", "cosine-sinc", where the default is "cubic"')
    padding_value = traits.Float(argstr="--padding-value %s", desc="Set padding value for input image. Pixels with this value will be ignored.")
    interleaving_axis = traits.Enum("guess-from-input", "axial", "sagittal", "coronal", "interleave-x", "interleave-y", "interleave-z",
                                    argstr="--%s", default='--guess-from-input',
                                    desc='Define interleave axis: this is the through-slice direction of the acquisition.')
    reference_image = File(argstr='--reference-image %s', exists=True, default=None, desc='Use a separate high-resolution reference image for registration [Default: NONE]')
    registration_metric = traits.Enum("msd", "nmi", "mi", "cr", "cc", argstr='--%s', default="--msd", desc='Registration metric for motion estimation by image-to-image registration.')
    import_xforms_path = File(argstr='--import-xforms-path %s', default=None, desc='Path of file from which to import transformations between passes. [Default: NONE]')
    export_xforms_path = File(argstr='--export-xforms-path %s', default=None, desc='Path of file to which to export transformations between passes. [Default: NONE]')
    fourth_order_error = traits.Bool(argstr='--fourth-order-error', desc="Use fourth-order (rather than second-order) error for optimization.")
    l_norm_weight = traits.Float(0, argstr="--l-norm-weight %s", desc="Set constraint weight for Tikhonov-type L-Norm regularization (0 disables constraint) [Default: 0]")
    no_truncation = traits.Bool(argstr='--no-truncation', desc="Turn off regional intensity truncation")
    write_injected_image = File(argstr='--write-injected-image %s', default=None, desc='Write initial volume injection image to path [Default: NONE]')
    write_images_as_float = traits.Bool(argstr='--write-images-as-float', desc="Write output images as floating point [default: same as input]")

class FilmOutputSpec(TraitedSpec):
    image = File(exists=True, desc='output image')

class Film(ANTSCommand):
    """
    Examples
    --------
    >>>
    """
    _cmd = '/ipldev/sharedopt/20120722/Darwin_i386/cmtk/bin/film'
    input_spec = FilmInputSpec
    output_spec = FilmOutputSpec

    def getOutputFilename(self):
        image_dir_split = self.inputs.input_image.strip().split('/')
        site = image_dir_split[3]
        imagename = image_dir_split[-1]
        return '%s_%s_%s' % (self.inputs.output_prefix, site, imagename)

    def _format_arg(self, opt, spec, val):
        if opt == 'output_image':
            return self.getOutputFilename()
        return super(Film, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['image'] = os.path.abspath(self.getOutputFilename())
        return outputs
