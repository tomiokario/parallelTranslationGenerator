import sys
from flask import Flask, render_template,request
from flask_bootstrap import Bootstrap

# 内部処理
import requests
import subprocess   # Shellコマンドの実行(openコマンドの実行)
import re           # 正規表現
import json         # json操作

# 環境変数の読み込み
import os
from os.path import join, dirname
from dotenv import load_dotenv



####################
####  setting  #####
####################

app = Flask(__name__)
bootstrap = Bootstrap(app)

#####################
#####   field   #####
#####################
# エスケープ文字の登録
escape = [
        #   対象  ⇄  エスケープ先
            ['e.g.', 'ESCEGEGEGESC'],
            ['i.e.', 'ESCIEIEIEESC'],
            ['Eq.',  'ESCEQEQEQESC'],
            ['vs.',  'ESCVSVSVSESC'],
            ['Fig.', 'ESCFIGFIGESC']
        ]
# アプリケーションのPATHを登録
path_browser = "/Applications/Brave Browser.app"

# 先頭に挿入する文字列
en_top = ">"        # 英文：引用
jp_top = "\t "     # 訳文：インデント下げ+疑問符



####################
#####  method  #####
####################
# 英語文字列を日本語文字列に翻訳
def en2jp(translate_text):
    # 環境変数の取得
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    API = os.environ.get("API")
    # リクエスト用の辞書変数(json)を作成
    params = {
        'text': translate_text,
        'source': 'en',
        'target': 'ja'
    }
    # 翻訳の実行と応答の整形
    r_post = requests.post(API, data=params)        # APIにPOSTリクエストを送信
    r_data = json.loads(r_post.text)                # 応答をrequests型からdict型に変換
    jp_text = r_data['text']                        # textを抽出
    return jp_text


########################
### routing & action ###
########################

#indexページ(フォーム画面)
@app.route('/')
def index():
    return render_template('index.html')

# outputページ
@app.route('/output/', methods = ['POST', 'GET'])
def output():
    ##########   初期化   ###########
    # 出力用文字列の初期化
    japanese_str = ""
    english_str = ""
    output = ""
    msg = ""

    # フォームから文字列を取得
    english_str = request.form['eng_text']  # フォームからnameを取得


    #############################################################################################
    ##################
    ### 英文の整形 ###
    ##################
    ###### PDFの改行後のスペースを整形 ######
    # 改行文字を削除
    english_str = english_str.replace('\n', ' ')
    # 全角スペースを半角スペースに変換
    english_str = english_str.replace('\u3000',' ')
    # ピリオド後の空白文字を削除
    english_str = re.sub(r"\.\s+", ".", english_str)
    # 先頭の空白文字を削除
    english_str = re.sub(r"^\s+", "", english_str)

    ###### エスケープ #####
    # ピリオドを含む文字をエスケープ
    for i in range(len(escape)):
        english_str = english_str.replace(escape[i][0], escape[i][1])

    # 小数をエスケープ
    array_dicimal = re.findall(r"\d+\.\d+", english_str)    # 小数を抽出してリストに保存
    english_str = re.sub(r"\d+\.\d+", "<DICIMALDICIMALDICIMAL>", english_str)   # エスケープ

    # ピリオド後の文献番号をエスケープ
    numbers = re.findall(r"\.\d+", english_str)   #.<数字>のパターンを抽出してリストに保存
    english_str = re.sub(r"\.[0-9]+", "<DOTPLUSNUMBERSPATTERN>", english_str) # エスケープ

    # ピリオド後の[文献番号]をエスケープ
    brackets_numbers = re.findall(r"\.\[\d+\]", english_str)   #.<数字>のパターンを抽出してリストに保存
    english_str = re.sub(r"\.\[[0-9]+\]", "<DOTPLUSBRACKETSNUMBERSPATTERN>", english_str) # エスケープ

    ###### 改行文字の挿入 ######
    # ピリオドの後に改行を挿入
    english_str = english_str.replace('.', '.\n\n')
    # ピリオド+引用文献の後に改行を挿入
    english_str = english_str.replace("<DOTPLUSNUMBERSPATTERN>", "<DOTPLUSNUMBERSPATTERN>\n\n")
    english_str = english_str.replace("<DOTPLUSBRACKETSNUMBERSPATTERN>", "<DOTPLUSBRACKETSNUMBERSPATTERN>\n\n")

    ###### エスケープ文字をもとに戻す ######
    # ピリオドを含む文字列を戻す
    for i in range(len(escape)):
        english_str = english_str.replace(escape[i][1], escape[i][0])
    # 小数をもとに戻す
    for dicimal in array_dicimal:
        english_str = english_str.replace("<DICIMALDICIMALDICIMAL>", str(dicimal), 1) #先頭を置換
    # ピリオド後の文献番号を元の位置に挿入
    for number in numbers:
        english_str = english_str.replace("<DOTPLUSNUMBERSPATTERN>", str(number), 1)  #先頭を置換
    # ピリオド後の[文献番号]を元の位置に挿入
    for brackets_number in brackets_numbers:
        english_str = english_str.replace("<DOTPLUSBRACKETSNUMBERSPATTERN>", str(brackets_number), 1)  #先頭を置換
    #############################################################################################
    ##################
    ### 英文の翻訳 ###
    ##################

    # 英文文字列から翻訳文字列の取得
    input_str = en2jp(english_str)

    #############################################################################################
    ##################
    ### 文章の整形 ###
    ##################

    # 文字列を一行ごとに分割して配列に格納
    array_jp = input_str.split('\n')
    array_en = english_str.split('\n')

    for j in range(len(array_jp)):
        # 空行をスキップ
        if array_jp[j] == "" or array_jp[j]==" ":
            continue
        # テキストを生成
        output += en_top + array_en[j] + "\n"
        output += jp_top + array_jp[j] + "\n"


    # output.htmlに変数を渡す
    return render_template("output.html",result_text=output)


####################
####  MAIN処理  ####
####################
if __name__ == '__main__':
    # アプリケーションの開始
    app.run()
