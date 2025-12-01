#!/usr/bin/env python3
import csv
import argparse
import sys
import os
from collections import defaultdict

def read_and_combine_csv_files(file_paths):
    all_rows = []
    headers = None
    total_files = len(file_paths)
    
    for i, file_path in enumerate(file_paths, 1):
        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл '{file_path}' не найден")
            
            # Проверяем размер файла
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                print(f"    Файл {i}/{total_files}: '{file_path}' пуст, пропускаем")
                continue
            
            with open(file_path, 'r', encoding='utf-8') as file:
                
                sample = file.read(1024)
                file.seek(0)
                
                delimiter = ',' if ',' in sample else ';'
                reader = csv.DictReader(file, delimiter=delimiter)
                
                
                if headers is None:
                    headers = reader.fieldnames
                    print(f"   Файл {i}/{total_files}: '{file_path}' - заголовки: {headers}")
                else:
                    
                    current_headers = set(reader.fieldnames or [])
                    expected_headers = set(headers)
                    
                    if current_headers != expected_headers:
                        
                        required = {'position', 'performance'}
                        common_required = required.intersection(current_headers)
                        
                        if len(common_required) < 2:
                            print(f"  Файл {i}/{total_files}: '{file_path}' - разные заголовки, но есть нужные колонки")
                        else:
                            print(f"  Файл {i}/{total_files}: '{file_path}' - разные заголовки")
                
                # Читаем и подсчитываем строки
                file_rows = list(reader)
                all_rows.extend(file_rows)
                
                print(f"     Добавлено {len(file_rows)} строк из файла '{os.path.basename(file_path)}'")
                
        except FileNotFoundError as e:
            print(f"   Ошибка: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"   Ошибка чтения файла '{file_path}': {e}", file=sys.stderr)
            sys.exit(1)
    
    if not all_rows:
        print("Ошибка: Во всех файлах нет данных", file=sys.stderr)
        sys.exit(1)
    
    print(f" Объединено всего: {len(all_rows)} строк из {total_files} файлов\n")
    return all_rows, headers

def calculate_performance_report(data):    
    performance_stats = defaultdict(lambda: {'sum': 0.0, 'count': 0})
    skipped_rows = 0
    
    for i, row in enumerate(data, 1):
        position = row.get('position')
        performance_str = row.get('performance')
        
        if position and performance_str:
            try:
                performance = float(performance_str)
                performance_stats[position]['sum'] += performance
                performance_stats[position]['count'] += 1
            except (ValueError, TypeError):
                skipped_rows += 1
        else:
            skipped_rows += 1
    

    report = []
    for position, stats in performance_stats.items():
        if stats['count'] > 0:
            average = stats['sum'] / stats['count']
            report.append({
                'position': position.strip(), 
                'average_performance': round(average, 2),
                'count': stats['count']  # Для информации
            })
    
    if skipped_rows > 0:
        print(f" Пропущено {skipped_rows} строк с некорректными данными")
    return report

def write_report(report_data, output_file):
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['position', 'average_performance']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in report_data:
                writer.writerow({
                    'position': row['position'],
                    'average_performance': row['average_performance']
                })
        
        return True, len(report_data)
    except Exception as e:
        print(f"Ошибка записи отчета: {e}", file=sys.stderr)
        return False, 0

def main():
    parser = argparse.ArgumentParser(
        description='Генерация отчета performance по объединенным данным из CSV файлов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  #(prog)s --files data1.csv --report output.csv
  #%(prog)s --files data1.csv data2.csv data3.csv --report output.csv
  #%(prog)s --files *.csv --report performance_report.csv
        """
    )
    
    parser.add_argument(
        '--files',
        nargs='+',
        required=True,
        help='Один или несколько CSV файлов для обработки'
    )
    
    parser.add_argument(
        '--report',
        required=True,
        help='Имя выходного CSV файла с отчетом'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Подробный вывод информации'
    )
    
    args = parser.parse_args()
    
  
    

    combined_data, headers = read_and_combine_csv_files(args.files)

    if headers:
        required_columns = {'position', 'performance'}
        missing_columns = required_columns - set(headers)
        if missing_columns:
            print(f"Ошибка: В файлах отсутствуют колонки: {missing_columns}")
            print(f"   Найдены колонки: {headers}")
            sys.exit(1)
    
 
    report_data = calculate_performance_report(combined_data)
    
    if not report_data:
        print("Нет данных для формирования отчета")
        sys.exit(1)
    
 
    report_data.sort(key=lambda x: x['average_performance'], reverse=True)
    

    success, positions_count = write_report(report_data, args.report)
    
    if success:
        print(f"\nОтчет успешно сохранен в '{args.report}'")
        print(f"📊 Позиций в отчете: {positions_count}")
        print(f"📁 Исходных строк: {len(combined_data)}")
        
        print("\n🏆 ТОП-5 ПО ЭФФЕКТИВНОСТИ:")
        print("-" * 35)
        for i, item in enumerate(report_data[:5], 1):
            print(f"{i:2}. {item['position']:20} {item['average_performance']:>8.2f} (на основе {item['count']} записей)")
        
        # Показываем содержимое файла
        if args.verbose:
            print(f"\n Содержимое файла '{args.report}':")
            print("-" * 40)
            with open(args.report, 'r') as f:
                print(f.read())
    
    print("\n" + "=" * 60)
    print(" ВЫПОЛНЕНО")
    print("=" * 60)

if __name__ == "__main__":
    main()