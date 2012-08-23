import film

test = film.Film()
test.inputs.input_image = "/paulsen/MRx/PHD_175/0728/74457/ANONRAW/0728_74457_T2-15_4.nii.gz"
#test.inputs.output_image = "/ipldev/scratch/jforbes/film/0728_74457_T2-15_4_film_output.nii.gz"
test.inputs.passes = 3
test.inputs.injection_kernel_sigma = 1
test.inputs.injection_kernel_radius = 1
test.inputs.num_iterations = 30
test.inputs.verbose = True
test.inputs.inverse_interpolation_kernel ="cubic"
#test.inputs.padding_value = 2
test.inputs.interleaving_axis = "coronal"
#test.inputs.reference_image = "/nopoulos/structural/Mouse_MR/davidson+lee/BacHD/Bac592/20110627/04/NEW_ANALYSIS/SIMPLECONVERSION_Bac592_04.nii.gz"
#test.inputs.registration_metric = 'nmi'
#test.inputs.import_xforms_path = 'import/path'
#test.inputs.export_xforms_path = 'export/path'
#test.inputs.fourth_order_error = True
#test.inputs.l_norm_weight = 1
#test.inputs.no_truncation = True
#test.inputs.write_injected_image = 'file/path'
#test.inputs.write_images_as_float = True

target = "/ipldev/scratch/johnsonhj/src/cmtk-build/bin/film -v -C -p 2 --injection-kernel-sigma 1 --injection-kernel-radius 1 --num-iterations 30 /nopoulos/structural/Mouse_MR/davidson+lee/BacHD/Bac592/20110627/04/NEW_ANALYSIS/SIMPLECONVERSION_Bac592_04.nii.gz film_output.nii.gz"

print test.cmdline
print '++++++++++++++++'
print target

#assert test.cmdline.strip() == target.strip()