from jira import JIRA
from atlassian import Confluence
import markdown

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
    Создает Markdown-файл, заменяя переносы строк на пробелы
    и экранируя спецсимволы.
    """
    try:
        options = {'server': url_jira_server, 'verify': path_to_cert}
        jira = JIRA(options=options, basic_auth=log_passw)

        table_header = "| Задача | Что изменено | Как изменено |\n"
        table_divider = "|:---|:---|:---|\n"
        markdown_content = table_header + table_divider

        for issue_key in issues_list:
            issue = jira.issue(issue_key, fields=f"{field_what},{field_how}")
            
            what_value = getattr(issue.fields, field_what, None)
            how_value = getattr(issue.fields, field_how, None)

            if what_value:
                # 1. Заменяем оба вида переносов на пробел
                # 2. Экранируем '|' для избежания конфликтов с компилятором markdown
                what_str = str(what_value).replace('\r\n', ' ').replace('\n', ' ').replace('|', '\\|')
            else:
                what_str = "-"

            if how_value:
                how_str = str(how_value).replace('\r\n', ' ').replace('\n', ' ').replace('|', '\\|')
            else:
                how_str = "-"
            
            issue_link = f"[{issue_key}]({url_jira_server}/browse/{issue_key})"
                
            markdown_content += f"| {issue_link} | {what_str} | {how_str} |\n"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Корректный Markdown-файл успешно создан: '{filename}'")

    except Exception as e:
        print(f"Произошла ошибка при создании Markdown-файла: {e}")

def create_confluence_space_and_page(confluence_url,
                                     login,
                                     passw,
                                     space_key,
                                     space_name,
                                     page_title,
                                     markdown_file_path,
                                     path_to_cert="",
                                     parent_page_id=None): # Параметр оставлен для совместимости, но не используется в create_space
    """
    Проверяет наличие пространства, при необходимости создает его,
    затем читает Markdown, конвертирует его в HTML и загружает 
    в виде страницы в Confluence.
    """
    try:
        confluence = Confluence(
            url=confluence_url,
            username=login,
            password=passw,
            cloud=False,
            verify_ssl=path_to_cert if path_to_cert else True
        )

        # Проверяем, существует ли пространство
        try:
            confluence.get_space(space_key)
            print(f"Пространство '{space_key}' уже существует.")
        except Exception:
            # get_space() вызывает исключение
            print(f"Пространство '{space_key}' не найдено. Создаем новое...")
            try:
                confluence.create_space(
                    space_key=space_key,
                    space_name=space_name
                )
                print(f"Пространство '{space_name}' ({space_key}) успешно создано.")
            except Exception as e:
                print(f"Не удалось создать пространство '{space_key}': {e}")
                return

        if not markdown_file_path:
            print("Путь к Markdown файлу не указан. Создание/обновление страницы пропущено.")
            return

        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Конвертируем Markdown в HTML
        body_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
        
        # Проверяем и создаем/обновляем страницу
        if confluence.page_exists(space=space_key, title=page_title):
            page_id = confluence.get_page_id(space=space_key, title=page_title)
            status = confluence.update_page(
                page_id=page_id,
                title=page_title,
                body=body_content,
                parent_id=parent_page_id,
                representation='storage'
            )
            if status and 'id' in status:
                print(f"Страница '{page_title}' успешно обновлена. ID: {status['id']}")
            else:
                print(f"Страница '{page_title}' была обновлена, но API не вернул подтверждение.")
        else:
            status = confluence.create_page(
                space=space_key,
                title=page_title,
                body=body_content,
                parent_id=parent_page_id,
                representation='storage'
            )
            if status and 'id' in status:
                print(f"Страница '{page_title}' успешно создана. ID: {status['id']}")
            else:
                print(f"Не удалось создать страницу '{page_title}'.")

    except Exception as e:
        print(f"Произошла общая ошибка при работе с Confluence: {e}")

# Данные для подключения
# Путь к файлу сертификата if use virtual envirament
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
space_name = "test"
page_title = "Заголовок"


linked_issues = linked_issues_func(url, (log, passw), task_num, path_to_cert)

print(linked_issues)

create_table_md(url, (log, passw), linked_issues, field_WHAT, field_HOW,
                table_md_path, path_to_cert)

create_confluence_space_and_page(url_confluence, log, passw,
                                 space_key, space_name,
                                 page_title, table_md_path, path_to_cert)