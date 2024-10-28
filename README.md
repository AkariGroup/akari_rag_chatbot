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
- `-w`, `--weaviate_url`: weaviateのベースURL。デフォルトは"http://127.0.0.1:8080"  
- `-p`, `--path`: テキストファイルの保存されているディレクトリパス  
- `-c`, `--collections`: データをアップロードするコレクション名。デフォルトは"Test"  
- `-r`, `--remove`: 既存のコレクションを削除するかどうか。この引数をつけた場合削除する。  

## Weaviateのサンプル実行
- Weaviateのobjectsの確認  
   Weaviateのコレクション内に保存されているオブジェクトを一覧表示する。  
  `python3 weaviate_get_objects_example.py`  

   引数は下記が使用可能  
   - `-c`, `--collections`: 検索先のコレクション名。デフォルトは"Test"  
   - `-s`, `--show_all`: このオプションをつけると、オブジェクトの本文を全文表示する。  

- Weaviateの検索テスト  
   Weaviateのハイブリッド検索を用いて、データを検索する。  
  `python3 weaviate_search_example.py`  

   引数は下記が使用可能  
   - `-c`, `--collections`: 検索先のコレクション名。デフォルトは"Test"  
   - `-s`, `--show_objects`: このオプションをつけると、コレクションの中身の一覧を表示する。  

- Weaviateを用いた対話サンプル  
   Weaviateのハイブリッド検索を用いて取得したデータを元に対話する。  
   `python3 weaviate_qa_example.py`  

   引数は下記が使用可能  
   - `-m`, `--model`: 使用するモデル名を指定可能。モデル名はOpenaiもしくはAnthropicのものが選択可能。モデル名を羅列することで、全モデルに対して一括で問いかけが可能。  
   - `-c`, `--collections`: 検索先のコレクション名。デフォルトは"Test"  


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
