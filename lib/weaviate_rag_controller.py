import os

from datetime import datetime, timezone
import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Rerank
from typing import Any, Dict, List, Optional
from langchain.text_splitter import CharacterTextSplitter

from .conf import COHERE_APIKEY, OPENAI_APIKEY


class WeaviateRagController(object):
    """
    Weaviateを使ったRAGのリトリーバ
    """

    def __init__(
        self,
    ) -> None:
        """
        コンストラクタ
        """
        self.cohere_rerank = False
        if OPENAI_APIKEY is None:
            raise ValueError("OPENAI_API_KEY is not set.")
        headers = {"X-OpenAI-Api-Key": OPENAI_APIKEY}
        if COHERE_APIKEY is not None:
            headers["X-Cohere-Api-Key"] = COHERE_APIKEY
            self.cohere_rerank = True
        self.chunk_size = 512
        self.chunk_overlap = 128
        self.client = weaviate.connect_to_local(port=10080, headers=headers)

    def __del__(self) -> None:
        """
        デストラクタ
        """
        self.client.close()

    def get_collections(self) -> list[str]:
        """
        コレクション名前の一覧を取得

        Returns:
            list: コレクション名の一覧
        """
        collections = self.client.collections.list_all(simple=False)
        collection_list = [collection for collection in collections.keys()]
        return collection_list

    def remove_collection(self, collection_name: str) -> None:
        """
        コレクションを削除

        Args:
            name(str): コレクション名
        """
        print(f"Removing collection: {collection_name}")
        self.client.collections.delete(collection_name)
        return

    def check_collection_available(self, name: str) -> bool:
        """コレクションが存在するか確認

        Args:
            name(str): コレクション名

        Returns:
            bool: コレクションが存在する場合True
        """
        try:
            collection_list = self.get_collections()
            if name.capitalize() in collection_list:
                return True
            else:
                return False
        except weaviate.exceptions.WeaviateCollectionDoesNotExist:
            return False

    def remove_object_by_uuid(self, uuid: str) -> None:
        """
        UUIDでオブジェクトを削除

        Args:
            uuid(str): オブジェクトのUUID
        """
        self.client.data_object.delete(uuid)
        return

    def ensure_collection_exists(self, collection_name) -> None:
        """コレクションが存在しない場合は作成する

        Args:
            collection_name(str): コレクション名

        """
        if self.check_collection_available(collection_name):
            return
        self.client.collections.create(
            name=collection_name,
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

    def get_objects(self, collection_name: str) -> list:
        """
        コレクション内のオブジェクトを取得

        Args:
            collection_name(str): コレクション名

        Returns:
            list: オブジェクトのリスト
        """
        collection = self.client.collections.get(collection_name)
        object_list = []
        for item in collection.iterator():
            object_list.append(item)
        return object_list

    def get_objects_by_source(self, collection_name: str, source: str) -> List[Any]:
        """
        ソース名でオブジェクトを取得

        Args:
            collection_name(str): コレクション名
            source(str): ソース名

        Returns:
            List[Any]: オブジェクトのリスト
        """
        all_objects = self.get_objects(collection_name=collection_name)
        objects = [obj for obj in all_objects if obj.properties["source"] == source]
        return objects

    def hybrid_search(
        self,
        collection_name: str,
        text: str,
        limit: int = 3,
        alpha: float = 0.75,
        rerank: bool = False,
    ) -> str:
        """
        ハイブリッド検索を実行し、結果を返す

        Args:
            collection_name(str): コレクション名
            text(str): 検索クエリ
            limit(int): 検索結果の最大数
            alpha(float): ハイブリッド検索の重み
            rerank(bool): rerankを行うかどうか

        Returns:
            str: 検索結果
        """
        collection = self.client.collections.get(collection_name)
        response = ""
        if rerank:
            if not self.cohere_rerank:
                raise ValueError("COHERE_API_KEY is not set.")
            response = collection.query.hybrid(
                query=text,
                limit=limit,
                alpha=alpha,
                query_properties=["content"],
                return_metadata=wvc.query.MetadataQuery(
                    distance=True, certainty=True, score=True, explain_score=True
                ),
                rerank=Rerank(prop="content", query=text),
            )
        else:
            response = collection.query.hybrid(
                query=text,
                limit=limit,
                alpha=alpha,
                query_properties=["content"],
                return_metadata=wvc.query.MetadataQuery(
                    distance=True, certainty=True, score=True, explain_score=True
                ),
            )
        return response

    def set_chunk_size(self, chunk_size: int) -> None:
        """
        チャンクサイズを設定

        Args:
            chunk_size(int): チャンクサイズ
        """
        self.chunk_size = chunk_size

    def set_chunk_overlap(self, chunk_overlap: int) -> None:
        """
        チャンクオーバーラップを設定

        Args:
            chunk_overlap(int): チャンクオーバーラップ
        """
        self.chunk_overlap = chunk_overlap

    def upload_chunks(
        self,
        collection_name: str,
        chunks: List[str],
        source: str = "",
        date: Optional[datetime] = None,
    ) -> str:
        """
        チャンクをWeaviateにアップロード

        Args:
            collection_name(str): コレクション名
            chunks(List[str]): チャンクリスト
            source(str): ソースファイル名。デフォルトは""。
            chunk_index(int): チャンクインデックス番号。デフォルトは0。
            date(datetime): 更新日時。ない場合は現在時刻がつく。デフォルトはNone。

        Returns:
            str: アップロードされたチャンクのID
        """
        self.ensure_collection_exists(collection_name=collection_name)
        collection = self.client.collections.get(collection_name)
        chunk_ids = []
        if date is None:
            date = datetime.now(timezone.utc)
        with collection.batch.dynamic() as batch:
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
        if len(collection.batch.failed_objects) > 0:
            raise ValueError(
                "Failed to upload some chunks: {self.collection.batch.failed_objects}"
            )
        return chunk_ids

    def upload_text(
        self,
        collection_name: str,
        text: str,
        source: str,
    ) -> List[str]:
        """
        テキストを分割してWeaviateにアップロード

        Args:
            collection_name(str): コレクション名
            text(str): アップロードするテキスト
            source(str): テキストのソース
            chunk_size(int): チャンクサイズ
            chunk_overlap(int): チャンクのオーバーラップ

        Returns:
            List[str]: アップロードされたチャンクのIDリスト
        """
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separator="\n\n",
        )
        # テキストを分割
        chunks = text_splitter.split_text(text)
        # 現在時刻
        upload_time = datetime.now(timezone.utc)
        result = self.upload_chunks(
            collection_name=collection_name,
            chunks=chunks,
            source=source,
            date=upload_time,
        )
        return result

    def upload_text_file(
        self, collection_name: str, file_path: str, metadata: Optional[Dict] = None
    ) -> List[str]:
        """
        ファイルを読み込んでWeaviateにアップロード

        Args:
            collection_name(str): コレクション名
            file_path(str): ファイルパス
            metadata(Dict): メタデータ

        Returns:
            List[str]: アップロードされたチャンクのIDリスト

        """
        # try:
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
            file_name = os.path.basename(file_path)
            return self.upload_text(
                collection_name=collection_name,
                text=text,
                source=file_name,
            )
        # except Exception as e:
        #    print(f"Error processing {file_path}: {str(e)}")
        #    return []

    def upload_files(
        self,
        collection_name: str,
        file_paths: List[str],
        metadata: Optional[Dict] = None,
    ) -> Dict[str, List[str]]:
        """
        複数のファイルをアップロード

        Args:
            collection_name(str): コレクション名
            file_paths(List[str]): ファイルパスリスト
            metadata(Dict): メタデータ

        Returns:
            Dict[str, List[str]]: アップロードされたファイルとチャンクIDのリスト
        """
        results = {}
        for file_path in file_paths:
            if file_path.endswith(".txt"):
                chunk_ids = self.upload_text_file(
                    collection_name=collection_name,
                    file_path=file_path,
                    metadata=metadata,
                )
                results[file_path] = chunk_ids
                print(f"Uploaded {file_path}: {len(chunk_ids)} chunks")
        return results