-- Создание таблиц для Telegram-бота бронирования аудиторий КЦ «Дар»

-- Таблица пользователей
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица аудиторий
CREATE TABLE rooms (
    id BIGSERIAL PRIMARY KEY,
    room_number VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255),
    floor INTEGER NOT NULL CHECK (floor IN (2, 3, 4)),
    area INTEGER NOT NULL, -- площадь в кв.м
    chairs INTEGER DEFAULT 0,
    tables INTEGER DEFAULT 0,
    monitor BOOLEAN DEFAULT FALSE,
    flipchart BOOLEAN DEFAULT FALSE,
    air_conditioning BOOLEAN DEFAULT FALSE,
    photo_url TEXT,
    comments TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица бронирований
CREATE TABLE bookings (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    room_id BIGINT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    purpose TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индексов для оптимизации запросов
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_rooms_floor ON rooms(floor);
CREATE INDEX idx_rooms_room_number ON rooms(room_number);
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_room_id ON bookings(room_id);
CREATE INDEX idx_bookings_start_time ON bookings(start_time);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_room_date ON bookings(room_id, start_time);

-- Создание представления для удобного просмотра бронирований с информацией об аудиториях
CREATE VIEW booking_details AS
SELECT 
    b.id,
    b.full_name,
    b.purpose,
    b.start_time,
    b.end_time,
    b.status,
    b.created_at,
    r.room_number,
    r.name as room_name,
    r.floor,
    u.telegram_id,
    u.username
FROM bookings b
JOIN rooms r ON b.room_id = r.id
JOIN users u ON b.user_id = u.id;

-- Создание представления для проверки доступности аудиторий
CREATE VIEW room_availability AS
SELECT 
    r.id,
    r.room_number,
    r.name,
    r.floor,
    r.area,
    r.chairs,
    r.tables,
    r.monitor,
    r.flipchart,
    r.air_conditioning,
    r.comments,
    COUNT(b.id) as active_bookings_count
FROM rooms r
LEFT JOIN bookings b ON r.id = b.room_id 
    AND b.status = 'confirmed' 
    AND b.start_time >= NOW()
GROUP BY r.id, r.room_number, r.name, r.floor, r.area, r.chairs, r.tables, r.monitor, r.flipchart, r.air_conditioning, r.comments;

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция для проверки доступности аудитории
CREATE OR REPLACE FUNCTION check_room_availability(
    p_room_id BIGINT,
    p_start_time TIMESTAMP WITH TIME ZONE,
    p_end_time TIMESTAMP WITH TIME ZONE
)
RETURNS BOOLEAN AS $$
DECLARE
    conflicting_bookings INTEGER;
BEGIN
    SELECT COUNT(*) INTO conflicting_bookings
    FROM bookings
    WHERE room_id = p_room_id
      AND status = 'confirmed'
      AND (
          (start_time < p_end_time AND end_time > p_start_time)
          OR (start_time = p_start_time)
          OR (end_time = p_end_time)
      );
    
    RETURN conflicting_bookings = 0;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения занятости аудитории на определенную дату
CREATE OR REPLACE FUNCTION get_room_schedule(
    p_room_id BIGINT,
    p_date DATE
)
RETURNS TABLE(
    time_slot TIME,
    is_available BOOLEAN,
    booking_info TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH time_slots AS (
        SELECT generate_series(
            '08:00'::time, 
            '22:00'::time, 
            '00:30'::time
        )::time AS time_slot
    ),
    existing_bookings AS (
        SELECT 
            start_time::time as start_t,
            end_time::time as end_t,
            full_name,
            purpose
        FROM bookings
        WHERE room_id = p_room_id
          AND DATE(start_time) = p_date
          AND status = 'confirmed'
    )
    SELECT 
        ts.time_slot,
        CASE 
            WHEN eb.start_t IS NULL THEN TRUE
            ELSE FALSE
        END as is_available,
        CASE 
            WHEN eb.start_t IS NULL THEN ''
            ELSE eb.full_name || ' - ' || eb.purpose
        END as booking_info
    FROM time_slots ts
    LEFT JOIN existing_bookings eb ON ts.time_slot >= eb.start_t AND ts.time_slot < eb.end_t
    ORDER BY ts.time_slot;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения статистики по аудиториям
CREATE OR REPLACE FUNCTION get_room_statistics(
    p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    room_id BIGINT,
    room_number VARCHAR,
    room_name VARCHAR,
    total_bookings BIGINT,
    total_hours NUMERIC,
    utilization_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.room_number,
        COALESCE(r.name, 'Аудитория ' || r.room_number) as room_name,
        COUNT(b.id) as total_bookings,
        COALESCE(SUM(EXTRACT(EPOCH FROM (b.end_time - b.start_time)) / 3600), 0)::NUMERIC(10,2) as total_hours,
        CASE 
            WHEN r.area > 0 THEN 
                (COALESCE(SUM(EXTRACT(EPOCH FROM (b.end_time - b.start_time)) / 3600), 0) / 
                (EXTRACT(EPOCH FROM (p_end_date - p_start_date + INTERVAL '1 day')) / 3600 * 14)) * 100
            ELSE 0
        END::NUMERIC(5,2) as utilization_rate
    FROM rooms r
    LEFT JOIN bookings b ON r.id = b.room_id 
        AND b.status = 'confirmed'
        AND DATE(b.start_time) BETWEEN p_start_date AND p_end_date
    WHERE r.is_active = TRUE
    GROUP BY r.id, r.room_number, r.name, r.area
    ORDER BY total_bookings DESC;
END;
$$ LANGUAGE plpgsql;

-- Вставка тестовых данных для аудиторий
INSERT INTO rooms (room_number, name, floor, area, chairs, tables, monitor, flipchart, air_conditioning, comments) VALUES
('201', 'Конференц-зал', 2, 45, 20, 5, TRUE, TRUE, TRUE, 'Для лекций и презентаций'),
('202', 'Переговорная', 2, 25, 8, 2, TRUE, FALSE, TRUE, 'Для совещаний'),
('203', 'Тренинг-зал', 2, 35, 15, 3, FALSE, TRUE, TRUE, 'Для мастер-классов'),
('301', 'Аудитория', 3, 30, 12, 4, TRUE, TRUE, FALSE, 'Универсальная'),
('302', 'Студия', 3, 20, 6, 2, TRUE, FALSE, TRUE, 'Для творческих занятий'),
('401', 'Лекторий', 4, 50, 25, 6, TRUE, TRUE, TRUE, 'Для больших мероприятий'),
('402', 'Класс', 4, 28, 14, 3, FALSE, TRUE, TRUE, 'Для групповых занятий');

-- Создание RLS (Row Level Security) политик
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

-- Политика для пользователей (каждый может видеть только себя)
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (telegram_id = current_setting('app.current_user_id', true)::BIGINT);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (telegram_id = current_setting('app.current_user_id', true)::BIGINT);

-- Политика для аудиторий (все могут просматривать)
CREATE POLICY "Anyone can view rooms" ON rooms
    FOR SELECT USING (is_active = TRUE);

-- Политика для бронирований
CREATE POLICY "Users can view own bookings" ON bookings
    FOR SELECT USING (user_id = (SELECT id FROM users WHERE telegram_id = current_setting('app.current_user_id', true)::BIGINT));

CREATE POLICY "Users can create own bookings" ON bookings
    FOR INSERT WITH CHECK (user_id = (SELECT id FROM users WHERE telegram_id = current_setting('app.current_user_id', true)::BIGINT));

CREATE POLICY "Admins can view all bookings" ON bookings
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE telegram_id = current_setting('app.current_user_id', true)::BIGINT 
            AND is_admin = TRUE
        )
    );

CREATE POLICY "Admins can manage all bookings" ON bookings
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE telegram_id = current_setting('app.current_user_id', true)::BIGINT 
            AND is_admin = TRUE
        )
    );

-- Функция для установки текущего пользователя
CREATE OR REPLACE FUNCTION set_current_user(telegram_id BIGINT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', telegram_id::TEXT, FALSE);
END;
$$ LANGUAGE plpgsql;