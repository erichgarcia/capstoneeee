from zipfile import ZipFile
from lxml import etree
n={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile('outputs/document-fix/source.docx') as z:
 r=etree.fromstring(z.read('word/document.xml')); ps=r.xpath('//w:body/w:p | //w:body/w:tbl',namespaces=n)
 for i in [37,43,84,134,137,138]:
  print(i, etree.tostring(ps[i]).decode().split('>')[1:][:3]); print(etree.tostring(ps[i]).decode()[etree.tostring(ps[i]).decode().find('<w:pPr'):][-1800:])
 for i,p in enumerate(ps):
  t=''.join(p.xpath('.//w:t/text()',namespaces=n)).strip()
  if t.startswith('Appendix ') and i>138: print(i,t,'NEXT', ''.join(ps[i+1].xpath('.//w:t/text()',namespaces=n)))
 for i,p in enumerate(ps):
  if p.xpath('./w:pPr/w:sectPr',namespaces=n):print('SECTION AT',i)
