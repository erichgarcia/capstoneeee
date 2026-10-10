from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
p='outputs/document-fix/CapstoneCHAPTER1-5_Corrected.docx';w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
with ZipFile(p) as z:d={n:z.read(n) for n in z.namelist()}
r=E.fromstring(d['word/document.xml'])
for pnode in r.findall('.//'+w+'body/'+w+'p'):
 if pnode.find(w+'fldSimple') is None:continue
 pr=pnode.find(w+'pPr');ind=pr.find(w+'ind')
 if ind is None:ind=E.SubElement(pr,w+'ind')
 ind.set(w+'right','360')
d['word/document.xml']=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(p,'w',ZIP_DEFLATED) as z:
 for n,b in d.items():z.writestr(n,b)
