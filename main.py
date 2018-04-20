# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 22:15:23 2018

@author: daniel
"""
import re
import pandas as pd
import xlrd
import requests
from bs4 import BeautifulSoup

headers = {
    'Origin': 'http://www.ssp.sp.gov.br',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Referer': 'http://www.ssp.sp.gov.br/transparenciassp/',
    'Connection': 'keep-alive',
}

def get_viewstate_eventvalidation(html):
    """
    Extract __VIEWSTATE and __EVENTVALIDATION
    """
    soup = BeautifulSoup(html, 'lxml')
    viewstate = soup.find('input', attrs={'id': '__VIEWSTATE'})
    viewstate_value = viewstate['value']
    eventvalidation = soup.find('input', attrs={'id': '__EVENTVALIDATION'})
    eventvalidation_value = eventvalidation['value']

    return viewstate_value, eventvalidation_value


def get_response(session, viewstate, event_validation, event_target, outro=None, stream=False, hdfExport=''):
    """
    Handles all the responses received from every request made to the website.
    """
    url = "http://www.ssp.sp.gov.br/transparenciassp/"
    data = [
        ('__EVENTTARGET', event_target),
        ('__EVENTARGUMENT', ''),
        ('__VIEWSTATE', viewstate),
        ('__EVENTVALIDATION', event_validation),
        ('ctl00$cphBody$hdfExport', hdfExport),

    ]

    if outro:
        data.append(('ctl00$cphBody$filtroDepartamento', '0'))
        data.append(('__LASTFOCUS', ''))

    response = session.post(url, headers=headers, data=data, stream=stream)
    return response

def extract_file_name(response_headers):
    """
    Tries to extract the filename returned from the response of the request.
    """

    try:
        file_name = re.search('=.*xls', response_headers)
        file_name = file_name.group().replace('=', '')
    except Exception:
        file_name = "dados.xls"

    return file_name

def extract(month_value, year_value, information, write_to_disk=False):
    """
    Returns a dataframe with the information from the website.
    If write_to_disk is True, then a xls file is created on disk.
    """
    print("Extracting")
    session = requests.session()

    url = "http://www.ssp.sp.gov.br/transparenciassp/"

    response = session.post(url, headers=headers)
    viewstate, eventvalidation = get_viewstate_eventvalidation(response.text)

    parameters_list = [
        [information],
        [month_value, True, False],
        [year_value, True, False],
    ]
    for parameters in parameters_list:
        response = get_response(session, viewstate, eventvalidation, *parameters)
        html = response.text
        viewstate, eventvalidation = get_viewstate_eventvalidation(html)

    response = get_response(session, 
                        viewstate,
                        eventvalidation, 
                        'ctl00$cphBody$ExportarBOLink',
                        True,
                        True,
                        0)
    file_name = extract_file_name(response.headers['content-disposition'])

    ssp_data = response.text.split('\n')
    corrected_ssp_data = []
    for dado in ssp_data:
        dado_corrigido = re.split('\t{1}', dado)
        corrected_ssp_data.append(dado_corrigido)

    if write_to_disk:
        header = corrected_ssp_data[0]
        corrected_ssp_data = corrected_ssp_data[1:]
        df = pd.DataFrame(corrected_ssp_data)
        df.to_excel(file_name, index=False, encoding='utf-8', header=header)

    df = pd.DataFrame(corrected_ssp_data)
    return df

def run(write_to_disk=False):

    """
    Interactive optin to run the scraper.
    Choose an option, a month and a year to download the corrected information.
    """
    print("Opções:")
    print("1 - Homicídio Doloso")
    print("2 - Latrocínio")
    print("3 - Lesão Corporal Seguida de Morte")
    print("4 - Morte Decorrente de Oposição À Intervenção Policial")
    print("5 - Morte Suspeita")
    print("6 - Furto de Veículo")
    print("7 - Roubo de Veículo")
    print("8 - Furto de Celular")
    print("9 - Roubo de Celular")
    option = int(input("Escolha a opção: "))
    year = str(input("Informe o ano  ( 2003 - 2018 ): "))
    year = year[-2:]
    year_value = "ctl00$cphBody$lkAno{}".format(year)
    month = str(input("Informe o mês ( 1 - 12 ): "))
    month_value = "ctl00$cphBody$lkMes{}".format(month)

    informations = {
        1:"ctl00$cphBody$btnHomicicio",
        2:"ctl00$cphBody$btnLatrocinio",
        3:"ctl00$cphBody$btnLesaoMorte",
        4:"ctl00$cphBody$btnMortePolicial",
        5:"ctl00$cphBody$btnMorteSuspeita",
        6:"ctl00$cphBody$btnFurtoVeiculo",
        7:"ctl00$cphBody$btnRouboVeiculo",
        8:"ctl00$cphBody$btnFurtoCelular",
        9:"ctl00$cphBody$btnRouboCelular",
    }

    information = informations[option]
    return extract(month_value, year_value, information, write_to_disk)