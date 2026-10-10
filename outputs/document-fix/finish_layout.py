from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
p='outputs/document-fix/CapstoneCHAPTER1-5_Corrected.docx';w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
with ZipFile(p) as z:d={n:z.read(n) for n in z.namelist()}
r=E.fromstring(d['word/document.xml'])
for e in r.findall('.//'+w+'body/'+w+'p'):
 t=''.join(e.itertext())
 visible=''.join(x.text or '' for x in e.iter(w+'t'))
 if visible=='LIST OF TABLES':
  pr=e.find(w+'pPr')
  if pr is None:pr=E.SubElement(e,w+'pPr')
  if pr.find(w+'pageBreakBefore') is None:E.SubElement(pr,w+'pageBreakBefore')
d['word/document.xml']=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(p,'w',ZIP_DEFLATED) as z:
 for n,b in d.items():z.writestr(n,b)
