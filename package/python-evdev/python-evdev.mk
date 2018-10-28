################################################################################
#
# python-evdev
#
################################################################################

PYTHON_EVDEV_VERSION = 1.1.2
PYTHON_EVDEV_SOURCE = evdev-$(PYTHON_EVDEV_VERSION).tar.gz
PYTHON_EVDEV_SITE = https://files.pythonhosted.org/packages/7e/53/374b82dd2ccec240b7388c65075391147524255466651a14340615aabb5f
PYTHON_EVDEV_SETUP_TYPE = setuptools
PYTHON_EVDEV_LICENSE = MIT
PYTHON_EVDEV_LICENSE_FILES = PKG-INFO
PYTHON_EVDEV_BUILD_OPTS += --evdev-header $(STAGING_DIR)/usr/include/linux/input.h:$(STAGING_DIR)/usr/include/linux/input-event-codes.h:$(STAGING_DIR)/usr/include/uinput.h



define PYTHON_EVDEV_BUILD_CMDS
        cd $(PYTHON_EVDEV_BUILDDIR); \
                $(PYTHON_EVDEV_BASE_ENV) $(PYTHON_EVDEV_ENV) \
                $(PYTHON_EVDEV_PYTHON_INTERPRETER) setup.py build build_ecodes \
                $(PYTHON_EVDEV_BASE_BUILD_OPTS) $(PYTHON_EVDEV_BUILD_OPTS) build_ext
endef

define PYTHON_EVDEV_INSTALL_TARGET_CMDS
        cd $(PYTHON_EVDEV_BUILDDIR); \
                $(PYTHON_EVDEV_BASE_ENV) $(PYTHON_EVDEV_ENV) \
                $(PYTHON_EVDEV_PYTHON_INTERPRETER) setup.py build build_ecodes \
                $(PYTHON_EVDEV_BUILD_OPTS) build_ext install \
                $(PYTHON_EVDEV_BASE_INSTALL_TARGET_OPTS) \
                $(PYTHON_EVDEV_INSTALL_TARGET_OPTS)
endef

$(eval $(python-package))
