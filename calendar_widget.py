"""
Календарь для выбора даты бронирования
Аналог telegram-bot-calendar-lite для Python
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, date, timedelta
from typing import List, Optional, Callable
import calendar as cal

class TelegramCalendar:
    """Календарь для выбора даты в Telegram боте"""
    
    def __init__(self):
        self.month_names = [
            'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
            'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'
        ]
        self.week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        self.select_icon = '✅'
        self.prev_icon = '⬅️'
        self.next_icon = '➡️'
        self.close_icon = '❌'
        self.today_icon = '📅'
        self.locked_dates = []  # Список заблокированных дат
        
    def set_month_names(self, names: List[str]):
        """Установить названия месяцев"""
        if len(names) == 12:
            self.month_names = names
    
    def set_week_days(self, days: List[str]):
        """Установить названия дней недели"""
        if len(days) == 7:
            self.week_days = days
    
    def set_select_icon(self, icon: str):
        """Установить иконку для выбранной даты"""
        self.select_icon = icon
    
    def set_prev_icon(self, icon: str):
        """Установить иконку для кнопки 'Предыдущий месяц'"""
        self.prev_icon = icon
    
    def set_next_icon(self, icon: str):
        """Установить иконку для кнопки 'Следующий месяц'"""
        self.next_icon = icon
    
    def set_close_icon(self, icon: str):
        """Установить иконку для заблокированных дат"""
        self.close_icon = icon
    
    def set_today_icon(self, icon: str):
        """Установить иконку для сегодняшней даты"""
        self.today_icon = icon
    
    def set_locked_dates(self, dates: List[date]):
        """Установить заблокированные даты"""
        self.locked_dates = dates
    
    def create_calendar(self, year: int, month: int, selected_date: Optional[date] = None) -> InlineKeyboardMarkup:
        """Создать календарь для указанного месяца и года"""
        today = date.today()
        
        # Заголовок календаря
        month_name = self.month_names[month - 1]
        header = f"{month_name} {year}"
        
        # Создаем клавиатуру
        keyboard = []
        
        # Кнопки навигации
        nav_row = []
        if year > today.year or (year == today.year and month > today.month):
            nav_row.append(InlineKeyboardButton(
                self.prev_icon, 
                callback_data=f"cal_prev_{year}_{month}"
            ))
        else:
            nav_row.append(InlineKeyboardButton(" ", callback_data="cal_none"))
            
        nav_row.append(InlineKeyboardButton(header, callback_data="cal_none"))
        
        if year < today.year + 1 or (year == today.year + 1 and month < 12):
            nav_row.append(InlineKeyboardButton(
                self.next_icon, 
                callback_data=f"cal_next_{year}_{month}"
            ))
        else:
            nav_row.append(InlineKeyboardButton(" ", callback_data="cal_none"))
            
        keyboard.append(nav_row)
        
        # Дни недели
        week_row = []
        for day in self.week_days:
            week_row.append(InlineKeyboardButton(day, callback_data="cal_none"))
        keyboard.append(week_row)
        
        # Дни месяца
        month_calendar = cal.monthcalendar(year, month)
        
        for week in month_calendar:
            week_row = []
            for day in week:
                if day == 0:
                    week_row.append(InlineKeyboardButton(" ", callback_data="cal_none"))
                else:
                    current_date = date(year, month, day)
                    
                    # Проверяем, можно ли выбрать эту дату
                    if current_date < today:
                        # Прошедшая дата
                        week_row.append(InlineKeyboardButton(
                            f"{self.close_icon}{day}", 
                            callback_data="cal_none"
                        ))
                    elif current_date in self.locked_dates:
                        # Заблокированная дата
                        week_row.append(InlineKeyboardButton(
                            f"{self.close_icon}{day}", 
                            callback_data="cal_none"
                        ))
                    elif current_date == today:
                        # Сегодняшняя дата
                        week_row.append(InlineKeyboardButton(
                            f"{self.today_icon}{day}", 
                            callback_data=f"cal_select_{year}_{month}_{day}"
                        ))
                    elif current_date == selected_date:
                        # Выбранная дата
                        week_row.append(InlineKeyboardButton(
                            f"{self.select_icon}{day}", 
                            callback_data=f"cal_select_{year}_{month}_{day}"
                        ))
                    else:
                        # Обычная дата
                        week_row.append(InlineKeyboardButton(
                            str(day), 
                            callback_data=f"cal_select_{year}_{month}_{day}"
                        ))
            keyboard.append(week_row)
        
        # Дополнительные кнопки
        extra_row = []
        extra_row.append(InlineKeyboardButton("Отмена", callback_data="cal_cancel"))
        keyboard.append(extra_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_calendar_for_booking(self, start_date: Optional[date] = None) -> InlineKeyboardMarkup:
        """Создать календарь для бронирования с учетом ограничений"""
        if start_date is None:
            start_date = date.today()
        
        # Ограничиваем выбор на 30 дней вперед
        max_date = start_date + timedelta(days=30)
        
        return self.create_calendar(start_date.year, start_date.month, start_date)
    
    def parse_callback_data(self, callback_data: str) -> dict:
        """Парсить callback_data календаря"""
        parts = callback_data.split('_')
        
        if len(parts) < 2:
            return {'action': 'none'}
        
        action = parts[1]
        
        if action == 'prev' and len(parts) >= 4:
            return {
                'action': 'prev',
                'year': int(parts[2]),
                'month': int(parts[3])
            }
        elif action == 'next' and len(parts) >= 4:
            return {
                'action': 'next',
                'year': int(parts[2]),
                'month': int(parts[3])
            }
        elif action == 'select' and len(parts) >= 5:
            return {
                'action': 'select',
                'year': int(parts[2]),
                'month': int(parts[3]),
                'day': int(parts[4])
            }
        elif action == 'manual':
            return {'action': 'manual'}
        elif action == 'cancel':
            return {'action': 'cancel'}
        else:
            return {'action': 'none'}
    
    def get_next_month(self, year: int, month: int) -> tuple:
        """Получить следующий месяц"""
        if month == 12:
            return year + 1, 1
        else:
            return year, month + 1
    
    def get_prev_month(self, year: int, month: int) -> tuple:
        """Получить предыдущий месяц"""
        if month == 1:
            return year - 1, 12
        else:
            return year, month - 1

# Глобальный экземпляр календаря
booking_calendar = TelegramCalendar()

# Настройка календаря для бронирования
booking_calendar.set_month_names([
    'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
    'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'
])
booking_calendar.set_week_days(['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'])
booking_calendar.set_select_icon('✅')
booking_calendar.set_prev_icon('⬅️')
booking_calendar.set_next_icon('➡️')
booking_calendar.set_close_icon('❌')
booking_calendar.set_today_icon('📅')
