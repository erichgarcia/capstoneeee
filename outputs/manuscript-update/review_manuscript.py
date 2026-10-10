from docx import Document
import json,os
from PIL import Image
p=Document(r'C:/Users/Erich Garcia/Downloads/Capstone_Progress_Final-main (2)/outputs/manuscript-update/source.docx')
json.dump([{'i':i,'text':x.text,'style':x.style.name,'image':bool(x._p.xpath('.//w:drawing'))} for i,x in enumerate(p.paragraphs)],open(r'C:/Users/Erich Garcia/Downloads/Capstone_Progress_Final-main (2)/outputs/manuscript-update/paragraphs.json','w'),indent=2)
files=[]
for base in [r'C:/Users/Erich Garcia/Downloads',r'C:/Users/Erich Garcia/Downloads/Telegram Desktop']:
 if not os.path.isdir(base):continue
 for n in os.listdir(base):
  f=os.path.join(base,n)
  if n.lower().endswith(('.png','.jpg','.jpeg')):
   try:
    im=Image.open(f);w,h=im.size
    if w>1500 and h>650 and h<1200:files.append({'path':f,'size':[w,h],'mtime':os.path.getmtime(f)})
   except:pass
json.dump(sorted(files,key=lambda x:x['mtime'],reverse=True),open(r'C:/Users/Erich Garcia/Downloads/Capstone_Progress_Final-main (2)/outputs/manuscript-update/images.json','w'),indent=2)
