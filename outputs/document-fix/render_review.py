import importlib.util,os,json
from pathlib import Path
root=Path(r'C:/Users/Erich Garcia/.cache/codex-runtimes/codex-primary-runtime')
os.environ['PATH']=str(root/'dependencies/native/poppler/Library/bin')+os.pathsep+os.environ['PATH']
spec=importlib.util.spec_from_file_location('renderer',r'C:/Users/Erich Garcia/.codex/plugins/cache/openai-primary-runtime/documents/26.909.12148/skills/documents/render_docx.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Windows bundle has no LibreOffice. Use Word's finalized pagination for rendering.
m.convert_to_pdf=lambda *args,**kwargs:(str(Path('outputs/document-fix/qa_document.pdf').resolve()),'PDF exported by Microsoft Word')
paths=[str(Path(f'outputs/document-fix/render/page-{i}.png')) for i in range(1,159)]
print('Rendered pages:',len(paths))
import pdfplumber
pdf=pdfplumber.open('outputs/document-fix/qa_document.pdf').pages
for i in range(11):
 print('PAGE',i+1);print(pdf[i].extract_text()[:4000])
rows=json.loads(Path('outputs/document-fix/word_page_audit.json').read_text(encoding='utf-8-sig'))
errors=[]
for row in rows:
 if not row['Display'].strip() or 'Error' in row['Display']:errors.append(row)
print('Invalid references:',errors)
from PIL import Image,ImageDraw
for start in range(0,len(paths),20):
 sheet=Image.new('RGB',(1800,5*480),'#ddd');d=ImageDraw.Draw(sheet)
 for j,path in enumerate(paths[start:start+20]):
  im=Image.open(path);im.thumbnail((440,445));x=(j%4)*450;y=(j//4)*480;sheet.paste(im,(x,y+25));d.text((x+10,y+5),str(start+j+1),fill='black')
 sheet.save(f'outputs/document-fix/contact-{start//20+1}.png')

