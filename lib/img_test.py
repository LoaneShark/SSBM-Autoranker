import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from matplotlib.patches import Circle
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,AnnotationBbox)
from matplotlib.cbook import get_sample_data

def getImage(path,zoom=0.1):
	return OffsetImage(plt.imread(path),zoom=zoom)

def main():
	fig, ax = plt.subplots(1,1)
	artists = []
	x = [0,1,2,3,4]
	y = [0,1,2,3,4]
	A = np.random.random(size=(5,5))
	ax.matshow(A)

	xl, yl, xh, yh=np.array(ax.get_position()).ravel()
	print(xl, yl, xh, yh)
	w=xh-xl
	h=yh-yl
	xp=xl+w*0.5 #if replace '0' label, can also be calculated systematically using xlim()
	print(xp)
	size=0.01

	#for x0, y0 in zip(x, y):
	ab = AnnotationBbox(getImage('../lib/todd2.jpg'), (xp-size*0.5, yh), frameon=False, box_alignment=(0.,0.))
	artists.append(ax.add_artist(ab))

	plt.show()

def old_test():
	A = np.random.random(size=(5,5))
	fig, ax = plt.subplots(1, 1)

	xl, yl, xh, yh=np.array(ax.get_position()).ravel()
	print(xl, yl, xh, yh)
	w=xh-xl
	h=yh-yl
	xp=xl+w*0.5 #if replace '0' label, can also be calculated systematically using xlim()
	print(xp)
	size=0.1

	img=mpimg.imread('todd2.jpg',format='jpg')
	ax.matshow(A)
	ax1=fig.add_axes([xp-size*0.5, yh, size, size])
	ax1.axison = False
	imgplot = ax1.imshow(img,transform=ax.transAxes)

	plt.show()

if __name__ == '__main__':

	main()

	if False:
		old_test()

	if True:
		fig, ax = plt.subplots()

		# Define a 1st position to annotate (display it with a marker)
		xy = (0.5, 0.7)
		ax.plot(xy[0], xy[1], ".r")

		# Annotate the 1st position with a text box ('Test 1')
		offsetbox = TextArea("Test 1", minimumdescent=False)

		ab = AnnotationBbox(offsetbox, xy,xybox=(-20, 40),xycoords='data',boxcoords="offset points",\
							arrowprops=dict(arrowstyle="->"))
		ax.add_artist(ab)

		# Annotate the 1st position with another text box ('Test')
		offsetbox = TextArea("Test", minimumdescent=False)

		ab = AnnotationBbox(offsetbox, xy,xybox=(1.02, xy[1]),xycoords='data',boxcoords=("axes fraction", "data"),\
							box_alignment=(0., 0.5),arrowprops=dict(arrowstyle="->"))
		ax.add_artist(ab)

		# Define a 2nd position to annotate (don't display with a marker this time)
		xy = [0.3, 0.55]

		# Annotate the 2nd position with a circle patch
		da = DrawingArea(20, 20, 0, 0)
		p = Circle((10, 10), 10)
		da.add_artist(p)

		ab = AnnotationBbox(da, xy,xybox=(1.02, xy[1]),xycoords='data',\
			boxcoords=("axes fraction", "data"),box_alignment=(0., 0.5),arrowprops=dict(arrowstyle="->"))

		ax.add_artist(ab)

		# Annotate the 2nd position with an image (a generated array of pixels)
		arr = np.arange(100).reshape((10, 10))
		im = OffsetImage(arr, zoom=2)
		im.image.axes = ax

		ab = AnnotationBbox(im, xy,xybox=(-50., 50.),xycoords='data',\
							boxcoords="offset points",pad=0.3,arrowprops=dict(arrowstyle="->"))

		ax.add_artist(ab)

		'''# Annotate the 2nd position with another image (a Grace Hopper portrait)
		fn = get_sample_data("grace.png", asfileobj=False)
		arr_img = plt.imread(fn, format='png')

		imagebox = OffsetImage(arr_img, zoom=0.2)
		imagebox.image.axes = ax

		ab = AnnotationBbox(imagebox, xy,xybox=(120., -80.),xycoords='data',boxcoords="offset points",pad=0.5,\
							arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=90,rad=3"))

		ax.add_artist(ab)'''

		# Fix the display limits to see everything
		ax.set_xlim(0, 1)
		ax.set_ylim(0, 1)

		plt.show()