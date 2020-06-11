import cv2
import numpy as np

def gen_mask(image):
	h,w, *_ = image.shape
	c_x = 0.49
	c_y = 0.515
	r = 0.58
	circle_x = int(w*c_x)
	circle_y = int(h*c_y)
	circle_r = int(r*h)            
	mask = np.zeros([h,w], dtype=np.uint8)
	cv2.circle(mask, (circle_x, circle_y), circle_r, 255, -1)
	return mask

def draw_mask(image):
	h,w, *_ = image.shape
	c_x = 0.49
	c_y = 0.515
	r = 0.58
	circle_x = int(w*c_x)
	circle_y = int(h*c_y)
	circle_r = int(r*h)            
	cv2.circle(image, (circle_x, circle_y), circle_r, (0,255,0), 5)
	return image


def prep_img(image, factor=1.0):
	height, width, *_ = image.shape
	newsize = (int(width/factor),int(height/factor))
	resized = cv2.resize(image, newsize)
	blurred = cv2.GaussianBlur(resized, ksize=(9,9), sigmaX=0)
	return blurred

def crop_rect(image, rect):
	# get new and old coordinates
	height, width, *_ = image.shape
	new_height, new_width = np.float32(rect[1])
	
	# generate src and dst triangle
	dst = np.float32([[new_width,0], [0,0], [0,new_height]])
	box = cv2.boxPoints(rect)
	src = np.flip(np.float32(box[0:3]),1)
	
	# do transform
	m_crop = cv2.getAffineTransform(src, dst)
	img_crop =  cv2.warpAffine(image, m_crop, (int(new_width), int(new_height)))

	return img_crop

def to_jpg(image):
	params = list()
	params.append(cv2.IMWRITE_JPEG_QUALITY)
	params.append(90) # compression level
	ret, image_encoded = cv2.imencode('.jpg', image, params)
	return image_encoded.tobytes()

def to_png(image):
	params = list()
	params.append(cv2.IMWRITE_PNG_COMPRESSION)
	params.append(9) # compression level
	ret, image_encoded = cv2.imencode('.png', image, params)
	return image_encoded.tobytes()

def find_rect(img_org):
	# reduce image size for speed
	factor = 4

	# use gray only
	img_gray = cv2.cvtColor(img_org, cv2.COLOR_RGB2GRAY)

	# resize and blur
	img_prep = prep_img(img_gray, factor)
	mask = gen_mask(img_prep)

	# detect edges
	img_canny = cv2.Canny(img_prep,16,48)
	img_canny_masked = cv2.bitwise_and(img_canny, mask)
	edges = np.nonzero(img_canny_masked)

	# if too few edges found, return None
	if len(edges[0]) < 100:
		return False
	
	# crop onto found edges
	(cx,cy),(sx,sy),r = cv2.minAreaRect(np.transpose(edges)) # center, size and rotation
	rect = ((cx*factor,cy*factor),(sx*factor,sy*factor),r) # scale center and size
	return rect

def autocrop_rect(img_org):
	rect = find_rect(img_org)
	if rect == False:
		return img_org, False
	else:
		img_crop = crop_rect(img_org, rect)
		img_landscape = auto_landscape(img_crop)
		img_leveled = auto_level(img_landscape)
		return img_leveled, True

def autocrop_rect_hdr(hdr_series):
	max_exp = max(hdr_series)
	rect = find_rect(hdr_series[max_exp])
	if rect == False:
		return hdr_series[max_exp], False
	else:
		hdr_crop = {}
		for exp in hdr_series.keys():
			hdr_crop[exp] = crop_rect(hdr_series[exp], rect)

		img_out = hdr_process(hdr_crop)
		img_landscape = auto_landscape(img_out)
		return img_landscape, True

def autocrop_ring(img_org):
	# reduce image size for speed
	factor = 4

	# use gray only
	img_gray = cv2.cvtColor(img_org, cv2.COLOR_RGB2GRAY)
	#if img_gray.dtype == np.uint16:
	#	img_gray = (img_gray/256).astype('uint8')

	# resize and blur
	img_prep = prep_img(img_gray, factor)
	mask = gen_mask(img_prep)

	# detect edges, threshold and mask
	img_thrs = cv2.adaptiveThreshold(img_prep, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 20)
	img_thrs_masked = cv2.bitwise_and(img_thrs, mask)
	edges = np.transpose(np.nonzero(img_thrs_masked))
	
	# get circle parameters and scale to full size
	(mask_x, mask_y), mask_r = cv2.minEnclosingCircle(edges)
	mask_x = int(mask_x * factor)
	mask_y = int(mask_y * factor)
	mask_r = int(mask_r * factor)

	x1 = max(mask_x-mask_r, 0)
	x2 = min(mask_x+mask_r, img_org.shape[0])
	y1 = max(mask_y-mask_r, 0)
	y2 = min(mask_y+mask_r, img_org.shape[1])

	# if too small radius (<30%) or too much off center, fail
	min_radius = 0.3
	#max_outside = 0.3
	min_axis = min(img_org.shape[0:1])
	rel_r = mask_r / min_axis # size of r relative to shortest axis
	#rel_x = abs((mask_x / min_axis) - 0.5)*2
	#rel_y = abs((mask_y / min_axis) - 0.5)*2

	if rel_r < min_radius:
		return img_org, False
	
	# set pizels outside circle to black
	mask = np.zeros_like(img_org)
	cv2.circle(mask, (mask_y, mask_x), mask_r, (255,255,255), -1)
	img_out = cv2.bitwise_and(img_org, mask)
	img_out = img_out[x1:x2, y1:y2]

	return img_out, True

def auto_level(img):
	# histogram equalization
	img_yuv = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
	clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
	img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
	return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)

def auto_landscape(img):
	# rotate to landscape if needed
	if img.shape[0] > img.shape[1]:
		return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
	else:
		return img

def hdr_process(hdr_series):
	# mask images
	exp = np.array([1./e for e in hdr_series.keys()], dtype=np.float32)
	img = list(hdr_series.values())
	
	# Merge exposures to HDR image
	merge_mertens = cv2.createMergeMertens()
	hdr_img = merge_mertens.process(img)

	# Tonemap HDR image
	#tonemap1 = cv2.createTonemap(gamma=2.2)
	#img_tonemap = tonemap1.process(hdr_img)

	img_out = np.clip(hdr_img*255, 0, 255).astype('uint8')

	return img_out
	
	
