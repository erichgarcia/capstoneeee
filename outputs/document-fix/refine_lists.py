from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';p='outputs/document-fix/CapstoneCHAPTER1-5_Formatted.docx'
with ZipFile(p) as z:d={n:z.read(n) for n in z.namelist()}
r=E.fromstring(d['word/document.xml'])
for tbl in r.iter(w+'tbl'):
 if not any('PAGEREF figure_' in (t.text or '') or 'PAGEREF table_' in (t.text or '') for t in tbl.iter(w+'instrText')):continue
 for sp in tbl.iter(w+'spacing'):sp.set(w+'line','440')
d['word/document.xml']=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(p,'w',ZIP_DEFLATED) as z:
 for n,b in d.items():z.writestr(n,b)
