#!/bin/bash
echo "                                            "
echo "***************  WARNING  ******************"
echo "You are loading software for Course 47332 "
echo "Autonomous materials discovery"
echo "It might conflict with software for other courses"
echo "Change your .bashrc file to avoid this"
echo "********************************************"
echo "                                            "


module load python3

# alias jupnote='jupyter notebook --no-browser --port=40000 --ip=$HOSTNAME'
ROOTDIR=~jchang/47332_pkgs/47332-exercises
export PATH=$ROOTDIR/bin:$PATH

source /zhome/cb/a/119810/pkgs/47332/bin/activate 