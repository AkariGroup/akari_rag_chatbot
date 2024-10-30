import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import weaviate
import weaviate.classes as wvc
from langchain.text_splitter import CharacterTextSplitter

from .conf import COHERE_APIKEY, OPENAI_APIKEY


class WeaviateRagUploader(object):
    def __init__(
        self,
        weaviate_url: str = "http://localhost:8080",
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        collection_name: str = "Test",
        remove_collection: bool = False,
    ):
        """
        初期化

        Args:
            collection_name(str): コレクション名
            weaviate_url(str): WeaviateのURL
            chunk_size(int): テキストのチャンクサイズ
            chunk_overlap(int): チャンクのオーバーラップ
            remove_collection(bool): コレクションを削除する場合True
        """
        if OPENAI_APIKEY is None:
            raise ValueError("OPENAI_API_KEY is not set.")
        headers = {"X-OpenAI-Api-Key": OPENAI_APIKEY}
        if COHERE_APIKEY is not None:
            headers["X-Cohere-Api-Key"] = COHERE_APIKEY
        self.client = weaviate.connect_to_local(port=10080, headers=headers)

        self.text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n\n",
        )

        self.collection_name = collection_name.capitalize()
        self.client.connect()
        self.check_collection_available(self.collection_name)
        if remove_collection:
            self.delete_collection()
        self.collection = None

    def __del__(self):
        """
        デストラクタ
        """
        self.client.close()

    def delete_collection(self) -> None:
        """コレクションを削除"""
        self.client.collections.delete(self.collection_name)

    def check_collection_available(self, name: str) -> bool:
        """コレクションが存在するか確認

        Args:
            name(str): コレクション名

        Returns:
            bool: コレクションが存在する場合True
        """
        try:
            response = self.client.collections.list_all(simple=False)
            if name in response.keys():
                return True
            else:
                return False
        except weaviate.exceptions.WeaviateCollectionDoesNotExist:
            return False

    def ensure_collection_exists(self) -> None:
        """コレクションが存在しない場合は作成する"""
        if self.collection is not None:
            return
        if self.check_collection_available(self.collection_name):
            print("Collection already exists")
            self.collection = self.client.collections.get(self.collection_name)
            return
        self.collection = self.client.collections.create(
            name=self.collection_name,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-large",  # モデルはtext-embedding-3-largeを使用
                vectorize_collection_name=False,  # コレクション名はベクトル化に含めない
            ),
            reranker_config=wvc.config.Configure.Reranker.cohere(
                model="rerank-multilingual-v3.0"
            ),
            properties=[
                wvc.config.Property(
                    name="content",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=False,  # ベクトル化を有効
                    vectorize_property_name=False,  # プロパティ名をベクトル化に含めない
                    index_searchable=True,
                    index_filterable=False,
                    tokenization=wvc.config.Tokenization.GSE,
                ),
                wvc.config.Property(
                    name="source",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,  # ベクトル化無効
                    index_searchable=False,
                    index_filterable=False,
                ),
                wvc.config.Property(
                    name="chunk_index",
                    data_type=wvc.config.DataType.INT,  # INT型はベクトル化されない
                    skip_vectorization=True,
                ),
                wvc.config.Property(
                    name="date",
                    data_type=wvc.config.DataType.DATE,
                    skip_vectorization=True,
                ),
            ],
        )

    def upload_chunks(
        self,
        chunks: List[str],
        source: str = "",
        date: Optional[datetime] = None,
    ) -> str:
        """
        チャンクをWeaviateにアップロード

        Args:
            chunks(List[str]): チャンクリスト
            source(str): ソースファイル名。デフォルトは""。
            chunk_index(int): チャンクインデックス番号。デフォルトは0。
            date(datetime): 更新日時。ない場合は現在時刻がつく。デフォルトはNone。

        Returns:
            str: アップロードされたチャンクのID
        """
        self.ensure_collection_exists()
        chunk_ids = []
        if date is None:
            date = datetime.now(timezone.utc)
        with self.collection.batch.dynamic() as batch:
            for i, chunk in enumerate(chunks):
                # データオブジェクトの作成
                properties = {
                    "content": chunk,
                    "source": source,
                    "chunk_index": i,
                    "date": date.isoformat(("T")),
                }
                # オブジェクトの追加
                try:
                    result = batch.add_object(properties=properties)
                    chunk_ids.append(result)
                except Exception as e:
                    print(f"Error uploading chunk: {str(e)}")
        if len(self.collection.batch.failed_objects) > 0:
            raise ValueError(
                "Failed to upload some chunks: {self.collection.batch.failed_objects}"
            )
        return chunk_ids

    def upload_text(
        self,
        text: str,
        source: str,
    ) -> List[str]:
        """
        テキストを分割してWeaviateにアップロード

        Args:
            text(str): アップロードするテキスト
            source(str): テキストのソース

        Returns:
            List[str]: アップロードされたチャンクのIDリスト
        """
        # テキストを分割
        chunks = self.text_splitter.split_text(text)
        chunk_ids = []
        # 現在時刻
        upload_time = datetime.now(timezone.utc)
        result = self.upload_chunks(chunks=chunks, source=source, date=upload_time)
        return result

    def upload_text_file(
        self, file_path: str, metadata: Optional[Dict] = None
    ) -> List[str]:
        """
        ファイルを読み込んでWeaviateにアップロード

        Args:
            file_path(str): ファイルパス
            metadata(Dict): メタデータ

        Returns:
            List[str]: アップロードされたチャンクのIDリスト

        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
                return self.upload_text(
                    text=text,
                    source=file_path,
                )
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return []

    def upload_files(
        self, file_paths: List[str], metadata: Optional[Dict] = None
    ) -> Dict[str, List[str]]:
        """
        複数のファイルをアップロード

        Args:
            file_paths(List[str]): ファイルパスリスト
            metadata(Dict): メタデータ

        Returns:
            Dict[str, List[str]]: アップロードされたファイルとチャンクIDのリスト
        """
        results = {}
        for file_path in file_paths:
            if file_path.endswith(".txt"):
                chunk_ids = self.upload_text_file(file_path, metadata)
                results[file_path] = chunk_ids
                print(f"Uploaded {file_path}: {len(chunk_ids)} chunks")
        return results
