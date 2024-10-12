
# Methods for searching and moving data between projects in XNAT

This code is based on the work of [Andre Zugman](https://github.com/zugmana), specifically
the 'subjmove.py' module (in the 'cli' folder) in his
[xnat-access](https://github.com/zugmana/xnat-access) repository.

The code has been reworked to allow much of the needed information (XNAT host URL, source
and destination projects), and data to be found, to be input as CSV files.  This module
allows for the 'bulk' searching and moving of sessions of data between projects in XNAT
(thanks to @crewalsh for tips on how to implement this optimization!).

