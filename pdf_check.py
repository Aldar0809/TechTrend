from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
import os


def generate_invoice_pdf(order):
    filename = f'invoice.pdf'

    try:
        os.remove(filename)
    except Exception:
        pass

    # Регистрация кириллического шрифта
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))

    # Создаем PDF-документ
    doc = SimpleDocTemplate(filename)
    elements = []

    # Создаем стиль для абзацев с увеличенным размером текста
    style = getSampleStyleSheet()["BodyText"]
    style.fontName = 'Arial'
    style.fontSize = 14  # Увеличенный размер текста

    # Добавляем поздравление с покупкой
    elements.append(Paragraph(f'Поздравляем с покупкой! Заказ №{order.id}', style))
    elements.append(Paragraph(f'Клиент: {order.customer_name}', style))
    elements.append(Paragraph(f'Дата заказа: {order.created_at}', style))
    elements.append(Paragraph('', style))  # Пустой абзац для разделения

    # Добавляем таблицу с товарами и их ценами
    data = [['Товар', 'Цена']]
    for item in order.order_items:
        data.append([item.product.name, str(item.product.price) + ' ₽'])
    table = Table(data)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                               ]))
    elements.append(table)

    # Добавляем итоговую стоимость
    total_price = order.total_amount
    elements.append(Paragraph(f'Итоговая стоимость: {total_price} ₽', style))

    # Сохраняем документ
    doc.build(elements)

    return filename
