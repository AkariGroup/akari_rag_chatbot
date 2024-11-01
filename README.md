# akari_rag_chatbot

AKARIの音声対話botにWeaviateを用いたRAG機能を追加するアプリ

## submoduleの更新
`git submodule update --init --recursive`  

## 仮想環境の作成
`python -m venv venv`  
`source venv/bin/activate`  
`pip install -r requirements.txt`  

## セットアップ方法
[akari_chatgpt_botのREADME](https://github.com/AkariGroup/akari_chatgpt_bot/blob/main/README.md)のセットアップ手順に沿って実行する。  

Weaviateをdockerで起動する。  
`cd weaviate/docker`  
`docker-compose up -d`  

## Weaviateについて
Weaviateは、ベクトル検索を用いたデータベース。  
このchatbotでは、Weaviateを用いてRAG(Retrieval Augmented Generation)を行う。  
Weaviateにデータを登録し、ユーザーの質問に対して、Weaviateを用いてデータを検索し、その結果を元に対話を行う。  
WeaviateではCollectionという単位でデータを管理し、各Collection内にObjectとしてデータを登録する。検索する際は、指定したCollection内のObjectから検索を行う。  

## Weaviateへのデータ追加
Weaviateにテキストファイルをアップロードする。  
テキストファイルは、所定の長さで分割され、各Objectに登録される。  
`python3 weaviate_uploader.py`  

引数は下記が使用可能  
- `-p`, `--path`: テキストファイルの保存されているパス。ディレクトリを指定すると、ディレクトリ内のファイルを一括で追加する。  
- `-c`, `--collection`: データをアップロードするコレクション名。デフォルトは"Test"  
- `-r`, `--remove`: 既存のコレクションを削除するかどうか。この引数をつけた場合削除する。  

## Weaviateのサンプル実行
- Weaviateのobjectsの確認  
   Weaviateのコレクション内に保存されているオブジェクトを一覧表示する。  
  `python3 weaviate_get_objects_example.py`  

   引数は下記が使用可能  
   - `-c`, `--collection`: 検索先のコレクション名。デフォルトは"Test"  
   - `-s`, `--show_all`: このオプションをつけると、オブジェクトの本文を全文表示する。  
   - `-d`, `--sort_by_date`: このオプションをつけると、オブジェクトのソートを日付順で行う。つけない場合は、source名の順にソートする。  

- Weaviateの検索テスト  
   Weaviateのハイブリッド検索を用いて、データを検索する。  
  `python3 weaviate_search_example.py`  

   引数は下記が使用可能  
   - `-c`, `--collection`: 検索先のコレクション名。デフォルトは"Test"  
   - `-s`, `--show_objects`: このオプションをつけると、コレクションの中身の一覧を表示する。  

- Weaviateを用いた対話サンプル  
   Weaviateのハイブリッド検索を用いて取得したデータを元に対話する。  
   `python3 weaviate_qa_example.py`  

   引数は下記が使用可能  
   - `-m`, `--model`: 使用するモデル名を指定可能。モデル名はOpenaiもしくはAnthropicのものが選択可能。モデル名を羅列することで、全モデルに対して一括で問いかけが可能。  
   - `-c`, `--collection`: 検索先のコレクション名。デフォルトは"Test"  


## Weaviateを用いた音声対話の起動方法

1. [akari_chatgpt_botのREADME](https://github.com/AkariGroup/akari_chatgpt_bot/blob/main/README.md)内 **遅延なし音声対話botの実行** の起動方法1.~3.を実行する。  

2. rag_gpt_publisherを起動する。
   `python3 rag_gpt_publisher.py`  

   引数は下記が使用可能  
   - `--ip`: gpt_serverのIPアドレス。デフォルトは"127.0.0.1"  
   - `--port`: gpt_serverのポート。デフォルトは"10001"  
   - `-c`, `--collections`: 検索先のコレクション名。デフォルトは"Test"  

### スクリプトで一括起動する方法

1. [akari_chatgpt_botのREADME](https://github.com/AkariGroup/akari_chatgpt_bot/blob/main/README.md)内 **VOICEVOXをOSS版で使いたい場合** の手順を元に、別PCでVoicevoxを起動しておく。  

2. スクリプトを実行する。  
   `cd script`  
   `./rag_chatbot.sh {1.でVoicevoxを起動したPCのIPアドレス} {akari_motion_serverのパス}`  


## Weaviateへのデータ追加、対話までの流れ
ここでは、サンプルのテキストを使ったWeaviateへのデータ追加、対話アプリへの適用方法を説明します。  

### サンプルデータの追加  
`data_sample` 直下にAKARIの情報を記載したサンプルのテキストファイルが2つあります。  
まずはこれをweaviateに追加してみます。  

`python3 weaviate_uploader.py -c Test -p data_sample/`  

これを実行すると、`Test` というコレクション名の中に2つのテキストファイルが追加されます。  
テキストファイルは、指定した文字数で分割され、各オブジェクトに登録されます。  

### Weaviateの内容確認
先程追加したデータが正しく登録されているか確認します。  

`python3 weaviate_get_objects_example.py -c Test`

これを実行すると、`Test` というコレクション内に登録されているオブジェクトの一覧が表示されます。  
オブジェクトに分割されたテキストファイルの内容が確認できればOKです。  

### Weaviateの検索テスト
Weaviateの検索機能をテストします。  

`python3 weaviate_search_example.py -c Test`  

これを実行すると、テキスト入力を求められます。  
テキストを入力してからEnterを押すと、そのテキストに関連する オブジェクトを検索し、その結果を表示します。  
検索はベクトル類似度による検索と、キーワードによる全文検索を組み合わせたハイブリッド検索により行われます。  
例えば"AKARIに使われているCPUは？"検索すると、CPUについて記載したオブジェクトが最初に表示され、スコアが一番高いことが分かると思います。

### Weaviateを用いた文章生成
Weaviateの検索結果を元に文章生成を行います。

`python3 weaviate_qa_example.py -c Test`

これを実行すると、テキスト入力を求められます。  
テキストを入力してからEnterを押すと、そのテキストに関連する オブジェクトを検索し、その内容を元にLLMで文章生成を行います。  
例えば"AKARIに使われているCPUは？"検索すると、"AKARIには、Intelの第8世代Core m3-8100Yを搭載したシングルボードコンピュータ、LattePanda Alpha 864sが使われています。"といったような、検索結果に基づいた文章が生成されると思います。  

### 音声対話アプリの実行
最後に、上記の"Weaviateを用いた音声対話の起動方法" の中で、rag_gpt_publisherを
   `python3 rag_gpt_publisher.py -c Test`  

で起動すると、この知識を元にした音声対話が可能となります。  
これを参考に、各自のデータをWeaviateに登録し、音声対話アプリを実行してみてください。  


