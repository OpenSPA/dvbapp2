#ifndef __lib_gui_epixmap_h
#define __lib_gui_epixmap_h

#include <lib/gui/ewidget.h>

class ePixmap: public eWidget
{
	int m_alphatest;
	int m_scale;
public:
	ePixmap(eWidget *parent);

	void setPixmap(gPixmap *pixmap);
	void setPixmap(ePtr<gPixmap> &pixmap);
	void setPixmapFromFile(const char *filename);
	void setAlphatest(int alphatest); /* 1 for alphatest, 2 for alphablend */
	void setScale(int scale);
	void setPixmapScaleFlags(int flags);
	void setBorderWidth(int pixel);
	void setBorderColor(const gRGB &color);
	void setGradient(const gRGB &startcolor, const gRGB &endcolor, int direction, int blend);

	enum
	{
		GRADIENT_VERTICAL = 0,
		GRADIENT_HORIZONTAL = 1
	};

protected:
	ePtr<gPixmap> m_pixmap;
	int event(int event, void *data=0, void *data2=0);
	void checkSize();
private:
	enum eLabelEvent
	{
		evtChangedPixmap = evtUserWidget,
	};
	bool m_have_border_color, m_gradient_set;
	int m_border_width, m_gradient_direction;
	gRGB m_border_color, m_gradient_startcolor, m_gradient_endcolor;
};

#endif
