"""PDF legible por empresa, a partir de las mismas alertas que el Excel."""
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor('#163B59')
TEAL = colors.HexColor('#087F8C')


class Bar(Flowable):
    def __init__(self, value, maximum):
        super().__init__()
        self.width, self.height = 240, 14
        self.value, self.maximum = value, maximum
    def draw(self):
        self.canv.setFillColor(colors.HexColor('#E8F3F5'))
        self.canv.roundRect(0, 3, 240, 8, 2, fill=1, stroke=0)
        self.canv.setFillColor(TEAL)
        self.canv.roundRect(0, 3, max(2, 240 * self.value / self.maximum), 8, 2, fill=1, stroke=0)


def write_pdf(path, events, exported, title, day):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Company', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=NAVY, spaceAfter=12))
    styles.add(ParagraphStyle(name='SmallNote', fontSize=9, leading=13, textColor=colors.HexColor('#526576')))
    styles.add(ParagraphStyle(name='CellSmall', fontSize=9, leading=12, textColor=NAVY))
    styles.add(ParagraphStyle(name='Metric', fontSize=23, leading=27, alignment=TA_CENTER, textColor=NAVY))
    styles.add(ParagraphStyle(name='MetricLabel', fontSize=9, leading=13, alignment=TA_CENTER, textColor=TEAL))
    width, height = landscape(A4)
    usable = width - 64
    def p(value, style='CellSmall'):
        return Paragraph(escape(str(value)), styles[style])
    def table(data, widths, header=True):
        result = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
        commands = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F5F8')])]
        if header:
            commands += [('BACKGROUND', (0, 0), (-1, 0), NAVY), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')]
        result.setStyle(TableStyle(commands))
        return result
    story = [p('O.S. LOGISTICS PERÚ S.A.C.', 'SmallNote'), Spacer(1, 8), p(title, 'Company'),
             p(f'Reporte de alertas | {day} | Hora local Lima', 'SmallNote'), Spacer(1, 16)]
    metrics = [('ALERTAS', len(events)), ('VELOCIDAD', int(events.Alerta.str.contains('velocidad', case=False).sum())),
               ('MANIOBRAS BRUSCAS', int(events.Alerta.str.contains('brusc', case=False).sum())), ('SOS', int(events.Alerta.eq('SOS').sum()))]
    cards = Table([[p(label, 'MetricLabel') for label, _ in metrics], [p(value, 'Metric') for _, value in metrics]], colWidths=[usable / 4] * 4)
    cards.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F3F5')), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
    story += [cards, Spacer(1, 18), p('Principales alertas por frecuencia', 'Heading2')]
    counts = events.Alerta.value_counts()
    ranking = [['Tipo de alerta', 'Cantidad', 'Frecuencia relativa']]
    for alert, count in counts.items():
        ranking.append([p(alert), int(count), Bar(int(count), int(counts.max()))])
    if len(ranking) > 1:
        story.append(table(ranking, [usable - 345, 75, 270]))
    else:
        story.append(p('Sin alertas de las categorías seleccionadas. Esto no acredita ausencia de incidentes.', 'SmallNote'))
    story += [Spacer(1, 14), p('Unidades con exportación en este reporte', 'Heading2')]
    fleet = [['Placa', 'Alertas seleccionadas']]
    for plate, frame in exported.groupby('_placa'):
        fleet.append([p(frame['Placa/Patente'].iloc[0]), int(events._placa.eq(plate).sum())])
    story += [table(fleet, [usable - 160, 160]), Spacer(1, 12),
              p('Fuente: exportación manual Onway y padrón de unidades. Solo conducción y seguridad; incluye baches como seguridad vial. Los conteos no califican al conductor. Las unidades sin archivo no se consideran libres de incidentes.', 'SmallNote')]
    if not events.empty:
        story += [PageBreak(), p('Detalle de alertas', 'Company'), p(title + ' | ' + day, 'SmallNote'), Spacer(1, 12)]
        headers = ['Fecha', 'Hora', 'Placa', 'Alerta', 'Velocidad km/h', 'Zona']
        detail = [headers]
        for _, row in events.iterrows():
            speed = row.get('Velocidad (Km/h)', '')
            if isinstance(speed, (int, float)):
                speed = f'{speed:.1f}'
            detail.append([p(row['Fecha'].strftime('%d/%m/%Y')), p(row['Hora'].strftime('%H:%M:%S')),
                           p(row['Placa/Patente']), p(row['Alerta']), p(speed), p(row.get('Zona', ''))])
        story += [table(detail, [70, 60, 70, 220, 95, usable - 515]), Spacer(1, 10),
                  p('El Excel local conserva el detalle completo de campos útiles, incluidas coordenadas y datos adicionales disponibles.', 'SmallNote')]
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#526576'))
        canvas.drawString(32, 18, 'O.S. Logistics Perú S.A.C. | Reporte GPS por empresa')
        canvas.drawRightString(width - 32, 18, f'{day} | Página {doc.page}')
        canvas.restoreState()
    SimpleDocTemplate(str(path), pagesize=(width, height), rightMargin=32, leftMargin=32, topMargin=28,
                      bottomMargin=34, title=f'{title} - Alertas GPS {day}', author='O.S. Logistics Perú S.A.C.').build(story, onFirstPage=footer, onLaterPages=footer)
