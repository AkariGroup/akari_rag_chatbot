import os

import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Rerank

from .conf import COHERE_APIKEY, OPENAI_APIKEY


class WeaviateRagRetriever(object):
    def __init__(self) -> None:
        """
        初期化

        Args:
            collection_name(str): コレクション名
        """
        self.cohere_rerank = False
        if OPENAI_APIKEY is None:
            raise ValueError("OPENAI_API_KEY is not set.")
        headers = {"X-OpenAI-Api-Key": OPENAI_APIKEY}
        if COHERE_APIKEY is not None:
            headers["X-Cohere-Api-Key"] = COHERE_APIKEY
            self.cohere_rerank = True
        self.client = weaviate.connect_to_local(port=10080,headers=headers)

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
