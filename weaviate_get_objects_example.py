import argparse

from lib.weaviate_rag_retriever import WeaviateRagRetriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--collections",
        default="Test",
        type=str,
        help="Weaviate collection name",
    )
    parser.add_argument(
        "-s",
        "--show_all",
        action="store_true",
        help="Show all content in objects",
    )
    args = parser.parse_args()
    retriever = WeaviateRagRetriever()
    list = retriever.get_objects(collection_name=args.collections)
    list.sort(key=lambda item: (item.properties['source'], item.properties['chunk_index']))
    for item in list:
        print(f"source: {item.properties['source']}")
        print(f"uuid: {item.uuid}")
        print(f"date: {item.properties['date']}")
        print(f"chunk_index: {item.properties['chunk_index']}")
        if args.show_all:
            print(f"content: {item.properties['content']}")
        else:
            print(f"content: {item.properties['content'][:60]}...")
        print("====================================")


if __name__ == "__main__":
    main()
