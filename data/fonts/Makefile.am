installdir = $(datadir)/fonts

dist_install_DATA = \
	ae_AlMateen.ttf \
	andale.ttf \
	lcd.ttf \
	md_khmurabi_10.ttf \
	time.ttf \
	DejaVuSans.ttf \
	nmsbd.ttf \
	LiberationSans-Bold.ttf \
	LiberationSans-BoldItalic.ttf \
	LiberationSans-Italic.ttf \
	LiberationSans-Regular.ttf \
	OpenSans-Regular.ttf \
	wqy-microhei.ttc

install-data-hook:
	cd $(DESTDIR)$(datadir)/fonts && \
	$(LN_S) wqy-microhei.ttc fallback.font

if VUULTIMO
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf
endif

if VUDUO2
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf
endif

if ET10000
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf
endif

if SKYLAKE
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf
endif

if INIHDP
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf
endif

if VUSOLO4K
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf verdana.ttf
endif

if VUULTIMO4K
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf verdana.ttf
endif

if VUUNO4KSE
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf
endif

if VUDUO4K
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf
endif

if ET8500
dist_install_DATA += verdana.ttf
endif

if ET8500S
dist_install_DATA += verdana.ttf
endif

if HAVE_COLORLCD220
dist_install_DATA += hd2.ttf tuxtxt2.ttf
endif

if HAVE_COLORLCD400
dist_install_DATA += hd2.ttf tuxtxt2.ttf robotobold.ttf robotoregular.ttf OpenSans-Regular.ttf verdana.ttf
endif

if HAVE_COLORLCD400S
dist_install_DATA += hd2.ttf tuxtxt2.ttf robotobold.ttf robotoregular.ttf verdana.ttf
endif

if OSMIO4KPLUS
dist_install_DATA += analog.ttf MyriadPro-Regular.otf MyriadPro-Semibold.otf MyriadPro-SemiboldIt.otf
endif
