#!/bin/sh
# script for execution of deployed applications
#
# Sets up the MATLAB Runtime environment for the current $ARCH and executes 
# the specified command.
#
exe_name=$0
exe_dir=`dirname "$0"`
echo "------------------------------------------"
if [ "x$1" = "x" ]; then
  echo Usage:
  echo    $0 \<deployedMCRroot\> args
else
  echo Setting up environment variables
  MCRROOT="$1"
  echo ---
  LD_LIBRARY_PATH=.:${MCRROOT}/runtime/glnxa64 ;
  LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/bin/glnxa64 ;
  LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/sys/os/glnxa64;
  # LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/sys/opengl/lib/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v911/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v911/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v911/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v911/extern/bin/glnxa64;
  LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v911/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v911/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v911/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v911/extern/bin/glnxa64;
  # LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/sys/os/glnxa64:/home/ubuntu/matlab/r2021b/bin/glnxa64:/home/ubuntu/matlab/r2021b/sys/os/glnxa64:/usr/lib/x86_64-linux-gnu:/home/ubuntu/matlab/sys/os/glnxa64/:/home/ubuntu/matlab/sys/opengl/lib/glnxa64:/home/ubuntu/matlab/r2021b/bin/glnxa64/:/home/ubuntu/matlab/r2021b/runtime/glnxa64/
  export LD_LIBRARY_PATH;
  echo LD_LIBRARY_PATH is ${LD_LIBRARY_PATH};
# Preload glibc_shim in case of RHEL7 variants
  test -e /usr/bin/ldd &&  ldd --version |  grep -q "(GNU libc) 2\.17"  \
            && export LD_PRELOAD="${MCRROOT}/bin/glnxa64/glibc-2.17_shim.so"
  shift 1
  args=
  while [ $# -gt 0 ]; do
      token=$1
      args="${args} \"${token}\"" 
      shift
  done
  eval "\"${exe_dir}/step1_main_read_json_mask\"" $args
fi
exit

