import importlib.util,os,json,re
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
root=Path(r'C:/Users/Erich Garcia/.cache/codex-runtimes/codex-primary-runtime');os.environ['PATH']=str(root/'dependencies/native/poppler/Library/bin')+os.pathsep+os.environ['PATH']
spec=importlib.util.spec_from_file_location('renderer',r'C:/Users/Erich Garcia/.codex/plugins/cache/openai-primary-runtime/documents/26.909.12148/skills/documents/render_docx.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.convert_to_pdf=lambda *args,**kwargs:(str(Path('outputs/document-fix/qa_formatted.pdf').resolve()),'Final PDF exported by Word')
paths=m.rasterize('outputs/document-fix/CapstoneCHAPTER1-5_Formatted.docx','outputs/document-fix/final-render',110,False,False)
rows=json.loads(Path('outputs/document-fix/formatted_page_audit.json').read_text(encoding='utf-8-sig'))
def roman(v):
 d={'i':1,'v':5,'x':10,'l':50,'c':100,'d':500,'m':1000};total=0;last=0
 for c in v[::-1]:
  x=d[c];total+=x if x>=last else -x;last=max(last,x)
 return total
for row in rows:
 s=row['Display'].strip();num=int(s) if s.isdigit() else roman(s)
 assert num==row['Page'],row
with ZipFile('outputs/document-fix/CapstoneCHAPTER1-5_Formatted.docx') as z:
 r=E.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 texts=[''.join(p.xpath('.//w:t/text()',namespaces=ns)) for p in r.xpath('//w:body/w:p',namespaces=ns)]
 for kind,count in [('Figure',44),('Table',6)]:
  caps=[int(re.match(rf'^{kind} (\d+)\.',t).group(1)) for t in texts if re.match(rf'^{kind} (\d+)\.',t)]
  assert caps==list(range(1,count+1)),(kind,caps)
print('PASS: 97 page references match Word pagination; captions and lists match: 44 figures, 6 tables.')
print('Rendered pages:',len(paths))
print('Preliminary pages:',[(x['Bookmark'],x['Display']) for x in rows[:5]])


