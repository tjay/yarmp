################################################################################
#
# python-python-mpd2
#
################################################################################

PYTHON_MPD2_VERSION = 1.0.0
PYTHON_MPD2_SOURCE = python-mpd2-$(PYTHON_MPD2_VERSION).tar.bz2
PYTHON_MPD2_SITE = https://files.pythonhosted.org/packages/a8/12/63bdb3ee8e0bd7dd0476e79f0f130c1caeff408a1b1e5531ae9891805f7d
PYTHON_MPD2_SETUP_TYPE = setuptools
PYTHON_MPD2_LICENSE = MIT
PYTHON_MPD2_LICENSE_FILES = PKG-INFO

$(eval $(python-package))
