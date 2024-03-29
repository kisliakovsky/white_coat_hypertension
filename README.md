# Report parser
Программа для автоматизированного разбора отчётов об измерении артериального давления

## Загрузка
Архив с программой можно скачать [здесь](https://niuitmo-my.sharepoint.com/personal/kisliakovskiii_niuitmo_ru/_layouts/15/guestaccess.aspx?docid=149429cd3888b4d8489cf1d1c7be43c31&authkey=AX_a8oJklIbgA6oeU-ESySA)

## Алгоритм установки
1. Распаковать архив с программой  
2. В папке с программой есть папка с названием *raw*. В данную папку необходимо поместить отчёты, которые необходимо обработать. (По умолчанию в папке находится пример отчета *example.pdf*)  
3. После этого необходимо найти в папке с программой файл main.exe и запустить его двойным кликом мыши. После запуска на экран будет выводится информация о ходе работы программы. Подробнее см. **Сообщения о работе программы**  
4. В папке с программой появится папка с названием *output*. В данной папке будет находится файл с результатами работы программы в формате csv. После каждого запуска программы будет создан новый файл с результатами.

## Сообщения о работе программы
1) Сообщение об успехе:
    ```bash
    Report example.pdf has been parsed (1/1)
	```
	Или о неудаче:
	```bash
	Report example.pdf has NOT been parsed (1/1)
	```
	Здесь:  
		*example.pdf* - название файла с отчётом  
		*(1/1)* - (номер отчёта/количество отчётов)
2) Сообщение о проблеме с данными:
    ```bash
    Please enter the values of periodic measurements of the blood pressure (systolic and diastolic) of the column #1 manually (Report example_2.pdf)
	```
	Здесь:  
		*example_2.pdf* - название файла с отчётом  
		Подробнее см. **Примечание**
3) Итог работы:
    ```bash
    The number of processed reports (success/fail/total): 1/0/1
	```
	Здесь:  
		*1/0/1* - количество разобранных отчётов/количество неразобранных отчётов/всего отчётов
4) Расположение файла с результатами:
    ```bash
    The output file was saved as E:\Users\ilya\Desktop\report_parser_1.0.0\output\output_4.csv
	```
	Здесь:  
		*E:\Users\ilya\Desktop\report_parser_1.0.0\output\output_4.csv* - путь к файлу

### Примечание
Сообщение
```bash
Please enter the values of periodic measurements of the blood pressure (systolic and diastolic) of the column #1 manually (Report example_2.pdf)
```
означает следующее:   
Возникли проблемы с разбором значений систолического и диастолического давления, которые находятся в столбцах в нижней части отчёта.  
    Здесь:   
		*column #1* - колонка с указанием её порядкового номера
		*example_2.pdf* - название файла с отчётом
		
## Сообщения о релизах
### 1.1.1
##### Features
- Добавлены СКО для значений периодических измерений систолического и диастолического давления  
##### Bugs
- Исправлено распределение Awake/Asleep периодов 
##### Другое
- Изменено расположение папок *raw* и *output*
### 1.1.2
##### Bugs
- Исправлена внутренняя ошибка, связанная с расчётом СКО  
### 2.0.0
TBD