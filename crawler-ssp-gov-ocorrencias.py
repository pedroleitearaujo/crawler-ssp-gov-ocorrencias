import http.client, re, json, traceback, datetime, requests
from html.parser import HTMLParser
from bs4 import BeautifulSoup
from operator import itemgetter

start_time = ''
end_time = ''

def date_today():
    date = datetime.datetime.now()
    return date.strftime('%d/%m/%Y %H:%M:%S')

def getInfoByBox():
    try:
        features = 'html.parser'
        date = datetime.date.today()

        start_time = date_today()
        print(f"Começou às {start_time}.")
        url = 'http://www.ssp.sp.gov.br/Estatistica/Pesquisa.aspx'

        response = requests.post(url)
        soup = BeautifulSoup(response.text, features=features)

        # Pegando os parametros da Requisição
        body = {
            '__EVENTTARGET':'ctl00$conteudo$btnMensal',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': '',
            '__VIEWSTATEGENERATOR':'D5E3DF7A',
            '__EVENTVALIDATION': '',
            'ctl00$conteudo$ddlAnos':'0',
            'ctl00$conteudo$ddlRegioes':'0',
            'ctl00$conteudo$ddlMunicipios':'0',
            'ctl00$conteudo$ddlDelegacias':'0'
        }

        body['__VIEWSTATE'], body['__EVENTVALIDATION'] = getViewstateAndEventvalidation(soup)

        response = requests.post(url, data=body)
        soup = BeautifulSoup(response.text, features=features)
        
        html_select_regioes = soup.find("select", {"id": "conteudo_ddlRegioes"})
        html_select_regioes = html_select_regioes.findAll("option")

        table = []
        for index_regiao, regiao in enumerate(html_select_regioes):
            if index_regiao != 0:
                body['__EVENTTARGET'] = 'ctl00$conteudo$ddlRegioes'
                body['ctl00$conteudo$ddlRegioes'] = regiao['value']

                body['__VIEWSTATE'], body['__EVENTVALIDATION'] = getViewstateAndEventvalidation(soup)

                response = requests.post(url, data=body)
                soup = BeautifulSoup(response.text, features=features)

                html_select_municipios = soup.find("select", {"id": "conteudo_ddlMunicipios"})
                html_select_municipios = html_select_municipios.findAll("option")

                for index_mun, mun in enumerate(html_select_municipios):
                    if index_mun != 0:
                        year = date.year

                        body['__EVENTTARGET'] = 'ctl00$conteudo$ddlMunicipios'
                        body['ctl00$conteudo$ddlMunicipios'] = mun['value']

                        body['__VIEWSTATE'], body['__EVENTVALIDATION'] = getViewstateAndEventvalidation(soup)
                        
                        response = requests.post(url, data=body)
                        soup = BeautifulSoup(response.text, features=features)

                        print(f"Município: {mun.text} Código: {mun['value']} e Região: {regiao.text} Código: {regiao['value']}")

                        # Pegar as tabelas.
                        for i in range(3):
                            html_table_repAnos = soup.find("table", {"id": f"conteudo_repAnos_gridDados_{i}"})
                            html_lines = html_table_repAnos.findAll('tr')

                            if(len(html_lines) > 0):
                                for index_line, line in enumerate(html_lines):
                                    if index_line == 0:
                                        continue
                                    else:
                                        html_colums_data = line.findAll('td')
                                        if(len(html_colums_data) > 0):
                                            for index_colum_data, colum_data in enumerate(html_colums_data):
                                                if index_colum_data == 0 or index_colum_data == (len(html_colums_data)-1):
                                                    continue
                                                else:
                                                    table.append({
                                                        'cod_mun': int(mun['value']),
                                                        'mes': int(index_colum_data),
                                                        'natureza': html_colums_data[0].text,
                                                        'valor': colum_data.text if str(colum_data.text) != '...' else 0,
                                                        'ano': int(year)
                                                    })
                            year+= -1
        makeQuerySql(table)

    except Exception as e:
        print(traceback.format_exc())

def makeQuerySql(data):
    txt_file = open("/var/www/html/estasticas-ssp.txt", 'w', encoding='utf-8')
    # Ordenar em codigo de municipio para ver se tem algum faltando.
    data.sort(key=lambda x: x.get('cod_mun'))
    
    query = "INSERT INTO tb_ocorrencias_mes (cod_mun, mes, natureza, valor, ano) VALUES "
    txt_file.write(f'{query}\n')

    for index, value in enumerate(data):

        if index == 0 or value['cod_mun'] != data[index - 1]['cod_mun']:
            print(f"Criando querys de insert para o município com o código: {value['cod_mun']}")

        string_values = f"({value['cod_mun']}, {value['mes']}, '{value['natureza']}', {value['valor']}, {value['ano']})"

        if index == (len(data) - 1):
            string_values+= ";"
        else:
            string_values+= ","

        txt_file.write(f'{string_values}\n')
    end_time = date_today()
    print(f"Começou às {start_time} e finalizou às {end_time}.")
    txt_file.close()

def getViewstateAndEventvalidation(soup):
    return itemgetter('value')(soup.find("input", {"id": "__VIEWSTATE"})), itemgetter('value')(soup.find("input", {"id": "__EVENTVALIDATION"}))


getInfoByBox()