# Pyradiomics on CONDR_METS Lesion Data

## 2018-01-23 Part 2

Again I spent almost the whole day downloading data, cleaning it up, and uploading it. But I did finally get that all working. It is now almost 7:00 pm, and I have been working for almost 10 hours.

Luckily for me, the rest of the stuff has been a breeze. The script to get the label value out of the mask file took almost no time to write. I am cruising through the wrapper script, which I will put into the wrapper image for which I already have a Dockerfile started. Once I get the image up and tested, it should not take long to get a command written and working.

Ok, image is up. I can run it by hand.

    docker run -v /data/xnat/archive/foo/arc001/S001_E01:/data -v ${HOME}/temp:/output --entrypoint "" xnat/pyradiomics-wrapper:beta run.sh

It needs:

* A session mounted to /data
* An output mounted to /output
* Entrypoint override (which is default now, but I think will soon be not default)
* The command is just "run.sh" with no parameters or anything

✅ Command is done.

## 2018-01-23 Part 1

What I need to do today: get a command written that can run pyradiomics (or an image I make to run pyradiomics with a wrapper script). I spent the entire day yesterday working on cleaning up the CSV from Misha, then writing a script to download the data from CONDR_METS. It didn't seem like a big task in the morning, but it just kept going on and on all day. I feel like I'm kinda close to getting everything to download properly, but not necessarily to getting it uploaded. Which means I don't know exactly how my "clean" sessions will look. Which means I don't know exactly how my command + wrapper to run pyradiomics (or the wrapper script I may need to write around it) will look.\

Here's the dilemma I am pondering. First I will describe what I have. For each session, I will have a single scan, which has the image I want in a nifti resource, and a single session resource which has one or more lesion ROI masks in nifti. For a given session, each of the mask files has a different non-zero value. Now, what I need. To run pyradiomics I need the path to an image, the path to a mask file, and the "level", which is the single non-zero value to pull out of the mask file (because I guess these mask files usually have multiple different values at different places, rather than one "level" per file).
Say I'm a script. I have just started up and I see a session directory mounted. I can easily find the scan and its nifti resource, so I know the path to the image file. I can also find the session resource, so I can find the mask files and iterate over them if I need to. But I don't know how to find the level within a given mask file. And I don't know what to do with the stats when I am done. How do I name the files?

To figure out:

* How do I write a script to read the level from the mask file before running pyradiomics?
* How to name the output files?

## 2018-01-18
I met with Misha today to ask him which scan is intended to be used with the lesion masks. He said the scan ID is in the gk_scan column in the big CSV of session/scan/etc info. (gk stands for Gamma Knife, which is the type of surgical procedure performed in this study.) He said this would be the post-contrast T1.

For my example, I got the correct scan from the HOF_reg resource (in 4dfp) and converted it to nifti (I snatched nifti_4dfp from nrgpackages/whatever/nil-tools and ran it in a centos 6 container). This allows me to run pyradiomics.

    $ docker run --rm --entrypoint "" -v $(pwd):/data radiomics/pyradiomics:CLI pyradiomics /data/HOF_QC_nii/<some image file>.nii /data/ROI_DICOMRT/LES1.nii --param /usr/src/pyradiomics/examples/exampleSettings/exampleMR_3mm.yaml --label 2

    $ docker run --rm --entrypoint "" -v $(pwd):/data radiomics/pyradiomics:CLI pyradiomics /data/HOF_QC_nii/<some image file>.nii /data/ROI_DICOMRT/LES2.nii --param /usr/src/pyradiomics/examples/exampleSettings/exampleMR_3mm.yaml --label 3

The "label" value given is the intensity value of the non-zero part of the mask image. I had to look those values up to get it to work. Before that I got the error "Label (1) not present in the mask". Since the two lesions have different values, I could probably just add the two images together and have a single mask with two different ROI labels. But I won't right now.

This spits out a bunch of stats. I don't know what to do with them yet. Should I whip up an assessor data type?

Next thing, I guess, should be making a command.

## 2018-01-17

Starting this project. I need to explore the data, figure out where the lesions are, how I am going to get at the data for the demo, etc.

I am building on top of a project I did last year using this data, which I called `condr-lesion-atlas`. In that project, I mounted the entire `CONDR_METS` project into a container, read in and registered all the lesions, and made a whole-project lesion atlas. I got a lot of help from Misha to do this, including all the scripts that did the work of registration and atlas generation, along with a CSV file with the locations of the lesion data.

I will be copying and re-using that CSV for sure. I don't think I will be running this in batch mode, so I don't think I will be using the CSV directly. I don't know. But I do know that, without that CSV, I would never be able to find the right sessions and resources and files that have the lesion data I want. It also has a bunch of parameters that I may need.

Downloading a sample subject and session. In that resource, I find binary mask images for the lesions. So that's good to know. And they're in nifti, which is also nice. But I need to apply those on top of a scan—presuably anatomical, presumably co-registered. I know from my past experience with the lesion data that there is additional information in another resource on each session, possibly multiple different files. I need to go deconstruct the scripts from the previous project to understand what they did and what I need to know.

This is maddening. All this data is completely locked up in its proprietary format. Ok, chill. I don't need to understand everything. I should focus on my first goal: a single test run-through of pyradiomics. If I can get that to work, then I can figure out what I need to do to run more test cases.

So what do I need? Well, I can get the lesion mask images. But pyradiomics wants both the mask and the image to which that mask should be applied. So I need to find an anatomical scan co-registered to the mask.

Useful to know

* `<session resources>/HOF_QC/sfind_4dfp.txt` has a bunch of information about the scans