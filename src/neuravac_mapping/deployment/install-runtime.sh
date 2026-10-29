#!/usr/bin/env bash
# Official Ubuntu/ROS arm64 binary runtime in a user-owned prefix; no sudo.
set -euo pipefail
NEURAVAC_RUNTIME="$HOME/neuravac-slam-runtime"
mkdir -p "$NEURAVAC_RUNTIME/debs" "$NEURAVAC_RUNTIME/root"
cd "$NEURAVAC_RUNTIME/debs"
apt-get download ros-jazzy-slam-toolbox libboost-serialization1.83.0 \
  libboost-thread1.83.0 libtbb12 libtbbmalloc2 libtbbbind-2-5 \
  ros-jazzy-bond ros-jazzy-bondcpp ros-jazzy-interactive-markers \
  ros-jazzy-smclib libceres4t64 libgoogle-glog0v6t64 libgflags2.2 \
  libcholmod5 libspqr4 libamd3 libcamd3 libccolamd3 libcolamd3 \
  libsuitesparseconfig7 libmetis5
for package in *.deb; do dpkg-deb -x "$package" "$NEURAVAC_RUNTIME/root"; done
sha256sum *.deb > packages.sha256
