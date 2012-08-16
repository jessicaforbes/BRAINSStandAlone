#################################################################################
## Program:   Build Template Parallel
## Language:  Python
##
## Authors:  Jessica Forbes, Grace Murray, and Hans Johnson, University of Iowa
##
##      This software is distributed WITHOUT ANY WARRANTY; without even
##      the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
##      PURPOSE.
##
#################################################################################

import argparse
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import antsAverageImages
import antsAverageAffineTransform
import antsMultiplyImages
import ants
import antsWarp
import antsMultiplyImages
from nipype.interfaces.io import DataGrabber
from nipype.interfaces.utility import Merge, Split, Function, Rename, IdentityInterface

def ANTSTemplateBuildSingleIterationWF(iterationPhasePrefix,CLUSTER_QUEUE):

    antsTemplateBuildSingleIterationWF = pe.Workflow(name = 'ANTSTemplateBuildSingleIterationWF_'+iterationPhasePrefix)

    inputSpec = pe.Node(interface=util.IdentityInterface(fields=['images', 'fixed_image','ListOfPassiveImagesDictionararies']),
                run_without_submitting=True,
                name='InputSpec')
    outputSpec = pe.Node(interface=util.IdentityInterface(fields=['template','transforms_list','passive_deformed_templates']),
                run_without_submitting=True,
                name='OutputSpec')

    ### NOTE MAP NODE! warp each of the original images to the provided fixed_image as the template
    BeginANTS=pe.MapNode(interface=ants.ANTS(), name = 'BeginANTS', iterfield=['moving_image'])
    many_cpu_BeginANTS_options_dictionary={'qsub_args': '-S /bin/bash -pe smp1 8-12 -l mem_free=6000M -o /dev/null -e /dev/null '+CLUSTER_QUEUE, 'overwrite': True}
    BeginANTS.plugin_args=many_cpu_BeginANTS_options_dictionary
    BeginANTS.inputs.dimension = 3
    BeginANTS.inputs.output_transform_prefix = iterationPhasePrefix+'_tfm'
    BeginANTS.inputs.metric = ['CC']
    BeginANTS.inputs.metric_weight = [1.0]
    BeginANTS.inputs.radius = [5]
    BeginANTS.inputs.transformation_model = 'SyN'
    BeginANTS.inputs.gradient_step_length = 0.25
    BeginANTS.inputs.number_of_iterations = [50, 35, 15]
    BeginANTS.inputs.use_histogram_matching = True
    BeginANTS.inputs.mi_option = [32, 16000]
    BeginANTS.inputs.regularization = 'Gauss'
    BeginANTS.inputs.regularization_gradient_field_sigma = 3
    BeginANTS.inputs.regularization_deformation_field_sigma = 0
    BeginANTS.inputs.number_of_affine_iterations = [10000,10000,10000,10000,10000]
    antsTemplateBuildSingleIterationWF.connect(inputSpec, 'images', BeginANTS, 'moving_image')
    antsTemplateBuildSingleIterationWF.connect(inputSpec, 'fixed_image', BeginANTS, 'fixed_image')

    ## Utility Function
    ## This will make a list of list pairs for defining the concatenation of transforms
    ## wp=['wp1.nii','wp2.nii','wp3.nii']
    ## af=['af1.mat','af2.mat','af3.mat']
    ## ll=map(list,zip(af,wp))
    ## ll
    ##[['af1.mat', 'wp1.nii'], ['af2.mat', 'wp2.nii'], ['af3.mat', 'wp3.nii']]
    def MakeListsOfTransformLists(warpTransformList, AffineTransformList):
        return map(list, zip(warpTransformList,AffineTransformList))
    MakeTransformsLists = pe.Node(interface=util.Function(function=MakeListsOfTransformLists,
                    input_names=['warpTransformList', 'AffineTransformList'],
                    output_names=['out']),
                    run_without_submitting=True,
                    name='MakeTransformsLists')
    MakeTransformsLists.inputs.ignore_exception = True
    antsTemplateBuildSingleIterationWF.connect(BeginANTS, 'warp_transform', MakeTransformsLists, 'warpTransformList')
    antsTemplateBuildSingleIterationWF.connect(BeginANTS, 'affine_transform', MakeTransformsLists, 'AffineTransformList')

    ## Now warp all the moving_images images
    wimtdeformed = pe.MapNode(interface = antsWarp.WarpImageMultiTransform(),
                     iterfield=['transformation_series', 'moving_image'],
                     name ='wimtdeformed')
    antsTemplateBuildSingleIterationWF.connect(inputSpec, 'images', wimtdeformed, 'moving_image')
    antsTemplateBuildSingleIterationWF.connect(MakeTransformsLists, 'out', wimtdeformed, 'transformation_series')


    ##  Shape Update Next =====
    ## Now  Average All moving_images deformed images together to create an updated template average
    AvgDeformedImages=pe.Node(interface=antsAverageImages.AntsAverageImages(), name='AvgDeformedImages')
    AvgDeformedImages.inputs.dimension = 3
    AvgDeformedImages.inputs.output_average_image = iterationPhasePrefix+'.nii.gz'
    AvgDeformedImages.inputs.normalize = 1
    antsTemplateBuildSingleIterationWF.connect(wimtdeformed, "output_image", AvgDeformedImages, 'images')

    ## Now average all affine transforms together
    AvgAffineTransform = pe.Node(interface=antsAverageAffineTransform.AntsAverageAffineTransform(), name = 'AvgAffineTransform')
    AvgAffineTransform.inputs.dimension = 3
    AvgAffineTransform.inputs.output_affine_transform = iterationPhasePrefix+'Affine.mat'
    antsTemplateBuildSingleIterationWF.connect(BeginANTS, 'affine_transform', AvgAffineTransform, 'transforms')

    ## Now average the warp fields togther
    AvgWarpImages=pe.Node(interface=antsAverageImages.AntsAverageImages(), name='AvgWarpImages')
    AvgWarpImages.inputs.dimension = 3
    AvgWarpImages.inputs.output_average_image = iterationPhasePrefix+'warp.nii.gz'
    AvgWarpImages.inputs.normalize = 1
    antsTemplateBuildSingleIterationWF.connect(BeginANTS, 'warp_transform', AvgWarpImages, 'images')

    ## Now average the images together
    ## TODO:  For now GradientStep is set to 0.25 as a hard coded default value.
    GradientStep = 0.25
    GradientStepWarpImage=pe.Node(interface=antsMultiplyImages.AntsMultiplyImages(), name='GradientStepWarpImage')
    GradientStepWarpImage.inputs.dimension = 3
    GradientStepWarpImage.inputs.second_input = -1.0 * GradientStep
    GradientStepWarpImage.inputs.output_product_image = iterationPhasePrefix+'warp.nii.gz'
    antsTemplateBuildSingleIterationWF.connect(AvgWarpImages, 'average_image', GradientStepWarpImage, 'first_input')

    ## Now create the new template shape based on the average of all deformed images
    UpdateTemplateShape = pe.Node(interface = antsWarp.WarpImageMultiTransform(), name = 'UpdateTemplateShape')
    UpdateTemplateShape.inputs.invert_affine = [1]
    antsTemplateBuildSingleIterationWF.connect(AvgDeformedImages, 'average_image', UpdateTemplateShape, 'reference_image')
    antsTemplateBuildSingleIterationWF.connect(AvgAffineTransform, 'affine_transform', UpdateTemplateShape, 'transformation_series')
    antsTemplateBuildSingleIterationWF.connect(GradientStepWarpImage, 'product_image', UpdateTemplateShape, 'moving_image')

    def MakeTransformListWithGradientWarps(averageAffineTranform, gradientStepWarp):
        return [averageAffineTranform, gradientStepWarp, gradientStepWarp, gradientStepWarp, gradientStepWarp]
    ApplyInvAverageAndFourTimesGradientStepWarpImage = pe.Node(interface=util.Function(function=MakeTransformListWithGradientWarps,
                                         input_names=['averageAffineTranform', 'gradientStepWarp'],
                                         output_names=['TransformListWithGradientWarps']),
                 run_without_submitting=True,
                 name='MakeTransformListWithGradientWarps')
    ApplyInvAverageAndFourTimesGradientStepWarpImage.inputs.ignore_exception = True

    antsTemplateBuildSingleIterationWF.connect(AvgAffineTransform, 'affine_transform', ApplyInvAverageAndFourTimesGradientStepWarpImage, 'averageAffineTranform')
    antsTemplateBuildSingleIterationWF.connect(UpdateTemplateShape, 'output_image', ApplyInvAverageAndFourTimesGradientStepWarpImage, 'gradientStepWarp')

    ReshapeAverageImageWithShapeUpdate = pe.Node(interface = antsWarp.WarpImageMultiTransform(), name = 'ReshapeAverageImageWithShapeUpdate')
    ReshapeAverageImageWithShapeUpdate.inputs.invert_affine = [1]
    ReshapeAverageImageWithShapeUpdate.inputs.out_postfix = '_Reshaped'
    antsTemplateBuildSingleIterationWF.connect(AvgDeformedImages, 'average_image', ReshapeAverageImageWithShapeUpdate, 'moving_image')
    antsTemplateBuildSingleIterationWF.connect(AvgDeformedImages, 'average_image', ReshapeAverageImageWithShapeUpdate, 'reference_image')
    antsTemplateBuildSingleIterationWF.connect(ApplyInvAverageAndFourTimesGradientStepWarpImage, 'TransformListWithGradientWarps', ReshapeAverageImageWithShapeUpdate, 'transformation_series')
    antsTemplateBuildSingleIterationWF.connect(ReshapeAverageImageWithShapeUpdate, 'output_image', outputSpec, 'template')

    ######
    ######
    ######  Process all the passive deformed images in a way similar to the main image used for registration
    ######
    ######
    ######
    ##############################################
    ## Now warp all the ListOfPassiveImagesDictionararies images
    ## Flatten and return equal length transform and images lists.
    def FlattenTransformAndImagesList(ListOfPassiveImagesDictionararies,transformation_series):
        flattened_images=list()
        flattened_image_nametypes=list()
        flattened_transforms=list()
        subjCount=len(ListOfPassiveImagesDictionararies)
        tranCount=len(transformation_series)
        passiveImagesCount = len(ListOfPassiveImagesDictionararies[0])
        if subjCount != tranCount:
          print "ERROR:  subjCount must equal tranCount {0} != {1}".format(subjCount,tranCount)
          sys.exit(-1)
        for subjIndex in range(0,subjCount):
            if passiveImagesCount != len(ListOfPassiveImagesDictionararies[subjIndex]):
                 print "ERROR:  all image lengths must be equal {0} != {1}".format(passiveImagesCount,len(ListOfPassiveImagesDictionararies[subjIndex]))
                 sys.exit(-1)
            subjImgDictionary=ListOfPassiveImagesDictionararies[subjIndex]
            subjToAtlasTransform=transformation_series[subjIndex]
            for imgname,img in subjImgDictionary.items():
               flattened_images.append(img)
               flattened_image_nametypes.append(imgname)
               flattened_transforms.append(subjToAtlasTransform)
        return flattened_images,flattened_transforms,flattened_image_nametypes
    FlattenTransformAndImagesListNode = pe.Node( Function(function=FlattenTransformAndImagesList,
                                  input_names = ['ListOfPassiveImagesDictionararies','transformation_series'],
                                  output_names = ['flattened_images','flattened_transforms','flattened_image_nametypes']),
                                  run_without_submitting=True, name="99_FlattenTransformAndImagesList")
    antsTemplateBuildSingleIterationWF.connect( inputSpec,'ListOfPassiveImagesDictionararies', FlattenTransformAndImagesListNode, 'ListOfPassiveImagesDictionararies' )
    antsTemplateBuildSingleIterationWF.connect( MakeTransformsLists ,'out', FlattenTransformAndImagesListNode, 'transformation_series' )
    wimtPassivedeformed = pe.MapNode(interface = antsWarp.WarpImageMultiTransform(),
                     iterfield=['transformation_series', 'moving_image'],
                     name ='wimtPassivedeformed')
    antsTemplateBuildSingleIterationWF.connect(FlattenTransformAndImagesListNode, 'flattened_images',     wimtPassivedeformed, 'moving_image')
    antsTemplateBuildSingleIterationWF.connect(FlattenTransformAndImagesListNode, 'flattened_transforms', wimtPassivedeformed, 'transformation_series')

    def RenestDeformedPassiveImages(deformedPassiveImages,flattened_image_nametypes):
        import os
        """ Now make a list of lists of images where the outter list is per image type,
        and the inner list is the same size as the number of subjects to be averaged.
        In this case, the first element will be a list of all the deformed T2's, and
        the second element will be a list of all deformed POSTERIOR_AIR,  etc..
        """
        all_images_size=len(deformedPassiveImages)
        image_dictionary_of_lists=dict()
        nested_imagetype_list=list()
        outputAverageImageName_list=list()
        image_type_list=list()
        ## make empty_list, this is not efficient, but it works
        for name in flattened_image_nametypes:
           image_dictionary_of_lists[name]=list()
        for index in range(0,all_images_size):
          curr_name=flattened_image_nametypes[index]
          curr_file=deformedPassiveImages[index]
          image_dictionary_of_lists[curr_name].append(curr_file)
        for image_type,image_list in image_dictionary_of_lists.items():
          nested_imagetype_list.append(image_list)
          outputAverageImageName_list.append('AVG_'+image_type+'.nii.gz')
          image_type_list.append('WARP_AVG_'+image_type)
        print "\n"*10
        print "HACK: ", nested_imagetype_list
        print "HACK: ", outputAverageImageName_list
        print "HACK: ", image_type_list
        return nested_imagetype_list,outputAverageImageName_list,image_type_list
    RenestDeformedPassiveImagesNode = pe.Node( Function(function=RenestDeformedPassiveImages,
                                  input_names = ['deformedPassiveImages','flattened_image_nametypes'],
                                  output_names = ['nested_imagetype_list','outputAverageImageName_list','image_type_list']),
                                  run_without_submitting=True, name="99_RenestDeformedPassiveImages")
    antsTemplateBuildSingleIterationWF.connect(wimtPassivedeformed, 'output_image', RenestDeformedPassiveImagesNode, 'deformedPassiveImages')
    antsTemplateBuildSingleIterationWF.connect(FlattenTransformAndImagesListNode, 'flattened_image_nametypes', RenestDeformedPassiveImagesNode, 'flattened_image_nametypes')
    ## Now  Average All passive moving_images deformed images together to create an updated template average
    AvgDeformedPassiveImages=pe.MapNode(interface=antsAverageImages.AntsAverageImages(),
      iterfield=['images','output_average_image'],
      name='AvgDeformedPassiveImages')
    AvgDeformedPassiveImages.inputs.dimension = 3
    AvgDeformedPassiveImages.inputs.normalize = 0
    antsTemplateBuildSingleIterationWF.connect(RenestDeformedPassiveImagesNode, "nested_imagetype_list", AvgDeformedPassiveImages, 'images')
    antsTemplateBuildSingleIterationWF.connect(RenestDeformedPassiveImagesNode, "outputAverageImageName_list", AvgDeformedPassiveImages, 'output_average_image')

    ## -- TODO:  Now neeed to reshape all the passive images as well
    ReshapeAveragePassiveImageWithShapeUpdate = pe.MapNode(interface = antsWarp.WarpImageMultiTransform(),
      iterfield=['moving_image','reference_image','out_postfix'],
      name = 'ReshapeAveragePassiveImageWithShapeUpdate')
    ReshapeAveragePassiveImageWithShapeUpdate.inputs.invert_affine = [1]
    antsTemplateBuildSingleIterationWF.connect(RenestDeformedPassiveImagesNode, "image_type_list", ReshapeAveragePassiveImageWithShapeUpdate, 'out_postfix')
    antsTemplateBuildSingleIterationWF.connect(AvgDeformedPassiveImages, 'average_image', ReshapeAveragePassiveImageWithShapeUpdate, 'moving_image')
    antsTemplateBuildSingleIterationWF.connect(AvgDeformedPassiveImages, 'average_image', ReshapeAveragePassiveImageWithShapeUpdate, 'reference_image')
    antsTemplateBuildSingleIterationWF.connect(ApplyInvAverageAndFourTimesGradientStepWarpImage, 'TransformListWithGradientWarps', ReshapeAveragePassiveImageWithShapeUpdate, 'transformation_series')
    antsTemplateBuildSingleIterationWF.connect(ReshapeAveragePassiveImageWithShapeUpdate, 'output_image', outputSpec, 'passive_deformed_templates')

    return antsTemplateBuildSingleIterationWF
