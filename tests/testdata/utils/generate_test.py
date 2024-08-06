import csv

header = ['column1', 'column2', 'column3']
data = [
    ['value1', 'value2', 'value3'],
    ['value4', 'value5', 'value6'],
    ['value7', 'value8', 'value9']
]

with open('tests/testdata/test.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(data)

    