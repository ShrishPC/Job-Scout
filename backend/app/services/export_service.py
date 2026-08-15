import io
import re
import fitz
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def parse_markdown_runs(text: str):
    """
    Parses a string with markdown bold formatting (**text**) into runs of (text, is_bold).
    """
    runs = []
    tokens = re.split(r'(\*\*.*?\*\*)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            runs.append((token[2:-2], True))
        else:
            runs.append((token, False))
    return runs

def generate_docx_export(
    title: str,
    content: str,
    mode: str = "cover_letter",
    candidate_name: str | None = None,
    candidate_email: str | None = None,
    candidate_phone: str | None = None,
    company: str | None = None,
    job_title: str | None = None,
) -> bytes:
    """
    Generates a beautifully styled Word (.docx) document for a resume or cover letter.
    """
    doc = docx.Document()
    
    # Page setup: 0.75 inch margins
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Base style font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(30, 41, 59) # Slate 800

    # Document Header
    display_name = candidate_name.strip() if candidate_name and candidate_name.strip() else "Applicant"
    p_header = doc.add_paragraph()
    p_header.paragraph_format.space_before = Pt(0)
    p_header.paragraph_format.space_after = Pt(2)
    
    r_title = p_header.add_run(display_name.upper())
    r_title.font.size = Pt(20)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42) # Slate 900

    # Contact line
    contacts = []
    if candidate_email and candidate_email.strip():
        contacts.append(candidate_email.strip())
    if candidate_phone and candidate_phone.strip():
        contacts.append(candidate_phone.strip())
    
    if mode == "cover_letter":
        if job_title or company:
            target_str = f"Target Role: {job_title or 'Position'}" + (f" @ {company}" if company else "")
            contacts.append(target_str)
    elif mode == "tailor":
        contacts.append("Tailored Application Profile")

    if contacts:
        p_contact = doc.add_paragraph()
        p_contact.paragraph_format.space_before = Pt(0)
        p_contact.paragraph_format.space_after = Pt(8)
        r_contact = p_contact.add_run("  •  ".join(contacts))
        r_contact.font.size = Pt(9.5)
        r_contact.font.color.rgb = RGBColor(100, 116, 139) # Slate 500

    # Divider bar
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_before = Pt(0)
    p_div.paragraph_format.space_after = Pt(12)
    pBrd = parse_xml(r'<w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                     r'<w:bottom w:val="single" w:sz="18" w:space="1" w:color="0F172A"/>'
                     r'</w:pBdr>')
    p_div._p.get_or_add_pPr().append(pBrd)

    # Document Body Parsing
    lines = content.split('\n')
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith('# '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            r = p.add_run(line[2:].strip())
            r.font.size = Pt(14)
            r.font.bold = True
            r.font.color.rgb = RGBColor(15, 23, 42)
            # Add bottom border
            hBrd = parse_xml(r'<w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                             r'<w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E1"/>'
                             r'</w:pBdr>')
            p._p.get_or_add_pPr().append(hBrd)

        elif line.startswith('## '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            r = p.add_run(line[3:].strip())
            r.font.size = Pt(12)
            r.font.bold = True
            r.font.color.rgb = RGBColor(30, 41, 59)

        elif line.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            r = p.add_run(line[4:].strip())
            r.font.size = Pt(11)
            r.font.bold = True
            r.font.color.rgb = RGBColor(51, 65, 85)

        elif line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            bullet_text = line[2:].strip()
            runs = parse_markdown_runs(bullet_text)
            for text, is_bold in runs:
                r = p.add_run(text)
                r.font.size = Pt(10.5)
                r.font.bold = is_bold
                r.font.color.rgb = RGBColor(30, 41, 59)

        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
            runs = parse_markdown_runs(line)
            for text, is_bold in runs:
                r = p.add_run(text)
                r.font.size = Pt(10.5)
                r.font.bold = is_bold
                r.font.color.rgb = RGBColor(30, 41, 59)

    doc_io = io.BytesIO()
    doc.save(doc_io)
    return doc_io.getvalue()


def generate_pdf_export(
    title: str,
    content: str,
    mode: str = "cover_letter",
    candidate_name: str | None = None,
    candidate_email: str | None = None,
    candidate_phone: str | None = None,
    company: str | None = None,
    job_title: str | None = None,
) -> bytes:
    """
    Generates a crisp, vector-rendered PDF document with headers, word wrapping, and pagination.
    """
    doc = fitz.open()
    page_w, page_h = 595.32, 841.92 # A4
    margin_l, margin_r = 45, 550
    margin_t, margin_b = 90, 785
    max_w = margin_r - margin_l

    font_helv = fitz.Font('helv')
    font_hebo = fitz.Font('hebo')

    display_name = candidate_name.strip() if candidate_name and candidate_name.strip() else "Applicant"

    def add_page(is_first: bool = False):
        page = doc.new_page(width=page_w, height=page_h)
        if is_first:
            # Banner header on first page
            banner_rect = fitz.Rect(0, 0, page_w, 75)
            page.draw_rect(banner_rect, color=None, fill=(0.06, 0.09, 0.16)) # #0F172A
            
            page.insert_text((margin_l, 34), display_name.upper(), fontsize=15, fontname='hebo', color=(1, 1, 1))
            
            contact_parts = []
            if candidate_email and candidate_email.strip():
                contact_parts.append(candidate_email.strip())
            if candidate_phone and candidate_phone.strip():
                contact_parts.append(candidate_phone.strip())
            if job_title or company:
                target_str = f"Target: {job_title or 'Role'}" + (f" @ {company}" if company else "")
                contact_parts.append(target_str)
            
            contact_str = "  •  ".join(contact_parts) if contact_parts else "Tailored Application Document"
            page.insert_text((margin_l, 52), contact_str, fontsize=9, fontname='helv', color=(0.75, 0.8, 0.88))
            
            # Neo-Brutalist bottom line
            page.draw_line(fitz.Point(0, 75), fitz.Point(page_w, 75), color=(0.98, 0.33, 0.0), width=3) # Orange accent
            return page, margin_t + 10
        else:
            page.insert_text((margin_l, 40), f"{display_name} — {title}", fontsize=8, fontname='helv', color=(0.5, 0.5, 0.5))
            page.draw_line(fitz.Point(margin_l, 48), fitz.Point(margin_r, 48), color=(0.85, 0.85, 0.85), width=0.75)
            return page, 65

    page, curr_y = add_page(is_first=True)

    def wrap_words(text: str, font: fitz.Font, size: float, width: float):
        words = text.split(' ')
        lines = []
        cur_line = []
        for word in words:
            test_line = ' '.join(cur_line + [word])
            if font.text_length(test_line, fontsize=size) <= width:
                cur_line.append(word)
            else:
                if cur_line:
                    lines.append(' '.join(cur_line))
                    cur_line = [word]
                else:
                    lines.append(word)
                    cur_line = []
        if cur_line:
            lines.append(' '.join(cur_line))
        return lines

    for raw_line in content.split('\n'):
        line = raw_line.strip()
        if not line:
            curr_y += 7
            continue

        if line.startswith('# '):
            curr_y += 12
            if curr_y + 25 > margin_b:
                page, curr_y = add_page(is_first=False)
            h_text = line[2:].strip()
            page.insert_text((margin_l, curr_y), h_text, fontsize=13, fontname='hebo', color=(0.06, 0.09, 0.16))
            curr_y += 4
            page.draw_line(fitz.Point(margin_l, curr_y), fitz.Point(margin_r, curr_y), color=(0.8, 0.85, 0.9), width=1)
            curr_y += 14

        elif line.startswith('## '):
            curr_y += 10
            if curr_y + 20 > margin_b:
                page, curr_y = add_page(is_first=False)
            h_text = line[3:].strip()
            page.insert_text((margin_l, curr_y), h_text, fontsize=11, fontname='hebo', color=(0.15, 0.2, 0.3))
            curr_y += 14

        elif line.startswith('### '):
            curr_y += 8
            if curr_y + 16 > margin_b:
                page, curr_y = add_page(is_first=False)
            h_text = line[4:].strip()
            page.insert_text((margin_l, curr_y), h_text, fontsize=10, fontname='hebo', color=(0.2, 0.25, 0.35))
            curr_y += 12

        elif line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
            bullet_text = line[2:].strip()
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', bullet_text)
            wrapped = wrap_words(clean_text, font_helv, 9.5, max_w - 18)
            for idx, w_line in enumerate(wrapped):
                if curr_y + 14 > margin_b:
                    page, curr_y = add_page(is_first=False)
                if idx == 0:
                    page.insert_text((margin_l + 4, curr_y), '•', fontsize=10, fontname='hebo', color=(0.98, 0.33, 0.0))
                page.insert_text((margin_l + 16, curr_y), w_line, fontsize=9.5, fontname='helv', color=(0.15, 0.15, 0.15))
                curr_y += 13
            curr_y += 3

        else:
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            wrapped = wrap_words(clean_text, font_helv, 9.5, max_w)
            for w_line in wrapped:
                if curr_y + 14 > margin_b:
                    page, curr_y = add_page(is_first=False)
                page.insert_text((margin_l, curr_y), w_line, fontsize=9.5, fontname='helv', color=(0.15, 0.15, 0.15))
                curr_y += 13
            curr_y += 4

    # Page Footers
    total_pages = len(doc)
    for p_idx, p in enumerate(doc):
        p.draw_line(fitz.Point(margin_l, margin_b + 10), fitz.Point(margin_r, margin_b + 10), color=(0.85, 0.85, 0.85), width=0.5)
        p.insert_text((margin_l, margin_b + 22), 'Job Scout | AI-Powered Application Suite', fontsize=7.5, fontname='helv', color=(0.55, 0.55, 0.55))
        p.insert_text((margin_r - 55, margin_b + 22), f'Page {p_idx + 1} of {total_pages}', fontsize=7.5, fontname='helv', color=(0.55, 0.55, 0.55))

    return doc.tobytes()
