from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
p='outputs/document-fix/CapstoneCHAPTER1-5_Corrected.docx';w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
with ZipFile(p) as z:d={n:z.read(n) for n in z.namelist()}
r=E.fromstring(d['word/document.xml'])
for pnode in r.findall('.//'+w+'body/'+w+'p'):
 if not any('PAGEREF' in (x.text or '') for x in pnode.iter(w+'instrText')):continue
 for t in pnode.iter(w+'t'):
  if (t.text or '').startswith('Figure 9.'):
   t.text=t.text.replace('Physical Setup','').rstrip();rr=t.getparent();at=rr.index(t)+1;rr.insert(at,E.Element(w+'br'));tt=E.Element(w+'t');tt.text='Physical Setup';rr.insert(at+1,tt)
d['word/document.xml']=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(p,'w',ZIP_DEFLATED) as z:
 for n,b in d.items():z.writestr(n,b)

