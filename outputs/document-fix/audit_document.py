from zipfile import ZipFile
from lxml import etree
from pathlib import Path
p=Path(r'outputs/document-fix/source.docx')
n={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(p) as z:
 r=etree.fromstring(z.read('word/document.xml'))
 lines=[]
 for i,e in enumerate(r.xpath('//w:body/w:p | //w:body/w:tbl',namespaces=n)):
  t=''.join(e.xpath('.//w:t/text()',namespaces=n))
  st=e.xpath('./w:pPr/w:pStyle/@w:val',namespaces=n)
  lines.append(f'{i}\t{st}\t{t}')
 Path('outputs/document-fix/inventory.txt').write_text('\n'.join(lines),encoding='utf-8')
 print('\n'.join(lines[:170]))
 print('FIELDS',r.xpath('//w:instrText/text()',namespaces=n)[:50])
 print('SECTIONS',len(r.xpath('//w:sectPr',namespaces=n)))

