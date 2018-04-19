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

def get_viewstate(html):
    soup = BeautifulSoup(html, 'lxml')
    viewstate = soup.find('input', attrs={'id': '__VIEWSTATE'})
    viewstate_value = viewstate['value']
    eventvalidation = soup.find('input', attrs={'id': '__EVENTVALIDATION'})
    eventvalidation_value = eventvalidation['value']

    return viewstate_value, eventvalidation_value


def get_html(session, viewstate, event_validation, event_target, outro=None, stream=False, hdfExport=''):
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


def download():
    session = requests.session()

    url = "http://www.ssp.sp.gov.br/transparenciassp/"

    response = session.post(url, headers=headers)
    viewstate, eventvalidation = get_viewstate(response.text)

    params = [
        ['ctl00$cphBody$btnRouboCelular'],
        ['ctl00$cphBody$lkAno17', True, False],
        ['ctl00$cphBody$lkMes10', True, False],
        ['ctl00$cphBody$ExportarBOLink', True, True, 0]
    ]
    for i in range(len(params) - 1):
        response = get_html(session, viewstate, eventvalidation, *params[i])
        html = response.text
        viewstate, eventvalidation = get_viewstate(html)
    response = get_html(session, viewstate, eventvalidation, *params[-1])
    try:
        file_name = re.search('=.*xls', response.headers['content-disposition'])
        file_name = file_name.group().replace('=', '')
    except Exception:
        file_name = "dados.xls"

    ssp_data = response.text.split('\n')
    corrected_ssp_data = []
    for dado in ssp_data:
        dado_corrigido = re.split('\t{1}', dado)
        corrected_ssp_data.append(dado_corrigido)

    header = corrected_ssp_data[0]
    corrected_ssp_data = corrected_ssp_data[1:]
    df = pd.DataFrame(corrected_ssp_data)
    df.to_excel(file_name, index=False, encoding='utf-8', header=header)
