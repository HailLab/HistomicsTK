FROM girder/tox-and-node
LABEL maintainer="Kitware, Inc. <kitware@kitware.com>"

ENV LANG en_US.UTF-8

# This Dockerfile is used to generate the docker image dsarchive/histomicstk
# This docker image includes the HistomicsTK python package along with its
# dependencies.
#
# All plugins of HistomicsTK should derive from this docker image

RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
    # For installing pip \
    curl \
    ca-certificates \
    # For versioning \
    git \
    # for convenience \
    wget \
    # Needed for building \
    build-essential \
    # can speed up large_image caching \
    memcached \
    apt-get install -y --no-install-recommends \
    # For ease of running tox tests inside containers \
    iptables \
    dnsutils \
    # Install some additional packages for convenience when testing \
    bsdmainutils \
    iputils-ping \
    telnet-ssl \
    tmux \
    # For developer convenience \
    nano \
    jq \
    # Needed for su command
    # sudo \
    && \
    # Clean up to reduce docker size \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    find / -xdev -name '*.py[oc]' -type f -exec rm {} \+ && \
    find / -xdev -name __pycache__ -type d -exec rm -r {} \+

# Make a specific version of python the default and install pip
# RUN rm -f /usr/bin/python && \
#     rm -f /usr/bin/python3 && \
#     ln `which python3.8` /usr/bin/python && \
#     ln `which python3.8` /usr/bin/python3 && \
#     curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
#     python get-pip.py && \
#     rm get-pip.py && \
#     ln `which pip3` /usr/bin/pip && \
#     python --version

# copy HistomicsTK files
ENV htk_path=$PWD/HistomicsTK
RUN mkdir -p $htk_path

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    # Install bokeh to help debug dask \
    pip install --no-cache-dir 'bokeh>=0.12.14,<3' && \
    # Install large_image memcached and sources extras \
    pip install --no-cache-dir 'large-image[all]' --find-links https://girder.github.io/large_image_wheels && \
    # Install girder-client \
    pip install --no-cache-dir girder-client && \
    # Install some other dependencies here to save time in the histomicstk \
    # install step \
    pip install --no-cache-dir nimfa numpy scipy Pillow pandas scikit-image scikit-learn imageio 'shapely[vectorized]' opencv-python-headless sqlalchemy matplotlib 'dask[dataframe]' distributed && \
    # clean up \
    rm -rf /root/.cache/pip/*

# Install the latest version of large_image.  This can be disabled if the
# latest version we need has had an official release
# RUN cd /opt && \
#     git clone https://github.com/girder/large_image && \
#     cd large_image && \
#     # git checkout some-branch && \
#     pip install .[all] -r requirements-dev.txt --find-links https://girder.github.io/large_image_wheels

COPY . $htk_path/
COPY histomicstk/cli/dask_config.yaml /root/.config/dask/dask_config.yaml
WORKDIR $htk_path

# Make sure core packages are up to date
RUN python --version && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -U tox wheel

# Install HistomicsTK and its dependencies
RUN pip install --no-cache-dir . --find-links https://girder.github.io/large_image_wheels && \
    pip install --no-cache-dir virtualenv && \
    rm -rf /root/.cache/pip/*

# Show what was installed
RUN pip freeze

# Clone packages and pip install what we want to be local
RUN cd /opt && \
    git clone https://github.com/girder/girder && \
    cd /opt/girder && \
    pip install --no-cache-dir -e .[mount] && \
    pip install --no-cache-dir -e clients/python

RUN cd /opt && \
    git clone https://github.com/girder/girder_worker_utils && \
    cd /opt/girder_worker_utils && \
    pip install --no-cache-dir -e .

RUN cd /opt && \
    git clone https://github.com/girder/girder_worker && \
    cd /opt/girder_worker && \
    pip install --no-cache-dir -e .[girder,worker]

# define entrypoint through which all CLIs can be run
WORKDIR $htk_path/histomicstk/cli

# Test our entrypoint.  If we have incompatible versions of numpy and
# openslide, one of these will fail
RUN python -m slicer_cli_web.cli_list_entrypoint --list_cli
RUN python -m slicer_cli_web.cli_list_entrypoint ColorDeconvolution --help
# Debug import time
RUN python -X importtime ColorDeconvolution/ColorDeconvolution.py --help

ENV PYTHONUNBUFFERED=TRUE

RUN cd /opt && \
    git clone https://github.com/DigitalSlideArchive/import-tracker.git && \
    cd /opt/import-tracker && \
    pip install --no-cache-dir -e .

RUN cd /opt && \
    git clone https://github.com/girder/slicer_cli_web && \
    cd /opt/slicer_cli_web && \
    pip install --no-cache-dir -e .

RUN cd /opt && \
    git clone https://github.com/girder/large_image && \
    cd /opt/large_image && \
    pip install --no-cache-dir --find-links https://girder.github.io/large_image_wheels -e .[memcached] -rrequirements-dev.txt && \
    # Reduice docker size by de-duplicating some libraries that get installed \
    rdfind -minsize 1048576 -makehardlinks true -makeresultsfile false /opt/venv

RUN cd /opt && \
    git clone https://github.com/DigitalSlideArchive/HistomicsUI && \
    cd /opt/HistomicsUI && \
    pip install --no-cache-dir -e .[analysis]

# Install additional girder plugins
RUN pip install --no-cache-dir --pre \
    girder-archive-access \
    girder-dicom-viewer \
    girder-homepage \
    girder-ldap \
    girder-resource-path-tools \
    girder-user-quota \
    girder-virtual-folders \
    girder-xtk-demo

# Build the girder web client
RUN NPM_CONFIG_FUND=false NPM_CONFIG_AUDIT=false NPM_CONFIG_AUDIT_LEVEL=high NPM_CONFIG_LOGLEVEL=warn NPM_CONFIG_PROGRESS=false NPM_CONFIG_PREFER_OFFLINE=true \
    girder build --dev && \
    # Get rid of unnecessary files to keep the docker image smaller \
    find /opt -xdev -name node_modules -exec rm -rf {} \+ && \
    find /opt -name package-lock.json -exec rm -f {} \+ && \
    rm -rf /tmp/* ~/.npm

# Install phantomjs for testing
RUN npm install -g phantomjs-prebuilt --unsafe-perm && \
    rm -rf /tmp/* ~/.npm

# When running the worker, adjust some settings
RUN echo 'task_reject_on_worker_lost = True' >> /opt/girder_worker/girder_worker/celeryconfig.py
RUN echo 'task_acks_late = True' >> /opt/girder_worker/girder_worker/celeryconfig.py

COPY . /opt/digital_slide_archive

ENV PATH="/opt/digital_slide_archive/devops/dsa/utils:$PATH"

WORKDIR /opt/HistomicsUI

# add a variety of directories
RUN mkdir -p /fuse --mode=a+rwx && \
    mkdir /logs && \
    mkdir /assetstore && \
    mkdir /mounts --mode=a+rwx

RUN cp /opt/digital_slide_archive/devops/dsa/utils/.vimrc ~/.vimrc && \
    cp /opt/digital_slide_archive/devops/dsa/girder.cfg /etc/girder.cfg && \
    cp /opt/digital_slide_archive/devops/dsa/worker.local.cfg /opt/girder_worker/girder_worker/.

# Better shutdown signalling
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD bash
