Created by Andre Zugman. andre.zugman@nih.gov
This is a set of tool to interface with Robin and fmrif XNAT server.
It is intended for EDB use only, however it is modifiable to more generic approaches.
It facilitates searching subjects with SDAN ID instead of using MRN. 
This is still experimental. Use at your own risk.

The sample setup folder contains example of necessary setup. You'll need to setup a conda environment prior to using. I recommend you install mamba https://mamba.readthedocs.io/en/latest/
and setup a new environment.

You can now either search subjects by id or download all subjects from a certain date.

To see all options type xnat-tools -h

If you don't have a .netrc you will be prompted to use your password.


