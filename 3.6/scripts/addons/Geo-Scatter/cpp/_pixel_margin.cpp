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


  ///////  ///////  ///////  //////////////////////  ///////  ///////  ///////    
 ///////  ///////  ///////  ///// DLL FUNCT //////  ///////  ///////  ///////    
///////  ///////  ///////  //////////////////////  ///////  ///////  ///////    



/*
WHAT IS "extern "C" ?

Name mangling:
Dans le code, on ecrit par ex:
int fct(double x) {...}
Ca signifie:
Name:fct ; arg:double; return int
En C++, c'est compilé sous la forme (par ex):
"GfctA1DRi" devient le nom interne de la fct
En C, le nom interne est juste: "fct"
Avec extern "C" on dit de ne pas faire de name mangling.
*/


struct Pixel {
	double r, g, b, a;
};



//looping every pixels by row (y,-y,x,-x) and when finding a empty pixel just next to full, 
extern "C" DECLSPEC
void pixel_margin(double* pixels, const int resolution, const int iteration) {

	int res_x = resolution;
	int res_y = resolution;

	//w will check if last pixels was empty or not (by looking at alpha channel)
	//w value will be reset on each rows
	bool w;

	cout << "test" << endl;


	//create pointer on pixel	
	//set pointer ppt on position 0 of array 
	
	for (int i = 0; i < iteration; ++i) {
		Pixel* ppt = reinterpret_cast<Pixel*>(pixels);

		//loop pixels horizontal
		for (int y = 0; y < res_y; ++y) {
			w = false;
			for (int x = 0; x < res_x; ++x, ++ppt) {

				//if found a full pixel, mark w
				if (ppt->a > 0) {
					w = true;

					//if last pixel was empty, add bleed to last
					if (x != 0) {
						if ((ppt - 1)->a == 0)  {
							(ppt - 1)->r = ppt->r;
							(ppt - 1)->g = ppt->g;
							(ppt - 1)->b = ppt->b;
							(ppt - 1)->a = 1;
						}
					}
				}
				//otherwise if found an empty pixel and w is marked, that means we need to add some bleeding, then reset w
				else {
					if (w == true) {
						ppt->r = (ppt - 1)->r;
						ppt->g = (ppt - 1)->g;
						ppt->b = (ppt - 1)->b;
						ppt->a = 1;
						w = false;
					}
				}
			}
		}

		
		//set pointer ppt on position 0 of array 
		ppt = reinterpret_cast<Pixel*>(pixels); // eqv à: ppt = (Pixel*)pixels;
		Pixel* pxbegin = ppt;

		for (int x = 0; x < res_x; ++x, ++pxbegin) {
			w = false;
			ppt = pxbegin;
			for (int y = 0; y < res_y; ++y, ppt += res_x) {

				
				//if found a full pixel, mark w
				if (ppt->a > 0) {
					w = true;

					
					//if pixel last was empty, add bleed to last 
					if (y != 0) {
						if ((ppt - res_x)->a == 0) {
							(ppt - res_x)->r = ppt->r;
							(ppt - res_x)->g = ppt->g;
							(ppt - res_x)->b = ppt->b;
							(ppt - res_x)->a = 1;
						}
					}
					

				}
				//otherwise if found an empty pixel and w is marked, that means we need to add some bleeding, then reset w

				else {
					if (w == true) {
						ppt->r = (ppt - res_x)->r;
						ppt->g = (ppt - res_x)->g;
						ppt->b = (ppt - res_x)->b;
						ppt->a = 1;
						w = false;
					}
				}
				
			}
		}
		
	}
	

}





/*
//OLD VERSION OF THE CODE, without looping via ptr

extern "C" DECLSPEC
void pixel_bleeding(double* pixels, const int resolution, const int iteration) {

	// define globals used by fcts

	double* _pixels = pixels;
	int res_x = resolution;
	int res_y = resolution;

	//w will check if last pixels was empty or not (by looking at alpha channel)
	//w value will be reset on each rows
	bool w;

	//retain pixel information from last loop
	Pixel px;

	//delta used in calculation
	int _d;
	int _e;

	for (int i = 0; i < iteration; ++i) {

		//loop pixels row from down to up
		for (int x = 0; x < res_x; ++x) {
			w = false;
			for (int y = 0; y < res_y; ++y) {
				_d = (y * res_x + x) * 4;

				//if found a full pixel, mark w
				if (_pixels[_d + 3] == 1) {
					w = true;

					//if pixel last was empty, add bleed to last
					if (y != 0) {
						_e = ((y - 1) * res_x + x) * 4;
						if (_pixels[_e + 3] == 0) {
							_pixels[_e + 0] = _pixels[_d + 0];
							_pixels[_e + 1] = _pixels[_d + 1];
							_pixels[_e + 2] = _pixels[_d + 2];
							_pixels[_e + 3] = 1;
						}
					}
				}
				//otherwise if found an empty pixel and w is marked, that means we need to add some bleeding, then reset w
				else {
					if (w == true) {
						_pixels[_d + 0] = px.r;
						_pixels[_d + 1] = px.g;
						_pixels[_d + 2] = px.b;
						_pixels[_d + 3] = 1;
						w = false;
					}
				}

				px.r = _pixels[_d + 0];
				px.g = _pixels[_d + 1];
				px.b = _pixels[_d + 2];
			}
		}

		//loop pixels left to right
		for (int y = 0; y < res_y; ++y) {
			w = false;
			for (int x = 0; x < res_x; ++x) {
				_d = (y * res_x + x) * 4;

				//if found a full pixel, mark w
				if (_pixels[_d + 3] == 1) {
					w = true;

					//if pixel last was empty, add bleed to last
					if (x != 0) {
						_e = (y * res_x + (x - 1)) * 4;
						if (_pixels[_e + 3] == 0) {
							_pixels[_e + 0] = _pixels[_d + 0];
							_pixels[_e + 1] = _pixels[_d + 1];
							_pixels[_e + 2] = _pixels[_d + 2];
							_pixels[_e + 3] = 1;
						}
					}
				}
				//otherwise if found an empty pixel and w is marked, that means we need to add some bleeding, then reset w
				else {
					if (w == true) {
						_pixels[_d + 0] = px.r;
						_pixels[_d + 1] = px.g;
						_pixels[_d + 2] = px.b;
						_pixels[_d + 3] = 1;
						w = false;
					}
				}

				px.r = _pixels[_d + 0];
				px.g = _pixels[_d + 1];
				px.b = _pixels[_d + 2];
			}
		}


	}
}
*/

