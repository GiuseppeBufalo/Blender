/*
WINDOWS = Scatter/cpp/x64/Release/scatter.dll
  -Open 'scatter.vcxproj' from VisualStudio (default = dynamic lib project)
  -'extern "C"' needed for each function
  -'__declspec(dllexport)' = specific for windows os
  -use 'ctrl+shift+b' to refresh the dll file
  -need to create one dll per os, and procedurally choose correct lib in py TODO
*/

#include "pch.h"
#include <stdio.h>
#include <iostream> 
using namespace std;

//windows specific classmethod 
#ifdef _WIN32
#define DECLSPEC __declspec(dllexport)
#else
#define DECLSPEC 
#endif 


  ///////  ///////  ///////  ////////////////////  ///////  ///////  ///////  
 ///////  ///////  ///////  ///// GLOBALS //////  ///////  ///////  ///////  
///////  ///////  ///////  ////////////////////  ///////  ///////  ///////  


//global pixel array, used in draw_point function
static double* _pixels = nullptr;

//global res_x, res_y
static int res_x = 0;
static int res_y = 0;


  ///////  ///////  ///////  ////////////////////////  ///////  ///////  ///////
 ///////  ///////  ///////  ///// POINT CLASS //////  ///////  ///////  ///////  
///////  ///////  ///////  ////////////////////////  ///////  ///////  ///////  


struct Point {
	double x, y, r, g, b;
};


  ///////  ///////  ///////  ///////////////////////  ///////  ///////  ///////
 ///////  ///////  ///////  ///// DRAW POINT //////  ///////  ///////  ///////  
///////  ///////  ///////  ///////////////////////  ///////  ///////  ///////  


static void draw_point(const int y, const int x, const double r, const double g, const double b) {

	//reading pixels array:
	//origin = bottom left
	//reading row from left to right first on x axis, bottom to top on y axis
	//See example below to add in rasterize_tris 
	
	_pixels[(y * res_x + x) * 4 + 0] = r;
	_pixels[(y * res_x + x) * 4 + 1] = g;
	_pixels[(y * res_x + x) * 4 + 2] = b;
	_pixels[(y * res_x + x) * 4 + 3] = 1;
}


/*
for (int x = 0; x < res_x; ++x) {
	for (int y = 0; y < res_y; ++y) {
		_pixels[(y * res_x + x) * 4 + 0] = y * 1. / 512.;
		_pixels[(y * res_x + x) * 4 + 1] = x * 1. / 512.;
		_pixels[(y * res_x + x) * 4 + 2] = 0;
		_pixels[(y * res_x + x) * 4 + 3] = 1;
	}
}
return;
*/


  ///////  ///////  ///////  ///////////////////////  ///////  ///////  ///////
 ///////  ///////  ///////  ///// RASTER LINE /////  ///////  ///////  /////// 
///////  ///////  ///////  ///////////////////////  ///////  ///////  ///////  


static void raster_line(const int y, const Point* pa, const Point* pb) {

	//raster from left to right 

	//No line but a single point ? draw point directly!
	//(only if point not out of bounds)

	if (pa->x == pb->x) {
		if (pa->x >= 0) {
			if (pa->x < res_x) {
				draw_point(y, pa->x, pa->r, pa->g, pa->b);
			}
			return;
		}
	}

	//we need var to change.., don't touch our const arg

	const Point* left = pa;
	const Point* right = pb;

	//always left to right! if not reverse

	if (left->x > right->x) {
		const Point* temp;
		temp = left;
		left = right;
		right = temp;
	}

	//rgb values to interpolate

	double r = left->r;
	double g = left->g;
	double b = left->b;

	//and their delta 
	double dx = right->x - left->x;
	double delta_r = (right->r - left->r) / dx;
	double delta_g = (right->g - left->g) / dx;
	double delta_b = (right->b - left->b) / dx;

	//below = check if we are going out of pixel array bounds!

	int minx = 0.5 + left->x;

	if (minx < 0) {
		r -= minx * delta_r;
		g -= minx * delta_g;
		b -= minx * delta_b;
		minx = 0;
	}

	int maxx = 0.5 + right->x;

	if (maxx >= res_x - 1) {
		maxx = res_x - 1;
	}

	//draw each pixel on the line

	for (int x = minx; x < maxx + 1; ++x) {// = python "x in range(minx, maxx + 1)"?

		draw_point(y, x, r, g, b);

		//increment rgb

		r += delta_r;
		g += delta_g;
		b += delta_b;
	}
}


  ///////  ///////  ///////  ///////////////////////  ///////  ///////  ///////
 ///////  ///////  ///////  ///// RASTER TRI //////  ///////  ///////  ///////  
///////  ///////  ///////  ///////////////////////  ///////  ///////  ///////   


static void rasterize_tri(const Point* p1, const Point* p2, const Point* p3) {

	//get Low,Medium,High points pointer from p1,p2,p3

	const Point* l = p1; //aliasing
	const Point* m = p2;
	const Point* h = p3;

	//Sort points from Low to High, depending on Y coord 

	if (m->y < l->y) { const Point* s = l; l = m; m = s; }
	if (h->y < l->y) { const Point* s = l; l = h; h = s; }
	if (h->y < m->y) { const Point* s = m; m = h; h = s; }

	//cout << l->y << endl;
	//cout << m->y << endl;
	//cout << h->y << endl;
	//cout << endl;

	//get Y distance from one point to another in px

	const double lh_y = h->y - l->y; //from y low to y high
	const double lm_y = m->y - l->y; //from y low to y mid
	const double mh_y = h->y - m->y; //from y mid to y high

	//skip if tris is empty 

	if (lh_y <= 0) return;

	//incremented variables + incrementation steps

	Point Plh = *l; //point that will move on the vector lh
	double _lhX = (h->x - l->x) / lh_y;  //incrementation delta x
	double _lhR = (h->r - l->r) / lh_y;  //incrementation delta r
	double _lhG = (h->g - l->g) / lh_y;  //incrementation delta g
	double _lhB = (h->b - l->b) / lh_y;  //incrementation delta b


	////////////// separate our triangle in two //////////////


	if (lm_y > 0) { //is there's an lower triangle?

		//incremented variables + incrementation steps

		Point Plm = *l; //point that will move on the vector lm
		double _lmX = (m->x - l->x) / lm_y;  //incrementation delta x
		double _lmR = (m->r - l->r) / lm_y;  //incrementation delta r
		double _lmG = (m->g - l->g) / lm_y;  //incrementation delta g
		double _lmB = (m->b - l->b) / lm_y;  //incrementation delta b

		//below = crop if out of pixels array bounds

		int miny = 0.5 + l->y;
		int maxy = 0.5 + m->y;

		if (miny < 0) {

			Plh.x -= _lhX * miny;
			Plh.r -= _lhR * miny;
			Plh.g -= _lhG * miny;
			Plh.b -= _lhB * miny;

			Plm.x -= _lmX * miny;
			Plm.r -= _lmR * miny;
			Plm.g -= _lmG * miny;
			Plm.b -= _lmB * miny;

			miny = 0;
		}

		if (maxy >= res_y) {
			maxy = res_y - 1;
		}

		//rasterize lower triangle

		for (int y = miny; y < maxy; y++) { //= like python "for y in range(miny, maxy)" ?

			//rasterize line on y from Plh to Plm point, with interpolated rgb values

			raster_line(y, &Plh, &Plm);

			//increment the two points x location and their interpolated rgb values

			Plh.x += _lhX;
			Plh.r += _lhR;
			Plh.g += _lhG;
			Plh.b += _lhB;

			Plm.x += _lmX;
			Plm.r += _lmR;
			Plm.g += _lmG;
			Plm.b += _lmB;

		}
	}


	////////////// separate our triangle in two //////////////


	if (mh_y > 0) { //is there's an upper triangle?

		//incremented variables + incrementation steps

		Point Pmh = *m; //point that will move on the vector mh
		double _mhX = (h->x - m->x) / mh_y;  //incrementation delta x
		double _mhR = (h->r - m->r) / mh_y;  //incrementation delta r
		double _mhG = (h->g - m->g) / mh_y;  //incrementation delta g
		double _mhB = (h->b - m->b) / mh_y;  //incrementation delta b

		//below = crop if out of pixels array bounds

		int miny = 0.5 + m->y;
		int maxy = 0.5 + h->y;

		if (miny < 0) {

			Plh.x -= _lhX * miny;
			Plh.r -= _lhR * miny;
			Plh.g -= _lhG * miny;
			Plh.b -= _lhB * miny;

			Pmh.x -= _mhX * miny;
			Pmh.r -= _mhR * miny;
			Pmh.g -= _mhG * miny;
			Pmh.b -= _mhB * miny;

			miny = 0;
		}

		if (maxy >= res_y) {
			maxy = res_y - 1;
		}

		//rasterize upper triangle

		for (int y = miny; y < maxy; y++) { //= like python "for y in range(miny, maxy)" ?

			//rasterize line on y from Plh to Plm point, with interpolated rgb values

			raster_line(y, &Plh, &Pmh);

			//increment the two points x location and their interpolated rgb values

			Plh.x += _lhX;
			Plh.r += _lhR;
			Plh.g += _lhG;
			Plh.b += _lhB;

			Pmh.x += _mhX;
			Pmh.r += _mhR;
			Pmh.g += _mhG;
			Pmh.b += _mhB;
		}
	}
}


  ///////  ///////  ///////  //////////////////////  ///////  ///////  ///////    
 ///////  ///////  ///////  ///// DLL FUNCT //////  ///////  ///////  ///////    
///////  ///////  ///////  //////////////////////  ///////  ///////  ///////    


extern "C" DECLSPEC
void rasterize_tris(const double* tris, double* pixels, const size_t tri_nbr, const int resolution) {

	// define globals used by fcts

	_pixels = pixels; //aliasing
	res_x = resolution;
	res_y = resolution;

	//create pt pointer on 5 double

	const Point* pt = reinterpret_cast<const Point*>(tris);

	for (size_t t = 0; t < tri_nbr; ++t) {

		//get the 3 points, xyrgb format 

		const Point* p1 = pt++;
		const Point* p2 = pt++;
		const Point* p3 = pt++;

		rasterize_tri(p1, p2, p3);
	}
}
