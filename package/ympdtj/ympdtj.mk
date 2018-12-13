################################################################################
#
# ympd-tjay
#
################################################################################

YMPDTJ_VERSION = master
YMPDTJ_SITE = $(call github,tjay,ympd,$(YMPDTJ_VERSION))
YMPDTJ_LICENSE = GPL-2.0
YMPDTJ_LICENSE_FILES = LICENSE
YMPDTJ_DEPENDENCIES = libmpdclient

ifeq ($(BR2_PACKAGE_OPENSSL),y)
YMPDTJ_DEPENDENCIES += openssl
YMPDTJ_CONF_OPTS += -DWITH_SSL=ON
else
YMPDTJ_CONF_OPTS += -DWITH_SSL=OFF
endif

$(eval $(cmake-package))
