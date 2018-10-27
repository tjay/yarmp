################################################################################
#
# python-rpio
#
################################################################################

PYTHON_RPIO_VERSION = v2
PYTHON_RPIO_SITE = $(call github,JamesGKent,RPIO,$(PYTHON_RPIO_VERSION))
PYTHON_RPIO_SETUP_TYPE = setuptools
PYTHON_RPIO_LICENSE = GPL
PYTHON_RPIO_LICENSE_FILES = PKG-INFO
PYTHON_RPIO_SUBDIR = .
PYTHON_RPIO_EXCLUDES = source/scripts/man 

$(eval $(python-package))
$(eval $(host-python-package))
