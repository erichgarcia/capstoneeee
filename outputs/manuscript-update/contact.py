from PIL import Image,ImageDraw
import glob,os
files=sorted(glob.glob(r'C:/Users/Erich Garcia/Downloads/Capstone_Progress_Final-main (2)/outputs/manuscript-update/Screenshot*.png'))
canvas=Image.new('RGB',(1200,((len(files)+2)//3)*230),'white');d=ImageDraw.Draw(canvas)
for i,f in enumerate(files):
 im=Image.open(f);im.thumbnail((390,195));x=(i%3)*400;y=(i//3)*230;canvas.paste(im,(x,y));d.text((x,y+197),os.path.basename(f),fill='black')
canvas.save(r'C:/Users/Erich Garcia/Downloads/Capstone_Progress_Final-main (2)/outputs/manuscript-update/contact.png')
