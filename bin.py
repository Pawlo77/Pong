from PIL import Image
import PIL.ImageOps    

image = Image.open('info2.jpeg')

inverted_image = PIL.ImageOps.invert(image)

inverted_image.save('info2.jpeg')