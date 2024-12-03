import argparse

from lib.weaviate_rag_controller import WeaviateRagController


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Weaviate host")
    parser.add_argument("--port", type=int, default=10080, help="Weaviate port")
    parser.add_argument(
        "-c",
        "--collection",
        default="Test",
        type=str,
        help="Weaviate collection name",
    )
    parser.add_argument(
        "-s",
        "--show_objects",
        action="store_true",
        help="Show objects in the collection",
    )
    args = parser.parse_args()
    weaviate_controller = WeaviateRagController(host=args.host, port=args.port)
    if args.show_objects:
        list = weaviate_controller.get_objects(collection_name=args.collection)
        for item in list:
            print(f"source: {item.properties['source']}")
            print(f"uuid: {item.uuid}")
            print(f"date: {item.properties['date']}")
            print(f"chunk_index: {item.properties['chunk_index']}")
            print(f"content: {item.properties['content']}")
            print("====================================")
    while True:
        print("文章をキーボード入力後、Enterを押してください。")
        text = input("Input: ")
        response = weaviate_controller.hybrid_search(
            text=text,
            limit=3,
            alpha=0.75,
            rerank=False,
            collection_name=args.collection,
        )
        for p in response.objects:
            print(f"distance: {p.metadata.distance}")
            print(f"certainty: {p.metadata.certainty}")
            print(f"score: {p.metadata.score}")
            print(f"explain_score: {p.metadata.explain_score}")
            print(f"source: {p.properties['source']}")
            print(f"content: {p.properties['content']}")
            print()


if __name__ == "__main__":
    main()
