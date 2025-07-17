#!/usr/bin/env python3
# -*- coding: utf‑8 -*-

"""
Скрипт:  visualise_cameras.py
Зависимости: pdfplumber, folium, pandas (для удобства).
Установка:  pip install pdfplumber folium pandas
Запуск:     python visualise_cameras.py document.pdf
"""

import sys
import re
from pathlib import Path
import pdfplumber
import pandas as pd
import folium


def extract_coords(pdf_path: Path) -> pd.DataFrame:
    """Извлекает все пары широта‑долгота из PDF и возвращает DataFrame."""
    pattern = re.compile(r'([3-4][0-9][.,][0-9]+)[ \t\r\n]+([6][0-9][.,][0-9]+)')
    coords = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for raw_lat, raw_lon in pattern.findall(text):
                # приводим «41,555 616» или «41 555616» к «41.555616»
                lat = float(raw_lat.replace(" ", "").replace(",", "."))
                lon = float(raw_lon.replace(" ", "").replace(",", "."))

                # фильтруем по реалистичным для Узбекистана диапазонам
                if 38 <= lat <= 43 and 60 <= lon <= 74:
                    coords.add((round(lat, 6), round(lon, 6)))

    df = pd.DataFrame(coords, columns=["lat", "lon"]).sort_values(["lat", "lon"])
    return df


def extract_coords_by_camera_numbers(pdf_path: Path) -> pd.DataFrame:
    """Извлекает координаты из строк с номерами камер, используя более гибкий подход."""
    coords = set()
    
    # Простой паттерн для поиска координат в конце строки
    pattern = re.compile(r'([3-4][0-9][.,][0-9]+)[ ]+([6][0-9][.,][0-9]+)')

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            for line in lines:
                # Ищем строки, начинающиеся с 4-значного номера (камера)
                if re.match(r'^[0-9]{4}', line.strip()):
                    # Ищем координаты в строке
                    matches = pattern.findall(line)
                    for raw_lat, raw_lon in matches:
                        try:
                            lat = float(raw_lat.replace(",", "."))
                            lon = float(raw_lon.replace(",", "."))
                            
                            # Фильтруем по реалистичным диапазонам
                            if 38 <= lat <= 43 and 60 <= lon <= 74:
                                coords.add((round(lat, 6), round(lon, 6)))
                        except ValueError:
                            continue

    df = pd.DataFrame(coords, columns=["lat", "lon"]).sort_values(["lat", "lon"])
    return df


def extract_coords_combined(pdf_path: Path) -> pd.DataFrame:
    """Комбинированный метод извлечения координат - использует оба подхода для максимального покрытия."""
    coords = set()
    
    # Метод 1: Извлечение по номерам камер
    pattern1 = re.compile(r'([3-4][0-9][.,][0-9]+)[ ]+([6][0-9][.,][0-9]+)')
    
    # Метод 2: Универсальное извлечение
    pattern2 = re.compile(r'([3-4][0-9][.,][0-9]+)[ \t\r\n]+([6][0-9][.,][0-9]+)')

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            # Метод 1: По строкам с номерами камер
            lines = text.split('\n')
            for line in lines:
                if re.match(r'^[0-9]{4}', line.strip()):
                    matches = pattern1.findall(line)
                    for raw_lat, raw_lon in matches:
                        try:
                            lat = float(raw_lat.replace(",", "."))
                            lon = float(raw_lon.replace(",", "."))
                            if 38 <= lat <= 43 and 60 <= lon <= 74:
                                coords.add((round(lat, 6), round(lon, 6)))
                        except ValueError:
                            continue
            
            # Метод 2: Универсальное извлечение из всего текста
            matches = pattern2.findall(text)
            for raw_lat, raw_lon in matches:
                try:
                    lat = float(raw_lat.replace(",", "."))
                    lon = float(raw_lon.replace(",", "."))
                    if 38 <= lat <= 43 and 60 <= lon <= 74:
                        coords.add((round(lat, 6), round(lon, 6)))
                except ValueError:
                    continue

    df = pd.DataFrame(coords, columns=["lat", "lon"]).sort_values(["lat", "lon"])
    return df


def make_map(df: pd.DataFrame, outfile: Path = Path("cameras_map.html")) -> None:
    """Создаёт интерактивную карту Folium с маркерами камер."""
    center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=8, tiles="OpenStreetMap")

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=4,
            weight=1,
            fill=True,
            fill_opacity=0.8,
        ).add_to(m)

    m.save(outfile)
    print(f"🗺  Карта сохранена в {outfile.absolute()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Укажи путь к PDF:  python visualise_cameras.py document.pdf")

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        sys.exit(f"Файл {pdf_path} не найден")

    # Используем новый метод извлечения по номерам камер
    df_coords = extract_coords_combined(pdf_path)
    print(f"Найдено координат: {len(df_coords)}")
    make_map(df_coords) 