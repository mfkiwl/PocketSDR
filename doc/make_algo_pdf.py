#!/usr/bin/env python3
"""
Generate algorithms_and_models.pdf for Pocket SDR documentation.
Style follows command_ref.pdf: A4, Calibri font, page numbers top-left.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Polygon, Group
)
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable
import os, sys

# ---------------------------------------------------------------------------
# Register Calibri fonts
# ---------------------------------------------------------------------------
FONT_DIR = "C:/Windows/Fonts"
pdfmetrics.registerFont(TTFont('Calibri',      f'{FONT_DIR}/calibri.ttf'))
pdfmetrics.registerFont(TTFont('Calibri-Bold', f'{FONT_DIR}/calibrib.ttf'))
pdfmetrics.registerFont(TTFont('Calibri-Italic', f'{FONT_DIR}/calibrii.ttf'))
pdfmetrics.registerFontFamily('Calibri',
    normal='Calibri', bold='Calibri-Bold', italic='Calibri-Italic')

# Courier is built-in; use it for monospace (code)
MONO = 'Courier'

# ---------------------------------------------------------------------------
# Page geometry (matches command_ref.pdf: A4)
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = A4          # 595.28 x 841.89 pt
MARGIN_L = 25 * mm
MARGIN_R = 25 * mm
MARGIN_T = 20 * mm
MARGIN_B = 20 * mm

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def make_styles():
    s = {}

    s['normal'] = ParagraphStyle(
        'normal', fontName='Calibri', fontSize=10, leading=14,
        spaceAfter=4, leftIndent=0, alignment=TA_JUSTIFY,
        wordWrap='CJK')

    s['normal_left'] = ParagraphStyle(
        'normal_left', fontName='Calibri', fontSize=10, leading=14,
        spaceAfter=4, leftIndent=0, alignment=TA_LEFT)

    s['h1'] = ParagraphStyle(
        'h1', fontName='Calibri-Bold', fontSize=14, leading=18,
        spaceBefore=14, spaceAfter=6, alignment=TA_LEFT)

    s['h2'] = ParagraphStyle(
        'h2', fontName='Calibri-Bold', fontSize=11, leading=15,
        spaceBefore=10, spaceAfter=4, alignment=TA_LEFT)

    s['h3'] = ParagraphStyle(
        'h3', fontName='Calibri-Bold', fontSize=10, leading=14,
        spaceBefore=8, spaceAfter=3, alignment=TA_LEFT)

    s['cover_title'] = ParagraphStyle(
        'cover_title', fontName='Calibri-Bold', fontSize=22, leading=28,
        spaceBefore=0, spaceAfter=8, alignment=TA_LEFT)

    s['cover_subtitle'] = ParagraphStyle(
        'cover_subtitle', fontName='Calibri', fontSize=14, leading=20,
        spaceAfter=6, alignment=TA_LEFT)

    s['cover_info'] = ParagraphStyle(
        'cover_info', fontName='Calibri', fontSize=11, leading=16,
        spaceAfter=4, alignment=TA_LEFT)

    s['toc_title'] = ParagraphStyle(
        'toc_title', fontName='Calibri-Bold', fontSize=12, leading=16,
        spaceBefore=4, spaceAfter=2, alignment=TA_LEFT)

    s['toc_entry'] = ParagraphStyle(
        'toc_entry', fontName='Calibri', fontSize=10, leading=14,
        spaceAfter=1, leftIndent=0, alignment=TA_LEFT)

    s['toc_sub'] = ParagraphStyle(
        'toc_sub', fontName='Calibri', fontSize=9.5, leading=13,
        spaceAfter=1, leftIndent=10, alignment=TA_LEFT)

    s['code'] = ParagraphStyle(
        'code', fontName=MONO, fontSize=8.5, leading=12,
        spaceAfter=2, leftIndent=6, alignment=TA_LEFT,
        backColor=colors.HexColor('#F5F5F5'))

    s['table_header'] = ParagraphStyle(
        'table_header', fontName='Calibri-Bold', fontSize=9.5, leading=13,
        alignment=TA_LEFT)

    s['table_cell'] = ParagraphStyle(
        'table_cell', fontName='Calibri', fontSize=9.5, leading=13,
        alignment=TA_LEFT)

    s['note'] = ParagraphStyle(
        'note', fontName='Calibri-Italic', fontSize=9.5, leading=13,
        spaceAfter=4, leftIndent=6, alignment=TA_LEFT)

    return s

STYLES = make_styles()

# ---------------------------------------------------------------------------
# Page template: header shows page number (top-left) like command_ref.pdf
# ---------------------------------------------------------------------------
class DocWithPageNum(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._page_num = 0

    def handle_pageBegin(self):
        super().handle_pageBegin()
        self._page_num += 1

    def afterPage(self):
        canvas = self.canv
        pn = self._page_num
        if pn == 1:
            return  # No header on cover page
        canvas.saveState()
        canvas.setFont('Calibri', 10)
        # Page number top-left (matches command_ref.pdf)
        canvas.drawString(MARGIN_L, PAGE_H - MARGIN_T + 4 * mm, str(pn - 1))
        # Horizontal rule below page number
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_L, PAGE_H - MARGIN_T + 2 * mm,
                    PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 2 * mm)
        canvas.restoreState()

# ---------------------------------------------------------------------------
# Helper: code block
# ---------------------------------------------------------------------------
def code_block(text):
    """Return a list of flowables representing a monospace code block."""
    items = []
    lines = text.strip('\n').split('\n')
    for line in lines:
        # Escape ReportLab XML
        line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        items.append(Paragraph(line if line.strip() else '&nbsp;', STYLES['code']))
    return items

# ---------------------------------------------------------------------------
# Helper: simple table
# ---------------------------------------------------------------------------
def make_table(headers, rows, col_widths=None):
    usable = PAGE_W - MARGIN_L - MARGIN_R
    if col_widths is None:
        n = len(headers)
        col_widths = [usable / n] * n

    data = [[Paragraph(h, STYLES['table_header']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), STYLES['table_cell']) for c in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0),  colors.HexColor('#E0E0E0')),
        ('TEXTCOLOR',   (0, 0), (-1, 0),  colors.black),
        ('GRID',        (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
            [colors.white, colors.HexColor('#F8F8F8')]),
        ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',  (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0,0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',(0, 0), (-1, -1), 5),
    ]))
    return t

# ---------------------------------------------------------------------------
# Content builders
# ---------------------------------------------------------------------------
def build_cover():
    story = []
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph('Pocket SDR ver. 0.14', STYLES['cover_subtitle']))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph('Algorithms and Models', STYLES['cover_title']))
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.black))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph('2026-03-16', STYLES['cover_info']))
    story.append(PageBreak())
    return story

def build_toc():
    S = STYLES
    story = []
    story.append(Paragraph('Contents', S['h1']))
    story.append(Spacer(1, 2 * mm))

    toc_data = [
        ('1.', 'System Overview', []),
        ('2.', 'IF Data Handling', [
            'Data Format', 'Sampling Parameters', 'GLONASS FDMA Frequency Shift']),
        ('3.', 'Spreading Code Generation', [
            'Code Types', 'Code Generation Method',
            'Code FFT Pre-computation', 'Code Resampling']),
        ('4.', 'Signal Acquisition', [
            'Parallel Code Search', 'Non-Coherent Integration',
            'Detection and Threshold', 'Fine Doppler Estimation',
            'Doppler Search Range']),
        ('5.', 'Signal Tracking', [
            'Correlator Structure', 'Carrier Tracking: FLL and PLL',
            'Code Tracking: DLL', 'C/N0 Estimation',
            'Secondary Code Synchronization', 'CSK Demodulation (QZSS L6)']),
        ('6.', 'Navigation Data Decoding', [
            'Symbol Synchronization', 'Frame Synchronization',
            'Supported Navigation Messages']),
        ('7.', 'Error Correction', [
            'Convolutional Coding / Viterbi Decoding', 'CRC Checking',
            'LDPC Decoding', 'BCH Error Correction', 'Reed-Solomon Decoding']),
        ('8.', 'PVT Generation', [
            'Overview', 'Observation Data', 'Positioning Engine',
            'Output Formats']),
        ('9.', 'Snapshot Positioning', ['Principle', 'Algorithm']),
        ('10.', 'Receiver Channel State Machine', [
            'State Transitions', 'Timing Parameters']),
    ]

    for num, title, subs in toc_data:
        story.append(Paragraph(f'{num}&nbsp;&nbsp;{title}', S['toc_title']))
        for sub in subs:
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;{sub}', S['toc_sub']))

    story.append(PageBreak())
    return story

# ---------------------------------------------------------------------------
# Section 1: System Overview
# ---------------------------------------------------------------------------
def sec1():
    S = STYLES
    story = []
    story.append(Paragraph('1.  System Overview', S['h1']))

    story.append(Paragraph(
        'Pocket SDR is an open-source GNSS software-defined radio (SDR) receiver. '
        'It processes digitized intermediate-frequency (IF) samples from the Pocket '
        'SDR FE hardware frontend and produces GNSS signal acquisition results '
        '(code offset, Doppler, C/N0), tracked signal observables (carrier phase, '
        'pseudorange, Doppler), decoded navigation data (ephemerides, time, '
        'corrections), and Position/Velocity/Time (PVT) solutions.',
        S['normal']))

    story.append(Paragraph('The software is organized into a layered pipeline:', S['normal']))

    story += code_block("""\
RF Front-end (Pocket SDR FE)
        | digitized IF samples (int8)
        v
IF Data Buffer
        |
        +---> Acquisition (parallel code search)
        |
        +---> Tracking --> Nav Decoding --> PVT""")

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph('Supported GNSS Systems and Signals', S['h2']))

    headers = ['System', 'Signals']
    rows = [
        ['GPS',     'L1C/A, L1C-D, L1C-P, L2C-M, L5-I, L5-Q'],
        ['GLONASS', 'L1C/A (FDMA), L2C/A (FDMA), L1OCd, L1OCp, L2OCp, L3OCd, L3OCp'],
        ['Galileo', 'E1-B, E1-C, E5a-I, E5a-Q, E5b-I, E5b-Q, E6-B, E6-C'],
        ['QZSS',    'L1C/A, L1C/B, L1C-D, L1C-P, L1S, L2C-M, L5-I, L5-Q, L5S-I, L5S-Q, L6D, L6E'],
        ['BeiDou',  'B1I, B1C-D, B1C-P, B2a-D, B2a-P, B2I, B2b-I, B3I'],
        ['NavIC',   'L1-SPS-D, L1-SPS-P, L5-SPS'],
        ['SBAS',    'L1C/A, L5-I, L5-Q'],
    ]
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story.append(make_table(headers, rows, [usable * 0.2, usable * 0.8]))
    return story

# ---------------------------------------------------------------------------
# Section 2: IF Data Handling
# ---------------------------------------------------------------------------
def sec2():
    S = STYLES
    story = []
    story.append(Paragraph('2.  IF Data Handling', S['h1']))

    story.append(Paragraph('2.1  Data Format', S['h2']))
    story.append(Paragraph(
        'The Pocket SDR FE captures IF data in one of the following formats:',
        S['normal']))

    headers = ['Format', 'Description']
    rows = [
        ['I-sampling (real)',    'Single int8 sample per time step'],
        ['IQ-sampling (complex)','Interleaved int8 pairs: I, Q, I, Q, ...'],
    ]
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story.append(make_table(headers, rows, [usable * 0.3, usable * 0.7]))

    story.append(Paragraph(
        'The read_data() function (sdr_func.py) reads raw int8 samples from a binary '
        'file and converts them to complex64 (numpy complex64) arrays. '
        'For I-sampling: data = int8_sample + 0j. '
        'For IQ-sampling: data = I_sample - j * Q_sample. '
        'The negative sign on Q derives from the down-conversion convention used '
        'by the MAX2771 frontend IC.',
        S['normal']))

    story.append(Paragraph('2.2  Sampling Parameters', S['h2']))
    story.append(Paragraph(
        'Key parameters for IF data processing:', S['normal']))

    headers = ['Parameter', 'Symbol', 'Typical Values']
    rows = [
        ['Sampling frequency', 'fs', '12 MHz, 24 MHz, 48 MHz'],
        ['IF frequency',       'fi', '0 Hz (zero-IF) or non-zero'],
        ['Sample type',        'IQ', '1 (I-only) or 2 (IQ)'],
    ]
    story.append(make_table(headers, rows, [usable*0.4, usable*0.2, usable*0.4]))
    story.append(Paragraph(
        'For zero-IF (fi = 0), IQ-sampling is assumed automatically.',
        S['normal']))

    story.append(Paragraph('2.3  GLONASS FDMA Frequency Shift', S['h2']))
    story.append(Paragraph(
        'GLONASS uses FDMA with per-satellite frequency channel numbers (FCN). '
        'The IF frequency is shifted accordingly before correlation:',
        S['normal']))
    story += code_block("""\
G1CA:  fi_shifted = fi + 0.5625 MHz x FCN
G2CA:  fi_shifted = fi + 0.4375 MHz x FCN""")
    return story

# ---------------------------------------------------------------------------
# Section 3: Spreading Code Generation
# ---------------------------------------------------------------------------
def sec3():
    S = STYLES
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story = []
    story.append(Paragraph('3.  Spreading Code Generation', S['h1']))

    story.append(Paragraph('3.1  Code Types', S['h2']))
    story.append(Paragraph(
        'Pocket SDR generates spreading codes for all supported signals in software. '
        'The primary code is a PRN-specific binary sequence (chip values +/-1). '
        'Several signal types additionally use a secondary (overlay) code modulated '
        'on top of the primary code to extend coherent integration.',
        S['normal']))

    headers = ['Signal', 'Primary Code', 'Secondary Code']
    rows = [
        ['GPS L1C/A',    '1023-chip Gold code',       'None'],
        ['GPS L1C-D',    '10230-chip Weil code',      '1800-chip overlay'],
        ['GPS L5-I',     '10230-chip XB code',        '10-chip Neumann-Hofman'],
        ['Galileo E1-B', '4092-chip memory code',     'None'],
        ['Galileo E5a-I','10230-chip memory code',    '20-chip secondary'],
        ['QZSS L6D/L6E', '10230-chip CSK code',       'None'],
        ['BeiDou B1C-D', '10230-chip Weil code',      '1800-chip overlay'],
        ['GLONASS L1C/A','511-chip m-sequence',       'None'],
    ]
    story.append(make_table(headers, rows, [usable*0.25, usable*0.42, usable*0.33]))

    story.append(Paragraph('3.2  Code Generation Method', S['h2']))
    story.append(Paragraph(
        'Most codes are generated by linear feedback shift registers (LFSRs) or '
        'stored memory tables derived from the respective ICD. The generation '
        'polynomial for each signal follows its official interface control document (ICD). '
        'Code generation for all supported signals is implemented in sdr_code.py '
        'and sdr_code_gal.py.',
        S['normal']))

    story.append(Paragraph('3.3  Code FFT Pre-computation', S['h2']))
    story.append(Paragraph(
        'For the FFT-based correlator, the code DFT (discrete Fourier transform) '
        'is pre-computed once per channel and reused across all Doppler bins:',
        S['normal']))
    story += code_block(
        'code_fft = conj( FFT( code_resampled_with_zero_padding ) )')
    story.append(Paragraph(
        'Zero-padding to twice the code length (2N) is optional (the -nz flag '
        'disables it). Zero-padding enables circular correlation without aliasing.',
        S['normal']))

    story.append(Paragraph('3.4  Code Resampling', S['h2']))
    story.append(Paragraph(
        'When the code chip rate does not divide evenly into the sampling frequency, '
        'the code is resampled to the sample grid. For tracking, a code bank of '
        'N_CODE = 10 versions with sub-sample offsets is maintained to allow '
        'fractional-chip code offset tracking without re-interpolation at every epoch.',
        S['normal']))
    return story

# ---------------------------------------------------------------------------
# Section 4: Signal Acquisition
# ---------------------------------------------------------------------------
def sec4():
    S = STYLES
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story = []
    story.append(Paragraph('4.  Signal Acquisition', S['h1']))

    story.append(Paragraph('4.1  Parallel Code Search', S['h2']))
    story.append(Paragraph(
        'Signal acquisition searches a two-dimensional space of code offset tau '
        'and Doppler frequency fd. The search uses a parallel code search algorithm '
        'based on the circular cross-correlation property of the FFT.',
        S['normal']))
    story.append(Paragraph('For each Doppler bin fd_i:', S['normal']))
    story += code_block("""\
1. Mix IF data with a local carrier at fi + fd_i:
   data_mixed[n] = data[n] * exp(-j 2pi (fi + fd_i) n / fs)

2. Compute circular cross-correlation via FFT:
   C[tau] = IFFT( FFT(data_mixed) * code_fft )
   where code_fft = conj( FFT(code) )

3. Compute correlation power:
   P[i, tau] = |C[tau]|^2""")
    story.append(Paragraph(
        'The result is a 2D power surface P(fd, tau).', S['normal']))

    story.append(Paragraph('4.2  Non-Coherent Integration', S['h2']))
    story.append(Paragraph(
        'To improve sensitivity, correlation powers from multiple code cycles are '
        'accumulated non-coherently (power summation, not complex summation):',
        S['normal']))
    story += code_block('P_sum += P[i, tau]   for each code cycle')
    story.append(Paragraph(
        'The default non-coherent integration time is T_ACQ = 10 ms (approximately '
        '10 code cycles for 1 ms codes). This avoids the navigation data bit '
        'ambiguity while providing approximately 10 dB integration gain.',
        S['normal']))

    story.append(Paragraph('4.3  Detection and Threshold', S['h2']))
    story.append(Paragraph(
        'After integration, the peak is found and the C/N0 metric is computed:',
        S['normal']))
    story += code_block("""\
P_max = max(P_sum)
P_ave = mean(P_sum)
C/N0  = 10 * log10( (P_max - P_ave) / P_ave / T_code )   [dB-Hz]""")
    story.append(Paragraph(
        'The signal is declared acquired when C/N0 >= 35 dB-Hz.',
        S['normal']))

    story.append(Paragraph('4.4  Fine Doppler Estimation', S['h2']))
    story.append(Paragraph(
        'The coarse Doppler bin index is refined by fitting a quadratic polynomial '
        'to the three power values around the peak bin:',
        S['normal']))
    story += code_block("""\
p(f) = a*f^2 + b*f + c
f_fine = -b / (2*a)""")
    story.append(Paragraph(
        'This provides sub-bin Doppler accuracy without reducing the bin spacing.',
        S['normal']))

    story.append(Paragraph('4.5  Doppler Search Range', S['h2']))
    story.append(Paragraph(
        'Default Doppler search range: +/-5000 Hz. '
        'Search step: DOP_STEP / T_code = 0.5 / T_code Hz (0.5 bins per code cycle). '
        'For GLONASS FDMA signals, the search centre is shifted by the FCN '
        'frequency offset before the search.',
        S['normal']))
    return story

# ---------------------------------------------------------------------------
# Section 5: Signal Tracking
# ---------------------------------------------------------------------------
def sec5():
    S = STYLES
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story = []
    story.append(Paragraph('5.  Signal Tracking', S['h1']))

    story.append(Paragraph('5.1  Correlator Structure', S['h2']))
    story.append(Paragraph(
        'The tracking loop uses a set of correlators at different code phase offsets:',
        S['normal']))

    headers = ['Correlator', 'Offset', 'Purpose']
    rows = [
        ['Prompt (P)', '0 chips',         'Phase/frequency error discrimination'],
        ['Early (E)',  '+d/2 chips',       'DLL discriminator'],
        ['Late (L)',   '-d/2 chips',       'DLL discriminator'],
        ['Noise (N)',  '-80 samples',      'Noise floor estimate for C/N0'],
    ]
    story.append(make_table(headers, rows, [usable*0.2, usable*0.2, usable*0.6]))
    story.append(Paragraph(
        'Default correlator spacing: d = 0.25 chips (SP_CORR). '
        'At each epoch (one code cycle), the correlator outputs are computed by '
        'mixing the IF data with the local carrier replica and integrating against '
        'the local code replica:',
        S['normal']))
    story += code_block(
        'C_k = SUM{ data[n] * exp(-j 2pi fc_k n / fs) * code[n - tau_k] } / N')
    story.append(Paragraph(
        'For QZSS L6D/L6E (CSK modulation), the FFT correlator is used instead '
        '(see Section 5.6).',
        S['normal']))

    story.append(Paragraph('5.2  Carrier Tracking: FLL and PLL', S['h2']))
    story.append(Paragraph(
        'The tracking loop uses a two-stage approach:', S['normal']))
    story.append(Paragraph(
        'Stage 1 - Frequency Lock Loop (FLL): '
        'Active for the first T_FPULLIN = 1.0 s to achieve initial frequency lock. '
        'The FLL discriminator uses the cross/dot product of consecutive P correlator outputs:',
        S['normal']))
    story += code_block("""\
dot   = I1*I2 + Q1*Q2
cross = I1*Q2 - Q1*I2
err_freq = atan(cross / dot)    [Costas, for BPSK]
         = atan2(cross, dot)    [non-Costas, for data-less pilot]

Frequency update:
fd -= (B_FLL / 0.25) * err_freq / (2*pi)""")
    story.append(Paragraph(
        'FLL bandwidth transitions from 5 Hz (wide) to 2 Hz (narrow) at the '
        'halfway point of the pull-in time.',
        S['normal']))
    story.append(Paragraph(
        'Stage 2 - Phase Lock Loop (PLL): '
        'Activated after FLL pull-in. Uses a second-order PLL (B_PLL = 5.0 Hz):',
        S['normal']))
    story += code_block("""\
err_phas = atan(QP / IP) / (2*pi)    [Costas]
         = atan2(QP, IP) / (2*pi)    [non-Costas]

W = B_PLL / 0.53
fd += 1.4*W*(err_phas - err_phas_prev) + W^2 * err_phas * T""")

    story.append(Paragraph('5.3  Code Tracking: DLL', S['h2']))
    story.append(Paragraph(
        'A non-coherent Early-minus-Late (EML) delay lock loop (DLL) tracks the '
        'code phase. The DLL runs every N = T_DLL / T_code epochs (default: 10 '
        'epochs for 1 ms codes) using accumulated E and L magnitudes.',
        S['normal']))
    story += code_block("""\
Discriminator (normalized):
err_code = (|E| - |L|) / (|E| + |L|) / 2 * T_code / code_length   [s]

Code phase update:
coff -= (B_DLL / 0.25) * err_code * T_code * N     [B_DLL = 0.25 Hz]

Carrier-aided code tracking:
coff -= fd / fc * dt""")
    story.append(Paragraph(
        'Carrier-aided code tracking reduces code tracking noise by incorporating '
        'the tracked carrier Doppler, where fc is the carrier frequency and dt is '
        'the elapsed time since the last update.',
        S['normal']))

    story.append(Paragraph('5.4  C/N0 Estimation', S['h2']))
    story.append(Paragraph(
        'C/N0 is estimated using the signal-to-noise ratio of the Prompt correlator '
        'output versus the noise reference correlator (N):',
        S['normal']))
    story += code_block("""\
C/N0 = 10 * log10( SUM|P|^2 / SUM|N|^2 / T_code )   [dB-Hz]""")
    story.append(Paragraph(
        'The estimate is smoothed with an exponential moving average (alpha = 0.5) '
        'over T_CN0 = 1.0 s. Signal lock is declared lost when C/N0 < 32 dB-Hz.',
        S['normal']))

    story.append(Paragraph('5.5  Secondary Code Synchronization', S['h2']))
    story.append(Paragraph(
        'Pilot signals (e.g., GPS L1C-P, Galileo E1-C, BeiDou B1C-P) modulate the '
        'primary code with a secondary (overlay) code. Pocket SDR detects and '
        'removes this secondary code by computing the cross-correlation of the P '
        'correlator history with the known secondary code sequence. '
        'Synchronization is declared when the normalized correlation exceeds '
        'THRES_SYNC = 0.02. After synchronization, each P correlator output is '
        'multiplied by the corresponding secondary code chip.',
        S['normal']))

    story.append(Paragraph('5.6  CSK Demodulation (QZSS L6)', S['h2']))
    story.append(Paragraph(
        'QZSS L6D/L6E uses Code-Shift Keying (CSK) modulation. The transmitted '
        'symbol is encoded as a circular shift of the spreading code. '
        'Pocket SDR decodes it using the following procedure:',
        S['normal']))
    story += code_block("""\
1. Compute full circular cross-correlation over the code period via FFT.
2. Interpolate the correlation power profile at +/-255 chips around center.
3. Detect the peak position; the peak shift index gives the CSK symbol (0-255).
4. The correlator output at the peak position is used as the P correlator.""")
    return story

# ---------------------------------------------------------------------------
# Section 6: Navigation Data Decoding
# ---------------------------------------------------------------------------
def sec6():
    S = STYLES
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story = []
    story.append(Paragraph('6.  Navigation Data Decoding', S['h1']))

    story.append(Paragraph('6.1  Symbol Synchronization', S['h2']))
    story.append(Paragraph(
        'Navigation data bits (symbols) are extracted from the P correlator outputs. '
        'Symbol boundaries are detected by monitoring transitions in the sign of '
        'accumulated P correlator outputs. Once synchronized, each bit is decided '
        'by the sign of the integrated P output over one symbol period.',
        S['normal']))

    story.append(Paragraph('6.2  Frame Synchronization', S['h2']))
    story.append(Paragraph(
        'Each navigation message format has a known preamble or sync word. '
        'Pocket SDR searches for the preamble in the accumulated symbol buffer. '
        'On detection, the frame boundary and data polarity (normal/inverted) '
        'are established.',
        S['normal']))

    story.append(Paragraph('6.3  Supported Navigation Messages', S['h2']))

    headers = ['Signal', 'Message Format', 'Key Content']
    rows = [
        ['GPS L1C/A',    'LNAV (25 words x 30 bits)', 'Ephemeris, almanac, UTC/iono'],
        ['GPS L1C-D',    'CNAV-2 (subframe 2 & 3)',   'Ephemeris'],
        ['GPS L2C-M',    'CNAV',                       'Ephemeris, clock corrections'],
        ['GPS L5-I',     'CNAV',                       'Ephemeris, clock corrections'],
        ['Galileo E1-B', 'I/NAV (page pairs)',         'Ephemeris, iono, UTC'],
        ['Galileo E5b-I','I/NAV',                      'Ephemeris'],
        ['Galileo E6-B', 'HAS (High Accuracy Service)','PPP corrections'],
        ['QZSS L1C/A',   'LNAV',                       'Ephemeris (QZSS-specific)'],
        ['QZSS L6D',     'CLAS message (Reed-Solomon)','Centimetre-level augmentation'],
        ['BeiDou B1I',   'D1/D2 NAV',                  'Ephemeris, almanac'],
        ['BeiDou B1C-D', 'CNAV-1',                     'Ephemeris'],
        ['BeiDou B2a-D', 'CNAV-2',                     'Ephemeris'],
        ['GLONASS L1C/A','GLONASS NAV (strings)',      'Ephemeris, almanac'],
        ['NavIC L5-SPS', 'IRNSS NAV',                  'Ephemeris'],
    ]
    story.append(make_table(headers, rows, [usable*0.22, usable*0.35, usable*0.43]))
    return story

# ---------------------------------------------------------------------------
# Section 7: Error Correction
# ---------------------------------------------------------------------------
def sec7():
    S = STYLES
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story = []
    story.append(Paragraph('7.  Error Correction', S['h1']))

    story.append(Paragraph('7.1  Convolutional Coding / Viterbi Decoding', S['h2']))
    story.append(Paragraph(
        'Many GNSS navigation messages (GPS L5, Galileo E1-B/E5, BeiDou B1C) use '
        'rate-1/2, constraint-length-7 convolutional channel coding. '
        'Pocket SDR decodes these using the Viterbi algorithm implemented in '
        'the libfec external library.',
        S['normal']))

    headers = ['Parameter', 'Value']
    rows = [
        ['Code rate',                 '1/2'],
        ['Constraint length',         'K = 7'],
        ['Generator polynomial G1',   '0x4F'],
        ['Generator polynomial G2',   '0x6D'],
    ]
    story.append(make_table(headers, rows, [usable*0.4, usable*0.6]))

    story.append(Paragraph('7.2  CRC Checking', S['h2']))
    story.append(Paragraph(
        'Navigation frames include CRC (cyclic redundancy check) fields that are '
        'verified after Viterbi decoding. Only frames passing CRC are accepted.',
        S['normal']))

    story.append(Paragraph('7.3  LDPC Decoding (BeiDou B1C, B2a, B2b)', S['h2']))
    story.append(Paragraph(
        'BeiDou new-generation signals use Low-Density Parity-Check (LDPC) codes. '
        'Pocket SDR provides two decoders:',
        S['normal']))
    story += code_block("""\
Full LDPC decoder (sdr_ldpc.py):
  Uses the LDPC-codes external library (sum-product / belief propagation).

NB-LDPC decoder (sdr_nb_ldpc.py):
  Compact non-binary LDPC decoder optimized for B1C, B2a, and B2b subframes.""")

    story.append(Paragraph('7.4  BCH Error Correction (BeiDou B1I)', S['h2']))
    story.append(Paragraph(
        'BeiDou B1I uses BCH(15, 11, 1) error correction for certain fields. '
        'Pocket SDR implements this via a pre-computed error correction lookup '
        'table (BCH_CORR_TBL in sdr_nav.py) covering all single-bit error patterns.',
        S['normal']))

    story.append(Paragraph('7.5  Reed-Solomon Decoding (QZSS L6)', S['h2']))
    story.append(Paragraph(
        'QZSS L6D CLAS data uses Reed-Solomon error correction applied across '
        'message frames. Pocket SDR decodes this using the libfec library\'s '
        'RS(255, 223) implementation.',
        S['normal']))
    return story

# ---------------------------------------------------------------------------
# Section 8: PVT Generation
# ---------------------------------------------------------------------------
def sec8():
    S = STYLES
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story = []
    story.append(Paragraph('8.  PVT Generation', S['h1']))

    story.append(Paragraph('8.1  Overview', S['h2']))
    story.append(Paragraph(
        'The PVT module (sdr_pvt.c) generates position, velocity, and time '
        'solutions using RTKLIB as the positioning engine. PVT is computed '
        'at 1 Hz epochs.',
        S['normal']))

    story.append(Paragraph('8.2  Observation Data', S['h2']))
    story.append(Paragraph(
        'At each epoch, observables are assembled from all locked channels:',
        S['normal']))
    story += code_block("""\
Pseudorange  : derived from tracked code phase offset and receiver time
Carrier phase: integrated from accumulated Doppler and current carrier phase
Doppler      : from the tracked carrier frequency offset (fd)
C/N0         : from the C/N0 estimator (Section 5.4)""")
    story.append(Paragraph(
        'An elevation mask of 15 degrees is applied to reject low-elevation '
        'satellites.',
        S['normal']))

    story.append(Paragraph('8.3  Positioning Engine', S['h2']))
    story.append(Paragraph(
        'PVT uses RTKLIB\'s least-squares single-point positioning algorithm. '
        'The solution accounts for:',
        S['normal']))
    story += code_block("""\
- Satellite positions and velocities from decoded ephemerides
- Ionospheric delay (Klobuchar model for GPS/QZSS, Galileo NeQuick broadcast)
- Tropospheric delay (Saastamoinen model)
- Satellite clock corrections from navigation data
- Relativistic corrections""")

    story.append(Paragraph('8.4  Output Formats', S['h2']))
    headers = ['Format', 'Description']
    rows = [
        ['NMEA 0183', 'GGA, RMC, GSA, GSV sentences (standard marine/mapping format)'],
        ['RTCM3',     'RTCM 10403.x binary format for differential corrections'],
        ['Internal log', 'CSV-format $POS, $OBS, $SAT log records'],
    ]
    story.append(make_table(headers, rows, [usable*0.25, usable*0.75]))
    return story

# ---------------------------------------------------------------------------
# Section 9: Snapshot Positioning
# ---------------------------------------------------------------------------
def sec9():
    S = STYLES
    story = []
    story.append(Paragraph('9.  Snapshot Positioning', S['h1']))

    story.append(Paragraph('9.1  Principle', S['h2']))
    story.append(Paragraph(
        'Snapshot positioning (pocket_snap.py, pocket_snap) computes a position '
        'from a single short capture of IF data (typically a few milliseconds), '
        'without requiring continuous tracking or navigation data download. '
        'It uses a coarse time and approximate position to predict the expected '
        'code offset for each visible satellite, acquire signals to measure the '
        'actual code offsets, and compute a position from the pseudorange differences.',
        S['normal']))

    story.append(Paragraph('9.2  Algorithm', S['h2']))
    story += code_block("""\
1. Signal acquisition:
   Run parallel code search over the snapshot buffer
   for each candidate satellite and signal.

2. Pseudorange prediction:
   Using the known approximate receiver position and time,
   compute predicted pseudoranges from broadcast ephemerides.

3. Residual computation:
   Compute pseudorange residuals between measured and predicted values.

4. Position solution:
   Solve for position using RTKLIB's positioning engine
   with the residual pseudoranges.""")
    story.append(Paragraph(
        'This approach requires an initial position estimate (within approximately '
        '150 km) and approximate time (within approximately 1 minute).',
        S['normal']))
    return story

# ---------------------------------------------------------------------------
# State machine diagram (ReportLab Drawing)
# ---------------------------------------------------------------------------
def state_machine_drawing(width=440):
    """
    Draw the IDLE/SRCH/LOCK state machine diagram.
    Layout (left to right):  IDLE --- SRCH
                                        |
                             IDLE <-- LOCK
    with a wrap-around arc from LOCK back to IDLE via the top.
    """
    BW, BH = 80, 36        # box width/height
    FN  = 'Calibri-Bold'
    FNr = 'Calibri'
    FS  = 9
    GREY = colors.HexColor('#D8D8D8')
    BLACK = colors.black
    BLUE  = colors.HexColor('#1F497D')

    # Box centres  (x, y)  — y increases upward in RL coordinates
    H = 160   # drawing height
    cy_mid = H / 2         # vertical centre for IDLE and SRCH
    cx_idle = 70
    cx_srch = 230
    cx_lock = 370

    def box(cx, cy, label):
        g = Group()
        g.add(Rect(cx - BW/2, cy - BH/2, BW, BH,
                   fillColor=GREY, strokeColor=BLACK, strokeWidth=0.8))
        g.add(String(cx, cy - FS/2, label,
                     fontName=FN, fontSize=FS+1,
                     fillColor=BLACK, textAnchor='middle'))
        return g

    def arrow(x1, y1, x2, y2, label='', label_above=True, color=BLACK):
        """Straight arrow from (x1,y1) to (x2,y2)."""
        g = Group()
        g.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=0.8))
        # arrowhead
        dx, dy = x2 - x1, y2 - y1
        L = (dx*dx + dy*dy) ** 0.5
        if L == 0:
            return g
        ux, uy = dx/L, dy/L
        aw, ah = 5, 9
        tip = (x2, y2)
        p1 = (x2 - uy*aw - ux*ah, y2 + ux*aw - uy*ah)
        p2 = (x2 + uy*aw - ux*ah, y2 - ux*aw - uy*ah)
        g.add(Polygon([tip[0], tip[1], p1[0], p1[1], p2[0], p2[1]],
                      fillColor=color, strokeColor=color, strokeWidth=0.5))
        if label:
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            off = 8 if label_above else -8
            # rotate label for vertical arrows
            if abs(dx) < 1:
                g.add(String(mx + off, my, label,
                             fontName=FNr, fontSize=FS - 1,
                             fillColor=color, textAnchor='start' if off > 0 else 'end'))
            else:
                g.add(String(mx, my + off, label,
                             fontName=FNr, fontSize=FS - 1,
                             fillColor=color, textAnchor='middle'))
        return g

    d = Drawing(width, H)

    # -- IDLE -> SRCH (top, left to right) -----------------------------------
    d.add(arrow(cx_idle + BW/2, cy_mid + 8,
                cx_srch - BW/2, cy_mid + 8,
                'C/N0 >= 35 dB-Hz  (signal acquired)', label_above=True))

    # -- SRCH -> IDLE (bottom, right to left — "not found") ------------------
    d.add(arrow(cx_srch - BW/2, cy_mid - 8,
                cx_idle + BW/2, cy_mid - 8,
                'signal not found', label_above=False))

    # -- SRCH -> LOCK (right side, top to bottom) ----------------------------
    d.add(arrow(cx_srch + BW/2, cy_mid,
                cx_lock - BW/2, cy_mid,
                'signal found', label_above=True))

    # -- LOCK -> IDLE  (diagonal arc via bottom) ----------------------------
    # Use a polyline:  LOCK bottom -> midpoint bottom -> IDLE bottom -> IDLE
    lx = cx_lock - BW/2
    ly = cy_mid - BH/2
    mid_x = (cx_idle + cx_lock) / 2
    bot_y = 14
    ix = cx_idle
    iy = cy_mid - BH/2
    g = Group()
    pts = [lx + BW/2, ly,
           mid_x,    bot_y + 4,
           cx_idle + BW/2 - 10, bot_y + 4]
    for i in range(0, len(pts) - 2, 2):
        g.add(Line(pts[i], pts[i+1], pts[i+2], pts[i+3],
                   strokeColor=BLACK, strokeWidth=0.8))
    # last segment with arrow
    g.add(arrow(cx_idle + BW/2 - 10, bot_y + 4,
                cx_idle + BW/2, iy,
                '', color=BLACK))
    g.add(String(mid_x, bot_y - 4,
                 'C/N0 < 32 dB-Hz  (signal lost)',
                 fontName=FNr, fontSize=FS - 1,
                 fillColor=BLACK, textAnchor='middle'))
    d.add(g)

    # -- Boxes (drawn last so they sit on top of arrows) ---------------------
    d.add(box(cx_idle, cy_mid, 'IDLE'))
    d.add(box(cx_srch, cy_mid, 'SRCH'))
    d.add(box(cx_lock, cy_mid, 'LOCK'))

    return d

# Wrap Drawing as a Platypus Flowable
class DrawingFlowable(Flowable):
    def __init__(self, drawing):
        super().__init__()
        self.drawing = drawing
        self.width  = drawing.width
        self.height = drawing.height

    def draw(self):
        renderPDF.draw(self.drawing, self.canv, 0, 0)

# ---------------------------------------------------------------------------
# Section 10: Receiver Channel State Machine
# ---------------------------------------------------------------------------
def sec10():
    S = STYLES
    usable = PAGE_W - MARGIN_L - MARGIN_R
    story = []
    story.append(Paragraph('10.  Receiver Channel State Machine', S['h1']))

    story.append(Paragraph(
        'Each receiver channel (sdr_ch.py) is an independent state machine with '
        'three states:',
        S['normal']))
    usable_w = PAGE_W - MARGIN_L - MARGIN_R
    story.append(Spacer(1, 3 * mm))
    story.append(DrawingFlowable(state_machine_drawing(width=float(usable_w))))
    story.append(Spacer(1, 3 * mm))

    headers = ['State', 'Description']
    rows = [
        ['IDLE', 'Waiting for the next acquisition trigger'],
        ['SRCH', 'Running parallel code search (acquisition)'],
        ['LOCK', 'Running tracking loops (DLL/FLL/PLL) and decoding navigation data'],
    ]
    story.append(make_table(headers, rows, [usable*0.2, usable*0.8]))

    story.append(Paragraph('10.1  State Transitions', S['h2']))
    story += code_block("""\
IDLE -> SRCH : Triggered externally by the receiver scheduler.
SRCH -> LOCK : Signal found (C/N0 >= 35 dB-Hz after T_ACQ integration).
SRCH -> IDLE : Signal not found after T_ACQ integration.
LOCK -> IDLE : C/N0 drops below 32 dB-Hz (signal lost).""")

    story.append(Paragraph('10.2  Timing Parameters', S['h2']))
    headers = ['Parameter', 'Symbol', 'Default', 'Description']
    rows = [
        ['Acquisition integration', 'T_ACQ',       '10 ms',    'Non-coherent integration for acquisition'],
        ['FLL pull-in',             'T_FPULLIN',    '1.0 s',    'Duration of FLL before switching to PLL'],
        ['Nav pull-in',             'T_NPULLIN',    '1.5 s',    'Delay before starting nav data decoding'],
        ['DLL integration',         'T_DLL',        '10 ms',    'Non-coherent integration for DLL'],
        ['C/N0 averaging',          'T_CN0',        '1.0 s',    'Averaging window for C/N0 estimator'],
        ['Lock threshold',          'THRES_CN0[0]', '35 dB-Hz', 'C/N0 to declare acquisition success'],
        ['Lost threshold',          'THRES_CN0[1]', '32 dB-Hz', 'C/N0 below which tracking is lost'],
    ]
    story.append(make_table(headers, rows,
        [usable*0.32, usable*0.18, usable*0.13, usable*0.37]))
    return story

# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
def build_refs():
    S = STYLES
    story = []
    story.append(Paragraph('References', S['h1']))
    refs = [
        '[1] IS-GPS-200K, NAVSTAR GPS Space Segment/Navigation User Segment Interfaces, May 19, 2019.',
        '[2] IS-GPS-800F, Navstar GPS Space Segment / User Segment L1C Interfaces, March 4, 2019.',
        '[3] IS-GPS-705A, Navstar GPS Space Segment / User Segment L5 Interfaces, June 8, 2010.',
        '[4] Galileo Open Service Signal In Space Interface Control Document, Issue 2.0.',
        '[5] Galileo E6-B/C Codes Technical Note, Issue 1, January 2019.',
        '[6] IS-QZSS-PNT-004, Quasi-Zenith Satellite System Interface Specification, November 5, 2018.',
        '[7] IS-QZSS-L6-003, Quasi-Zenith Satellite System Interface Specification - '
            'Centimeter Level Augmentation Service, August 20, 2020.',
        '[8] BeiDou Navigation Satellite System Signal In Space ICDs '
            '(B1I v3.0, B1C v1.0, B2a v1.0, B2b v1.0, B3I v1.0).',
        '[9] GLONASS Interface Control Document (L1, L2, L3 bands).',
        '[10] IRNSS/NavIC SIS ICD for Standard Positioning Service, version 1.1, August 2017.',
        '[11] NavIC Signal in Space ICD for Standard Positioning Service in L1, version 1.0, August 2023.',
        '[12] RTKLIB: An Open Source Program Package for GNSS Positioning (https://rtklib.com/).',
        '[13] libfec: A library for Forward Error Correction (https://github.com/quiet/libfec).',
        '[14] LDPC-codes: A library for LDPC decoding (https://github.com/radfordneal/LDPC-codes).',
        '[15] T.Takasu, Pocket SDR: Design, Implementation and Applications, '
            'A seminar for GNSS Software Defined Receivers, Nov 19, 2024.',
    ]
    for r in refs:
        story.append(Paragraph(r, S['normal_left']))
        story.append(Spacer(1, 1 * mm))
    return story

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    out_path = 'C:/share/PocketSDR/.claude/worktrees/sad-vaughan/doc/algorithms_and_models.pdf'

    doc = DocWithPageNum(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T + 8 * mm,
        bottomMargin=MARGIN_B,
        title='Pocket SDR Algorithms and Models',
        author='T.Takasu',
        subject='GNSS SDR Algorithms',
    )

    story = []
    story += build_cover()
    story += build_toc()
    story += sec1()
    story.append(PageBreak())
    story += sec2()
    story.append(PageBreak())
    story += sec3()
    story.append(PageBreak())
    story += sec4()
    story.append(PageBreak())
    story += sec5()
    story.append(PageBreak())
    story += sec6()
    story.append(PageBreak())
    story += sec7()
    story.append(PageBreak())
    story += sec8()
    story.append(PageBreak())
    story += sec9()
    story.append(PageBreak())
    story += sec10()
    story.append(PageBreak())
    story += build_refs()

    doc.build(story)
    print(f'PDF generated: {out_path}')

if __name__ == '__main__':
    main()
