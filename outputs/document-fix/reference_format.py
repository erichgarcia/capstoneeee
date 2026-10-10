from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
from copy import deepcopy
import re
w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';p='outputs/document-fix/CapstoneCHAPTER1-5_Corrected.docx'
with ZipFile(p) as z:d={n:z.read(n) for n in z.namelist()}
r=E.fromstring(d['word/document.xml']);body=r.find(w+'body')
def vis(e):return ''.join(t.text or '' for t in e.iter(w+'t'))
def prop(e,name,attrs):
 x=e.find(w+name)
 if x is None:x=E.SubElement(e,w+name)
 for k,v in attrs.items():x.set(w+k,str(v))
 return x
def fmt(p,align='left',bold=False):
 pr=prop(p,'pPr',{})
 for name in ['tabs','ind','spacing','jc','pageBreakBefore']:
  e=pr.find(w+name)
  if e is not None:pr.remove(e)
 prop(pr,'spacing',{'before':0,'after':0,'line':480,'lineRule':'auto'});prop(pr,'jc',{'val':align})
 for rr in p.iter(w+'r'):
  rp=prop(rr,'rPr',{});prop(rp,'rFonts',{'ascii':'Arial','hAnsi':'Arial'});prop(rp,'sz',{'val':24});prop(rp,'b',{'val':1 if bold else 0})
for pp in list(body):
 codes=''.join(t.text or '' for t in pp.iter(w+'instrText'))
 if 'PAGEREF' not in codes:continue
 if re.search(r'PAGEREF (figure|table)_',codes):continue
 label=vis(pp);bold=label.startswith('Chapter ') or label.startswith('REFERENCES') or label.startswith('APPENDICES')
 fmt(pp,bold=bold);pr=pp.find(w+'pPr');prop(pr,'ind',{'left':0 if bold else 720})
 tabs=prop(pr,'tabs',{});prop(tabs,'tab',{'val':'right','pos':8640,'leader':'none'})
 if label.startswith('Chapter '):prop(pr,'spacing',{'before':240})
 if 'PAGEREF nav_58 ' in codes:prop(pr,'pageBreakBefore',{})
for kind in ['figure','table']:
 entries=[pp for pp in body if re.search(rf'PAGEREF {kind}_\d+', ''.join(t.text or '' for t in pp.iter(w+'instrText')))]
 at=body.index(entries[0]);header=body[at-1]
 if vis(header).replace(' ','')=='NoTitlePage':body.remove(header);at-=1
 tbl=E.Element(w+'tbl');pr=E.SubElement(tbl,w+'tblPr');prop(pr,'tblW',{'w':8640,'type':'dxa'});prop(pr,'tblLayout',{'type':'fixed'})
 borders=prop(pr,'tblBorders',{})
 for side in ['top','left','bottom','right','insideH','insideV']:prop(borders,side,{'val':'nil'})
 mar=prop(pr,'tblCellMar',{})
 for side in ['top','bottom','left','right']:prop(mar,side,{'w':0,'type':'dxa'})
 grid=E.SubElement(tbl,w+'tblGrid')
 for width in [600,7440,600]:E.SubElement(grid,w+'gridCol').set(w+'w',str(width))
 def row(cells):
  tr=E.SubElement(tbl,w+'tr');trpr=E.SubElement(tr,w+'trPr');E.SubElement(trpr,w+'cantSplit')
  for j,(width,pp) in enumerate(zip([600,7440,600],cells)):
   tc=E.SubElement(tr,w+'tc');tcpr=E.SubElement(tc,w+'tcPr');prop(tcpr,'tcW',{'w':width,'type':'dxa'});prop(tcpr,'vAlign',{'val':'center'});fmt(pp,['left','center','right'][j]);tc.append(pp)
 def plain(s):
  pp=E.Element(w+'p');rr=E.SubElement(pp,w+'r');E.SubElement(rr,w+'t').text=s;return pp
 row([plain('No'),plain('Title'),plain('Page')])
 for old in entries:
  texts=list(old.iter(w+'t'));label=''.join(t.text or '' for t in texts[:-1]);m=re.match(r'(?:Figure|Table) (\d+)\.\s*(.*)',label)
  number=m.group(1);title=m.group(2)
  # Preserve title spacing when the prior list had a manual line break.
  if kind=='figure' and number=='9':title='Intelligent Queue Management System Interfaces and Physical Setup'
  pp=plain('');
  # Copy only page-reference field runs from the original paragraph.
  infield=False
  for rr in old:
   if rr.tag!=w+'r':continue
   if any(x.get(w+'fldCharType')=='begin' for x in rr.iter(w+'fldChar')):infield=True
   if infield:pp.append(deepcopy(rr))
   if any(x.get(w+'fldCharType')=='end' for x in rr.iter(w+'fldChar')):infield=False
  row([plain(number),plain(title.strip()),pp]);body.remove(old)
 body.insert(at,tbl)
d['word/document.xml']=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile('outputs/document-fix/CapstoneCHAPTER1-5_Formatted.docx','w',ZIP_DEFLATED) as z:
 for n,b in d.items():z.writestr(n,b)
print('Applied screenshot format to contents and three-column lists.')

