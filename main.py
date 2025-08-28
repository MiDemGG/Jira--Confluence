from jira import JIRA

def linked_issues_func(url_jira_server, log_passw, task_key, path_to_cert):
    
    # Для виртуального окружения сертификат
    options = {
        'server': url_jira_server,
        'verify': path_to_cert
    }

    # Авторизация
    jira = JIRA(options=options,
                basic_auth=log_passw)

    # Ключ задачи
    issue = jira.issue(task_key)

    # Массив привязанных задач
    linked_issues = []
    for link in issue.fields.issuelinks:
        # задачи, на которые ссылается текущая
        if hasattr(link, "outwardIssue"):
            linked_issues.append(link.outwardIssue.key)
        # задачи, которые ссылаются на текущую
        if hasattr(link, "inwardIssue"):
            linked_issues.append(link.inwardIssue.key)
    return linked_issues

def create_table_md(url_jira_server,
                    log_passw,
                    issues_list,
                    field_what,
                    field_how,
                    filename,
                    path_to_cert):
    """
    Создает корректный Markdown-файл со ссылками на задачи,
    правильно обрабатывая переносы строк и спецсимволы.
    """
    try:
        # Для виртуального окружения сертификат
        options = {
            'server': url_jira_server,
            'verify': path_to_cert
        }

        jira = JIRA(options=options, basic_auth=log_passw)

        table_header = "| Задача | Что изменено | Как изменено |\n"
        table_divider = "|:---|:---|:---|\n"
        markdown_content = table_header + table_divider

        for issue_key in issues_list:
            issue = jira.issue(issue_key, fields=f"{field_what},{field_how}")
            
            what_value = getattr(issue.fields, field_what, None)
            how_value = getattr(issue.fields, field_how, None)

            # Готовим текст для ячеек
            what_str = str(what_value).replace('\r', '').replace('\n', '<br>').replace('|', '\|') if what_value else "-"
            how_str = str(how_value).replace('\r', '').replace('\n', '<br>').replace('|', '\|') if how_value else "-"
            
            # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
            # Формируем Markdown-ссылку на задачу
            issue_link = f"[{issue_key}]({url_jira_server}/browse/{issue_key})"
            # ---------------------
                
            markdown_content += f"| {issue_link} | {what_str} | {how_str} |\n"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Отчет успешно создан и сохранен в файл: '{filename}'")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Данные для подключения
# Путь к файлу сертификата if use virtual envirement
path_to_cert = './venv/cert/jira-gal-lan-chain.pem'
# Jira server
url = 'https://jira.galaktika.local'
log = 'dementev@gal.lan'
passw = 'MiDem31052004!'
task_num = 'ERP-12800'
field_WHAT = 'customfield_10310'
field_HOW = 'customfield_10311'
table_md_path = './tmp/table.md'
# Confluence server
url_confluence = "https://jira.galaktika.local/wiki"
space_key = "test" # ключ пространства
page_title = "Заголовок"


linked_issues = linked_issues_func(url, (log, passw), task_num, path_to_cert)

print(linked_issues)

create_table_md(url, (log, passw), linked_issues, field_WHAT, field_HOW,
                table_md_path, path_to_cert)
