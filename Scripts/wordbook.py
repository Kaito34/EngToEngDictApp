import requests
from bs4 import BeautifulSoup
import csv
import sys
import pandas as pd
import numpy as np
import logging
import traceback
import os
import time
import datetime
import gspread
from gspread_formatting import *
import json
from oauth2client.service_account import ServiceAccountCredentials


# デフォルトディレクトリはアプリケーションない

#単語が保存されているリストファイルを開く
# (1) Google Spread Sheetsにアクセス
def connect_gspread(jsonf,key):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(jsonf, scope)
    gc = gspread.authorize(credentials)
    SPREADSHEET_KEY = key
    worksheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
    return worksheet

jsonf = "../Data/engtoengapp-b8f9889764f5.json"
spread_sheet_key = "1DtxvYGENRqAgcAtuvz8r-pELl3xyb5rETs38ZXvcpmc"
ws = connect_gspread(jsonf,spread_sheet_key)
list_of_lists = ws.get_all_values()

#未記入の場合に備える
if np.array(list_of_lists).shape[1] == 0 :
    print('Please register words that you want to learn.')
    exit(1)

#読み込み
word_df = pd.DataFrame(list_of_lists,columns=['date','word','checkbox',"IPA",'the_part_of_speech','def','sentence','synonym']).iloc[1:,:]
wsrange = word_df.shape[0]

#重複は削除
word_df = word_df[~word_df.duplicated(subset='word')]
word_df = word_df.set_index(keys='word')



#検索する単語を入力
word_emp = word_df[
    (word_df['def'].isnull()) |
    (word_df['def'] == '')].index.tolist()
synonym_emp = word_df[
    (word_df['synonym'].isnull()) |
    (word_df['synonym'] == '')].index.tolist()


def search_definition(word_df,word):
    #初期化
    word_mean = "nodata"
    word_the_part_of_speech = word_ipa = word_example_sentence = ""

    #urlを検索・スクレイピング
    search_url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
    print(f"search_url = {search_url}")

    # if error: requests.exceptions.ConnectionError:('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
    # The issue is that the website filters out requests without a proper User-Agent, so just use a random one from MDN:
    try:
        url = requests.get(search_url,headers={
    "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    })
        soup = BeautifulSoup(url.text, "html.parser")
        #候補が複数ある場合は空白を返す
        if len(soup.find_all(class_='pos dpos')) == 0:
            #TODO わざとエラーを起こす
            print("We have these words with similar spellings or pronunciations") 
            asdfasd.hoasdf()

        #TODO 全部に帰る
        """
        suggest
        難しい方の意味を持ってきたい　例:novel→new　複数辞書参照する？
        synonymも追加したい
        トリガーの設定
        """
        
        word_mean = soup.find_all(class_='ddef_h')[0].get_text()
        word_ipa = soup.find_all(class_='pron dpron')[-1].get_text()
        word_the_part_of_speech = soup.find_all(class_='pos dpos')[0].get_text()
        word_example_sentence = soup.find_all(class_='examp dexamp')[0].get_text()
        
        """ 例文は一番長いやつにする
        #比較用変数
        tmp_word_mean = ''
        tmp_word_example_sentence = ''
        word_means = soup.find_all(class_='ddef_h')
        for word_mean_elem in word_means:
            if len(word_mean_elem.get_text()) > len(tmp_word_mean):
                tmp_word_mean = word_mean_elem.get_text()
        word_mean = tmp_word_mean

        word_example_sentences = soup.find_all(class_='examp dexamp')
        for word_example_sentence_elem in word_example_sentences:
            if len(word_example_sentence_elem.get_text()) > len(tmp_word_example_sentence):
                tmp_word_example_sentence = word_example_sentence_elem.get_text()
        word_example_sentence = tmp_word_example_sentence
        """
        

    except:
        logging.error(traceback.format_exc())
        print("This word doesn't exist. Start again.")


    #元のdfに入れていく
    word_df.loc[word,"IPA"]  = word_ipa
    word_df.loc[word,"the_part_of_speech"] = word_the_part_of_speech
    word_df.loc[word,"def"] = word_mean
    word_df.loc[word,"sentence"] = word_example_sentence

    return word_df

# synonym
def search_synonym(word_df,word):
    #初期値
    synonym_stuck = 'nodata'

    search_url = f"https://www.thesaurus.com/browse/{word}"

    try:
        url = requests.get(search_url,headers={
        "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
        })

        soup = BeautifulSoup(url.text, "html.parser")

        #css-1gyuw4i eh475bn0 が一番近い TODO 関連性の範囲,最大5つにする
        #最上位の意味が無い場合
        if len(soup.find_all(class_='css-1gyuw4i eh475bn0')) == 0:
            print('関連する単語が見つかりません')

            #2番目に関連度のある類義語をストックする
            for rep,synonym_ele in enumerate(soup.find_all(class_='css-1n6g4vv eh475bn0')):
                #最大で5つ類義語を取得
                if rep > 4:
                    break

                if synonym_stuck == 'nodata':
                    synonym_stuck = synonym_ele.get_text().split(' ')[0]
                else:
                    synonym_stuck += f", {synonym_ele.get_text().split(' ')[0]}"
            
        
        #類義語をストックする
        for rep,synonym_ele in enumerate(soup.find_all(class_='css-1gyuw4i eh475bn0')):
            #最大で5つ類義語を取得
            if rep > 4:
                break

            if synonym_stuck == 'nodata':
                synonym_stuck = synonym_ele.get_text().split(' ')[0]
            else:
                synonym_stuck += f", {synonym_ele.get_text().split(' ')[0]}"
        
        print(synonym_stuck)
        
    except:
        logging.error(traceback.format_exc())
    
    word_df.loc[word,"synonym"] = synonym_stuck

    return word_df



for i in range(len(word_emp)):
    word = word_emp[i]
    word_df = search_definition(word_df,word)
    time.sleep(3)

for i in range(len(synonym_emp)):
    word = synonym_emp[i]
    word_df = search_synonym(word_df,word)
    time.sleep(3)

"""整形"""
#空白行を削除
"""
word_df = word_df[
        (word_df['date']!='') &
        (word_df['IPA']!='') &
        (word_df['the_part_of_speech']!='') &
        (word_df['def']!='') &
        (word_df['sentence']!='')]
"""

#改行は消す 先頭の空白も消す
def delHeadSpace(wstring):
    if len(wstring) == 0: #空白の場合は返す
        return wstring
    wstring = wstring.replace('\n',' ').replace('  ',' ')
    if wstring[0] == ' ':
        wstring = wstring[1:]
    if wstring[-1] == ':':
        wstring = wstring[:-1]
    if wstring[-2:] == ': ':
        wstring = wstring[:-2]
    return wstring

word_df['def'] = word_df['def'].map(delHeadSpace)
word_df['sentence'] = word_df['sentence'].map(delHeadSpace)

# synonymのnodata,...は消す

# C1, B2みたいなやつも消す
# 日付がかぶっていたら秒数を微妙に帰る
dateVariety,numb = np.unique( word_df['date'].values,return_counts=True)
date_unique_df = pd.DataFrame(np.unique(word_df['date'].values,return_counts=True),index=['date','number']).T

for date_ele in date_unique_df[date_unique_df['number']>1]['date']:
    word_df_ele = word_df[word_df['date']==date_ele].copy()
    word_df_nonele = word_df[word_df['date']!=date_ele].copy()
    word_df_ele['date'] = np.array(
            [
                (
                    (datetime.datetime.strptime(
                        word_df_ele['date'][0],
                        '%m/%d/%Y %H:%M:%S')
                    )+datetime.timedelta(seconds=i)
                ).strftime('%m/%d/%Y %H:%M:%S') 
                for i in range(len(word_df_ele['date']))
            ])
    word_df = pd.concat([word_df_ele,word_df_nonele])

# 日付順に
word_df['datetime'] = pd.to_datetime(
    word_df['date'], format='%m/%d/%Y %H:%M:%S')
word_df = word_df.sort_values(by='datetime').drop('datetime', axis=1)

#synonymがかけていればチェックマーク
word_df.loc[word_df[
    (word_df['synonym'].isnull()) |
    (word_df['synonym'] == '')].index,'checkbox'] = '×'

#なにか一つでも情報が欠けていたら頭に固める　チェックボックス導入
word_df_nodata = word_df[word_df['checkbox']=='×']
word_df_withdata = word_df[~(word_df.index.isin(word_df_nodata.index))]
word_df = pd.concat([
    word_df_nodata,word_df_withdata])

#スプシを反映 no attribte errorはgspreadのバージョンによるエラー
word_df = word_df.reset_index()
word_df = word_df[['date','word','checkbox',"IPA",'the_part_of_speech','def','sentence','synonym']]

word_list = word_df.values.tolist()

for i in range(wsrange - word_df.shape[0]):
    word_list.append(['' for i in range(len(word_df.columns))])
ws.update(f'A2:H{wsrange+1}',word_list)


#不備があれば色をつける それ以外は無色
fmt = cellFormat(
        backgroundColor=color(1, 1, 1),
        textFormat=textFormat(bold=False, foregroundColor=color(0, 0, 0)),
        horizontalAlignment='LEFT'
        )
format_cell_range(ws, f'A2:H{word_df.shape[0]+1}', fmt)
if word_df_nodata.shape[0] != 0:
    fmt_colorize = cellFormat(
        backgroundColor=color(1, 0.9, 0.9),
        textFormat=textFormat(bold=True, foregroundColor=color(1, 0, 1)),
        horizontalAlignment='LEFT'
        )
    format_cell_range(ws, f'A2:H{word_df_nodata.shape[0]+1}', fmt_colorize)


# csvで出力用に整形
word_df = word_df[word_df['checkbox']!='×'][['word',"IPA",'the_part_of_speech','def','sentence','synonym']]
word_df.to_csv('../Data/sheet_for_anki.csv',header=False,index=False)