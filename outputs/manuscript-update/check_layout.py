from docx import Document
from pathlib import Path
p=Path(r'C:/Users/Erich Garcia/Downloads/Capstone_Progress_Final-main (2)/outputs/manuscript-update')
d=Document(p/'source.docx')
print([(s.page_width.inches,s.page_height.inches,s.left_margin.inches,s.right_margin.inches) for s in d.sections])
for i in [517,570,571,619,629,632]:
 q=d.paragraphs[i]
 print(i,q.text,[(r.text,len(r._r.xpath('.//w:drawing'))) for r in q.runs],q.style.name)
