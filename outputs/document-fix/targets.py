from zipfile import ZipFile
from lxml import etree
n={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile('outputs/document-fix/source.docx') as z:
 r=etree.fromstring(z.read('word/document.xml')); ps=r.xpath('//w:body/w:p | //w:body/w:tbl',namespaces=n)
 for i,p in enumerate(ps):
  t=''.join(p.xpath('.//w:t/text()',namespaces=n)).strip()
  if i>137 and len(t)<100 and t: print(i,repr(t))
 for i in [37,43,84,134,138]:print(i,etree.tostring(ps[i],pretty_print=True).decode()[:2500])
 for s in r.xpath('//w:sectPr',namespaces=n):print(etree.tostring(s).decode()[-1800:])
