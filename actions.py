from flask import Blueprint, request, render_template, redirect, url_for, flash, Response, jsonify
import re
import os
import xml.dom.minidom
import logging
import openpyxl
from datetime import datetime
import warnings
import pandas as pd
import configparser

# Cấu hình logging
logging.basicConfig(filename='logfile.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info('#################################################')
logging.info('#                 Start APP                     #')
logging.info('#################################################')

actions = Blueprint('actions', __name__, template_folder='templates')

parser = configparser.ConfigParser()
parser.read("./config/config.txt")

def count_leading_spaces(line):
    """Đếm số khoảng trắng ở đầu mỗi dòng."""
    count = 0
    for char in line:
        if char == ' ':
            count += 1
        elif char == '\t':
            count += 3
        else:
            break  # Ngừng khi gặp ký tự không phải khoảng trắng
    return count

@actions.route('/convert-project', methods=['POST', 'GET'])
def convert_project():
    return render_template('convert-project.html')


@actions.route('/convert-file', methods=['POST', 'GET'])
def convert_file():
    return render_template('convert-file.html')


@actions.route('/', methods=['POST', 'GET'])
def convert_code():
    return render_template('convert-code.html')


@actions.route('/start-convert-files', methods=['POST', 'GET'])
def start_convert_files():
    logging.info("#### [start-convert-files] ####")
    pattern_path = parser.get("config", "pattern_path")
    conversion_rules_file_path = pattern_path
    conversion_rules = read_conversion_rules_from_file_excel(conversion_rules_file_path)
    if request.method == 'POST':
        files = request.files.getlist('filepond')
        workbook = openpyxl.Workbook()
        for file in files:
            item_sheet = workbook.create_sheet(title=file.filename)
            data_result = process_code(file, conversion_rules)
        return render_template('convert-file.html')


@actions.route('/convert-editor', methods=['POST'])
def convert_editor():
    try:
        print("### [convert_editor] ###")
        today = datetime.now().strftime("%Y/%m/%d")
        from_code = request.form['code-editor-1']
        pattern_path = parser.get("config", "pattern_path")
        conversion_rules_file_path = pattern_path
        conversion_rules = read_conversion_rules_from_file_excel(conversion_rules_file_path)
        input_code = from_code
        output_code = input_code
        for pattern, regex, replace in conversion_rules:
            if (pattern != None) and (regex != None) and (replace != None) and (regex.strip() != "TBD"):
                match_pattern = re.findall(regex, pattern)
                if match_pattern:
                    output_code = re.sub(regex,
                                         r'//(STR) ' + today + r' K21-674 TOOL MOD\n' + '//' + pattern + r'\n' + replace + r'\n//(STR) ' + today + r' K21-674 TOOL MOD',
                                         output_code)
        print(f"Input: {input_code}")
        print(f"Output: {output_code}")

        to_code = output_code
        return jsonify({
            "from_code": from_code,
            "to_code": to_code
        })

    except Exception as e:
        # Xảy ra lỗi khi kết nối
        print('Error: ' + str(e))
        return jsonify({'status': 'error', 'message': str(e)})


def read_conversion_rules_from_file_excel(file_path):
    try:
        # Mở workbook
        workbook = openpyxl.load_workbook(file_path)
        # Chọn sheet cần đọc
        sheet = workbook['Pattern Summary']

        # Lấy tên cột từ hàng thứ 4 (index 4)
        column_names = [cell.value for cell in sheet[4]]

        # Đọc dữ liệu từ hàng thứ 5 trở đi
        data = sheet.iter_rows(min_row=5, values_only=True)
        df = pd.DataFrame(data, columns=column_names)

        # Lấy ra các giá trị từ cột "Pattern"
        pattern_list = df['Pattern'].tolist()

        # Lấy ra các giá trị từ cột "Regex"
        regex_list = df['Regex'].tolist()

        # Lấy ra các giá trị từ cột "Replace"
        replace_list_1 = df['Replace '].tolist()
        replace_list = []
        for item in replace_list_1:
            if item != None and item.strip() != "TBD":
                item = re.sub(r'\$', '\\\\', item)
            replace_list.append(item)
        return list(zip(pattern_list, regex_list, replace_list))
    except Exception as e:
        # Xảy ra lỗi khi kết nối
        print('Error: ' + str(e))
        return jsonify({'status': 'error', 'message': str(e)})


def convert_with_pattern_file_excel(source_code, conversion_rules):
    try:
        today = datetime.now().strftime("%Y/%m/%d")
        if isinstance(source_code, bytes):
            source_code = source_code.decode('utf-8')
        output_code = source_code
        for pattern, regex, replace in conversion_rules:
            if (pattern != None) and (regex != None) and (replace != None) and (regex.strip() != "TBD"):
                match_pattern = re.finditer(regex, output_code)
                if match_pattern:
                    output_code = re.sub(regex,
                                         r'//(STR) ' + today + r' K21-674 TOOL MOD\n' + '//' + pattern + r'\n' + replace + r'\n//(END) ' + today + r' K21-674 TOOL MOD',
                                         output_code)
        return output_code
    except Exception as e:
        print('Error: ' + str(e))
        return jsonify({'status': 'error', 'message': str(e)})


def process_code(file, conversion_rules):
    with open(file, encoding="utf-8") as f:
        source_code = f.read()
    if isinstance(source_code, bytes):
        source_code = source_code.decode('utf-8')
    lines = source_code.splitlines()
    total_lines = len(lines)

    # read file pattern and onvert
    new_source_code = convert_with_pattern_file_excel(source_code, conversion_rules)
    warnings.simplefilter("ignore", category=UserWarning)
    print(f'    ### Total lines code in the file {file}: {total_lines}')
    return new_source_code


def read_files():
    files = []
    files_path = []
    today = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join('output_source', today)
    pattern_path = parser.get("config", "pattern_path")
    conversion_rules_file_path = pattern_path
    conversion_rules = read_conversion_rules_from_file_excel(conversion_rules_file_path)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    project_path = parser.get("config", "project_path")

    for root, dirnames, filenames in os.walk(project_path):
        if root == project_path:
            save_root = save_dir
        else:
            rel_dir = os.path.relpath(root, project_path)
            save_root = os.path.join(save_dir, rel_dir)
        if not os.path.exists(save_root):
            os.makedirs(save_root)

        for filename in filenames:
            if filename.endswith('.java') or filename.endswith('.jsp'):
                filepath = os.path.join(root, filename)
                # Tạo lại cấu trúc thư mục gốc
                save_path = os.path.join(save_root, filename)

                data_result = process_code_all(filepath, conversion_rules)
                with open(save_path, 'w', encoding="utf-8") as f:
                    f.write(data_result)

                files.append(filename)
                files_path.append(filepath)
    return {'files': list(zip(files, files_path))}

def convert_with_pattern_file_excel_by_lines(source_code, conversion_rules):
    try:
        today = datetime.now().strftime("%Y/%m/%d")
        today_his = datetime.now().strftime("%Y.%m.%d")
        output_code = []
        pattern_history = r'修正履歴：XXXX.XX.XX XXX-XXX Name'
        pattern_history2 = r'修正履歴：20XX.XX.XX'
        for line in source_code:
            match_pattern_his = re.findall(pattern_history, line)
            match_pattern_his2 = re.findall(pattern_history2, line)
            if(match_pattern_his2):
                line = re.sub(pattern_history, r'修正履歴：' + today_his + r' K21-674 TOOL MOD\n' + r' * 修正履歴：XXXX.XX.XX XXX-XXX Name',line)
            if(match_pattern_his):
                line = re.sub(pattern_history, r'修正履歴：' + today_his + r' K21-674 TOOL MOD\n' + r' * 修正履歴：XXXX.XX.XX XXX-XXX Name',line)
            count_space = count_leading_spaces(line)
            for pattern, regex, replace in conversion_rules:
                if (pattern != None) and (regex != None) and (replace != None) and (regex.strip() != "TBD"):
                    match_pattern = re.findall(regex, line)
                    if match_pattern:
                        line = re.sub(regex,
                                             r'//(STR) ' + today + r' K21-674 TOOL MOD\n' + count_space * ' ' + '//'+line.strip() + r'\n' + count_space * ' ' + replace + r'\n' + count_space * ' ' + '//(END) ' + today + r' K21-674 TOOL MOD',
                                             line)
            output_code.append(line)
        result = ""
        for line in output_code:
            result += line + "\n"
        return result
    except Exception as e:
        print('Error: ' + str(e))
        return jsonify({'status': 'error', 'message': str(e)})

def process_code_all(file, conversion_rules):
    with open(file, encoding="utf-8") as f:
        source_code = f.read()
    if isinstance(source_code, bytes):
        source_code = source_code.decode('utf-8')
    lines = source_code.splitlines()
    total_lines = len(lines)
    # read file pattern and onvert
    new_source_code = convert_with_pattern_file_excel_by_lines(lines, conversion_rules)
    warnings.simplefilter("ignore", category=UserWarning)
    print(f'    ### Total lines code in the file {file}: {total_lines}')
    return new_source_code

print(read_files())


