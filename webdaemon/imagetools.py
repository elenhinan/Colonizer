import cv2
import numpy as np
from settings import settings

def get_circle(image):
   h,w, *_ = image.shape
   c_x = settings["autocrop"]["settleplate"]["c_x"]
   c_y = settings["autocrop"]["settleplate"]["c_y"]
   c_r = settings["autocrop"]["settleplate"]["c_r"]
   circle_x = int(w*c_x)
   circle_y = int(h*c_y)
   circle_r = int(h*c_r)
   return circle_x, circle_y, circle_r     

def gen_mask(image):
   h,w, *_ = image.shape
   circle_x, circle_y, circle_r = get_circle(image)
   mask = np.zeros([h,w], dtype=np.uint8)
   cv2.circle(mask, (circle_x, circle_y), circle_r, 1, -1)
   return mask

def draw_mask(image):
   circle_x, circle_y, circle_r = get_circle(image)         
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
   factor = 8

   # use gray only
   img_gray = cv2.cvtColor(img_org, cv2.COLOR_RGB2GRAY)

   # resize and blur
   img_prep = prep_img(img_gray, factor)
   mask = gen_mask(img_prep)

   # detect edges
   t1 = settings["autocrop"]["plate"]["canny_t1"]
   t2 = settings["autocrop"]["plate"]["canny_t2"]
   img_canny = cv2.Canny(img_prep,t1,t2)
   img_canny_masked = img_canny * mask
   edges = np.nonzero(img_canny_masked)

   # if too few edges found, return None
   if len(edges[0]) < 100:
      return False
   
   # crop onto found edges
   (cx,cy),(sx,sy),r = cv2.minAreaRect(np.transpose(edges)) # center, size and rotation
   rect = ((cx*factor,cy*factor),(sx*factor,sy*factor),r) # scale center and size
   return rect

def mask_image(img_org):
   mask = gen_mask(img_org)
   img_masked = img_org * mask[...,None]
   return img_masked

def autocrop_rect(img_org):
   rect = find_rect(img_org)
   if rect == False:
      return img_org
   else:
      img = crop_rect(img_org, rect)
      img = auto_landscape(img)
      if settings["autocrop"]["plate"]["autolevel"]:
         img = auto_level(img)
      return img

def autocrop_ring(img_org, color=(0,0,0)):
   # reduce image size for speed
   factor = 8

   # use gray only
   img_gray = cv2.cvtColor(img_org, cv2.COLOR_RGB2GRAY)
   #if img_gray.dtype == np.uint16:
   #	img_gray = (img_gray/256).astype('uint8')

   # resize and blur
   img_prep = prep_img(img_gray, factor)
   mask = gen_mask(img_prep)

   # detect edges, threshold and mask
   img_thrs = cv2.adaptiveThreshold(img_prep, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 10)
   img_thrs_masked = img_thrs * mask
   edges = np.transpose(np.nonzero(img_thrs_masked))
   
   # get circle parameters and scale to full size
   (mask_x, mask_y), mask_r = cv2.minEnclosingCircle(edges)
   mask_x = int(mask_x * factor+0.5)
   mask_y = int(mask_y * factor+0.5)
   mask_r = int(mask_r * factor+0.5)

   x1 = max(mask_x-mask_r, 0)
   x2 = min(mask_x+mask_r, img_org.shape[0])
   y1 = max(mask_y-mask_r, 0)
   y2 = min(mask_y+mask_r, img_org.shape[1])

   # if too small radius (<30%) or too much off center, fail
   min_radius = 0.2
   #max_outside = 0.3
   min_axis = min(img_org.shape[0:1])
   rel_r = mask_r / min_axis # size of r relative to shortest axis
   #rel_x = abs((mask_x / min_axis) - 0.5)*2
   #rel_y = abs((mask_y / min_axis) - 0.5)*2

   if rel_r < min_radius:
      return img_org
   
   # set pizels outside circle to color
   mask = np.zeros_like(img_org)
   cv2.circle(mask, (mask_y, mask_x), mask_r, color, -1)
   img_out = cv2.bitwise_and(img_org, mask)
   img_out = img_out[x1:x2, y1:y2]

   return img_out

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
   
def rotate_image(image, rotation):
   rotation = rotation.lower()
   if rotation == 'cw':
      dir = cv2.ROTATE_90_CLOCKWISE
   elif rotation == 'ccw':
      dir = cv2.ROTATE_90_COUNTERCLOCKWISE
   elif rotation == '180':
      dir = cv2.ROTATE_180
   else:
      return image
   return cv2.rotate(image, dir)