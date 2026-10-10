from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
from copy import deepcopy
from pathlib import Path
import re,json
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'; ns={'w':W}
def q(s):return '{'+W+'}'+s
def text(p):return ''.join(p.xpath('.//w:t/text()',namespaces=ns))
with ZipFile('outputs/document-fix/source.docx') as z:data={n:z.read(n) for n in z.namelist()}
r=E.fromstring(data['word/document.xml']); body=r.find(q('body')); ps=body.xpath('./w:p | ./w:tbl',namespaces=ns)
nextid=10000; audit=[]
def bookmark(p,name):
 global nextid
 b=E.Element(q('bookmarkStart')); b.set(q('id'),str(nextid));b.set(q('name'),name)
 e=E.Element(q('bookmarkEnd'));e.set(q('id'),str(nextid));nextid+=1
 p.insert(1 if p.find(q('pPr')) is not None else 0,b);p.append(e)
def run(p,s):
 rr=E.SubElement(p,q('r'));pr=E.SubElement(rr,q('rPr'));E.SubElement(pr,q('sz')).set(q('val'),'24');
 for j,part in enumerate(s.split('\t')):
  if j:E.SubElement(rr,q('tab'))
  t=E.SubElement(rr,q('t'));t.text=part;t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
def entry(template,label,target,name):
 p=E.Element(q('p'));pr=template.find(q('pPr'))
 if pr is not None:p.append(deepcopy(pr))
 pp=p.find(q('pPr'))
 if pp is None:pp=E.SubElement(p,q('pPr'))
 for e in list(pp):
  if e.tag in [q('tabs'),q('ind'),q('jc')]:pp.remove(e)
 tabs=E.SubElement(pp,q('tabs'));tb=E.SubElement(tabs,q('tab'));tb.set(q('val'),'right');tb.set(q('pos'),'8640');tb.set(q('leader'),'dot')
 sp=pp.find(q('spacing'))
 if sp is not None:sp.set(q('line'),'360')
 run(p,label+'\t')
 f=E.SubElement(p,q('fldSimple'));f.set(q('instr'),f' PAGEREF {name} \\h ');run(f,'1')
 bookmark(target,name);audit.append({'bookmark':name,'label':label,'target':text(target)})
 return p
# Consecutive caption numbers in actual document order, preserving formatting.
figs=[];tbls=[]
for i,p in enumerate(ps):
 if i<138 or p.tag!=q('p'):continue
 t=text(p).strip();m=re.match(r'^(Figure|Table)\s+(\d+)\.',t)
 if not m:continue
 group=figs if m[1]=='Figure' else tbls;num=len(group)+1
 # Replace just the existing number across text runs.
 old=m.group(2);offset=t.find(old);allnodes=p.xpath('.//w:t',namespaces=ns);pos=0
 full=text(p);start=full.index(m.group(1))+len(m.group(1))+1; match=re.search(r'\d+',full[start:]);start+=match.start();end=start+len(old)
 for node in allnodes:
  s=node.text or '';lo=max(start,pos);hi=min(end,pos+len(s))
  if lo<hi:node.text=s[:lo-pos]+(str(num) if lo==start else '')+s[hi-pos:]
  pos+=len(s)
 group.append((p,re.sub(r'^(Figure|Table)\s+\d+\.\s*','',text(p).strip())))
# Existing TOC entries get reliable bookmark page fields.
mapping={37:1,38:27,39:35,40:79,41:131,43:138,44:140,45:147,46:154,47:174,48:185,50:202,51:209,52:223,53:238,54:329,55:346,56:354,58:403,59:434,60:492,61:513,62:644,63:658,64:700,65:702,66:709,67:719,68:734,69:754,70:756,71:766,72:775,73:804,74:843}
labels={48:'Scope and Limitation',61:'Design of Software, Systems, Product and/or Process',67:'Capabilities and Limitations',68:'Evaluation Result',73:'REFERENCES'}
for idx,target in mapping.items():
 t=text(ps[idx]);label=labels.get(idx,re.sub(r'(?:\d+|[ivxlcdm]+)$','',t).strip())
 new=entry(ps[idx],label,ps[target],f'nav_{idx}');body.replace(ps[idx],new)
# Expand appendices A-L and fix the Photo Ops / Curriculum Vitae distinction.
for idx in [75,76,77]:body.remove(ps[idx])
# The paragraph 78 ends the TOC section; insert all appendix entries before it.
body.remove(ps[78]) if False else None
for k,(idx) in enumerate([844,857,881,887,984,1011,1034,1045,1051,1240,1245,1275]):
 label=text(ps[idx]).strip()+' - '+text(ps[idx+1]).strip()
 new=entry(ps[75],label,ps[idx],f'appendix_{k}');body.insert(body.index(ps[78]),new)
body.remove(ps[78-1]) if False else None
# Original Appendix L entry is superseded by all actual appendices.
body.remove(ps[78]) if False else None
# index 78 is section paragraph; original appendix entries are 75-78? 78 was Appendix L plus section.
for child in list(ps[78]):
 if child.tag!=q('pPr'):ps[78].remove(child)
# Replace full lists and remove old excess empty paragraphs.
for start,end,items,prefix in [(84,130,figs,'Figure'),(134,136,tbls,'Table')]:
 anchor=ps[start];at=body.index(anchor);template=deepcopy(anchor)
 for i in range(start,end+1):
  if ps[i].getparent() is body:body.remove(ps[i])
 for k,(target,title) in enumerate(items,1):
  new=entry(template,f'{prefix} {k}. {title}',target,f'{prefix.lower()}_{k}');body.insert(at,new);at+=1
# Remove generated citation tokens already visible in source references.
for t in r.xpath('//w:t',namespaces=ns):
 if t.text:t.text=re.sub(r'\s*:contentReference\[oaicite:\d+\]\{index=\d+\}','',t.text)
data['word/document.xml']=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
settings=E.fromstring(data['word/settings.xml']);u=settings.find(q('updateFields'))
if u is None:u=E.SubElement(settings,q('updateFields'))
u.set(q('val'),'true');data['word/settings.xml']=E.tostring(settings,xml_declaration=True,encoding='UTF-8',standalone=True)
out=Path('outputs/document-fix/CapstoneCHAPTER1-5_Corrected.docx')
with ZipFile(out,'w',ZIP_DEFLATED) as z:
 for n,b in data.items():z.writestr(n,b)
Path('outputs/document-fix/navigation_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('Figures:',len(figs),'Tables:',len(tbls),'Navigation entries:',len(audit))
