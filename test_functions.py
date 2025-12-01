import pytest
import performance_report
import csv
import sys
import os
from io import StringIO
from unittest.mock import mock_open, patch
from performance_report import read_and_combine_csv_files

class TestReadAndCombineCSVFiles:
    
    def test_single_valid_csv_file(self, mocker):
        """Тест с одним корректным CSV файлом"""
        csv_content = """position,performance,task_id
Developer,85,1
QA,78,2
Developer,90,3"""
        
     
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=100)
        mocker.patch('os.path.basename', return_value='test.csv')
       
        mock_file = mocker.mock_open(read_data=csv_content)
        mocker.patch('builtins.open', mock_file)
  
        captured_output = []
        mocker.patch('builtins.print', 
                    side_effect=lambda *args: captured_output.append(' '.join(str(a) for a in args)))
        
 
        result_rows, result_headers = read_and_combine_csv_files(['test.csv'])
        
    
        assert result_headers == ['position', 'performance', 'task_id']
        assert len(result_rows) == 3
        assert result_rows[0]['position'] == 'Developer'
        assert result_rows[0]['performance'] == '85'
        assert result_rows[2]['position'] == 'Developer'
        assert result_rows[2]['performance'] == '90'
        
        # Проверяем вывод
        assert any('заголовки' in line for line in captured_output)
    
    def test_multiple_csv_files(self, mocker):
        """Тест с несколькими CSV файлами одинаковой структуры"""
        # Тестовые данные
        csv1 = """position,performance,task_id
Dev,85,1
QA,78,2"""
        
        csv2 = """position,performance,task_id
PM,92,3
Dev,88,4"""
        
        mock_open_side_effect = [
            mocker.mock_open(read_data=csv1).return_value,
            mocker.mock_open(read_data=csv2).return_value
        ]
        
        mocker.patch('builtins.open', side_effect=mock_open_side_effect)
        mocker.patch('os.path.exists', side_effect=[True, True])
        mocker.patch('os.path.getsize', side_effect=[100, 100])
        mocker.patch('os.path.basename', side_effect=['file1.csv', 'file2.csv'])
        
        result_rows, _ = read_and_combine_csv_files(['file1.csv', 'file2.csv'])
        
        assert len(result_rows) == 4
        positions = [row['position'] for row in result_rows]
        assert 'Dev' in positions
        assert 'QA' in positions
        assert 'PM' in positions
    
    def test_csv_with_semicolon_delimiter(self, mocker):
        csv_content = """position;performance;task_id
Developer;85;1
QA;78;2"""
        
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=100)
        mocker.patch('builtins.open', mocker.mock_open(read_data=csv_content))
        
        result_rows, result_headers = read_and_combine_csv_files(['test.csv'])
        
        assert result_headers == ['position', 'performance', 'task_id']
        assert len(result_rows) == 2
        assert result_rows[0]['position'] == 'Developer'
    
    def test_files_with_different_headers_but_required_columns(self, mocker, capsys):
        """Тест с файлами с разными заголовками, но имеющими нужные колонки"""
        csv1 = """position,performance,task_id,department
Dev,85,1,IT
QA,78,2,QA"""
        
        csv2 = """position,performance,project,date
PM,92,ProjectA,2024-01-01
Dev,88,ProjectB,2024-01-02"""
        
        # Мокаем чтение файлов
        mock_open_side_effect = [
            mocker.mock_open(read_data=csv1).return_value,
            mocker.mock_open(read_data=csv2).return_value
        ]
        
        mocker.patch('builtins.open', side_effect=mock_open_side_effect)
        mocker.patch('os.path.exists', side_effect=[True, True])
        mocker.patch('os.path.getsize', side_effect=[100, 100])
        mocker.patch('os.path.basename', side_effect=['file1.csv', 'file2.csv'])
        
        result_rows, _ = read_and_combine_csv_files(['file1.csv', 'file2.csv'])
        
        assert len(result_rows) == 4
        
        captured = capsys.readouterr()
        assert 'разные заголовки' in captured.out
    
    
    def test_file_not_found(self, mocker):
        """Тест с несуществующим файлом"""
        mocker.patch('os.path.exists', return_value=False)
        
        # Проверяем, что функция завершается с ошибкой
        with pytest.raises(SystemExit) as exc_info:
            read_and_combine_csv_files(['nonexistent.csv'])
        
        assert exc_info.value.code == 1
    
    def test_empty_file(self, mocker, capsys):
        """Тест с пустым файлом (должен быть пропущен)"""
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=0)
        
        # Для этого теста нам нужен второй валидный файл
        csv_content = """position,performance,task_id
Dev,85,1"""
        
        mock_open_side_effect = [
            mocker.mock_open(read_data='').return_value,  # Пустой файл
            mocker.mock_open(read_data=csv_content).return_value  # Валидный файл
        ]
        
        mocker.patch('builtins.open', side_effect=mock_open_side_effect)
        mocker.patch('os.path.getsize', side_effect=[0, 100])
        mocker.patch('os.path.basename', side_effect=['empty.csv', 'valid.csv'])
        
        # Вызываем функцию
        result_rows, _ = read_and_combine_csv_files(['empty.csv', 'valid.csv'])
        
        # Проверяем, что пустой файл пропущен
        assert len(result_rows) == 1
        
        # Проверяем вывод
        captured = capsys.readouterr()
        assert 'пуст' in captured.out
    
    def test_all_files_empty(self, mocker):
        """Тест, когда все файлы пустые"""
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=0)
        mocker.patch('builtins.open', mocker.mock_open(read_data=''))
        
        # Функция должна завершиться с ошибкой
        with pytest.raises(SystemExit) as exc_info:
            read_and_combine_csv_files(['empty1.csv', 'empty2.csv'])
        
        assert exc_info.value.code == 1
    
    def test_csv_parsing_error(self, mocker):
        """Тест с некорректным CSV"""
        # Битый CSV - нет закрывающей кавычки
        csv_content = """position,performance,task_id
"Developer,85,1
QA,78,2"""
        
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=100)
        mock_file = mocker.mock_open(read_data=csv_content)
        mocker.patch('builtins.open', mock_file)
        
        # Функция должна завершиться с ошибкой
        with pytest.raises(SystemExit) as exc_info:
            read_and_combine_csv_files(['broken.csv'])
        
        assert exc_info.value.code == 1
    
    def test_file_without_required_columns(self, mocker):
        """Тест с файлом без обязательных колонок"""
        # Нет колонки 'performance'
        csv_content = """position,task_id,salary
Dev,1,100000
QA,2,80000"""
        
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=100)
        mocker.patch('builtins.open', mocker.mock_open(read_data=csv_content))
        
        # Функция должна завершиться
        with pytest.raises(SystemExit) as exc_info:
            read_and_combine_csv_files(['no_performance.csv'])
        
        assert exc_info.value.code == 1
    
    # ========== ГРАНИЧНЫЕ ТЕСТЫ ==========
    
    def test_large_file_chunk_reading(self, mocker):
        """Тест, что функция читает только первые 1024 байта для определения разделителя"""
        # Создаем большой заголовок (>1024 байт)
        long_header = 'position,' + 'x' * 2000 + ',performance,task_id\n'
        csv_content = long_header + "Developer,85,1\nQA,78,2"
        
        # Мокаем read(1024) чтобы он возвращал только часть данных
        mock_file = mocker.MagicMock()
        mock_file.read.side_effect = [
            long_header[:1024],  # Первое чтение для определения разделителя
            csv_content  # Второе чтение (после seek(0))
        ]
        mock_file.__enter__.return_value = mock_file
        
        mocker.patch('builtins.open', return_value=mock_file)
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=5000)
        
        # Вызываем функцию
        result_rows, result_headers = read_and_combine_csv_files(['large.csv'])
        
        # Проверяем
        assert len(result_rows) == 2
        assert 'position' in result_headers
    
    def test_unicode_characters(self, mocker):
        """Тест с Unicode символами в данных"""
        csv_content = """position,performance,task_id
Разработчик,85,1
QA-специалист,78,2
😊Смайл,90,3"""
        
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=100)
        mocker.patch('builtins.open', 
                    mocker.mock_open(read_data=csv_content.encode('utf-8').decode('utf-8')))
        
        result_rows, _ = read_and_combine_csv_files(['unicode.csv'])
        
        assert len(result_rows) == 3
        assert result_rows[0]['position'] == 'Разработчик'
        assert result_rows[2]['position'] == '😊Смайл'
    
    def test_mixed_delimiters_across_files(self, mocker):
        """Тест с разными разделителями в разных файлах"""
        csv1 = """position,performance,task_id
Dev,85,1
QA,78,2"""
        
        csv2 = """position;performance;task_id
PM;92;3
Dev;88;4"""
        
        mock_open_side_effect = [
            mocker.mock_open(read_data=csv1).return_value,
            mocker.mock_open(read_data=csv2).return_value
        ]
        
        mocker.patch('builtins.open', side_effect=mock_open_side_effect)
        mocker.patch('os.path.exists', side_effect=[True, True])
        mocker.patch('os.path.getsize', side_effect=[100, 100])
        
        result_rows, _ = read_and_combine_csv_files(['comma.csv', 'semicolon.csv'])
        
        assert len(result_rows) == 4
    
    def test_performance_with_many_files(self, mocker):
        """Тест производительности с большим количеством файлов"""
        file_count = 50
        file_paths = [f'file{i}.csv' for i in range(file_count)]
        
        # Мокаем все файлы с одинаковым содержанием
        csv_content = """position,performance,task_id
Dev,85,1"""
        
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('os.path.getsize', return_value=100)
        mocker.patch('builtins.open', mocker.mock_open(read_data=csv_content))
        mocker.patch('os.path.basename', side_effect=lambda x: x)
        
        # Вызываем функцию
        result_rows, _ = read_and_combine_csv_files(file_paths)
        
        assert len(result_rows) == file_count