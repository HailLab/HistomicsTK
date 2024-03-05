================================================
HistomicsTK |build-status| |codecov-io| |gitter|
================================================

.. |build-status| image:: https://travis-ci.org/DigitalSlideArchive/HistomicsTK.svg?branch=master
    :target: https://travis-ci.org/DigitalSlideArchive/HistomicsTK
    :alt: Build Status

.. |codecov-io| image:: https://codecov.io/github/DigitalSlideArchive/HistomicsTK/coverage.svg?branch=master
    :target: https://codecov.io/github/DigitalSlideArchive/HistomicsTK?branch=master
    :alt: codecov.io

.. |gitter| image:: https://badges.gitter.im/DigitalSlideArchive/HistomicsTK.svg
   :target: https://gitter.im/DigitalSlideArchive/HistomicsTK?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
   :alt: Join the chat at https://gitter.im/DigitalSlideArchive/HistomicsTK

HistomicsTK is a Python and REST API for the analysis of Histopathology images
in association with clinical and genomic data. 

Histopathology, which involves the examination of thin-slices of diseased
tissue at a cellular resolution using a microscope, is regarded as the gold
standard in clinical diagnosis, staging, and prognosis of several diseases
including most types of cancer. The recent emergence and increased clinical
adoption of whole-slide imaging systems that capture large digital images of
an entire tissue section at a high magnification, has resulted in an explosion
of data. Compared to the related areas of radiology and genomics, there is a
dearth of mature open-source tools for the management, visualization and
quantitative analysis of the massive and rapidly growing collections of
data in the domain of digital pathology. This is precisely the gap that
we aim to fill with the development of HistomicsTK.

Developed in coordination with the `Digital Slide Archive`_ and
`large_image`_, HistomicsTK aims to serve the needs of both
pathologists/biologists interested in using state-of-the-art algorithms
to analyze their data, and algorithm researchers interested in developing
new/improved algorithms and disseminate them for wider use by the community.

You may view the following introductory videos for more information about
DSA and HistomicsTK:

- General overview: https://www.youtube.com/watch?v=NenUKZaT--k

- Simple annotation and data management tutorial: https://www.youtube.com/watch?v=HTvLMyKYyGs

HistomicsTK can be used in two ways:

- **As a pure Python package**: This is intended to enable algorithm
  researchers to use and/or extend the analytics functionality within
  HistomicsTK in Python. HistomicsTK provides algorithms for fundamental
  image analysis tasks such as color normalization, color deconvolution,
  cell-nuclei segmentation, and feature extraction. Please see the
  `api-docs <https://digitalslidearchive.github.io/HistomicsTK/api-docs.html>`__
  and `examples <https://digitalslidearchive.github.io/HistomicsTK/examples.html>`__
  for more information.
  
  Installation instructions on Linux:
  
  *To install HistomicsTK using PyPI*::
  
  $ python -m pip install histomicstk

VUMC IT Server Maintenance
##########################
The AD group to permit access onto the host is SG-KNK_admin. Users added to that AD group have the ability to sudo to the knkapp application account, i.e. sudo su – knkapp. Sudo functions within the application account can be viewed with the following command: `sudo -l -U knkapp`. Application related files should be stored in the /app001 volume on the host.
 
Additional work to the host should be requested through the Pegasus Request Management module using the VUMC IT LINUX – GENERAL REQUEST form. Be sure to specify the hostname where work is to be performed. LTM work is requested using the Pegasus Request Management forms relating to VUMC IT LINUX – F5 LTM requests. Applications must be fully configured before submitting requests for LTM work. Requested packages or versions not available in Red Hat repositories will have to be installed by the customer within the application volume
 
Server Details:
###############
- knk1001ld / 10.158.184.186 (knk_app1_hosts)
- knk1001lp  / 10.100.128.170 (knk_app1_hosts)
- knk1002ld / 10.158.188.36 (knk_mongodb_hosts)
- knk1002lp / 10.100.132.69 (knk_mongodb_hosts)
 
FQDN:
#####
* knk1001ld.hs.it.vumc.io
* knk1001lp.hs.it.vumc.io
* knk1002ld.hs.it.vumc.io
* knk1002lp.hs.it.vumc.io

Installation
############
  *To install HistomicsTK from source*::
  
  $ git clone https://github.com/DigitalSlideArchive/HistomicsTK/
  $ cd HistomicsTK/
  $ python -m pip install setuptools-scm Cython>=1.25.2 scikit-build>=0.8.1 cmake>=0.6.0 numpy>=1.12.1
  $ python -m pip install -e .

Notes
#####
  HistomicsTK uses the `large_image`_ library to read and various microscopy
  image formats.  Depending on your exact system, installing the necessary 
  libraries to support these formats can be complex.  There are some
  non-official prebuilt libraries available for Linux that can be included as
  part of the installation by specifying 
  ``pip install histomicstk --find-links https://girder.github.io/large_image_wheels``.
  Note that if you previously installed HistomicsTK or large_image without
  these, you may need to add ``--force-reinstall --no-cache-dir`` to the
  ``pip install`` command to force it to use the find-links option.

  The system version of various libraries are used if the ``--find-links``
  option is not specified.  You will need to use your package manager to
  install appropriate libraries (on Ubuntu, for instance, you'll need 
  ``libopenslide-dev`` and ``libtiff-dev``).

- **As a server-side Girder plugin for web-based analysis**: This is intended
  to allow pathologists/biologists to apply analysis modules/pipelines
  containerized in HistomicsTK's docker plugins on data over the web. Girder_
  is a Python-based framework (under active development by Kitware_) for
  building web-applications that store, aggregate, and process scientific data.
  It is built on CherryPy_ and provides functionality for authentication,
  access control, customizable metadata association, easy upload/download of
  data, an abstraction layer that exposes data stored on multiple backends
  (e.g. Native file system, Amazon S3, MongoDB GridFS) through a uniform
  RESTful API, and most importantly an extensible plugin framework for
  building server-side analytics apps. To inherit all these capabilities,
  HistomicsTK is being developed to act also as a Girder plugin in addition
  to its use as a pure Python package. To further support web-based analysis,
  HistomicsTK depends on three other Girder plugins: (i) girder_worker_ for
  distributed task execution and monitoring, (ii) large_image_ for displaying,
  serving, and reading large multi-resolution images produced by whole-slide
  imaging systems, and (iii) slicer_cli_web_ to provide web-based RESTFul
  access to image analysis pipelines developed as `slicer execution model`_
  CLIs and containerized using Docker.

Skin maintenance
################
To login:
*********
1. Navigate to https://skin.app.vumc.org.
2. Select Login in the upper-right-hand corner with an administrative account.

To add a new user:
******************
1. Select Users in the left navigation or navigate to https://skin.app.vumc.org/#users.
2. Select "Create User" in the top navigation.
3. Use a login name derived from the first part of the user's email address (before the @ sign).

To add a user to an image group:
********************************
1. Select Groups from the left navigation.
2. Select group you would like to add the user to, (i.e. Baseline or GVHD).
3. Type the user's name into the search field of the Member table.
4. Click the user from the autocomplete.
5. Select "Add as member" yellow button.
6. Repeat for other groups you would like to add.
7. Wait an hour for the server to run scripts which will create the annotation layers for all images.

To export all annotations from baseline:
****************************************
.. code-block:: bash

    ssh -i "~/.ssh/skin.app.vumc.org.pem" ubuntu@ec2-3-227-207-182.compute-1.amazonaws.com  # This assumes you have a bash-like shell environment. PuTTY should work fine in Windows though.
    screen -dr skin  # I recommend you work in a screen in case of disconnect. You’ll need to execute `screen -S skin` to create the screen on your first connection or after any reboots.
    python /opt/histomicstk/HistomicsTK/histomicstk/utils/manage_skin.py --help  # if you want to see a list of all available arguments
    python /opt/histomicstk/HistomicsTK/histomicstk/utils/manage_skin.py --operation export --token a******************************Y --folder 5f0dc45cc9f8c18253ae949b > /tmp/skin-annotations-all-$(date +'%Y-%m-%d').json  # export all baseline demarcations. Update folder to 5f0dc449c9f8c18253ae949a if you want to export RCT instead.
    screen -d htk  # detach from screen
    exit
    scp /tmp/skin-annotations-all-$(date +'%Y-%m-%d').json .  # Downloads annotations onto your local machine. This is assuming you have a bash-like shell environment on your native system. Winscp is a fine alternative on Windows

To export annotations by date from RCT folder:
**********************************************
.. code-block:: bash

    ssh -i "~/.ssh/skin.app.vumc.org.pem" ubuntu@ec2-3-227-207-182.compute-1.amazonaws.com  # This assumes you have a bash-like shell environment. PuTTY should work fine in Windows though.
    screen -dr skin  # I recommend you work in a screen in case of disconnect. You’ll need to execute `screen -S skin` to create the screen on your first connection or after any reboots.
    python /opt/histomicstk/HistomicsTK/histomicstk/utils/manage_skin.py --help  # if you want to see a list of all available arguments
    START_DATE=2021-01-01; END_DATE=2021-01-01; python /opt/histomicstk/HistomicsTK/histomicstk/utils/manage_skin.py --operation export --token a******************************Y --folder 5f0dc449c9f8c18253ae949a --startdate $START_DATE --enddate $END_DATE > /tmp/skin-annotations-${START_DATE}--${END_DATE}.json  # export baseline demarcations on a particular date. Remove start or end to set only an upper or lower bound. Set a range to export a range of dates (inclusive). Update folder to 5f0dc45cc9f8c18253ae949b if you want to export baseline instead.
    screen -d htk  # detach from screen
    exit
    scp /tmp/skin-annotations-all-2021-01-01--2021-01-01.json .  # Downloads annotations onto your local machine. This is assuming you have a bash-like shell environment on your native system. Winscp is a fine alternative on Windows. Make sure to update dates in file name.

To create layers for new workers:
*********************************
.. code-block:: bash

    ssh -i "~/.ssh/skin.app.vumc.org.pem" ubuntu@ec2-3-227-207-182.compute-1.amazonaws.com  # This assumes you have a bash-like shell environment. PuTTY should work fine in Windows though.
    screen -dr skin  # I recommend you work in a screen in case of disconnect. You’ll need to execute `screen -S skin` to create the screen on your first connection or after any reboots.
    python /opt/histomicstk/HistomicsTK/histomicstk/utils/manage_skin.py --help  # if you want to see a list of all available arguments
    python /opt/histomicstk/HistomicsTK/histomicstk/utils/manage_skin.py --operation process_baseline --token a******************************Y --folder 5f0dc45cc9f8c18253ae949b
    python /opt/histomicstk/HistomicsTK/histomicstk/utils/manage_skin.py --operation process --token a******************************Y --folder 5f0dc449c9f8c18253ae949a

After making alterations to js files:
*************************************
girder-install web &

After causing an error in a py file:
************************************
Navigate to /#plugins and select "Rebuilt and restart" button in the upper right.

After making changes to MATLAB script:
**************************************
.. code-block:: bash

    matlab
    mcc -W python:annotateimage /home/ubuntu/skin-overlay/step1_main_read_json_mask.m
    mcc -m /home/ubuntu/skin-overlay/step1_main_read_json_mask.m
    cp ~/run_step1_main_read_json_mask.sh /opt/histomicstk/HistomicsTK/histomicstk/utils/
    cp ~/step1_main_read_json_mask /opt/histomicstk/HistomicsTK/histomicstk/utils/
    JSON_FOLDER='/opt/histomicstk_data/natiens_pilot/Pilot06/1_211004/json/' BASELINE_FOLDER='/opt/histomicstk_data/natiens_pilot/Pilot06/1_211004/imgsrc/' ANNOTATED_IMAGES_FOLDER='/opt/histomicstk_data/natiens_pilot/Pilot06/1_211004/annotated/' MASKS_FOLDER='/opt/histomicstk_data/natiens_pilot/Pilot06/1_211004/masks/' /opt/histomicstk/HistomicsTK/histomicstk/utils/run_step1_main_read_json_mask.sh /home/ubuntu/matlab/r2021b/mcr

Server admin
############
HistomicsTK is hosted on an AWS instance. Backup images are being created of it.

To install, on Amazon Linux instance with a minimum of 120GB SSD and IP restricted networking:
**********************************************************************************************
.. code-block:: bash

    sudo yum install git docker python3-pip nginx
    sudo usermod -aG docker $USER
    reset
    sudo service docker start
    git clone git@github.com:HailLab/HistomicsTK.git  # you'll need to create keys and upload to your GitHub or use a personal access token
    cd HistomicsTK/
    pip install -r requirements_dev.txt
    pip install docker
    python3 ansible/deploy_docker.py start --mount ~/HistomicsTK/:/opt/histomicstk/HistomicsTK/  # kill command if it appears as though deployment is looping. The containers were still created properly.
    sudo mkdir /etc/nginx/sites-enabled/
    sudo cp devops/skin.app.vumc.org.conf.example /etc/nginx/sites-enabled/skin.app.vumc.org.conf
    sudo service nginx restart

On source server:
-----------------
.. code-block:: bash

    docker exec $(docker ps -aqf "ancestor=mongo:latest") mongodump -d girder --gzip --out /root/htkdb
    docker cp $(docker ps -aqf "ancestor=mongo:latest"):/root/htkdb ~/
    docker cp $(docker ps -aqf "ancestor=dsarchive/histomicstk_main:latest"):/opt/histomicstk/assetstore ~/assetstore

On local machine:
-----------------
.. code-block:: bash

    # unless access permissions are opened up between servers, it's easiest to use your working computer as an intermediate. If database gets larger than 15GB, this could be space inefficient and require opening up permissions on servers for direct communication
    scp -r -i ~/.ssh/skin.cer skinold:~/htkdb ~/htkdb
    scp -r -i ~/.ssh/skin.cer skinold:~/assetstore ~/assetstore
    scp -r -i ~/.ssh/skin.cer ~/htkdb skinnew:~/htkdb
    scp -r -i ~/.ssh/skin.cer ~/assetstore skinnew:~/assetstore

On destination server:
----------------------
.. code-block:: bash

    docker cp ~/htkdb $(docker ps -aqf "ancestor=mongo:latest"):/root/htkdb
    docker exec $(docker ps -aqf "ancestor=mongo:latest") mongorestore -d girder --gzip /root/htkdb/girder
    docker cp ~/assetstore $(docker ps -aqf "ancestor=dsarchive/histomicstk_main:latest"):/opt/histomicstk
    docker exec $(docker ps -aqf "ancestor=dsarchive/histomicstk_main:latest") bash -c "\
        sudo mkdir -p /opt/histomicstk_data; \
        sudo chown -R root:ubuntu /opt/histomicstk_data/; \
        sudo chmod -R g+w /opt/histomicstk_data/; \
        sudo apt-get update -y; \
        sudo apt install -y cron libgl1-mesa-dev; \
        sudo systemctl enable cron; \
        pip install nameparser; \
        mkdir -p /opt/histomicstk/girder/clients/web/static/timeme.js; \
        cd /opt/histomicstk/girder/clients/web/static/timeme.js; \
        curl -O https://cdnjs.cloudflare.com/ajax/libs/TimeMe.js/2.0.0/timeme.min.js; \
        cd /opt/histomicstk/girder/clients/web/static/; \
        curl -O https://wurfl.io/wurfl.js;"

Erata
#####
Please refer to https://digitalslidearchive.github.io/HistomicsTK/ for more information.

For questions, comments, or to get in touch with the maintainers, head to our
`Discourse forum`_, or use our `Gitter Chatroom`_.

This work is funded by the NIH grant U24-CA194362-01_.

.. _Digital Slide Archive: http://github.com/DigitalSlideArchive
.. _Docker: https://www.docker.com/
.. _Kitware: http://www.kitware.com/
.. _U24-CA194362-01: http://grantome.com/grant/NIH/U24-CA194362-01

.. _CherryPy: http://www.cherrypy.org/
.. _Girder: http://girder.readthedocs.io/en/latest/
.. _girder_worker: http://girder-worker.readthedocs.io/en/latest/
.. _large_image: https://github.com/girder/large_image
.. _slicer_cli_web: https://github.com/girder/slicer_cli_web
.. _slicer execution model: https://www.slicer.org/slicerWiki/index.php/Slicer3:Execution_Model_Documentation
.. _Discourse forum: https://discourse.girder.org/c/histomicstk
.. _Gitter Chatroom: https://gitter.im/DigitalSlideArchive/HistomicsTK?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

