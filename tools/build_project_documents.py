"""Build reviewable manuscripts and defense slides from measured project results.

Optional dependencies: requirements-research.txt. Run from the repository root.
The same content blocks generate Markdown, editable Word files and PDFs.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/paper'
AUTHORS = ['Boncajes, Rhian Jared D.', 'Marcos, Maricar N.', 'Carandang, Jamie Pearl U.']
TITLE = 'CCIThink: Development and Evaluation of a Source-Grounded CCIT Chatbot with Naive Bayes FAQ Classification'


def para(text):
    return {'kind': 'paragraph', 'text': ' '.join(text.split())}


def head(text, level=1):
    return {'kind': 'heading', 'text': text, 'level': level}


def bullets(items):
    return {'kind': 'bullets', 'items': items}


def table(caption, headers, rows, widths=None):
    return {'kind': 'table', 'caption': caption, 'headers': headers, 'rows': rows, 'widths': widths}


def figure(filename, caption):
    return {'kind': 'figure', 'path': ROOT / 'research/results/figures' / filename, 'caption': caption}


def cover(subtitle):
    return [{'kind': 'title', 'text': TITLE}, {'kind': 'center', 'text': subtitle},
            *[{'kind': 'center', 'text': name} for name in AUTHORS],
            {'kind': 'center', 'text': 'CCIT, FAITH Colleges'},
            {'kind': 'center', 'text': 'Principles of Artificial Intelligence and Data Science'},
            {'kind': 'center', 'text': 'November 2026 · Draft for author review'}, {'kind': 'pagebreak'}]


def content(report):
    """Use the same measured findings for the article and five-chapter report."""
    import csv
    from build_imrad import manuscript

    article = manuscript(report)

    def section(name):
        # Copy one section, stopping at the next heading of the same level.
        result = []
        level = None
        for block in article:
            if block.get('text') == name:
                level = block['level']
                continue
            if level is not None:
                if block['kind'] == 'heading' and block['level'] <= level:
                    break
                result.append(dict(block))
        return result

    related = section('Related concepts and scope')
    intro = [head('Background of the study', 2)] + section('Background of the study')
    intro += [head('Problem statement', 2), para('Students need a way to find a supported answer in the supplied department information. The study asks which of four Naive Bayes configurations best classifies the constructed validation questions, how the selected model performs on the fixed test questions, and which limitations prevent broader claims.')]
    intro += [head('General and specific objectives', 2)] + section('Objectives')
    intro += [head('Scope and limitations', 2), related[-1], head('Significance of the project', 2), para('The project demonstrates a complete Python data-science workflow using department questions. Its value is a working, explainable prototype and a reproducible experiment. It does not establish reduced staff workload, student satisfaction, or deployment effectiveness.')]

    concepts = [head('AI and Data Science concepts', 2)] + related[:-1]
    concepts += [head('Related systems and selected algorithm', 2), table('Comparison of approaches', ['Approach', 'Role and limitation'], [
        ['Manual FAQ search', 'Readers locate an answer themselves; no trained prediction.'],
        ['Naive Bayes text classification', 'Learns word counts from labeled questions; predicts an FAQ label, not a verified fact (Scikit-learn developers, n.d.-b).'],
        ['Source-grounded chat prototype', 'CCIThink combines source checks with bounded model ranking and optional provider wording. Successful live generation has not been established.'],
    ]), head('Opportunities for improvement', 2), para('Related wording, sparse training examples, and overlapping course names make classification difficult. Independently written questions and reviewed labels are needed before claiming reliable real-student performance. This comparison explains design choices rather than inventing a comparative user study.')]

    methods = section('II. METHODOLOGY')
    methods += [head('Feature selection and Naive Bayes calculation', 2), para('Question text is converted to counts of words or adjacent word pairs. FAQ IDs, answers, authoring-language tags, and split labels are excluded from input features. The implementation uses log scores to avoid multiplying many small values.'),
        {'kind': 'code', 'text': 'score(label) = log P(label) + sum(count(word) * log P(word | label))\nP(word | label) = (training count + alpha) /\n                  (all feature counts for label + alpha * vocabulary size)'},
        para('The class prior is its training-question count divided by all training questions. Alpha adds a small smoothing count. Naive Bayes assumes conditional independence of features given the label; that assumption is imperfect for natural language (Scikit-learn developers, n.d.-b).'),
        head('System architecture and workflow', 2), bullets([
            'Offline: load CSV, validate and clean rows, describe the data, train four settings, select on validation, evaluate on test, and save the model/report/figures.',
            'Online: validate a question, detect private requests, resolve a bounded follow-up, check source scope, rank eligible FAQs, and return the source-supported response.',
            'The local classifier cannot supply missing facts. Unclear requests ask for details; unsupported questions fall back. Optional AI wording uses selected source text only.',
        ])]
    findings = section('III. RESULT')
    findings += [head('Language coverage', 2), figure('language_distribution.png', 'Figure 5. All current authoring examples are English. This chart exposes a coverage limitation, not a student-language survey.')]
    discussion = section('Meaning of the findings') + section('Limitations and recommendations')
    conclusion = section('Conclusion')
    conclusion += [head('Achievement of objectives and recommendations', 2), para('The system loads and validates data, describes patterns with five charts, implements and compares an explained classifier, evaluates fixed test questions, and demonstrates supported chat and predictions. The objective is a course prototype, not proof of unrestricted reliability.'), *section('Limitations and recommendations')]

    references = section('REFERENCES')
    references[0]['text'] = 'CCIT knowledge database. (n.d.). *database_v3.json and department-chair update* [User-supplied source collection; currency and broader usage permission unconfirmed].'
    references[1]['text'] = 'Final project: AI-powered data analysis and prediction system. (n.d.). *Final project documentation guidelines* [Course handout; original PDF retained as docs/FINAL_PROJECT.pdf].'
    references[2]['text'] = 'Scikit-learn developers. (n.d.-a). *Metrics and scoring: Quantifying the quality of predictions*. https://scikit-learn.org/stable/modules/model_evaluation.html'
    references[3]['text'] = 'Scikit-learn developers. (n.d.-b). *Naive Bayes*. https://scikit-learn.org/stable/modules/naive_bayes.html'
    citations = {'[1]': '(CCIT knowledge database, n.d.)', '[2]': '(Final project: AI-powered data analysis and prediction system, n.d.)', '[3]': '(Scikit-learn developers, n.d.-a)', '[4]': '(Scikit-learn developers, n.d.-b)'}
    for blocks in [intro, concepts, methods, findings, discussion, conclusion]:
        for block in blocks:
            if 'text' in block:
                for number, author_date in citations.items():
                    block['text'] = block['text'].replace(number, author_date)

    with (ROOT / 'data/questions.csv').open(newline='', encoding='utf-8') as stream:
        samples = list(csv.DictReader(stream))[:3]
    appendices = [head('Appendices'), head('A. Source code, dataset, and usage', 2),
        para('Repository: https://github.com/jared-boncajes/CCIT_Chatbot. The data dictionary is data/README.md. data/knowledge.json contains the supported source answers; data/questions.csv contains labeled classification questions. Institutional currency and wider redistribution permissions remain unconfirmed.'),
        table('Permitted project sample: constructed questions, not student transcripts', ['Sample', 'Question', 'Target'], [[row['sample_id'], row['question'], row['faq_id']] for row in samples]),
        head('B. Demonstration screenshots', 2),
        {'kind': 'figure', 'path': ROOT / 'docs/screenshots/chat.png', 'caption': 'Chat demonstration: a shorthand department-chair question uses the supplied source.'},
        {'kind': 'figure', 'path': ROOT / 'docs/screenshots/analysis.png', 'caption': 'Analysis demonstration: current corpus, cleaning summary, charts, and prediction form.'},
        head('C. Test cases and additional results', 2), para('The tests directory includes canonical/alternative question checks, shorthand, unclear scope, source support, privacy, provider failures, CSV validation, model arithmetic, leakage checks, and repeatable training. docs/testing.md records the latest executed validation. research/results/test_predictions.csv retains every classifier test prediction; report.json contains per-class scores and errors.'),
        head('D. User guide and responsible AI disclosure', 2), para('See README.md for installation and docs/beginner-guide.md for the code-reading guide and worked Bayes example. AI assistance was used for implementation, constructed questions, debugging, and drafting. Named authors must review the work and be able to explain the code. No interviews, survey results, or real-user outcomes are claimed.'),
        {'kind': 'code', 'text': 'python -m pip install -r requirements-research.txt\npython tools/build_dataset.py\npython analyze.py\npython -m pytest -q\n# Start a separate terminal with CHAT_MODE=faq, then: python app.py\npython tools/build_project_documents.py'}]
    return {'abstract': [head('Abstract')] + section('ABSTRACT'), 'intro': intro,
            'related': concepts, 'methods': methods, 'results': findings,
            'discussion': discussion, 'conclusion': conclusion,
            'references': [head('References')] + references, 'appendices': appendices}


def inline_runs(text):
    # Manuscript formatting only; input is project-authored content, not chat HTML.
    parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', str(text))
    return [(part[2:-2], 'bold') if part.startswith('**') and part.endswith('**')
            else (part[1:-1], 'italic') if part.startswith('*') and part.endswith('*') else (part, '') for part in parts]


def register_pdf_fonts():
    """Embed fonts so PDF viewers never substitute incompatible glyph metrics."""
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    bundled = Path(reportlab.__file__).parent / 'fonts'
    fallback = [bundled / name for name in ['Vera.ttf', 'VeraBd.ttf', 'VeraIt.ttf', 'VeraBI.ttf']]
    for family, windows, linux in [('PaperSerif', ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf'], 'LiberationSerif'),
                                    ('SlideSans', ['arial.ttf', 'arialbd.ttf', 'ariali.ttf', 'arialbi.ttf'], 'LiberationSans'),
                                    ('CodeMono', ['cour.ttf', 'courbd.ttf', 'couri.ttf', 'courbi.ttf'], 'LiberationMono')]:
        candidates = [[Path('C:/Windows/Fonts') / name for name in windows]]
        candidates += [[Path('/usr/share/fonts/truetype') / folder / (linux + '-' + suffix + '.ttf')
                        for suffix in ['Regular', 'Bold', 'Italic', 'BoldItalic']] for folder in ['liberation', 'liberation2']]
        paths = next((paths for paths in candidates if all(path.exists() for path in paths)), fallback)
        names = [family, family + '-Bold', family + '-Italic', family + '-BoldItalic']
        for name, path in zip(names, paths):
            pdfmetrics.registerFont(TTFont(name, str(path)))
        pdfmetrics.registerFontFamily(family, normal=names[0], bold=names[1], italic=names[2], boldItalic=names[3])


def write_markdown(blocks, path):
    lines = []
    for block in blocks:
        kind = block['kind']
        if kind in {'title', 'heading'}:
            lines.append('#' * (1 if kind == 'title' else block['level'] + 1) + ' ' + block['text'])
        elif kind in {'paragraph', 'center', 'reference'}:
            lines.append(block['text'])
        elif kind == 'pagebreak':
            lines.append('<!-- page break -->')
        elif kind == 'code':
            lines.append('```' + block.get('language', 'python') + '\n' + block['text'] + '\n```')
        elif kind == 'bullets':
            lines.append('\n'.join('- ' + item for item in block['items']))
        elif kind == 'table':
            lines.append(block['caption'])
            lines.append('| ' + ' | '.join(block['headers']) + ' |\n| ' + ' | '.join('---' for _ in block['headers']) + ' |')
            lines.extend('| ' + ' | '.join(map(str, row)) + ' |' for row in block['rows'])
        elif kind == 'figure':
            relative = Path('../..') / block['path'].relative_to(ROOT)
            lines.append(f"![{block['caption']}]({relative.as_posix()})")
        lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def write_docx(blocks, path, document_title=TITLE, compact=False):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt
    from reportlab.lib.utils import ImageReader
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(1)
    normal = document.styles['Normal']
    normal.font.name, normal.font.size = 'Times New Roman', Pt(11 if compact else 12)
    normal.paragraph_format.line_spacing = 1.15 if compact else 2
    normal.paragraph_format.space_after = Pt(0)
    for name in ['Title', 'Heading 1', 'Heading 2', 'Heading 3']:
        document.styles[name].font.name = 'Times New Roman'
        document.styles[name].font.color.rgb = None
        document.styles[name].font.size = Pt(16 if name == 'Title' else 12)
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    header._p.append(field)
    for block in blocks:
        kind = block['kind']
        if kind == 'pagebreak':
            document.add_page_break()
        elif kind in {'title', 'heading'}:
            paragraph = document.add_paragraph(style='Title' if kind == 'title' else f"Heading {min(block['level'], 3)}")
            paragraph.add_run(block['text'])
            if kind == 'title' or block['level'] == 1:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.keep_with_next = True
        elif kind in {'paragraph', 'center', 'reference'}:
            paragraph = document.add_paragraph()
            if kind == 'center':
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if kind == 'reference':
                paragraph.paragraph_format.left_indent = Inches(.5)
                paragraph.paragraph_format.first_line_indent = Inches(-.5)
            for text, emphasis in inline_runs(block['text']):
                run = paragraph.add_run(text)
                run.bold, run.italic = emphasis == 'bold', emphasis == 'italic'
        elif kind == 'bullets':
            for item in block['items']:
                document.add_paragraph(item, style='List Bullet')
        elif kind == 'code':
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.line_spacing = 1
            paragraph.paragraph_format.keep_together = True
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(10)
            run = paragraph.add_run(block['text'])
            run.font.name, run.font.size = 'Consolas', Pt(9)
        elif kind == 'table':
            document.add_paragraph(block['caption'], style='Caption')
            grid = document.add_table(rows=1, cols=len(block['headers']))
            grid.style = 'Light Shading Accent 1'
            for cell, text in zip(grid.rows[0].cells, block['headers']):
                cell.text = text
            for row in block['rows']:
                for cell, text in zip(grid.add_row().cells, row):
                    cell.text = str(text)
            for row in grid.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.line_spacing = 1
                        for run in paragraph.runs:
                            run.font.size = Pt(10)
        elif kind == 'figure':
            width, height = ImageReader(str(block['path'])).getSize()
            document.add_picture(str(block['path']), width=Inches(min(6.3, 7 * width / height)))
            image_paragraph = document.paragraphs[-1]
            image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            image_paragraph.paragraph_format.line_spacing = 1
            image_paragraph.paragraph_format.keep_with_next = True
            caption = document.add_paragraph(block['caption'], style='Caption')
            caption.paragraph_format.line_spacing = 1
    document.core_properties.title = document_title
    document.core_properties.author = '; '.join(AUTHORS)
    document.core_properties.subject = 'AI-assisted research draft; measured offline evaluation'
    document.save(path)


def write_pdf(blocks, path, document_title=TITLE, compact=False):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib.utils import ImageReader
    styles = getSampleStyleSheet()
    body = ParagraphStyle('ManuscriptBody', fontName='PaperSerif', fontSize=11 if compact else 12, leading=16 if compact else 22,
                          spaceAfter=8, alignment=TA_JUSTIFY, splitLongWords=True)
    center = ParagraphStyle('ManuscriptCenter', parent=body, alignment=TA_CENTER, spaceAfter=12)
    title = ParagraphStyle('ManuscriptTitle', parent=center, fontName='PaperSerif-Bold', fontSize=17, leading=23, spaceBefore=78, spaceAfter=34)
    h1 = ParagraphStyle('ManuscriptH1', parent=body, fontName='PaperSerif-Bold', fontSize=14, leading=19,
                        alignment=TA_CENTER, spaceBefore=18, spaceAfter=12, keepWithNext=True)
    h2 = ParagraphStyle('ManuscriptH2', parent=h1, fontSize=12, leading=17, alignment=0, spaceBefore=12, spaceAfter=6)
    caption = ParagraphStyle('ManuscriptCaption', parent=body, fontName='PaperSerif-Italic', fontSize=10, leading=14, spaceAfter=10)
    cell_style = ParagraphStyle('ManuscriptCell', parent=body, fontSize=9.5, leading=12, spaceAfter=0, alignment=0)
    reference_style = ParagraphStyle('ManuscriptReference', parent=body, leftIndent=36, firstLineIndent=-36, alignment=0)
    code_style = ParagraphStyle('CodeBlock', fontName='CodeMono', fontSize=9, leading=12,
                               leftIndent=8, spaceBefore=6, spaceAfter=10)

    def markup(text):
        return ''.join(('<b>' + html.escape(part) + '</b>') if emphasis == 'bold' else
                       ('<i>' + html.escape(part) + '</i>') if emphasis == 'italic' else html.escape(part)
                       for part, emphasis in inline_runs(text))

    story = []
    for block in blocks:
        kind = block['kind']
        if kind in {'paragraph', 'center', 'title', 'heading', 'reference'}:
            style = title if kind == 'title' else center if kind == 'center' else reference_style if kind == 'reference' else (h1 if block['level'] == 1 else h2) if kind == 'heading' else body
            story.append(Paragraph(markup(block['text']), style))
        elif kind == 'pagebreak':
            story.append(PageBreak())
        elif kind == 'code':
            story.append(KeepTogether([Preformatted(block['text'], code_style, maxLineLength=83)]))
        elif kind == 'bullets':
            for item in block['items']:
                story.append(Paragraph('• ' + markup(item), body))
        elif kind == 'table':
            story.append(Paragraph(markup(block['caption']), caption))
            data = [[Paragraph('<b>' + markup(value) + '</b>', cell_style) for value in block['headers']]]
            data += [[Paragraph(markup(value), cell_style) for value in row] for row in block['rows']]
            count = len(block['headers'])
            weights = block['widths'] or ([.34, .66] if count == 2 else [1 / count] * count)
            grid = Table(data, colWidths=[468 * value for value in weights], repeatRows=1, hAlign='LEFT')
            grid.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4eeee')),
                ('LINEBELOW', (0, 0), (-1, 0), .8, colors.HexColor('#84201c')),
                ('LINEBELOW', (0, 1), (-1, -1), .3, colors.HexColor('#dddddd')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7), ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))
            story.extend([grid, Spacer(1, 12)])
        elif kind == 'figure':
            width, height = ImageReader(str(block['path'])).getSize()
            scale = min(468 / width, 430 / height)
            story.append(KeepTogether([Image(str(block['path']), width=width * scale, height=height * scale),
                                      Paragraph(markup(block['caption']), caption)]))

    def page(canvas, document):
        canvas.setTitle(document_title)
        canvas.setAuthor('; '.join(AUTHORS))
        canvas.setFont('PaperSerif', 12)
        canvas.drawRightString(540, 756, str(document.page))
    SimpleDocTemplate(str(path), pagesize=letter, leftMargin=72, rightMargin=72,
                      topMargin=72, bottomMargin=65).build(story, onFirstPage=page, onLaterPages=page)


def slides(report):
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit
    test = report['test']
    data = report['dataset']
    selected = report['selected']
    splits = data['split_counts']
    classes = len(report['labels'])
    entries = [
        ('CCIThink', ['CCIT information chatbot and explainable FAQ classifier', *AUTHORS, 'Principles of Artificial Intelligence and Data Science'], None,
         'Introduce the team and approved department-information topic. This is a class prototype, not a student-record system. About 45 seconds.'),
        ('Problem and objectives', [f'Find supported answers within {classes} active department FAQs.', 'Prepare data, describe patterns, train a classifier, and evaluate results.', 'Keep unclear and unsupported questions separate from supported answers.'], None,
         'Explain the information-search problem without claiming measured waiting times or staff workload savings. About 1 minute.'),
        ('Dataset and source', [f"{data['quality']['retained_rows']:,} labeled English questions; {classes} FAQ labels.", f"{splits['train']} train / {splits['validation']} validation / {splits['test']} test.", 'Training titles and variants were supplied with the knowledge.', 'Holdouts are AI-authored constructed examples, not student transcripts.'], 'class_distribution.png',
         'Show data/questions.csv and data/README.md. Explain why a small constructed corpus demonstrates the workflow but cannot establish population accuracy. About 1 minute.'),
        ('Cleaning and exploration', ['Check missing fields, duplicates, labels, and formats.', 'Reject label conflicts and cross-split duplicates.', f"{data['quality']['missing_rows_removed']} missing, {data['quality']['duplicate_rows_removed']} duplicate, {data['quality']['invalid_rows_removed']} invalid rows removed.", f"Mean {data['token_lengths']['mean']:.2f} tokens; {data['quality']['token_length_outliers']} long valid questions retained."], 'question_lengths.png',
         'Explain that valid long questions remain. Only question text becomes input features. The reported cleaning counts are measured, not fabricated dirty data. About 1 minute.'),
        ('Coverage and bias', ['All current dataset examples are English.', 'The model test does not establish Filipino or Taglish accuracy.', 'Topic counts are designed examples, not measured student demand.'], 'language_distribution.png',
         'This is the third EDA visualization. Explain language coverage and the difference between dataset composition and real student behavior. About 45 seconds.'),
        ('How Naive Bayes works', ['Count words in training questions for each FAQ label.', 'Estimate a label prior and smoothed word likelihoods.', 'Add log likelihoods to rank possible labels.', 'Independence is an approximation; scores are uncalibrated.'], None,
         'Open chatbot/intent_model.py and explain the worked example in docs/beginner-guide.md. The implementation uses ordinary Python, counters, loops, and math. About 90 seconds.'),
        ('Parameter experiment', ['Compare four fixed unigram/bigram and alpha settings.', 'Select with validation macro F1; keep test questions separate.', f"Selected: {selected['name']}.", f"Validation: {selected['correct']}/{selected['samples']} correct; macro F1 {selected['macro_f1']:.3f}."], 'validation_experiment.png',
         'Explain the validation comparison and tie-breaking rule. No test-based parameter tuning or retraining on held-out questions. About 1 minute.'),
        ('Test results', [f"{test['correct']}/{test['samples']} correct ({test['accuracy']:.1%}).", f"Macro F1 {test['macro_f1']:.3f}.", f"Majority baseline: {report['baseline']['accuracy']:.1%} accuracy.", f"{len(report['errors'])} errors; two test questions per label."], 'test_confusion.png',
         'Interpret actual and predicted labels. These are constructed-question classifier results, not chat-user satisfaction or independent real-world accuracy. About 1 minute.'),
        ('Errors and limitations', ['Similar course and curriculum wording can confuse labels.', 'AI-authored questions may share templates.', 'FAQ-020 was retired by user request; other IDs remain stable.', 'Recomputed results do not constitute a new independent study.'], None,
         'Show an actual error in research/results/test_predictions.csv. Explain that changing the corpus changes the scores and does not itself prove better generalization. About 1 minute.'),
        ('Working demonstration', ['Run python analyze.py, then start python app.py in FAQ mode.', 'Use /analysis for five charts, metrics, and a local prediction.', 'Use chat for source-supported answers and short forms.', 'Try an ambiguous question and an unsupported detail.'], None,
         'Demonstrate Who teaches BSCS?, it dept chair, and a missing contact detail. Distinguish application regressions from classifier test accuracy. About 90 seconds.'),
        ('Ethics and responsible AI', ['No private student records are required.', 'Source currency and permissions still need review.', 'AI assistance is disclosed; authors must explain their work.', 'Optional provider wording is not a verified live-generation result.'], None,
         'Discuss privacy, source currency, language bias, and required AI disclosure. Optional AI mode sends selected context to a provider; FAQ mode does not. About 1 minute.'),
        ('Conclusion and next steps', ['A complete data-science workflow supports the chatbot.', 'The classifier remains limited to a constructed, closed-set task.', 'Next: confirmed sources, permissioned student questions, independent labels.', 'Questions and defense discussion'], None,
         'Summarize the objectives and limitations. Prepare each team member to explain their contribution and the algorithm. Reserve 5 minutes for questions after the 10–15-minute presentation.'),
    ]
    presentation = Presentation()
    presentation.slide_width, presentation.slide_height = Inches(13.333), Inches(7.5)
    pdf = canvas.Canvas(str(OUT / 'CCIThink_Defense.pdf'), pagesize=(960, 540))
    pdf.setTitle('CCIThink: Defense Presentation')
    pdf.setAuthor('; '.join(AUTHORS))
    presentation.core_properties.title = 'CCIThink: Defense Presentation'
    presentation.core_properties.author = '; '.join(AUTHORS)
    outline = []
    for index, (title, points, image, notes) in enumerate(entries, 1):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        shape = slide.shapes.add_shape(1, 0, 0, presentation.slide_width, Inches(.16))
        shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string('A71917'); shape.line.fill.background()
        box = slide.shapes.add_textbox(Inches(.55), Inches(.45), Inches(12.2), Inches(.8))
        box.text_frame.text = title
        box.text_frame.paragraphs[0].font.size = Pt(30)
        box.text_frame.paragraphs[0].font.bold = True
        width = 6.1 if image else 12.1
        body = slide.shapes.add_textbox(Inches(.6), Inches(1.55), Inches(width), Inches(5.25))
        body.text_frame.word_wrap = True
        for item_index, point in enumerate(points):
            paragraph = body.text_frame.paragraphs[0] if item_index == 0 else body.text_frame.add_paragraph()
            paragraph.text = '• ' + point
            paragraph.font.size = Pt(22 if len(points) < 5 else 20)
            paragraph.space_after = Pt(22)
        if image:
            slide.shapes.add_picture(str(ROOT / 'research/results/figures' / image), Inches(6.95), Inches(1.65), width=Inches(5.8))
        slide.notes_slide.notes_text_frame.text = notes
        pdf.setFillColor(colors.HexColor('#a71917')); pdf.rect(0, 528, 960, 12, fill=1, stroke=0)
        pdf.setFillColor(colors.black); pdf.setFont('SlideSans-Bold', 30); pdf.drawString(40, 477, title)
        y = 410
        for point in points:
            for line in simpleSplit('• ' + point, 'SlideSans', 20, 430 if image else 870):
                pdf.setFont('SlideSans', 20); pdf.drawString(43, y, line); y -= 27
            y -= 17
        if image:
            pdf.drawImage(str(ROOT / 'research/results/figures' / image), 505, 120, width=420, height=300, preserveAspectRatio=True, anchor='c')
        pdf.setFont('SlideSans', 10); pdf.drawRightString(920, 23, f'CCIThink · {index}/12')
        pdf.showPage()
        outline.extend([f'## Slide {index}: {title}', '', *['- ' + point for point in points], '', '**Speaker notes:** ' + notes, ''])
    presentation.save(OUT / 'CCIThink_Defense.pptx')
    pdf.save()
    (OUT / 'defense-slides.md').write_text('\n'.join(outline), encoding='utf-8')


def main():
    # All submission documents use this one current result file.
    report = json.loads((ROOT / 'research/results/report.json').read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    register_pdf_fonts()
    parts = content(report)
    technical = cover('Five-chapter technical documentation · Draft for author review') + parts['abstract']
    chapters = [('Chapter 1: Introduction', parts['intro']),
                ('Chapter 2: Review of Related Systems and Concepts', parts['related']),
                ('Chapter 3: Methodology', parts['methods']),
                ('Chapter 4: Results and Discussion', parts['results'] + parts['discussion']),
                ('Chapter 5: Conclusion and Recommendations', parts['conclusion'])]
    for name, blocks in chapters:
        technical += [{'kind': 'pagebreak'}, head(name)] + blocks
    technical += [{'kind': 'pagebreak'}] + parts['references'] + parts['appendices']
    write_markdown(technical, OUT / 'technical-report.md')
    write_docx(technical, OUT / 'CCIThink_Technical_Report_Draft.docx')
    write_pdf(technical, OUT / 'CCIThink_Technical_Report_Draft.pdf')
    from build_imrad import main as build_article
    build_article()
    slides(report)
    print('Built current five-chapter report, IMRaD, and 12-slide defense.')


if __name__ == '__main__':
    main()
