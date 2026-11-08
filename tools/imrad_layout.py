"""Journal layout matching the supplied Klarify format without copying its content."""
from html import escape
from build_project_documents import AUTHORS


def write_pdf(blocks, path, document_title):
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
        NextPageTemplate, FrameBreak, Table, TableStyle, Image, Spacer, KeepTogether)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.utils import ImageReader
    width, height, margin, gap = 612, 792, 42, 18
    usable = width - 2 * margin
    column = (usable - gap) / 2
    body = ParagraphStyle('Body', fontName='SlideSans', fontSize=10, leading=12.5,
        alignment=TA_JUSTIFY, firstLineIndent=16, spaceAfter=8)
    center = ParagraphStyle('Center', parent=body, alignment=TA_CENTER, firstLineIndent=0)
    title = ParagraphStyle('Title', parent=center, fontName='SlideSans-Bold', fontSize=12, leading=15, spaceAfter=16)
    heading = ParagraphStyle('Heading', parent=center, fontName='SlideSans-Bold', spaceBefore=12, spaceAfter=8, keepWithNext=True)
    subheading = ParagraphStyle('Subheading', parent=heading, alignment=0)
    caption = ParagraphStyle('Caption', parent=center, fontSize=8, leading=10, spaceAfter=10)
    cell = ParagraphStyle('Cell', parent=body, fontSize=7, leading=9, firstLineIndent=0, alignment=0, spaceAfter=0)
    ref = ParagraphStyle('Reference', parent=body, firstLineIndent=-12, leftIndent=12, alignment=0, fontSize=9, leading=11)
    def frame(x,y,w,h,ident): return Frame(x,y,w,h,id=ident,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    # The title/abstract span the first page; body continues below in two columns.
    first = [frame(margin,340,usable,410,'abstract'),frame(margin,margin,column,280,'left-first'),frame(margin+column+gap,margin,column,280,'right-first')]
    later = [frame(margin,margin,column,height-2*margin,'left'),frame(margin+column+gap,margin,column,height-2*margin,'right')]
    doc=BaseDocTemplate(str(path),pagesize=(width,height),title=document_title,author='; '.join(AUTHORS))
    doc.addPageTemplates([PageTemplate(id='first',frames=first),PageTemplate(id='body',frames=later)])
    story=[NextPageTemplate('body')]
    for block in blocks:
        kind=block['kind']
        if kind=='heading' and block['text']=='I. INTRODUCTION': story.append(FrameBreak())
        if kind in {'title','center','paragraph','heading','reference'}:
            style=title if kind=='title' else center if kind=='center' else ref if kind=='reference' else (heading if block['level']==1 else subheading) if kind=='heading' else body
            story.append(Paragraph(escape(block['text']),style))
        elif kind=='bullets':
            story.extend(Paragraph('• '+escape(t),body) for t in block['items'])
        elif kind=='figure':
            w,h=ImageReader(str(block['path'])).getSize(); scale=min(column/w,210/h)
            story.append(KeepTogether([Image(str(block['path']),width=w*scale,height=h*scale),Paragraph(escape(block['caption']),caption)]))
        elif kind=='table':
            rows=[block['headers']]+block['rows']
            grid=Table([[Paragraph(escape(str(v)),cell) for v in row] for row in rows],colWidths=[column/len(rows[0])]*len(rows[0]),repeatRows=1)
            grid.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,'black'),('LINEBELOW',(0,-1),(-1,-1),.4,'black'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
            story.extend([Paragraph(escape(block['caption']),caption),grid,Spacer(1,8)])
        elif kind=='code':
            for line in block['text'].splitlines(): story.append(Paragraph(escape(line),cell))
    doc.build(story)


def write_docx(blocks,path,document_title):
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.section import WD_SECTION_START
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    document=Document(); section=document.sections[0]
    section.page_width,section.page_height=Inches(8.5),Inches(11)
    section.top_margin=section.bottom_margin=section.left_margin=section.right_margin=Inches(.58)
    normal=document.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(10)
    normal.paragraph_format.line_spacing=1.15;normal.paragraph_format.space_after=Pt(8)
    normal.paragraph_format.first_line_indent=Inches(.22)
    for name in ['Title','Heading 1','Heading 2']:
        style=document.styles[name];style.font.name='Arial';style.font.size=Pt(12 if name=='Title' else 10);style.font.bold=True;style.font.color.rgb=None
    for block in blocks:
        kind=block['kind']
        if kind=='heading' and block['text']=='I. INTRODUCTION':
            sec=document.add_section(WD_SECTION_START.CONTINUOUS)
            cols=sec._sectPr.find(qn('w:cols'));cols.set(qn('w:num'),'2');cols.set(qn('w:space'),'360')
        if kind in {'paragraph','reference','title','center','heading'}:
            p=document.add_paragraph(block['text'],style='Title' if kind=='title' else f"Heading {min(block['level'],2)}" if kind=='heading' else 'Normal')
            if kind in {'title','center'} or kind=='heading' and block['level']==1:
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Inches(0)
            else: p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
        elif kind=='bullets':
            for t in block['items']: document.add_paragraph(t,style='List Bullet')
        elif kind=='figure':
            document.add_picture(str(block['path']),width=Inches(3.5));document.add_paragraph(block['caption'],style='Caption')
        elif kind=='table':
            document.add_paragraph(block['caption'],style='Caption');grid=document.add_table(rows=0,cols=len(block['headers']));grid.autofit=False
            for col in grid.columns:
                col.width=Inches(3.5/len(block['headers']))
            for row in [block['headers']]+block['rows']:
                for c,v in zip(grid.add_row().cells,row):
                    c.width=Inches(3.5/len(row));c.text=str(v)
                    for p in c.paragraphs:
                        p.paragraph_format.first_line_indent=Inches(0)
                        for r in p.runs:r.font.size=Pt(8)
        elif kind=='code':document.add_paragraph(block['text'])
    document.core_properties.author='; '.join(AUTHORS)
    document.core_properties.title=document_title
    document.save(path)
