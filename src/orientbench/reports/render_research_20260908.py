"""Render the dated research decision memo; no experiment or model operations."""
from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'doc/report-source.md'
OUTPUT = ROOT / 'doc/ORIENTBENCH_RESEARCH_PLAN_20260908.pdf'


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  r'<link href="\2" color="#146C94"><u>\1</u></link>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    return text.replace('`', '')


def render() -> None:
    font_dir = Path('C:/Windows/Fonts')
    pdfmetrics.registerFont(TTFont('YaHei', str(font_dir / 'msyh.ttc')))
    pdfmetrics.registerFont(TTFont('YaHeiBold', str(font_dir / 'msyhbd.ttc')))
    pdfmetrics.registerFontFamily('YaHei', normal='YaHei', bold='YaHeiBold')
    base = ParagraphStyle('base', fontName='YaHei', fontSize=10.2, leading=17.2,
                          textColor=colors.HexColor('#243647'), wordWrap='CJK',
                          spaceAfter=8, alignment=TA_LEFT)
    styles = {
        'p': base,
        'h1': ParagraphStyle('h1', parent=base, fontName='YaHeiBold', fontSize=23,
                             leading=32, spaceAfter=17, textColor=colors.HexColor('#12334A')),
        'h2': ParagraphStyle('h2', parent=base, fontName='YaHeiBold', fontSize=16,
                             leading=23, spaceBefore=4, spaceAfter=12, keepWithNext=True),
        'h3': ParagraphStyle('h3', parent=base, fontName='YaHeiBold', fontSize=11.2,
                             leading=18, spaceBefore=7, spaceAfter=5, keepWithNext=True),
        'cell': ParagraphStyle('cell', parent=base, fontSize=8.8, leading=14.4, spaceAfter=0),
        'head': ParagraphStyle('head', parent=base, fontName='YaHeiBold', fontSize=9,
                               leading=14.5, textColor=colors.white, spaceAfter=0),
    }
    story = []
    lines = SOURCE.read_text(encoding='utf-8').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == '---':
            story.append(PageBreak())
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', c) for c in cells):
                    rows.append(cells)
                i += 1
            cols = len(rows[0])
            widths = ([37*mm, 133*mm] if cols == 2 else
                      [35*mm, 66*mm, 69*mm] if cols == 3 else [170*mm/cols]*cols)
            data = [[Paragraph(inline(c), styles['head' if n == 0 else 'cell'])
                     for c in row] for n, row in enumerate(rows)]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#12334A')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.HexColor('#F0F5F8'), colors.white]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#CAD8E0')),
            ]))
            story.extend([table, Spacer(1, 9)])
            continue
        key = 'p'
        if line.startswith('### '):
            key, line = 'h3', line[4:]
        elif line.startswith('## '):
            key, line = 'h2', line[3:]
        elif line.startswith('# '):
            key, line = 'h1', line[2:]
        elif line.startswith('- '):
            line = '• ' + line[2:]
        else:
            while i + 1 < len(lines) and lines[i+1].strip() and not lines[i+1].startswith(('#', '|', '- ')) and lines[i+1].strip() != '---':
                i += 1
                line += ' ' + lines[i].strip()
        story.append(Paragraph(inline(line), styles[key]))
        i += 1

    def page(canvas, doc):
        canvas.saveState()
        w, h = doc.pagesize
        canvas.setStrokeColor(colors.HexColor('#B7CAD6'))
        canvas.line(20*mm, h-16*mm, w-20*mm, h-16*mm)
        canvas.setFont('YaHei', 8)
        canvas.setFillColor(colors.HexColor('#617788'))
        canvas.drawString(20*mm, h-12*mm, 'ORIENTBENCH  /  研究投入决策')
        canvas.drawString(20*mm, 13*mm, '2026-09-08 UTC  |  B主笔，真实C端审阅')
        canvas.drawRightString(w-20*mm, 13*mm, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(OUTPUT), pagesize=(210*mm, 297*mm),
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=24*mm, bottomMargin=23*mm,
                            title='OrientBench 深度调研与下一步研究方案',
                            author='B; independent review by C')
    doc.build(story, onFirstPage=page, onLaterPages=page)
    print(OUTPUT)


if __name__ == '__main__':
    render()
