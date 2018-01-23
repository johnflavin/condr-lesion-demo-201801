#!/bin/bash

for scandir in $(find data -type d -name scan); do
    echo "----------"
    scan_4dfp_path=$(ls ${scandir}/*.4dfp.ifh)
    scan_4dfp_ifh=$(basename ${scan_4dfp_path})
    scan_nii=${scan_4dfp_ifh%.4dfp.ifh}.nii

    echo "docker run --rm -v $(pwd):/input -w /input/${scandir} centos:6 /input/bin/nifti_4dfp -n $scan_4dfp_ifh $scan_nii"
    docker run --rm -v $(pwd):/input -w /input/${scandir} centos:6 /input/bin/nifti_4dfp -n $scan_4dfp_ifh $scan_nii
done
