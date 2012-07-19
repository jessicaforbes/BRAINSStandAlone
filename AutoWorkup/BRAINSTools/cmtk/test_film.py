import film

test = film.Film()
test.inputs.input_image = "/nopoulos/structural/Mouse_MR/davidson+lee/BacHD/Bac592/20110627/04/NEW_ANALYSIS/SIMPLECONVERSION_Bac592_04.nii.gz"
test.inputs.output_image = "film_output.nii.gz"
test.inputs.num_of_passes = 2
test.inputs.injection_kernel_sigma = 1
test.inputs.injection_kernel_radius = 1
test.inputs.num_iterations = 30
test.inputs.verbose = True
test.inputs.inverse_interpolation_kernel ="cubic"

target = "/ipldev/scratch/johnsonhj/src/cmtk-build/bin/film -v -C -p 2 --injection-kernel-sigma 1 --injection-kernel-radius 1 --num-iterations 30 /nopoulos/structural/Mouse_MR/davidson+lee/BacHD/Bac592/20110627/04/NEW_ANALYSIS/SIMPLECONVERSION_Bac592_04.nii.gz film_output.nii.gz"

print test.cmdline
print '++++++++++++++++'
print target

#assert test.cmdline.strip() == target.strip()